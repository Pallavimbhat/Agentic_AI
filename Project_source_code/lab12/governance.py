"""Lab 12: Safety, Evaluation and Governance — gated change proposals."""
class GovernanceAgent:
    def __init__(self, pass_rate=0.9, threshold=0.8):
        self.pass_rate, self.threshold, self.audit_log = pass_rate, threshold, []
        self.permissions = {"can_read": True, "can_write_production": False}
    def evaluate(self):
        passed = self.pass_rate >= self.threshold
        self.audit_log.append({"event": "evaluation", "passed": passed})
        return passed
    def propose_change(self, diagnosis, action, rollback_plan, privacy_scrubbed, estimated_cost=None, budget=100, finance_approved=False):
        if self.permissions["can_write_production"]:
            raise PermissionError("Agent must not hold direct production write access.")
        if not diagnosis or not action or not rollback_plan:
            result = {"rejected": True, "reason": "Diagnosis, action and rollback plan are mandatory."}
        elif not privacy_scrubbed:
            result = {"rejected": True, "reason": "Input must be privacy-scrubbed."}
        elif estimated_cost is None:
            result = {"rejected": True, "reason": "Cost estimate is mandatory."}
        elif estimated_cost > budget and not finance_approved:
            result = {"rejected": True, "reason": "Finance approval required; budget exceeded."}
        elif not self.evaluate():
            result = {"rejected": True, "reason": "Evaluation gate failed."}
        else:
            result = {"rejected": False, "requires_approval": True, "diagnosis": diagnosis, "action": action,
                      "rollback_plan": rollback_plan, "estimated_cost": estimated_cost}
        self.audit_log.append({"event": "proposal", "result": result})
        return result
    def apply_after_approval(self, proposal, decision):
        self.audit_log.append({"event": "human_decision", "decision": decision})
        return {"applied": False, "handed_off": decision == "approved", "reason": "Separate privileged deployment process required."}
