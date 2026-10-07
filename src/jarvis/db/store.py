"""SignalStore: facade over the SQLite repositories (T6.1).

Agents and graph nodes never write SQL; they call this facade. Re-running the
same cycle_id upserts, never duplicates (Backend_Schema §5.5).
"""
import hashlib
import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session

from jarvis.config.models import ConfigModel, InstrumentConfig
from jarvis.db.models import CycleModel, InstrumentModel, OutcomeModel, SignalModel
from jarvis.db.repositories import cycles, outcomes, signals
from jarvis.db.session import DEFAULT_DB_PATH, init_db, make_engine
from jarvis.schemas import CycleTrigger, Outcome, Signal


def config_hash(*configs: ConfigModel) -> str:
    """Deterministic hash of config models (cycles.config_hash)."""
    payload = json.dumps([c.model_dump(mode="json") for c in configs], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SignalStore:
    """Typed facade for cycle/signal/outcome persistence."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        instruments: Sequence[InstrumentConfig] = (),
    ) -> None:
        path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self._engine: Engine = make_engine(path)
        init_db(self._engine)
        self._seed_instruments(list(instruments))

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Expose a short-lived session for repository calls in tests."""
        with Session(self._engine) as session:
            yield session

    def close(self) -> None:
        """Dispose the engine so SQLite file handles are released."""
        self._engine.dispose()

    def _seed_instruments(self, instruments: Sequence[InstrumentConfig]) -> None:
        with self.session() as session:
            for cfg in instruments:
                existing = session.get(InstrumentModel, cfg.symbol)
                if existing is None:
                    session.add(
                        InstrumentModel(
                            symbol=cfg.symbol,
                            broker_symbol=cfg.broker_symbol,
                            agent_name=cfg.agent,
                            enabled=1,
                            created_at=datetime.now(UTC),
                        )
                    )
            session.commit()

    def start_cycle(
        self,
        cycle_id: str,
        trigger: CycleTrigger,
        config_hash: str,
        config_text: str = "{}",
    ) -> None:
        """Start (or idempotently resume) a cycle and store its config snapshot."""
        with self.session() as session:
            cycles.upsert_cycle(session, cycle_id, trigger, config_hash, config_text)

    def complete_cycle(
        self,
        cycle_id: str,
        status: str,
        finished_at: datetime | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Finish a cycle with its final status."""
        with self.session() as session:
            cycles.complete_cycle(session, cycle_id, status, finished_at, duration_ms)

    def get_cycle(self, cycle_id: str) -> CycleModel | None:
        """Fetch a cycle row by id (None if unknown)."""
        with self.session() as session:
            return cycles.get_cycle(session, cycle_id)

    def upsert_signal(self, signal: Signal, cycle_id: str) -> None:
        """Persist one signal (insert or update); unique-OPEN index enforced by DB."""
        with self.session() as session:
            signals.upsert_signal(session, signal, cycle_id)

    def get_signal(self, signal_id: str) -> SignalModel | None:
        """Fetch one signal row by id."""
        with self.session() as session:
            return signals.get_signal(session, signal_id)

    def get_open_signals(self, symbol: str | None = None) -> list[SignalModel]:
        """All OPEN signals, optionally for one symbol."""
        with self.session() as session:
            return signals.get_open_signals(session, symbol)

    def list_signals(self, limit: int = 100) -> list[SignalModel]:
        """Most recent signals first."""
        with self.session() as session:
            return signals.list_signals(session, limit)

    def resolve_outcome(self, outcome: Outcome) -> None:
        """Write an outcome row and update the signal status (once per signal)."""
        with self.session() as session:
            outcomes.resolve_outcome(session, outcome)

    def get_outcome(self, signal_id: str) -> OutcomeModel | None:
        """Fetch the outcome row for a signal, if any."""
        with self.session() as session:
            return outcomes.get_outcome(session, signal_id)

    def list_outcomes(self, limit: int = 100) -> list[OutcomeModel]:
        """Most recently resolved outcomes first."""
        with self.session() as session:
            return outcomes.list_outcomes(session, limit)
