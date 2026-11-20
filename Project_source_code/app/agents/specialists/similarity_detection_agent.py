from app.agents.base_agent import BaseAgent
from app.services.similarity_service import SimilarityService
from app.database.connection import get_connection


class SimilarityDetectionAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Similarity Detection Agent",
            description=(
                "Analyses assignment submissions using "
                "TF-IDF and cosine similarity."
            )
        )

    def execute(self, input_data):

        role = input_data.get("role")
        user_id = input_data.get("user_id")

        if role != "professor":
            raise PermissionError(
                "Only professors can initiate similarity reviews."
            )

        if not user_id:
            raise ValueError("Professor ID is required.")

        submission_id = input_data.get("submission_id")
        assignment_id = input_data.get("assignment_id")

        if not submission_id or not assignment_id:
            raise ValueError(
                "Submission ID and Assignment ID are required."
            )

        # Verify that this professor owns the assignment.
        connection = get_connection()

        try:
            assignment = connection.execute(
                """
                SELECT id
                FROM assignments
                WHERE id = ? AND created_by = ?
                """,
                (assignment_id, user_id)
            ).fetchone()

        finally:
            connection.close()

        if not assignment:
            raise PermissionError(
                "You are not authorized to review this assignment."
            )

        result = SimilarityService.compare_submission(
            submission_id=submission_id,
            assignment_id=assignment_id
        )

        return {
            "analysis_type": "TF-IDF Cosine Similarity",
            "similarity_analysis": result
        }