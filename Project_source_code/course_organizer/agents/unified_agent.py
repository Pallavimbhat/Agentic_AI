"""Single-entry assistant that routes natural-language requests to integrated lab capabilities.

The labs are capabilities behind one assistant, not separate user-facing pages/buttons.
All local/offline limitations are returned explicitly in execution metadata.
"""
from __future__ import annotations

import json
import re
from time import perf_counter
from typing import Any

from course_organizer.agents.integrated_lab_agent import IntegratedLabAgent

CAPABILITIES = {
    1: ("Agent vs Chatbot", "Natural-language intent detection, tool selection and comparison"),
    2: ("Tool-Using Agent", "Calculator, course database and text-analysis tools"),
    3: ("Reusable Skills", "Create, version, list and execute reusable skills"),
    4: ("Memory & Retrieval", "User-scoped persistent memory and retrieval"),
    5: ("Connectors", "Discover and invoke registered database, workspace and HTTP connectors"),
    6: ("Agent Runtime", "Runtime lifecycle, events, status and execution logging"),
    7: ("Agentic Node Graph", "Dependency-aware graph execution and validation"),
    8: ("Parallel Agent Swarm", "Concurrent specialist workers and aggregation"),
    9: ("Deep Research", "Evidence brief from the bundled local corpus and user-supplied sources"),
    10: ("Cloud Operations", "Log diagnosis and non-destructive remediation recommendations"),
    11: ("Agentic SDLC", "Requirement-specific user stories, acceptance criteria and test artifacts"),
    12: ("Safety & Governance", "Input validation, risk checks, audit and human approval records"),
    13: ("Engineering Specialists", "Mechanical, civil and electrical sensor analysis with configurable thresholds"),
    14: ("Capstone Project Studio", "Persistent helpdesk triage and ticket lifecycle"),
}


class UnifiedAcademicAgent:
    def __init__(self, db):
        self.db = db
        self.academic = IntegratedLabAgent(db)

    @staticmethod
    def _route(question: str) -> int | None:
        q = question.lower().strip()

        # -----------------------------------------
        # 1. STRUCTURED JSON REQUESTS
        # -----------------------------------------
        try:
            structured = json.loads(question)
        except (TypeError, ValueError):
            structured = None

        if isinstance(structured, dict):

            if structured.get("nodes") is not None:
                return 7

            if structured.get("readings") is not None:
                return 13

            if structured.get("domain") in {
                "mechanical", "civil", "electrical"
            }:
                return 13

            if (
                structured.get("diagnosis") is not None
                or structured.get("proposed_change") is not None
            ):
                return 12

            if structured.get("logs") is not None:
                return 10

            if structured.get("requirement") is not None:
                return 11

            if structured.get("topic") is not None:
                return 9

            if (
                structured.get("connector") is not None
                or structured.get("action") == "list_connectors"
            ):
                return 5

            if (
                structured.get("user_id") is not None
                and structured.get("action") in {"remember", "recall"}
            ):
                return 4

            if (
                structured.get("action") in {"create", "run"}
                and (
                    structured.get("operation")
                    or structured.get("name")
                )
            ):
                return 3

            if (
                structured.get("issue") is not None
                or structured.get("ticket_id") is not None
            ):
                return 14

        # -----------------------------------------
        # 2. LAB 1 - AGENT VS CHATBOT
        # -----------------------------------------
        if re.search(
            r"\b(compare|comparison)\b.*\b(chatbot|agent)\b"
            r"|\bchatbot\s+vs\s+agent\b",
            q
        ):
            return 1

        # -----------------------------------------
        # 3. LAB 2 - TOOL USING AGENT
        # -----------------------------------------
        # Text analysis must be checked before
        # engineering-specialist routing.

        text_patterns = [
             r"\b(count the words|word count|character count)\b",
             r"\b(unique words|frequent words|top terms)\b",
             r"\b(extract keywords|extract entities)\b",
             r"\b(sentiment analysis|analyse sentiment|analyze sentiment)\b",
             r"\b(text analyzer|text analysis tool)\b",
             r"\b(analyse|analyze)\s+(this\s+)?text\b",
        ]

        if any(re.search(pattern, q) for pattern in text_patterns):
            return 2

        if re.search(
            r"\b(calculate|compute|calculator|arithmetic|evaluate)\b"
            r"|\b(use a tool|tool execution)\b",
            q
        ):
            return 2

        # -----------------------------------------
        # 4. LAB 3 - REUSABLE SKILLS
        # -----------------------------------------
        if re.search(
            r"\b(skill|skills)\b"
            r"|\b(reusable|create|register|execute)\s+skill\b",
            q
        ):
            return 3

        # -----------------------------------------
        # 5. LAB 4 - MEMORY
        # -----------------------------------------
        if re.search(
            r"\b(remember|recall|retrieve memory|"
            r"my preferences|what do you remember)\b",
            q
        ):
            return 4

        # -----------------------------------------
        # 6. LAB 5 - CONNECTORS
        # -----------------------------------------
        if re.search(
            r"\b(connector|connectors|mcp)\b",
            q
        ):
            return 5

        # -----------------------------------------
        # 7. LAB 6 - AGENT RUNTIME
        # -----------------------------------------
        if re.search(
            r"\b(runtime|execution lifecycle|runtime events|"
            r"retry execution|cancel execution)\b",
            q
        ):
            return 6

        # -----------------------------------------
        # 8. LAB 7 - NODE GRAPH
        # -----------------------------------------
        if re.search(
            r"\b(node graph|workflow graph|dependency graph|dag)\b",
            q
        ):
            return 7

        # -----------------------------------------
        # 9. LAB 8 - PARALLEL AGENT SWARM
        # -----------------------------------------
        if re.search(
            r"\b(parallel|concurrent|swarm|specialist agents)\b",
            q
        ):
            return 8

        # -----------------------------------------
        # 10. LAB 9 - DEEP RESEARCH
        # -----------------------------------------
        if re.search(
            r"\b(research|literature review|evidence brief|"
            r"research brief)\b",
            q
        ):
            return 9

        # -----------------------------------------
        # 11. LAB 10 - CLOUD OPERATIONS
        # -----------------------------------------
        if re.search(
            r"\b(cloud operations|cloud log|server log)\b"
            r"|\b(diagnose|analyse|analyze)\b.*\blogs?\b",
            q
        ):
            return 10

        # -----------------------------------------
        # 12. LAB 11 - AGENTIC SDLC
        # -----------------------------------------
        if re.search(
            r"\b(sdlc|software development lifecycle|"
            r"acceptance criteria|test plan|requirements document)\b",
            q
        ):
            return 11

        # -----------------------------------------
        # 13. LAB 12 - SAFETY AND GOVERNANCE
        # -----------------------------------------
        if re.search(
            r"\b(governance|approval|approve change|"
            r"propose change|risk assessment|safety review)\b",
            q
        ):
            return 12

        # -----------------------------------------
        # 14. LAB 13 - ENGINEERING SPECIALISTS
        # -----------------------------------------
        # Do not route based on the generic word
        # "engineering" alone.

        if re.search(
            r"\b(sensor readings|mechanical sensor|civil sensor|"
            r"electrical sensor|vibration|temperature readings|"
            r"mechanical engineering|civil engineering|"
            r"electrical engineering|mechanical domain|civil domain|"
            r"electrical domain|structural analysis|"
            r"structural damage|civil structural damage|"
            r"crack width|structural displacement|"
            r"electrical circuit analysis)\b",
            q
        ):
            return 13

        # -----------------------------------------
        # 15. LAB 14 - CAPSTONE
        # -----------------------------------------
        if re.search(
            r"\b(helpdesk|support ticket|ticket\b|capstone)\b",
            q
        ):
            return 14

        # -----------------------------------------
        # 16. COURSE CATALOGUE LOOKUP
        # -----------------------------------------
        personal_course_query = bool(
            re.search(
                r"\b(my|enrolled|enrolment|enrollment)\b",
                q
            )
        )

        if (
            not personal_course_query
            and re.search(
                r"\b(list|show|find|search)\b.*"
                r"\b(courses?|subjects?)\b"
                r"|\b(course catalogue|course catalog|"
                r"find course|search course)\b",
                q
            )
        ):
            return 1

        return None

    @staticmethod
    def _lab_input(lab_id: int, question: str, user_id: int) -> str:
        q = question.strip()
        low = q.lower()
        if lab_id in {2, 6}:
            # Convert common natural-language arithmetic into the safe AST calculator syntax.
            average = re.search(r"\b(?:average|mean)\s+of\s+(.+)$", q, re.I)
            if average:
                numbers = re.findall(r"-?\d+(?:\.\d+)?", average.group(1))
                if not numbers:
                    raise ValueError("Provide at least one number for the average.")
                return "calculate (" + "+".join(numbers) + ")/" + str(len(numbers))
            total = re.search(r"\b(?:sum|total)\s+of\s+(.+)$", q, re.I)
            if total:
                numbers = re.findall(r"-?\d+(?:\.\d+)?", total.group(1))
                if not numbers:
                    raise ValueError("Provide numbers to calculate the sum.")
                return "calculate " + "+".join(numbers)
            math = re.search(r"(?:calculat(?:e|ing)|comput(?:e|ing)|evaluat(?:e|ing))\s+(.+)$", q, re.I)
            if math:
                expr = math.group(1).strip().rstrip("?.!")
                expr = re.sub(r"\b(multiplied by|times)\b", "*", expr, flags=re.I)
                expr = re.sub(r"\b(divided by|over)\b", "/", expr, flags=re.I)
                expr = re.sub(r"\b(plus|added to)\b", "+", expr, flags=re.I)
                expr = re.sub(r"\b(minus|subtracted by)\b", "-", expr, flags=re.I)
                expr = re.sub(r",?\s*(then\s+)?(divide|divided)\s+(the result|result)\s+by\s+", " / ", expr, flags=re.I)
                expr = re.sub(r",?\s*(then\s+)?(multiply|multiplied)\s+(the result|result)\s+by\s+", " * ", expr, flags=re.I)
                expr = re.sub(r"\b(the result|result)\b", "", expr, flags=re.I)
                expr = re.sub(r"\bzero\b", "0", expr, flags=re.I)
                expr = re.sub(r"\bone\b", "1", expr, flags=re.I)
                expr = re.sub(r"\s+", " ", expr).strip()
                return "calculate " + expr
            return q
        if lab_id == 13:
            domain_match = re.search(r"\b(civil|mechanical|electrical)\b", q, re.I)
            domain = domain_match.group(1).lower() if domain_match else "mechanical"
            q = re.sub(r"^(?:please\s+)?(?:analyse|analyze)\s+(?:these\s+)?(?:civil|mechanical|electrical)?\s*engineering\s+sensor\s+readings\s*:?\s*", "", q, flags=re.I)
            q = re.sub(r"^(?:please\s+)?(?:analyse|analyze)\s+(?:these\s+)?(?:civil|mechanical|electrical)?\s*sensor\s+readings\s*:?\s*", "", q, flags=re.I)
            # Convert prose measurements into the engineering agent's explicit
            # key=value input format; preserve units only in the user-facing trace.
            aliases = {
                "vibration": "vibration_mm_s", "temperature": "temp_c",
                "temp": "temp_c", "voltage": "voltage_v", "current": "current_a",
                "displacement": "displacement_mm", "strain": "strain",
                "crack width": "crack_width_mm",
            }
            extracted = []
            for label, key in aliases.items():
                match = re.search(rf"\b{re.escape(label)}\b\s*[:=]?\s*(-?\d+(?:\.\d+)?)", q, re.I)
                if match:
                    extracted.append(f"{key}={match.group(1)}")
            if extracted:
                return domain + "\n" + "\n".join(extracted)
            return domain + "\n" + q
        if lab_id == 5:
            if re.search(r"\b(list|show|discover)\b.*\b(connectors?|integrations?)\b", low):
                return "list connectors"
            course = re.search(r"(?:course|courses)\s+(?:through|using)\s+(?:the\s+)?database\s+connector\s*[:：]?\s*(.*)$", q, re.I)
            if course:
                return json.dumps({"action": "call", "connector": "academic_db", "arguments": {"query": course.group(1).strip()}})
            if re.search(r"\bread\b.*\bfile\b", low):
                filename = re.sub(r"^.*?\bread\s+(?:the\s+)?file\s+", "", q, flags=re.I).strip()
                return "read file " + filename
            return q
        if lab_id == 4:
            if re.match(r"^(remember|store)\b", low):
                text = re.sub(r"^(remember|store)(\s+that)?\s*", "", q, flags=re.I)
                return json.dumps({"action": "remember", "user_id": str(user_id), "text": text})
            query = re.sub(r"^(what do you remember|recall|retrieve)(\s+about)?\s*", "", q, flags=re.I)
            return json.dumps({"action": "recall", "user_id": str(user_id), "query": query})
        if lab_id == 14:
            data = None
            try:
                data = json.loads(q)
            except Exception:
                pass
            if isinstance(data, dict):
                data["user_id"] = str(user_id)
                return json.dumps(data)
            if low.startswith(("create ticket", "open ticket", "ticket ")):
                issue = re.sub(r"^(create ticket|open ticket|ticket)\s*", "", q, flags=re.I)
                issue = re.sub(r"^for\s+", "", issue, flags=re.I)
                return json.dumps({"action": "create", "user_id": str(user_id), "issue": issue})
            if low.startswith("list tickets"):
                return json.dumps({"action": "list", "user_id": str(user_id)})
            if low.startswith("triage "):
                return json.dumps({"action": "triage", "user_id": str(user_id), "issue": q[6:].strip()})
        return q

    def _professor_query(self, user_id: int, question: str) -> dict:
        """Answer professor questions from records in the professor's teaching scope."""
        q = question.lower()
        courses = [c for c in self.db.list_courses() if c.get("created_by") in (None, user_id)]
        course_ids = {c["id"] for c in courses}
        overview = any(term in q for term in ("overview", "everything", "all academic", "complete summary", "overall"))
        intents = []
        if overview or any(x in q for x in ("course", "subject", "curriculum")): intents.append("courses")
        if overview or any(x in q for x in ("student", "learner", "enrol")): intents.append("students")
        if overview or any(x in q for x in ("note", "notes", "study material")): intents.append("notes")
        if overview or any(x in q for x in ("assignment", "deadline", "due date")): intents.append("assignments")
        if overview or any(x in q for x in ("submission", "submitted", "upload")): intents.append("submissions")
        if overview or any(x in q for x in ("grade", "grades", "marks", "feedback", "score")): intents.append("grades")
        if not intents:
            return {"answer": "I can answer questions about your teaching courses, enrolled students, course notes, assignments, deadlines, submissions, grades and feedback. Try 'Give me an overview of everything in my courses'.", "data": {}, "intents": []}

        data = {}
        if "courses" in intents: data["courses"] = courses
        if "students" in intents:
            # Return student identities only, never credential fields.
            students = self.db.list_users(role="student")
            data["students"] = [{k:v for k,v in row.items() if k.lower() not in {"password", "password_hash", "hashed_password", "token", "secret", "api_key"}} for row in students]
        if "notes" in intents:
            data["notes"] = [n for n in self.db.list_notes() if n.get("course_id") in course_ids]
        if "assignments" in intents:
            data["assignments"] = [a for a in self.db.list_assignments() if a.get("course_id") in course_ids]
        assignment_ids = {a["id"] for a in data.get("assignments", self.db.list_assignments()) if a.get("course_id") in course_ids}
        if "submissions" in intents:
            data["submissions"] = [r for r in self.db.list_submissions() if r.get("assignment_id") in assignment_ids]
        if "grades" in intents:
            data["grades"] = [g for g in self.db.list_grades() if g.get("submission_id") in {r.get("id") for r in data.get("submissions", self.db.list_submissions())}]
        counts = {key: len(value) for key, value in data.items() if isinstance(value, list)}
        answer = "Retrieved teaching-scope records from the database: " + ", ".join(f"{key}: {count}" for key, count in counts.items()) + "."
        return {"answer": answer, "data": data, "intents": intents, "scope": "courses owned by this professor or institution-wide courses"}

    def run(self, user_id: int, role: str, question: str) -> dict:
        started = perf_counter()
        question = (question or "").strip()
        if not question:
            return {"success": False, "answer": "Enter a request for the Academic AI Assistant."}
        # One natural-language command executes and records one representative
        # end-to-end worklet for every lab. This is a single assistant entry point,
        # not fourteen separate launch buttons.
        if re.search(r"\b(run|execute|launch)\b.*\b(14|fourteen)\b.*\b(labs?|demonstration|demo|suite)\b", question.lower()) or re.search(r"\b(demonstrate|execute)\b.*\ball\s+14\s+labs\b", question.lower()):
            return self._run_demo_suite(user_id)
        lab_id = self._route(question)
        llm_routing = None
        if lab_id is None:
            # Optional model-assisted intent classification for requests that
            # the deterministic router cannot confidently classify. The model
            # proposes a capability/input only; local code still validates and
            # executes every tool and records the actual result.
            try:
                from agentic_core.llm_provider import classify_request
                llm_routing = classify_request(question)
                if llm_routing and llm_routing.get("lab_id"):
                    lab_id = int(llm_routing["lab_id"])
                    question = llm_routing["input"]
            except Exception:
                llm_routing = None
        if lab_id is None:
            if role == "student":
                result = self.academic.run(user_id=user_id, question=question, role=role)
                result["capabilities"] = [{"lab": i, "name": name, "description": desc, "availability": "integrated"} for i, (name, desc) in CAPABILITIES.items()]
                result["architecture"] = "One assistant routes academic questions through authenticated academic agents, tools, skills, memory, connectors, runtime, graph and parallel workers. Specialized capabilities are invoked when relevant."
                return result
            result = self._professor_query(user_id, question)
            return {"success": True, **result, "intents": ["professor_academic_data"], "trace": [{"lab": 1, "component": "Request interpretation", "status": "completed"}, {"lab": 2, "component": "Role-scoped database tools", "status": "completed"}, {"lab": 5, "component": "Academic database connector", "status": "completed"}], "capabilities": [{"lab": i, "name": name, "description": desc, "availability": "integrated"} for i, (name, desc) in CAPABILITIES.items()]}

        from agentic_core.runtime import run_lab
        payload = self._lab_input(lab_id, question, user_id)
        try:
            recorded = run_lab(lab_id, payload)
            result = recorded.get("output", {})
            ok = bool(recorded.get("success"))
            name, description = CAPABILITIES[lab_id]
            trace = [{"lab": lab_id, "component": name, "status": recorded.get("status", "failed"),
                      "run_id": recorded.get("run_id"), "duration_seconds": recorded.get("duration_seconds"),
                      "details": description}]
            if lab_id in {1, 2} and isinstance(result, dict):
                agent = result.get("agent", {}) if lab_id == 1 else result
                trace.append({"lab": 2, "component": "Selected tool execution",
                              "status": "completed" if ok else "failed",
                              "tool": agent.get("tool"), "arguments": agent.get("arguments")})
            answer = self._summarise_lab(lab_id, result)
            return {"success": ok, "answer": answer, "selected_capability": {"lab": lab_id, "name": name},
                    "routing_mode": "configured_llm_plus_local_tools" if llm_routing else "deterministic_local_router",
                    "result": result, "run_id": recorded.get("run_id"), "trace": trace,
                    "execution_seconds": round(perf_counter() - started, 6),
                    "capabilities": [{"lab": i, "name": n, "description": d, "availability": "integrated"} for i, (n, d) in CAPABILITIES.items()]}
        except Exception as exc:
            name, _ = CAPABILITIES[lab_id]
            return {"success": False, "answer": f"{name} could not complete the request: {exc}", "selected_capability": {"lab": lab_id, "name": name}, "trace": [{"lab": lab_id, "component": name, "status": "failed", "error": str(exc)}], "execution_seconds": round(perf_counter() - started, 6)}

    def _run_demo_suite(self, user_id: int) -> dict:
        """Execute a transparent, deterministic sample workflow for each lab.

        Inputs are clearly marked as demonstration fixtures. Every step is run
        through run_lab and therefore receives a persistent execution record.
        """
        from agentic_core.runtime import run_lab
        import uuid
        user_key = f"professor-demo-{user_id}"
        skill_name = f"demo_uppercase_{user_id}"
        ticket_issue = f"Demonstration projector support request {uuid.uuid4().hex[:6]}"
        examples = {
            1: "Compare a chatbot and an agent for finding courses.",
            2: "calculate (125*48)/6",
            3: json.dumps({"action":"create","name":skill_name,"description":"Demo reusable uppercase skill","operation":"uppercase"}),
            4: json.dumps({"action":"remember","user_id":user_key,"text":"Demo memory persists across assistant requests."}),
            5: json.dumps({"action":"list"}),
            6: "calculate 9*9",
            7: json.dumps({"nodes":[{"id":"request","operation":"word_count","input":"Agentic AI course organizer demo"},{"id":"format","operation":"uppercase","input":"demo complete","depends_on":["request"]}]}),
            8: "The campus portal failed with timeout; contact support@example.edu.",
            9: json.dumps({"topic":"AI in academic course management","sources":[{"title":"Demonstration evidence","text":"Course management systems can support structured learning workflows and transparent assessment."}]}),
            10: json.dumps({"service":"course-api","environment":"demo","logs":"INFO service started\nERROR database connection timeout\nWARN retry exhausted"}),
            11: json.dumps({"requirement":"Build a course assignment submission portal with deadline tracking and feedback."}),
            12: json.dumps({"diagnosis":"Demo service capacity issue","proposed_change":"Increase worker pool after load testing","rollback_plan":"Restore previous worker count","privacy_scrubbed":True,"estimated_cost":10,"budget":50}),
            13: json.dumps({"domain":"mechanical","readings":[{"vibration_mm_s":8.2,"temperature_c":72}],"thresholds":{"vibration_mm_s":7.0}}),
            14: json.dumps({"action":"create","user_id":user_key,"issue":ticket_issue}),
        }
        steps=[]
        for lab_id in range(1,15):
            payload=examples[lab_id]
            rec=run_lab(lab_id,payload)
            steps.append({"lab":lab_id,"name":CAPABILITIES[lab_id][0],"status":rec["status"],"run_id":rec["run_id"],"duration_seconds":rec["duration_seconds"],"input":payload,"output":rec["output"]})
            # Demonstrate the stateful half of Labs 3, 4 and 5 as additional
            # separately recorded operations, while retaining one assistant entry.
            if lab_id==3 and rec["success"]:
                follow=run_lab(3,json.dumps({"action":"run","name":skill_name,"input":"fourteen labs integrated"}))
                steps.append({"lab":3,"name":"Reusable Skills — execute created skill","status":follow["status"],"run_id":follow["run_id"],"duration_seconds":follow["duration_seconds"],"output":follow["output"]})
            elif lab_id==4 and rec["success"]:
                follow=run_lab(4,json.dumps({"action":"recall","user_id":user_key,"query":"Demo memory"}))
                steps.append({"lab":4,"name":"Memory — retrieve persisted fact","status":follow["status"],"run_id":follow["run_id"],"duration_seconds":follow["duration_seconds"],"output":follow["output"]})
            elif lab_id==5 and rec["success"]:
                follow=run_lab(5,json.dumps({"action":"call","connector":"academic_db","arguments":{"query":""}}))
                steps.append({"lab":5,"name":"Connectors — execute academic database connector","status":follow["status"],"run_id":follow["run_id"],"duration_seconds":follow["duration_seconds"],"output":follow["output"]})
        passed=sum(x["status"]=="completed" for x in steps)
        failed=len(steps)-passed
        trace=[{"lab":x["lab"],"component":x["name"],"status":x["status"],"run_id":x["run_id"],"duration_seconds":x["duration_seconds"]} for x in steps]
        return {"success":failed==0,"answer":f"Demonstration suite executed {len(steps)} recorded worklets covering all 14 labs: {passed} completed, {failed} failed. Inputs are labelled demonstration fixtures; inspect the output for each run.","selected_capability":{"lab":"1–14","name":"Integrated 14-lab demonstration suite"},"result":{"demonstration_fixture":True,"labs_covered":14,"steps":steps,"completed":passed,"failed":failed,"history_note":"Every step was persisted in the shared executions table."},"trace":trace,"run_id":None,"capabilities":[{"lab":i,"name":n,"description":d,"availability":"integrated"} for i,(n,d) in CAPABILITIES.items()]}

    @staticmethod
    def _summarise_lab(lab_id: int, result: Any) -> str:
        if not isinstance(result, dict):
            return str(result)
        if lab_id == 1:
            agent = result.get("agent", {})
            output = agent.get("output", {})
            matches = output.get("matches", []) if isinstance(output, dict) else []
            comparison = result.get("comparison", {})
            if agent.get("tool") == "course_lookup":
                if matches:
                    labels = [f"{row.get('course_code', row.get('code', ''))} — {row.get('name', row.get('course_name', row.get('title', 'Course')))}" for row in matches]
                    return ("Chatbot: text-only response (0 tool calls). Agent: executed course_lookup "
                            f"and retrieved {len(matches)} actual record(s): " + "; ".join(labels[:8]))
                return "The agent executed course_lookup, but the database returned no matching courses. Check the database path and query details."
            if agent.get("tool") == "calculator":
                return f"Chatbot: text-only (0 tool calls). Agent: calculator executed {agent.get('arguments', {}).get('expression')} and returned {output.get('result')}."
            return (f"Chatbot: text-only (0 tool calls). Agent: executed {agent.get('tool')} "
                    f"with {len(comparison) and comparison.get('agent_tool_calls', 1)} tool call(s).")
        if lab_id == 2:
            if result.get("success") is False or result.get("error"):
                error = str(result.get('error', result.get('message', 'Invalid tool input')))
                if "division by zero" in error.lower():
                    return "Calculation could not be completed: division by zero is undefined. The error was handled safely and recorded."
                return f"Tool execution failed safely: {error}"
            return f"Tool execution result: {result.get('result', result.get('output', result))}"
        if lab_id == 3:
            return f"Skill operation completed: {json.dumps(result, ensure_ascii=False)[:1200]}"
        if lab_id == 4:
            return f"Memory operation completed: {json.dumps(result, ensure_ascii=False)[:1200]}"
        if lab_id == 5:
            return f"Connector operation completed: {json.dumps(result, ensure_ascii=False)[:1200]}"
        if lab_id == 9:
            return f"Research brief prepared from the configured local evidence corpus. {result.get('limitations', 'Review provenance in the result details.')}"
        if lab_id == 10:
            return f"Log analysis completed. Severity: {result.get('severity', 'not classified')}. No infrastructure changes were executed."
        if lab_id == 11:
            return "SDLC artifacts generated from the supplied requirement. Review the user story, acceptance criteria and test matrix in the result details."
        if lab_id == 12:
            return f"Governance evaluation completed. Approval status: {result.get('status', 'review result')}. No production action was executed."
        if lab_id == 13:
            return f"Engineering analysis completed. Status: {result.get('status', 'unclassified')}. Thresholds and assumptions are included in the result details."
        if lab_id == 14:
            return f"Capstone/helpdesk workflow completed: {json.dumps(result, ensure_ascii=False)[:1200]}"
        return f"{CAPABILITIES[lab_id][0]} completed. Inspect execution details for outputs and events."
