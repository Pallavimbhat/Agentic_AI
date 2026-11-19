"""Standalone interactive launcher shared by all fourteen lab packages."""
import json
from .runtime import run_lab

EXAMPLES={
1:"Find course Artificial Intelligence",
2:"calculate (12+8)*3",
3:'{"action":"create","name":"uppercase_demo","description":"Uppercase text","operation":"uppercase"}',
4:'{"action":"remember","user_id":"student-101","text":"My project uses FastAPI"}',
5:'{"action":"list"}',
6:"calculate 7*9",
7:'{"nodes":[{"id":"a","operation":"word_count","input":"one two three"}]}',
8:"A service failed with timeout and error",
9:"AI governance and accountability",
10:"ERROR database unavailable",
11:"Build an assignment submission portal",
12:'{"diagnosis":"service issue","proposed_change":"increase capacity","rollback_plan":"restore previous capacity","privacy_scrubbed":true,"estimated_cost":10,"budget":100}',
13:'{"domain":"mechanical","readings":[{"vibration_mm_s":6.2,"temp_c":84}]}',
14:'{"action":"triage","user_id":"student-101","issue":"My printer is not working"}'
}

def main(lab_id:int):
    print(f"\nAGENTIC AI — LAB {lab_id:02d}")
    print("Enter a task or JSON payload. Type :example to see a sample; :quit to exit.\n")
    while True:
        try: text=input(f"lab{lab_id}> ").strip()
        except (EOFError,KeyboardInterrupt):
            print(); return
        if text.lower() in {":quit","quit","exit"}: return
        if text==":example":
            print(EXAMPLES[lab_id]); continue
        if not text: continue
        result=run_lab(lab_id,text)
        print(json.dumps(result,indent=2,ensure_ascii=False,default=str))
