from __future__ import annotations

import json

from langchain_core.messages import AnyMessage

from .models import MentorState, StructuredBrief


def clean_text(value: str) -> str:
    return " ".join(value.split()).strip()


def normalize_string_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def normalize_int(value: int | None) -> int:
    if value is None:
        return 0
    return max(0, value)


def message_to_text(message: AnyMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""


def conversation_text(messages: list[AnyMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        text = message_to_text(message)
        if not text:
            continue
        prefix = "User" if message.type == "human" else "Assistant"
        lines.append(f"{prefix}: {text}")
    return "\n".join(lines).strip()


def resolve_raw_input(state: MentorState) -> str:
    messages = state.get("messages", [])
    if messages:
        message_text = conversation_text(messages)
        if message_text:
            return message_text
    return state.get("raw_input", "").strip()


def raw_input_is_too_short(raw_input: str) -> bool:
    return len(raw_input.split()) < 5


def normalize_brief(brief: StructuredBrief) -> StructuredBrief:
    return StructuredBrief(
        concept_statement=clean_text(brief.concept_statement),
        target_player=clean_text(brief.target_player),
        emotion_goal=clean_text(brief.emotion_goal),
        core_loop=clean_text(brief.core_loop),
        reward_structure=clean_text(brief.reward_structure),
        differentiation_points=normalize_string_list(brief.differentiation_points),
        feature_list=normalize_string_list(brief.feature_list),
        development_window_weeks=normalize_int(brief.development_window_weeks),
        team_composition=clean_text(brief.team_composition),
        mvp_goal=clean_text(brief.mvp_goal),
        test_audience=clean_text(brief.test_audience),
        constraints_note=clean_text(brief.constraints_note),
        reference_titles=normalize_string_list(brief.reference_titles),
    )


def brief_from_state(state: MentorState) -> StructuredBrief:
    return StructuredBrief(
        concept_statement=state.get("concept_statement", ""),
        target_player=state.get("target_player", ""),
        emotion_goal=state.get("emotion_goal", ""),
        core_loop=state.get("core_loop", ""),
        reward_structure=state.get("reward_structure", ""),
        differentiation_points=state.get("differentiation_points", []),
        feature_list=state.get("feature_list", []),
        development_window_weeks=state.get("development_window_weeks", 0),
        team_composition=state.get("team_composition", ""),
        mvp_goal=state.get("mvp_goal", ""),
        test_audience=state.get("test_audience", ""),
        constraints_note=state.get("constraints_note", ""),
        reference_titles=state.get("reference_titles", []),
    )


def apply_brief_to_state(state: MentorState, brief: StructuredBrief) -> None:
    normalized = normalize_brief(brief)
    state.update(normalized.model_dump())


def serialize_brief_for_prompt(state: MentorState) -> str:
    return json.dumps(
        brief_from_state(state).model_dump(),
        ensure_ascii=False,
        indent=2,
    )
