# Professor Demonstration — One Assistant, Fourteen Integrated Labs

## Start
1. Run `START_APPLICATION.bat` from this folder (or activate the same Python environment and run `python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002`).
2. Open `http://127.0.0.1:8002/` and sign in with the professor account already configured in your database.
3. Use the fourteen **Live Lab Demonstration** cards. Each button invokes its lab through the same **Academic AI Assistant**; the dashboard also has a **Run complete 14-lab demo** button.

## One-click execution of the complete demonstration suite
Click **Run complete 14-lab demo**. Alternatively, paste this into the Academic AI Assistant:

```text
Run the 14-lab demonstration suite
```

The assistant runs a deterministic, clearly labelled sample worklet for every lab, persists every run in the shared SQLite execution log, and displays each lab's status and run ID in the execution trace. Expand **Detailed execution output (JSON)** to inspect the actual inputs and outputs. The recent execution-history panel shows persisted records.

The suite creates demonstration artifacts: a reusable skill, a user-scoped memory, a pending governance approval, and a helpdesk ticket. These are labelled demo data and can be inspected in the corresponding outputs.

## Individual live prompts

1. **Agent vs Chatbot:** `Compare a chatbot and an agent for finding courses.`
2. **Tool-Using Agent:** `Calculate 125 multiplied by 48, then divide the result by 6.`
3. **Reusable Skills:** `{"action":"create","name":"demo_uppercase","description":"Reusable uppercase transform","operation":"uppercase"}` then `{"action":"run","name":"demo_uppercase","input":"hello professor"}`
4. **Memory:** `Remember that my demo preference is concise explanations.` then `Recall demo preference.`
5. **Connectors:** `List available connectors.` or `{"action":"call","connector":"academic_db","arguments":{"query":""}}`
6. **Runtime:** `Show runtime events for calculating 25 + 17.`
7. **Node Graph:** `{"nodes":[{"id":"a","operation":"word_count","input":"agentic course organizer"},{"id":"b","operation":"uppercase","input":"graph completed","depends_on":["a"]}]}`
8. **Parallel Swarm:** `Run parallel specialist analysis on this text: the portal failed with timeout; contact support@example.edu.`
9. **Deep Research:** `{"topic":"AI in academic course management","sources":[{"title":"My project note","text":"Course management supports structured learning and assessment."}]}`
10. **Cloud Operations:** `{"service":"course-api","environment":"demo","logs":"INFO service started\nERROR database connection timeout\nWARN retry exhausted"}`
11. **Agentic SDLC:** `Generate an SDLC test plan for a library book reservation portal.`
12. **Safety & Governance:** `{"diagnosis":"Demo service capacity issue","proposed_change":"Increase worker pool after load testing","rollback_plan":"Restore previous worker count","privacy_scrubbed":true,"estimated_cost":10,"budget":50}`
13. **Engineering Specialists:** `{"domain":"civil","readings":[{"crack_width_mm":0.5,"displacement_mm":2}],"thresholds":{"crack_width_mm":0.3}}`
14. **Capstone Studio:** `Create ticket for a broken projector in room 204.`

## What to show the professor
- The natural-language input in the one assistant.
- The answer and selected capability.
- **Execution trace — components actually invoked**.
- **Detailed execution output (JSON)**, including input, output, run ID, duration and status.
- The recent persisted execution-history table.

## Honest implementation boundaries
- Lab 5 is an internal typed connector registry with MCP-style concepts; it is not a full official MCP SDK server or transport implementation.
- Lab 8 runs concurrent Python specialist workers; it does not claim four independent LLM agents.
- Lab 9 uses the bundled offline evidence corpus and clearly attributed user-supplied sources; it does not claim live web research.
- Lab 10 diagnoses supplied logs and recommends non-destructive remediation; it does not operate a live cloud account.
- Lab 12 records governance decisions; approval does not deploy or change production systems.
- Lab 13 uses configurable thresholds; defaults are illustrative and must not be treated as certified engineering limits.

Do not present a local deterministic worklet as a production deployment, live cloud action, or official MCP SDK server.
