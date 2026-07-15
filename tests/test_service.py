from __future__ import annotations

import unittest

from mentor.service import _append_clarifying_chat_update


class ServiceTest(unittest.TestCase):
    def test_append_clarifying_chat_update_keeps_confirmed_note_separate(self) -> None:
        updated = _append_clarifying_chat_update(
            raw_input="짧은 세션 설산 생존 전략 게임",
            answer_note="타깃 플레이어는 20~30대 전략 게임 팬이다.",
        )

        self.assertIn("Clarifying chat updates:", updated)
        self.assertIn("타깃 플레이어는 20~30대 전략 게임 팬이다.", updated)

if __name__ == "__main__":
    unittest.main()
