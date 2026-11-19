# Integrated architecture and demonstration contract

The user-facing application has one Academic AI Assistant. Lab concepts are backend capabilities; there is no separate lab dashboard or per-lab launch control in the UI.

## Request lifecycle

1. Authenticate the user and resolve their role/user ID.
2. Classify the natural-language or structured request.
3. Route it to the appropriate lab capability or the academic workflow.
4. Invoke only relevant tools, skills, connectors, memory, graph or specialists.
5. Persist supported execution/memory/approval/ticket data in the agentic SQLite store.
6. Return a grounded answer, selected capability and execution trace.

## Lab-to-capability mapping

| Lab | Backend capability | Assistant invocation example |
|---|---|---|
| 1 | Agent-vs-chatbot and course lookup | Compare a chatbot and an agent for finding courses |
| 2 | Calculator/database/text tools | Calculate 125 * 8 |
| 3 | Versioned custom skills | List skills; structured create/run JSON |
| 4 | User-scoped persistent memory | Remember / recall |
| 5 | Connector registry | List available connectors |
| 6 | Runtime lifecycle | Show runtime events for calculating 25 + 17 |
| 7 | Dependency graph | Structured nodes JSON |
| 8 | Concurrent specialist workers | Parallel specialist analysis |
| 9 | Local-corpus research | Research a topic |
| 10 | Supplied-log diagnosis | Analyse supplied cloud logs |
| 11 | SDLC artifact generation | Generate an SDLC test plan |
| 12 | Governance and approval record | Structured proposal JSON |
| 13 | Engineering sensor analysis | CSV, JSON or key=value readings |
| 14 | Persistent helpdesk ticket workflow | Create/list/triage ticket |

## Trace truthfulness

A lab is marked as executed only when its capability handler is invoked for the request. For ordinary student academic requests, Labs 1–8 are used by the academic workflow; Labs 9–14 are marked `available_not_invoked` unless a relevant specialized request is routed to them. This avoids claiming that synthetic fixed examples ran for every question.

## Boundaries

- Lab 5: internal connector registry abstraction; not the full official MCP SDK/server transport.
- Lab 8: concurrent Python specialist workers; not independent LLM agents.
- Lab 9: local evidence corpus plus user-supplied sources; not live web research.
- Lab 10: log analysis/advice only; no live cloud changes.
- Lab 11: lifecycle planning artifacts; no production code deployment.
- Lab 12: approval records only; no production execution.
- Lab 13: illustrative thresholds; not certified engineering limits.

## User interface contract

The `/labs` showcase router is deliberately not mounted in the FastAPI application. The main dashboard contains one shared assistant form for student and professor accounts, plus a read-only capability map. Users do not launch labs individually. They demonstrate the concepts by entering requests in the same assistant and inspecting the resulting execution trace.
