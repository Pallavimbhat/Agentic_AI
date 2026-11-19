"""Lab 11: Agentic SDLC Factory — traceable software work products."""
def build_sdlc(requirement):
    if not requirement or not requirement.strip():
        return {"success": False, "error": "Requirement is required."}
    req = requirement.strip()
    return {"success": True, "requirement": req,
            "artifacts": [
                {"stage": "requirements", "output": f"Acceptance criterion: {req} must be testable."},
                {"stage": "design", "output": "Define components, interfaces, data validation and failure handling."},
                {"stage": "implementation_plan", "output": "Implement the smallest change behind a clear interface."},
                {"stage": "testing", "output": "Add positive, negative and boundary tests for the acceptance criterion."},
                {"stage": "review", "output": "Review correctness, security, maintainability and regression risk."},
                {"stage": "release", "output": "Release only after human review and passing tests."}],
            "lineage": "Each stage references the original requirement; outputs are planning artifacts, not generated production code."}
