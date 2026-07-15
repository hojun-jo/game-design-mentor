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
Use only facts explicitly stated in the user's draft or later user clarifications.
Never fill a field from genre conventions, likely intent, best practices, or your own assumptions.
If the source text does not clearly state a field, return the empty value for that field so the app can ask the user.

Field rules:
- concept_statement: one concise sentence describing the explicitly stated game concept, or "" if no concept is stated
- target_player: explicitly stated target player group, or ""
- emotion_goal: explicitly stated player emotion goal, or ""
- core_loop: explicitly stated repeatable player action loop, or ""
- reward_structure: explicitly stated reward or repeat motivation, or ""
- differentiation_points: explicitly stated concrete experience differences only, or []
- feature_list: explicitly stated MVP features only, or []
- development_window_weeks: explicitly stated integer weeks, or 0 if unknown
- team_composition: explicitly stated roles and headcount, or ""
- mvp_goal: explicitly stated MVP validation goal, or ""
- test_audience: explicitly stated playtest audience, or ""
- constraints_note: explicitly stated budget, asset, or technical constraints, or ""
- reference_titles: explicitly named comparable reference titles only, or []

Extraction bans:
- Do not infer target_player from genre, platform, theme, difficulty, or tone.
- Do not infer emotion_goal from adjectives unless the user says players should feel it.
- Do not convert a list of possible ideas into confirmed MVP features unless the user marks them as MVP scope.
- Do not infer reward_structure from common genre loops.
- Do not infer mvp_goal from the concept or core loop.
- Do not infer test_audience from target_player.
- Do not repair contradictions. Preserve only what is explicit and let validation ask follow-up questions.

User draft:
{raw_input}
""".strip()

    extracted = get_extractor_llm().invoke(prompt)
    return normalize_brief(extracted).model_dump()
