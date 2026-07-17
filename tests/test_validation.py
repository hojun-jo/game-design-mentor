from __future__ import annotations

import unittest

from mentor.models import StructuredBrief
from mentor.validation import (
    build_clarifying_questions,
    is_game_design_related,
    validate_required_fields,
)


class ValidationTest(unittest.TestCase):
    def test_clarifying_questions_include_learning_context(self) -> None:
        questions = build_clarifying_questions(
            missing_fields=["emotion_goal", "core_loop"],
            soft_missing_fields=["target_player", "reward_structure"],
        )

        self.assertEqual(
            questions[0].question,
            "어떤 플레이어에게 어떤 감정을 주고 싶나요?",
        )
        self.assertTrue(questions[0].learning_goal)
        self.assertTrue(questions[0].blocks_review)
        self.assertEqual(questions[1].field, "core_loop")
        self.assertEqual(questions[2].field, "reward_structure")
        self.assertNotIn("emotion_goal", [question.field for question in questions])
        self.assertNotIn("target_player", [question.field for question in questions])

    def test_emotion_goal_question_is_not_duplicated(self) -> None:
        questions = build_clarifying_questions(
            missing_fields=["emotion_goal"],
            soft_missing_fields=[],
        )

        self.assertEqual([question.field for question in questions], ["emotion_goal"])

    def test_target_player_question_is_specific_when_emotion_exists(self) -> None:
        questions = build_clarifying_questions(
            missing_fields=[],
            soft_missing_fields=["target_player"],
        )

        self.assertEqual([question.field for question in questions], ["target_player"])

    def test_hard_required_fields_block_review(self) -> None:
        validation = validate_required_fields(
            {
                "concept_statement": "짧은 세션 설산 생존 전략 게임",
                "target_player": "",
                "emotion_goal": "",
                "core_loop": "",
                "reward_structure": "",
                "feature_list": [],
                "mvp_goal": "",
            }
        )

        self.assertFalse(validation.review_ready)
        self.assertEqual(validation.missing_fields, ["emotion_goal", "core_loop"])
        self.assertIn("target_player", validation.soft_missing_fields)

    def test_soft_required_fields_block_review_until_answered(self) -> None:
        validation = validate_required_fields(
            {
                "concept_statement": "짧은 세션 설산 생존 전략 게임",
                "target_player": "",
                "emotion_goal": "불안하지만 한 턴만 더 하고 싶은 긴장감",
                "core_loop": "정찰 -> 자원 선택 -> 날씨 리스크 버티기 -> 거점 복귀",
                "reward_structure": "",
                "feature_list": [],
                "mvp_goal": "",
            }
        )

        self.assertFalse(validation.review_ready)
        self.assertEqual(validation.missing_fields, [])
        self.assertIn("target_player", validation.soft_missing_fields)
        self.assertIn("reward_structure", validation.soft_missing_fields)
        self.assertIn("feature_list", validation.soft_missing_fields)
        self.assertIn("mvp_goal", validation.soft_missing_fields)

    def test_unrelated_input_is_not_game_design_related(self) -> None:
        self.assertFalse(
            is_game_design_related(
                raw_input="이번 분기 영업 보고서와 채용 계획을 정리한 문서입니다.",
                brief=StructuredBrief(
                    concept_statement="이번 분기 영업 보고서와 채용 계획",
                ),
            )
        )

    def test_game_brief_without_game_word_is_related(self) -> None:
        self.assertTrue(
            is_game_design_related(
                raw_input=(
                    "짧은 세션의 설산 생존 전략 기획이다. "
                    "불안하지만 한 턴만 더 하고 싶은 긴장감을 준다."
                ),
                brief=StructuredBrief(
                    concept_statement="짧은 세션의 설산 생존 전략",
                    emotion_goal="불안하지만 한 턴만 더 하고 싶은 긴장감",
                    core_loop="정찰 -> 자원 선택 -> 날씨 리스크 버티기 -> 거점 복귀",
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
