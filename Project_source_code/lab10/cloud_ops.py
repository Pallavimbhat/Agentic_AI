"""Lab 10: Cloud Operations Agent — log diagnosis with approval gate."""
import re
def analyse_logs(log_text):
    if not isinstance(log_text, str) or not log_text.strip():
        return {"success": False, "error": "Log text is required."}
    lines = log_text.splitlines()
    errors = [line for line in lines if re.search(r"error|failed|exception|timeout", line, re.I)]
    severity = "high" if any(re.search(r"out of memory|database unavailable|crash", x, re.I) for x in errors) else ("medium" if errors else "low")
    root = "Possible memory exhaustion or service crash" if severity == "high" else ("Review the reported errors and dependencies" if errors else "No error pattern detected")
    return {"success": True, "severity": severity, "error_lines": errors, "likely_cause": root,
            "recommended_action": "Investigate and prepare a rollback plan; request operator approval before remediation." if errors else "Continue monitoring.",
            "approval_required": bool(errors), "auto_remediation": False}
