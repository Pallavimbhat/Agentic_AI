import unittest, tempfile, os, json
from agentic_core import run_lab, remember, recall, list_traces, list_skills, list_connectors, decide_approval
class SharedCoreTests(unittest.TestCase):
 def test_dynamic_calculator_inputs(self):
  a=run_lab(2,"calculate 7*(8+2)")
  b=run_lab(2,"calculate 100/4")
  self.assertEqual(a["output"]["output"],70)
  self.assertEqual(b["output"]["output"],25)
  self.assertNotEqual(a["run_id"],b["run_id"])
 def test_persistent_memory(self):
  remember("phase six verification marker")
  self.assertTrue(any("phase six verification marker" in x["text"] for x in recall("phase six verification marker")))
 def test_registries(self):
  self.assertTrue(any(x["name"]=="calculator" for x in list_skills()))
  self.assertTrue(any(x["name"]=="academic_db" for x in list_connectors()))
 def test_trace_persisted(self):
  run_lab(1,"find course AI")
  self.assertTrue(any(x["lab_id"]==1 for x in list_traces()))
 def test_approval_is_single_use(self):
  r=run_lab(12,"propose change logging")
  aid=r["output"]["approval_id"]
  self.assertTrue(decide_approval(aid,"approved")["success"])
  self.assertFalse(decide_approval(aid,"rejected")["success"])
if __name__=="__main__": unittest.main()
