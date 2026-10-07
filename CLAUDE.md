# JARVIS — Claude Code entry point
Read-only multi-agent trade-signal system (LangGraph + MT5 + TimesFM). NEVER add order execution.
Session start: read `Memory.md` then `Task.md`. Consult by section only when needed:
- `PRD.md` (what/why) · `Architecture.md` (flow, structure, schemas, conventions) · `Design.md` (UI)
- `Backend_Schema.md` (DB tables/constraints) · `API_Integrations.md` (3rd-party + internal API; VERIFY items)
- `Security_Access.md` (roles, error boundaries, privacy, error protocol) · `AI_Guardrails.md` (LLM rules/gates)
- `Feature_Tickets.md` (ticket IDs/AC) · `Deployment.md` (run/ops)
Obey `Rules.md` (zero hallucination, verify before using any API/package, test before "done", small slices, update Memory.md/Task.md after each task). Right context of whatever is done so far in the project so that the coding agent gets the context when session is restarted.
Use `/compact` at ~60% context, `/clear` between phases.

## Agent skills

### Issue tracker

Issues and specs are tracked as local markdown files under `.scratch/<feature>/` in this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

The default triage vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and one `docs/adr/` at the repo root. See `docs/agents/domain.md`.
