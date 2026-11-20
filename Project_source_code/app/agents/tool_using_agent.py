import json
import re

from app.agents.base_agent import BaseAgent
from app.services.ollama_service import OllamaService
from app.tools.academic_tools import build_academic_tool_registry


class ToolUsingAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="Academic Tool Using Agent",
            description=(
                "Uses an LLM to understand academic requests, "
                "select registered tools, execute operations, "
                "and generate contextual responses."
            )
        )

        self.registry = build_academic_tool_registry()

    # --------------------------------------------------
    # STEP 1: Parse JSON returned by the LLM
    # --------------------------------------------------

    def _parse_json(self, response):

        response = response.strip()

        response = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response
        )

        try:
            return json.loads(response)

        except json.JSONDecodeError as error:

            raise ValueError(
                f"LLM returned invalid JSON: {response}"
            ) from error

    # --------------------------------------------------
    # STEP 2: Inject authenticated identity
    # --------------------------------------------------

    def _inject_identity(self, tool_name, arguments, input_data):

        tool = self.registry.get_tool(tool_name)

        if not tool:
            raise ValueError(
                f"Unknown tool selected: {tool_name}"
            )

        identity = {
            "user_id": input_data.get("user_id"),
            "role": input_data.get("role"),
            "professor_id": input_data.get("user_id"),
            "student_id": input_data.get("user_id")
        }

        for parameter, value in identity.items():

            if (
                parameter in tool.required_parameters
                or parameter in tool.optional_parameters
            ):
                arguments[parameter] = value

        return arguments

    # --------------------------------------------------
    # STEP 3: Handle general conversational responses
    # --------------------------------------------------

    def _generate_general_response(self, input_data):

        messages = input_data.get("messages", [])

        if not messages:
            messages = [
                {
                    "role": "user",
                    "content": input_data.get("request", "")
                }
            ]

        answer = OllamaService.generate_response(
            messages=messages,
            context=input_data.get("context", {})
        )

        return {
            "status": "responded",
            "final_response": answer,
            "selection_reason": "No academic tool was required."
        }

    # --------------------------------------------------
    # STEP 4: Main agent execution
    # --------------------------------------------------

    def execute(self, input_data):

        user_request = input_data.get("request")
        user_id = input_data.get("user_id")
        role = input_data.get("role")

        if (
            not isinstance(user_request, str)
            or not user_request.strip()
        ):
            raise ValueError("User request is required.")

        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
            or role not in ("student", "professor")
        ):
            raise ValueError("Valid user identity is required.")

        available_tools = self.registry.list_tools()

        # ----------------------------------------------
        # STEP 1: Ask LLM to understand the request
        # ----------------------------------------------

        selection_prompt = f"""
You are the intelligent decision-making engine of AcademicFlow.

Understand the user's request and decide whether to:

1. Execute a registered academic tool.
2. Respond conversationally without a tool.
3. Ask the user for clarification.

AVAILABLE TOOLS:

{json.dumps(available_tools, indent=2, default=str)}

USER ROLE:
{role}

USER REQUEST:
{user_request}

DECISION RULES:

1. Use "execute" when the request requires retrieving or
   performing an academic operation supported by an available tool.

2. Use "respond" when the user asks general questions,
   greetings, explanations, academic concepts, or conversational
   questions that do not require accessing academic records.

3. Use "clarify" when a required academic identifier or
   other necessary information is missing.

4. Select only tools listed in AVAILABLE TOOLS.

5. Never invent tool names, academic IDs, user IDs,
   professor IDs or student IDs.

6. Do not select a tool for a general academic explanation.

7. Do not claim that an academic operation has been completed
   unless a tool is actually executed.

8. Return only valid JSON. Do not include markdown.

OUTPUT FORMAT:

For tool execution:

{{
    "action": "execute",
    "tool_name": "exact_registered_tool_name",
    "arguments": {{}},
    "reason": "Reason for selecting the tool"
}}

For conversational response:

{{
    "action": "respond",
    "reason": "Reason why no tool is required"
}}

For clarification:

{{
    "action": "clarify",
    "message": "Information required from the user"
}}
"""

        selection_response = OllamaService.generate_response(
            messages=[
                {
                    "role": "user",
                    "content": selection_prompt
                }
            ]
        )

        decision = self._parse_json(selection_response)

        if not isinstance(decision, dict):
            raise ValueError(
                "LLM decision must be a JSON object."
            )

        action = decision.get("action")

        # ----------------------------------------------
        # STEP 2: Handle conversational response
        # ----------------------------------------------

        if action == "respond":

            return self._generate_general_response(input_data)

        # ----------------------------------------------
        # STEP 3: Handle clarification
        # ----------------------------------------------

        if action == "clarify":

            return {
                "status": "clarification_required",
                "message": decision.get(
                    "message",
                    "Additional information is required."
                )
            }

        if action != "execute":

            raise ValueError(
                f"Invalid action returned by the LLM: {action}"
            )

        # ----------------------------------------------
        # STEP 4: Validate selected tool
        # ----------------------------------------------

        tool_name = decision.get("tool_name")
        arguments = decision.get("arguments", {})

        if not isinstance(tool_name, str):
            raise ValueError("Invalid tool name.")

        if not isinstance(arguments, dict):
            raise ValueError(
                "Tool arguments must be a dictionary."
            )

        tool = self.registry.get_tool(tool_name)

        if not tool:
            raise ValueError(
                f"LLM selected an unregistered tool: {tool_name}"
            )

        # ----------------------------------------------
        # STEP 5: Inject authenticated identity
        # ----------------------------------------------

        arguments = self._inject_identity(
            tool_name,
            arguments,
            input_data
        )

        # ----------------------------------------------
        # STEP 6: Execute registered tool
        # ----------------------------------------------

        tool_result = self.registry.execute_tool(
            tool_name,
            arguments
        )

        # ----------------------------------------------
        # STEP 7: Generate natural language response
        # ----------------------------------------------

        final_response = OllamaService.generate_response(
            messages=[
                {
                    "role": "user",
                    "content": f"""
You are AcademicFlow AI.

USER REQUEST:
{user_request}

EXECUTED TOOL:
{tool_name}

ACTUAL TOOL RESULT:
{json.dumps(tool_result, default=str, ensure_ascii=False)}

Explain the result clearly and naturally.

RULES:

1. Use only information present in the actual tool result.
2. Never invent academic records or identifiers.
3. Preserve actual marks, deadlines, IDs and statuses.
4. If no records are available, clearly communicate that.
5. Do not claim an operation succeeded unless the tool result
   confirms it.
6. Keep the response relevant to the user's request.
"""
                }
            ]
        )

        # ----------------------------------------------
        # STEP 8: Return execution information
        # ----------------------------------------------

        return {
            "status": "completed",
            "selected_tool": tool_name,
            "selection_reason": decision.get("reason"),
            "tool_arguments": arguments,
            "tool_output": tool_result,
            "final_response": final_response
        }