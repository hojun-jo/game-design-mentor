from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .extractor import extract_brief
from .models import MentorState
from .reference_tools import lookup_reference_game, merge_reference_lookup_results
from .reviewer import (
    build_learning_summary,
    generate_core_loop_review,
    generate_direction_compare,
    generate_intent_alignment_review,
    generate_scope_playtest_review,
    merge_review_guidance,
)
from .validation import validate_required_fields_patch


def build_clarifying_response(_: MentorState) -> dict:
    return {"mode": "clarifying"}


def build_review_response(_: MentorState) -> dict:
    return {"mode": "reviewed"}


def route_after_validation(state: MentorState) -> Literal[
    "build_clarifying_response",
    "reference_lookup_tool_node",
    "mark_reference_lookup_skipped",
]:
    if not state.get("review_ready", False):
        return "build_clarifying_response"
    if state.get("reference_titles", []):
        return "reference_lookup_tool_node"
    return "mark_reference_lookup_skipped"


def prepare_reference_lookup(state: MentorState) -> dict:
    tool_calls = []
    for index, title in enumerate(state.get("reference_titles", [])[:3]):
        tool_calls.append(
            {
                "id": f"reference-lookup-{index}",
                "name": "lookup_reference_game",
                "args": {"title": title},
                "type": "tool_call",
            }
        )
    return {"messages": [AIMessage(content="", tool_calls=tool_calls)]}


def mark_reference_lookup_skipped(_: MentorState) -> dict:
    return {
        "reference_contexts": [],
        "reference_citations": [],
        "reference_lookup_status": "skipped",
        "reference_lookup_notes": [],
    }


@lru_cache(maxsize=1)
def get_review_graph():
    reference_lookup_tool_node = ToolNode([lookup_reference_game], name="reference_lookup_tool_node")
    graph_builder = StateGraph(MentorState)
    graph_builder.add_node("extract_brief", extract_brief)
    graph_builder.add_node("validate_required_fields", validate_required_fields_patch)
    graph_builder.add_node("build_clarifying_response", build_clarifying_response)
    graph_builder.add_node("prepare_reference_lookup", prepare_reference_lookup)
    graph_builder.add_node("reference_lookup_tool_node", reference_lookup_tool_node)
    graph_builder.add_node("merge_reference_lookup_results", merge_reference_lookup_results)
    graph_builder.add_node("mark_reference_lookup_skipped", mark_reference_lookup_skipped)
    graph_builder.add_node("intent_alignment_review", generate_intent_alignment_review)
    graph_builder.add_node("core_loop_review", generate_core_loop_review)
    graph_builder.add_node("scope_playtest_review", generate_scope_playtest_review)
    graph_builder.add_node("merge_review_guidance", merge_review_guidance)
    graph_builder.add_node("direction_compare", generate_direction_compare)
    graph_builder.add_node("build_learning_summary", build_learning_summary)
    graph_builder.add_node("build_review_response", build_review_response)

    graph_builder.add_edge(START, "extract_brief")
    graph_builder.add_edge("extract_brief", "validate_required_fields")
    graph_builder.add_conditional_edges(
        "validate_required_fields",
        route_after_validation,
        {
            "build_clarifying_response": "build_clarifying_response",
            "reference_lookup_tool_node": "prepare_reference_lookup",
            "mark_reference_lookup_skipped": "mark_reference_lookup_skipped",
        },
    )
    graph_builder.add_edge("build_clarifying_response", END)
    graph_builder.add_edge("prepare_reference_lookup", "reference_lookup_tool_node")
    graph_builder.add_edge("reference_lookup_tool_node", "merge_reference_lookup_results")
    graph_builder.add_edge("merge_reference_lookup_results", "intent_alignment_review")
    graph_builder.add_edge("merge_reference_lookup_results", "core_loop_review")
    graph_builder.add_edge("merge_reference_lookup_results", "scope_playtest_review")
    graph_builder.add_edge("mark_reference_lookup_skipped", "intent_alignment_review")
    graph_builder.add_edge("mark_reference_lookup_skipped", "core_loop_review")
    graph_builder.add_edge("mark_reference_lookup_skipped", "scope_playtest_review")
    graph_builder.add_edge("intent_alignment_review", "merge_review_guidance")
    graph_builder.add_edge("core_loop_review", "merge_review_guidance")
    graph_builder.add_edge("scope_playtest_review", "merge_review_guidance")
    graph_builder.add_edge("merge_review_guidance", "direction_compare")
    graph_builder.add_edge("direction_compare", "build_learning_summary")
    graph_builder.add_edge("build_learning_summary", "build_review_response")
    graph_builder.add_edge("build_review_response", END)
    return graph_builder.compile()
