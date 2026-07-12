from __future__ import annotations

from typing import Final

import streamlit as st

from app_ui import (
    get_raw_input,
    init_session_state,
    render_brief,
    render_clarifying_mode,
    render_reviewed_mode,
)
from mentor.models import ReviewResponse
from mentor.service import continue_brief_review, run_brief_review

PAGE_TITLE: Final = "Game Design Mentor"


def _render_result(result: ReviewResponse) -> None:
    render_brief(result)

    if result.mode == "clarifying":
        submitted, answers = render_clarifying_mode(result)
        if not submitted:
            return

        with st.spinner("답변을 반영해 다시 리뷰하는 중입니다..."):
            try:
                refreshed = continue_brief_review(
                    raw_input=st.session_state["source_text"],
                    questions=result.questions,
                    answers=answers,
                )
            except Exception as exc:
                st.error(str(exc))
                return

        st.session_state["source_text"] = refreshed.raw_input
        st.session_state["review_result"] = refreshed
        st.rerun()

    render_reviewed_mode(result)


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    init_session_state()
    st.title("Game Design Mentor")
    st.caption("초보 인디 개발자를 위한 일회성 게임 기획 리뷰")

    st.markdown(
        """
기획 초안을 자유롭게 붙여넣거나 `.md` 파일로 업로드하세요.
현재 앱은 `구조화 -> 검증 -> 질문 보완 -> 3개 리뷰 축 -> 방향 비교 -> 최종 출력` 흐름을 지원합니다.
"""
    )

    text_input = st.text_area(
        "기획 초안 붙여넣기",
        height=320,
        placeholder=(
            "예시:\n"
            "짧은 세션의 설산 생존 전략 게임이다.\n"
            "전략 판단을 좋아하는 20~30대 솔로 플레이어가 대상이다.\n"
            "불안하지만 한 턴만 더 해보고 싶은 긴장감을 주고 싶다.\n"
            "정찰 -> 자원 선택 -> 날씨 리스크 버티기 -> 거점 복귀가 코어 루프다.\n"
            "이번 MVP는 루프가 반복 재미를 만드는지 검증하려고 한다."
        ),
    )
    uploaded_file = st.file_uploader("또는 Markdown 파일 업로드", type=["md"])

    if st.button("리뷰 실행", type="primary"):
        raw_input = get_raw_input(text_input, uploaded_file)
        if raw_input is None:
            return

        with st.spinner("기획 초안을 구조화하고 리뷰하는 중입니다..."):
            try:
                result = run_brief_review(raw_input)
            except Exception as exc:
                st.error(str(exc))
                return

        st.session_state["source_text"] = result.raw_input
        st.session_state["review_result"] = result

    result = st.session_state.get("review_result")
    if result is not None:
        _render_result(result)


if __name__ == "__main__":
    main()
