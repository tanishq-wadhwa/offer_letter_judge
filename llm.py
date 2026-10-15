"""Groq model setup. Models are created lazily so API keys can be entered in the UI."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

BIG_MODEL = "openai/gpt-oss-120b"  # analysis + critic
SMALL_MODEL = "openai/gpt-oss-20b"  # extraction (saves free-tier tokens)

_cache = {}


def get_llm(kind: str = "big"):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .env or the sidebar.")
    name = BIG_MODEL if kind == "big" else SMALL_MODEL
    ck = (name, key)
    if ck not in _cache:
        _cache[ck] = init_chat_model(name, model_provider="groq", temperature=0)
    return _cache[ck]
