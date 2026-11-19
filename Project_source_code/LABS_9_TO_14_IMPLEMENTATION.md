# Labs 9–14 implementation notes

These labs are included as runnable, offline Python worklets and are also invoked by the existing one-query academic assistant. Their results are recorded in the assistant execution trace under L9–L14. They do not alter or invent student academic records.

- **Lab 9 — Deep Research Agent:** evidence table and synthesized briefing using a small, explicitly disclosed teaching corpus. This is not live web research.
- **Lab 10 — Cloud Operations Agent:** log severity/root-cause triage; remediation is never auto-executed and requires operator approval.
- **Lab 11 — Agentic SDLC Factory:** requirement-to-design/implementation-plan/testing/review/release artifact pipeline with requirement lineage.
- **Lab 12 — Safety, Evaluation and Governance:** evaluation gate, privacy-scrubbed inputs, mandatory rollback plan, cost/budget check, audit events, and no direct production write permission.
- **Lab 13 — Discipline-Specific Engineering Agent:** mechanical predictive maintenance using illustrative vibration/temperature thresholds. Alarm recommendations are for human review only; thresholds are not certified operating limits.
- **Lab 14 — Capstone Project Studio:** help-desk worklet with three tools (FAQ search, ticket creation, ticket lookup), reusable triage skill, session/history memory, prompt log, audit log, input safety check and five-case evaluation.

Run each independently from the project root:
`python -m lab9`, `python -m lab10`, ... `python -m lab14`.
Run the additional tests:
`python -m unittest discover -s tests -v`

The labs are instructional demonstrations, not production deployment systems. Review outputs and safety constraints before using them operationally.
