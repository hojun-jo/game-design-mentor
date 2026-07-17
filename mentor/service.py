from __future__ import annotations

from collections.abc import Callable

from langchain_core.messages import HumanMessage

from .graph import get_review_graph
from .llm_stream import LLMOutputCallback, llm_output_context
from .models import (
    ChatMessage,
    DiagnosisResult,
    LearningResult,
    MentorState,
    PlaytestPlan,
    ReviewResponse,
    ScopeResult,
)
from .reviewer import (
    classify_clarifying_follow_up,
    classify_review_follow_up,
    normalize_review_payload,
)
from .state_utils import brief_from_state, clean_text

ProgressCallback = Callable[[str], None]

GRAPH_PROGRESS_MESSAGES: dict[str, str] = {
    "extract_brief": "기획 초안에서 콘셉트, 감정 목표, 코어 루프를 구조화했습니다.",
    "validate_required_fields": "리뷰에 필요한 핵심 정보가 충분한지 확인했습니다.",
    "build_clarifying_response": "리뷰 전에 확인할 보완 질문을 준비했습니다.",
    "prepare_reference_lookup": "언급된 레퍼런스 게임을 조회할 준비를 했습니다.",
    "reference_lookup_tool_node": "레퍼런스 게임의 공개 정보를 확인했습니다.",
    "merge_reference_lookup_results": "레퍼런스 조회 결과를 리뷰 컨텍스트에 합쳤습니다.",
    "mark_reference_lookup_skipped": "명시된 레퍼런스가 없어 비교 조회를 건너뛰었습니다.",
    "intent_alignment_review": "플레이어 의도와 감정 목표의 정렬을 진단했습니다.",
    "core_loop_review": "코어 루프와 반복 동기의 연결을 진단했습니다.",
    "scope_playtest_review": "MVP 범위와 플레이테스트 가설을 점검했습니다.",
    "merge_review_guidance": "세 가지 진단에서 나온 판단 기준을 정리했습니다.",
    "direction_compare": "선택 가능한 해석 방향 2개를 비교했습니다.",
    "build_learning_summary": "다음 기획에도 쓸 수 있는 학습 요약을 작성했습니다.",
    "build_review_response": "리뷰 리포트로 표시할 응답을 정리했습니다.",
}

GRAPH_NEXT_PROGRESS_MESSAGES: dict[str, str] = {
    "extract_brief": "필수 정보와 권장 입력의 누락 여부를 확인하고 있습니다.",
    "validate_required_fields": "리뷰 가능 여부에 따라 다음 단계를 고르고 있습니다.",
    "prepare_reference_lookup": "레퍼런스 게임의 공개 정보를 확인하고 있습니다.",
    "reference_lookup_tool_node": "레퍼런스 결과를 리뷰 컨텍스트에 합치고 있습니다.",
    "merge_reference_lookup_results": "의도, 코어 루프, MVP 범위를 나눠 진단하고 있습니다.",
    "mark_reference_lookup_skipped": "의도, 코어 루프, MVP 범위를 나눠 진단하고 있습니다.",
    "intent_alignment_review": "다른 진단 결과를 기다리며 리뷰 기준을 모으고 있습니다.",
    "core_loop_review": "다른 진단 결과를 기다리며 리뷰 기준을 모으고 있습니다.",
    "scope_playtest_review": "다른 진단 결과를 기다리며 리뷰 기준을 모으고 있습니다.",
    "merge_review_guidance": "서로 다른 선택 방향과 트레이드오프를 비교하고 있습니다.",
    "direction_compare": "리뷰 내용을 학습 요약으로 압축하고 있습니다.",
    "build_learning_summary": "화면에 표시할 리뷰 응답을 정리하고 있습니다.",
}


def _review_context_for_chat(result: ReviewResponse) -> dict:
    return {
        "mode": result.mode,
        "brief": result.brief.model_dump(),
        "reference_summary": [
            reference.model_dump() for reference in result.reference_summary
        ],
        "missing_fields": result.missing_fields,
        "soft_missing_fields": result.soft_missing_fields,
        "diagnosis": result.diagnosis.model_dump(),
        "directions": [direction.model_dump() for direction in result.directions],
        "scope": result.scope.model_dump(),
        "playtest_plan": result.playtest_plan.model_dump(),
        "learning": result.learning.model_dump(),
        "mentor_questions": [question.model_dump() for question in result.questions],
        "final_summary": result.final_summary,
    }


def _append_review_follow_up(raw_input: str, revision_note: str) -> str:
    lines = [
        raw_input.strip(),
        "",
        "Review follow-up corrections:",
        f"- {revision_note}",
    ]
    return "\n".join(line for line in lines if line).strip()


def _append_clarifying_chat_update(raw_input: str, answer_note: str) -> str:
    lines = [
        raw_input.strip(),
        "",
        "Clarifying chat updates:",
        f"- {answer_note}",
    ]
    return "\n".join(line for line in lines if line).strip()


def _build_response(state: MentorState) -> ReviewResponse:
    mode = state.get("mode", "clarifying")
    normalized_review = (
        normalize_review_payload(state)
        if mode == "reviewed"
        else {
            "intent_diagnosis": "",
            "intent_rationale": [],
            "core_loop_diagnosis": "",
            "core_loop_rationale": [],
            "scope_diagnosis": "",
            "scope_rationale": [],
            "playtest_rationale": [],
            "mentor_principles": [],
            "mentor_questions": [],
            "scope_recommendations": [],
            "playtest_hypothesis": "",
            "playtest_questions": [],
            "direction_options": [],
            "reflection_summary": "",
            "next_self_check_question": "",
            "final_summary": "",
        }
    )
    return ReviewResponse(
        mode=mode,
        brief=brief_from_state(state),
        reference_summary=state.get("reference_contexts", []),
        reference_citations=state.get("reference_citations", []),
        reference_lookup_status=state.get("reference_lookup_status", "skipped"),
        reference_lookup_notes=state.get("reference_lookup_notes", []),
        diagnosis=DiagnosisResult(
            intent=normalized_review["intent_diagnosis"],
            intent_rationale=normalized_review["intent_rationale"],
            core_loop=normalized_review["core_loop_diagnosis"],
            core_loop_rationale=normalized_review["core_loop_rationale"],
            scope=normalized_review["scope_diagnosis"],
            scope_rationale=normalized_review["scope_rationale"],
        ),
        directions=normalized_review["direction_options"],
        scope=ScopeResult(
            summary=normalized_review["scope_diagnosis"],
            rationale=normalized_review["scope_rationale"],
            recommendations=normalized_review["scope_recommendations"],
        ),
        playtest_plan=PlaytestPlan(
            hypothesis=normalized_review["playtest_hypothesis"],
            rationale=normalized_review["playtest_rationale"],
            questions=normalized_review["playtest_questions"],
            target_audience=state.get("test_audience", ""),
        ),
        learning=LearningResult(
            principles=normalized_review["mentor_principles"],
            reflection_summary=normalized_review["reflection_summary"],
            next_self_check_question=normalized_review["next_self_check_question"],
        ),
        questions=(
            state.get("clarifying_questions", [])
            if mode == "clarifying"
            else normalized_review["mentor_questions"]
        ),
        final_summary=normalized_review["final_summary"],
        missing_fields=state.get("missing_fields", []),
        soft_missing_fields=state.get("soft_missing_fields", []),
        raw_input=state.get("raw_input", ""),
    )


def _report_progress(progress_callback: ProgressCallback | None, message: str) -> None:
    if progress_callback is not None:
        progress_callback(message)


def invoke_graph(
    state: MentorState,
    progress_callback: ProgressCallback | None = None,
    output_callback: LLMOutputCallback | None = None,
) -> ReviewResponse:
    with llm_output_context(output_callback):
        if progress_callback is None:
            final_state = get_review_graph().invoke(state)
            return _build_response(final_state)

        final_state: MentorState = dict(state)
        _report_progress(
            progress_callback,
            "기획 초안에서 구조화된 브리프를 추출하고 있습니다.",
        )
        for chunk in get_review_graph().stream(state, stream_mode="updates"):
            for node_name, update in chunk.items():
                if isinstance(update, dict):
                    final_state.update(update)
                message = GRAPH_PROGRESS_MESSAGES.get(node_name)
                if message:
                    _report_progress(progress_callback, message)
                next_message = GRAPH_NEXT_PROGRESS_MESSAGES.get(node_name)
                if next_message:
                    _report_progress(progress_callback, next_message)
        return _build_response(final_state)


def run_brief_review(
    raw_input: str,
    progress_callback: ProgressCallback | None = None,
    output_callback: LLMOutputCallback | None = None,
) -> ReviewResponse:
    normalized_input = raw_input.strip()
    state: MentorState = {
        "raw_input": normalized_input,
        "messages": [HumanMessage(content=normalized_input)],
    }
    return invoke_graph(
        state,
        progress_callback=progress_callback,
        output_callback=output_callback,
    )


def answer_clarifying_chat(
    result: ReviewResponse,
    user_message: str,
    chat_history: list[ChatMessage],
    progress_callback: ProgressCallback | None = None,
    output_callback: LLMOutputCallback | None = None,
) -> tuple[str, ReviewResponse | None]:
    message = clean_text(user_message)
    if not message:
        raise ValueError("보완 질문에 대한 답변이나 질문을 입력해 주세요.")

    _report_progress(
        progress_callback,
        "보완 메시지가 질문인지, 리뷰를 계속할 수 있는 답변인지 분류하고 있습니다.",
    )
    with llm_output_context(output_callback):
        payload = classify_clarifying_follow_up(
            brief_context=result.brief.model_dump(),
            questions=result.questions,
            chat_history=chat_history,
            user_message=message,
        )
    if payload.action == "answer":
        _report_progress(progress_callback, "보완 질문에 대한 답변을 작성했습니다.")
        return payload.reply, None

    _report_progress(
        progress_callback,
        "확인된 보완 내용을 원문에 반영해 리뷰를 다시 시도합니다.",
    )
    refreshed = run_brief_review(
        _append_clarifying_chat_update(result.raw_input, payload.answer_note),
        progress_callback=progress_callback,
        output_callback=output_callback,
    )
    return payload.reply, refreshed


def answer_review_chat(
    result: ReviewResponse,
    user_message: str,
    chat_history: list[ChatMessage],
    progress_callback: ProgressCallback | None = None,
    output_callback: LLMOutputCallback | None = None,
) -> tuple[str, ReviewResponse | None]:
    message = clean_text(user_message)
    if not message:
        raise ValueError("후속 질문이나 정정 내용을 입력해 주세요.")

    _report_progress(
        progress_callback,
        "후속 메시지가 질문인지, 리뷰를 갱신해야 하는 정정인지 분류하고 있습니다.",
    )
    with llm_output_context(output_callback):
        payload = classify_review_follow_up(
            review_context=_review_context_for_chat(result),
            chat_history=chat_history,
            user_message=message,
        )
    if payload.action == "answer":
        _report_progress(progress_callback, "현재 리뷰 컨텍스트를 바탕으로 답변을 작성했습니다.")
        return payload.reply, None

    _report_progress(
        progress_callback,
        "정정 내용을 원문에 반영해 리뷰를 다시 생성합니다.",
    )
    refreshed = run_brief_review(
        _append_review_follow_up(result.raw_input, payload.revision_note),
        progress_callback=progress_callback,
        output_callback=output_callback,
    )
    return payload.reply, refreshed
