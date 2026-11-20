import json
from datetime import datetime


class SafetyGovernanceAgent:
    """Evaluates agent actions against safety and access policies."""

    ALLOWED_ROLES = {"student", "professor", "admin"}

    RESTRICTED_ACTIONS = {
        "delete_database",
        "delete_users",
        "modify_permissions",
        "unauthorized_deployment"
    }

    def evaluate(self, role, action, input_data=None):
        checks = []

        role_valid = role in self.ALLOWED_ROLES
        action_allowed = action not in self.RESTRICTED_ACTIONS
        input_valid = isinstance(input_data or {}, dict)

        checks.append({
            "check": "Role Validation",
            "passed": role_valid
        })

        checks.append({
            "check": "Action Authorization",
            "passed": action_allowed
        })

        checks.append({
            "check": "Input Validation",
            "passed": input_valid
        })

        approved = all(item["passed"] for item in checks)

        return {
            "agent": "Safety and Governance Agent",
            "status": "approved" if approved else "blocked",
            "role": role,
            "action": action,
            "checks": checks,
            "evaluation_score": round(
                sum(item["passed"] for item in checks) / len(checks) * 100,
                2
            ),
            "audit_timestamp": datetime.now().isoformat()
        }


def run_lab():
    agent = SafetyGovernanceAgent()

    result = agent.evaluate(
        role="student",
        action="view_courses",
        input_data={"course_id": 101}
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run_lab()