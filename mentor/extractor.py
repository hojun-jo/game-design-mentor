from __future__ import annotations

from .llm import get_extractor_llm
from .models import MentorState
from .state_utils import normalize_brief, raw_input_is_too_short, resolve_raw_input


def extract_brief(state: MentorState) -> dict:
    raw_input = resolve_raw_input(state)
    if not raw_input:
        raise ValueError("raw_input or messages is required.")
    if raw_input_is_too_short(raw_input):
        raise ValueError(
            "입력이 너무 짧습니다. 게임 콘셉트, 감정 목표, 코어 루프를 2~3문장 이상 적어 주세요."
        )

    prompt = f"""
You extract a structured game design brief from free-form text for a beginner indie game design mentor.
Return only what is explicitly stated or strongly implied. Never invent specific mechanics, schedule, or team details.

Field rules:
- concept_statement: one concise sentence describing the game concept
- target_player: one primary target player group
- emotion_goal: what the player should feel
- core_loop: the repeatable player action loop
- reward_structure: what makes the player want another run or turn
- differentiation_points: concrete experience differences, not slogan words
- feature_list: major MVP features only
- development_window_weeks: integer weeks, or 0 if unknown
- team_composition: short summary of roles and headcount
- mvp_goal: the one thing this MVP should prove
- test_audience: who should playtest first
- constraints_note: budget, asset, or technical constraints
- reference_titles: comparable reference titles only

User draft:
{raw_input}
""".strip()

    extracted = get_extractor_llm().invoke(prompt)
    return normalize_brief(extracted).model_dump()
