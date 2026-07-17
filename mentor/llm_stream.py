from __future__ import annotations

import json
import re
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

LLMOutputCallback = Callable[[str, str], None]

_CURRENT_OUTPUT_CALLBACK: ContextVar[LLMOutputCallback | None] = ContextVar(
    "current_llm_output_callback",
    default=None,
)

FIELD_LABELS: dict[str, str] = {
    "concept_statement": "콘셉트",
    "target_player": "타깃 플레이어",
    "emotion_goal": "감정 목표",
    "core_loop": "코어 루프",
    "reward_structure": "반복 동기",
    "mvp_goal": "MVP 목표",
    "intent_diagnosis": "의도 정렬 진단",
    "core_loop_diagnosis": "코어 루프 진단",
    "scope_diagnosis": "범위 진단",
    "playtest_hypothesis": "플레이테스트 가설",
    "reflection_summary": "학습 요약",
    "next_self_check_question": "다음 자가 점검 질문",
    "final_summary": "먼저 정할 것",
    "reply": "답변",
    "revision_note": "정정 메모",
    "answer_note": "보완 메모",
    "reason": "분류 근거",
}

LIST_FIELD_LABELS: dict[str, str] = {
    "differentiation_points": "차별화 포인트",
    "feature_list": "기능 목록",
    "reference_titles": "레퍼런스",
    "intent_rationale": "의도 정렬 근거",
    "core_loop_rationale": "코어 루프 근거",
    "scope_rationale": "범위 근거",
    "playtest_rationale": "플레이테스트 근거",
    "mentor_principles": "판단 기준",
    "scope_recommendations": "범위 제안",
    "playtest_questions": "플레이테스트 질문",
}


@contextmanager
def llm_output_context(output_callback: LLMOutputCallback | None):
    token = _CURRENT_OUTPUT_CALLBACK.set(output_callback)
    try:
        yield
    finally:
        _CURRENT_OUTPUT_CALLBACK.reset(token)


def get_stream_config(title: str) -> dict[str, Any] | None:
    output_callback = _CURRENT_OUTPUT_CALLBACK.get()
    if output_callback is None:
        return None
    return {"callbacks": [_ReadableTokenCallback(title, output_callback)]}


def report_structured_output(title: str, payload: Any) -> None:
    output_callback = _CURRENT_OUTPUT_CALLBACK.get()
    if output_callback is None:
        return

    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif isinstance(payload, dict):
        data = payload
    else:
        output_callback(title, str(payload))
        return

    rendered = _render_data(data)
    if rendered:
        output_callback(title, rendered)


class _ReadableTokenCallback(BaseCallbackHandler):
    def __init__(self, title: str, output_callback: LLMOutputCallback) -> None:
        self.title = title
        self.output_callback = output_callback
        self.buffer = ""
        self.last_display = ""

    def on_llm_new_token(self, token: str, **_: Any) -> None:
        if not token:
            return
        self.buffer += token
        display = _humanize_stream_buffer(self.buffer)
        if not display or display == self.last_display:
            return
        if len(display) - len(self.last_display) < 12 and not display.endswith((".", "다", "요", "\n")):
            return
        self.last_display = display
        self.output_callback(self.title, display)


def _humanize_stream_buffer(buffer: str) -> str:
    lines: list[str] = []

    for field, label in FIELD_LABELS.items():
        value = _extract_partial_string_value(buffer, field)
        if value:
            lines.append(f"**{label}**\n{value}")

    for field, label in LIST_FIELD_LABELS.items():
        values = _extract_partial_list_values(buffer, field)
        if values:
            lines.append(f"**{label}**\n" + "\n".join(f"- {value}" for value in values))

    if lines:
        return "\n\n".join(lines)

    return _compact_raw_tokens(buffer)


def _extract_partial_string_value(buffer: str, field: str) -> str:
    match = re.search(rf'"{re.escape(field)}"\s*:\s*"((?:\\.|[^"\\])*)', buffer)
    if match is None:
        return ""
    return _decode_jsonish_string(match.group(1))


def _extract_partial_list_values(buffer: str, field: str) -> list[str]:
    match = re.search(rf'"{re.escape(field)}"\s*:\s*\[(.*?)(?:\]|\Z)', buffer, re.S)
    if match is None:
        return []
    values = []
    for raw_value in re.findall(r'"((?:\\.|[^"\\])*)"', match.group(1)):
        value = _decode_jsonish_string(raw_value)
        if value:
            values.append(value)
    return values


def _decode_jsonish_string(raw_value: str) -> str:
    try:
        return str(json.loads(f'"{raw_value}"')).strip()
    except json.JSONDecodeError:
        return (
            raw_value.replace("\\n", "\n")
            .replace('\\"', '"')
            .replace("\\/", "/")
            .strip()
        )


def _compact_raw_tokens(buffer: str) -> str:
    compacted = (
        buffer.replace("{", "")
        .replace("}", "")
        .replace("[", "")
        .replace("]", "")
        .replace('"', "")
        .replace(",", "\n")
        .strip()
    )
    return compacted[-1000:]


def _render_data(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for field, label in FIELD_LABELS.items():
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            lines.append(f"**{label}**\n{value.strip()}")

    for field, label in LIST_FIELD_LABELS.items():
        value = data.get(field)
        if isinstance(value, list) and value:
            rendered_values = [
                item.strip()
                for item in value
                if isinstance(item, str) and item.strip()
            ]
            if rendered_values:
                lines.append(
                    f"**{label}**\n"
                    + "\n".join(f"- {item}" for item in rendered_values)
                )

    if not lines:
        for field, value in data.items():
            if isinstance(value, str) and value.strip():
                lines.append(f"**{field}**\n{value.strip()}")

    return "\n\n".join(lines)
