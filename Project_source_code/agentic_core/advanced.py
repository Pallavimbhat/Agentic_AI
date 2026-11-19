"""Dynamic, auditable implementations for the 14 academic agent labs.

This module deliberately uses deterministic local tools. It does not pretend to
be an LLM, a live web research engine, a production cloud controller, or a full
MCP SDK server. External side effects remain approval-gated / human-operated.
"""
from __future__ import annotations
import csv, io, json, re, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "agentic_workspace"
WORKSPACE.mkdir(exist_ok=True)


def _json(text: str):
    try:
        value=json.loads(text)
        return value if isinstance(value,dict) else None
    except Exception:
        return None

def _now(): return datetime.now(timezone.utc).isoformat()

def _lab1(text):
    """Compare a text-only chatbot with an agent using the requested tool.

    For course lookups, preserve the user's requested course phrase. An empty
    query is used only when the user explicitly asks for the whole catalogue.
    """
    from .runtime import course_lookup, calculate
    q = text.strip()
    low = q.lower()

    is_comparison = bool(re.search(r"\b(compare|comparison)\b", low) and
                         re.search(r"\b(chatbot|agent)\b", low))
    math_match = re.search(r"(?:calculate|compute|evaluate)\s+(.+)$", q, re.I)

    if math_match:
        expr = math_match.group(1).strip().rstrip("?.!")
        value = calculate(expr)
        intent, args = "calculator", {"expression": expr}
        tool_output = {"success": True, "result": value}
    else:
        # Extract a subject phrase from common natural-language constructions.
        # Examples: "find Introduction to AI", "for finding DBMS", and
        # "compare chatbot and agent for finding Introduction to AI".
        candidate = q
        marker = re.search(
            r"\b(?:for\s+)?(?:finding|find|search(?:ing)?|looking\s+up|look\s+up)\s+(.+)$",
            q, re.I)
        if marker:
            candidate = marker.group(1)
        candidate = re.sub(r"[?.!]+$", "", candidate).strip()
        candidate = re.sub(r"^(?:the\s+)?(?:course|subject)\s+(?:named|called)\s+", "", candidate, flags=re.I)
        candidate = re.sub(r"^(?:the\s+)?(?:course|subject)\s+", "", candidate, flags=re.I)

        list_all = bool(re.search(r"\b(all|every|available)\s+(?:the\s+)?courses?\b", low)
                        or re.search(r"\b(courses?|subjects?)\s+(?:in|from)\s+(?:the\s+)?database\b", low))
        # A generic comparison about "finding courses" is a catalogue request;
        # a comparison containing a named subject is a targeted lookup.
        if is_comparison and re.fullmatch(r"(?:the\s+)?courses?", candidate, re.I):
            list_all = True
        if is_comparison and re.search(r"\b(?:courses?|subjects?)\b", candidate, re.I) and not re.search(r"\b(?:introduction|artificial|database|machine|computer|cloud|deep|software|network|programming|[A-Z]{2,}\d{2,})\b", candidate, re.I):
            list_all = True

        generic_request = bool(re.search(r"\b(course|courses|subject|subjects|class|curriculum|database|find|search|list|show)\b", low))
        # A bare subject title is also a valid lookup request.
        bare_title_match = bool(course_lookup(candidate).get("matches")) if candidate else False
        if is_comparison or generic_request or candidate != q or bare_title_match:
            query = "" if list_all else candidate
            intent, args = "course_lookup", {"query": query}
            tool_output = course_lookup(query)
        else:
            # For non-database questions, perform an actual text-analysis tool
            # rather than silently querying the course catalogue.
            intent, args = "text_analysis", {"text": q}
            tool_output = {"characters": len(q), "words": len(q.split()),
                           "keywords": re.findall(r"[A-Za-z][A-Za-z0-9_-]*", q)[:12]}

    return {
        "success": bool(tool_output.get("success", True)) if isinstance(tool_output, dict) else True,
        "chatbot": {"mode": "text_only", "tool_calls": 0,
                    "response": f"Text-only chatbot: I can discuss '{q}', but I did not query the database or execute a tool."},
        "agent": {"mode": "tool_using_agent", "decision": f"Selected {intent} based on the request intent.",
                  "tool": intent, "arguments": args, "output": tool_output},
        "comparison": {"chatbot_tool_calls": 0, "agent_tool_calls": 1,
                       "difference": "The chatbot produced a text-only response; the agent selected and executed a local tool.",
                       "agent_tool": intent,
                       "agent_result_count": len(tool_output.get("matches", [])) if isinstance(tool_output, dict) else None},
    }

def _lab2(text):
    from .runtime import calculate, course_lookup
    low=text.strip().lower()
    if low.startswith("calculate "):
        expr=text.strip()[9:].strip(); value=calculate(expr); return {"success":True,"tool":"calculator","arguments":{"expression":expr},"output":value,"result":value}
    if low.startswith(("find course ","search course ","course ")):
        q=text.strip().split(" ",2)[-1]; return {"success":True,"tool":"academic_course_lookup","arguments":{"query":q},"output":course_lookup(q),"result":course_lookup(q)}
    if low.startswith("analyse ") or low.startswith("analyze "):
        s=text.strip().split(" ",1)[1]; return {"success":True,"tool":"text_analyzer","result":{"characters":len(s),"words":len(s.split()),"lines":len(s.splitlines()),"unique_words":len(set(re.findall(r"\w+",s.lower()))),"top_terms":_top_terms(s)}}
    if low in ("list tools","tools","help"):
        return {"success":True,"tools":[{"name":"calculator","input":"calculate (12+8)*3"},{"name":"academic_course_lookup","input":"find course Artificial Intelligence"},{"name":"text_analyzer","input":"analyse your own text"}]}
    return {"success":True,"message":"No tool was run because the command was not recognized.","available_commands":["calculate <expression>","find course <course name>","analyse <arbitrary text>","list tools"]}

def _top_terms(text, limit=8):
    from collections import Counter
    words=re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}",text.lower())
    stop={"the","and","for","with","that","this","from","are","was","were","you","your","have","has","will","into"}
    return [{"term":w,"count":n} for w,n in Counter(x for x in words if x not in stop).most_common(limit)]

def _lab3(text):
    from .runtime import _conn, calculate, course_lookup
    data=_json(text)
    low=text.strip().lower()
    with _conn() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS custom_skills(name TEXT PRIMARY KEY, description TEXT, operation TEXT, version INTEGER, created_at TEXT, updated_at TEXT)")
        data=_json(text)
        low=text.strip().lower()
        if low in ("list skills","show skills","skills"):
            rows=[dict(r) for r in conn.execute("SELECT name,description,operation,version,created_at,updated_at FROM custom_skills ORDER BY name")]
            return {"success":True,"built_in_skills":["calculator","course_lookup","text_analysis"],"custom_skills":rows}
        if data and data.get("action")=="create":
            name=str(data.get("name","")).strip().lower().replace(" ","_")
            desc=str(data.get("description","")).strip(); op=str(data.get("operation","")).strip()
            allowed={"uppercase","lowercase","word_count","character_count","extract_emails","calculate","course_lookup"}
            if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}",name) or not desc or op not in allowed: raise ValueError("Provide name, description and an allowed operation: "+", ".join(sorted(allowed)))
            old=conn.execute("SELECT version FROM custom_skills WHERE name=?",(name,)).fetchone(); version=(old[0]+1) if old else 1
            conn.execute("INSERT INTO custom_skills VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET description=excluded.description,operation=excluded.operation,version=excluded.version,updated_at=excluded.updated_at",(name,desc,op,version,_now(),_now())); conn.commit()
            return {"success":True,"created":name,"version":version,"operation":op,"reusable":True}
        if data and data.get("action")=="run":
            name=str(data.get("name","")); arg=str(data.get("input",""))
            row=conn.execute("SELECT * FROM custom_skills WHERE name=?",(name,)).fetchone()
            if not row: raise ValueError(f"Unknown custom skill: {name}")
            return {"success":True,"skill":name,"version":row["version"],"result":_apply_skill(row["operation"],arg)}
        if low.startswith("calculate "): return {"success":True,"skill":"calculator","result":calculate(text[9:])}
        return {"success":True,"hint":"Use JSON action=create to register a reusable skill, action=run to execute it, or 'list skills'.","example_create":{"action":"create","name":"clean_text","description":"Convert text to uppercase","operation":"uppercase"},"example_run":{"action":"run","name":"clean_text","input":"hello world"},"skills":_lab3("list skills")}

def _apply_skill(op, value):
    from .runtime import calculate, course_lookup
    if op=="uppercase": return value.upper()
    if op=="lowercase": return value.lower()
    if op=="word_count": return {"words":len(value.split())}
    if op=="character_count": return {"characters":len(value)}
    if op=="extract_emails": return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",value)
    if op=="calculate": return calculate(value)
    if op=="course_lookup": return course_lookup(value)
    raise ValueError("Unsupported skill operation")

def _lab4(text):
    from .runtime import remember, recall
    data=_json(text)
    if data:
        user=str(data.get("user_id","demo"))[:100]
        action=data.get("action","recall")
        if action=="remember": return {"success":True,"memory":remember(str(data.get("text","")),user)}
        if action=="recall": return {"success":True,"user_id":user,"memories":recall(str(data.get("query","")),user)}
        raise ValueError("action must be remember or recall")
    low=text.strip().lower()
    if low.startswith(("remember ","store ")): return {"success":True,"memory":remember(text.split(" ",1)[1])}
    if low.startswith(("recall","retrieve")):
        q=text.split(" ",1)[1] if " " in text else ""; return {"success":True,"memories":recall(q)}
    return {"success":True,"commands":["remember <fact>","recall [keyword]"],"example_json":{"action":"remember","user_id":"student-101","text":"I prefer examples in Python"},"recent_memories":recall()}

def _lab5(text):
    from .runtime import list_connectors, execute_connector
    data=_json(text); low=text.strip().lower()
    if data:
        name=data.get("connector"); args=data.get("arguments",{})
        if data.get("action")=="list": return {"success":True,"connectors":list_connectors(),"protocol":"Internal registry API; not a full MCP server/SDK."}
        if data.get("action")=="call": return {"success":True,"connector":name,"result":execute_connector(name,**args)}
    if low in ("list connectors","show connectors","connectors"): return {"success":True,"connectors":list_connectors(),"protocol_note":"Internal connector registry with typed actions; not a full official MCP implementation."}
    if low.startswith("find course "): return {"success":True,"connector":"academic_db","output":execute_connector("academic_db",query=text[12:])}
    if low.startswith("list files"): return {"success":True,"connector":"workspace_files","output":execute_connector("workspace_files",action="list")}
    if low.startswith("read file "): return {"success":True,"connector":"workspace_files","output":execute_connector("workspace_files",action="read",path=text[10:])}
    if low.startswith("write file "):
        _,name,_,content=text.split(" ",3); return {"success":True,"connector":"workspace_files","output":execute_connector("workspace_files",action="write",path=name,content=content)}
    return {"success":True,"hint":"Use JSON {action:'list'} or {action:'call', connector:'workspace_files', arguments:{action:'list'}}.","connectors":list_connectors()}

def _lab6(text):
    from .runtime import _run
    events=[{"seq":1,"state":"accepted","at":_now(),"detail":"Request validated"},{"seq":2,"state":"planning","at":_now(),"detail":"Selecting a safe local tool workflow"},{"seq":3,"state":"running","at":_now(),"detail":"Executing Lab 2 tool workflow"}]
    try:
        result=_run(2,text)
        events.append({"seq":4,"state":"completed","at":_now(),"detail":"Workflow returned"})
        return {"success":True,"runtime_id":uuid.uuid4().hex,"state":"completed","events":events,"result":result,"retry_policy":"No automatic retry for deterministic local actions"}
    except Exception as exc:
        events.append({"seq":4,"state":"failed","at":_now(),"detail":str(exc)})
        return {"success":False,"runtime_id":uuid.uuid4().hex,"state":"failed","events":events,"error":str(exc)}

def _lab7(text):
    data=_json(text)
    if data and isinstance(data.get("nodes"),list):
        nodes=data["nodes"]
        if len(nodes)>30: raise ValueError("Graph limited to 30 nodes")
        by={str(n.get("id")):n for n in nodes}
        if len(by)!=len(nodes) or "None" in by: raise ValueError("Every graph node needs a unique id")
        done={}; order=[]; pending=set(by)
        while pending:
            ready=[i for i in pending if all(str(dep) in done for dep in by[i].get("depends_on",[]))]
            if not ready: raise ValueError("Graph contains a cycle or unknown dependency")
            for i in ready:
                n=by[i]; op=n.get("operation","word_count"); value=str(n.get("input",data.get("input","")))
                done[i]=_graph_op(op,value); order.append(i); pending.remove(i)
        return {"success":True,"execution_order":order,"nodes":[{"id":i,"status":"completed","output":done[i]} for i in order],"result":done}
    s=text.strip(); return {"success":True,"graph_id":uuid.uuid4().hex,"nodes":[{"id":"request","depends_on":[],"status":"completed","output":s},{"id":"profile","depends_on":["request"],"status":"completed","output":{"words":len(s.split()),"characters":len(s)}},{"id":"terms","depends_on":["request"],"status":"completed","output":_top_terms(s)},{"id":"summary","depends_on":["profile","terms"],"status":"completed","output":f"Input contains {len(s.split())} words; extracted {len(_top_terms(s))} key terms."}],"note":"Supply JSON nodes to define a custom DAG; dependencies are validated before execution."}
def _graph_op(op,s):
    if op=="word_count": return {"words":len(s.split())}
    if op=="character_count": return {"characters":len(s)}
    if op=="top_terms": return _top_terms(s)
    if op=="uppercase": return s.upper()
    if op=="extract_emails": return re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",s)
    raise ValueError(f"Unknown graph operation: {op}")

def _lab8(text):
    data=_json(text); s=str(data.get("text", "")) if data else text
    if not s.strip(): raise ValueError("Provide text or JSON {text: ...}")
    def keyword(): return {"agent":"keyword_specialist","terms":_top_terms(s,10)}
    def sentiment():
        pos={"good","great","excellent","success","stable","resolved","happy","improved"}; neg={"bad","failed","failure","error","crash","urgent","broken","poor","slow"}
        words=set(re.findall(r"[a-z]+",s.lower())); p=sorted(words&pos); n=sorted(words&neg)
        return {"agent":"sentiment_specialist","positive_signals":p,"negative_signals":n,"label":"negative" if len(n)>len(p) else "positive" if p else "neutral"}
    def entities(): return {"agent":"entity_specialist","emails":re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",s),"numbers":re.findall(r"\b\d+(?:\.\d+)?\b",s)}
    def stats(): return {"agent":"statistics_specialist","characters":len(s),"words":len(s.split()),"lines":len(s.splitlines())}
    jobs={"keyword":keyword,"sentiment":sentiment,"entities":entities,"statistics":stats}; outputs={}; timings={}
    with ThreadPoolExecutor(max_workers=4,thread_name_prefix="lab8-agent") as pool:
        futures={pool.submit(fn):name for name,fn in jobs.items()}
        for f in as_completed(futures):
            name=futures[f]; t=time.perf_counter(); outputs[name]=f.result(); timings[name]="completed"
    return {"success":True,"execution_mode":"concurrent specialist workers (ThreadPoolExecutor)","agents_dispatched":4,"results":outputs,"statuses":timings,"aggregation":"All specialist outputs were collected before final response."}

def _lab9(text):
    from lab9.deep_research import research_brief, SOURCES
    data=_json(text)
    if data:
        topic=str(data.get("topic","")); extra=data.get("sources",[])
        if not topic.strip(): raise ValueError("topic is required")
        # User-supplied evidence is clearly separated and attributed to its supplied title.
        base=research_brief(topic)
        supplied=[]
        for item in extra[:20]:
            if isinstance(item,dict) and item.get("title") and item.get("text"):
                supplied.append({"source":str(item["title"]),"evidence":str(item["text"]),"provenance":"user_supplied","relevance_terms":sorted(set(re.findall(r"[a-z0-9]+",topic.lower())) & set(re.findall(r"[a-z0-9]+",str(item["text"]).lower())))})
        base["user_supplied_evidence"]=supplied
        base["source_count_total"]=len(base.get("evidence_table",[]))+len(supplied)
        return base
    return research_brief(text)

def _lab10(text):
    from lab10.cloud_ops import analyse_logs
    data=_json(text)
    if data:
        log=str(data.get("logs", "")); service=str(data.get("service","unspecified")); env=str(data.get("environment","unspecified"))
        result=analyse_logs(log); result.update({"service":service,"environment":env,"log_lines":len(log.splitlines()),"timeline":[{"line":i+1,"text":line} for i,line in enumerate(log.splitlines()) if re.search(r"error|warn|fail|timeout|exception|critical",line,re.I)]})
        return result
    return analyse_logs(text)

def _lab11(text):
    from lab11.sdlc_factory import build_sdlc
    data=_json(text)
    req=str(data.get("requirement","")) if data else text
    result=build_sdlc(req)
    if not result.get("success"): return result
    words=req.split(); verbs=[w for w in words if w.lower() in {"create","build","allow","enable","display","manage","export","upload","search","generate","track","notify"}]
    result["user_story"]=f"As a user, I want {req[:240]} so that the workflow is completed reliably."
    result["acceptance_criteria"]=[f"Given the requirement '{req[:180]}', when valid input is provided, then the expected result is produced.","Invalid input is rejected with a clear validation message.","Execution is traceable and failures are logged."]
    result["test_matrix"]=[{"type":"positive","case":"Valid requirement/input","expected":"Successful artifact generation"},{"type":"negative","case":"Empty or malformed input","expected":"Validation error"},{"type":"boundary","case":"Maximum supported input size","expected":"Handled without crash"},{"type":"security","case":"Untrusted text input","expected":"Treated as data, not executable code"}]
    result["risks"]=["Ambiguous acceptance criteria","Unvalidated external dependencies","Regression in existing workflows"]
    result["detected_action_verbs"]=verbs
    return result

def _lab12(text):
    from .runtime import _conn
    data=_json(text)
    if not data and isinstance(text,str) and text.strip().lower().startswith("propose "):
        # Backward-compatible draft mode: records a proposal only; it does not
        # assert privacy/cost validation and cannot trigger a production action.
        with _conn() as c:
            aid=uuid.uuid4().hex
            draft={"legacy_draft":text.strip()[8:],"validation":"incomplete; replace with structured proposal for governance checks"}
            c.execute("INSERT INTO approvals(id,action,status,created_at) VALUES(?,?,?,?)",(aid,json.dumps(draft),"pending",_now()))
            c.execute("INSERT INTO audit_events(event,detail,created_at) VALUES(?,?,?)",("approval_requested_legacy_draft",aid,_now()))
        return {"success":True,"approval_id":aid,"status":"pending","legacy_draft":True,"warning":"Draft recorded for workflow compatibility. It is not a validated change request and no production action is executed."}
    if not data:
        return {"success":True,"required_fields":{"action":"propose","diagnosis":"what happened","proposed_change":"what should change","rollback_plan":"how to reverse","privacy_scrubbed":True,"estimated_cost":0,"budget":100},"message":"Submit a JSON proposal. Approval records a human decision only; it never deploys or modifies production."}
    if data.get("action")=="list":
        with _conn() as c: rows=[dict(r) for r in c.execute("SELECT * FROM approvals ORDER BY created_at DESC LIMIT 50")]
        return {"success":True,"approvals":rows}
    required=["diagnosis","proposed_change","rollback_plan"]
    missing=[k for k in required if not str(data.get(k," ")).strip()]
    if missing: return {"success":True,"rejected":True,"reason":"Missing mandatory fields","missing":missing}
    if data.get("privacy_scrubbed") is not True: return {"success":True,"rejected":True,"reason":"Input must be explicitly privacy-scrubbed"}
    try: cost=float(data.get("estimated_cost")) ; budget=float(data.get("budget",100))
    except (TypeError,ValueError): return {"success":True,"rejected":True,"reason":"Numeric estimated_cost and budget are required"}
    if cost<0 or budget<0: return {"success":True,"rejected":True,"reason":"Cost and budget cannot be negative"}
    if cost>budget and data.get("finance_approved") is not True: return {"success":True,"rejected":True,"reason":"Finance approval required because estimated cost exceeds budget"}
    with _conn() as c:
        aid=uuid.uuid4().hex
        action=json.dumps({k:data.get(k) for k in required+['privacy_scrubbed','estimated_cost','budget']},ensure_ascii=False)
        c.execute("INSERT INTO approvals(id,action,status,created_at) VALUES(?,?,?,?)",(aid,action,"pending",_now()))
        c.execute("INSERT INTO audit_events(event,detail,created_at) VALUES(?,?,?)",("approval_requested",aid,_now()))
    return {"success":True,"approval_id":aid,"status":"pending","requires_human_decision":True,"production_action_executed":False,"proposal":data}

def _lab13(text):
    from lab13.engineering_agent import analyse_engineering_input, DEFAULTS

    data = _json(text)

    # Handle structured JSON requests
    if data and "readings" in data:

        domain = str(data.get("domain", "mechanical")).lower()

        if domain not in DEFAULTS:
            raise ValueError(
                "domain must be mechanical, civil or electrical"
            )

        readings = data["readings"]

        if not isinstance(readings, list) or not readings:
            raise ValueError(
                "readings must be a non-empty list of objects"
            )

        if not all(isinstance(row, dict) for row in readings):
            raise ValueError(
                "Every reading must be a JSON object"
            )

        # Perform analysis on every reading
        result = analyse_engineering_input(json.dumps(readings))

        if not result.get("success"):
            return result

        # Load domain-specific thresholds
        custom = data.get("thresholds", {})

        if not isinstance(custom, dict):
            raise ValueError("thresholds must be a JSON object")

        thresholds = dict(DEFAULTS[domain])

        thresholds.update({
            k: float(v)
            for k, v in custom.items()
        })

        # Recheck every reading using the selected domain
        all_breaches = []
        reading_reports = []

        for report in result.get("reading_reports", []):

            reading_breaches = []

            for sensor, value in report["sensor_values"].items():

                if sensor in thresholds and value >= thresholds[sensor]:

                    breach = {
                        "reading_number": report["reading_number"],
                        "sensor": sensor,
                        "value": value,
                        "limit": thresholds[sensor],
                        "status": "ABNORMAL"
                    }

                    reading_breaches.append(breach)
                    all_breaches.append(breach)

            report["threshold_breaches"] = reading_breaches

            report["status"] = (
                "ABNORMAL" if reading_breaches else "NORMAL"
            )

            reading_reports.append(report)

        # Generate final engineering assessment
        result.update({
            "domain": domain,
            "thresholds": thresholds,
            "reading_reports": reading_reports,
            "threshold_breaches": all_breaches,
            "status": (
                "ALARM" if all_breaches
                else "NORMAL_OR_UNASSESSED"
            ),
            "threshold_note": (
                "Use site-approved engineering limits; "
                "defaults are illustrative."
            ),
            "recommended_action": (
                "Escalate to a qualified engineer for review. "
                "Do not automatically control equipment."
                if all_breaches
                else "Continue monitoring and validate against approved site limits."
            )
        })

        return result

    # Handle ordinary text, CSV and key-value inputs
    result = analyse_engineering_input(text)

    if (
        not result.get("success")
        and "Could not parse" in result.get("error", "")
    ):
        return {
            "success": True,
            "message": (
                "Engineering agent is ready. Provide JSON readings, "
                "CSV with headers, or key=value lines."
            ),
            "supported_domains": list(DEFAULTS),
            "illustrative_thresholds": DEFAULTS,
            "example": {
                "domain": "civil",
                "readings": [
                    {
                        "crack_width_mm": 0.1,
                        "displacement_mm": 2.0
                    }
                ]
            }
        }

    return result

def _lab14(text):
    from .runtime import _conn, remember, recall
    data=_json(text); low=text.strip().lower()
    if data:
        action=data.get("action","triage"); user=str(data.get("user_id","demo"))[:100]
        if action=="create":
            issue=str(data.get("issue","" )).strip()
            if len(issue)<5: raise ValueError("Issue must contain at least 5 characters")
            with _conn() as c:
                cur=c.execute("INSERT INTO helpdesk_tickets(user_key,issue,status,created_at) VALUES(?,?,?,?)",(user,issue,"open",_now()))
                tid=cur.lastrowid
            return {"success":True,"ticket_id":tid,"user_id":user,"issue":issue,"status":"open","persistent":True,"triage":_triage(issue)}
        if action=="list":
            with _conn() as c: rows=[dict(r) for r in c.execute("SELECT * FROM helpdesk_tickets WHERE user_key=? ORDER BY id DESC LIMIT 100",(user,))]
            return {"success":True,"tickets":rows}
        if action in ("get","update","close"):
            tid=int(data.get("ticket_id"))
            with _conn() as c:
                row=c.execute("SELECT * FROM helpdesk_tickets WHERE id=? AND user_key=?",(tid,user)).fetchone()
                if not row: return {"success":False,"error":"Ticket not found for this user"}
                if action in ("update","close"):
                    status="closed" if action=="close" else str(data.get("status","in_progress"))
                    if status not in ("open","in_progress","waiting","closed"): raise ValueError("Invalid ticket status")
                    c.execute("UPDATE helpdesk_tickets SET status=? WHERE id=? AND user_key=?",(status,tid,user))
                    row=c.execute("SELECT * FROM helpdesk_tickets WHERE id=?",(tid,)).fetchone()
                return {"success":True,"ticket":dict(row),"persistent":True}
        if action=="triage":
            issue=str(data.get("issue","" )).strip()
            if not issue: raise ValueError("issue is required")
            triage=_triage(issue)
            if triage["resolution"]=="faq": return {"success":True,"triage":triage,"ticket_created":False}
            return _lab14(json.dumps({"action":"create","user_id":user,"issue":issue}))
        raise ValueError("action must be triage/create/list/get/update/close")
    if low.startswith("ticket "):
        return _lab14(json.dumps({"action":"create","issue":text[7:].strip()}))
    if low.startswith("check ticket "):
        tid=int(text[13:]); return _lab14(json.dumps({"action":"get","ticket_id":tid}))
    if low.startswith("close ticket "):
        tid=int(text[13:]); return _lab14(json.dumps({"action":"close","ticket_id":tid}))
    if low.startswith("list tickets"): return _lab14(json.dumps({"action":"list"}))
    return {"success":True,"workflow":"capstone_helpdesk","commands":["ticket <issue>","check ticket <id>","close ticket <id>","list tickets"],"faq_topics":["wifi","password","portal","printer","email"],"persistent_storage":"SQLite"}
def _triage(issue):
    rules={"wifi":"Connect to the campus secure Wi-Fi and authenticate with your institution credentials.","password":"Use the official password-reset process; never share your password with support staff.","printer":"Check printer power, network connection and queue; contact IT if the queue remains blocked.","portal":"Try a supported browser and clear cached site data; report the exact error if it persists.","email":"Check mailbox quota and official mail-service status; do not share verification codes."}
    for key,answer in rules.items():
        if key in issue.lower(): return {"resolution":"faq","topic":key,"answer":answer,"source":"built_in_helpdesk_faq"}
    return {"resolution":"escalated","reason":"No verified FAQ matched; ticket recommended."}

HANDLERS={1:_lab1,2:_lab2,3:_lab3,4:_lab4,5:_lab5,6:_lab6,7:_lab7,8:_lab8,9:_lab9,10:_lab10,11:_lab11,12:_lab12,13:_lab13,14:_lab14}
def execute(lab_id:int,text:str):
    if lab_id not in HANDLERS: raise ValueError("Lab ID must be between 1 and 14")
    return HANDLERS[lab_id](text)
