
import os
import requests
import logging

from pathlib import Path
from dotenv import load_dotenv
from contextvars import ContextVar


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


# =====================================
# AI PROVIDER CONFIGURATION
# =====================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY", ""
).strip()

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434"
).rstrip("/")

AI_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:1.5b"
)

OLLAMA_ENABLED = os.getenv(
    "OLLAMA_ENABLED", "true"
).lower() == "true"


# Request-local provider tracking

last_provider = ContextVar(
    "last_provider",
    default="None"
)

last_model = ContextVar(
    "last_model",
    default=""
)


# =====================================
# CENTRAL AI BRAIN
# =====================================

SYSTEM_PROMPT = """
You are CreatorOS AI, an intelligent assistant
for social media content creators.

Your expertise includes:

- YouTube and Instagram scripts
- Video titles and descriptions
- Hashtags and SEO keywords
- Content ideas
- AI prompt engineering
- Video concepts and storyboards
- Content planning
- Thumbnail recommendations
- Audience engagement
- Monetization guidance

Instructions:

1. Follow the requested language strictly.
2. Generate original and engaging content.
3. Follow the selected social media platform.
4. Provide clear and structured responses.
5. Follow the requested video duration.
6. Never invent analytics or live trends.
7. Never guarantee views or earnings.
8. Avoid unnecessary introductions.
9. Focus on the user's requirements.
10. For Hindi and Marathi, use Devanagari script.
"""


# =====================================
# PROVIDER 1 - GOOGLE GEMINI
# =====================================

def generate_gemini(prompt):

    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured.")

    url = (
        "https://generativelanguage.googleapis.com"
        f"/v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "systemInstruction": {
            "parts": [
                {"text": SYSTEM_PROMPT}
            ]
        },

        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],

        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=(5, 25)
    )

    response.raise_for_status()

    data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise ValueError("Gemini returned no content.")

    parts = candidates[0].get(
        "content", {}
    ).get("parts", [])

    output = "\n".join(
        part.get("text", "")
        for part in parts
        if not part.get("thought", False)
    ).strip()

    if not output:
        raise ValueError("Gemini returned empty content.")

    return output


# =====================================
# PROVIDER 2 - OPENROUTER
# =====================================

def generate_openrouter(prompt):

    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OpenRouter API key not configured."
        )

    url = (
        "https://openrouter.ai/api/v1/chat/completions"
    )

    headers = {
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json",
        "X-Title": "CreatorOS AI"
    }

    payload = {
        "model": OPENROUTER_MODEL,

        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=(5, 30)
    )

    response.raise_for_status()

    data = response.json()

    choices = data.get("choices", [])

    if not choices:
        raise ValueError(
            "OpenRouter returned no content."
        )

    output = (
        choices[0]
        .get("message", {})
        .get("content") or ""
    ).strip()

    if not output:
        raise ValueError(
            "OpenRouter returned empty content."
        )

    last_model.set(
        data.get("model", OPENROUTER_MODEL)
    )

    return output


# =====================================
# PROVIDER 3 - OLLAMA LOCAL AI
# =====================================

def generate_ollama(prompt):

    if not OLLAMA_ENABLED:
        raise ValueError("Ollama is disabled.")

    payload = {
        "model": AI_MODEL,

        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "stream": False,
        "keep_alive": "5m",

        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 1000,
            "num_ctx": 4096,
            "repeat_penalty": 1.1
        }
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=(5, 300)
    )

    response.raise_for_status()

    data = response.json()

    output = (
        data.get("message", {})
        .get("content") or ""
    ).strip()

    if not output:
        raise ValueError(
            "Ollama returned empty content."
        )

    return output


# =====================================
# AUTOMATIC TRIPLE FALLBACK ENGINE
# =====================================

def generate_ai_content(prompt):

    prompt = str(prompt).strip()

    if not prompt:
        raise ValueError(
            "Please enter your requirements."
        )

    last_provider.set("None")
    last_model.set("")

    providers = [
        (
            "Gemini",
            GEMINI_MODEL,
            generate_gemini,
            bool(GEMINI_API_KEY)
        ),
        (
            "OpenRouter",
            OPENROUTER_MODEL,
            generate_openrouter,
            bool(OPENROUTER_API_KEY)
        ),
        (
            "Ollama",
            AI_MODEL,
            generate_ollama,
            OLLAMA_ENABLED
        )
    ]

    for name, model, generator, enabled in providers:

        if not enabled:
            logger.info("%s skipped: disabled", name)
            continue

        try:

            last_model.set(model)

            logger.info("Trying AI provider: %s", name)

            output = generator(prompt)

            last_provider.set(name)

            logger.info(
                "AI generation successful: %s", name
            )

            return output

        except requests.exceptions.HTTPError as error:

            status = (
                error.response.status_code
                if error.response is not None
                else None
            )

            logger.warning(
                "%s failed with HTTP status %s. "
                "Trying next provider.",
                name,
                status
            )

        except (
            requests.exceptions.RequestException,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            IndexError
        ) as error:

            logger.warning(
                "%s unavailable (%s). "
                "Trying next provider.",
                name,
                type(error).__name__
            )

    last_provider.set("None")
    last_model.set("")

    raise ValueError(
        "All configured AI providers are currently "
        "unavailable. Please try again later."
    )


# =====================================
# LAST SUCCESSFUL AI PROVIDER
# =====================================

def get_last_provider():

    return last_provider.get()


def get_last_model():

    return last_model.get()


# =====================================
# AI CONNECTION STATUS
# =====================================

def check_ai_status():

    ollama_connected = False
    ollama_ready = False
    installed_models = []

    if OLLAMA_ENABLED:

        try:

            response = requests.get(
                f"{OLLAMA_URL}/api/tags",
                timeout=5
            )

            response.raise_for_status()

            installed_models = [
                model.get("name", "")
                for model in response.json().get(
                    "models", []
                )
            ]

            ollama_connected = True

            ollama_ready = AI_MODEL in installed_models

        except (
            requests.exceptions.RequestException,
            ValueError
        ):

            pass

    providers = {
        "Gemini": {
            "configured": bool(GEMINI_API_KEY),
            "model": GEMINI_MODEL
        },

        "OpenRouter": {
            "configured": bool(OPENROUTER_API_KEY),
            "model": OPENROUTER_MODEL
        },

        "Ollama": {
            "enabled": OLLAMA_ENABLED,
            "connected": ollama_connected,
            "ready": ollama_ready,
            "model": AI_MODEL
        }
    }

    return {
        "connected": ollama_connected,
        "ready": ollama_ready,
        "provider": "Multi-AI",
        "model": "Automatic Fallback",
        "installed_models": installed_models,
        "providers": providers
    }
