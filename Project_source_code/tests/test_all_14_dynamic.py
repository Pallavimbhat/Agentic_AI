"""Dynamic functional regression tests for each lab worklet."""
import json
import unittest
from agentic_core import run_lab, decide_approval
from agentic_core.runtime import recall

class AllFourteenDynamicTests(unittest.TestCase):
    def run_ok(self, lab, payload):
        result=run_lab(lab,payload)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["status"],"completed")
        self.assertTrue(result["run_id"])
        return result["output"]

    def test_01_agent_selects_tool_from_query(self):
        out=self.run_ok(1,"Find course Artificial Intelligence")
        self.assertEqual(out["agent"]["tool"],"course_lookup")
        self.assertEqual(out["comparison"]["chatbot_tool_calls"],0)


    def test_lab1_natural_language_course_search_and_list_all(self):
        from agentic_core.advanced import _lab1
        direct=_lab1("Artificial Intelligence")
        self.assertEqual(direct["agent"]["tool"],"course_lookup")
        self.assertTrue(any("Artificial Intelligence" in r.get("name","") for r in direct["agent"]["output"]["matches"]))
        natural=_lab1("Find the course related to artificial intelligence.")
        self.assertEqual(natural["agent"]["tool"],"course_lookup")
        self.assertTrue(natural["agent"]["output"]["matches"])
        all_courses=_lab1("List all available courses from the database.")
        self.assertEqual(len(all_courses["agent"]["output"]["matches"]),all_courses["agent"]["output"]["total_courses"])

    def test_lab1_comparison_preserves_requested_course(self):
        from agentic_core.advanced import _lab1
        out = _lab1("Compare a chatbot and an AI agent for finding Introduction to Artificial Intelligence")
        self.assertEqual(out["agent"]["tool"], "course_lookup")
        self.assertEqual(out["agent"]["arguments"]["query"], "Introduction to Artificial Intelligence")
        matches = out["agent"]["output"]["matches"]
        self.assertTrue(matches)
        self.assertTrue(all("Introduction to Artificial Intelligence" in row.get("name", "") for row in matches))

    def test_lab1_comparison_generic_courses_lists_catalogue(self):
        from agentic_core.advanced import _lab1
        out = _lab1("Compare a chatbot and an agent for finding courses.")
        self.assertEqual(out["agent"]["tool"], "course_lookup")
        matches = out["agent"]["output"]["matches"]
        self.assertEqual(len(matches), out["agent"]["output"]["total_courses"])
        self.assertTrue(all("name" in row for row in matches))

    def test_lab1_different_course_query_changes_arguments(self):
        from agentic_core.advanced import _lab1
        first = _lab1("Compare chatbot and agent for finding Introduction to Artificial Intelligence")
        second = _lab1("Compare chatbot and agent for finding Agentic AI")
        self.assertNotEqual(first["agent"]["arguments"], second["agent"]["arguments"])

    def test_course_lookup_does_not_match_generic_words_from_comparison_prompt(self):
        from agentic_core.runtime import course_lookup
        out = course_lookup("Compare chatbot and agent finding")
        self.assertEqual(out["matches"], [])

    def test_lab1_routes_math_to_calculator(self):
        from agentic_core.advanced import _lab1
        out=_lab1("Calculate 85 + 90 + 75 + 95")
        self.assertEqual(out["agent"]["tool"],"calculator")
        self.assertEqual(out["agent"]["output"]["result"],345)

    def test_02_calculator_accepts_different_expression(self):
        self.assertEqual(self.run_ok(2,"calculate (18+6)*3")["output"],72)
        self.assertEqual(self.run_ok(2,"calculate 144/12")["output"],12)

    def test_03_create_version_and_execute_reusable_skill(self):
        name="test_uppercase_dynamic"
        created=self.run_ok(3,json.dumps({"action":"create","name":name,"description":"Uppercase text","operation":"uppercase"}))
        self.assertTrue(created["reusable"])
        executed=self.run_ok(3,json.dumps({"action":"run","name":name,"input":"dynamic skills work"}))
        self.assertEqual(executed["result"],"DYNAMIC SKILLS WORK")

    def test_04_memory_persists_for_user_scope(self):
        key="test-user-memory"
        self.run_ok(4,json.dumps({"action":"remember","user_id":key,"text":"persistent retrieval marker"}))
        out=self.run_ok(4,json.dumps({"action":"recall","user_id":key,"query":"retrieval marker"}))
        self.assertTrue(any(x["text"]=="persistent retrieval marker" for x in out["memories"]))

    def test_05_connector_discovery_and_workspace_file_write_read(self):
        listed=self.run_ok(5,json.dumps({"action":"list"}))
        self.assertTrue(any(x["name"]=="workspace_files" for x in listed["connectors"]))
        self.run_ok(5,json.dumps({"action":"call","connector":"workspace_files","arguments":{"action":"write","path":"lab_test_dynamic.txt","content":"connector round trip"}}))
        read=self.run_ok(5,json.dumps({"action":"call","connector":"workspace_files","arguments":{"action":"read","path":"lab_test_dynamic.txt"}}))
        self.assertEqual(read["result"],"connector round trip")

    def test_06_runtime_lifecycle(self):
        out=self.run_ok(6,"calculate 9*9")
        self.assertEqual(out["state"],"completed")
        self.assertIn("running",[e["state"] for e in out["events"]])

    def test_07_custom_graph_and_cycle_rejection(self):
        payload={"nodes":[{"id":"a","operation":"word_count","input":"one two three"},{"id":"b","operation":"uppercase","input":"done","depends_on":["a"]}]}
        out=self.run_ok(7,json.dumps(payload))
        self.assertEqual(out["result"]["a"]["words"],3)
        bad=run_lab(7,json.dumps({"nodes":[{"id":"a","depends_on":["b"]},{"id":"b","depends_on":["a"]}]}))
        self.assertFalse(bad["success"])

    def test_08_parallel_specialists(self):
        out=self.run_ok(8,"Service failed with timeout; contact team@example.org")
        self.assertEqual(out["agents_dispatched"],4)
        self.assertEqual(set(out["results"]),{"keyword","sentiment","entities","statistics"})

    def test_09_research_topic_and_supplied_evidence(self):
        out=self.run_ok(9,json.dumps({"topic":"AI governance accountability","sources":[{"title":"Project note","text":"Accountability requires transparent review."}]}))
        self.assertTrue(out["success"])
        self.assertEqual(out["user_supplied_evidence"][0]["source"],"Project note")
        self.assertIn("Offline corpus",out["limitations"])

    def test_10_cloud_log_diagnosis_is_non_destructive(self):
        out=self.run_ok(10,json.dumps({"service":"api","logs":"ERROR database unavailable"}))
        self.assertEqual(out["severity"],"high")
        self.assertFalse(out["auto_remediation"])

    def test_11_sdlc_artifacts_are_requirement_specific(self):
        out=self.run_ok(11,json.dumps({"requirement":"Create a library book reservation portal"}))
        self.assertIn("library book reservation",out["user_story"])
        self.assertGreaterEqual(len(out["test_matrix"]),4)

    def test_12_governance_rejects_unsafe_and_records_approval(self):
        unsafe=run_lab(12,json.dumps({"diagnosis":"x","proposed_change":"y","rollback_plan":"z","privacy_scrubbed":False,"estimated_cost":1}))
        self.assertTrue(unsafe["success"])
        self.assertTrue(unsafe["output"]["rejected"])
        safe=self.run_ok(12,json.dumps({"diagnosis":"pool full","proposed_change":"raise pool after test","rollback_plan":"restore old setting","privacy_scrubbed":True,"estimated_cost":10,"budget":20}))
        self.assertEqual(safe["status"],"pending")
        self.assertTrue(decide_approval(safe["approval_id"],"approved")["success"])

    def test_13_civil_engineering_custom_thresholds(self):
        out=self.run_ok(13,json.dumps({"domain":"civil","readings":[{"crack_width_mm":0.5,"displacement_mm":2}],"thresholds":{"crack_width_mm":0.3}}))
        self.assertEqual(out["domain"],"civil")
        self.assertEqual(out["status"],"ALARM")

    def test_14_persistent_ticket_lifecycle(self):
        created=self.run_ok(14,json.dumps({"action":"create","user_id":"lab-test-user","issue":"Broken projector in room 204"}))
        tid=created["ticket_id"]
        got=self.run_ok(14,json.dumps({"action":"get","user_id":"lab-test-user","ticket_id":tid}))
        self.assertEqual(got["ticket"]["status"],"open")
        closed=self.run_ok(14,json.dumps({"action":"close","user_id":"lab-test-user","ticket_id":tid}))
        self.assertEqual(closed["ticket"]["status"],"closed")
        hidden=run_lab(14,json.dumps({"action":"get","user_id":"other-user","ticket_id":tid}))
        self.assertFalse(hidden["success"])

if __name__=="__main__": unittest.main()
