from decimal import ROUND_FLOOR, Decimal

from jarvis.config.models import JarvisConfig, RiskSettings
from jarvis.schemas import RiskAssessment, SetupCandidate, SymbolInfo, Tick


def run_war_machine(
    candidate: SetupCandidate,
    tick: Tick,
    symbol_info: SymbolInfo,
    atr_value: float,
    account_equity: float,
    jarvis_config: JarvisConfig,
    risk_settings: RiskSettings,
) -> RiskAssessment:
    """Assess candidate price geometry, broker spread, ATR bounds, and lot size."""
    if atr_value <= 0:
        raise ValueError("atr_value must be positive")
    if account_equity <= 0:
        raise ValueError("account_equity must be positive")
    if symbol_info.symbol != candidate.symbol:
        raise ValueError("symbol info does not match candidate symbol")

    issues: list[str] = []
    stop_distance, reward_distance = _distances(candidate)
    rr = reward_distance / stop_distance if stop_distance > 0 else 0.0
    sl_atr_mult = stop_distance / atr_value if stop_distance > 0 else 0.0
    if stop_distance <= 0 or reward_distance <= 0:
        issues.append("invalid directional price geometry")
    if rr < jarvis_config.minimum_rr:
        issues.append("reward:risk below minimum")
    if not (
        risk_settings.minimum_sl_atr_multiple
        <= sl_atr_mult
        <= risk_settings.maximum_sl_atr_multiple
    ):
        issues.append("stop distance outside ATR bounds")

    spread_points = (tick.ask - tick.bid) / symbol_info.point
    spread_ok = spread_points <= risk_settings.maximum_spread_points
    if not spread_ok:
        issues.append("spread exceeds maximum")

    suggested_lot = _suggest_lot(
        stop_distance, symbol_info, account_equity, jarvis_config.risk_percent
    )
    if suggested_lot is None:
        issues.append("risk-sized lot is below broker minimum")
    return RiskAssessment(
        candidate_id=_candidate_id(candidate),
        valid=not issues,
        rr=rr,
        sl_atr_mult=sl_atr_mult,
        spread_ok=spread_ok,
        suggested_lot=suggested_lot,
        issues=issues,
    )


def _distances(candidate: SetupCandidate) -> tuple[float, float]:
    if candidate.direction == "BUY":
        return candidate.entry - candidate.sl, candidate.tp - candidate.entry
    return candidate.sl - candidate.entry, candidate.entry - candidate.tp


def _suggest_lot(
    stop_distance: float,
    info: SymbolInfo,
    account_equity: float,
    risk_percent: float,
) -> float | None:
    if stop_distance <= 0 or info.trade_tick_value <= 0:
        return None
    risk_cash = account_equity * risk_percent / 100
    risk_per_lot = stop_distance / info.trade_tick_size * info.trade_tick_value
    raw_lot = risk_cash / risk_per_lot
    step = Decimal(str(info.volume_step))
    lot = (Decimal(str(raw_lot)) / step).to_integral_value(rounding=ROUND_FLOOR) * step
    if lot < Decimal(str(info.volume_min)):
        return None
    return float(min(lot, Decimal(str(info.volume_max))))


def _candidate_id(candidate: SetupCandidate) -> str:
    return (
        f"{candidate.symbol}:{candidate.strategy}:{candidate.created_at.isoformat()}"
        f":{candidate.direction}:{candidate.entry}:{candidate.sl}:{candidate.tp}"
    )
