import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv


load_dotenv()


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL = "openrouter/free"


def ask_ai(
    prompt,
    system_prompt=None,
    model=DEFAULT_MODEL,
    temperature=0.7,
    max_tokens=800,
):
    """
    Send a prompt to OpenRouter and return the AI response.
    """

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is not configured.",
            "response": None,
        }

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    request_data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OPENROUTER_URL,
        data=request_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:5000",
            "X-Title": "RicozStore",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:

            raw_response = response.read().decode(
                "utf-8"
            )

            data = json.loads(raw_response)

            choices = data.get(
                "choices",
                []
            )

            if not choices:
                return {
                    "success": False,
                    "error": "AI returned an empty response.",
                    "response": None,
                }

            message = choices[0].get(
                "message",
                {}
            )

            content = message.get(
                "content",
                ""
            )

            return {
                "success": True,
                "error": None,
                "response": content.strip(),
                "model": data.get(
                    "model",
                    model,
                ),
            }

    except urllib.error.HTTPError as error:

        try:
            error_body = error.read().decode(
                "utf-8"
            )

            error_data = json.loads(
                error_body
            )

            error_message = (
                error_data
                .get("error", {})
                .get(
                    "message",
                    "OpenRouter request failed.",
                )
            )

        except Exception:

            error_message = (
                "OpenRouter request failed."
            )

        return {
            "success": False,
            "error": error_message,
            "response": None,
            "status_code": error.code,
        }

    except urllib.error.URLError as error:

        return {
            "success": False,
            "error": (
                "Unable to connect to OpenRouter: "
                f"{error.reason}"
            ),
            "response": None,
        }

    except TimeoutError:

        return {
            "success": False,
            "error": (
                "The AI request timed out. "
                "Please try again."
            ),
            "response": None,
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error),
            "response": None,
        }