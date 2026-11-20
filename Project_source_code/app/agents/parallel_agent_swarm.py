from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

from app.agents.central_agent import CentralAgent


class ParallelAgentSwarm:

    def __init__(self, max_workers=3):

        self.max_workers = max_workers

    def execute_single_task(self, task_data):

        task_name = task_data.get("task", "unknown")

        start_time = time.perf_counter()

        started_at = datetime.now().isoformat()

        try:

            # Each task gets its own coordinator instance.
            # This avoids sharing mutable agent state across threads.

            coordinator = CentralAgent()

            result = coordinator.run(task_data)

            duration = round(
                time.perf_counter() - start_time,
                4
            )

            return {
                "task": task_name,
                "status": "completed",
                "started_at": started_at,
                "completed_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "result": result
            }

        except Exception as error:

            duration = round(
                time.perf_counter() - start_time,
                4
            )

            return {
                "task": task_name,
                "status": "failed",
                "started_at": started_at,
                "completed_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "error": str(error)
            }

    def execute(self, tasks):

        if not isinstance(tasks, list) or not tasks:

            raise ValueError(
                "Tasks must be a non-empty list."
            )

        print("\n[PARALLEL SWARM STARTED]")

        overall_start = time.perf_counter()

        results = []

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            future_to_task = {

                executor.submit(
                    self.execute_single_task,
                    task
                ): task

                for task in tasks
            }

            for future in as_completed(future_to_task):

                result = future.result()

                results.append(result)

                print(
                    f"[{result['status'].upper()}] "
                    f"{result['task']} | "
                    f"{result['duration_seconds']} seconds"
                )

        total_duration = round(
            time.perf_counter() - overall_start,
            4
        )

        completed = sum(
            1 for result in results
            if result["status"] == "completed"
        )

        failed = sum(
            1 for result in results
            if result["status"] == "failed"
        )

        print("\n[PARALLEL SWARM FINISHED]")

        return {

            "swarm": "AcademicFlow Parallel Agent Swarm",

            "total_tasks": len(tasks),

            "completed_tasks": completed,

            "failed_tasks": failed,

            "max_workers": self.max_workers,

            "total_duration_seconds": total_duration,

            "results": results
        }