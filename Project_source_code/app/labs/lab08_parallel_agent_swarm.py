import json

from app.agents.parallel_agent_swarm import ParallelAgentSwarm


def main():

    print("=" * 55)

    print("       LAB 8 - PARALLEL AGENT SWARM")

    print("=" * 55)

    # Three independent academic tasks.
    # All operations below are read-only.

    tasks = [

        {
            "task": "notes",
            "user_id": 1,
            "role": "professor"
        },

        {
            "task": "assignments",
            "action": "list",
            "course_id": 1,
            "user_id": 1,
            "role": "professor"
        },

        {
            "task": "milestones",
            "action": "list",
            "project_id": 1,
            "user_id": 1,
            "role": "professor"
        }

    ]

    print("\n[1] TASK DISTRIBUTION")

    for index, task in enumerate(tasks, start=1):

        print(
            f"{index}. {task['task']} agent"
        )

    # Create the swarm.

    swarm = ParallelAgentSwarm(max_workers=3)

    print("\n[2] PARALLEL EXECUTION")

    result = swarm.execute(tasks)

    print("\n[3] FINAL SWARM RESULT")

    print(
        json.dumps(
            result,
            indent=4,
            default=str
        )
    )

    print("\n[4] EXECUTION SUMMARY")

    print(
        "Total Tasks:",
        result["total_tasks"]
    )

    print(
        "Completed:",
        result["completed_tasks"]
    )

    print(
        "Failed:",
        result["failed_tasks"]
    )

    print(
        "Total Execution Time:",
        result["total_duration_seconds"],
        "seconds"
    )

    print("\n[5] INDIVIDUAL AGENT RESULTS")

    for item in result["results"]:

        print("\nTask:", item["task"])

        print("Status:", item["status"])

        print(
            "Duration:",
            item["duration_seconds"],
            "seconds"
        )

        if item["status"] == "failed":

            print("Error:", item["error"])

    print("\n" + "=" * 55)

    print("       LAB 8 EXECUTION COMPLETED")

    print("=" * 55)


if __name__ == "__main__":

    main()