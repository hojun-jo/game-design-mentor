from __future__ import annotations

from typing import Literal

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class MentorState(MessagesState, total=False):
    raw_input: str
    mode: Literal["clarifying", "reviewed"]
    concept_statement: str
    target_player: str
    emotion_goal: str
    core_loop: str
    reward_structure: str
    differentiation_points: list[str]
    feature_list: list[str]
    development_window_weeks: int
    team_composition: str
    mvp_goal: str
    test_audience: str
    constraints_note: str
    reference_titles: list[str]
    reference_contexts: list["ReferenceGameContext"]
    reference_citations: list["ReferenceCitation"]
    reference_lookup_status: Literal["ok", "partial", "failed", "skipped"]
    reference_lookup_notes: list[str]
    missing_fields: list[str]
    soft_missing_fields: list[str]
    clarifying_questions: list["ClarifyingQuestion"]
    mentor_questions: list["ClarifyingQuestion"]
    mentor_principles: list[str]
    intent_mentor_questions: list["ClarifyingQuestion"]
    intent_mentor_principles: list[str]
    core_loop_mentor_questions: list["ClarifyingQuestion"]
    core_loop_mentor_principles: list[str]
    scope_mentor_questions: list["ClarifyingQuestion"]
    scope_mentor_principles: list[str]
    review_ready: bool
    intent_diagnosis: str
    intent_rationale: list[str]
    core_loop_diagnosis: str
    core_loop_rationale: list[str]
    scope_diagnosis: str
    scope_rationale: list[str]
    playtest_rationale: list[str]
    playtest_hypothesis: str
    direction_options: list["DirectionOption"]
    scope_recommendations: list[str]
    playtest_questions: list[str]
    reflection_summary: str
    next_self_check_question: str
    final_summary: str


class StructuredBrief(BaseModel):
    concept_statement: str = Field(default="")
    target_player: str = Field(default="")
    emotion_goal: str = Field(default="")
    core_loop: str = Field(default="")
    reward_structure: str = Field(default="")
    differentiation_points: list[str] = Field(default_factory=list)
    feature_list: list[str] = Field(default_factory=list)
    development_window_weeks: int = Field(default=0)
    team_composition: str = Field(default="")
    mvp_goal: str = Field(default="")
    test_audience: str = Field(default="")
    constraints_note: str = Field(default="")
    reference_titles: list[str] = Field(default_factory=list)


class ClarifyingQuestion(BaseModel):
    field: str
    priority: Literal["hard", "soft"]
    question: str
    question_type: Literal["clarify", "challenge", "compare", "reflect"] = "clarify"
    learning_goal: str = Field(default="")
    rationale: str = Field(default="")
    blocks_review: bool = False


class ValidationResult(BaseModel):
    missing_fields: list[str] = Field(default_factory=list)
    soft_missing_fields: list[str] = Field(default_factory=list)
    clarifying_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    review_ready: bool = False


class DirectionOption(BaseModel):
    title: str = Field(default="")
    reason: str = Field(default="")
    tradeoff: str = Field(default="")


class ReferenceGameContext(BaseModel):
    title: str = Field(default="")
    matched_name: str = Field(default="")
    genre_tags: list[str] = Field(default_factory=list)
    core_loop_summary: str = Field(default="")
    notable_positioning: str = Field(default="")
    source_notes: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"


class ReferenceCitation(BaseModel):
    reference_title: str = Field(default="")
    url: str = Field(default="")
    title: str = Field(default="")
    snippet: str = Field(default="")


class ReferenceLookupResult(BaseModel):
    title: str = Field(default="")
    status: Literal["ok", "not_found", "ambiguous", "error"] = "not_found"
    context: ReferenceGameContext | None = None
    note: str = Field(default="")
    citations: list[ReferenceCitation] = Field(default_factory=list)


class ReviewPayload(BaseModel):
    intent_diagnosis: str = Field(default="")
    intent_rationale: list[str] = Field(default_factory=list)
    core_loop_diagnosis: str = Field(default="")
    core_loop_rationale: list[str] = Field(default_factory=list)
    scope_diagnosis: str = Field(default="")
    scope_rationale: list[str] = Field(default_factory=list)
    playtest_rationale: list[str] = Field(default_factory=list)
    mentor_principles: list[str] = Field(default_factory=list)
    mentor_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    scope_recommendations: list[str] = Field(default_factory=list)
    playtest_hypothesis: str = Field(default="")
    playtest_questions: list[str] = Field(default_factory=list)
    direction_options: list[DirectionOption] = Field(default_factory=list)
    reflection_summary: str = Field(default="")
    next_self_check_question: str = Field(default="")
    final_summary: str = Field(default="")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(default="")


class ReviewChatPayload(BaseModel):
    action: Literal["answer", "revise"] = "answer"
    reply: str = Field(default="")
    revision_note: str = Field(default="")


class ClarifyingChatPayload(BaseModel):
    action: Literal["answer", "continue_review"] = "answer"
    reply: str = Field(default="")
    answer_note: str = Field(default="")


class IntentReviewPayload(BaseModel):
    intent_diagnosis: str = Field(default="")
    intent_rationale: list[str] = Field(default_factory=list)
    mentor_principles: list[str] = Field(default_factory=list)
    mentor_questions: list[ClarifyingQuestion] = Field(default_factory=list)


class CoreLoopReviewPayload(BaseModel):
    core_loop_diagnosis: str = Field(default="")
    core_loop_rationale: list[str] = Field(default_factory=list)
    mentor_principles: list[str] = Field(default_factory=list)
    mentor_questions: list[ClarifyingQuestion] = Field(default_factory=list)


class ScopePlaytestPayload(BaseModel):
    scope_diagnosis: str = Field(default="")
    scope_rationale: list[str] = Field(default_factory=list)
    playtest_rationale: list[str] = Field(default_factory=list)
    mentor_principles: list[str] = Field(default_factory=list)
    mentor_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    scope_recommendations: list[str] = Field(default_factory=list)
    playtest_hypothesis: str = Field(default="")
    playtest_questions: list[str] = Field(default_factory=list)


class DirectionComparePayload(BaseModel):
    direction_options: list[DirectionOption] = Field(default_factory=list)
    final_summary: str = Field(default="")


class LearningSummaryPayload(BaseModel):
    reflection_summary: str = Field(default="")
    next_self_check_question: str = Field(default="")
    final_summary: str = Field(default="")


class DiagnosisResult(BaseModel):
    intent: str = Field(default="")
    intent_rationale: list[str] = Field(default_factory=list)
    core_loop: str = Field(default="")
    core_loop_rationale: list[str] = Field(default_factory=list)
    scope: str = Field(default="")
    scope_rationale: list[str] = Field(default_factory=list)


class ScopeResult(BaseModel):
    summary: str = Field(default="")
    rationale: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PlaytestPlan(BaseModel):
    hypothesis: str = Field(default="")
    rationale: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    target_audience: str = Field(default="")


class LearningResult(BaseModel):
    principles: list[str] = Field(default_factory=list)
    reflection_summary: str = Field(default="")
    next_self_check_question: str = Field(default="")


class ReviewResponse(BaseModel):
    mode: Literal["clarifying", "reviewed"]
    questions: list[ClarifyingQuestion] = Field(default_factory=list)
    brief: StructuredBrief = Field(default_factory=StructuredBrief)
    reference_summary: list[ReferenceGameContext] = Field(default_factory=list)
    reference_citations: list[ReferenceCitation] = Field(default_factory=list)
    reference_lookup_status: Literal["ok", "partial", "failed", "skipped"] = "skipped"
    reference_lookup_notes: list[str] = Field(default_factory=list)
    diagnosis: DiagnosisResult = Field(default_factory=DiagnosisResult)
    directions: list[DirectionOption] = Field(default_factory=list)
    scope: ScopeResult = Field(default_factory=ScopeResult)
    playtest_plan: PlaytestPlan = Field(default_factory=PlaytestPlan)
    learning: LearningResult = Field(default_factory=LearningResult)
    final_summary: str = Field(default="")
    missing_fields: list[str] = Field(default_factory=list)
    soft_missing_fields: list[str] = Field(default_factory=list)
    raw_input: str = Field(default="")
