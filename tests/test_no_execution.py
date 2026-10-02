import ast
import io
import tokenize
from pathlib import Path

FORBIDDEN_NAMES = {
    "order_send",
    "order_check",
    "positions_get",
    "positions_total",
    "orders_get",
    "orders_total",
    "history_orders_get",
    "history_deals_get",
    "TRADE_ACTION_DEAL",
    "TRADE_ACTION_PENDING",
}
FORBIDDEN_PREFIXES = ("positions_", "order_send", "order_check")


def _forbidden_name(name: str) -> bool:
    return name in FORBIDDEN_NAMES or name.startswith(FORBIDDEN_PREFIXES)


def _find_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    found = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and _forbidden_name(node.id)
    }
    found.update(
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and _forbidden_name(node.attr)
    )
    found.update(
        alias.name.split(".")[-1]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
        if _forbidden_name(alias.name.split(".")[-1])
    )
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.STRING:
            try:
                value = ast.literal_eval(token.string)
            except (SyntaxError, ValueError):
                continue
            if isinstance(value, str) and _forbidden_name(value):
                found.add(value)
    return sorted(found)


def scan_production_source(source_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        for name in _find_violations(path.read_text(encoding="utf-8")):
            violations.append(f"{path}: forbidden trading API {name}")
    return violations


def test_production_source_has_no_trade_execution_apis() -> None:
    source_root = Path(__file__).parents[1] / "src" / "jarvis"

    assert scan_production_source(source_root) == []


def test_scanner_rejects_direct_calls_and_imports() -> None:
    source = "import MetaTrader5 as mt5\nmt5.order_send(request)\n"

    assert _find_violations(source) == ["order_send"]


def test_scanner_rejects_dynamic_api_names() -> None:
    source = 'getattr(mt5, "positions_get")("XAUUSD")\n'

    assert _find_violations(source) == ["positions_get"]


def test_scanner_allows_read_only_mt5_apis() -> None:
    source = """
mt5.initialize()
mt5.copy_rates_from_pos(symbol, timeframe, 1, count)
mt5.symbol_info(symbol)
mt5.symbol_info_tick(symbol)
mt5.shutdown()
"""

    assert _find_violations(source) == []
