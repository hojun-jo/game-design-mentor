from __future__ import annotations

import json

from .llm import get_reviewer_base_llm
from .llm_stream import get_stream_config, report_structured_output
from .models import DomainClassificationPayload, StructuredBrief
from .validation import is_game_design_related

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


def ensure_game_design_domain(raw_input: str, brief: StructuredBrief) -> None:
    classification = classify_game_design_domain(raw_input, brief)
    if not classification.is_game_design_related or classification.confidence == "low":
        raise ValueError(DOMAIN_REJECTION_MESSAGE)
