# app/llm.py
# -----------------------------------------------------------
# LLM module — Groq API integration with rule-based fallback.
#
# Primary:  Groq API  (llama3 via OpenAI-compatible client)
# Fallback: Rule-based keyword matching (offline-safe)
# -----------------------------------------------------------

import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import (
    GROQ_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    SYSTEM_PROMPT,
)
from app.utils import setup_logger

logger = setup_logger()


# ── Groq API call ─────────────────────────────────────────────

def call_groq(user_text: str, api_key: str) -> str:
    """
    Send user_text to Groq API and return the LLM response string.

    """
    # try:
    #     from openai import OpenAI
    # except ImportError:
    #     raise RuntimeError("openai package required: pip install openai")

    # client = OpenAI(
    #     api_key=api_key,
    #     base_url="https://api.groq.com/openai/v1",
    # )
    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("groq package required: pip install groq")

    client = Groq(api_key=api_key)

    logger.info(f"🤖 Calling Groq API (model: {GROQ_MODEL})...")

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_text},
        ],
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
    )

    response = completion.choices[0].message.content.strip()
    #logger.info("✅ Groq API response received.")
    if not response:
        return "No response generated."

    logger.info("✅ Groq API response received.")
    return response


# ── Rule-based fallback ───────────────────────────────────────

_RULES: list[tuple[list[str], str]] = [
    (
        ["temperature", "temp", "hot", "cold", "weather", "climate"],
        (
            "Observation noted. For temperature records, consider logging exact "
            "readings in Celsius along with time, GPS coordinates, and cloud cover. "
            "[SUMMARY] Temperature observation logged. Recommend cross-referencing "
            "with local meteorological data."
        ),
    ),
    (
        ["animal", "bird", "mammal", "species", "insect", "plant", "flora", "fauna"],
        (
            "Interesting biological observation! Note the exact location, time, "
            "behavior, and if possible capture a photo for species verification. "
            "[SUMMARY] Wildlife/flora sighting recorded. Document distinguishing "
            "features for later taxonomic identification."
        ),
    ),
    (
        ["water", "river", "stream", "lake", "rain", "flood", "moisture"],
        (
            "Hydrological observation logged. Consider recording water clarity, "
            "flow rate, and proximity to upstream sources. "
            "[SUMMARY] Water-related observation noted. Recommend pH and turbidity "
            "measurements if equipment is available."
        ),
    ),
    (
        ["soil", "rock", "geology", "mineral", "sediment", "erosion", "ground"],
        (
            "Geological note captured. Document layer depth, color, texture, and "
            "composition if possible. "
            "[SUMMARY] Soil/geology observation recorded. Consider soil sample "
            "collection for lab analysis."
        ),
    ),
    (
        ["wind", "air", "storm", "cloud", "fog", "mist", "humidity"],
        (
            "Atmospheric condition noted. Record wind direction, estimated speed, "
            "and visibility range for complete meteorological data. "
            "[SUMMARY] Atmospheric observation logged."
        ),
    ),
    (
        ["sample", "collect", "collect", "specimen", "measure", "record"],
        (
            "Collection activity noted. Ensure all samples are labeled with "
            "date, time, GPS coordinates, and field collector ID. "
            "[SUMMARY] Collection/measurement activity documented."
        ),
    ),
]

_DEFAULT_FALLBACK = (
    "Field note received and logged. Your observation has been recorded for "
    "later analysis. Consider adding GPS coordinates, timestamp, and environmental "
    "conditions for richer context. "
    "[SUMMARY] General field observation captured. Review and annotate during "
    "post-field data processing."
)


def rule_based_response(user_text: str) -> str:
    """
    Generate a response using keyword matching — no API required.

    Args:
        user_text: The user's transcribed text.

    Returns:
        A relevant pre-written response string.
    """
    lower = user_text.lower()
    for keywords, response in _RULES:
        if any(kw in lower for kw in keywords):
            logger.info(f"📋 Rule-based fallback matched keyword(s).")
            return response

    logger.info("📋 Rule-based fallback: using default response.")
    return _DEFAULT_FALLBACK


# ── Main entry point ──────────────────────────────────────────

def generate_response(user_text: str) -> str:
    """
    Generate an AI response for the given user text.

    Tries the Groq API first; falls back to rule-based if:
      - GROQ_API_KEY is not set
      - API call raises any exception

    Args:
        user_text: Transcribed user observation text.

    Returns:
        Response string (from Groq or fallback).
    """
    if not user_text or user_text.strip() == "(no speech detected)":
        return (
            "I didn't catch any speech. Please speak clearly into the microphone "
            "or check your audio file."
        )

    # Load API key from environment (dotenv loaded in main.py)
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not api_key:
        logger.warning("⚠️ GROQ_API_KEY not found. Using rule-based fallback.")
        return rule_based_response(user_text)

    try:
        return call_groq(user_text, api_key)
    except Exception as e:
        logger.error(f"❌ Groq API error: {e}")
        logger.info("🔄 Falling back to rule-based response...")
        return rule_based_response(user_text)