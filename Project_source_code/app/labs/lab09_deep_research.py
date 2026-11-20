import json
from datetime import datetime


class DeepResearchAgent:
    """Collects, evaluates and synthesizes evidence from supplied sources."""

    def run(self, topic, sources):
        if not topic or not isinstance(sources, list):
            raise ValueError("A topic and a list of sources are required.")

        evidence = []

        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                continue

            title = source.get("title", f"Source {index}")
            content = str(source.get("content", "")).strip()

            if content:
                evidence.append({
                    "source_id": index,
                    "title": title,
                    "evidence": content,
                    "word_count": len(content.split())
                })

        return {
            "agent": "Deep Research Agent",
            "topic": topic,
            "status": "completed" if evidence else "no_evidence",
            "evidence_count": len(evidence),
            "evidence": evidence,
            "research_summary": (
                f"Collected {len(evidence)} evidence items for: {topic}. "
                "The findings below are based only on the supplied sources."
            ),
            "limitations": (
                "No independent web verification was performed. "
                "Source accuracy has not been independently confirmed."
            ),
            "timestamp": datetime.now().isoformat()
        }


def run_lab():
    agent = DeepResearchAgent()

    result = agent.run(
        topic="Applications of Artificial Intelligence in Education",
        sources=[
            {
                "title": "Source 1 - Adaptive Learning",
                "content": (
                    "Adaptive learning systems personalize educational "
                    "content based on student performance and learning needs."
                )
            },
            {
                "title": "Source 2 - Automated Assessment",
                "content": (
                    "Artificial intelligence can support automated "
                    "assessment, feedback generation and learning analytics."
                )
            },
            {
                "title": "Source 3 - Academic Assistance",
                "content": (
                    "AI assistants can help students understand concepts "
                    "and access academic information."
                )
            }
        ]
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run_lab()