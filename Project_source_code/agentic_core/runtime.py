from __future__ import annotations
import ast, json, os, re, sqlite3, time, uuid, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
STATE_DB=Path(os.environ.get("AGENTIC_CORE_DB", str(ROOT/"course_organizer"/"database"/"agentic_core.sqlite3")))
LEGACY_DB=Path(os.environ.get("COURSE_ORGANIZER_DB", str(ROOT/"course_organizer"/"database"/"course_organizer.db")))
FILE_ROOT=ROOT/"agentic_workspace"
FILE_ROOT.mkdir(parents=True,exist_ok=True)

class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()

def _conn():
    STATE_DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(STATE_DB,timeout=10,factory=_ClosingConnection)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS executions(id TEXT PRIMARY KEY, lab_id INTEGER, input TEXT, status TEXT, output TEXT, started_at TEXT, duration REAL);
    CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT, text TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS skills(name TEXT PRIMARY KEY, description TEXT, version TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS connectors(name TEXT PRIMARY KEY, description TEXT, risk TEXT);
    CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, action TEXT, status TEXT, created_at TEXT, decided_at TEXT);
    CREATE TABLE IF NOT EXISTS helpdesk_tickets(id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT, issue TEXT, status TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_events(id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, detail TEXT, created_at TEXT);
    """)
    for row in [("calculator","Safely evaluate arithmetic expressions","1.0"),("course_lookup","Search the existing academic database read-only","1.0"),("text_analysis","Analyse supplied text for keywords and counts","1.0")]:
        c.execute("INSERT OR IGNORE INTO skills VALUES(?,?,?,?)",(*row,datetime.now(timezone.utc).isoformat()))
    for row in [("academic_db","Read-only access to existing academic records","low"),("workspace_files","Sandboxed project workspace files","medium"),("http_get","HTTP GET to explicitly supplied public URL","medium")]:
        c.execute("INSERT OR IGNORE INTO connectors VALUES(?,?,?)",row)
    c.commit()
    return c

class Arithmetic(ast.NodeVisitor):
    OPS={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b,ast.Pow:lambda a,b:a**b,ast.Mod:lambda a,b:a%b,ast.FloorDiv:lambda a,b:a//b}
    def visit_Expression(self,n): return self.visit(n.body)
    def visit_Constant(self,n):
        if type(n.value) not in (int,float): raise ValueError("Only numeric values are allowed")
        return n.value
    def visit_UnaryOp(self,n):
        if isinstance(n.op,ast.USub): return -self.visit(n.operand)
        if isinstance(n.op,ast.UAdd): return self.visit(n.operand)
        raise ValueError("Unsupported unary operator")
    def visit_BinOp(self,n):
        fn=self.OPS.get(type(n.op))
        if not fn: raise ValueError("Unsupported operator")
        a,b=self.visit(n.left),self.visit(n.right)
        if isinstance(n.op,ast.Pow) and abs(b)>8: raise ValueError("Exponent too large")
        return fn(a,b)
    def generic_visit(self,n): raise ValueError("Unsupported expression")
def calculate(expr):
    if not isinstance(expr,str) or len(expr)>200: raise ValueError("Invalid expression")
    return Arithmetic().visit(ast.parse(expr,mode="eval"))

def course_lookup(query=""):
    """Read-only, forgiving search over the Course Organizer's real courses table.

    Empty/list-all queries return all courses. Natural-language questions are
    reduced to meaningful terms and matched against code, name and description.
    """
    if not LEGACY_DB.exists():
        return {"database":"not_found","matches":[],"database_path":str(LEGACY_DB)}
    q=str(query or "").strip()
    qlow=q.lower().strip(" .?!")
    list_all = (not qlow) or (bool(re.search(r"\b(all|available|every|list|show)\b", qlow)) and
                bool(re.search(r"\b(course|courses|subject|subjects|database)\b", qlow)))
    stop={"please","find","search","show","list","the","a","an","course","courses","subject","subjects","related","to","about","for","in","from","database","available","all","me","which","what","is","are","teach","teaches","named","called","and","or","compare","comparison","chatbot","agent","agents","finding","lookup","look","up","please","can","you","could","would","i","want","need","give","tell","about"}
    terms=[t for t in re.findall(r"[a-z0-9]+",qlow) if t not in stop and len(t)>1]
    c=sqlite3.connect(f"file:{LEGACY_DB}?mode=ro",uri=True); c.row_factory=sqlite3.Row
    try:
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        table=next((t for t in ("courses","course") if t in tables),None)
        if not table: return {"database":"available","matches":[],"note":"No recognized courses table"}
        cols=[r[1] for r in c.execute(f'PRAGMA table_info("{table}")')]
        searchable=[x for x in ("course_code","code","name","course_name","title","description") if x in cols]
        namecol=next((x for x in ("name","course_name","title") if x in cols),None)
        if not namecol: return {"database":"available","matches":[],"note":"Course table has no recognized name column"}
        selected=c.execute(f'SELECT * FROM "{table}" LIMIT 500').fetchall()
        if list_all:
            matches=[dict(r) for r in selected]
        else:
            ranked=[]
            for row in selected:
                values={col:str(row[col] or "").lower() for col in searchable}
                hay=" ".join(values.values())
                score=sum(3 if term in values.get(namecol,"") else 1
                      for term in terms if len(term) >= 3 and
                      re.search(r"(?<![a-z0-9])"+re.escape(term)+r"(?![a-z0-9])", hay))
                # Exact phrase in name/code/description gets a strong preference.
                if qlow and any(qlow in value for value in values.values()): score+=10
                if score: ranked.append((score,dict(row)))
            # If the requested phrase occurs in a course title, prefer title
            # matches and exclude records that only mention the phrase in a
            # description. This prevents a specific title lookup returning
            # unrelated catalogue entries.
            title_matches = [dict(row) for row in selected
                             if qlow and qlow in str(row[namecol] or "").lower()]
            if title_matches:
                matches = title_matches
            else:
                ranked.sort(key=lambda item:item[0],reverse=True)
                matches=[row for _,row in ranked[:50]]
        return {"database":"existing_course_organizer","database_path":str(LEGACY_DB),"table":table,
                "query":q,"search_terms":terms,"total_courses":len(selected),"matches":matches}
    finally:
        c.close()

def remember(text,user_key="demo"):
    if not text or not text.strip(): raise ValueError("Memory text is required")
    with _conn() as c:
        cur=c.execute("INSERT INTO memories(user_key,text,created_at) VALUES(?,?,?)",(user_key,text.strip(),datetime.now(timezone.utc).isoformat()))
        c.execute("INSERT INTO audit_events(event,detail,created_at) VALUES(?,?,?)",("memory_saved",f"user={user_key}; id={cur.lastrowid}",datetime.now(timezone.utc).isoformat()))
        return {"id":cur.lastrowid,"text":text.strip(),"persistent":True}
def recall(query="",user_key="demo"):
    with _conn() as c:
        if query:
            rows=c.execute("SELECT id,text,created_at FROM memories WHERE user_key=? AND text LIKE ? ORDER BY id DESC LIMIT 20",(user_key,f"%{query}%")).fetchall()
        else: rows=c.execute("SELECT id,text,created_at FROM memories WHERE user_key=? ORDER BY id DESC LIMIT 20",(user_key,)).fetchall()
        return [dict(r) for r in rows]
def list_skills():
    with _conn() as c:return [dict(r) for r in c.execute("SELECT * FROM skills ORDER BY name")]
def execute_skill(name,**kwargs):
    if name=="calculator": return {"success":True,"result":calculate(kwargs.get("expression",""))}
    if name=="course_lookup": return {"success":True,"result":course_lookup(kwargs.get("query",""))}
    if name=="text_analysis":
        t=kwargs.get("text","")
        return {"success":True,"result":{"characters":len(t),"words":len(t.split()),"lines":len(t.splitlines())}}
    raise ValueError(f"Unknown skill: {name}")
def list_connectors():
    with _conn() as c:return [dict(r) for r in c.execute("SELECT * FROM connectors ORDER BY name")]
def execute_connector(name,**kwargs):
    if name=="academic_db": return course_lookup(kwargs.get("query",""))
    if name=="workspace_files":
        action=kwargs.get("action","list"); p=Path(kwargs.get("path","")).name
        target=(FILE_ROOT/p).resolve()
        if action=="list": return sorted(x.name for x in FILE_ROOT.iterdir() if x.is_file())
        if target.parent!=FILE_ROOT.resolve(): raise ValueError("Path is outside workspace")
        if action=="read": return target.read_text(encoding="utf8")
        if action=="write":
            target.write_text(str(kwargs.get("content","")),encoding="utf8"); return {"written":p}
        raise ValueError("Use list, read or write")
    if name=="http_get":
        url=kwargs.get("url","")
        parsed=urllib.parse.urlparse(url)
        if parsed.scheme!="https" or not parsed.hostname: raise ValueError("Only valid HTTPS URLs are allowed")
        req=urllib.request.Request(url,headers={"User-Agent":"AcademicAgent/1.0"})
        with urllib.request.urlopen(req,timeout=5) as r:
            return {"status":r.status,"content_type":r.headers.get("Content-Type"),"body":r.read(5000).decode("utf8","replace")}
    raise ValueError(f"Unknown connector: {name}")

def _run(lab_id,text):
    # All labs route through one shared, testable dispatch layer.
    from .advanced import execute
    return execute(lab_id, text)

def run_lab(lab_id,text):
    if not isinstance(text,str) or not text.strip(): raise ValueError("Input is required")
    started=time.perf_counter(); rid=uuid.uuid4().hex
    try:
        output=_run(lab_id,text); status="completed" if not (isinstance(output,dict) and output.get("success") is False) else "failed"
    except Exception as e:
        output={"error":f"{type(e).__name__}: {e}"}; status="failed"
    duration=round(time.perf_counter()-started,6)
    with _conn() as c:
        c.execute("INSERT INTO executions VALUES(?,?,?,?,?,?,?)",(rid,lab_id,text,status,json.dumps(output,default=str),datetime.now(timezone.utc).isoformat(),duration))
        c.execute("INSERT INTO audit_events(event,detail,created_at) VALUES(?,?,?)",("lab_run",f"{rid}: lab={lab_id}; status={status}",datetime.now(timezone.utc).isoformat()))
    return {"success":status=="completed","run_id":rid,"lab_id":lab_id,"status":status,"duration_seconds":duration,"input":text,"output":output}
def list_traces(limit=50):
    with _conn() as c:return [dict(r) for r in c.execute("SELECT * FROM executions ORDER BY started_at DESC LIMIT ?",(limit,))]

def decide_approval(approval_id, decision):
    if decision not in ("approved","rejected"): raise ValueError("Decision must be approved or rejected")
    with _conn() as c:
        cur=c.execute("UPDATE approvals SET status=?,decided_at=? WHERE id=? AND status='pending'",(decision,datetime.now(timezone.utc).isoformat(),approval_id))
        if cur.rowcount!=1: return {"success":False,"error":"Approval not found or already decided"}
        c.execute("INSERT INTO audit_events(event,detail,created_at) VALUES(?,?,?)",("approval_decided",f"{approval_id}:{decision}",datetime.now(timezone.utc).isoformat()))
        return {"success":True,"approval_id":approval_id,"status":decision,"executed":False,"note":"Decision recorded; no production action is executed."}
