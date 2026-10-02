# JARVIS — Claude Code entry point
Read-only multi-agent trade-signal system (LangGraph + MT5 + TimesFM). NEVER add order execution.
Session start: read `Memory.md` then `Task.md`. Consult by section only when needed:
- `PRD.md` (what/why) · `Architecture.md` (flow, structure, schemas, conventions) · `Design.md` (UI)
- `Backend_Schema.md` (DB tables/constraints) · `API_Integrations.md` (3rd-party + internal API; VERIFY items)
- `Security_Access.md` (roles, error boundaries, privacy, error protocol) · `AI_Guardrails.md` (LLM rules/gates)
- `Feature_Tickets.md` (ticket IDs/AC) · `Deployment.md` (run/ops)
Obey `Rules.md` (zero hallucination, verify before using any API/package, test before "done", small slices, update Memory.md/Task.md after each task).
Use `/compact` at ~60% context, `/clear` between phases.
