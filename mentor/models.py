from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class MentorState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
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
    review_ready: bool
    intent_diagnosis: str
    core_loop_diagnosis: str
    scope_diagnosis: str
    playtest_hypothesis: str
    direction_options: list["DirectionOption"]
    scope_recommendations: list[str]
    playtest_questions: list[str]
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
    core_loop_diagnosis: str = Field(default="")
    scope_diagnosis: str = Field(default="")
    scope_recommendations: list[str] = Field(default_factory=list)
    playtest_hypothesis: str = Field(default="")
    playtest_questions: list[str] = Field(default_factory=list)
    direction_options: list[DirectionOption] = Field(default_factory=list)
    final_summary: str = Field(default="")


class IntentReviewPayload(BaseModel):
    intent_diagnosis: str = Field(default="")


class CoreLoopReviewPayload(BaseModel):
    core_loop_diagnosis: str = Field(default="")


class ScopePlaytestPayload(BaseModel):
    scope_diagnosis: str = Field(default="")
    scope_recommendations: list[str] = Field(default_factory=list)
    playtest_hypothesis: str = Field(default="")
    playtest_questions: list[str] = Field(default_factory=list)


class DirectionComparePayload(BaseModel):
    direction_options: list[DirectionOption] = Field(default_factory=list)
    final_summary: str = Field(default="")


class DiagnosisResult(BaseModel):
    intent: str = Field(default="")
    core_loop: str = Field(default="")
    scope: str = Field(default="")


class ScopeResult(BaseModel):
    summary: str = Field(default="")
    recommendations: list[str] = Field(default_factory=list)


class PlaytestPlan(BaseModel):
    hypothesis: str = Field(default="")
    questions: list[str] = Field(default_factory=list)
    target_audience: str = Field(default="")


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
    final_summary: str = Field(default="")
    missing_fields: list[str] = Field(default_factory=list)
    soft_missing_fields: list[str] = Field(default_factory=list)
    raw_input: str = Field(default="")
