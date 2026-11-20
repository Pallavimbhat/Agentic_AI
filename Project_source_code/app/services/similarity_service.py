import re
from pathlib import Path

from docx import Document
from pptx import Presentation
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.database.connection import get_connection
from app.core.config import SIMILARITY_REVIEW_THRESHOLD


class SimilarityService:
    """Extract document text and compare submissions within an assignment."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}

    @staticmethod
    def extract_text(file_path):
        """Extract readable text from a supported document."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Submission file not found: {path}")

        extension = path.suffix.lower()

        if extension not in SimilarityService.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format for similarity checking: {extension}"
            )

        if extension == ".pdf":
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)

        elif extension == ".docx":
            document = Document(str(path))
            text = "\n".join(
                paragraph.text for paragraph in document.paragraphs
            )

            for table in document.tables:
                for row in table.rows:
                    text += "\n" + " ".join(cell.text for cell in row.cells)

        elif extension == ".pptx":
            presentation = Presentation(str(path))
            parts = []

            for slide in presentation.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        parts.append(shape.text)

                    if shape.has_table:
                        for row in shape.table.rows:
                            parts.append(
                                " ".join(cell.text for cell in row.cells)
                            )

            text = "\n".join(parts)

        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        return SimilarityService.preprocess_text(text)

    @staticmethod
    def preprocess_text(text):
        """Normalize extracted text before comparison."""

        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def calculate_similarity(text1, text2):
        """Calculate TF-IDF cosine similarity as a percentage."""

        if not text1 or not text2:
            return 0.0

        vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=20000,
            sublinear_tf=True
        )

        try:
            vectors = vectorizer.fit_transform([text1, text2])
            score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return round(float(score) * 100, 2)

        except ValueError:
            return 0.0

    @staticmethod
    def compare_submission(submission_id, assignment_id):
        """
        Compare a new submission with previous submissions
        belonging to the same assignment.
        """

        connection = get_connection()

        try:
            current = connection.execute(
                """
                SELECT id, assignment_id, file_path, file_hash
                FROM submissions
                WHERE id = ? AND assignment_id = ?
                """,
                (submission_id, assignment_id)
            ).fetchone()

            if not current:
                raise ValueError("Submission not found.")

            current_text = SimilarityService.extract_text(
                current["file_path"]
            )

            previous_submissions = connection.execute(
                """
                SELECT id, file_path, file_hash
                FROM submissions
                WHERE assignment_id = ?
                  AND id != ?
                ORDER BY submitted_at ASC
                """,
                (assignment_id, submission_id)
            ).fetchall()

            reports = []
            highest_score = 0.0
            most_similar_submission = None

            for previous in previous_submissions:

                # Exact duplicate detection is handled separately.
                if current["file_hash"] == previous["file_hash"]:
                    continue

                try:
                    previous_text = SimilarityService.extract_text(
                        previous["file_path"]
                    )
                except (FileNotFoundError, ValueError):
                    continue

                score = SimilarityService.calculate_similarity(
                    current_text,
                    previous_text
                )

                if score > highest_score:
                    highest_score = score
                    most_similar_submission = previous["id"]

                decision = (
                    "flagged_review"
                    if score >= SIMILARITY_REVIEW_THRESHOLD
                    else "accepted"
                )

                matching_details = (
                    f"TF-IDF word unigram and bigram cosine similarity: "
                    f"{score}%."
                )

                connection.execute(
                    """
                    INSERT INTO similarity_reports (
                        submission_id,
                        compared_submission_id,
                        similarity_score,
                        comparison_method,
                        decision,
                        matching_details
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        submission_id,
                        previous["id"],
                        score,
                        "tfidf_cosine",
                        decision,
                        matching_details
                    )
                )

                reports.append({
                    "compared_submission_id": previous["id"],
                    "similarity_score": score,
                    "decision": decision
                })

            flagged = highest_score >= SIMILARITY_REVIEW_THRESHOLD

            current_status = connection.execute(
                """
                SELECT status FROM submissions WHERE id = ?
                """,
                (submission_id,)
            ).fetchone()["status"]

            if flagged:
                new_status = "flagged_review"
            elif current_status == "late":
                new_status = "late"
            else:
                new_status = "accepted"

            connection.execute(
                """
                UPDATE submissions
                SET status = ?
                WHERE id = ?
                """,
                (new_status, submission_id)
            )

            connection.commit()

            return {
                "success": True,
                "submission_id": submission_id,
                "comparisons_performed": len(reports),
                "highest_similarity_score": highest_score,
                "most_similar_submission_id": most_similar_submission,
                "flagged_for_review": flagged,
                "reports": reports
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()