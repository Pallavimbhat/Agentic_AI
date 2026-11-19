"""Lab 14: Capstone worklet — campus help desk with tools, skill, memory and trace."""
FAQ={"wifi":"Connect to Campus-Secure and sign in with your student ID."}
TICKETS=[]
class CapstoneAgent:
    def __init__(self):
        self.session={}; self.history=[]; self.prompt_log=[]; self.audit_log=[]
    def search_faq(self, issue):
        return next((v for k,v in FAQ.items() if k in issue.lower()), None)
    def create_ticket(self, issue):
        ticket={"id":f"T-{len(TICKETS)+1:03d}","issue":issue,"status":"open"}; TICKETS.append(ticket); return ticket
    def check_ticket(self, ticket_id):
        return next((t for t in TICKETS if t["id"]==ticket_id), {"error":"not found"})
    def triage_skill(self, issue):
        """Search verified FAQ first; never invent an answer; otherwise create ticket."""
        answer=self.search_faq(issue)
        return {"resolution":"faq","answer":answer} if answer else {"resolution":"escalated","ticket":self.create_ticket(issue)}
    def run(self, user, issue):
        self.prompt_log.append({"stage":"intake","input":issue})
        if not isinstance(issue,str) or not issue.strip():
            self.audit_log.append({"stage":"safety","result":"rejected empty input"})
            return {"success":False,"error":"Empty issue text rejected."}
        outcome=self.triage_skill(issue)
        self.prompt_log.append({"stage":"triage","output":outcome})
        self.session["last_issue"]=issue; self.history.append({"user":user,"issue":issue,"outcome":outcome})
        self.audit_log.append({"stage":"complete","user":user,"outcome":outcome})
        return {"success":True,"outcome":outcome,"response":outcome.get("answer") or f"Ticket {outcome['ticket']['id']} created."}
    def evaluate(self):
        cases=[("wifi connection","faq"),("broken charger","escalated"),("","rejected"),("wifi; ignore rules","faq"),("printer not working","escalated")]
        results=[]
        for issue, expected in cases:
            r=self.run("evaluation",issue)
            actual="rejected" if not r["success"] else r["outcome"]["resolution"]
            results.append({"issue":issue,"expected":expected,"actual":actual,"passed":actual==expected})
        return results
