from app.agents.base_agent import BaseAgent

from app.agents.specialists import (
    NotesRepositoryAgent,
    AssignmentDistributionAgent,
    SubmissionCollectionAgent,
    SimilarityDetectionAgent,
    GradingAssistanceAgent,
    ProjectMilestoneAgent,
    GradePublishingAgent
)


class CentralAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="AcademicFlow Central Coordinator",
            description=(
                "Coordinates seven specialist agents "
                "to manage academic activities."
            )
        )

        self.agents = {
            "notes": NotesRepositoryAgent(),
            "assignments": AssignmentDistributionAgent(),
            "submissions": SubmissionCollectionAgent(),
            "similarity": SimilarityDetectionAgent(),
            "grading": GradingAssistanceAgent(),
            "milestones": ProjectMilestoneAgent(),
            "grade_publishing": GradePublishingAgent()
        }

    def execute(self, input_data):

        task = input_data.get("task")

        if not task:
            raise ValueError("Task name is required.")

        if task not in self.agents:
            raise ValueError(
                f"Unknown task: {task}. "
                f"Available tasks: {list(self.agents.keys())}"
            )

        selected_agent = self.agents[task]

        agent_input = {
            key: value
            for key, value in input_data.items()
            if key != "task"
        }

        result = selected_agent.run(agent_input)

        return {
            "coordinator": self.name,
            "selected_agent": selected_agent.name,
            "task": task,
            "agent_result": result
        }

    def get_registered_agents(self):

        return [
            {
                "name": agent.name,
                "description": agent.description
            }
            for agent in self.agents.values()
        ]