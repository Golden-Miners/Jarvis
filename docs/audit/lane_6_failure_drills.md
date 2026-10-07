# Lane 6: Failure Drills

## Status Summary
- **PASS**: 0
- **FAIL**: 0
- **UNVERIFIED**: 9
- **BLOCKERS**: The project dependencies could not be correctly invoked in the current test environment (ModuleNotFoundErrors for sqlmodel, feedparser, langchain_core etc. when running `pytest`). The `MockProvider` tests were observed statically but a full drill of the main graph was unverified due to the inability to execute tests fully without the correct environment.

## Drills
1. **MT5 not connected**: UNVERIFIED. (Requires testing `MT5Provider` connection exception bubbling up to `instrument_graph` and degrading).
2. **Symbol missing**: UNVERIFIED.
3. **Stale or NaN candles**: UNVERIFIED.
4. **News feeds down**: UNVERIFIED.
5. **Calendar down**: UNVERIFIED.
6. **LLM timeout / invalid schema / auth failure**: UNVERIFIED.
7. **TimesFM load or inference failure**: UNVERIFIED.
8. **DB write failure**: UNVERIFIED.
9. **One instrument subgraph raising**: UNVERIFIED.

## Restart Recovery & Weekend/Market-Closed Behaviour
- **Restart Recovery**: UNVERIFIED.
- **Market-Closed**: UNVERIFIED.

## Conclusion
Due to environment constraints, the readiness drills could not be reliably executed. The evidence must be obtained from a fully configured environment or a functional CI pipeline.
