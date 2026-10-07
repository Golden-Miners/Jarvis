# Dashboard Layout Spec — JARVIS
Extends `Design.md` (tokens, fonts, palette stay the same). Adapts the common 5-zone dashboard pattern (top navbar, sidebar, stats cards, main content, widgets/panels, data table, quick actions) to a **signal-intelligence** product. **No charts. No trade buttons.**

## 1. Adaptation of the reference pattern
| Reference zone | JARVIS equivalent |
|---|---|
| Top navbar (logo, search, bell, profile) | Command bar: logo, cycle status, live indicator, filter/search, alerts, theme, role/profile |
| Sidebar nav | Slim nav rail: Overview, Signals, Instruments, News & Macro, Agents, History, Stats, Settings (OWNER) |
| Stats cards (Users, Orders, Revenue) | **Brief cards**: Qualified setups, Waiting, Open signals, Next high-impact event, System health |
| Main content (chart + donut) | **Instrument strip + Signal feed** (cards, numbers, badges; replaces charts) |
| Widgets/panels | News & Macro, Event calendar, Agent roster, Cycle pipeline |
| Recent orders table | **Recent signals table** with outcome and R-multiple |
| Quick actions | Run now (OWNER), Copy signal, Filters, Export CSV (OWNER), Theme |
Deliberate differences: dark HUD, not pastel multi-colour cards. Colour is semantic only: green = BUY, red = SELL, amber = warning/blackout, cyan = system/primary, gold = XAUUSD accent. Cards stay neutral surfaces.

## 2. Grid & breakpoints
| Breakpoint | Layout |
|---|---|
| ≥1280 desktop | Nav rail 232px (collapsible to 72px) + content max 1440px; 12-col grid, 16px gap; main 8 cols + right rail 4 cols |
| 768–1279 tablet | Rail collapsed to icons (72px); main 12 cols; right rail widgets move below the signal feed in 2 columns |
| <768 mobile | No rail; sticky top bar (56px) + bottom tab bar (64px + safe-area); single column |
Spacing 8px grid; card radius 16, chip radius 10; page padding 24 (desktop) / 16 (mobile). Safe-area insets honoured.

## 3. Desktop wireframe (Overview)
```
┌────────┬──────────────────────────────────────────────────────────────────────────┐
│ ◉JARVIS│ ◉ Cycle: IDLE · next 14:15 · ● Live      [ Filter ⌕ ]  🔔  ☾  [Owner ▾]   │  Top bar 64px
│        ├──────────────────────────────────────────────────────────────────────────┤
│ ▣ Over-│ JARVIS BRIEF  "2 setups qualified, 3 waiting. Next: FOMC in 2h 10m."      │  Brief line
│   view │ ┌────────────┬────────────┬────────────┬─────────────┬──────────────────┐ │
│ ◈ Sign-│ │ QUALIFIED  │ WAITING    │ OPEN       │ NEXT EVENT  │ SYSTEM HEALTH    │ │  Brief cards
│   als  │ │ 2          │ 3          │ 2          │ FOMC 2h10m  │ 16/17 agents ●   │ │
│ ◎ Instr│ └────────────┴────────────┴────────────┴─────────────┴──────────────────┘ │
│ ✉ News │ ┌─ XAUUSD ★ (wide) ─┬ XAGUSD ┬ BTCUSD ┬ ETHUSD ┬ USOUSD ┐   Instrument strip│
│ ☰ Agent│ │ Iron Man · SELL   │ Waiting│ BUY    │ Waiting│ Blackout│                  │
│ ⏱ Histo│ │ 0.77 ring · fresh │ reason │ 0.62   │ reason │ reason  │                  │
│ ▤ Stats│ └───────────────────┴────────┴────────┴────────┴────────┘                  │
│        │ ┌───────────── MAIN (8 cols) ──────────┐ ┌──────── RIGHT RAIL (4) ───────┐ │
│ ⚙ Sett.│ │ Cycle pipeline: Vision→Fury→Instr…   │ │ News & Macro (impact meters)  │ │
│        │ │ Active signals (feed of cards)       │ │ Event calendar + blackouts    │ │
│        │ │  ┌ SignalCard ───────────────────┐   │ │ Agent roster (grouped)        │ │
│        │ │  │ XAUUSD SELL  conf 0.77  ⏱42m  │   │ │ Quick actions                 │ │
│        │ │  │ Entry  SL  TP  RR  [Copy] [Why▾]│ │ └───────────────────────────────┘ │
│        │ │  └───────────────────────────────┘   │                                    │
│        │ ├───────────── FULL WIDTH ─────────────┤                                    │
│        │ │ Recent signals table  (View all →)   │                                    │
│        │ └──────────────────────────────────────┘                                    │
├────────┴──────────────────────────────────────────────────────────────────────────┤
│ Signals are informational, not financial advice.                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 4. Zone specifications

### 4.1 Top bar (64px, glass, sticky)
Left: logo mark + "JARVIS" (+ subtitle hidden <1024). Centre: **cycle status pill** (IDLE/RUNNING/DEGRADED/FAILED, StatusRing, "last run 3m ago · next 14:15") from `cycles[0]`, and **connection pill** (Live / Reconnecting / Offline from SSE). Right: filter/search (symbol, strategy, status; `/` focuses), alerts bell (degraded agents, new TRADE signals, last 20, unread dot), theme toggle, profile menu (username, role badge OWNER/VIEWER, sign out). Mobile: logo, cycle pill, bell, overflow menu.

### 4.2 Nav rail (desktop/tablet)
Items: Overview, Signals, Instruments, News & Macro, Agents, History, Stats, Settings (OWNER only). Active item: arc-cyan left bar + surface-2. Collapsed state shows icons + tooltips. Bottom of rail: environment badge (`PAPER`/`DEMO`), version, "Signals only — no execution" chip.

### 4.3 Brief line + Brief cards
Brief line (Jarvis voice, generated from real data, no LLM needed): `"{n} setups qualified, {m} waiting. Next high-impact: {event} in {t}."` Cards (5, equal width, neutral surface, big mono number, small label, delta/subtext):
1. **Qualified** – count of TRADE signals this cycle (buy/sell split chips).
2. **Waiting** – count of NO_TRADE instruments; subtext = top reason.
3. **Open** – OPEN signals; subtext = nearest expiry.
4. **Next event** – name + countdown; amber if blackout active.
5. **System health** – agents OK/total; red dot + banner if any critical agent failed.
No coloured pastel backgrounds; a 2px top accent line only.

### 4.4 Instrument strip (5 tiles)
XAUUSD tile ×1.6 width with gold accent; others equal. Tile anatomy:
```
[Agent avatar] Iron Man            ● fresh 2m
XAUUSD                         [SELL]  chip
Decision: TRADE | WAITING
Confidence ring 0.77     Price (last)  4151.20
Reason (if waiting): "News blackout until 14:30"
Strategies aligned: 3/5  ▮▮▮▯▯ (pips, not a chart)
```
Click → Instrument detail page. States: TRADE (direction border-left), WAITING (neutral), STALE (amber dot "data 12m old"), DEGRADED (warn icon), DISABLED (dimmed). Mobile: horizontal scroll-snap row.

### 4.5 Cycle pipeline strip
Five steps: Vision → Nick Fury → Instruments (×5) → Jarvis → Coulson. Each: icon, state (pending/running/ok/degraded/error), latency ms. Running step pulses in arc colour. Collapsible on mobile (single line "Step 3/5: Instruments").

### 4.6 Signal feed (main)
Sorted: OPEN first (newest), then recent resolved (collapsed). Filter chips: All · BUY · SELL · Symbol · Strategy. Only `TRADE` signals in "Active signals"; NO_TRADE appear in tiles and in History.
**SignalCard anatomy**
```
Header:  [XAUUSD] [SELL chip]  conf ring 0.77   status chip OPEN   ⏱ expires 42m
Prices:  ENTRY 4151.20 | SL 4167.91 (−16.7 · 1.1 ATR) | TP 4117.77 (+33.4 · 2.2 ATR) | RR 2.0
Proportion bar (optional, static SL—Entry—TP, not a chart)
Meta:    Strategy: Hawkeye (SMC) · Aligned 3/5 · Structure H1/H4 DOWN · Forecast agrees · News neutral
Actions: [Copy signal]  [Why ▾]  [Mark taken/skipped] (P2)
Why ▾:   Rationale (≤5 bullets) · Score breakdown bars · Agent verdict list (aligned/neutral/veto/error) · Risk notes · Risks (≤3)
Footer:  "Informational, not financial advice."
```
Copy signal text: `XAUUSD SELL | Entry 4151.20 | SL 4167.91 | TP 4117.77 | RR 2.0 | Conf 77% | expires 14:57 UTC | not financial advice`. Numbers use symbol digits; mono, tabular.

### 4.7 Right rail widgets
1. **News & Macro** – impact meter 0–10 (segmented 10-pip bar), bias chip, source · time, symbols affected; max 6 items, "View all". Empty states: "No news source configured" vs "No relevant news right now".
2. **Event calendar** – next 5 events: time (local, UTC on hover), currency, importance dots, countdown; blackout windows shown as amber badges "Blackout 14:00–14:30".
3. **Agent roster** – grouped: Core (Jarvis, Vision, Strange, Fury, Quicksilver, War Machine, Coulson), Instruments (5), Strategies (5). Row: initial avatar, name, role, health dot, last latency, degraded reason on hover/expand.
4. **Quick actions** (2×2 tiles like the reference): **Run now** (OWNER, cooldown 60s countdown), **Copy latest signal**, **Export CSV** (OWNER), **Theme**. No trade actions.

### 4.8 Recent signals table (full width)
Columns: Time · Symbol · Dir · Entry · SL · TP · RR · Conf · Strategy · Status · R-multiple. Sort by time; row click opens detail drawer; sticky header; zebra off, hairline rows; 10 rows + "View all". Mobile: card list instead of table.

## 5. Pages / routes
| Route | Content | Role |
|---|---|---|
| `/login` | Username/password, error states, lockout notice | public |
| `/` Overview | Sections 4.3–4.8 | VIEWER+ |
| `/signals` | Full feed + filters + detail drawer | VIEWER+ |
| `/instruments/:symbol` | Header (agent hero, price, session, volatility regime, trend per TF as chips), latest decision + reason, candidates from each strategy (table: strategy, dir, entry/SL/TP, conf, risk valid?), structure summary (key levels as list), forecast summary (direction, strength, q10/q90 numbers), news for symbol, signal history for symbol | VIEWER+ |
| `/news` | Full news list with filters, calendar, blackout windows | VIEWER+ |
| `/agents` | Roster with run history (last 20 runs, status, latency, tokens, error code) | VIEWER+ |
| `/history` | Filterable table (symbol, strategy, decision, status, date range), pagination, CSV export | VIEWER+ / export OWNER |
| `/stats` | Number cards by overall / strategy / symbol: signals, win rate, avg R, expectancy, avg hold; **sample size always shown; "low sample (n<30)" badge**; confidence calibration table (bucket vs actual hit rate) | VIEWER+ |
| `/settings` | Instruments enable/disable, thresholds view (read-only for now), users, audit log view | OWNER |

## 6. Mobile layout (<768)
```
┌──────────────────────────┐
│ ◉ JARVIS   ● IDLE  🔔  ⋯ │ top 56px
├──────────────────────────┤
│ Brief: 2 qualified, 3 …  │
│ [Q 2][Wait 3][Open 2] →  │ scroll-snap cards
│ ◂ XAUUSD ▸ XAG BTC ETH … │ tile row
│ Active signals           │
│ ┌ SignalCard (stacked) ┐ │
│ Entry / SL / TP grid 3×1 │
│ └──────────────────────┘ │
├──────────────────────────┤
│ Signals News Agents Hist Stats │ bottom tab bar
└──────────────────────────┘
```
Prices in a 3-column grid at 20px mono; "Why" opens as a bottom sheet; tables become cards; run-now lives in the overflow menu; touch targets ≥44px.

## 7. States (every panel)
| State | Behaviour |
|---|---|
| Loading | Skeletons matching final shape (no spinners over content) |
| Empty | Jarvis voice, e.g. "No qualified setups. Jarvis is patient." plus top waiting reasons |
| Error | Per-panel ErrorBoundary with retry; page stays usable |
| Degraded | Amber banner under top bar: "News feed unavailable. Confidence lowered on all signals." with agent links |
| Offline/SSE down | Pill "Reconnecting…", fall back to 30s polling, banner after 60s |
| Stale | Tile + card show age; >2 cycles old → amber, signals past expiry greyed with EXPIRED |
| Forbidden | 403 page for VIEWER on OWNER routes |

## 8. NO_TRADE reason mapping (plain language)
`NEWS_BLACKOUT` "News blackout until {t}" · `CONFLICT` "Strategies disagree" · `RR_LOW` "Risk/reward below minimum" · `SCORE_LOW` "Not enough confluence" · `MIN_ALIGNED` "Fewer than 2 strategies aligned" · `DATA_STALE` "Market data stale" · `RISK_INVALID` "Risk check failed" · `FORECAST_OPPOSITE` "Forecast disagrees" · `DUPLICATE_OPEN` "Signal already open" · `DAILY_CAP` "Daily signal limit reached" · `DEGRADED:{agent}` "{agent} unavailable".

## 9. Data mapping
| UI | Endpoint / SSE | Key fields |
|---|---|---|
| Top bar cycle pill | GET /cycles, SSE `cycle.status` | status, started_at, finished_at |
| Brief cards | GET /signals, /instruments, /calendar | decision counts, next event |
| Instrument tiles | GET /instruments | latest decision, reason, confidence, freshness |
| Signal feed | GET /signals, SSE `signal.created/updated` | prices, rr, confidence, verdicts |
| Pipeline strip | GET /agents/status, SSE `agent.health` | agent, status, latency |
| News/calendar | GET /news, /calendar | impact, bias, events, blackout |
| Table/History | GET /signals?filters&cursor | outcome, r_multiple |
| Stats | GET /stats | per strategy/symbol with n |
All via typed hooks; cache and invalidate on SSE events.

## 10. Interaction, motion, shortcuts
Transitions 150–250ms ease-out; new signal slides in with a one-time arc glow (2s); StatusRing pulse only while running; all disabled under reduced motion. Shortcuts: `R` run (OWNER), `T` theme, `/` filter, `G then S/N/A/H` go to Signals/News/Agents/History, `?` help overlay. Toasts for run started/finished, new TRADE signal, errors (aria-live polite).

## 11. Accessibility & quality bar
WCAG AA contrast (muted text ≥ 4.5:1), min text 12px (labels) / 14px (body), direction never colour-only (arrow icon + text), full keyboard navigation, visible focus rings (arc), landmarks (header, nav, main, aside), tabs/drawers/menus via Radix, skip-link, aria-live for signal arrival, tabular numerals, local time with UTC tooltip.

## 12. Implementation order & acceptance
1. Shell: top bar, nav rail/bottom bar, routes, auth guard → *AC:* role-gated routes work, responsive at 390/768/1440.
2. Overview: brief + cards + instrument strip + signal feed → *AC:* shows real NO_TRADE reasons.
3. Right rail widgets + pipeline strip → *AC:* updates via SSE without reload.
4. Table + History + Instrument detail → *AC:* filters, pagination, drawer.
5. Stats + calibration, Settings, Login → *AC:* sample-size warnings, OWNER-only controls hidden for VIEWER.
6. Polish: skeletons, empty/error/degraded states, shortcuts, a11y pass → *AC:* axe: 0 serious/critical; Playwright screenshots at 3 widths × 2 themes reviewed.
