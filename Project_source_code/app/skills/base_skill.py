from abc import ABC, abstractmethod


class BaseSkill(ABC):

    def __init__(self, name, description, required_parameters=None):

        self.name = name
        self.description = description
        self.required_parameters = required_parameters or []

    @abstractmethod
    def execute(self, context, parameters):
        pass

    def run(self, context, parameters=None):

        parameters = parameters or {}

        if not isinstance(context, dict):
            raise TypeError("Skill context must be a dictionary.")

        if not isinstance(parameters, dict):
            raise TypeError("Skill parameters must be a dictionary.")

        missing = [
            parameter
            for parameter in self.required_parameters
            if parameter not in parameters
        ]

        if missing:
            raise ValueError(
                f"Missing skill parameters: {missing}"
            )

        return self.execute(context, parameters)