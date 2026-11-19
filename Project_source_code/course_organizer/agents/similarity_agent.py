from course_organizer.agents.base_agent import BaseAgent
import math
import json
import re
from collections import Counter


class SimilarityAgent(BaseAgent):
    """Manages similarity reports and human review."""

    def __init__(self, db=None, review_threshold=70.0):
        super().__init__("Plagiarism / Similarity Agent", db)
        self.review_threshold = review_threshold

    def create_report(
        self,
        submission_id,
        compared_submission_id,
        similarity_score,
        details="",
    ):
        try:
            if submission_id == compared_submission_id:
                return self.failure(
                    "create_report",
                    "A submission cannot be compared with itself.",
                )

            score = float(similarity_score)

            if not 0 <= score <= 100:
                return self.failure(
                    "create_report",
                    "Similarity score must be between 0 and 100.",
                )

            report = self.db.create_similarity_report(
                submission_id=submission_id,
                compared_submission_id=compared_submission_id,
                similarity_score=score,
                details=details,
            )

            requires_review = score >= self.review_threshold

            self.log_action(
                action="create_similarity_report",
                entity_type="similarity_report",
                details=(
                    f"Compared submissions {submission_id} and "
                    f"{compared_submission_id}; score={score}; "
                    f"requires_review={requires_review}."
                ),
            )

            return self.success(
                "create_report",
                (
                    "Similarity report created; human review recommended."
                    if requires_review
                    else "Similarity report created."
                ),
                {
                    "report": report,
                    "similarity_score": score,
                    "requires_human_review": requires_review,
                },
            )

        except (TypeError, ValueError):
            return self.failure(
                "create_report",
                "Similarity score must be a number between 0 and 100.",
            )
        except Exception as exc:
            return self.failure("create_report", str(exc))


    @staticmethod
    def _similarity(text_a, text_b):
        """Return a transparent lexical similarity score (not an AI plagiarism verdict)."""
        def tokens(text):
            return re.findall(r"[a-z0-9]+", (text or "").casefold())

        a, b = tokens(text_a), tokens(text_b)
        if not a or not b:
            raise ValueError("Both submissions must contain text before comparison.")
        def shingles(words, size=3):
            if len(words) < size:
                return {" ".join(words)}
            return {" ".join(words[i:i + size]) for i in range(len(words) - size + 1)}
        sa, sb = shingles(a), shingles(b)
        overlap = len(sa & sb) / len(sa | sb) if sa or sb else 0.0
        ca, cb = Counter(a), Counter(b)
        vocab = set(ca) | set(cb)
        dot = sum(ca[t] * cb[t] for t in vocab)
        na = math.sqrt(sum(v * v for v in ca.values()))
        nb = math.sqrt(sum(v * v for v in cb.values()))
        cosine = dot / (na * nb) if na and nb else 0.0
        score = round((0.65 * overlap + 0.35 * cosine) * 100, 2)
        return score, {"method": "word trigram Jaccard (65%) + token-frequency cosine (35%)",
                       "shared_trigram_count": len(sa & sb),
                       "unique_trigram_count": len(sa | sb),
                       "token_cosine": round(cosine, 4),
                       "disclaimer": "Lexical similarity is a screening signal, not proof of plagiarism. A professor must review context, citations, templates and common terminology."}

    def compare_submissions(self, submission_id, compared_submission_id):
        try:
            if submission_id == compared_submission_id:
                return self.failure("compare_submissions", "Choose two different submissions.")
            first = self.db.get_submission(submission_id)
            second = self.db.get_submission(compared_submission_id)
            if not first or not second:
                return self.failure("compare_submissions", "One or both submission IDs were not found.")
            if first.get("assignment_id") != second.get("assignment_id"):
                return self.failure(
                    "compare_submissions",
                    "Submissions can only be compared when they belong to the same assignment.",
                )
            text_a, text_b = first.get("content") or "", second.get("content") or ""
            score, metrics = self._similarity(text_a, text_b)
            report = self.db.create_similarity_report(
                submission_id=submission_id, compared_submission_id=compared_submission_id,
                similarity_score=score, details=json.dumps(metrics, ensure_ascii=False)
            )
            return self.success("compare_submissions", "Submission comparison completed. Similarity is a review indicator, not a misconduct finding.",
                {"report": report, "submission_a": {"id": submission_id, "student": first.get("student_name"), "assignment": first.get("assignment_title")},
                 "submission_b": {"id": compared_submission_id, "student": second.get("student_name"), "assignment": second.get("assignment_title")},
                 "similarity_score": score, "requires_human_review": score >= self.review_threshold, "metrics": metrics})
        except ValueError as exc:
            return self.failure("compare_submissions", str(exc))
        except Exception as exc:
            return self.failure("compare_submissions", str(exc))

    def list_reports(self, submission_id=None):
        try:
            reports = self.db.list_similarity_reports(
                submission_id=submission_id
            )

            return self.success(
                "list_reports",
                "Similarity reports retrieved successfully.",
                reports,
            )

        except Exception as exc:
            return self.failure("list_reports", str(exc))

    def review_report(self, report_id, reviewer_id):
        try:
            report = self.db.review_similarity_report(
                report_id=report_id,
                reviewed_by=reviewer_id,
            )

            self.log_action(
                action="review_similarity_report",
                entity_type="similarity_report",
                entity_id=report_id,
                actor_id=reviewer_id,
                details="Similarity report reviewed by a human reviewer.",
            )

            return self.success(
                "review_report",
                "Similarity report review recorded.",
                report,
            )

        except Exception as exc:
            return self.failure("review_report", str(exc))