from pathlib import Path
from typing import TypeVar

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel

from jarvis.config.models import (
    InstrumentsConfig,
    JarvisConfig,
    RiskSettings,
    SessionsConfig,
    StrategiesConfig,
)

ModelT = TypeVar("ModelT", bound=BaseModel)
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def load_yaml_config(
    model_type: type[ModelT], filename: str, config_dir: Path | None = None
) -> ModelT:
    """Load and validate one YAML configuration file."""
    directory = config_dir if config_dir is not None else DEFAULT_CONFIG_DIR
    path = directory / filename
    with path.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return model_type.model_validate(data)


def load_instruments(config_dir: Path | None = None) -> InstrumentsConfig:
    """Load instrument configuration."""
    return load_yaml_config(InstrumentsConfig, "instruments.yaml", config_dir)


def load_strategies(config_dir: Path | None = None) -> StrategiesConfig:
    """Load strategy configuration."""
    return load_yaml_config(StrategiesConfig, "strategies.yaml", config_dir)


def load_jarvis(config_dir: Path | None = None) -> JarvisConfig:
    """Load Jarvis configuration."""
    return load_yaml_config(JarvisConfig, "jarvis.yaml", config_dir)


def load_risk(config_dir: Path | None = None) -> RiskSettings:
    """Load risk configuration."""
    return load_yaml_config(RiskSettings, "risk.yaml", config_dir)


def load_sessions(config_dir: Path | None = None) -> SessionsConfig:
    """Load session windows configuration."""
    return load_yaml_config(SessionsConfig, "sessions.yaml", config_dir)
