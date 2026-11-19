# 14-lab independent demonstration prompt bank

Use the **same Academic AI Assistant** for all prompts. Each prompt is routed to one capability and its run is persisted. For a direct, isolated lab run (without relying on natural-language routing), the authenticated API is `POST /api/labs/{lab_id}/run` with JSON body `{"question":"..."}`. The web dashboard remains a single assistant entry point; there are no separate lab showcase cards.

> Stateful prompts are intentionally paired: create/remember first, then run/retrieve. Use unique skill names and test text when repeating the demo.

## Lab 1 — Agent vs Chatbot
1. `Compare a chatbot and an AI agent for finding Introduction to Artificial Intelligence.`
2. `Compare a chatbot and an AI agent for finding Agentic AI.`
3. `Compare a chatbot and an AI agent for finding all available courses.`

Expected: chatbot has zero tool calls; agent calls `course_lookup`; targeted queries retain the named course, while the catalogue request returns all courses.

## Lab 2 — Tool-Using Agent
1. `Calculate 125 * 8.`
2. `Calculate (144 + 36) / 6.`
3. `Analyse this text: Database systems store, retrieve and manage structured information.`

Expected: calculator or text-analysis tool, actual arguments and computed/analysed output.

## Lab 3 — Reusable Skills
1. `{"action":"create","name":"uppercase_demo_pallavi","description":"Convert supplied text to uppercase","operation":"uppercase"}`
2. `{"action":"run","name":"uppercase_demo_pallavi","input":"agent skills are reusable"}`
3. `{"action":"run","name":"uppercase_demo_pallavi","input":"different input gives different output"}`

Expected: skill is stored/versioned, then invoked twice with different inputs and different outputs.

## Lab 4 — Memory and Retrieval
1. `Remember that I prefer worked examples and concise explanations.`
2. `What do you remember about my preferences?`
3. `{"action":"recall","user_id":"<your-user-id>","query":"worked examples"}`

Expected: persistent user-scoped memory; the retrieval must return the stored text for the same user.

## Lab 5 — Connectors
1. `List available connectors.`
2. `Retrieve courses through the database connector.`
3. `Read file lab_test_dynamic.txt through the workspace connector.`

Expected: connector discovery or actual connector invocation, resource name, status and result. Workspace file must exist before reading; use the connector write operation first if needed.

## Lab 6 — Agent Runtime
1. `Show runtime events for calculating 25 + 17.`
2. `Show runtime events for calculating 144 / 12.`
3. `Show runtime events for calculating 9 * 9.`

Expected: accepted → planning → running → completed/failed events and the actual result.

## Lab 7 — Agentic Node Graph
1. `{"nodes":[{"id":"count","operation":"word_count","input":"Students need help planning revision"},{"id":"format","operation":"uppercase","input":"agentic ai","depends_on":["count"]}]}`
2. `{"nodes":[{"id":"terms","operation":"top_terms","input":"Database indexing improves query performance"},{"id":"mail","operation":"extract_emails","input":"Contact mam@example.edu","depends_on":["terms"]}]}`
3. `{"nodes":[{"id":"a","operation":"word_count","input":"one two three"},{"id":"b","operation":"character_count","input":"dynamic graph"}]}`

Expected: node outputs, dependency-aware execution order and validation. A graph with a cycle should be rejected.

## Lab 8 — Parallel Specialist Workers
1. `Run parallel specialist analysis on this text: Student scores improved but one assignment failed. Contact team@example.edu.`
2. `Run parallel specialist analysis on this text: Server uptime is excellent; response time is 120 ms and 3 alerts remain.`
3. `Run parallel specialist analysis on this text: The portal crashed, the database timed out and support is investigating.`

Expected: keyword, sentiment, entity and statistics workers; each output changes with the input. Implementation uses concurrent Python workers, not autonomous LLM agents.

## Lab 9 — Deep Research
1. `Research applications of artificial intelligence in education.`
2. `Research privacy and accountability risks in generative AI.`
3. `Research intelligent tutoring systems and adaptive learning.`

Expected: research question, search terms, retrieved local-corpus evidence, findings and explicit offline-corpus limitations. It is not live web research unless an external search provider is separately configured.

## Lab 10 — Cloud Operations
1. `Analyse these cloud logs: INFO service started; ERROR database connection timeout; WARNING high memory usage.`
2. `Analyse these cloud logs: INFO backup completed; INFO health check passed.`
3. `Analyse these cloud logs: CRITICAL disk full; ERROR payment service unavailable; WARNING retry limit reached.`

Expected: events classified from the supplied lines, severity, likely causes and recommendations. No cloud infrastructure is modified.

## Lab 11 — SDLC Factory
1. `Generate an SDLC plan for a student attendance management application with login and reports.`
2. `Generate an SDLC plan for a library book reservation portal with due-date reminders.`
3. `Generate an SDLC plan for a campus transport tracking application.`

Expected: requirement-specific functional/non-functional requirements, architecture/modules, implementation plan and test cases.

## Lab 12 — Safety and Governance
1. `{"diagnosis":"Database connection pool saturation","proposed_change":"Increase pool size after load testing","rollback_plan":"Restore the previous pool size","privacy_scrubbed":true,"estimated_cost":10,"budget":50}`
2. `{"diagnosis":"Unreviewed change","proposed_change":"Modify production data","rollback_plan":"Restore backup","privacy_scrubbed":false,"estimated_cost":10,"budget":50}`
3. `{"diagnosis":"Cost overrun","proposed_change":"Add a paid service","rollback_plan":"Disable the service","privacy_scrubbed":true,"estimated_cost":500,"budget":100}`

Expected: first request creates a pending human-approval record; second is rejected for privacy validation; third requires finance approval. Approval records do not deploy or change production.

## Lab 13 — Engineering Specialist
1. `Analyse mechanical sensor readings: vibration 8.5 mm/s and temperature 92 degrees Celsius.`
2. `Analyse civil sensor readings: crack width 0.5 mm and displacement 12 mm.`
3. `Analyse electrical sensor readings: voltage 250 V and current 18 A.`

Expected: domain, parsed readings, configured illustrative thresholds, classification and recommendations. These thresholds are not certified engineering limits.

## Lab 14 — Capstone Helpdesk
1. `Create ticket for campus portal login failure.`
2. `Create ticket: I cannot access my Database Management Systems notes.`
3. `Show all open tickets.`

Expected: ticket persisted in SQLite with ID, issue, triage, status and timestamp. To demonstrate lifecycle, follow with `{"action":"update","ticket_id":<id>,"status":"closed"}`.

## What to show after every prompt

- Selected lab/capability.
- Actual tool, skill, connector, worker or workflow used.
- Input/arguments.
- Structured output (expand JSON details where shown).
- Completed/failed status and run ID.
- Execution history entry.

Never describe a feature as successful if the returned status is failed or the output is only a hint/validation message.
