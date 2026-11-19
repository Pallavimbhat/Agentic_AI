"""Parallel execution of independent specialist agents."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter

class SwarmManager:
    def __init__(self, agents, max_workers=None):
        if not agents: raise ValueError("At least one agent is required")
        self.agents = dict(agents); self.max_workers = max_workers or len(self.agents)
    def run(self, task):
        started = perf_counter(); results = {}; trace = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(fn, task): name for name, fn in self.agents.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = {"success": True, "result": future.result()}
                    trace.append({"agent": name, "status": "completed"})
                except Exception as exc:
                    results[name] = {"success": False, "error": str(exc)}
                    trace.append({"agent": name, "status": "failed", "error": str(exc)})
        return {"success": all(v["success"] for v in results.values()), "task": task,
                "results": results, "trace": trace, "execution_seconds": round(perf_counter()-started, 6),
                "aggregation": "Results from independent agents are collected into one response."}

def demo_swarm():
    agents = {
        "course_agent": lambda task: {"courses": ["AI101", "DBMS"]},
        "notes_agent": lambda task: {"notes_found": 3},
        "assignment_agent": lambda task: {"pending": 1, "overdue": 0},
    }
    return SwarmManager(agents).run("Prepare an academic status summary")
