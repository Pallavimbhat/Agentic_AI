# Professor demonstration guide — one assistant, 14 integrated capabilities

## Start the application

Run `START_APPLICATION.bat` or start Uvicorn from the project root. Open `http://127.0.0.1:8002/` and sign in as either the demo student or professor. The dashboard has one Academic AI Assistant and fourteen guided Live Lab Demonstration cards. Each card fills the assistant input and runs that lab through the same assistant; a separate lab showcase page is not used.

## Explain the architecture

The user submits one natural-language request. The unified orchestrator interprets the intent, routes to the relevant capability, invokes the necessary tools/skills/memory/connectors/workflow nodes or specialist workers, and returns an answer plus an execution trace. The trace only lists components actually invoked.

## Demonstrate the 14 capabilities from the dashboard

Click `Run Lab 1` through `Run Lab 14` to run each prepared prompt, or click `Run complete 14-lab demo` to execute the full demonstration suite. You can edit the populated prompt before submitting it.

1. **Agent vs Chatbot:** `Compare a chatbot and an agent for finding courses.`
2. **Tool-Using Agent:** `Calculate the average of 85, 90, 75 and 95.`
3. **Reusable Skills:** `List skills.` For a custom skill, send `{"action":"create","name":"upper_text","description":"Uppercase text","operation":"uppercase"}`; then send `{"action":"run","name":"upper_text","input":"hello"}`.
4. **Memory:** `Remember that I prefer concise explanations.` Then ask `What do you remember about my preferences?`
5. **Connectors:** `List available connectors.`
6. **Runtime:** `Show runtime events for calculating 25 + 17.`
7. **Node graph:** send `{"nodes":[{"id":"a","operation":"word_count","input":"hello world"},{"id":"b","operation":"uppercase","input":"agent","depends_on":["a"]}]}`.
8. **Parallel swarm:** `Run parallel specialist analysis on this text: student scores improved but one assignment failed.`
9. **Deep research:** `Research artificial intelligence applications in education.`
10. **Cloud operations:** `Analyse these cloud logs: INFO service started; ERROR database connection timeout.`
11. **SDLC:** `Generate an SDLC test plan for a library management system.`
12. **Governance:** send JSON with `diagnosis`, `proposed_change`, `rollback_plan`, `privacy_scrubbed: true`, `estimated_cost` and `budget`.
13. **Engineering:** `Analyse civil engineering sensor readings: crack_width_mm=0.5` followed by `displacement_mm=12` on a new line.
14. **Capstone:** `Create ticket for campus portal login failure.`

## What to show on screen

After each prompt, expand **Execution trace** to show the lab capability, component, status and selected tool where applicable. Expand **Detailed execution output (JSON)** to show arguments, actual result and events.

## Important limitations to disclose

- Lab 5 is an internal connector registry, not a full official MCP SDK/server transport.
- Lab 8 uses concurrent Python specialist workers, not independent LLM agents.
- Lab 9 uses a local evidence corpus and user-supplied evidence, not live web crawling.
- Lab 10 diagnoses logs and recommends remediation; it does not change cloud infrastructure.
- Lab 11 creates SDLC planning/testing artifacts; it does not deploy production code.
- Lab 12 records governance approvals; it does not execute production actions.
- Lab 13 uses illustrative thresholds that are not certified engineering limits.
