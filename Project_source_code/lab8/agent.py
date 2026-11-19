from lab8.swarm import SwarmManager, demo_swarm
class SwarmAgent:
    def run(self, task="Prepare an academic status summary"):
        agents={"course_agent":lambda t:{"courses":["AI101","DBMS"]},
                "notes_agent":lambda t:{"notes_found":3},
                "assignment_agent":lambda t:{"pending":1,"overdue":0}}
        return SwarmManager(agents).run(task)
