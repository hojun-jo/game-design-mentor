from __future__ import annotations

from typing import Final

from .models import ClarifyingQuestion, MentorState, ValidationResult

HARD_REQUIRED_FIELDS: Final[tuple[str, ...]] = ("emotion_goal", "core_loop")
SOFT_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "target_player",
    "reward_structure",
    "mvp_goal",
    "feature_list",
)

QUESTION_TEXT: Final[dict[str, str]] = {
    "target_player": "지금 가장 먼저 잡고 싶은 핵심 플레이어는 누구인가요?",
    "emotion_goal": "플레이어에게 어떤 감정을 남기고 싶은지 한 문장으로 적어 주세요.",
    "core_loop": "플레이어가 반복해서 하게 될 행동 흐름을 순서대로 적어 주세요.",
    "reward_structure": "플레이어가 한 번 더 플레이하게 만드는 보상이나 기대는 무엇인가요?",
    "mvp_goal": "이번 MVP가 가장 먼저 검증하려는 가설은 무엇인가요?",
    "feature_list": "이번 MVP에 꼭 필요한 기능 3개 안팎만 적어 주세요.",
}


def is_missing(value: object) -> bool:
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return len(value) == 0
    return value in (None, 0)


def build_clarifying_questions(
    missing_fields: list[str],
    soft_missing_fields: list[str],
) -> list[ClarifyingQuestion]:
    questions: list[ClarifyingQuestion] = []

    if "target_player" in soft_missing_fields or "emotion_goal" in missing_fields:
        questions.append(
            ClarifyingQuestion(
                field="intent_alignment",
                priority="hard" if "emotion_goal" in missing_fields else "soft",
                question="어떤 플레이어에게 어떤 감정을 주고 싶나요?",
            )
        )

    for field in ("emotion_goal", "core_loop"):
        if field in missing_fields:
            questions.append(
                ClarifyingQuestion(
                    field=field,
                    priority="hard",
                    question=QUESTION_TEXT[field],
                )
            )

    for field in ("target_player", "reward_structure", "mvp_goal", "feature_list"):
        if field in soft_missing_fields:
            questions.append(
                ClarifyingQuestion(
                    field=field,
                    priority="soft",
                    question=QUESTION_TEXT[field],
                )
            )

    return questions


def validate_required_fields(state: MentorState) -> ValidationResult:
    missing_fields = [
        field for field in HARD_REQUIRED_FIELDS if is_missing(state.get(field, ""))
    ]
    soft_missing_fields = [
        field for field in SOFT_REQUIRED_FIELDS if is_missing(state.get(field, ""))
    ]
    return ValidationResult(
        missing_fields=missing_fields,
        soft_missing_fields=soft_missing_fields,
        clarifying_questions=build_clarifying_questions(
            missing_fields=missing_fields,
            soft_missing_fields=soft_missing_fields,
        ),
        review_ready=not missing_fields,
    )


def validate_required_fields_patch(state: MentorState) -> dict:
    return validate_required_fields(state).model_dump()
