import json

from app.skills.academic_skills import build_academic_skill_registry


def run_lab():

    print("\n======================================")
    print(" LAB 3 - REUSABLE ACADEMIC SKILLS")
    print("======================================")

    registry = build_academic_skill_registry()

    print("\nREGISTERED SKILLS")

    print(json.dumps(
        registry.list_skills(),
        indent=4
    ))

    context = {
        "user_id": 1,
        "role": "professor"
    }

    print("\nTEST 1: ASSIGNMENT OVERVIEW SKILL")

    try:

        result = registry.execute(
            "assignment_overview",
            context,
            {"course_id": 1}
        )

        print(json.dumps(result, indent=4, default=str))

    except Exception as error:
        print("Error:", error)

    print("\nTEST 2: PROFESSOR SUBMISSION OVERVIEW")

    try:

        result = registry.execute(
            "professor_submission_overview",
            context,
            {"assignment_id": 1}
        )

        print(json.dumps(result, indent=4, default=str))

    except Exception as error:
        print("Error:", error)

    print("\nTEST 3: ROLE-BASED ACCESS CONTROL")

    try:

        registry.execute(
            "student_grade_review",
            context
        )

    except Exception as error:
        print("Expected permission rejection:", error)

    print("\n======================================")
    print(" LAB 3 EXECUTION COMPLETED")
    print("======================================")


if __name__ == "__main__":
    run_lab()