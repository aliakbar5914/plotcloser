"""Reads all settings from the .env file in one place."""
import os

from dotenv import load_dotenv

load_dotenv()  # loads backend/.env into environment variables


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required setting: {name} (check your .env file)")
    return value


ANTHROPIC_API_KEY = _required("ANTHROPIC_API_KEY")
DATABASE_URL = _required("DATABASE_URL")
ADMIN_PASSWORD = _required("ADMIN_PASSWORD")

MODEL_NAME = os.getenv("MODEL_NAME", "claude-haiku-5-5")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Cost controls
# Haiku 5.5 "thinks" before answering and thinking tokens count toward this cap,
# so 1024 leaves room for thinking + a short reply.
MAX_OUTPUT_TOKENS = 1024
REASONING_EFFORT = "low"      # less thinking = fewer tokens; enough for sales chat
MAX_HISTORY_MESSAGES = 10     # short-term memory trim size
MAX_MESSAGE_CHARS = 2000      # reject very long user messages
LLM_TIMEOUT_SECONDS = 30
LLM_MAX_RETRIES = 2           # SDK retries 429 / 5xx / network errors

# Haiku 5.5 price (USD per 1M tokens), used only to show cost in the dashboard
PRICE_INPUT_PER_MTOK = 0.10
PRICE_OUTPUT_PER_MTOK = 0.50
