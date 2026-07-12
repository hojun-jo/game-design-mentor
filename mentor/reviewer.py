from __future__ import annotations

import json

from .llm import get_reviewer_base_llm
from .models import (
    CoreLoopReviewPayload,
    DirectionComparePayload,
    DirectionOption,
    IntentReviewPayload,
    MentorState,
    ScopePlaytestPayload,
)
from .state_utils import clean_text, normalize_string_list, serialize_brief_for_prompt


def _jsonable_list(items: list) -> list:
    serialized: list = []
    for item in items:
        if hasattr(item, "model_dump"):
            serialized.append(item.model_dump())
        else:
            serialized.append(item)
    return serialized


def normalize_directions(
    directions: list[DirectionOption | dict],
) -> list[DirectionOption]:
    normalized: list[DirectionOption] = []
    for direction in directions[:2]:
        if isinstance(direction, dict):
            direction = DirectionOption.model_validate(direction)
        title = clean_text(direction.title)
        reason = clean_text(direction.reason)
        tradeoff = clean_text(direction.tradeoff)
        if title and reason and tradeoff:
            normalized.append(
                DirectionOption(title=title, reason=reason, tradeoff=tradeoff)
            )

    fallbacks = [
        DirectionOption(
            title="루프 단순화에 집중",
            reason="핵심 반복 흐름을 먼저 선명하게 만들면 초반 테스트에서 재미의 유무를 더 빨리 확인할 수 있습니다.",
            tradeoff="세계관이나 부가 기능의 매력은 초기 빌드에서 덜 드러날 수 있습니다.",
        ),
        DirectionOption(
            title="차별화 포인트를 먼저 드러내기",
            reason="레퍼런스와 다른 경험 지점을 앞세우면 플레이어 반응의 이유를 더 분명하게 관찰할 수 있습니다.",
            tradeoff="핵심 루프가 아직 약하면 차별화가 오히려 복잡도로 느껴질 수 있습니다.",
        ),
    ]

    while len(normalized) < 2:
        normalized.append(fallbacks[len(normalized)])

    return normalized[:2]


def normalize_playtest_questions(
    questions: list[str],
    state: MentorState,
) -> list[str]:
    normalized = normalize_string_list(questions)
    if len(normalized) >= 2:
        return normalized[:3]

    fallbacks = [
        f"플레이어가 첫 10분 안에 `{state.get('core_loop', '핵심 루프')}`를 스스로 이해하고 반복하려고 하나요?",
        f"플레이어가 `{state.get('emotion_goal', '의도한 감정')}`에 가까운 반응을 실제 플레이 중 보이나요?",
    ]
    for question in fallbacks:
        if question not in normalized:
            normalized.append(question)
        if len(normalized) >= 2:
            break
    return normalized[:3]


def _get_structured_reviewer(schema):
    return get_reviewer_base_llm().with_structured_output(schema)


def generate_intent_alignment_review(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write the review in Korean and keep it concise.

Focus only on intent alignment.

Rules:
- Diagnose how `concept_statement`, `target_player`, `emotion_goal`, and `reference_titles` align or conflict.
- Use `reference_contexts` when available to compare the user's stated reference against the public positioning of that game.
- Use observation before prescription.
- Do not praise vaguely.
- Respect the intended genre and emotion instead of forcing a generic standard.
- If `target_player` is missing, acknowledge that uncertainty directly.
- If `reference_lookup_status` is not `ok`, mention briefly that reference comparison was limited.
- `intent_diagnosis` should be a short paragraph of 2-3 sentences.

Reference lookup:
{json.dumps(
    {
        "reference_lookup_status": state.get("reference_lookup_status", "skipped"),
        "reference_lookup_notes": state.get("reference_lookup_notes", []),
        "reference_contexts": _jsonable_list(state.get("reference_contexts", [])),
    },
    ensure_ascii=False,
    indent=2,
)}

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _get_structured_reviewer(IntentReviewPayload).invoke(prompt)
    return {"intent_diagnosis": clean_text(review.intent_diagnosis)}


def generate_core_loop_review(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write the review in Korean and keep it concise.

Focus only on the core loop and differentiation.

Rules:
- Diagnose the repeatable loop, reward structure, and differentiation points.
- If `reference_contexts` exist, compare the current loop against the reference loop summaries only as a comparison baseline, not a target to copy.
- Separate loop quality from feature listing.
- Use observation before prescription.
- If `reward_structure` is missing, acknowledge that uncertainty directly.
 - `core_loop_diagnosis` should be a short paragraph of 2-3 sentences.

Reference lookup:
{json.dumps(_jsonable_list(state.get("reference_contexts", [])), ensure_ascii=False, indent=2)}

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _get_structured_reviewer(CoreLoopReviewPayload).invoke(prompt)
    return {"core_loop_diagnosis": clean_text(review.core_loop_diagnosis)}


def generate_scope_playtest_review(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write the review in Korean and keep it concise.

Focus only on MVP scope and playtest planning.

Rules:
- Diagnose current scope realism using `feature_list`, `development_window_weeks`, `team_composition`, `mvp_goal`, `test_audience`, and `constraints_note`.
- If scope inputs are missing, make conservative assumptions and say so directly.
- If reference lookup failed, you may mention that reference-based calibration was limited, but continue the review.
- `scope_diagnosis` should be a short paragraph of 2-3 sentences.
- `scope_recommendations` should be concrete cut-or-delay suggestions.
- `playtest_hypothesis` should be a single concrete hypothesis.
- `playtest_questions` should be observable player-behavior questions.

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _get_structured_reviewer(ScopePlaytestPayload).invoke(prompt)
    return {
        "scope_diagnosis": clean_text(review.scope_diagnosis),
        "scope_recommendations": normalize_string_list(review.scope_recommendations),
        "playtest_hypothesis": clean_text(review.playtest_hypothesis),
        "playtest_questions": normalize_playtest_questions(review.playtest_questions, state),
    }


def generate_direction_compare(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write the review in Korean and keep it concise.

Focus only on decision framing.

Rules:
- Use the existing diagnoses and playtest hypothesis to propose exactly 2 direction options.
- Each direction option needs a short title, one-sentence reason, and one-sentence tradeoff.
- Make the two directions meaningfully different.
- `final_summary` must be one sentence about what to decide first.

Diagnoses:
{json.dumps(
    {
        "intent_diagnosis": state.get("intent_diagnosis", ""),
        "core_loop_diagnosis": state.get("core_loop_diagnosis", ""),
        "scope_diagnosis": state.get("scope_diagnosis", ""),
        "scope_recommendations": state.get("scope_recommendations", []),
        "playtest_hypothesis": state.get("playtest_hypothesis", ""),
        "reference_contexts": _jsonable_list(state.get("reference_contexts", [])),
        "reference_lookup_status": state.get("reference_lookup_status", "skipped"),
    },
    ensure_ascii=False,
    indent=2,
)}

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _get_structured_reviewer(DirectionComparePayload).invoke(prompt)
    return {
        "direction_options": normalize_directions(review.direction_options),
        "final_summary": clean_text(review.final_summary),
    }


def normalize_review_payload(state: MentorState) -> dict:
    return {
        "intent_diagnosis": clean_text(state.get("intent_diagnosis", "")),
        "core_loop_diagnosis": clean_text(state.get("core_loop_diagnosis", "")),
        "scope_diagnosis": clean_text(state.get("scope_diagnosis", "")),
        "scope_recommendations": normalize_string_list(
            state.get("scope_recommendations", [])
        ),
        "playtest_hypothesis": clean_text(state.get("playtest_hypothesis", "")),
        "playtest_questions": normalize_playtest_questions(
            state.get("playtest_questions", []),
            state,
        ),
        "direction_options": normalize_directions(state.get("direction_options", [])),
        "final_summary": clean_text(state.get("final_summary", "")),
    }
