from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.config import load_instruments, load_jarvis, load_strategies
from jarvis.config.loaders import load_yaml_config
from jarvis.config.models import JarvisConfig


def test_loads_all_project_config_files() -> None:
    instruments = load_instruments()
    strategies = load_strategies()
    jarvis = load_jarvis()

    assert [item.symbol for item in instruments.instruments] == [
        "XAUUSD",
        "XAGUSD",
        "BTCUSD",
        "ETHUSD",
        "USOUSD",
    ]
    assert len(strategies.strategies) == 5
    assert jarvis.minimum_rr == 1.5
    assert jarvis.min_agreeing_strategies == 2


def test_loader_accepts_explicit_config_directory(tmp_path: Path) -> None:
    (tmp_path / "jarvis.yaml").write_text(
        "min_score: 0.5\n"
        "minimum_rr: 1.5\n"
        "min_agreeing_strategies: 2\n"
        "risk_percent: 1.0\n"
        "cycle_interval_seconds: 300\n",
        encoding="utf-8",
    )

    config = load_jarvis(tmp_path)

    assert config.min_score == 0.5
    assert config.cycle_interval_seconds == 300


def test_jarvis_config_rejects_out_of_range_values(tmp_path: Path) -> None:
    (tmp_path / "jarvis.yaml").write_text(
        "min_score: 0.5\n"
        "minimum_rr: 0\n"
        "min_agreeing_strategies: 2\n"
        "risk_percent: 1.0\n"
        "cycle_interval_seconds: 300\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_jarvis(tmp_path)


def test_loader_rejects_unknown_keys(tmp_path: Path) -> None:
    (tmp_path / "jarvis.yaml").write_text(
        "min_score: 0.5\n"
        "minimum_rr: 1.5\n"
        "min_agreeing_strategies: 2\n"
        "risk_percent: 1.0\n"
        "cycle_interval_seconds: 300\n"
        "unknown: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_yaml_config(JarvisConfig, "jarvis.yaml", tmp_path)


def test_loader_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    (tmp_path / "jarvis.yaml").write_text("- not-a-mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a YAML mapping"):
        load_jarvis(tmp_path)


def test_loader_propagates_yaml_syntax_errors(tmp_path: Path) -> None:
    (tmp_path / "jarvis.yaml").write_text("min_score: [\n", encoding="utf-8")

    with pytest.raises(Exception, match="while parsing a flow node"):
        load_jarvis(tmp_path)
