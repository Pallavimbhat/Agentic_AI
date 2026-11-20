import json
import re
from datetime import datetime


class CloudOperationsAgent:
    """Analyzes application logs and identifies potential incidents."""

    PATTERNS = {
        "critical": r"\b(CRITICAL|FATAL)\b",
        "high": r"\b(ERROR|EXCEPTION)\b",
        "medium": r"\b(WARNING|WARN)\b",
        "low": r"\b(INFO|DEBUG)\b"
    }

    def analyze_logs(self, logs):
        if not isinstance(logs, str):
            raise ValueError("Logs must be provided as text.")

        findings = []

        for line_number, line in enumerate(logs.splitlines(), start=1):
            for severity, pattern in self.PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "line": line_number,
                        "severity": severity,
                        "message": line.strip()
                    })
                    break

        counts = {
            level: sum(
                1 for item in findings
                if item["severity"] == level
            )
            for level in self.PATTERNS
        }

        if counts["critical"]:
            status = "critical_incident"
        elif counts["high"]:
            status = "high_priority_incident"
        elif counts["medium"]:
            status = "warning_detected"
        else:
            status = "healthy"

        recommendations = []

        if counts["critical"]:
            recommendations.append(
                "Investigate critical failures immediately."
            )
        if counts["high"]:
            recommendations.append(
                "Inspect exceptions and application error traces."
            )
        if counts["medium"]:
            recommendations.append(
                "Review warnings for recurring operational issues."
            )
        if not findings:
            recommendations.append(
                "No recognized severity indicators were found."
            )

        return {
            "agent": "Cloud Operations Agent",
            "status": status,
            "total_log_entries": len(logs.splitlines()),
            "detected_events": len(findings),
            "severity_counts": counts,
            "findings": findings,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }


def run_lab():
    sample_logs = """
    INFO Application started successfully
    WARNING Database response time is high
    ERROR Database connection failed
    CRITICAL Service unavailable
    INFO Health check completed
    """

    result = CloudOperationsAgent().analyze_logs(sample_logs)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run_lab()