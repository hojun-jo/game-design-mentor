from __future__ import annotations

import unittest

from langchain_core.messages import ToolMessage

from mentor.reference_tools import merge_reference_lookup_results


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


if __name__ == "__main__":
    unittest.main()
