from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app_ui import render_reviewed_mode
from mentor.models import ReferenceGameContext, ReviewResponse


class ReviewedModeTest(unittest.TestCase):
    def test_reference_summary_groups_user_and_recommended_games(self) -> None:
        result = ReviewResponse(
            mode="reviewed",
            reference_discovery_status="ok",
            reference_summary=[
                ReferenceGameContext(
                    title="Hades",
                    origin="user",
                    confidence="high",
                ),
                ReferenceGameContext(
                    title="Dead Cells",
                    origin="recommended",
                    similarity_reason="반복 전투와 성장 선택을 함께 다룹니다.",
                    difference_summary="더 빠른 액션 중심 구조입니다.",
                    confidence="high",
                ),
            ],
        )
        streamlit = MagicMock()

        with patch("app_ui.st", streamlit):
            render_reviewed_mode(result)

        rendered_markdown = [
            call.args[0]
            for call in streamlit.markdown.call_args_list
            if call.args
        ]
        self.assertIn("**사용자가 입력한 레퍼런스**", rendered_markdown)
        self.assertIn("**시스템이 찾은 유사 레퍼런스**", rendered_markdown)
        self.assertIn("**Hades**", rendered_markdown)
        self.assertIn("**Dead Cells**", rendered_markdown)
        rendered_writes = [call.args[0] for call in streamlit.write.call_args_list if call.args]
        self.assertIn("유사한 이유: 반복 전투와 성장 선택을 함께 다룹니다.", rendered_writes)
        self.assertIn("다른 점: 더 빠른 액션 중심 구조입니다.", rendered_writes)


if __name__ == "__main__":
    unittest.main()
