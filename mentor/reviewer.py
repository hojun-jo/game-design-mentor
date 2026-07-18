from __future__ import annotations

import json

from .llm_stream import get_stream_config, report_structured_output
from .llm import get_reviewer_base_llm
from .models import (
    ChatMessage,
    ClarifyingChatPayload,
    ClarifyingQuestion,
    CoreLoopReviewPayload,
    DirectionComparePayload,
    DirectionOption,
    EngineOption,
    EngineRecommendation,
    EngineRecommendationPayload,
    IntentReviewPayload,
    LearningSummaryPayload,
    MentorState,
    ReviewChatPayload,
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


def normalize_engine_recommendation(
    recommendation: EngineRecommendation | dict | None,
) -> EngineRecommendation:
    if isinstance(recommendation, dict):
        recommendation = EngineRecommendation.model_validate(recommendation)
    if recommendation is None:
        recommendation = EngineRecommendation()

    def normalize_option(option: EngineOption | dict | None) -> EngineOption | None:
        if isinstance(option, dict):
            option = EngineOption.model_validate(option)
        if option is None:
            return None
        name = clean_text(option.name)
        reason = clean_text(option.reason)
        tradeoff = clean_text(option.tradeoff)
        if not name or not reason or not tradeoff:
            return None
        return EngineOption(
            name=name,
            fit=option.fit,
            reason=reason,
            tradeoff=tradeoff,
        )

    primary = normalize_option(recommendation.primary)
    alternatives: list[EngineOption] = []
    for option in recommendation.alternatives:
        normalized = normalize_option(option)
        if normalized is None:
            continue
        if primary is not None and normalized.name == primary.name:
            continue
        if any(existing.name == normalized.name for existing in alternatives):
            continue
        alternatives.append(normalized)
        if len(alternatives) == 2:
            break

    status = recommendation.status if primary is not None else "insufficient"
    questions = normalize_string_list(recommendation.follow_up_questions)[:3]
    if status == "insufficient" and not questions:
        questions = [
            "우선 출시할 플랫폼(PC, 모바일, 웹, 콘솔)은 무엇인가요?",
            "2D/3D 표현 수준과 온라인 멀티플레이 필요 여부는 어떻게 되나요?",
        ]
    return EngineRecommendation(
        status=status,
        primary=primary,
        alternatives=alternatives,
        rationale=normalize_string_list(recommendation.rationale)[:3],
        assumptions=normalize_string_list(recommendation.assumptions)[:3],
        follow_up_questions=questions,
    )


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


def normalize_mentor_principles(values: list[str]) -> list[str]:
    return normalize_string_list(values)[:3]


def fallback_rationale(section: str) -> list[str]:
    fallbacks = {
        "intent": [
            "대상 플레이어, 감정 목표, 콘셉트가 같은 플레이 경험을 가리키는지 기준으로 판단했습니다.",
            "입력된 브리프에서 비어 있거나 넓게 표현된 항목은 진단의 불확실성으로 반영했습니다.",
        ],
        "core_loop": [
            "반복 행동, 피드백, 보상, 다음 선택이 서로 이어지는지 기준으로 판단했습니다.",
            "기능 목록이 코어 루프를 강화하는지, 아니면 주변 기능으로 흩어지는지 함께 보았습니다.",
        ],
        "scope": [
            "핵심 루프 검증에 직접 필요한 기능인지 기준으로 범위 우선순위를 판단했습니다.",
            "개발 기간, 팀 구성, MVP 목표가 비어 있으면 보수적인 1인 MVP 가정으로 판단했습니다.",
        ],
        "playtest": [
            "플레이어의 말보다 관찰 가능한 선택과 행동으로 검증할 수 있는지 기준으로 판단했습니다.",
            "플레이테스트 질문이 MVP 가설과 직접 연결되는지 확인했습니다.",
        ],
    }
    return fallbacks[section]


def normalize_rationale(value: str | list[str], section: str) -> list[str]:
    if isinstance(value, str):
        normalized = normalize_string_list([value])
    else:
        normalized = normalize_string_list(value)
    if len(normalized) >= 2:
        return normalized[:3]
    for fallback in fallback_rationale(section):
        if fallback not in normalized:
            normalized.append(fallback)
        if len(normalized) >= 2:
            break
    return normalized[:3]


def normalize_mentor_questions(
    questions: list[ClarifyingQuestion | dict],
) -> list[ClarifyingQuestion]:
    normalized: list[ClarifyingQuestion] = []
    for question in questions:
        if isinstance(question, dict):
            question = ClarifyingQuestion.model_validate(question)
        text = clean_text(question.question)
        if not text:
            continue
        normalized.append(
            ClarifyingQuestion(
                field=clean_text(question.field) or "reflection",
                priority=question.priority,
                question=text,
                question_type=question.question_type,
                learning_goal=clean_text(question.learning_goal),
                rationale=clean_text(question.rationale),
                blocks_review=question.blocks_review,
            )
        )
        if len(normalized) >= 3:
            break
    return normalized


def merge_mentor_principles(
    state: MentorState,
    new_principles: list[str],
) -> list[str]:
    return normalize_mentor_principles(
        [*state.get("mentor_principles", []), *new_principles]
    )


def merge_mentor_questions(
    state: MentorState,
    new_questions: list[ClarifyingQuestion | dict],
) -> list[ClarifyingQuestion]:
    return normalize_mentor_questions(
        [*state.get("mentor_questions", []), *new_questions]
    )


def merge_review_guidance(state: MentorState) -> dict:
    return {
        "mentor_principles": normalize_mentor_principles(
            [
                *state.get("intent_mentor_principles", []),
                *state.get("core_loop_mentor_principles", []),
                *state.get("scope_mentor_principles", []),
            ]
        ),
        "mentor_questions": normalize_mentor_questions(
            [
                *state.get("intent_mentor_questions", []),
                *state.get("core_loop_mentor_questions", []),
                *state.get("scope_mentor_questions", []),
            ]
        ),
    }


def _get_structured_reviewer(schema):
    return get_reviewer_base_llm().with_structured_output(schema)


def _invoke_structured_reviewer(schema, prompt: str, title: str):
    reviewer = _get_structured_reviewer(schema)
    config = get_stream_config(title)
    if config is None:
        payload = reviewer.invoke(prompt)
    else:
        payload = reviewer.invoke(prompt, config=config)
    report_structured_output(title, payload)
    return payload


def generate_intent_alignment_review(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write the review in Korean and keep it concise.

Focus only on intent alignment.

Rules:
- Diagnose how `concept_statement`, `target_player`, `emotion_goal`, and `reference_titles` align or conflict.
- Use `reference_contexts` when available as public comparison baselines. Contexts with `origin="user"` were supplied by the user; contexts with `origin="recommended"` were automatically discovered and must be described as suggestions, not as the user's stated intent.
- Use observation before prescription.
- Do not praise vaguely.
- Respect the intended genre and emotion instead of forcing a generic standard.
- If `target_player` is missing, acknowledge that uncertainty directly.
- If `reference_lookup_status` is not `ok`, mention briefly that reference comparison was limited.
- `intent_diagnosis` should be a short paragraph of 2-3 sentences.
- `intent_rationale` must contain 2-3 concrete evidence bullets. Each bullet must point to a specific input, missing input, contradiction, or reference comparison used for the diagnosis.
- Return 1 mentor principle explaining the design criterion used for intent alignment.
- Return 1 non-blocking reflect question that helps the user check target/emotion alignment next time.
- That question must use priority="soft", question_type="reflect", and blocks_review=false.

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

    review = _invoke_structured_reviewer(
        IntentReviewPayload,
        prompt,
        "의도 정렬 리뷰 생성 중",
    )
    return {
        "intent_diagnosis": clean_text(review.intent_diagnosis),
        "intent_rationale": normalize_rationale(review.intent_rationale, "intent"),
        "intent_mentor_principles": normalize_mentor_principles(
            review.mentor_principles
        ),
        "intent_mentor_questions": normalize_mentor_questions(review.mentor_questions),
    }


def generate_core_loop_review(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write the review in Korean and keep it concise.

Focus only on the core loop and differentiation.

Rules:
- Diagnose the repeatable loop, reward structure, and differentiation points.
- If `reference_contexts` exist, compare the current loop against the reference loop summaries only as a comparison baseline, not a target to copy. Treat automatically discovered contexts (`origin="recommended"`) as suggestions rather than assumed user intent.
- Separate loop quality from feature listing.
- Use observation before prescription.
- If `reward_structure` is missing, acknowledge that uncertainty directly.
- `core_loop_diagnosis` should be a short paragraph of 2-3 sentences.
- `core_loop_rationale` must contain 2-3 concrete evidence bullets. Each bullet must point to a specific loop step, reward cue, feature, missing input, or reference comparison used for the diagnosis.
- Return 1 mentor principle explaining how to judge loop/reward causality.
- Return 1 non-blocking reflect question about the player's repeated choice.
- That question must use priority="soft", question_type="reflect", and blocks_review=false.

Reference lookup:
{json.dumps(_jsonable_list(state.get("reference_contexts", [])), ensure_ascii=False, indent=2)}

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _invoke_structured_reviewer(
        CoreLoopReviewPayload,
        prompt,
        "코어 루프 리뷰 생성 중",
    )
    return {
        "core_loop_diagnosis": clean_text(review.core_loop_diagnosis),
        "core_loop_rationale": normalize_rationale(
            review.core_loop_rationale,
            "core_loop",
        ),
        "core_loop_mentor_principles": normalize_mentor_principles(
            review.mentor_principles
        ),
        "core_loop_mentor_questions": normalize_mentor_questions(
            review.mentor_questions
        ),
    }


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
- `scope_rationale` must contain 2-3 concrete evidence bullets. Each bullet must point to specific scope inputs, feature list items, missing constraints, or MVP goal evidence.
- `scope_recommendations` should be concrete cut-or-delay suggestions.
- `playtest_hypothesis` should be a single concrete hypothesis.
- `playtest_questions` should be observable player-behavior questions.
- `playtest_rationale` must contain 2-3 concrete evidence bullets explaining why the hypothesis and questions fit the brief.
- Return 1 mentor principle explaining scope as a learning hypothesis.
- Return 1 non-blocking reflect question about what the MVP must teach first.
- That question must use priority="soft", question_type="reflect", and blocks_review=false.

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _invoke_structured_reviewer(
        ScopePlaytestPayload,
        prompt,
        "MVP 범위와 플레이테스트 리뷰 생성 중",
    )
    return {
        "scope_diagnosis": clean_text(review.scope_diagnosis),
        "scope_rationale": normalize_rationale(review.scope_rationale, "scope"),
        "playtest_rationale": normalize_rationale(
            review.playtest_rationale,
            "playtest",
        ),
        "scope_mentor_principles": normalize_mentor_principles(
            review.mentor_principles
        ),
        "scope_mentor_questions": normalize_mentor_questions(review.mentor_questions),
        "scope_recommendations": normalize_string_list(review.scope_recommendations),
        "playtest_hypothesis": clean_text(review.playtest_hypothesis),
        "playtest_questions": normalize_playtest_questions(review.playtest_questions, state),
    }


def generate_engine_recommendation_review(state: MentorState) -> dict:
    prompt = f"""
You are a practical game technology advisor for beginner indie developers.
Write the recommendation in Korean and keep it concise.

Recommend a game engine only from explicitly stated project facts. The recommendation is
an aid for a prototype decision, not a permanent technical guarantee.

Rules:
- Compare a primary engine with at most 2 alternatives. Candidates may include Unity,
  Unreal Engine, Godot, or another clearly justified engine.
- Use platform, visual requirements, networking scope, team engine experience, MVP scope,
  development window, and constraints as evidence when they are present.
- Do not infer missing technical requirements from the genre.
- Never state current licensing, pricing, platform support, or policy terms as fact.
  Put any uncertainty in `assumptions` and ask the user to confirm official terms before
  committing to an engine.
- Set status="recommended" only when platform and at least two other engine-relevant facts
  are explicit. Set status="conditional" when a likely option exists but important facts are
  missing. Set status="insufficient" when no responsible primary recommendation is possible.
- For status="insufficient", set primary to null and return 1-3 concrete follow_up_questions.
- Every engine option requires a name, fit (높음/중간/낮음), one-sentence reason, and
  one-sentence tradeoff.
- rationale must contain 2-3 bullets tied to explicit brief fields or missing fields.
- assumptions must list only facts that need confirmation; do not disguise assumptions as facts.

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    recommendation = _invoke_structured_reviewer(
        EngineRecommendationPayload,
        prompt,
        "게임 엔진 추천 생성 중",
    )
    return {
        "engine_recommendation": normalize_engine_recommendation(recommendation),
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
- Use `mentor_principles` as the decision criteria.
- `final_summary` must be one sentence about what to decide first.

Diagnoses:
{json.dumps(
    {
        "intent_diagnosis": state.get("intent_diagnosis", ""),
        "core_loop_diagnosis": state.get("core_loop_diagnosis", ""),
        "scope_diagnosis": state.get("scope_diagnosis", ""),
        "scope_recommendations": state.get("scope_recommendations", []),
        "playtest_hypothesis": state.get("playtest_hypothesis", ""),
        "mentor_principles": state.get("mentor_principles", []),
        "reference_contexts": _jsonable_list(state.get("reference_contexts", [])),
        "reference_lookup_status": state.get("reference_lookup_status", "skipped"),
    },
    ensure_ascii=False,
    indent=2,
)}

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    review = _invoke_structured_reviewer(
        DirectionComparePayload,
        prompt,
        "해석 방향 비교 생성 중",
    )
    return {
        "direction_options": normalize_directions(review.direction_options),
        "final_summary": clean_text(review.final_summary),
    }


def build_learning_summary(state: MentorState) -> dict:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write in Korean and keep it concise.

Focus only on learning transfer.

Rules:
- `reflection_summary` should say what became clearer through this review in 1-2 sentences.
- `next_self_check_question` should be one reusable question the user can ask on their next game brief.
- `final_summary` should be one sentence about what to decide first.
- Do not introduce new product recommendations.

Review context:
{json.dumps(
    {
        "intent_diagnosis": state.get("intent_diagnosis", ""),
        "intent_rationale": state.get("intent_rationale", ""),
        "core_loop_diagnosis": state.get("core_loop_diagnosis", ""),
        "core_loop_rationale": state.get("core_loop_rationale", ""),
        "scope_diagnosis": state.get("scope_diagnosis", ""),
        "scope_rationale": state.get("scope_rationale", ""),
        "mentor_principles": state.get("mentor_principles", []),
        "mentor_questions": _jsonable_list(state.get("mentor_questions", [])),
        "direction_options": _jsonable_list(state.get("direction_options", [])),
        "final_summary": state.get("final_summary", ""),
    },
    ensure_ascii=False,
    indent=2,
)}

Structured brief:
{serialize_brief_for_prompt(state)}
""".strip()

    summary = _invoke_structured_reviewer(
        LearningSummaryPayload,
        prompt,
        "학습 요약 생성 중",
    )
    return {
        "reflection_summary": clean_text(summary.reflection_summary),
        "next_self_check_question": clean_text(summary.next_self_check_question),
        "final_summary": clean_text(summary.final_summary)
        or clean_text(state.get("final_summary", "")),
    }


def classify_review_follow_up(
    review_context: dict,
    chat_history: list[ChatMessage],
    user_message: str,
) -> ReviewChatPayload:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write in Korean and keep it concise.

The user is chatting after receiving a game design review.
Classify the latest user message and produce the next assistant response.

Rules:
- Use action="revise" only when the user corrects the brief, corrects your interpretation, adds missing design intent, or says the review misunderstood their game.
- Use action="answer" when the user asks why the review said something, asks for examples, asks how to apply feedback, or asks a follow-up question without changing the brief.
- If action="revise", `revision_note` must be a concise factual note that can be appended to the original brief before regenerating the review.
- If action="revise", `reply` should briefly say the correction will be reflected and the review refreshed.
- If action="answer", `reply` should answer from the current review context and mention uncertainty when the needed detail is absent.
- Do not invent new game details.
- Do not apologize unless there is a concrete mistake.

Current review context:
{json.dumps(review_context, ensure_ascii=False, indent=2)}

Conversation history including intake, clarification, and review follow-up:
{json.dumps(_jsonable_list(chat_history), ensure_ascii=False, indent=2)}

Latest user message:
{user_message}
""".strip()

    payload = _invoke_structured_reviewer(
        ReviewChatPayload,
        prompt,
        "후속 답변 생성 중",
    )
    action = payload.action if payload.action in {"answer", "revise"} else "answer"
    reply = clean_text(payload.reply)
    revision_note = clean_text(payload.revision_note)
    if action == "revise" and not revision_note:
        revision_note = clean_text(user_message)
    if not reply:
        if action == "revise":
            reply = "정정 내용을 반영해 리뷰를 다시 갱신하겠습니다."
        else:
            reply = "현재 리뷰 근거만으로는 확정하기 어렵습니다. 어떤 부분을 더 보고 싶은지 알려 주세요."
    return ReviewChatPayload(
        action=action,
        reply=reply,
        revision_note=revision_note,
    )


def classify_clarifying_follow_up(
    brief_context: dict,
    questions: list[ClarifyingQuestion],
    chat_history: list[ChatMessage],
    user_message: str,
) -> ClarifyingChatPayload:
    prompt = f"""
You are a rigorous but practical game design mentor for beginner indie developers.
Write in Korean and keep it concise.

The user is answering or asking about pre-review clarification questions.
Classify the latest user message and produce the next assistant response.

Rules:
- Use action="continue_review" only when the user provides or confirms concrete brief information that can answer at least one pending clarification question.
- Use action="answer" when the user asks what a question means, asks why it matters, asks for examples, asks for recommendations, or explores options without making a concrete choice.
- If the user asks for a recommendation, give 2-3 options with tradeoffs, but do not treat those options as confirmed brief facts.
- If action="continue_review", `answer_note` must contain only concise factual user-confirmed brief details. Do not include your recommendations unless the user explicitly chose them.
- If action="continue_review", `reply` should briefly say the answer will be reflected and the review retried.
- If action="answer", `reply` should help the user answer the pending questions and may include concrete examples or recommendations.
- Never invent confirmed facts about the user's game.

Current structured brief:
{json.dumps(brief_context, ensure_ascii=False, indent=2)}

Pending clarification questions:
{json.dumps(_jsonable_list(questions), ensure_ascii=False, indent=2)}

Clarifying chat so far:
{json.dumps(_jsonable_list(chat_history), ensure_ascii=False, indent=2)}

Latest user message:
{user_message}
""".strip()

    payload = _invoke_structured_reviewer(
        ClarifyingChatPayload,
        prompt,
        "보완 대화 답변 생성 중",
    )
    action = (
        payload.action
        if payload.action in {"answer", "continue_review"}
        else "answer"
    )
    reply = clean_text(payload.reply)
    answer_note = clean_text(payload.answer_note)
    if action == "continue_review" and not answer_note:
        answer_note = clean_text(user_message)
    if not reply:
        if action == "continue_review":
            reply = "답변을 반영해 다시 구조화하고 리뷰 가능 여부를 확인하겠습니다."
        else:
            reply = "현재 보완 질문 중 어떤 항목이 막히는지 알려 주세요. 예시나 추천 방향을 제안할 수 있습니다."
    return ClarifyingChatPayload(
        action=action,
        reply=reply,
        answer_note=answer_note,
    )


def normalize_review_payload(state: MentorState) -> dict:
    return {
        "intent_diagnosis": clean_text(state.get("intent_diagnosis", "")),
        "intent_rationale": normalize_rationale(
            state.get("intent_rationale", ""),
            "intent",
        ),
        "core_loop_diagnosis": clean_text(state.get("core_loop_diagnosis", "")),
        "core_loop_rationale": normalize_rationale(
            state.get("core_loop_rationale", ""),
            "core_loop",
        ),
        "scope_diagnosis": clean_text(state.get("scope_diagnosis", "")),
        "scope_rationale": normalize_rationale(
            state.get("scope_rationale", ""),
            "scope",
        ),
        "playtest_rationale": normalize_rationale(
            state.get("playtest_rationale", ""),
            "playtest",
        ),
        "mentor_principles": normalize_mentor_principles(
            state.get("mentor_principles", [])
        ),
        "mentor_questions": normalize_mentor_questions(
            state.get("mentor_questions", [])
        ),
        "scope_recommendations": normalize_string_list(
            state.get("scope_recommendations", [])
        ),
        "engine_recommendation": normalize_engine_recommendation(
            state.get("engine_recommendation")
        ),
        "playtest_hypothesis": clean_text(state.get("playtest_hypothesis", "")),
        "playtest_questions": normalize_playtest_questions(
            state.get("playtest_questions", []),
            state,
        ),
        "direction_options": normalize_directions(state.get("direction_options", [])),
        "reflection_summary": clean_text(state.get("reflection_summary", "")),
        "next_self_check_question": clean_text(
            state.get("next_self_check_question", "")
        ),
        "final_summary": clean_text(state.get("final_summary", "")),
    }
