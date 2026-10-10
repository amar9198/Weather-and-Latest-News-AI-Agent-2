
import os
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-120b"

MODELS = [
    "openai/gpt-oss-120b",
]

SUGGESTED_CITIES = [
    "Kanpur",
    "Lucknow",
    "Delhi",
    "Mumbai",
    "Agra",
]

DASHBOARD_NEWS_RESULTS = 3


def apply_streamlit_secrets():
    """Load configured API keys from Streamlit secrets."""
    for key in [
        "GROQ_API_KEY",
        "OPENWEATHER_API_KEY",
        "TAVILY_API_KEY",
    ]:
        try:
            value = st.secrets.get(key, "")
        except Exception:
            # No Streamlit secrets file; use environment/.env.
            continue

        if value and str(value).strip():
            os.environ[key] = str(value).strip()

def key_configured(key):
    """Return True when an API key is configured."""
    return bool(os.getenv(key, "").strip())


def missing_keys():
    """Return required API keys that have not been configured."""
    required = [
        "GROQ_API_KEY",
        "OPENWEATHER_API_KEY",
        "TAVILY_API_KEY",
    ]
    return [key for key in required if not key_configured(key)]


def redact(value):
    """Avoid exposing API keys in displayed error messages."""
    text = str(value)

    for key in [
        "GROQ_API_KEY",
        "OPENWEATHER_API_KEY",
        "TAVILY_API_KEY",
    ]:
        secret = os.getenv(key, "")
        if secret:
            text = text.replace(secret, "[REDACTED]")

    return text
