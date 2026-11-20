from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    function: Callable
    required_parameters: list
    optional_parameters: list


class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register_tool(
        self,
        name,
        description,
        function,
        required_parameters=None,
        optional_parameters=None
    ):
        if name in self.tools:
            raise ValueError(f"Tool already registered: {name}")

        self.tools[name] = Tool(
            name=name,
            description=description,
            function=function,
            required_parameters=required_parameters or [],
            optional_parameters=optional_parameters or []
        )

    def get_tool(self, name):
        return self.tools.get(name)

    def list_tools(self):
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "required_parameters": tool.required_parameters,
                "optional_parameters": tool.optional_parameters
            }
            for tool in self.tools.values()
        ]

    def execute_tool(self, name, arguments):

        tool = self.get_tool(name)

        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a dictionary.")

        missing = [
            parameter
            for parameter in tool.required_parameters
            if parameter not in arguments
        ]

        if missing:
            raise ValueError(
                f"Missing required parameters: {missing}"
            )

        allowed = (
            tool.required_parameters
            + tool.optional_parameters
        )

        unexpected = [
            parameter
            for parameter in arguments
            if parameter not in allowed
        ]

        if unexpected:
            raise ValueError(
                f"Unexpected parameters: {unexpected}"
            )

        return tool.function(**arguments)