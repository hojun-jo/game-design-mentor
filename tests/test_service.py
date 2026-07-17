from __future__ import annotations

import unittest
from unittest.mock import patch

from mentor.models import ReviewChatPayload
from mentor.service import (
    _append_clarifying_chat_update,
    answer_review_chat,
    run_brief_review,
)


class ServiceTest(unittest.TestCase):
    def test_append_clarifying_chat_update_keeps_confirmed_note_separate(self) -> None:
        updated = _append_clarifying_chat_update(
            raw_input="짧은 세션 설산 생존 전략 게임",
            answer_note="타깃 플레이어는 20~30대 전략 게임 팬이다.",
        )

        self.assertIn("Clarifying chat updates:", updated)
        self.assertIn("타깃 플레이어는 20~30대 전략 게임 팬이다.", updated)

    def test_run_brief_review_reports_graph_progress(self) -> None:
        class FakeGraph:
            def stream(self, state, stream_mode):
                assert stream_mode == "updates"
                yield {
                    "extract_brief": {
                        "concept_statement": "설산 생존 전략 게임",
                        "emotion_goal": "긴장감",
                        "core_loop": "정찰 -> 선택 -> 복귀",
                    }
                }
                yield {
                    "validate_required_fields": {
                        "missing_fields": [],
                        "soft_missing_fields": [],
                        "review_ready": True,
                    }
                }
                yield {"build_review_response": {"mode": "reviewed"}}

        progress_messages: list[str] = []
        with patch("mentor.service.get_review_graph", return_value=FakeGraph()):
            result = run_brief_review(
                "설산 생존 전략 게임. 긴장감을 준다. 정찰 -> 선택 -> 복귀를 반복한다.",
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.mode, "reviewed")
        self.assertIn(
            "기획 초안에서 구조화된 브리프를 추출하고 있습니다.",
            progress_messages,
        )
        self.assertIn(
            "기획 초안에서 콘셉트, 감정 목표, 코어 루프를 구조화했습니다.",
            progress_messages,
        )

    def test_answer_review_chat_reports_classification_progress(self) -> None:
        progress_messages: list[str] = []
        review = run_brief_review_without_graph()

        with patch(
            "mentor.service.classify_review_follow_up",
            return_value=ReviewChatPayload(action="answer", reply="범위 기준 때문입니다."),
        ):
            reply, refreshed = answer_review_chat(
                result=review,
                user_message="왜 범위를 줄이라고 했어?",
                chat_history=[],
                progress_callback=progress_messages.append,
            )

        self.assertEqual(reply, "범위 기준 때문입니다.")
        self.assertIsNone(refreshed)
        self.assertIn(
            "후속 메시지가 질문인지, 리뷰를 갱신해야 하는 정정인지 분류하고 있습니다.",
            progress_messages,
        )
        self.assertIn(
            "현재 리뷰 컨텍스트를 바탕으로 답변을 작성했습니다.",
            progress_messages,
        )


def run_brief_review_without_graph():
    class FakeGraph:
        def invoke(self, state):
            return {
                **state,
                "mode": "reviewed",
                "concept_statement": "설산 생존 전략 게임",
                "emotion_goal": "긴장감",
                "core_loop": "정찰 -> 선택 -> 복귀",
                "missing_fields": [],
                "soft_missing_fields": [],
            }

    with patch("mentor.service.get_review_graph", return_value=FakeGraph()):
        return run_brief_review(
            "설산 생존 전략 게임. 긴장감을 준다. 정찰 -> 선택 -> 복귀를 반복한다."
        )


if __name__ == "__main__":
    unittest.main()
