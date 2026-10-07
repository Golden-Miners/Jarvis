"""Fetch real MT5 candles for 5 symbols x 5 timeframes into data/real_fixtures/.

gitignored; tests skip if absent. Synthetic fixtures remain for CI.
"""
import json
from datetime import UTC, datetime
from pathlib import Path

import MetaTrader5 as mt5

SYMBOLS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "USOUSD"]
TIMEFRAMES = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}
CANDLE_COUNT = 1000  # enough for context windows

OUTPUT_DIR = Path("data") / "real_fixtures"
TF_MAP = {v: k for k, v in TIMEFRAMES.items()}


def fetch_all() -> None:
    if not mt5.initialize():
        print("MT5 init failed:", mt5.last_error())
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}

    for symbol in SYMBOLS:
        symbol_dir = OUTPUT_DIR / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        summary[symbol] = {}

        for tf_name, tf_const in TIMEFRAMES.items():
            rates = mt5.copy_rates_from_pos(
                symbol, tf_const, 0, CANDLE_COUNT
            )
            if rates is None or len(rates) == 0:
                print(f"  {symbol} {tf_name}: no data (error={mt5.last_error()})")
                summary[symbol][tf_name] = None
                continue

            # Convert to serialisable format
            records = []
            for r in rates:
                records.append({
                    "timestamp": datetime.fromtimestamp(r[0], tz=UTC).isoformat(),
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "volume": float(r[5]),
                    "spread": int(r[6]),
                    "real_volume": int(r[7]),
                })

            filepath = symbol_dir / f"{tf_name}.json"
            with open(filepath, "w") as f:
                json.dump(records, f, indent=2)

            count = len(records)
            first_ts = datetime.fromisoformat(records[0]["timestamp"])
            last_ts = datetime.fromisoformat(records[-1]["timestamp"])
            span_hours = (last_ts - first_ts).total_seconds() / 3600
            print(f"  {symbol} {tf_name}: {count} candles, {span_hours:.1f}h span")
            summary[symbol][tf_name] = {
                "count": count,
                "first": records[0]["timestamp"],
                "last": records[-1]["timestamp"],
            }

    # Write summary
    with open(OUTPUT_DIR / "_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    mt5.shutdown()
    print(f"\nDone. Data in {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    fetch_all()
