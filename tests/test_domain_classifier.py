from __future__ import annotations

import unittest
from unittest.mock import patch

from mentor.domain_classifier import DOMAIN_REJECTION_MESSAGE, ensure_game_design_domain
from mentor.models import DomainClassificationPayload, StructuredBrief


class DomainClassifierTest(unittest.TestCase):
    def test_rejects_unrelated_classification(self) -> None:
        with patch(
            "mentor.domain_classifier.classify_game_design_domain",
            return_value=DomainClassificationPayload(
                is_game_design_related=False,
                confidence="high",
                reason="영업 보고서입니다.",
            ),
        ):
            with self.assertRaisesRegex(ValueError, DOMAIN_REJECTION_MESSAGE[:12]):
                ensure_game_design_domain(
                    raw_input="이번 분기 영업 보고서입니다.",
                    brief=StructuredBrief(concept_statement="영업 보고서"),
                )

    def test_rejects_low_confidence_even_when_related(self) -> None:
        with patch(
            "mentor.domain_classifier.classify_game_design_domain",
            return_value=DomainClassificationPayload(
                is_game_design_related=True,
                confidence="low",
                reason="게임인지 일반 전략 문서인지 불명확합니다.",
            ),
        ):
            with self.assertRaises(ValueError):
                ensure_game_design_domain(
                    raw_input="전략과 보상 체계를 정리합니다.",
                    brief=StructuredBrief(concept_statement="전략과 보상 체계"),
                )

    def test_accepts_medium_confidence_game_design_classification(self) -> None:
        with patch(
            "mentor.domain_classifier.classify_game_design_domain",
            return_value=DomainClassificationPayload(
                is_game_design_related=True,
                confidence="medium",
                reason="코어 루프와 플레이어 경험을 다룹니다.",
            ),
        ):
            ensure_game_design_domain(
                raw_input="플레이어가 탐험과 귀환을 반복하는 생존 게임입니다.",
                brief=StructuredBrief(
                    concept_statement="탐험과 귀환을 반복하는 생존 게임",
                    core_loop="탐험 -> 자원 선택 -> 귀환",
                ),
            )


if __name__ == "__main__":
    unittest.main()
