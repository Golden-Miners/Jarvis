# JARVIS

A read-only multi-agent market intelligence system that turns market data, news, and forecasts into trade **Signals**. Signals are advisory: the system never executes trades.

## The cycle and its artifacts

**Cycle**:
One complete run of the system, from market-data fetch through strategy evaluation to signal emission (or explicit no-trade) and outcome tracking. Runs on M15 candle close or manually.
_Avoid_: run, iteration, tick

**Strategy**:
One of five independent evaluation methods (Hawkeye, Black Widow, Falcon, Ant-Man, Wasp) that judges an instrument within a cycle and submits a verdict.
_Avoid_: indicator, model, bot

**Verdict**:
A single strategy's judgment on an instrument in a cycle — LONG, SHORT, or WAIT — which the supervisor aggregates into a signal when enough strategies agree.
_Avoid_: vote, opinion, score

**Signal**:
A trade recommendation emitted for an instrument — direction, entry, stop, target, and reasoning — backed by agreeing verdicts. Advisory only; never executed.
_Avoid_: trade, order, alert

**Outcome**:
The final resolution of a past signal against subsequent price data: target hit, stop hit, or expired, with the best and worst excursions recorded.
_Avoid_: result, exit, payoff

## News suppression

**Blackout Window**:
A period during which signal generation is suppressed for affected instruments following high-impact news.
_Avoid_: news halt, freeze period

## Reliability and validation

**Degraded Mode**:
The defined behavior when a dependency is unavailable, per the per-dependency contract: a market-data outage fails the cycle; missing forecasts or news proceed without them.
_Avoid_: fallback mode, safe mode

**Failure Drill**:
A test that simulates one dependency outage and asserts the degraded-mode contract holds.
_Avoid_: chaos test, stress test

**Kill Switch**:
A guardrail that halts new cycles — tripped manually or automatically on a guardrail violation — while existing open signals continue to resolve so the outcome record stays complete.
_Avoid_: emergency stop, circuit breaker

**Backtest-lite**:
A smoke-grade replay of recorded market history through the full pipeline with the language model mocked, asserting strategies fire and outcomes resolve — explicitly not statistical proof of edge.
_Avoid_: backtest (unqualified), simulation

**Forward Test**:
A time-boxed paper run (two weeks, M15) with configuration frozen at start and all pre-flight gates passed, producing signals and tracked outcomes without execution.
_Avoid_: demo run, paper trading (unqualified)
