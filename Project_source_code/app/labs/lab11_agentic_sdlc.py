import json
from datetime import datetime


class AgenticSDLCFactory:
    """Breaks software requirements into structured development stages."""

    def run(self, requirement):
        if not isinstance(requirement, str) or not requirement.strip():
            raise ValueError("A software requirement is required.")

        requirement = requirement.strip()

        stages = [
            {
                "stage": "Requirements Analysis",
                "task": f"Understand and document: {requirement}"
            },
            {
                "stage": "System Design",
                "task": "Identify architecture, components and data flow."
            },
            {
                "stage": "Implementation",
                "task": "Develop the required modules and interfaces."
            },
            {
                "stage": "Testing",
                "task": "Prepare unit, integration and validation tests."
            },
            {
                "stage": "Code Review",
                "task": "Check readability, maintainability and security."
            },
            {
                "stage": "Deployment",
                "task": "Prepare deployment configuration and release checks."
            }
        ]

        return {
            "agent": "Agentic SDLC Factory",
            "requirement": requirement,
            "status": "completed",
            "development_stages": stages,
            "total_stages": len(stages),
            "quality_checks": [
                "Requirement completeness",
                "Input validation",
                "Error handling",
                "Security review",
                "Test coverage"
            ],
            "execution_note": (
                "This run generates a development workflow. "
                "It does not automatically modify or deploy source code."
            ),
            "timestamp": datetime.now().isoformat()
        }


def run_lab():
    result = AgenticSDLCFactory().run(
        "Develop a course management system with student enrollment, "
        "assignment tracking and an AI academic assistant."
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run_lab()