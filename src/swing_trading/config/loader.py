from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from swing_trading.config.models import AppConfig


class ConfigurationError(ValueError):
    """Raised when configuration bytes cannot be parsed or validated."""


@dataclass(frozen=True, slots=True)
class LoadedConfig:
    settings: AppConfig
    sha256: str
    raw_bytes: bytes
    source: Path


def load_config(path: Path) -> LoadedConfig:
    raw_bytes = path.read_bytes()
    try:
        payload: Any = yaml.safe_load(raw_bytes)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {path.name}") from exc
    if not isinstance(payload, dict):
        raise ConfigurationError("configuration root must be a mapping")
    try:
        settings = AppConfig.model_validate(payload)
    except ValidationError as exc:
        raise ConfigurationError(f"configuration validation failed: {exc}") from exc
    return LoadedConfig(
        settings=settings,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        raw_bytes=raw_bytes,
        source=path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a versioned strategy configuration")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    loaded = load_config(args.path)
    print(f"VALID {loaded.settings.strategy_version} sha256={loaded.sha256}")
    return 0
