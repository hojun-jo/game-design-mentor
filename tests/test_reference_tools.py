from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from langchain_core.messages import ToolMessage

from mentor.reference_tools import (
    RecommendedReferenceAssessment,
    discover_reference_games,
    merge_reference_lookup_results,
)


class ReferenceToolsTest(unittest.TestCase):
    def test_merge_reference_lookup_results_reads_tool_payload(self) -> None:
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

        self.assertEqual(merged_reference["reference_lookup_status"], "ok")
        self.assertEqual(len(merged_reference["reference_contexts"]), 1)
        self.assertEqual(len(merged_reference["reference_citations"]), 1)

    def test_discover_reference_games_excludes_user_titles_and_limits_to_three(self) -> None:
        response = MagicMock(
            output_text="Candidate games: Hades, Dead Cells, Risk of Rain 2, Rogue Legacy"
        )
        client = MagicMock()
        client.responses.create.return_value = response
        reviewer = MagicMock()
        reviewer.with_structured_output.return_value.invoke.return_value = MagicMock(
            titles=["Hades", "Dead Cells", "Risk of Rain 2", "Rogue Legacy"],
            note="",
        )

        with patch("mentor.reference_tools.get_openai_client", return_value=client), patch(
            "mentor.reference_tools.get_reviewer_base_llm", return_value=reviewer
        ):
            result = discover_reference_games(
                {
                    "concept_statement": "반복 전투와 성장 게임",
                    "emotion_goal": "긴장감",
                    "core_loop": "전투 후 업그레이드 선택",
                    "reference_titles": ["Hades"],
                }
            )

        self.assertEqual(result["reference_discovery_status"], "ok")
        self.assertEqual(
            result["recommended_reference_titles"],
            ["Dead Cells", "Risk of Rain 2", "Rogue Legacy"],
        )

    def test_merge_reference_lookup_results_keeps_only_verified_assessed_recommendations(self) -> None:
        with patch(
            "mentor.reference_tools._assess_recommended_references",
            return_value={
                "dead cells": RecommendedReferenceAssessment(
                    title="Dead Cells",
                    similarity_reason="반복 전투와 성장 선택을 함께 다룹니다.",
                    difference_summary="더 빠른 액션 중심 구조입니다.",
                )
            },
        ):
            merged_reference = merge_reference_lookup_results(
                {
                    "reference_titles": ["Hades"],
                    "messages": [
                        ToolMessage(
                            content=(
                                '{"title":"Hades","status":"ok","context":{"title":"Hades",'
                                '"matched_name":"Hades","confidence":"high"},"citations":[]}'
                            ),
                            tool_call_id="user-reference-0",
                            name="lookup_reference_game",
                        ),
                        ToolMessage(
                            content=(
                                '{"title":"Dead Cells","status":"ok","context":{"title":"Dead Cells",'
                                '"matched_name":"Dead Cells","confidence":"high"},"citations":['
                                '{"reference_title":"Dead Cells","url":"https://example.com/dead-cells"}]}'
                            ),
                            tool_call_id="recommended-reference-0",
                            name="lookup_reference_game",
                        ),
                        ToolMessage(
                            content=(
                                '{"title":"Low confidence","status":"ok","context":{"title":"Low confidence",'
                                '"matched_name":"Low confidence","confidence":"low"},"citations":['
                                '{"reference_title":"Low confidence","url":"https://example.com/low"}]}'
                            ),
                            tool_call_id="recommended-reference-1",
                            name="lookup_reference_game",
                        ),
                    ],
                }
            )

        self.assertEqual(
            [context.origin for context in merged_reference["reference_contexts"]],
            ["user", "recommended"],
        )
        recommended = merged_reference["reference_contexts"][1]
        self.assertEqual(recommended.similarity_reason, "반복 전투와 성장 선택을 함께 다룹니다.")
        self.assertEqual(recommended.difference_summary, "더 빠른 액션 중심 구조입니다.")
        self.assertEqual(
            [citation.reference_title for citation in merged_reference["reference_citations"]],
            ["Dead Cells"],
        )


if __name__ == "__main__":
    unittest.main()
