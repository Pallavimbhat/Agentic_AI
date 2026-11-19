"""Authenticated academic workflow used by the unified assistant.

This service handles student academic-record questions using Labs 1–8 concepts.
Specialized Labs 9–14 are routed on demand by UnifiedAcademicAgent rather than
being run with synthetic placeholder inputs on every academic question.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from course_organizer.agents.academic_assistant_agent import AcademicAssistantAgent
from lab5.registry import ConnectorRegistry
from lab6.runtime import AgentRuntime
from lab7.graph import AgentGraph
from lab8.swarm import SwarmManager


class IntegratedLabAgent:
    INTENT_TO_SKILL = {
        "assignments": "assignment_retrieval",
        "submissions": "submission_retrieval",
        "notes": "notes_retrieval",
        "courses": "course_retrieval",
        "grades": "published_grade_retrieval",
        "milestones": "milestone_retrieval",
    }

    def __init__(self, db):
        self.db = db
        self.assistant = AcademicAssistantAgent(db)
        self.memory_dir = Path(__file__).resolve().parents[1] / "data" / "academic_memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _memory_path(self, user_id: int) -> Path:
        return self.memory_dir / f"user_{int(user_id)}.json"

    def _load_memory(self, user_id: int) -> list[dict]:
        path = self._memory_path(user_id)
        try:
            value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save_memory(self, user_id: int, question: str) -> dict:
        memories = self._load_memory(user_id)
        match = re.search(r"^\s*(?:remember(?: that)?|my preference is|i prefer)\s+(.+)", question, re.I)
        kind = "preference" if match else "interaction"
        text = (match.group(1) if match else question).strip()[:500]
        entry = {"kind": kind, "text": text, "created_at": datetime.now(timezone.utc).isoformat()}
        memories.append(entry)
        path = self._memory_path(user_id)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(memories[-100:], indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)
        return entry

    @staticmethod
    def _is_overview(question: str) -> bool:
        phrases = ("overview", "overall status", "academic status", "workload",
                   "summarise my academics", "summarize my academics", "academic summary",
                   "summarise my assignments", "summarize my assignments")
        return any(term in question for term in phrases)

    def run(self, user_id: int, question: str, role: str = "student") -> dict:
        started = perf_counter()
        if role != "student":
            return {"success": False, "answer": "The Academic AI Assistant is available to student accounts. Professor functions are available in the professor dashboard."}
        question = (question or "").strip()
        if not question:
            return {"success": False, "answer": "Please enter an academic question."}

        # Lab 1: interpret natural language and build a selective retrieval plan.
        normalised = self.assistant._normalise(question)
        intents = self.assistant._classify(normalised)
        if self._is_overview(normalised):
            intents = ["courses", "assignments", "submissions", "notes", "grades", "milestones"]
        if any(term in normalised for term in ("remember", "my preference", "i prefer", "what do you remember", "study preference")):
            if "memory" not in intents:
                intents.append("memory")
        intents = list(dict.fromkeys(intents))
        trace: list[dict] = [{"lab": 1, "component": "Natural-language request interpretation", "status": "completed", "intents": intents}]

        def full_workflow():
            # Lab 5: discover and use the registered, authenticated connector.
            registry = ConnectorRegistry()

            class AuthenticatedAcademicConnector:
                name = "authenticated_academic_database"
                description = "Read-only access to the current student's permitted academic records"

                def __init__(self, db_service, assistant, student_id):
                    self.db = db_service
                    self.assistant = assistant
                    self.student_id = student_id

                def retrieve(self, intent):
                    return self.assistant._fetch(intent, self.student_id)[0]

            connector = AuthenticatedAcademicConnector(self.db, self.assistant, user_id)
            registry.connectors[connector.name] = connector
            discovered = [item.get("name") for item in registry.list_connectors()]

            # Lab 4: recall user preferences and persist this interaction.
            memories = self._load_memory(user_id)
            preferences = [item for item in memories if item.get("kind") == "preference"][-10:]
            explicit_memory = bool(re.search(r"^\s*(?:remember(?: that)?|my preference is|i prefer)\s+", question, re.I))
            saved = self._save_memory(user_id, question) if explicit_memory else {"kind": "not_saved", "reason": "No explicit memory request"}

            # Lab 3: build the reusable skill registry. Lab 2: skill calls are
            # the tool boundary to the authenticated academic connector.
            skills = {
                intent: (lambda key=intent: connector.retrieve(key))
                for intent in self.INTENT_TO_SKILL
            }

            def specialist(intent):
                if intent not in intents:
                    return {"intent": intent, "matched": False, "records": []}
                if intent == "memory":
                    return {"intent": intent, "matched": True, "records": preferences}
                if intent == "help":
                    return {"intent": intent, "matched": True, "records": []}
                records = skills[intent]()
                return {"intent": intent, "matched": True, "records": records}

            # Lab 8: every specialist is invoked concurrently. Nonmatching
            # specialists return an explicit no-match result without querying data.
            swarm_agents = {
                "assignment_specialist": lambda task: specialist("assignments"),
                "submission_specialist": lambda task: specialist("submissions"),
                "notes_specialist": lambda task: specialist("notes"),
                "course_specialist": lambda task: specialist("courses"),
                "grade_specialist": lambda task: specialist("grades"),
                "milestone_specialist": lambda task: specialist("milestones"),
            }
            swarm_result = SwarmManager(swarm_agents, max_workers=len(swarm_agents)).run(question)
            if not swarm_result["success"]:
                raise RuntimeError("A specialist agent failed: " + str(swarm_result["trace"]))

            records_by_intent = {}
            for item in swarm_result["results"].values():
                result = item["result"]
                if result["matched"] and result["intent"] not in {"memory", "help"}:
                    records_by_intent[result["intent"]] = result["records"]

            # Lab 2 tool dispatcher and Lab 3 skill selector are executed even
            # when no supported data intent matches; they then safely select 0 tools.
            tool_calls = {key: len(value) for key, value in records_by_intent.items()}
            selected_skills = [self.INTENT_TO_SKILL[key] for key in records_by_intent]

            # Lab 7: always execute a dependency graph, including clarification queries.
            graph = AgentGraph()
            graph.add_node("request_interpretation", lambda ctx: {"question": question, "intents": intents})
            graph.add_node("tool_and_skill_results", lambda ctx: records_by_intent, ["request_interpretation"])
            graph.add_node("verified_records", lambda ctx: dict(ctx["tool_and_skill_results"]), ["tool_and_skill_results"])
            graph_result = graph.run()
            if not graph_result["success"]:
                raise RuntimeError("Academic workflow graph failed")

            return {
                "connector_names": discovered,
                "preferences": preferences,
                "saved_memory": saved,
                "records": graph_result["context"]["verified_records"],
                "swarm": swarm_result,
                "graph": graph_result,
                "tool_calls": tool_calls,
                "skills_used": selected_skills,
            }

        # Lab 6: runtime wraps the whole connector-memory-tool-skill-swarm-graph path.
        runtime = AgentRuntime(name="Integrated Academic Assistant Runtime")
        runtime_result = runtime.execute(question, full_workflow)
        trace.append({"lab": 6, "component": "Agent runtime", "status": runtime_result["status"], "events": runtime_result.get("events", [])})
        if not runtime_result["success"]:
            error = runtime_result.get("error", "Unknown execution error")
            trace.extend([
                {"lab": 2, "component": "Academic database tools", "status": "failed", "detail": error},
                {"lab": 3, "component": "Reusable skills", "status": "failed", "detail": error},
                {"lab": 4, "component": "Persistent memory", "status": "failed", "detail": error},
                {"lab": 5, "component": "Connector registry", "status": "failed", "detail": error},
                {"lab": 7, "component": "Dependency graph", "status": "failed", "detail": error},
                {"lab": 8, "component": "Parallel specialist swarm", "status": "failed", "detail": error},
            ])
            return {"success": False, "answer": "I couldn't complete this request because an internal workflow component failed. Please try again or contact the administrator.", "trace": trace, "integrated_labs": {f"L{i}": ("failed" if i <= 8 else "available_not_invoked") for i in range(1, 15)}}

        result = runtime_result["result"]
        records = result["records"]
        # Add assignment titles to grade rows where available.
        for grade in records.get("grades", []):
            assignment_id = grade.get("assignment_id")
            if assignment_id:
                assignment = self.db.get_assignment(assignment_id)
                if assignment:
                    grade["assignment_title"] = assignment.get("title")

        # Lab 2 and 3 trace their real selected tools/skills, or a safe no-match.
        trace.append({"lab": 2, "component": "Academic database tool dispatcher", "status": "completed", "tool_calls": result["tool_calls"], "detail": "Only tools relevant to the interpreted request were called."})
        trace.append({"lab": 3, "component": "Reusable skill registry", "status": "completed", "skills_used": result["skills_used"], "detail": "Skill selection ran; no-match requests select no retrieval skill."})
        trace.append({"lab": 4, "component": "User-scoped persistent memory", "status": "completed", "preferences_recalled": len(result["preferences"]), "entry_saved": result["saved_memory"].get("kind")})
        trace.append({"lab": 5, "component": "Connector registry and authenticated academic connector", "status": "completed", "connectors": result["connector_names"]})
        trace.append({"lab": 8, "component": "Parallel specialist swarm", "status": "completed", "agents": result["swarm"]["trace"], "execution_seconds": result["swarm"]["execution_seconds"], "matched_specialists": [name for name, item in result["swarm"]["results"].items() if item["result"]["matched"]]})
        trace.append({"lab": 7, "component": "Dependency-aware workflow graph", "status": "completed", "nodes": [{"node": item["node"], "status": item["status"]} for item in result["graph"]["trace"]]})

        # Grounded, query-specific response. Unsupported questions receive a
        # helpful capability clarification after the relevant academic components have run.
        if not intents:
            answer = ("I can answer questions using your enrolled courses, notes, assignments, deadlines, "
                      "submission status, published grades and project milestones. I couldn't match this "
                      "question to those records, so I haven't invented an answer. Please rephrase it "
                      "or ask about one of those academic areas.")
            selected_data = {}
        else:
            answers, selected_data = [], {}
            for intent in intents:
                if intent == "memory":
                    if re.search(r"what do you remember|my study preference", normalised):
                        text = "; ".join(item["text"] for item in result["preferences"])
                        answer = "I remember these preferences: " + text if text else "I don't have saved study preferences yet. You can say: 'Remember that I prefer short study sessions.'"
                    else:
                        answer = "I've saved that information in your private, user-specific memory."
                    selected = result["preferences"]
                elif intent == "help":
                    answer = "I can help with your courses, notes, assignments, deadlines, submissions, published grades and project milestones. I use your own academic records and report when information is unavailable."
                    selected = []
                else:
                    answer, selected = self.assistant._answer(intent, normalised, records.get(intent, []))
                answers.append(answer)
                selected_data[intent] = selected
            answer = "\n\n".join(answers)

        trace.append({"lab": 1, "component": "Grounded response synthesis", "status": "completed", "intents_answered": intents})
        # Labs 9–14 are not fabricated or executed with fixed demonstration data
        # during an ordinary academic query. They are routed dynamically by the
        # UnifiedAcademicAgent when the user's request needs those capabilities.
        # This trace therefore reports only the components actually used here.
        lab_states = {f"L{i}": ("executed" if i <= 8 else "available_not_invoked") for i in range(1, 15)}

        return {
            "success": True,
            "answer": answer,
            "intents": intents,
            "plan": ["Interpret the request", "Select relevant tools and reusable skills", "Recall user-scoped memory", "Discover the academic connector", "Execute specialist agents concurrently", "Validate and aggregate results through the graph", "Return a grounded answer"],
            "data": selected_data,
            "memory": {"preferences_recalled": result["preferences"], "saved_entry": result["saved_memory"]},
            "integrated_labs": lab_states,
            "trace": trace,
            "execution_seconds": round(perf_counter() - started, 6),
        }
