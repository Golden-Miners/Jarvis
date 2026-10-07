#!/usr/bin/env python3
"""Seed instruments table from config/instruments.yaml."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlmodel import Session

from jarvis.config.loaders import load_instruments
from jarvis.db.models import InstrumentModel
from jarvis.db.session import make_engine

DB_PATH = Path("data") / "jarvis.db"

# Default digits/point for common forex/crypto symbols
DEFAULT_DIGITS = {
    "XAUUSD": 2,
    "XAGUSD": 3,
    "BTCUSD": 2,
    "ETHUSD": 2,
    "USOUSD": 2,
}
DEFAULT_POINT = {
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    "BTCUSD": 0.01,
    "ETHUSD": 0.01,
    "USOUSD": 0.01,
}

def seed_instruments() -> None:
    """Load instruments from YAML and upsert into DB."""
    config = load_instruments()
    engine = make_engine(DB_PATH)

    with Session(engine) as session:
        for inst in config.instruments:
            # Check if exists
            existing = session.get(InstrumentModel, inst.symbol)
            if existing:
                print(f"Updating {inst.symbol}...")
                existing.broker_symbol = inst.broker_symbol
                existing.agent_name = inst.agent
                existing.digits = DEFAULT_DIGITS.get(inst.symbol)
                existing.point = DEFAULT_POINT.get(inst.symbol)
                existing.enabled = 1
            else:
                print(f"Inserting {inst.symbol}...")
                session.add(
                    InstrumentModel(
                        symbol=inst.symbol,
                        broker_symbol=inst.broker_symbol,
                        agent_name=inst.agent,
                        digits=DEFAULT_DIGITS.get(inst.symbol),
                        point=DEFAULT_POINT.get(inst.symbol),
                        enabled=1,
                    )
                )
        session.commit()
    print("Instruments seeded successfully.")


if __name__ == "__main__":
    seed_instruments()