# Design — JARVIS Dashboard

## 1. Vision
A calm, premium command-centre: "Stark HUD" refined — dark, glassy, high-contrast numerics, restrained neon accents. Information-dense but uncluttered. **No charts.** Numbers, badges, cards, timelines and status rings only. Mobile-responsive (phone-first reading of signals).

## 2. Color palette (CSS tokens)
| Token | Dark (default) | Light |
|-------|----------------|-------|
| --bg | #0A0D14 | #F5F7FB |
| --surface | #121826 | #FFFFFF |
| --surface-2 | #1A2234 | #EEF2F8 |
| --border | #263149 | #D9E0EC |
| --text | #E8EEF9 | #0F1729 |
| --muted | #8FA0BF | #5B6B86 |
| --arc (primary, Jarvis cyan) | #38E1FF | #0891B2 |
| --gold (XAU accent) | #F5C451 | #B7860B |
| --buy | #2EE59D | #0E9F6E |
| --sell | #FF5C7A | #D92D50 |
| --warn | #FFB020 | #B45309 |
| --neutral | #7C8AA5 | #64748B |
Rules: buy=green, sell=red, only these carry directional meaning. Accent glow max 12% opacity.

## 3. Typography
- Headings/UI: **Space Grotesk** (600/500)
- Body: **Inter** (400/500)
- Numbers/prices/IDs: **JetBrains Mono** (tabular-nums)
Scale: 12 / 14 / 16 / 20 / 28 / 40 px. Prices 20–28px mono, SL/TP 16px mono.

## 4. Visual style
8px grid, radius 16 (cards) / 10 (chips), 1px borders, subtle backdrop-blur glass on top bar, soft inner shadow, gentle arc-reactor pulse on the Jarvis status ring. Motion: 150–250 ms ease-out, fade/slide-up on new signal; respect `prefers-reduced-motion`.

## 5. Layout
- **Top bar:** JARVIS wordmark + status ring (cycle running/idle), last run time, "Run now", theme toggle.
- **Hero strip:** 5 instrument tiles (XAUUSD featured/larger). Each: symbol, agent name (Iron Man…), decision badge (TRADE/NO TRADE), direction chip, confidence ring.
- **Main column — Signals:** Signal card = Entry / SL / TP (mono), RR, confidence, expiry countdown, status chip, expandable "Why" (Jarvis rationale + score breakdown bars + agent verdict list).
- **Side column:** News & Macro panel (Nick Fury): impact meter 0–10, upcoming events with blackout badges. Agent Roster panel: avatar initial, role, last-run latency, health dot.
- **History tab:** table of past signals with outcome (TP/SL/Expired), filters by symbol/strategy. **Stats tab:** win rate, avg RR, expectancy per strategy/instrument as number cards.
- Mobile: single column, tiles horizontal scroll, bottom tab bar.

## 6. Components
StatusRing, InstrumentTile, DecisionBadge, DirectionChip, PriceBlock (Entry/SL/TP), ConfidenceRing, ScoreBars, AgentRow, NewsItem, ImpactMeter, SignalCard, HistoryTable, StatCard, EmptyState, ErrorBanner (degraded agents), Toast.

## 7. States & a11y
Loading skeletons; empty ("No qualified setups — Jarvis is patient"); degraded banner when an agent failed; WCAG AA contrast; keyboard focus rings in --arc; aria-labels on badges; colour never the only signal (icons/arrows with text).

## 8. Voice
Concise, confident, Jarvis-like: "XAUUSD — BUY setup qualified. 3 of 5 strategies aligned." Always show footer: "Signals are informational, not financial advice."

## 9. Stack notes
React + Vite + TS + Tailwind (tokens above as CSS variables) + shadcn/ui primitives + lucide-react icons. Data via REST + SSE. Use the `frontend-design` skill and keep to this spec.
