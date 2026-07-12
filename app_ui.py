from __future__ import annotations

import streamlit as st

from mentor.models import ReviewResponse


def init_session_state() -> None:
    st.session_state.setdefault("review_result", None)
    st.session_state.setdefault("source_text", "")


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


def render_brief(result: ReviewResponse) -> None:
    st.subheader("구조화 브리프")
    if result.soft_missing_fields:
        st.caption("권장 입력이 비어 있습니다: " + ", ".join(result.soft_missing_fields))
    st.json(result.brief.model_dump())


def render_clarifying_mode(result: ReviewResponse) -> tuple[bool, dict[str, str]]:
    st.error("본 리뷰 전에 먼저 확인할 정보가 있습니다.")

    if result.missing_fields:
        st.caption("리뷰를 막는 핵심 누락: " + ", ".join(result.missing_fields))
    if result.soft_missing_fields:
        st.caption("같이 보완하면 더 정확해지는 항목: " + ", ".join(result.soft_missing_fields))

    st.subheader("보완 질문")
    with st.form("clarify_form"):
        for question in result.questions:
            st.text_area(
                f"[{question.priority}] {question.question}",
                key=f"clarify_{question.field}",
                height=90,
            )
        submitted = st.form_submit_button("답변 반영 후 다시 리뷰", type="primary")

    answers = {
        question.field: st.session_state.get(f"clarify_{question.field}", "")
        for question in result.questions
    }
    return submitted, answers


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
    st.markdown(f"**의도 정렬**\n\n{result.diagnosis.intent}")
    st.markdown(f"**코어 루프**\n\n{result.diagnosis.core_loop}")
    st.markdown(f"**범위와 테스트**\n\n{result.diagnosis.scope}")

    st.subheader("해석 방향 2개")
    for index, direction in enumerate(result.directions, start=1):
        st.markdown(f"**방향 {index}. {direction.title}**")
        st.write(f"근거: {direction.reason}")
        st.write(f"트레이드오프: {direction.tradeoff}")

    st.subheader("MVP 범위 제안")
    if result.scope.recommendations:
        for item in result.scope.recommendations:
            st.write(f"- {item}")
    else:
        st.write("범위 축소 제안이 없습니다.")

    st.subheader("플레이테스트 계획")
    st.write(f"가설: {result.playtest_plan.hypothesis}")
    if result.playtest_plan.target_audience:
        st.write(f"테스트 대상: {result.playtest_plan.target_audience}")
    for question in result.playtest_plan.questions:
        st.write(f"- {question}")

    st.subheader("지금 먼저 정할 것")
    st.info(result.final_summary)
