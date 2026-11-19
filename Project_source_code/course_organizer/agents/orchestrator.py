from course_organizer.agents.notes_agent import NotesAgent
from course_organizer.agents.assignment_agent import AssignmentAgent
from course_organizer.agents.submission_agent import SubmissionAgent
from course_organizer.agents.similarity_agent import SimilarityAgent
from course_organizer.agents.grading_agent import GradingAgent
from course_organizer.agents.milestone_agent import MilestoneAgent
from course_organizer.agents.grade_publishing_agent import (
    GradePublishingAgent,
)
from course_organizer.database.db_service import DatabaseService
from course_organizer.agents.academic_assistant_agent import AcademicAssistantAgent


class CourseOrganizerOrchestrator:
    """Coordinates the seven Course Organizer agents."""

    def __init__(self, db=None):
        self.db = db if db is not None else DatabaseService()

        # Share the same database service with every agent.
        self.notes_agent = NotesAgent(self.db)
        self.assignment_agent = AssignmentAgent(self.db)
        self.submission_agent = SubmissionAgent(self.db)
        self.similarity_agent = SimilarityAgent(self.db)
        self.grading_agent = GradingAgent(self.db)
        self.milestone_agent = MilestoneAgent(self.db)
        self.grade_publishing_agent = GradePublishingAgent(self.db)
        self.academic_assistant_agent = AcademicAssistantAgent(self.db)

        self.agents = {
            "notes": self.notes_agent,
            "assignments": self.assignment_agent,
            "submissions": self.submission_agent,
            "similarity": self.similarity_agent,
            "grading": self.grading_agent,
            "milestones": self.milestone_agent,
            "grade_publishing": self.grade_publishing_agent,
            "academic_assistant": self.academic_assistant_agent,
        }

    def list_agents(self):
        """Return the available agents and their responsibilities."""
        descriptions = {
            "notes": "Manage course notes and version history.",
            "assignments": "Manage assignments and deadlines.",
            "submissions": "Manage student assignment submissions.",
            "similarity": "Manage similarity reports for human review.",
            "grading": "Prepare grades and feedback.",
            "milestones": "Track project milestones and progress.",
            "grade_publishing": "Approve and publish grades under controlled rules.",
            "academic_assistant": "Plan student queries, select database tools, and return an execution trace.",
        }

        return {
            "success": True,
            "agent_count": len(self.agents),
            "agents": descriptions,
        }

    def execute(self, agent_name, action, **kwargs):
        """Dispatch a requested operation to a registered agent."""
        agent = self.agents.get(agent_name)

        if agent is None:
            return {
                "success": False,
                "message": f"Unknown agent: {agent_name}",
                "available_agents": list(self.agents.keys()),
            }

        operation = getattr(agent, action, None)

        if operation is None or not callable(operation):
            return {
                "success": False,
                "message": f"Unknown action '{action}' for agent '{agent_name}'.",
            }

        try:
            result = operation(**kwargs)

            if not isinstance(result, dict):
                return {
                    "success": False,
                    "message": "Agent returned an unexpected response.",
                }

            return result

        except Exception as exc:
            return {
                "success": False,
                "agent": agent.agent_name,
                "action": action,
                "message": str(exc),
            }