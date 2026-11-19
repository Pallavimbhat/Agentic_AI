"""Lab 9: Deep Research Agent using a transparent, topic-matched local corpus.
No live web search is claimed. Each result includes source provenance and limits.
"""
import re
SOURCES=[
 {"source":"NIST AI Risk Management Framework","text":"AI risk management functions include Govern, Map, Measure and Manage.","tags":["ai","risk","governance","management","model"]},
 {"source":"OECD AI Principles","text":"Trustworthy AI emphasizes inclusive growth, human-centred values, transparency, robustness, security and accountability.","tags":["ai","trust","ethics","transparency","accountability"]},
 {"source":"UNESCO Recommendation on the Ethics of AI","text":"AI ethics includes human rights, human oversight, privacy, fairness and accountability.","tags":["ai","ethics","privacy","fairness","human"]},
 {"source":"Course Organizer project documentation","text":"Agentic systems combine an agent runtime, tools, reusable skills, memory, connectors and observable execution traces.","tags":["agent","agentic","tools","skills","memory","connector","runtime"]},
 {"source":"Software testing principles (local teaching note)","text":"A test strategy should include positive, negative, boundary and regression tests.","tags":["testing","software","quality","sdlc","test"]},
]
def research_brief(topic=""):
    if not isinstance(topic,str) or not topic.strip(): return {"success":False,"error":"A research topic is required."}
    words=set(re.findall(r"[a-z0-9]+",topic.lower()))
    ranked=[]
    for s in SOURCES:
        overlap=words.intersection(set(s["tags"]))
        if overlap:
            ranked.append((len(overlap),s,sorted(overlap)))
    ranked.sort(key=lambda x:(-x[0],x[1]["source"]))
    evidence=[{"source":s["source"],"relevance_terms":terms,"evidence":s["text"],"match_score":score} for score,s,terms in ranked[:5]]
    return {"success":True,"topic":topic.strip(),"sources_consulted":len(evidence),"evidence_table":evidence,
      "synthesis":("The matched local sources suggest: "+" ".join(x["evidence"] for x in evidence)) if evidence else "No matching source was found in the local research corpus. Add verified sources or broaden the topic.",
      "method":"Keyword-based retrieval over a small local source corpus; not an LLM literature review.",
      "limitations":"Offline corpus only; no live web research. Do not cite these notes as primary academic sources without checking originals."}
