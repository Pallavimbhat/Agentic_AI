# Integration audit and Lab 1 correction

## Changes made
- Lab 1 comparison prompts now explicitly perform a course-catalogue lookup for the agent side and retain a text-only chatbot side.
- Lab 1 natural-language arithmetic requests select the calculator.
- Course lookup ignores generic comparison words and requires meaningful token matches, preventing an unrelated prompt from returning an arbitrary course.
- The unified assistant now uses `agentic_core.runtime.run_lab` for specialist lab requests. This writes a persistent execution record with run ID, lab ID, input, status, output, timestamp and duration.
- The UI response includes the persistent run ID and an honest status in the execution trace.
- Added regression tests for chatbot/agent comparison and false-positive course matching.

## Verification performed in the build environment
Command:
`python -m unittest tests.test_agentic_core tests.test_labs_9_14 tests.test_all_14_dynamic tests.test_unified_assistant tests.test_app_integration course_organizer.database.test_db_service course_organizer.database.test_extended_db_service course_organizer.agents.test_integrated_lab_agent lab3.test_skills lab4.test_memory lab5.test_connectors lab6.test_runtime lab7.test_graph lab8.test_swarm -v`

Result: **88 tests passed, 0 failed**.

This is automated unit/integration evidence from the build environment. It is not a claim that every workflow has been manually demonstrated on the user's Windows machine.

## Demonstration notes and implementation boundaries
- Lab 5 is an internal connector registry / MCP-style interface, not a full official MCP SDK server.
- Lab 8 runs concurrent deterministic Python specialist workers; it is not a swarm of independent LLMs.
- Lab 9 uses the bundled offline research corpus and user-supplied evidence; it does not perform live web research.
- Lab 10 diagnoses logs and recommends remediation; it does not control a real cloud account.
- Lab 11 generates SDLC planning/test artifacts; it does not build/deploy production software.
- Lab 12 records governance decisions; it does not execute production changes.
- Lab 13 uses configurable / illustrative thresholds, not certified engineering safety limits.
- Lab 14 provides a local persistent helpdesk workflow.

## Local verification required
After extracting, install requirements, run `RUN_TESTS.bat`, start the app, and verify the 14 demo prompts in `UNIFIED_14_CAPABILITIES_DEMO.md`. The actual browser session and Windows database path must be checked locally.
