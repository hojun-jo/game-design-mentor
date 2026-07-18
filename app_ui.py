from __future__ import annotations

import streamlit as st

from mentor.models import ChatMessage, ReviewResponse


def init_session_state() -> None:
    st.session_state.setdefault("review_result", None)
    st.session_state.setdefault("source_text", "")
    st.session_state.setdefault("conversation_messages", [])
    st.session_state.setdefault("intake_chat_messages", [])
    st.session_state.setdefault("review_chat_messages", [])
    st.session_state.setdefault("clarifying_chat_messages", [])
    st.session_state.setdefault("clarifying_chat_source", "")
    st.session_state.setdefault("review_chat_source", "")
    st.session_state.setdefault("uploaded_markdown_file", None)


def get_raw_input(text_input: str, uploaded_file) -> str | None:
    has_text = bool(text_input.strip())
    has_file = uploaded_file is not None

    if has_text and has_file:
        st.warning("텍스트 붙여넣기와 파일 업로드 중 하나만 사용해 주세요.")
        return None

    if has_file:
        return uploaded_file.getvalue().decode("utf-8", errors="replace").strip()

    if has_text:
        return text_input.strip()

    st.warning("기획 초안을 붙여넣거나 `.md` 파일을 업로드해 주세요.")
    return None


def render_rationale(title: str, rationales: list[str]) -> None:
    if not rationales:
        return
    st.markdown(f"**{title}**")
    for rationale in rationales:
        st.write(f"- {rationale}")


def render_brief(result: ReviewResponse, show_heading: bool = True) -> None:
    if show_heading:
        st.subheader("구조화 브리프")
    if result.soft_missing_fields:
        st.caption("권장 입력이 비어 있습니다: " + ", ".join(result.soft_missing_fields))
    st.json(result.brief.model_dump())


def render_clarifying_mode(result: ReviewResponse) -> None:
    st.error("본 리뷰 전에 먼저 확인할 정보가 있습니다.")

    if result.missing_fields:
        st.caption("리뷰를 막는 핵심 누락: " + ", ".join(result.missing_fields))
    if result.soft_missing_fields:
        st.caption("리뷰 전에 확인할 권장 입력: " + ", ".join(result.soft_missing_fields))

    st.info("아래 보완 대화에서 답변하거나, 질문의 의미와 추천 방향을 물어보세요.")


def render_chat_workspace(
    title: str | None,
    caption: str | None,
    messages: list[ChatMessage],
    form_key: str,
    input_label: str,
    placeholder: str,
) -> str | None:
    if title:
        st.subheader(title)
    if caption:
        st.caption(caption)

    for message in messages:
        with st.chat_message(message.role):
            st.write(message.content)

    with st.form(form_key, clear_on_submit=True):
        draft = st.text_area(
            input_label,
            placeholder=placeholder,
            height=130,
        )
        submitted = st.form_submit_button("보내기", type="primary")

    if not submitted or not draft.strip():
        return None
    return draft.strip()


def render_clarifying_sidebar_context(result: ReviewResponse) -> None:
    with st.sidebar:
        st.header("보완 컨텍스트")
        st.caption("본문 채팅에서 답변하거나 추천을 요청하세요.")

        if result.questions:
            with st.expander("확인 중인 질문", expanded=True):
                for question in result.questions:
                    st.markdown(f"**[{question.priority}] {question.question}**")
                    if question.learning_goal:
                        st.caption(f"학습 목표: {question.learning_goal}")
                    if question.rationale:
                        st.caption(f"왜 묻나요: {question.rationale}")

        with st.expander("구조화 브리프", expanded=False):
            render_brief(result, show_heading=False)


def render_reviewed_mode(result: ReviewResponse) -> None:
    st.success("리뷰가 준비됐습니다.")

    if result.reference_summary or result.reference_lookup_status in {"partial", "failed"}:
        st.subheader("레퍼런스 참고 요약")
        if result.reference_lookup_status in {"partial", "failed"} and result.reference_lookup_notes:
            st.caption("조회 제한: " + " / ".join(result.reference_lookup_notes))
        for reference in result.reference_summary:
            st.markdown(f"**{reference.title}**")
            if reference.matched_name and reference.matched_name != reference.title:
                st.write(f"매칭 이름: {reference.matched_name}")
            if reference.genre_tags:
                st.write("장르/포지셔닝: " + ", ".join(reference.genre_tags))
            if reference.core_loop_summary:
                st.write(f"핵심 루프: {reference.core_loop_summary}")
            if reference.notable_positioning:
                st.write(f"비교 포인트: {reference.notable_positioning}")
            st.write(f"신뢰도: {reference.confidence}")
            reference_citations = [
                citation
                for citation in result.reference_citations
                if citation.reference_title == reference.title
            ]
            if reference_citations:
                st.write("근거 링크:")
                for citation in reference_citations:
                    label = citation.title or citation.url
                    st.markdown(f"- [{label}]({citation.url})")
                    if citation.snippet:
                        st.caption(citation.snippet)

    st.subheader("짧은 진단")
    if result.learning.principles:
        st.markdown("**이번 리뷰의 판단 기준**")
        for principle in result.learning.principles:
            st.write(f"- {principle}")

    st.markdown(f"**의도 정렬**\n\n{result.diagnosis.intent}")
    render_rationale("근거", result.diagnosis.intent_rationale)
    st.markdown(f"**코어 루프**\n\n{result.diagnosis.core_loop}")
    render_rationale("근거", result.diagnosis.core_loop_rationale)
    st.markdown(f"**범위와 테스트**\n\n{result.diagnosis.scope}")
    render_rationale("근거", result.diagnosis.scope_rationale)

    if result.questions:
        st.subheader("스스로 점검할 질문")
        for question in result.questions:
            st.markdown(f"**{question.question}**")
            if question.learning_goal:
                st.caption(f"학습 목표: {question.learning_goal}")
            if question.rationale:
                st.caption(f"질문 이유: {question.rationale}")

    st.subheader("해석 방향 2개")
    for index, direction in enumerate(result.directions, start=1):
        st.markdown(f"**방향 {index}. {direction.title}**")
        st.write(f"근거: {direction.reason}")
        st.write(f"트레이드오프: {direction.tradeoff}")

    st.subheader("MVP 범위 제안")
    render_rationale("근거", result.scope.rationale)
    if result.scope.recommendations:
        for item in result.scope.recommendations:
            st.write(f"- {item}")
    else:
        st.write("범위 축소 제안이 없습니다.")

    st.subheader("플레이테스트 계획")
    st.write(f"가설: {result.playtest_plan.hypothesis}")
    render_rationale("근거", result.playtest_plan.rationale)
    if result.playtest_plan.target_audience:
        st.write(f"테스트 대상: {result.playtest_plan.target_audience}")
    for question in result.playtest_plan.questions:
        st.write(f"- {question}")

    if result.learning.reflection_summary or result.learning.next_self_check_question:
        st.subheader("학습 요약")
        if result.learning.reflection_summary:
            st.write(result.learning.reflection_summary)
        if result.learning.next_self_check_question:
            st.info(result.learning.next_self_check_question)

    st.subheader("지금 먼저 정할 것")
    st.info(result.final_summary)


def render_review_sidebar_context(result: ReviewResponse) -> None:
    with st.sidebar:
        st.header("리뷰 요약")
        st.caption("본문 채팅에서 리뷰에 대해 질문하거나 정정하세요.")

        if result.final_summary:
            st.markdown("**먼저 정할 것**")
            st.info(result.final_summary)

        with st.expander("핵심 진단", expanded=True):
            if result.diagnosis.intent:
                st.markdown("**의도 정렬**")
                st.write(result.diagnosis.intent)
            if result.diagnosis.core_loop:
                st.markdown("**코어 루프**")
                st.write(result.diagnosis.core_loop)
            if result.diagnosis.scope:
                st.markdown("**범위와 테스트**")
                st.write(result.diagnosis.scope)

        if result.directions:
            with st.expander("해석 방향", expanded=False):
                for index, direction in enumerate(result.directions, start=1):
                    st.markdown(f"**{index}. {direction.title}**")
                    if direction.tradeoff:
                        st.caption(direction.tradeoff)

        with st.expander("구조화 브리프", expanded=False):
            render_brief(result, show_heading=False)
