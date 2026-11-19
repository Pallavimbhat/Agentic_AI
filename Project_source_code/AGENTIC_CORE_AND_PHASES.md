# Shared Agentic Core and unified integration

This note is superseded by `INTEGRATED_ARCHITECTURE.md` and the current `README.md`.

The current build keeps one user-facing Academic AI Assistant. It uses `course_organizer/agents/unified_agent.py` to route user requests to one of fourteen backend capabilities. The shared `agentic_core/` provides safe local tools, persistent memory, connector registry, approval records, audit events and execution history.

See `VERIFICATION_REPORT.md` for the current test results and implementation boundaries.
