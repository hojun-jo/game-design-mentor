from __future__ import annotations

import unittest
from unittest.mock import patch

from mentor.models import DomainClassificationPayload, ReviewChatPayload
from mentor.service import (
    _append_clarifying_chat_update,
    answer_clarifying_chat,
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
        self.assertEqual(result.engine_recommendation.status, "insufficient")
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

        with (
            patch(
                "mentor.service.classify_follow_up_domain",
                return_value=DomainClassificationPayload(
                    is_game_design_related=True,
                    confidence="high",
                    reason="현재 리뷰의 범위 판단을 묻고 있습니다.",
                ),
            ),
            patch(
                "mentor.service.classify_review_follow_up",
                return_value=ReviewChatPayload(
                    action="answer",
                    reply="범위 기준 때문입니다.",
                ),
            ),
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

    def test_answer_review_chat_rejects_out_of_scope_follow_up(self) -> None:
        review = run_brief_review_without_graph()

        with (
            patch(
                "mentor.service.classify_follow_up_domain",
                return_value=DomainClassificationPayload(
                    is_game_design_related=False,
                    confidence="high",
                    reason="날씨 질문입니다.",
                ),
            ),
            patch("mentor.service.classify_review_follow_up") as classify_follow_up,
        ):
            reply, refreshed = answer_review_chat(
                result=review,
                user_message="오늘 서울 날씨 알려줘.",
                chat_history=[],
            )

        self.assertIn("게임 기획과 관련된 내용만 리뷰할 수 있습니다", reply)
        self.assertIsNone(refreshed)
        classify_follow_up.assert_not_called()

    def test_engine_brief_update_bypasses_guards_and_refreshes_review(self) -> None:
        review = run_brief_review_without_graph()
        update = "스팀 게임 출시 예정. 2d or 2.5d or 3d top view"

        with (
            patch("mentor.service.classify_follow_up_domain") as classify_domain,
            patch("mentor.service.classify_review_follow_up") as classify_follow_up,
            patch("mentor.service.run_brief_review", return_value=review) as refresh,
        ):
            reply, refreshed = answer_review_chat(
                result=review,
                user_message=update,
                chat_history=[],
            )

        self.assertIn("기술 조건을 반영", reply)
        self.assertIs(refreshed, review)
        classify_domain.assert_not_called()
        classify_follow_up.assert_not_called()
        self.assertIn(update, refresh.call_args.args[0])

    def test_answer_clarifying_chat_rejects_out_of_scope_follow_up(self) -> None:
        review = run_brief_review_without_graph()

        with (
            patch(
                "mentor.service.classify_follow_up_domain",
                return_value=DomainClassificationPayload(
                    is_game_design_related=False,
                    confidence="high",
                    reason="일반 코딩 질문입니다.",
                ),
            ),
            patch("mentor.service.classify_clarifying_follow_up") as classify_follow_up,
        ):
            reply, refreshed = answer_clarifying_chat(
                result=review,
                user_message="파이썬으로 파일 읽는 법 알려줘.",
                chat_history=[],
            )

        self.assertIn("게임 기획과 관련된 내용만 리뷰할 수 있습니다", reply)
        self.assertIsNone(refreshed)
        classify_follow_up.assert_not_called()

    def test_run_brief_review_builds_out_of_scope_response(self) -> None:
        class FakeGraph:
            def invoke(self, state):
                return {
                    **state,
                    "mode": "out_of_scope",
                    "final_summary": "게임 기획과 관련된 내용만 리뷰할 수 있습니다.",
                    "domain_is_allowed": False,
                    "domain_confidence": "high",
                    "domain_reason": "영업 보고서입니다.",
                }

        with patch("mentor.service.get_review_graph", return_value=FakeGraph()):
            result = run_brief_review("이번 분기 영업 보고서와 채용 계획입니다.")

        self.assertEqual(result.mode, "out_of_scope")
        self.assertFalse(result.domain_is_allowed)
        self.assertEqual(result.domain_confidence, "high")
        self.assertEqual(result.domain_reason, "영업 보고서입니다.")
        self.assertEqual(
            result.final_summary,
            "게임 기획과 관련된 내용만 리뷰할 수 있습니다.",
        )

    def test_run_brief_review_maps_engine_recommendation(self) -> None:
        class FakeGraph:
            def invoke(self, state):
                return {
                    **state,
                    "mode": "reviewed",
                    "engine_recommendation": {
                        "status": "conditional",
                        "primary": {
                            "name": "Godot",
                            "fit": "높음",
                            "reason": "2D 프로토타입 범위와 맞습니다.",
                            "tradeoff": "출시 플랫폼 조건을 더 확인해야 합니다.",
                        },
                        "rationale": ["목표 플랫폼은 PC로 명시됐습니다."],
                        "assumptions": ["온라인 기능은 MVP에 포함되지 않는다고 가정했습니다."],
                    },
                }

        with patch("mentor.service.get_review_graph", return_value=FakeGraph()):
            result = run_brief_review(
                "PC용 2D 퍼즐 게임입니다. 플레이어에게 성취감을 주며, 퍼즐을 풀고 별을 모아 다음 스테이지를 엽니다."
            )

        self.assertEqual(result.engine_recommendation.status, "conditional")
        self.assertEqual(result.engine_recommendation.primary.name, "Godot")


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
