from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from openai import OpenAI

from .models import StructuredBrief

load_dotenv()


def _require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")
    return api_key


@lru_cache(maxsize=1)
def get_extractor_llm():
    return init_chat_model(
        "openai:gpt-4o-mini",
        temperature=0,
        api_key=_require_api_key(),
    ).with_structured_output(StructuredBrief)


@lru_cache(maxsize=1)
def get_reviewer_base_llm():
    return init_chat_model(
        "openai:gpt-4o-mini",
        temperature=0.2,
        api_key=_require_api_key(),
    )


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    return OpenAI(api_key=_require_api_key())
