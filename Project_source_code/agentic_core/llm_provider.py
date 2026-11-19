"""Optional OpenAI-compatible LLM adapter for natural-language intent routing.

No key is bundled. When AI_API_KEY and AI_MODEL are configured, the model may
classify an ambiguous request into one of the existing 14 local capabilities.
Tool execution remains local, validated, and recorded by the agent runtime.
"""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass


def configured() -> bool:
    return bool(os.getenv("AI_API_KEY") and os.getenv("AI_MODEL"))


def classify_request(question: str) -> dict | None:
    if not configured():
        return None
    base = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ["AI_MODEL"]
    system = (
        "You are the intent router for an academic agent application. "
        "Classify the user's request into lab_id 1..14, or 0 if it is ordinary "
        "academic conversation. Return ONLY JSON with keys lab_id and input. "
        "input must preserve the user's actual data and must not invent values. "
        "Do not execute tools or claim results. Lab mapping: 1 agent-vs-chatbot; "
        "2 tools/calculator; 3 reusable skills; 4 memory; 5 connectors; "
        "6 runtime; 7 node graph; 8 parallel specialists; 9 research; "
        "10 cloud logs; 11 SDLC; 12 governance; 13 engineering sensors; "
        "14 helpdesk tickets."
    )
    payload = json.dumps({
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions", data=payload,
        headers={"Authorization": "Bearer " + os.environ["AI_API_KEY"],
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=float(os.getenv("AI_API_TIMEOUT", "12"))) as response:
            body = json.loads(response.read(1_000_000).decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        result = json.loads(content)
        lab_id = int(result.get("lab_id", 0))
        if lab_id not in range(0, 15):
            return None
        user_input = result.get("input", question)
        if not isinstance(user_input, str) or not user_input.strip():
            return None
        return {"lab_id": lab_id, "input": user_input.strip(), "provider": "configured_llm"}
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError):
        # Fail closed to the deterministic local router; never invent execution.
        return None
