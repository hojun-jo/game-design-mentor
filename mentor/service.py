from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from .graph import get_review_graph, route_after_validation
from .models import (
    ClarifyingQuestion,
    DiagnosisResult,
    MentorState,
    PlaytestPlan,
    ReviewResponse,
    ScopeResult,
)
from .reference_tools import merge_reference_lookup_results
from .reviewer import normalize_directions, normalize_playtest_questions, normalize_review_payload
from .state_utils import brief_from_state, clean_text
from .validation import build_clarifying_questions, validate_required_fields


def _merge_clarifying_answers(
    raw_input: str,
    questions: list[ClarifyingQuestion],
    answers: dict[str, str],
) -> str:
    lines = [raw_input.strip(), "", "Additional clarifications:"]
    for question in questions:
        answer = clean_text(answers.get(question.field, ""))
        if answer:
            lines.append(f"- {question.question} {answer}")
    return "\n".join(line for line in lines if line).strip()


def _build_response(state: MentorState) -> ReviewResponse:
    mode = state.get("mode", "clarifying")
    normalized_review = (
        normalize_review_payload(state)
        if mode == "reviewed"
        else {
            "intent_diagnosis": "",
            "core_loop_diagnosis": "",
            "scope_diagnosis": "",
            "scope_recommendations": [],
            "playtest_hypothesis": "",
            "playtest_questions": [],
            "direction_options": [],
            "final_summary": "",
        }
    )
    return ReviewResponse(
        mode=mode,
        questions=state.get("clarifying_questions", []),
        brief=brief_from_state(state),
        reference_summary=state.get("reference_contexts", []),
        reference_citations=state.get("reference_citations", []),
        reference_lookup_status=state.get("reference_lookup_status", "skipped"),
        reference_lookup_notes=state.get("reference_lookup_notes", []),
        diagnosis=DiagnosisResult(
            intent=normalized_review["intent_diagnosis"],
            core_loop=normalized_review["core_loop_diagnosis"],
            scope=normalized_review["scope_diagnosis"],
        ),
        directions=normalized_review["direction_options"],
        scope=ScopeResult(
            summary=normalized_review["scope_diagnosis"],
            recommendations=normalized_review["scope_recommendations"],
        ),
        playtest_plan=PlaytestPlan(
            hypothesis=normalized_review["playtest_hypothesis"],
            questions=normalized_review["playtest_questions"],
            target_audience=state.get("test_audience", ""),
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


def continue_brief_review(
    raw_input: str,
    questions: list[ClarifyingQuestion],
    answers: dict[str, str],
) -> ReviewResponse:
    merged_input = _merge_clarifying_answers(raw_input, questions, answers)
    state: MentorState = {
        "raw_input": merged_input,
        "messages": [
            HumanMessage(content=raw_input.strip()),
            AIMessage(content="\n".join(question.question for question in questions)),
            HumanMessage(
                content="\n".join(
                    f"{question.field}: {clean_text(answers.get(question.field, ''))}"
                    for question in questions
                    if clean_text(answers.get(question.field, ""))
                )
            ),
        ],
    }
    return invoke_graph(state)


def _self_check() -> None:
    questions = build_clarifying_questions(
        missing_fields=["emotion_goal", "core_loop"],
        soft_missing_fields=["target_player", "reward_structure"],
    )
    assert questions[0].question == "어떤 플레이어에게 어떤 감정을 주고 싶나요?"
    assert questions[1].field == "emotion_goal"
    assert questions[2].field == "core_loop"

    validation = validate_required_fields(
        {
            "concept_statement": "짧은 세션 설산 생존 전략 게임",
            "target_player": "",
            "emotion_goal": "",
            "core_loop": "",
            "reward_structure": "",
            "feature_list": [],
            "mvp_goal": "",
        }
    )
    assert validation.review_ready is False
    assert validation.missing_fields == ["emotion_goal", "core_loop"]
    assert "target_player" in validation.soft_missing_fields

    assert route_after_validation({"review_ready": False}) == "build_clarifying_response"
    assert (
        route_after_validation({"review_ready": True, "reference_titles": ["Hades"]})
        == "reference_lookup_tool_node"
    )
    assert (
        route_after_validation({"review_ready": True, "reference_titles": []})
        == "mark_reference_lookup_skipped"
    )
    assert get_review_graph() is not None

    merged_input = _merge_clarifying_answers(
        raw_input="짧은 세션 설산 생존 전략 게임",
        questions=[
            ClarifyingQuestion(
                field="intent_alignment",
                priority="hard",
                question="어떤 플레이어에게 어떤 감정을 주고 싶나요?",
            ),
            ClarifyingQuestion(
                field="core_loop",
                priority="hard",
                question="플레이어가 반복해서 하게 될 행동 흐름을 순서대로 적어 주세요.",
            ),
        ],
        answers={
            "intent_alignment": "전략 판단을 좋아하는 플레이어에게 불안하지만 한 턴 더 가고 싶은 긴장감을 주고 싶다.",
            "core_loop": "정찰 -> 자원 선택 -> 날씨 리스크 버티기 -> 거점 복귀",
        },
    )
    assert "Additional clarifications:" in merged_input
    assert "정찰 -> 자원 선택 -> 날씨 리스크 버티기 -> 거점 복귀" in merged_input

    merged_reference = merge_reference_lookup_results(
        {
            "messages": [
                ToolMessage(
                    content=(
                        '{"title":"Hades","status":"ok","context":{"title":"Hades","matched_name":"Hades",'
                        '"genre_tags":["로그라이크","액션"],"core_loop_summary":"전투와 성장 반복",'
                        '"notable_positioning":"빠른 전투 로그라이크","source_notes":["OpenAI web search"],'
                        '"confidence":"high"},"note":"","citations":[{"reference_title":"Hades",'
                        '"url":"https://store.steampowered.com/app/1145360/Hades/","title":"Hades on Steam",'
                        '"snippet":"Battle out of hell"}]}'
                    ),
                    tool_call_id="reference-lookup-0",
                    name="lookup_reference_game",
                )
            ]
        }
    )
    assert merged_reference["reference_lookup_status"] == "ok"
    assert len(merged_reference["reference_contexts"]) == 1
    assert len(merged_reference["reference_citations"]) == 1

    directions = normalize_directions([])
    assert len(directions) == 2

    playtest_questions = normalize_playtest_questions(
        [],
        {"core_loop": "탐험", "emotion_goal": "긴장감"},
    )
    assert len(playtest_questions) >= 2


if __name__ == "__main__":
    _self_check()
