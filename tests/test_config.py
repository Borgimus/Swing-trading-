from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from swing_trading.config.loader import ConfigurationError, load_config


def test_provisional_configuration_is_valid_and_hashed() -> None:
    loaded = load_config(Path("config/strategy-v1.yaml"))

    assert loaded.settings.paper_only is True
    assert loaded.settings.phase1_execution_enabled is False
    assert loaded.settings.risk.risk_fraction == 0.01
    assert loaded.settings.tc2000.base_universe_name is None
    assert len(loaded.sha256) == 64


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("paper_only",), False),
        (("phase1_execution_enabled",), True),
        (("mode",), "PAPER_AUTO"),
        (("risk", "risk_fraction"), 0.0101),
        (("risk", "max_risk_fraction"), 0.02),
        (("strategy_hypotheses", "average_dollar_volume_floor"), 4_999_999),
        (("strategy_hypotheses", "pyramiding_enabled"), True),
        (("strategy_hypotheses", "extended_hours_entries_enabled"), True),
    ],
)
def test_unsafe_configuration_is_rejected(
    tmp_path: Path, path: tuple[str, ...], value: object
) -> None:
    payload = yaml.safe_load(Path("config/strategy-v1.yaml").read_text())
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    candidate = tmp_path / "unsafe.yaml"
    candidate.write_text(yaml.safe_dump(payload))

    with pytest.raises(ConfigurationError):
        load_config(candidate)


def test_endpoint_configuration_key_is_forbidden(tmp_path: Path) -> None:
    payload = yaml.safe_load(Path("config/strategy-v1.yaml").read_text())
    payload["broker_endpoint"] = "https://example.invalid"
    candidate = tmp_path / "endpoint.yaml"
    candidate.write_text(yaml.safe_dump(payload))

    with pytest.raises(ConfigurationError, match="broker_endpoint"):
        load_config(candidate)


def test_partial_tc2000_freshness_configuration_is_rejected(tmp_path: Path) -> None:
    payload = yaml.safe_load(Path("config/strategy-v1.yaml").read_text())
    payload["tc2000"]["max_batch_age_minutes"] = 30
    candidate = tmp_path / "partial.yaml"
    candidate.write_text(yaml.safe_dump(payload))

    with pytest.raises(ConfigurationError, match="set together"):
        load_config(candidate)
