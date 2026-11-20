import json
from datetime import datetime

from app.labs.lab09_deep_research import DeepResearchAgent
from app.labs.lab10_cloud_operations import CloudOperationsAgent
from app.labs.lab11_agentic_sdlc import AgenticSDLCFactory
from app.labs.lab12_safety_governance import SafetyGovernanceAgent
from app.labs.lab13_engineering_agent import EngineeringAgent


class CapstoneProjectStudio:
    """Coordinates multiple specialized agents in one workflow."""

    def __init__(self):
        self.research_agent = DeepResearchAgent()
        self.cloud_agent = CloudOperationsAgent()
        self.sdlc_agent = AgenticSDLCFactory()
        self.governance_agent = SafetyGovernanceAgent()
        self.engineering_agent = EngineeringAgent()

    def run(self):
        trace = []

        research = self.research_agent.run(
            "AI-Based Predictive Maintenance",
            [
                {
                    "title": "Predictive Maintenance",
                    "content": (
                        "Predictive maintenance uses sensor data "
                        "to identify possible equipment failures."
                    )
                },
                {
                    "title": "Machine Learning",
                    "content": (
                        "Machine learning models analyze historical "
                        "and real-time readings to detect anomalies."
                    )
                }
            ]
        )
        trace.append("Deep Research Agent completed")

        cloud = self.cloud_agent.analyze_logs(
            "INFO Application started\n"
            "WARNING High memory usage\n"
            "ERROR Sensor service unavailable"
        )
        trace.append("Cloud Operations Agent completed")

        sdlc = self.sdlc_agent.run(
            "Build an AI-based predictive maintenance system."
        )
        trace.append("Agentic SDLC Factory completed")

        governance = self.governance_agent.evaluate(
            role="admin",
            action="analyze_sensor_data",
            input_data={"sensor_count": 5}
        )
        trace.append("Safety and Governance Agent completed")

        engineering = self.engineering_agent.analyze(
            [35, 40, 42, 38, 91, 43],
            threshold=80
        )
        trace.append("Engineering Analysis Agent completed")

        return {
            "project": "Agentic AI Capstone Project Studio",
            "status": "completed",
            "agents_executed": 5,
            "execution_trace": trace,
            "results": {
                "research": research,
                "cloud_operations": cloud,
                "software_development": sdlc,
                "governance": governance,
                "engineering_analysis": engineering
            },
            "timestamp": datetime.now().isoformat()
        }


def run_lab():
    result = CapstoneProjectStudio().run()
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run_lab()