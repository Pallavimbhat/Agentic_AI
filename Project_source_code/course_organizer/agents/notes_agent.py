from course_organizer.agents.base_agent import BaseAgent


class NotesAgent(BaseAgent):
    """Manages course notes and their version history."""

    def __init__(self, db=None):
        super().__init__("Notes Repository Agent", db)

    def create_note(self, course_id, title, content, created_by):
        try:
            if not title or not title.strip():
                return self.failure("create_note", "Note title is required.")

            if not content or not content.strip():
                return self.failure("create_note", "Note content is required.")

            note = self.db.create_note(
                course_id=course_id,
                title=title.strip(),
                content=content,
                created_by=created_by,
            )

            self.log_action(
                action="create_note",
                entity_type="note",
                entity_id=note.get("id") if isinstance(note, dict) else None,
                actor_id=created_by,
                details=f"Created note: {title}",
            )

            return self.success("create_note", "Note created successfully.", note)

        except Exception as exc:
            return self.failure("create_note", str(exc))

    def get_note(self, note_id):
        try:
            note = self.db.get_note(note_id)

            if not note:
                return self.failure("get_note", "Note not found.")

            return self.success("get_note", "Note retrieved successfully.", note)

        except Exception as exc:
            return self.failure("get_note", str(exc))

    def list_notes(self, course_id):
        try:
            notes = self.db.list_notes(course_id)

            return self.success(
                "list_notes",
                "Notes retrieved successfully.",
                notes,
            )

        except Exception as exc:
            return self.failure("list_notes", str(exc))

    def add_version(self, note_id, content, created_by):
        try:
            if not content or not content.strip():
                return self.failure(
                    "add_version",
                    "Version content cannot be empty.",
                )

            version = self.db.add_note_version(
                note_id=note_id,
                content=content,
                created_by=created_by,
            )

            self.log_action(
                action="add_note_version",
                entity_type="note",
                entity_id=note_id,
                actor_id=created_by,
                details="Added a new note version.",
            )

            return self.success(
                "add_version",
                "Note version added successfully.",
                version,
            )

        except Exception as exc:
            return self.failure("add_version", str(exc))

    def get_versions(self, note_id):
        try:
            versions = self.db.get_note_versions(note_id)

            return self.success(
                "get_versions",
                "Note version history retrieved.",
                versions,
            )

        except Exception as exc:
            return self.failure("get_versions", str(exc))