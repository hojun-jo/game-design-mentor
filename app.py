from __future__ import annotations

from typing import Final

import streamlit as st

from app_ui import (
    get_raw_input,
    init_session_state,
    render_chat_workspace,
    render_clarifying_mode,
    render_clarifying_sidebar_context,
    render_review_sidebar_context,
    render_reviewed_mode,
)
from mentor.models import ChatMessage, ReviewResponse
from mentor.service import answer_clarifying_chat, answer_review_chat, run_brief_review

PAGE_TITLE: Final = "Game Design Mentor"


def _apply_layout_styles() -> None:
    st.markdown(
        """
<style>
    [data-testid="stSidebar"] {
        min-width: 24rem;
        max-width: 24rem;
    }

    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"] {
        width: 24rem;
    }

    @media (max-width: 900px) {
        [data-testid="stSidebar"] {
            min-width: 20rem;
            max-width: 20rem;
        }

        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebarContent"] {
            width: 20rem;
        }
    }
</style>
""",
        unsafe_allow_html=True,
    )


def _get_review_chat_messages() -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    for message in st.session_state.get("review_chat_messages", []):
        if isinstance(message, ChatMessage):
            messages.append(message)
        else:
            messages.append(ChatMessage.model_validate(message))
    return messages


def _get_conversation_messages() -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    for message in st.session_state.get("conversation_messages", []):
        if isinstance(message, ChatMessage):
            messages.append(message)
        else:
            messages.append(ChatMessage.model_validate(message))
    return messages


def _get_intake_chat_messages() -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    for message in st.session_state.get("intake_chat_messages", []):
        if isinstance(message, ChatMessage):
            messages.append(message)
        else:
            messages.append(ChatMessage.model_validate(message))
    return messages


def _get_clarifying_chat_messages() -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    for message in st.session_state.get("clarifying_chat_messages", []):
        if isinstance(message, ChatMessage):
            messages.append(message)
        else:
            messages.append(ChatMessage.model_validate(message))
    return messages


def _append_intake_chat_message(role: str, content: str) -> None:
    message = ChatMessage(role=role, content=content)
    st.session_state["intake_chat_messages"].append(message)
    st.session_state["conversation_messages"].append(message)


def _append_review_chat_message(role: str, content: str) -> None:
    message = ChatMessage(role=role, content=content)
    st.session_state["review_chat_messages"].append(message)
    st.session_state["conversation_messages"].append(message)


def _append_clarifying_chat_message(role: str, content: str) -> None:
    message = ChatMessage(role=role, content=content)
    st.session_state["clarifying_chat_messages"].append(message)
    st.session_state["conversation_messages"].append(message)


def _ensure_intake_chat_started() -> None:
    if st.session_state.get("intake_chat_messages"):
        return
    _append_intake_chat_message(
        "assistant",
        (
            "기획 초안을 붙여넣어 주세요. 형식은 자유입니다.\n\n"
            "최소한 게임 콘셉트, 플레이어에게 남기고 싶은 감정, 반복 플레이 흐름이 있으면 좋습니다. "
            "부족한 부분은 제가 이어서 질문하겠습니다."
        ),
    )


def _build_clarifying_prompt(result: ReviewResponse) -> str:
    lines = ["리뷰 전에 아래 내용을 확인해야 합니다."]
    for question in result.questions:
        lines.append(f"- [{question.priority}] {question.question}")
    lines.append("")
    lines.append("답을 바로 적어도 되고, 예시나 추천 방향을 물어봐도 됩니다.")
    return "\n".join(lines).strip()


def _get_review_workspace_messages() -> list[ChatMessage]:
    return _get_conversation_messages()


def _ensure_clarifying_chat_started(result: ReviewResponse) -> None:
    if st.session_state.get("clarifying_chat_source") == result.raw_input:
        return
    st.session_state["clarifying_chat_source"] = result.raw_input
    _append_clarifying_chat_message("assistant", _build_clarifying_prompt(result))


def _ensure_review_chat_started(result: ReviewResponse) -> None:
    if st.session_state.get("review_chat_source") == result.raw_input:
        return
    st.session_state["review_chat_source"] = result.raw_input
    _append_review_chat_message(
        "assistant",
        (
            "리뷰가 준비됐습니다. 지금부터는 아래 리뷰 리포트를 기준으로 "
            "질문하거나, 의도와 다르게 해석된 부분을 정정할 수 있습니다."
        ),
    )


def _start_review_from_input(raw_input: str) -> None:
    with st.spinner("기획 초안을 구조화하고 리뷰하는 중입니다..."):
        try:
            result = run_brief_review(raw_input)
        except Exception as exc:
            st.error(str(exc))
            return

    st.session_state["source_text"] = result.raw_input
    st.session_state["review_result"] = result
    st.session_state["review_chat_messages"] = []
    st.session_state["clarifying_chat_messages"] = []
    st.session_state["clarifying_chat_source"] = ""
    st.session_state["review_chat_source"] = ""
    st.rerun()


def _render_intake() -> None:
    _ensure_intake_chat_started()

    with st.sidebar:
        st.header("파일 업로드")
        st.caption("채팅 대신 Markdown 파일로 시작할 때만 사용합니다.")
        uploaded_file = st.file_uploader("Markdown 파일 업로드", type=["md"])
        if st.button("업로드 파일로 리뷰 실행", type="primary"):
            raw_input = get_raw_input("", uploaded_file)
            if raw_input is None:
                return
            _append_intake_chat_message(
                "user",
                f"Markdown 파일 업로드: {uploaded_file.name}",
            )
            _start_review_from_input(raw_input)

    prompt = render_chat_workspace(
        title=None,
        caption=None,
        messages=_get_conversation_messages(),
        form_key="intake_chat_form",
        input_label="기획 초안",
        placeholder=(
            "예시:\n"
            "짧은 세션의 설산 생존 전략 게임이다.\n"
            "전략 판단을 좋아하는 20~30대 솔로 플레이어가 대상이다.\n"
            "불안하지만 한 턴만 더 해보고 싶은 긴장감을 주고 싶다.\n"
            "정찰 -> 자원 선택 -> 날씨 리스크 버티기 -> 거점 복귀가 코어 루프다.\n"
            "이번 MVP는 루프가 반복 재미를 만드는지 검증하려고 한다."
        ),
    )
    if prompt is None:
        return

    _append_intake_chat_message("user", prompt)
    _start_review_from_input(prompt)


def _render_result(result: ReviewResponse) -> None:
    if result.mode == "clarifying":
        _ensure_clarifying_chat_started(result)
        render_clarifying_sidebar_context(result)
        render_clarifying_mode(result)
        prompt = render_chat_workspace(
            title=None,
            caption=None,
            messages=_get_conversation_messages(),
            form_key="clarifying_chat_form",
            input_label="답변 또는 질문",
            placeholder="예: 타깃 플레이어 예시를 추천해줘 / 코어 루프는 탐험 -> 선택 -> 결과 확인이야",
        )
        if prompt is None:
            return

        chat_history = _get_conversation_messages()
        _append_clarifying_chat_message("user", prompt)
        with st.spinner("보완 대화를 반영하는 중입니다..."):
            try:
                reply, refreshed = answer_clarifying_chat(
                    result=result,
                    user_message=prompt,
                    chat_history=chat_history,
                )
            except Exception as exc:
                st.error(str(exc))
                return

        _append_clarifying_chat_message("assistant", reply)
        if refreshed is not None:
            st.session_state["source_text"] = refreshed.raw_input
            st.session_state["review_result"] = refreshed
            if refreshed.mode == "reviewed":
                st.session_state["review_chat_messages"] = []
                st.session_state["review_chat_source"] = ""
            else:
                st.session_state["clarifying_chat_source"] = refreshed.raw_input
                _append_clarifying_chat_message(
                    "assistant",
                    _build_clarifying_prompt(refreshed),
                )
        st.rerun()

    _ensure_review_chat_started(result)
    render_review_sidebar_context(result)
    review_workspace_messages = _get_review_workspace_messages()
    prompt = render_chat_workspace(
        title=None,
        caption=None,
        messages=review_workspace_messages,
        form_key="review_chat_form",
        input_label="질문 또는 정정",
        placeholder="예: 의도는 전투가 아니라 탐험 긴장감이야 / 왜 범위를 줄이라고 했어?",
    )

    with st.expander("리뷰 리포트", expanded=not _get_review_chat_messages()):
        render_reviewed_mode(result)

    if prompt is None:
        return

    chat_history = review_workspace_messages
    _append_review_chat_message("user", prompt)
    with st.spinner("후속 메시지를 반영하는 중입니다..."):
        try:
            reply, refreshed = answer_review_chat(
                result=result,
                user_message=prompt,
                chat_history=chat_history,
            )
        except Exception as exc:
            st.error(str(exc))
            return

    _append_review_chat_message("assistant", reply)
    if refreshed is not None:
        st.session_state["source_text"] = refreshed.raw_input
        st.session_state["review_result"] = refreshed
    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_layout_styles()
    init_session_state()
    st.title("Game Design Mentor")

    result = st.session_state.get("review_result")
    if result is None:
        _render_intake()
    else:
        _render_result(result)


if __name__ == "__main__":
    main()
