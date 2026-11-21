import os
import requests
from dotenv import load_dotenv
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)




def generate_ai_content(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

    if not api_key:
        raise ValueError("Gemini API key is missing.")

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    candidates = result.get("candidates", [])

    if not candidates:
        raise ValueError("AI did not return a response.")

    parts = candidates[0].get("content", {}).get("parts", [])

    output = "\n".join(
        part.get("text", "") for part in parts
    )

    if not output.strip():
        raise ValueError("AI returned empty content.")

    return output
