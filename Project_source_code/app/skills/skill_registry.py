class SkillRegistry:

    def __init__(self):
        self.skills = {}

    def register(self, skill):

        if skill.name in self.skills:
            raise ValueError(
                f"Skill already registered: {skill.name}"
            )

        self.skills[skill.name] = skill

    def get_skill(self, name):
        return self.skills.get(name)

    def list_skills(self):

        return [
            {
                "name": skill.name,
                "description": skill.description,
                "required_parameters": skill.required_parameters
            }
            for skill in self.skills.values()
        ]

    def execute(self, name, context, parameters=None):

        skill = self.get_skill(name)

        if not skill:
            raise ValueError(
                f"Unknown skill: {name}"
            )

        return skill.run(
            context=context,
            parameters=parameters or {}
        )