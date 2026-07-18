from __future__ import annotations

import unittest
from unittest.mock import patch

from mentor.domain_classifier import DOMAIN_REJECTION_MESSAGE
from mentor.graph import (
    classify_domain,
    get_review_graph,
    reject_out_of_scope,
    route_after_domain,
    route_after_validation,
)
from mentor.models import DomainClassificationPayload


def graph_edges() -> set[tuple[str, str]]:
    return {
        (edge.source, edge.target)
        for edge in get_review_graph().get_graph().edges
    }


class GraphTest(unittest.TestCase):
    def test_classify_domain_allows_medium_confidence_game_design_input(self) -> None:
        with patch(
            "mentor.graph.classify_game_design_domain",
            return_value=DomainClassificationPayload(
                is_game_design_related=True,
                confidence="medium",
                reason="코어 루프와 플레이어 경험을 다룹니다.",
            ),
        ):
            patch_result = classify_domain(
                {
                    "raw_input": "플레이어가 탐험과 귀환을 반복하는 생존 게임입니다.",
                    "concept_statement": "탐험과 귀환을 반복하는 생존 게임",
                    "core_loop": "탐험 -> 자원 선택 -> 귀환",
                }
            )

        self.assertTrue(patch_result["domain_is_allowed"])
        self.assertEqual(patch_result["domain_confidence"], "medium")

    def test_classify_domain_rejects_low_confidence(self) -> None:
        with patch(
            "mentor.graph.classify_game_design_domain",
            return_value=DomainClassificationPayload(
                is_game_design_related=True,
                confidence="low",
                reason="게임인지 일반 전략 문서인지 불명확합니다.",
            ),
        ):
            patch_result = classify_domain(
                {
                    "raw_input": "전략과 보상 체계를 정리합니다.",
                    "concept_statement": "전략과 보상 체계",
                }
            )

        self.assertFalse(patch_result["domain_is_allowed"])
        self.assertEqual(patch_result["domain_confidence"], "low")

    def test_route_after_domain_goes_to_rejection_when_not_allowed(self) -> None:
        self.assertEqual(
            route_after_domain({"domain_is_allowed": False}),
            "reject_out_of_scope",
        )

    def test_route_after_domain_goes_to_validation_when_allowed(self) -> None:
        self.assertEqual(
            route_after_domain({"domain_is_allowed": True}),
            "validate_required_fields",
        )

    def test_reject_out_of_scope_returns_normal_terminal_state(self) -> None:
        patch_result = reject_out_of_scope({})

        self.assertEqual(patch_result["mode"], "out_of_scope")
        self.assertEqual(patch_result["final_summary"], DOMAIN_REJECTION_MESSAGE)
        self.assertFalse(patch_result["review_ready"])

    def test_route_after_validation_goes_to_clarifying_when_not_ready(self) -> None:
        self.assertEqual(
            route_after_validation({"review_ready": False}),
            "build_clarifying_response",
        )

    def test_route_after_validation_looks_up_references_when_ready(self) -> None:
        self.assertEqual(
            route_after_validation({"review_ready": True, "reference_titles": ["Hades"]}),
            "reference_lookup_tool_node",
        )

    def test_route_after_validation_skips_lookup_without_references(self) -> None:
        self.assertEqual(
            route_after_validation({"review_ready": True, "reference_titles": []}),
            "mark_reference_lookup_skipped",
        )

    def test_review_graph_compiles(self) -> None:
        self.assertIsNotNone(get_review_graph())

    def test_review_graph_routes_through_domain_guard(self) -> None:
        edges = graph_edges()

        self.assertIn(("extract_brief", "classify_domain"), edges)
        self.assertIn(("classify_domain", "validate_required_fields"), edges)
        self.assertIn(("classify_domain", "reject_out_of_scope"), edges)

    def test_review_graph_fans_out_after_reference_lookup(self) -> None:
        edges = graph_edges()

        for source in {
            "merge_reference_lookup_results",
            "mark_reference_lookup_skipped",
        }:
            self.assertIn((source, "intent_alignment_review"), edges)
            self.assertIn((source, "core_loop_review"), edges)
            self.assertIn((source, "scope_playtest_review"), edges)
            self.assertIn((source, "engine_recommendation_review"), edges)

    def test_review_graph_fans_in_before_direction_compare(self) -> None:
        edges = graph_edges()

        self.assertIn(("intent_alignment_review", "merge_review_guidance"), edges)
        self.assertIn(("core_loop_review", "merge_review_guidance"), edges)
        self.assertIn(("scope_playtest_review", "merge_review_guidance"), edges)
        self.assertIn(("engine_recommendation_review", "merge_review_guidance"), edges)
        self.assertIn(("merge_review_guidance", "direction_compare"), edges)
        self.assertNotIn(("intent_alignment_review", "core_loop_review"), edges)
        self.assertNotIn(("core_loop_review", "scope_playtest_review"), edges)


if __name__ == "__main__":
    unittest.main()
