# Lane 5: Signal Correctness Audit Report

## 1. Execution of Full Cycle on Real MT5 Data

A full strategy analysis cycle was executed across the 5 configured symbols (XAUUSD, XAGUSD, BTCUSD, ETHUSD, USOUSD) using the real MT5 candle fixtures provided in `data/real_fixtures`. 

### Strategy Firing Frequency (1 cycle snapshot):
- **Hawkeye (FVG/OB):** 5 candidates found
- **Black Widow (EMA Pullback):** 2 candidates found
- **Falcon (Breakout):** 0 candidates
- **Ant-Man (Mean Reversion):** 0 candidates
- **Wasp (Supply/Demand Fib):** 0 candidates

*(Note: Run over 1 bar cycle. Backtesting replay script not present to generate 10+ signals easily across history, so 7 total candidates were manually verified from the latest bar).*

## 2. Hand-Check Verification of Produced Decisions

7 decisions (5 TRADE, 2 NO_TRADE) were successfully verified by manual recomputation from the cycle output.

### 1. XAUUSD (hawkeye) - SELL (TRADE)
- **Levels:** Entry=4151.20, SL=4167.8854, TP=4117.82921
- **Order:** TP < Entry < SL (Correct for SELL)
- **RR Math:** Risk = 16.6854, Reward = 33.3708, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 8.0285, SL Dist/ATR = 16.6854 / 8.0285 = 2.078 (Correct)
- **Lot size:** 0.05 lot 

### 2. XAUUSD (black_widow) - BUY (TRADE)
- **Levels:** Entry=4142.28, SL=4135.83, TP=4155.18
- **Order:** SL < Entry < TP (Correct for BUY)
- **RR Math:** Risk = 6.45, Reward = 12.90, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 8.0285, SL Dist/ATR = 6.45 / 8.0285 = 0.803 (Correct)
- **Lot size:** 0.15 lot

### 3. XAGUSD (hawkeye) - SELL (TRADE)
- **Levels:** Entry=65.3295, SL=65.58874, TP=64.81103
- **Order:** TP < Entry < SL (Correct)
- **RR Math:** Risk = 0.25924, Reward = 0.51847, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 0.1656, SL Dist/ATR = 1.565 (Correct)
- **Lot size:** 0.07 lot

### 4. BTCUSD (hawkeye) - SELL (NO_TRADE - Invalid Spread)
- **Levels:** Entry=84420.675, SL=84983.716, TP=83294.592
- **Order:** TP < Entry < SL (Correct)
- **RR Math:** Risk = 563.041, Reward = 1126.082, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 286.18, SL Dist/ATR = 1.967 (Correct)
- **Spread:** Actual Spread = 2065 pts. Risk cap = 1000 pts. Verdict: REJECTED. (Correct)

### 5. ETHUSD (hawkeye) - BUY (TRADE)
- **Levels:** Entry=2709.53, SL=2681.588, TP=2765.412
- **Order:** SL < Entry < TP (Correct)
- **RR Math:** Risk = 27.941, Reward = 55.882, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 14.774, SL Dist/ATR = 1.891 (Correct)
- **Lot size:** 3.57 lot

### 6. USOUSD (hawkeye) - BUY (TRADE)
- **Levels:** Entry=94.5855, SL=93.98904, TP=95.77842
- **Order:** SL < Entry < TP (Correct)
- **RR Math:** Risk = 0.59646, Reward = 1.19292, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 0.3920, SL Dist/ATR = 1.521 (Correct)
- **Lot size:** 1.67 lot

### 7. USOUSD (black_widow) - SELL (NO_TRADE - Invalid SL Dist)
- **Levels:** Entry=94.962, SL=95.137, TP=94.612
- **Order:** TP < Entry < SL (Correct)
- **RR Math:** Risk = 0.175, Reward = 0.350, RR = 2.0 (Correct)
- **ATR:** M15 ATR = 0.3920, SL Dist/ATR = 0.446 (Correct)
- **Risk bounds:** minimum_sl_atr_multiple = 0.5. Actual = 0.446. Verdict: REJECTED. (Correct)

## 3. Flagged Formulas & Assumptions (From Memory.md)
The following formulas are implemented but marked as "subject to review" by a domain expert:
1. **Wilder ATR:** Assumes standard 14-period exponential smoothing, requiring verification on exact weighting.
2. **Swing Pivots:** Assumes standard left/right n-bar lookbacks (typically 3 or 5 bars) to identify highs and lows.
3. **BOS/CHoCH:** Assumes a strict "close-cross" (the candle must close beyond the swing pivot level, not just wick past it).
4. **FVG (Fair Value Gap):** Assumes a 3-candle pattern where wick 1 and wick 3 do not overlap.
5. **Order Blocks:** Assumes the opposite-colored candle preceding a strong impulsive move.
6. **Zone Tolerance:** Assumes an arbitrary percentage or ATR-based buffer around historical price zones.
7. **Explicit-anchor Fib:** Relies on exact recent major swing high/low points, which may lag dynamic market interpretation.

## 4. Provisional / Unverified Config Values
The following config items are explicitly marked as provisional or require broker verification:
- **`config/sessions.yaml`:** Trading windows (LONDON, NEW_YORK, ASIAN, CRYPTO_24_7) are provisional and require broker server-time alignment.
- **`config/instruments.yaml`:** ATR multipliers and session lists are provisional.
- **`config/risk.yaml`:** Risk limits (`minimum_sl_atr_multiple: 0.5`, `maximum_sl_atr_multiple: 3.0`, `maximum_spread_points: 1000.0`) are provisional.
- **`config/jarvis.yaml`:** Scoring weights (`w_strategy`, `w_structure`, etc.) and `minimum_rr` are provisional.
- **`config/strategies.yaml`:** All internal strategy parameters (lookbacks, FVG min sizes, tolerances) are placeholders.
- **Tick Value & MT5 UTC:** `trade_tick_value` account currency interpretation and MT5 broker server-time vs UTC conversion are UNVERIFIED.

## Conclusion & Blockers
- **PASS:** 7 decision verifications (ordering, RR math, ATR distances, risk rule filters like spread/SL bounds).
- **UNVERIFIED:** 3 decisions (unable to easily reach 10 decisions due to limited one-bar firing; need a replay loop on historical bars).
- **UNVERIFIED:** MT5 server time to UTC conversion & lot size tick value correctness against specific broker specs.
- **BLOCKERS:** None for this lane, but TimesFM takes significant time to download/load in a fresh environment which affects pipeline start.
