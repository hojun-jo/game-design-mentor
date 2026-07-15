from __future__ import annotations

from langchain_core.messages import HumanMessage

from .graph import get_review_graph
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


def invoke_graph(state: MentorState) -> ReviewResponse:
    final_state = get_review_graph().invoke(state)
    return _build_response(final_state)


def run_brief_review(raw_input: str) -> ReviewResponse:
    normalized_input = raw_input.strip()
    state: MentorState = {
        "raw_input": normalized_input,
        "messages": [HumanMessage(content=normalized_input)],
    }
    return invoke_graph(state)


def answer_clarifying_chat(
    result: ReviewResponse,
    user_message: str,
    chat_history: list[ChatMessage],
) -> tuple[str, ReviewResponse | None]:
    message = clean_text(user_message)
    if not message:
        raise ValueError("보완 질문에 대한 답변이나 질문을 입력해 주세요.")

    payload = classify_clarifying_follow_up(
        brief_context=result.brief.model_dump(),
        questions=result.questions,
        chat_history=chat_history,
        user_message=message,
    )
    if payload.action == "answer":
        return payload.reply, None

    refreshed = run_brief_review(
        _append_clarifying_chat_update(result.raw_input, payload.answer_note)
    )
    return payload.reply, refreshed


def answer_review_chat(
    result: ReviewResponse,
    user_message: str,
    chat_history: list[ChatMessage],
) -> tuple[str, ReviewResponse | None]:
    message = clean_text(user_message)
    if not message:
        raise ValueError("후속 질문이나 정정 내용을 입력해 주세요.")

    payload = classify_review_follow_up(
        review_context=_review_context_for_chat(result),
        chat_history=chat_history,
        user_message=message,
    )
    if payload.action == "answer":
        return payload.reply, None

    refreshed = run_brief_review(
        _append_review_follow_up(result.raw_input, payload.revision_note)
    )
    return payload.reply, refreshed
