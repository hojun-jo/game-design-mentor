from __future__ import annotations

import json

from .llm import get_reviewer_base_llm
from .llm_stream import get_stream_config, report_structured_output
from .models import ChatMessage, DomainClassificationPayload, StructuredBrief
from .validation import is_game_design_related


ENGINE_PLATFORM_SIGNALS = (
    "steam",
    "스팀",
    "pc",
    "mobile",
    "모바일",
    "ios",
    "android",
    "web",
    "console",
    "콘솔",
)
ENGINE_VISUAL_SIGNALS = (
    "2d",
    "2.5d",
    "3d",
    "top view",
    "top-view",
    "탑뷰",
    "isometric",
    "아이소메트릭",
)
ENGINE_NETWORK_SIGNALS = (
    "multiplayer",
    "멀티플레이",
    "온라인",
    "network",
    "네트워크",
)
ENGINE_UPDATE_SIGNALS = (
    "출시",
    "예정",
    "목표",
    "검토",
    "후보",
    "지원",
    "요구",
    "사용",
    "경험",
)


def is_engine_brief_update(user_message: str) -> bool:
    """Recognize terse technical constraints added to an active game review."""
    text = " ".join(user_message.casefold().split())
    has_engine_constraint = any(
        signal in text
        for signal in (
            *ENGINE_PLATFORM_SIGNALS,
            *ENGINE_VISUAL_SIGNALS,
            *ENGINE_NETWORK_SIGNALS,
        )
    )
    if not has_engine_constraint:
        return False

    return any(signal in text for signal in ENGINE_UPDATE_SIGNALS) or "?" not in text

DOMAIN_REJECTION_MESSAGE = (
    "게임 기획과 관련된 내용만 리뷰할 수 있습니다. 게임 콘셉트, 플레이어, 코어 루프, "
    "보상 구조, MVP 목표 중 하나 이상을 포함해 주세요."
)


def classify_game_design_domain(
    raw_input: str,
    brief: StructuredBrief,
) -> DomainClassificationPayload:
    prompt = f"""
You classify whether a user's input is in scope for a game design mentor app.
Return only the structured classification.

Accept as in scope when the input is about designing, improving, or testing a game or game-like interactive experience.
In-scope examples include:
- game concept drafts, prototypes, MVP plans, player experience goals
- player intent, target player, emotion goals, mechanics, rules, core loops, rewards
- difficulty, balance, levels, enemies, quests, combat, puzzles, UI only when tied to gameplay
- playtest plans, design constraints, reference games used for design comparison

Reject as out of scope when the input is mainly about:
- general business strategy, sales, hiring, school assignments, personal advice, or software/product design unrelated to games
- game news, marketing copy, reviews, lore, fiction, or worldbuilding with no gameplay design question
- board reports or documents that merely contain ambiguous words like strategy, level, reward, or player

Classification rules:
- Do not accept only because one game-like keyword appears.
- Accept if there is a clear intent to design or evaluate gameplay, player experience, mechanics, scope, or playtesting.
- Use confidence="low" when the input could be interpreted either way.
- If confidence is low, set is_game_design_related=false so the app asks for a clearer game design brief.

Heuristic signal from local checks:
{json.dumps({"has_game_design_keyword_or_field_signal": is_game_design_related(raw_input, brief)}, ensure_ascii=False)}

Extracted structured brief:
{json.dumps(brief.model_dump(), ensure_ascii=False, indent=2)}

Original user input:
{raw_input}
""".strip()

    classifier = get_reviewer_base_llm().with_structured_output(
        DomainClassificationPayload
    )
    config = get_stream_config("게임 기획 관련성 확인 중")
    if config is None:
        payload = classifier.invoke(prompt)
    else:
        payload = classifier.invoke(prompt, config=config)
    report_structured_output("게임 기획 관련성 확인 중", payload)
    return DomainClassificationPayload(
        is_game_design_related=payload.is_game_design_related,
        confidence=payload.confidence,
        reason=payload.reason.strip(),
    )


def _jsonable_chat_history(chat_history: list[ChatMessage]) -> list[dict]:
    return [message.model_dump() for message in chat_history[-8:]]


def classify_follow_up_domain(
    user_message: str,
    interaction_context: dict,
    chat_history: list[ChatMessage],
) -> DomainClassificationPayload:
    prompt = f"""
You classify whether the latest user message is in scope for a game design mentor app conversation.
Return only the structured classification.

The app already has an active game design review or clarification flow.
Use the current context only to understand references like "why", "that point", "the scope", or "your question".

Accept as in scope when the latest user message:
- answers a pending game design clarification question
- asks what a pending clarification question means or asks for examples
- asks about the current review, its rationale, tradeoffs, scope, core loop, player intent, or playtest plan
- corrects or adds details about the current game design brief
- asks for help applying the review to this game design

Reject as out of scope when the latest user message is mainly about:
- unrelated general knowledge, weather, coding, business, hiring, schoolwork, personal advice, or non-game product design
- a new non-game document or task
- game news, lore, marketing, or entertainment discussion that does not ask for game design feedback

Classification rules:
- Classify the latest user message, not the whole history.
- Do not accept an unrelated latest message only because the existing context is game-related.
- Short context-dependent messages like "왜?", "예시 줘", or "그 범위는 왜 줄여?" are in scope if they naturally refer to the active review or pending question.
- Use confidence="low" when the latest message could plausibly be unrelated.
- If confidence is low, set is_game_design_related=false.

Current interaction context:
{json.dumps(interaction_context, ensure_ascii=False, indent=2)}

Recent chat history:
{json.dumps(_jsonable_chat_history(chat_history), ensure_ascii=False, indent=2)}

Latest user message:
{user_message}
""".strip()

    classifier = get_reviewer_base_llm().with_structured_output(
        DomainClassificationPayload
    )
    config = get_stream_config("대화 범위 확인 중")
    if config is None:
        payload = classifier.invoke(prompt)
    else:
        payload = classifier.invoke(prompt, config=config)
    report_structured_output("대화 범위 확인 중", payload)
    return DomainClassificationPayload(
        is_game_design_related=payload.is_game_design_related,
        confidence=payload.confidence,
        reason=payload.reason.strip(),
    )
