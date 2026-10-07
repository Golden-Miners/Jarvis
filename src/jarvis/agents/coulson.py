"""Coulson: outcome tracker — resolves hypothetical signal results from price action.

This agent monitors OPEN signals and checks current price against SL/TP to determine
if TP_HIT, SL_HIT, or EXPIRED. It writes outcomes to the database via the repositories.
"""
# mypy: ignore-errors
from datetime import datetime
from typing import Any

from jarvis.graph.state import JarvisState
from jarvis.schemas import Outcome, OutcomeResult


def run_coulson(
    state: JarvisState,
    store: Any,  # SignalStore
    timeframe: str,
    config_hash: str,
    trigger: str = "MANUAL",
) -> dict[str, Any]:
    """Resolve outcomes for all OPEN signals using the latest candle per symbol.

    Args:
        state: JarvisState with symbols, signals, and errors.
        store: SignalStore instance for DB access.
        timeframe: Primary timeframe (e.g., "M15") to use for price checks.
        config_hash: Config snapshot hash for cycle tracking.
        trigger: Cycle trigger type (default: MANUAL).

    Returns:
        Dict with "outcomes" (list[Outcome]) and "errors" (list[dict]).
    """
    outcomes: list[Outcome] = []
    errors: list[dict[str, Any]] = []

    # Get signals from state AND store (state for current cycle, store for all open)
    state_signals = state.get("signals", [])
    store_signals = store.get_open_signals()

    # Combine: prefer state signals (newer), but include store signals
    all_signals = {s.id: s for s in state_signals}
    for s in store_signals:
        if s.id not in all_signals:
            all_signals[s.id] = s
        else:
            # Signal in both: use DB version for status (more authoritative)
            all_signals[s.id] = s

    signals = list(all_signals.values())
    symbols_data = state.get("symbols", {})

    # Persist any signals from state that aren't in DB yet
    cycle_id = state.get("cycle_id", "")
    if cycle_id:
        # Ensure cycle exists in DB
        store.start_cycle(cycle_id, trigger, config_hash)
    for signal in state_signals:
        if store.get_signal(signal.id) is None:
            try:
                store.upsert_signal(signal, cycle_id)
            except Exception as e:
                errors.append({
                    "agent": "Coulson",
                    "error": f"failed to persist signal {signal.id}: {e}",
                    "signal_id": signal.id,
                })

    # Check for duplicate OPEN signals (same symbol, direction)
    seen = set()
    for signal in signals:
        if signal.status == "OPEN" and signal.direction:
            key = (signal.symbol, signal.direction)
            if key in seen:
                err_msg = (
                    f"duplicate OPEN signal for {signal.symbol} "
                    f"{signal.direction}: {signal.id}"
                )
                errors.append({
                    "agent": "Coulson",
                    "error": err_msg,
                    "signal_id": signal.id,
                })
                continue
            seen.add(key)

    for signal in signals:
        if signal.status != "OPEN":
            continue

        sym_data = symbols_data.get(signal.symbol)
        if not sym_data:
            # No candle data for this symbol: cannot decide, stay OPEN, no error
            continue

        candles = sym_data.get("candles", {}).get(timeframe, [])
        if not candles:
            # No candles for this timeframe: cannot decide, stay OPEN, no error
            continue

        # Only consider candles strictly after signal creation
        relevant_candles = [c for c in candles if c.timestamp > signal.created_at]
        if not relevant_candles:
            continue

        # Track max favorable/adverse excursion
        max_favorable = 0.0
        max_adverse = 0.0

        for candle in relevant_candles:
            if signal.direction == "BUY":
                favorable = candle.high - signal.entry if signal.entry else 0
                adverse = signal.entry - candle.low if signal.entry else 0
                if favorable > max_favorable:
                    max_favorable = favorable
                if adverse > max_adverse:
                    max_adverse = adverse

                if candle.high >= signal.tp:  # TP hit first (conservative: SL first if both)
                    if candle.low <= signal.sl:
                        outcome = _make_outcome(
                            signal, "SL_HIT", relevant_candles[-1].timestamp,
                            -1.0, max_favorable, max_adverse
                        )
                    else:
                        denom = signal.entry - signal.sl if signal.entry > signal.sl else 0
                        r_mult = (signal.tp - signal.entry) / denom if denom else 0
                        outcome = _make_outcome(
                            signal, "TP_HIT", relevant_candles[-1].timestamp,
                            r_mult, max_favorable, max_adverse
                        )
                    outcomes.append(outcome)
                    break
                elif candle.low <= signal.sl:
                    outcome = _make_outcome(
                        signal, "SL_HIT", relevant_candles[-1].timestamp,
                        -1.0, max_favorable, max_adverse
                    )
                    outcomes.append(outcome)
                    break

            elif signal.direction == "SELL":
                favorable = signal.entry - candle.low if signal.entry else 0
                adverse = candle.high - signal.entry if signal.entry else 0
                if favorable > max_favorable:
                    max_favorable = favorable
                if adverse > max_adverse:
                    max_adverse = adverse

                if candle.low <= signal.tp:
                    if candle.high >= signal.sl:
                        outcome = _make_outcome(
                            signal, "SL_HIT", relevant_candles[-1].timestamp,
                            -1.0, max_favorable, max_adverse
                        )
                    else:
                        denom = signal.sl - signal.entry if signal.sl > signal.entry else 0
                        r_mult = (signal.entry - signal.tp) / denom if denom else 0
                        outcome = _make_outcome(
                            signal, "TP_HIT", relevant_candles[-1].timestamp,
                            r_mult, max_favorable, max_adverse
                        )
                    outcomes.append(outcome)
                    break
                elif candle.high >= signal.sl:
                    outcome = _make_outcome(
                        signal, "SL_HIT", relevant_candles[-1].timestamp,
                        -1.0, max_favorable, max_adverse
                    )
                    outcomes.append(outcome)
                    break

        else:
            # No TP/SL hit - check expiry
            if signal.expires_at and relevant_candles[-1].timestamp >= signal.expires_at:
                last_close = relevant_candles[-1].close
                if signal.direction == "BUY" and signal.entry and signal.sl:
                    r_mult = (last_close - signal.entry) / (signal.entry - signal.sl)
                elif signal.direction == "SELL" and signal.entry and signal.sl:
                    r_mult = (signal.entry - last_close) / (signal.sl - signal.entry)
                else:
                    r_mult = 0.0
                outcome = _make_outcome(
                    signal, "EXPIRED", relevant_candles[-1].timestamp,
                    r_mult, max_favorable, max_adverse
                )
                outcomes.append(outcome)

    # Persist outcomes
    for outcome in outcomes:
        try:
            _persist_outcome(store, outcome)
        except Exception as e:
            errors.append({
                "agent": "Coulson",
                "error": f"failed to persist outcome for {outcome.signal_id}: {e}",
                "signal_id": outcome.signal_id,
            })

    # Complete the cycle
    cycle_id = state.get("cycle_id", "")
    if cycle_id:
        store.complete_cycle(cycle_id, "COMPLETED" if not errors else "DEGRADED")
    return {"outcomes": outcomes, "errors": errors}


def _make_outcome(
    signal: Any,
    result: OutcomeResult,
    resolved_at: datetime,
    r_multiple: float,
    max_favorable: float,
    max_adverse: float,
) -> Outcome:
    """Create an Outcome from signal and resolution data."""
    return Outcome(
        signal_id=signal.id,
        result=result,
        resolved_at=resolved_at,
        r_multiple=r_multiple,
        max_favorable=max_favorable,
        max_adverse=max_adverse,
    )


def _persist_outcome(store: Any, outcome: Outcome) -> None:
    """Write outcome to DB and update signal status."""
    store.resolve_outcome(outcome)


# Backward compatibility: simple MT5-based tracker
class Coulson:
    """Legacy MT5-based outcome tracker (not used in graph)."""

    def __init__(
        self,
        store: Any = None,
    ) -> None:
        self.store = store

    def __enter__(self) -> "Coulson":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    def resolve_all_open(self) -> list[Outcome]:
        """Check all OPEN signals and resolve outcomes (requires MT5)."""
        # This would need MT5 provider - not implemented for legacy class
        return []


def run_coulson_once() -> list[Outcome]:
    """Convenience function: run Coulson once and return resolved outcomes."""
    with Coulson() as coulson:
        return coulson.resolve_all_open()


if __name__ == "__main__":
    outcomes = run_coulson_once()
    print(f"Resolved {len(outcomes)} outcomes:")
    for o in outcomes:
        print(f"  {o.signal_id}: {o.result} (R={o.r_multiple:.2f})")