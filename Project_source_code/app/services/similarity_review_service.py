from app.database.connection import get_connection


class SimilarityReviewService:

    @staticmethod
    def get_submission_reports(submission_id, professor_id):
        connection = get_connection()

        try:
            submission = connection.execute(
                """
                SELECT s.id, s.assignment_id, a.created_by
                FROM submissions s
                JOIN assignments a ON a.id = s.assignment_id
                WHERE s.id = ?
                """,
                (submission_id,)
            ).fetchone()

            if not submission:
                raise ValueError("Submission not found.")

            if submission["created_by"] != professor_id:
                raise ValueError("You are not authorized to review this submission.")

            reports = connection.execute(
                """
                SELECT
                    sr.id AS report_id,
                    sr.submission_id,
                    sr.compared_submission_id,
                    sr.similarity_score,
                    sr.comparison_method,
                    sr.decision,
                    sr.matching_details,
                    sr.reviewed_by,
                    sr.review_reason,
                    sr.review_decision,
                    sr.created_at,
                    u.full_name AS compared_student_name
                FROM similarity_reports sr
                JOIN submissions cs
                    ON cs.id = sr.compared_submission_id
                JOIN users u
                    ON u.id = cs.student_id
                WHERE sr.submission_id = ?
                ORDER BY sr.similarity_score DESC
                """,
                (submission_id,)
            ).fetchall()

            return {
                "success": True,
                "submission_id": submission_id,
                "reports": [dict(report) for report in reports]
            }

        finally:
            connection.close()

    @staticmethod
    def review_report(report_id, professor_id, review_decision, reason):

        if review_decision not in ("confirmed", "not_confirmed"):
            raise ValueError(
                "Decision must be 'confirmed' or 'not_confirmed'."
            )

        if not reason or not reason.strip():
            raise ValueError("A review reason is required.")

        connection = get_connection()

        try:
            report = connection.execute(
                """
                SELECT sr.id, sr.submission_id, a.created_by
                FROM similarity_reports sr
                JOIN submissions s ON s.id = sr.submission_id
                JOIN assignments a ON a.id = s.assignment_id
                WHERE sr.id = ?
                """,
                (report_id,)
            ).fetchone()

            if not report:
                raise ValueError("Similarity report not found.")

            if report["created_by"] != professor_id:
                raise ValueError("You are not authorized to review this report.")

            connection.execute(
                """
                UPDATE similarity_reports
                SET reviewed_by = ?,
                   review_reason = ?,
                   review_decision = ?
                WHERE id = ?
                """,
                (
                   professor_id,
                   reason.strip(),
                   review_decision,
                   report_id
                )
            )

            connection.execute(
                """
                INSERT INTO audit_logs (
                    user_id,
                    action,
                    entity_type,
                    entity_id,
                    details
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    professor_id,
                    "SIMILARITY_REPORT_REVIEWED",
                    "similarity_report",
                    report_id,
                    f"Review decision: {review_decision}. Reason: {reason.strip()}"
                )
            )

            connection.commit()

            return {
                "success": True,
                "report_id": report_id,
                "reviewed_by": professor_id,
                "review_decision": review_decision,
                "review_reason": reason.strip(),
                "message": "Similarity report reviewed successfully."
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()