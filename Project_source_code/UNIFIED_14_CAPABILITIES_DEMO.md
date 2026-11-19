# Unified Academic AI Assistant — 14 Integrated Capabilities

This build uses one Academic AI Assistant entry point. It does not expose separate
Lab Showcase, Launch All Labs, or per-lab launch buttons in the dashboard.

## How the capabilities are demonstrated
Sign in to the Course Organizer and use the Academic AI Assistant. The assistant
routes requests to relevant capabilities and returns execution details. The
capability map is available under the assistant's expandable "View the 14
integrated capabilities" section.

## Suggested professor demonstration prompts
1. Agent vs Chatbot: "Compare a chatbot and an agent for finding courses."
2. Tool-Using Agent: "Calculate 125 * 8 using a tool."
3. Reusable Skills: "List skills."
4. Memory & Retrieval: "Remember that I prefer concise explanations."
5. Connectors: "List available connectors."
6. Agent Runtime: "Show runtime events for calculating 25 + 17."
7. Agentic Node Graph: "Run a workflow graph to analyse this text: students need help planning revision."
8. Parallel Agent Swarm: "Run parallel specialist analysis on this text: student performance is declining."
9. Deep Research: "Research AI applications in education."
10. Cloud Operations: "Analyse these cloud logs: ERROR database connection timeout."
11. Agentic SDLC: "Generate an SDLC plan and test cases for a library system."
12. Safety & Governance: "Evaluate this proposed change for approval: delete all course records."
13. Engineering Specialists: "Analyse these civil engineering sensor readings: [provide sample readings]."
14. Capstone Project Studio: "Create a helpdesk ticket for a campus portal issue."

## Important implementation boundaries
Read `INTEGRATED_ARCHITECTURE.md`, `DEMO_GUIDE.md`, and `VERIFICATION_REPORT.md`
before presenting the project. Do not describe offline/local analysis as live web
research, simulated specialist workers as independent LLMs, or connector
compatibility as a complete official MCP SDK server unless that has separately
been implemented and verified.

## Run
Follow `RUN_ME_FIRST.txt` and `README.md`. Preserve the existing database file
when moving from another installation. Back up the database before any migration.
