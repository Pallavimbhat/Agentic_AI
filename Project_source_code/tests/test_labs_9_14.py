import unittest
from lab9.deep_research import research_brief
from lab10.cloud_ops import analyse_logs
from lab11.sdlc_factory import build_sdlc
from lab12.governance import GovernanceAgent
from lab13.engineering_agent import predictive_maintenance_agent
from lab14.capstone import CapstoneAgent
from agentic_core.advanced import HANDLERS, execute

class NewLabsTests(unittest.TestCase):
    def test_all_fourteen_capability_handlers_are_registered(self):
        self.assertEqual(set(HANDLERS), set(range(1, 15)))

    def test_capability_handlers_accept_dynamic_input(self):
        samples = {
            1: "Find course Artificial Intelligence", 2: "calculate 5 * 7",
            3: "list skills", 4: '{"action":"recall","user_id":"test","query":""}',
            5: "list connectors", 6: "calculate 8 + 9", 7: "A dependency graph example",
            8: "parallel specialist analysis of student outcomes", 9: "AI in education",
            10: "ERROR database timeout", 11: "Build a course registration application",
            12: "{}", 13: "mechanical\nvibration_mm_s=2.1\ntemp_c=55",
            14: '{"action":"list","user_id":"test"}'
        }
        for lab_id, sample in samples.items():
            with self.subTest(lab_id=lab_id):
                result = execute(lab_id, sample)
                self.assertIsInstance(result, dict)

    def test_research_has_evidence_and_limitations(self):
        r=research_brief("AI safety"); self.assertTrue(r["success"]); self.assertEqual(r["sources_consulted"],3); self.assertIn("limitations",r)
    def test_cloud_high_severity_never_autoremediates(self):
        r=analyse_logs("ERROR database unavailable"); self.assertEqual(r["severity"],"high"); self.assertFalse(r["auto_remediation"]); self.assertTrue(r["approval_required"])
    def test_sdlc_pipeline(self):
        r=build_sdlc("Add login"); self.assertEqual(len(r["artifacts"]),6)
    def test_governance_rejects_missing_cost_and_requires_approval(self):
        g=GovernanceAgent()
        r=g.propose_change("diag","action","rollback",True)
        self.assertTrue(r["rejected"])
        r=g.propose_change("diag","action","rollback",True,estimated_cost=10)
        self.assertTrue(r["requires_approval"])
        self.assertFalse(g.apply_after_approval(r,"approved")["applied"])
    def test_engineering_alarm_never_auto_executes(self):
        r=predictive_maintenance_agent(); self.assertEqual(r["condition"],"ALARM"); self.assertFalse(r["auto_executed"])
    def test_capstone_safety_and_evaluation(self):
        a=CapstoneAgent(); self.assertFalse(a.run("x"," ")["success"]); self.assertTrue(all(x["passed"] for x in a.evaluate()))
if __name__=="__main__": unittest.main()
