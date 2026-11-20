import json
import urllib.request
import urllib.error


class OllamaService:

    BASE_URL = "http://localhost:11434/api/chat"
    MODEL = "qwen2.5:3b"

    @classmethod
    def generate_response(cls, messages, context=None):

        system_prompt = """
You are AcademicFlow AI, an intelligent academic assistant.

Your responsibilities:
1. Help students understand academic concepts.
2. Answer questions about courses and assignments.
3. Explain deadlines and academic requirements.
4. Help professors manage academic activities.
5. Assist with student projects and milestones.

IMPORTANT RULES:
- Use the academic context provided to answer questions.
- Never invent assignments, deadlines, grades or course details.
- If information is unavailable, clearly say so.
- Respect the user's role and accessible information.
- Give clear, accurate and helpful answers.
"""

        if context:
            context_text = json.dumps(
                context,
                ensure_ascii=False,
                default=str
            )

            system_prompt += (
                "\n\nACADEMIC CONTEXT:\n" + context_text
            )

        conversation_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        conversation_messages.extend(messages)

        payload = {
            "model": cls.MODEL,
            "messages": conversation_messages,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }

        request = urllib.request.Request(
            cls.BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=180
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

                return result["message"]["content"].strip()

        except urllib.error.URLError as error:
            raise RuntimeError(
                "Unable to connect to Ollama. "
                "Make sure Ollama is running."
            ) from error

        except (KeyError, ValueError) as error:
            raise RuntimeError(
                "Invalid response received from Ollama."
            ) from error