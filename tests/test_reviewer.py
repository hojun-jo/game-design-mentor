from __future__ import annotations

import unittest

from mentor.models import ClarifyingQuestion
from mentor.reviewer import (
    merge_review_guidance,
    normalize_directions,
    normalize_mentor_principles,
    normalize_mentor_questions,
    normalize_playtest_questions,
    normalize_rationale,
)


class ReviewerNormalizationTest(unittest.TestCase):
    def test_normalize_directions_supplies_two_fallbacks(self) -> None:
        self.assertEqual(len(normalize_directions([])), 2)

    def test_normalize_playtest_questions_supplies_minimum_questions(self) -> None:
        questions = normalize_playtest_questions(
            [],
            {"core_loop": "탐험", "emotion_goal": "긴장감"},
        )

        self.assertGreaterEqual(len(questions), 2)

    def test_normalize_mentor_principles_deduplicates(self) -> None:
        principles = normalize_mentor_principles(
            ["루프는 행동과 보상이 이어져야 한다.", "루프는 행동과 보상이 이어져야 한다."]
        )

        self.assertEqual(principles, ["루프는 행동과 보상이 이어져야 한다."])

    def test_normalize_mentor_questions_preserves_reflect_question(self) -> None:
        questions = normalize_mentor_questions(
            [
                ClarifyingQuestion(
                    field="core_loop",
                    priority="soft",
                    question="플레이어가 다음 선택을 하게 만드는 이유는 무엇인가요?",
                    question_type="reflect",
                    learning_goal="반복 선택의 이유 점검",
                    rationale="반복 동기가 보여야 루프를 판단할 수 있습니다.",
                    blocks_review=False,
                )
            ]
        )

        self.assertEqual(questions[0].question_type, "reflect")
        self.assertFalse(questions[0].blocks_review)

    def test_normalize_rationale_supplies_section_fallback(self) -> None:
        self.assertTrue(normalize_rationale("", "intent")[0].startswith("대상 플레이어"))

    def test_merge_review_guidance_preserves_section_order_and_limits(self) -> None:
        merged = merge_review_guidance(
            {
                "intent_mentor_principles": ["의도 원칙", "공통 원칙"],
                "core_loop_mentor_principles": ["루프 원칙", "공통 원칙"],
                "scope_mentor_principles": ["범위 원칙"],
                "intent_mentor_questions": [
                    ClarifyingQuestion(
                        field="target_player",
                        priority="soft",
                        question="누구에게 이 감정을 남기고 싶나요?",
                        question_type="reflect",
                        learning_goal="대상과 감정 정렬 점검",
                        rationale="대상이 좁아야 감정 목표를 판단할 수 있습니다.",
                        blocks_review=False,
                    )
                ],
                "core_loop_mentor_questions": [
                    ClarifyingQuestion(
                        field="core_loop",
                        priority="soft",
                        question="반복 선택의 이유는 무엇인가요?",
                        question_type="reflect",
                        learning_goal="루프 인과 점검",
                        rationale="행동과 보상이 이어져야 반복성을 판단할 수 있습니다.",
                        blocks_review=False,
                    )
                ],
                "scope_mentor_questions": [
                    ClarifyingQuestion(
                        field="mvp_goal",
                        priority="soft",
                        question="첫 MVP가 반드시 배워야 할 것은 무엇인가요?",
                        question_type="reflect",
                        learning_goal="MVP 학습 목표 점검",
                        rationale="범위는 먼저 배울 가설을 보호해야 합니다.",
                        blocks_review=False,
                    )
                ],
            }
        )

        self.assertEqual(merged["mentor_principles"], ["의도 원칙", "공통 원칙", "루프 원칙"])
        self.assertEqual(
            [question.field for question in merged["mentor_questions"]],
            ["target_player", "core_loop", "mvp_goal"],
        )
        self.assertEqual(merged["mentor_questions"][0].question_type, "reflect")
        self.assertFalse(merged["mentor_questions"][0].blocks_review)


if __name__ == "__main__":
    unittest.main()
