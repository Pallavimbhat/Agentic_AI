# Labs 1–14 — integrated capability guide

All fourteen lab concepts are exposed through the same Academic AI Assistant on the main Course Organizer dashboard. The UI has one input and one submit action. There are no individual lab launch buttons.

See `DEMO_GUIDE.md` for demonstration prompts and `INTEGRATED_ARCHITECTURE.md` for the routing lifecycle.

## Structured input formats

- Lab 3 custom skill: `{"action":"create","name":"upper_text","description":"Uppercase text","operation":"uppercase"}`; run with `{"action":"run","name":"upper_text","input":"hello"}`.
- Lab 7 graph: `{"nodes":[{"id":"first","operation":"word_count","input":"hello world"},{"id":"second","operation":"uppercase","input":"agent","depends_on":["first"]}]}`.
- Lab 12 proposal: `{"diagnosis":"...","proposed_change":"...","rollback_plan":"...","privacy_scrubbed":true,"estimated_cost":10,"budget":100}`. A pending approval is a record for human decision only.
- Lab 13 accepts JSON readings, CSV with headers, or `key=value` lines. Supply a domain (`mechanical`, `civil`, or `electrical`) and site-approved thresholds for meaningful analysis.
- Lab 14 supports ticket create/list/get/update/close/triage actions. Tickets are scoped to the authenticated user's ID by the unified assistant.

## Execution truthfulness

For ordinary academic questions, the academic workflow uses Labs 1–8 concepts. Labs 9–14 are invoked only when a relevant request is made. The result marks unused capabilities as available rather than claiming they ran.

## Implementation boundaries

The connector registry is not a full official MCP SDK server; the swarm uses concurrent Python workers; research uses a local corpus; cloud operations is advisory; SDLC produces planning artifacts; governance does not execute production actions; engineering thresholds are illustrative. These are explicitly labelled in the UI/docs and must not be represented as capabilities beyond what is implemented.
