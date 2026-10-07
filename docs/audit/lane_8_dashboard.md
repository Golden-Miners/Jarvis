# Audit Lane 8: Dashboard

## Summary
- **PASS**: 11
- **FAIL**: 3
- **UNVERIFIED**: 2
- **BLOCKERS**: 2

## Findings

### Layout & Component Accuracy (Compared against Dashboard_Layout.md)
1. **Top Bar**: PASS. Cycle status pill and SSE connection pill present. Actions block with theme toggle and user menu present.
2. **Nav Rail / Bottom Bar**: UNVERIFIED. (Could not visually inspect responsiveness in browser without Playwright permission).
3. **Brief Cards**: PASS. Verified via `OverviewPage.tsx`. Contains Qualified, Waiting, Open, Next Event, System Health.
4. **Instrument Tiles with NO_TRADE reasons**: PASS. Implemented using waiting count and reason variables.
5. **Signal Cards**: FAIL. Entry/SL/TP, RR, Confidence, Expiry, and Why section are present in `SignalCard.tsx` and `PriceBlock.tsx`. However, the **"Copy signal text format" button and string formatting are missing** entirely from the component.
6. **Pipeline Strip**: PASS/FAIL. The agent health dot matrix is partially implemented via `AgentMiniRow` in `OverviewPage.tsx`.
7. **Panels (News, Calendar, Agents)**: PASS. Layout implemented in `OverviewPage.tsx`.
8. **Recent Signals Table**: PASS. Implemented in `HistoryPage.tsx` with proper data columns.
9. **History Filters**: PASS. Implemented in `HistoryPage.tsx` (symbol and status dropdowns).
10. **Stats (Sample size & Low sample badge)**: PASS. Correctly verified in `StatsPage.tsx` (threshold `n<30` implemented).
11. **Login & Role-based UI**: PASS. `isOwner` checks present for Run Now button and Settings pages.

### Design & Interaction Constraints
12. **No charts, no trade buttons**: PASS. Only numerical grids and tiles are used for instruments and signals.
13. **Tailwind & Vite Setup**: PASS. Verified `index.css` uses Tailwind v4 properly (`@import "tailwindcss";`, `@theme` directives), and leftover Vite boilerplate CSS is removed.
14. **Fonts load**: PASS. `main.tsx` correctly imports `@fontsource` packages.
15. **Theme persistence**: PASS. The `index.html` sync script reads from localStorage properly and prevents FOUC.
16. **Live SSE updates**: UNVERIFIED. The backend could not start due to an import error (`ModuleNotFoundError: No module named 'jarvis'`), so live updating was untestable.
17. **No horizontal scroll**: UNVERIFIED (Visual check blocked).
18. **Axe-core scan (a11y)**: FAIL. Blocked from running Playwright to do an accessibility scan due to lacking Playwright browser binaries/permissions.

## Blockers
1. **Backend Initialization**: Running `uv run jarvis-api` or `python -m jarvis.api.main` fails with `ModuleNotFoundError: No module named 'jarvis'`, indicating that the environment is not synced or installed (`uv sync` required, but outside permission scope to fetch network dependencies without approval).
2. **Visual & A11y Testing**: Permission to use Playwright for browser interactions was blocked, preventing automated axe-core scanning and capturing visual screenshot evidence across different resolutions (390px, 768px, 1440px).

## Evidence
- Code excerpts reviewed and validated (see workspace).
- (Textual evidence file saved as a placeholder in `docs/audit/evidence/screens/unverified_visuals.txt` due to blocked browser access).
