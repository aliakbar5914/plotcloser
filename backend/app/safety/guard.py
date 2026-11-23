"""Rule-based safety check. Runs BEFORE the AI, so blocked messages cost $0.

Layer 1 (here): catch clear prompt-injection and clearly off-topic requests.
Layer 2 (system prompt): the AI itself refuses anything else off-topic.
"""
import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|your)\s+(instructions|rules|prompts?|messages)",
    r"(forget|disregard|override|bypass)\s+(all\s+|your\s+|the\s+|previous\s+)*(instructions|rules|guidelines|prompt)",
    r"(reveal|show|print|repeat|tell me|give me|what is|what are|what's)\s+(me\s+)?your\s+(system\s+)?(prompt|instructions|rules)",
    r"(reveal|show|print|repeat|output)\s+(the\s+)?(hidden\s+|initial\s+)?(prompt|instructions)",
    r"system\s+prompt",
    r"\byou\s+are\s+now\b",
    r"\b(developer|dev|god|admin|jailbreak|dan)\s+mode\b",
    r"\bjailbreak\b",
    r"pretend\s+(to\s+be|you\s+are)",
    r"act\s+as\s+(an?\s+)?(different|unrestricted|evil|hacker|admin|developer)",
    r"new\s+instructions\s*:",
    r"</?\s*(system|assistant|instructions?)\s*>",
    r"\b(api[\s_-]?key|secret\s+key|database\s+password|env\s+file)\b",
    r"\.env\b",
]

OTHER_USERS_PATTERNS = [
    r"\b(other|another|all|every)\s+(users?|customers?|clients?|leads?)('s)?\s+(data|details|orders|visits|bookings|numbers|info)",
    r"\b(data|details|visits|bookings|info)\s+(of|for)\s+(other|another|all)\s+(users?|customers?)",
    r"\bshow\s+(me\s+)?(user|customer)\s+\w+'?s?\s+(data|visits|bookings|details)",
    r"\b(list|show|dump|export)\s+(all|every)\s+(users?|customers?|leads?)",
]

OFF_TOPIC_PATTERNS = [
    r"\b(write|create|generate|give me)\b.{0,30}\b(poem|essay|story|song|lyrics|joke|code|program|script|function|assignment|homework)\b",
    r"\b(python|javascript|java|c\+\+|sql|html|css)\s+(code|program|script|function)\b",
    r"\b(solve|calculate)\b.{0,20}\b(equation|integral|derivative|math problem)\b",
    r"\b(homework|assignment)\b",
    r"\b(recipe|cook|cricket score|football score|movie|weather forecast|horoscope)\b",
    r"\btranslate\b.{0,40}\b(into|to)\s+\w+",
    r"\bwho\s+(won|is\s+the\s+(president|prime\s+minister))\b",
]

REFUSALS = {
    "injection": ("I can't do that. I'm PlotCloser, and I can only help you find, "
                  "visit or buy a property or car. What are you looking for?"),
    "other_users": ("Sorry, I can't share any other customer's information. "
                    "I can only help with your own search and bookings."),
    "off_topic": ("Sorry, I can only help with buying or renting property and cars "
                  "(listings, prices, visits and test drives). What are you looking for?"),
    "too_long": "Your message is too long. Please send a shorter message.",
}


def check_message(text: str, max_chars: int = 2000) -> str | None:
    """Return a refusal reason ('injection', 'off_topic', ...) or None if safe."""
    if len(text) > max_chars:
        return "too_long"
    lowered = text.lower()
    if any(re.search(p, lowered) for p in INJECTION_PATTERNS):
        return "injection"
    if any(re.search(p, lowered) for p in OTHER_USERS_PATTERNS):
        return "other_users"
    if any(re.search(p, lowered) for p in OFF_TOPIC_PATTERNS):
        return "off_topic"
    return None
