from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StrategyMode(StrEnum):
    BACKTEST = "BACKTEST"
    SHADOW = "SHADOW"
    PAPER_CONFIRM = "PAPER_CONFIRM"
    PAPER_AUTO = "PAPER_AUTO"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"


class OperatorApproval(StrictModel):
    status: ApprovalStatus
    approved_by: str | None
    approved_at: datetime | None
    approval_reference: str | None

    @model_validator(mode="after")
    def approval_is_complete(self) -> OperatorApproval:
        evidence = (self.approved_by, self.approved_at, self.approval_reference)
        if self.status is ApprovalStatus.APPROVED and any(value is None for value in evidence):
            raise ValueError("approved configuration requires complete approval evidence")
        if self.status is ApprovalStatus.PENDING and any(value is not None for value in evidence):
            raise ValueError("pending configuration cannot contain approval evidence")
        return self


class Tc2000Config(StrictModel):
    execution_candidate_mode: Literal["intersection_3_of_3"]
    shadow_candidate_modes: tuple[Literal["agreement_2_of_3", "union_ranked"], ...]
    base_universe_name: str | None
    operator_guide_verified: bool
    max_batch_age_minutes: int | None = Field(default=None, gt=0)
    max_export_skew_seconds: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def both_import_freshness_values_are_set_together(self) -> Tc2000Config:
        values = (self.max_batch_age_minutes, self.max_export_skew_seconds)
        if (values[0] is None) != (values[1] is None):
            raise ValueError("TC2000 age and timestamp-skew values must be set together")
        if set(self.shadow_candidate_modes) != {"agreement_2_of_3", "union_ranked"}:
            raise ValueError(
                "both non-execution candidate modes must remain enabled for shadow study"
            )
        return self


class RiskConfig(StrictModel):
    risk_fraction: float = Field(gt=0, le=0.01)
    max_risk_fraction: float = Field(ge=0.01, le=0.01)
    maximum_position_notional_fraction: float | None = Field(default=None, gt=0, le=1)
    maximum_portfolio_exposure_fraction: float | None = Field(default=None, gt=0, le=1)
    maximum_concurrent_positions: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def configured_risk_does_not_exceed_ceiling(self) -> RiskConfig:
        if self.risk_fraction > self.max_risk_fraction:
            raise ValueError("risk fraction cannot exceed the fixed 1% ceiling")
        return self


class StrategyHypotheses(StrictModel):
    minimum_price: float = Field(gt=0)
    volatility_definition: Literal["adr20_previous_close_percent"]
    minimum_volatility_percent: float = Field(gt=0)
    average_dollar_volume_floor: int = Field(ge=5_000_000)
    minimum_permitted_dollar_volume_floor: Literal[5_000_000]
    pyramiding_enabled: Literal[False]
    extended_hours_entries_enabled: Literal[False]
    five_r_partial_fraction: float = Field(ge=0.20, le=0.30)
    trend_slope_lookback: int | None = Field(default=None, gt=0)
    trend_slope_thresholds: dict[str, float] | None
    pivot_definition: dict[str, int | float | str] | None
    contraction_definition: dict[str, int | float | str] | None
    moving_average_proximity: dict[str, float | str] | None
    narrow_candle_atr_fraction: float | None = Field(default=None, gt=0)
    entry_chase_limit: float | None = Field(default=None, ge=0)
    entry_ttl_seconds: int | None = Field(default=None, gt=0)
    stop_width_limits: dict[str, float] | None

    @model_validator(mode="after")
    def liquidity_floor_is_safe(self) -> StrategyHypotheses:
        if self.average_dollar_volume_floor < self.minimum_permitted_dollar_volume_floor:
            raise ValueError("average dollar-volume floor cannot be below the absolute minimum")
        return self


class AppConfig(StrictModel):
    schema_version: Literal[1]
    strategy_version: str = Field(min_length=1)
    mode: StrategyMode
    operator_approval: OperatorApproval
    paper_only: Literal[True]
    phase1_execution_enabled: Literal[False]
    tc2000: Tc2000Config
    risk: RiskConfig
    strategy_hypotheses: StrategyHypotheses

    @model_validator(mode="after")
    def phase1_modes_fail_closed(self) -> AppConfig:
        if self.mode is not StrategyMode.BACKTEST:
            raise ValueError("Phase 1 configuration permits BACKTEST mode only")
        return self
