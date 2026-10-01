# PRD — JARVIS (Multi-Agent Trade Signal Intelligence System)

## 1. What we are building
JARVIS is a LangGraph-based multi-agent system that reads market data from MetaTrader 5 (MT5), analyses market structure, news and TimesFM forecasts, runs several trading strategies per instrument, and outputs **trade signals** (entry, SL, TP, confidence, rationale) to a web dashboard.
**JARVIS NEVER places, modifies or closes trades. Signals only. Read-only MT5 access.**

## 2. Problems solved
- Manual multi-timeframe, multi-instrument analysis is slow and inconsistent.
- Strategies, news and forecasts are analysed in isolation; no single confluence view.
- Emotional / undisciplined decisions; no audit trail of why a setup was taken or skipped.

## 3. Target user
One discretionary trader (the owner) who executes manually. Primary instrument XAUUSD; then XAGUSD, BTCUSD, ETHUSD, USOUSD (broker symbol names/suffixes mapped in config).

## 4. Features
| # | Feature | Priority |
|---|---------|----------|
| F1 | MT5 read-only data ingestion (OHLCV, spread, symbol info; M5/M15/H1/H4/D1) | P0 |
| F2 | Market structure analysis (swings, BOS/CHoCH, trend, S/R, sessions, ATR/volatility regime) | P0 |
| F3 | One instrument agent per symbol, with its own profile (volatility, sessions, ATR multipliers) | P0 |
| F4 | Strategy agents (SMC/ICT, trend-pullback, breakout/momentum, mean-reversion, supply-demand/Fib) | P0 |
| F5 | News & macro agent: calendar + headlines → impact score, bias, blackout windows | P1 |
| F6 | TimesFM forecast agent: quantile forecasts as a supporting input | P1 |
| F7 | Risk agent: SL/TP validation, R:R, ATR sanity, spread check, suggested lot size from user-set risk % | P0 |
| F8 | Supervisor (Jarvis): weighted confluence → TRADE / NO-TRADE + entry/SL/TP + rationale | P0 |
| F9 | Signal store + hypothetical outcome tracking (did TP or SL hit first) | P1 |
| F10 | Dashboard: live signals, per-agent verdicts, news panel, signal history, performance stats (no charts) | P0 |
| F11 | Optional alerts (Telegram/desktop) | P2 |

## 5. Agent roster
| Agent | Role |
|-------|------|
| **Jarvis** | Supervisor, final decision |
| **Vision** | Data agent (MT5 ingestion, caching, validation) |
| **Doctor Strange** | Market structure & multi-timeframe analysis |
| **Nick Fury** | News & macro impact |
| **Quicksilver** | TimesFM forecasting |
| **Iron Man** | XAUUSD instrument agent |
| **Captain America** | XAGUSD instrument agent |
| **Thor** | BTCUSD instrument agent |
| **Hulk** | ETHUSD instrument agent |
| **Black Panther** | USOUSD instrument agent |
| **Hawkeye** | Strategy: SMC/ICT (liquidity sweep, order block, FVG) |
| **Black Widow** | Strategy: trend + pullback (EMA/structure) |
| **Falcon** | Strategy: breakout / momentum |
| **Ant-Man** | Strategy: mean reversion / range |
| **Wasp** | Strategy: supply-demand zones + Fibonacci |
| **War Machine** | Risk & SL/TP validation |
| **Coulson** | Signal logger & outcome tracker |

## 6. Success metrics
- End-to-end cycle (all 5 instruments) < 60 s excluding LLM latency spikes.
- 100% of signals carry entry, SL, TP, RR, confidence, per-agent evidence.
- Zero order-execution code paths (enforced by test).
- Forward-test win rate / expectancy tracked per strategy and per instrument.

## 7. Non-goals
Order execution, portfolio management, chart rendering, HFT, financial advice. Signals are informational; trading carries risk.

## 8. Constraints
- Python 3.11+, LangGraph, MT5 Python package (Windows-native; on macOS/Linux use Wine or a bridge — see Architecture).
- Token/cost efficiency: deterministic code for numbers, LLM only for news interpretation and rationale.
