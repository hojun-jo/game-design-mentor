from __future__ import annotations

import unittest

from mentor.graph import get_review_graph, route_after_validation


def graph_edges() -> set[tuple[str, str]]:
    return {
        (edge.source, edge.target)
        for edge in get_review_graph().get_graph().edges
    }


class GraphTest(unittest.TestCase):
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

    def test_review_graph_fans_out_after_reference_lookup(self) -> None:
        edges = graph_edges()

        for source in {
            "merge_reference_lookup_results",
            "mark_reference_lookup_skipped",
        }:
            self.assertIn((source, "intent_alignment_review"), edges)
            self.assertIn((source, "core_loop_review"), edges)
            self.assertIn((source, "scope_playtest_review"), edges)

    def test_review_graph_fans_in_before_direction_compare(self) -> None:
        edges = graph_edges()

        self.assertIn(("intent_alignment_review", "merge_review_guidance"), edges)
        self.assertIn(("core_loop_review", "merge_review_guidance"), edges)
        self.assertIn(("scope_playtest_review", "merge_review_guidance"), edges)
        self.assertIn(("merge_review_guidance", "direction_compare"), edges)
        self.assertNotIn(("intent_alignment_review", "core_loop_review"), edges)
        self.assertNotIn(("core_loop_review", "scope_playtest_review"), edges)


if __name__ == "__main__":
    unittest.main()
