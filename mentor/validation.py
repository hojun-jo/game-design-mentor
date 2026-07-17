from __future__ import annotations

from typing import Final

from .models import ClarifyingQuestion, MentorState, StructuredBrief, ValidationResult

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

QUESTION_LEARNING_GOAL: Final[dict[str, str]] = {
    "intent_alignment": "대상 플레이어와 감정 목표를 같은 기준으로 묶기",
    "target_player": "핵심 플레이어를 좁혀 뒤 리뷰의 기준 세우기",
    "emotion_goal": "기능 설명과 감정 목표를 구분하기",
    "core_loop": "반복 행동 흐름을 단계로 설명하기",
    "reward_structure": "플레이어가 반복하는 이유를 보상과 기대 관점에서 보기",
    "mvp_goal": "이번 MVP가 무엇을 증명해야 하는지 정하기",
    "feature_list": "핵심 검증에 필요한 기능과 주변 기능을 구분하기",
}

QUESTION_RATIONALE: Final[dict[str, str]] = {
    "intent_alignment": "대상과 감정이 정해져야 코어 루프와 범위 판단의 기준이 흔들리지 않습니다.",
    "target_player": "플레이어가 넓으면 좋은 기능과 빼야 할 기능을 구분하기 어렵습니다.",
    "emotion_goal": "감정 목표는 어떤 루프와 보상이 필요한지 판단하는 기준입니다.",
    "core_loop": "코어 루프가 보여야 기능 목록이 반복 재미를 돕는지 판단할 수 있습니다.",
    "reward_structure": "보상 구조가 있어야 플레이어가 왜 한 번 더 반복하는지 볼 수 있습니다.",
    "mvp_goal": "MVP 목표가 있어야 범위 축소가 단순 삭제가 아니라 검증 설계가 됩니다.",
    "feature_list": "기능을 3개 안팎으로 좁히면 무엇을 먼저 테스트할지 선명해집니다.",
}

GAME_DESIGN_KEYWORDS: Final[tuple[str, ...]] = (
    "게임",
    "game",
    "플레이",
    "플레이어",
    "player",
    "플레이테스트",
    "playtest",
    "코어 루프",
    "core loop",
    "루프",
    "메커닉",
    "mechanic",
    "장르",
    "genre",
    "레벨",
    "level",
    "스테이지",
    "stage",
    "전투",
    "combat",
    "퀘스트",
    "quest",
    "퍼즐",
    "puzzle",
    "보상",
    "reward",
    "밸런스",
    "balance",
    "난이도",
    "difficulty",
    "조작",
    "control",
    "캐릭터",
    "character",
    "적",
    "enemy",
    "보스",
    "boss",
    "인벤토리",
    "inventory",
    "로그라이크",
    "roguelike",
    "rpg",
    "전략",
    "strategy",
    "생존",
    "survival",
    "덱빌딩",
    "deckbuilding",
    "시뮬레이션",
    "simulation",
    "플랫포머",
    "platformer",
)

GAME_BRIEF_FIELDS: Final[tuple[str, ...]] = (
    "concept_statement",
    "target_player",
    "emotion_goal",
    "core_loop",
    "reward_structure",
    "mvp_goal",
    "test_audience",
    "constraints_note",
)


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
    covered_fields: set[str] = set()

    if "target_player" in soft_missing_fields and "emotion_goal" in missing_fields:
        questions.append(
            ClarifyingQuestion(
                field="intent_alignment",
                priority="hard",
                question="어떤 플레이어에게 어떤 감정을 주고 싶나요?",
                question_type="clarify",
                learning_goal=QUESTION_LEARNING_GOAL["intent_alignment"],
                rationale=QUESTION_RATIONALE["intent_alignment"],
                blocks_review=True,
            )
        )
        covered_fields.update({"target_player", "emotion_goal"})

    for field in ("emotion_goal", "core_loop"):
        if field in missing_fields and field not in covered_fields:
            questions.append(
                ClarifyingQuestion(
                    field=field,
                    priority="hard",
                    question=QUESTION_TEXT[field],
                    question_type="clarify",
                    learning_goal=QUESTION_LEARNING_GOAL[field],
                    rationale=QUESTION_RATIONALE[field],
                    blocks_review=True,
                )
            )

    for field in ("target_player", "reward_structure", "mvp_goal", "feature_list"):
        if field in soft_missing_fields and field not in covered_fields:
            questions.append(
                ClarifyingQuestion(
                    field=field,
                    priority="soft",
                    question=QUESTION_TEXT[field],
                    question_type="clarify",
                    learning_goal=QUESTION_LEARNING_GOAL[field],
                    rationale=QUESTION_RATIONALE[field],
                    blocks_review=False,
                )
            )

    return questions


def is_game_design_related(raw_input: str, brief: StructuredBrief) -> bool:
    text = " ".join(
        [
            raw_input,
            *(getattr(brief, field) for field in GAME_BRIEF_FIELDS),
            *brief.differentiation_points,
            *brief.feature_list,
            *brief.reference_titles,
        ]
    ).casefold()
    if any(keyword in text for keyword in GAME_DESIGN_KEYWORDS):
        return True

    extracted_design_fields = [
        brief.core_loop,
        brief.reward_structure,
        brief.mvp_goal,
        brief.test_audience,
        *brief.feature_list,
        *brief.differentiation_points,
        *brief.reference_titles,
    ]
    return bool(brief.concept_statement.strip()) and any(
        str(value).strip() for value in extracted_design_fields
    )


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
        review_ready=not missing_fields and not soft_missing_fields,
    )


def validate_required_fields_patch(state: MentorState) -> dict:
    return validate_required_fields(state).model_dump()
