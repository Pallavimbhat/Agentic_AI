"""Database-backed academic workflows: planning, memory, reminders, and professor summaries.

These are deterministic, auditable workflows. They do not claim autonomous LLM reasoning;
optionally pair them with AcademicAssistantAgent for language understanding.
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from typing import Any

class AcademicWorkflowService:
    def __init__(self, db):
        self.db = db
        self._init_tables()

    def _init_tables(self):
        with self.db._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS study_plans (
              id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
              title TEXT NOT NULL, goal TEXT NOT NULL, start_date TEXT NOT NULL,
              end_date TEXT NOT NULL, plan_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending_approval',
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS academic_memory (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
              memory_key TEXT NOT NULL, memory_value TEXT NOT NULL, updated_at TEXT NOT NULL,
              UNIQUE(user_id, memory_key)
            );
            CREATE TABLE IF NOT EXISTS academic_notifications (
              id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
              assignment_id INTEGER NOT NULL, message TEXT NOT NULL, due_at TEXT,
              created_at TEXT NOT NULL, read_at TEXT,
              UNIQUE(student_id, assignment_id, message)
            );
            CREATE TABLE IF NOT EXISTS agent_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
              workflow TEXT NOT NULL, status TEXT NOT NULL, trace_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """)

    @staticmethod
    def _now(): return datetime.now().replace(microsecond=0)

    def _trace(self, user_id, workflow, status, steps):
        self.db._execute("INSERT INTO agent_runs(user_id,workflow,status,trace_json,created_at) VALUES(?,?,?,?,?)",
                         (user_id, workflow, status, json.dumps(steps), self._now().isoformat()))

    def create_study_plan(self, student_id: int, goal: str, days: int = 5, hours_per_day: float = 2.0):
        if not goal.strip(): raise ValueError("Please provide a study goal.")
        if not 1 <= days <= 60: raise ValueError("days must be between 1 and 60.")
        if not 0.5 <= hours_per_day <= 16: raise ValueError("hours_per_day must be between 0.5 and 16.")
        trace=[]
        trace.append({"agent":"Orchestrator","action":"understand_goal","result":goal})
        assignments=self.db.list_student_assignments(student_id)
        trace.append({"agent":"Assignment Agent","tool":"list_student_assignments","records":len(assignments)})
        notes=self.db.list_student_notes(student_id)
        trace.append({"agent":"Resource Agent","tool":"list_student_notes","records":len(notes)})
        pending=[a for a in assignments if a.get("work_status") in ("Pending","Overdue")]
        def due(a):
            try: return datetime.fromisoformat(str(a.get('deadline'))).replace(tzinfo=None)
            except (ValueError,TypeError): return datetime.max
        pending.sort(key=lambda a:(0 if a.get('work_status')=='Overdue' else 1,due(a)))
        tasks=[]
        # Reserve first slots for outstanding work; then cover relevant notes/topics.
        for a in pending:
            tasks.append({"task":f"Complete: {a.get('title','Assignment')}","type":"assignment","priority":"High","deadline":a.get("deadline"),"course_code":a.get("course_code"),"status":"planned"})
        for n in notes:
            tasks.append({"task":f"Review notes: {n.get('title','Course notes')}","type":"study","priority":"Medium","course_code":n.get("course_code"),"note_id":n.get("id"),"status":"planned"})
        if not tasks: tasks=[{"task":goal.strip(),"type":"study","priority":"High","status":"planned"}]
        daily=[{"day":i+1,"date":(self._now()+timedelta(days=i)).date().isoformat(),"available_hours":hours_per_day,"tasks":[]} for i in range(days)]
        # Simple transparent allocation: one task per day round-robin, all remaining tasks assigned sequentially.
        for idx,task in enumerate(tasks):
            daily[min(idx,days-1)]["tasks"].append(task)
        # Verification: flag if pending tasks exceed the requested number of days.
        warnings=[]
        if len(pending)>days: warnings.append(f"{len(pending)} outstanding assignments exceed the {days}-day planning window; some days may be overloaded.")
        plan={"goal":goal.strip(),"days":daily,"pending_assignment_count":len(pending),"available_notes_count":len(notes),"warnings":warnings,
              "verification":{"has_tasks":bool(tasks),"days_within_requested_window":len(daily)==days,"requires_student_review":True}}
        now=self._now().isoformat(); start=daily[0]["date"]; end=daily[-1]["date"]
        plan_id=self.db._execute("INSERT INTO study_plans(student_id,title,goal,start_date,end_date,plan_json,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
          (student_id,"Academic study plan",goal.strip(),start,end,json.dumps(plan),"pending_approval",now,now))
        trace.append({"agent":"Planning Agent","action":"allocate_tasks","tasks_created":len(tasks),"days":days})
        trace.append({"agent":"Verification Agent","action":"check_constraints","warnings":warnings,"requires_approval":True})
        trace.append({"agent":"Memory/State Tool","action":"save_plan","plan_id":plan_id,"status":"pending_approval"})
        self._trace(student_id,"study_plan", "awaiting_approval", trace)
        return {"success":True,"plan_id":plan_id,"status":"pending_approval","plan":plan,"trace":trace,"message":"Review the plan and approve it before treating it as your active schedule."}

    def list_study_plans(self, student_id):
        rows=self.db._fetch_all("SELECT * FROM study_plans WHERE student_id=? ORDER BY id DESC",(student_id,))
        for r in rows:
            try:r["plan_json"]=json.loads(r["plan_json"])
            except (ValueError,TypeError): pass
        return rows

    def update_plan_status(self, student_id, plan_id, status):
        if status not in {"approved","rejected","completed"}: raise ValueError("status must be approved, rejected, or completed")
        row=self.db._fetch_one("SELECT id FROM study_plans WHERE id=? AND student_id=?",(plan_id,student_id))
        if not row: return None
        self.db._execute("UPDATE study_plans SET status=?,updated_at=? WHERE id=? AND student_id=?",(status,self._now().isoformat(),plan_id,student_id))
        self._trace(student_id,"study_plan_status",status,[{"agent":"Approval Gate","action":"student_decision","plan_id":plan_id,"status":status}])
        return self.db._fetch_one("SELECT * FROM study_plans WHERE id=? AND student_id=?",(plan_id,student_id))

    def remember(self, user_id, key, value):
        key=key.strip().lower(); value=value.strip()
        if not key or not value: raise ValueError("Both memory key and value are required.")
        now=self._now().isoformat()
        self.db._execute("INSERT INTO academic_memory(user_id,memory_key,memory_value,updated_at) VALUES(?,?,?,?) ON CONFLICT(user_id,memory_key) DO UPDATE SET memory_value=excluded.memory_value,updated_at=excluded.updated_at",(user_id,key,value,now))
        return {"success":True,"memory_key":key,"memory_value":value,"updated_at":now}

    def memories(self, user_id):
        return self.db._fetch_all("SELECT memory_key,memory_value,updated_at FROM academic_memory WHERE user_id=? ORDER BY memory_key",(user_id,))

    def run_deadline_monitor(self, student_id, within_hours=48):
        if not 1 <= within_hours <= 720: raise ValueError("within_hours must be between 1 and 720")
        now=self._now(); limit=now+timedelta(hours=within_hours); assignments=self.db.list_student_assignments(student_id); created=[]; trace=[]
        for a in assignments:
            if a.get("work_status") not in ("Pending","Overdue"): continue
            try: due=datetime.fromisoformat(str(a.get("deadline"))).replace(tzinfo=None)
            except (ValueError,TypeError): continue
            if due <= limit:
                label="overdue" if due < now else "due soon"
                message=f"{a.get('title','Assignment')} is {label} (deadline: {due.isoformat(sep=' ')})."
                self.db._execute("INSERT OR IGNORE INTO academic_notifications(student_id,assignment_id,message,due_at,created_at) VALUES(?,?,?,?,?)",(student_id,a["assignment_id"],message,due.isoformat(),now.isoformat()))
                row=self.db._fetch_one("SELECT id,student_id,assignment_id,message,due_at,created_at,read_at FROM academic_notifications WHERE student_id=? AND assignment_id=? AND message=?",(student_id,a["assignment_id"],message))
                if row and row not in created: created.append(row)
        trace=[{"agent":"Deadline Monitoring Agent","tool":"list_student_assignments","records_checked":len(assignments)}, {"agent":"Notification Agent","action":"create_deduplicated_notifications","notifications_found":len(created),"window_hours":within_hours}]
        self._trace(student_id,"deadline_monitor","completed",trace)
        return {"success":True,"notifications":created,"trace":trace}

    def list_notifications(self, student_id):
        return self.db._fetch_all("SELECT * FROM academic_notifications WHERE student_id=? ORDER BY due_at, id DESC",(student_id,))

    def professor_missing_submissions(self, professor_id, course_id=None):
        # Restrict to courses owned by this professor. Unowned legacy courses are not exposed.
        sql="""SELECT c.id course_id,c.course_code,c.name course_name,a.id assignment_id,a.title assignment_title,a.deadline,u.id student_id,u.name student_name,u.email
               FROM courses c JOIN assignments a ON a.course_id=c.id JOIN course_enrollments e ON e.course_id=c.id
               JOIN users u ON u.id=e.student_id LEFT JOIN submissions s ON s.assignment_id=a.id AND s.student_id=u.id
               WHERE c.created_by=? AND s.id IS NULL"""
        vals=[professor_id]
        if course_id is not None: sql+=" AND c.id=?"; vals.append(course_id)
        sql+=" ORDER BY a.deadline,u.name"
        rows=self.db._fetch_all(sql,tuple(vals))
        trace=[{"agent":"Professor Orchestrator","action":"scope_courses_to_authenticated_professor"},{"agent":"Assignment Agent","tool":"query_missing_submissions","records":len(rows)}]
        self._trace(professor_id,"professor_missing_submissions","completed",trace)
        return {"success":True,"count":len(rows),"missing_submissions":rows,"trace":trace}

    def recent_runs(self, user_id, limit=20):
        return self.db._fetch_all("SELECT id,workflow,status,trace_json,created_at FROM agent_runs WHERE user_id=? ORDER BY id DESC LIMIT ?",(user_id,limit))
