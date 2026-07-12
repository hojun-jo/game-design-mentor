from __future__ import annotations

import os
from typing import Any, Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from .llm import get_openai_client, get_reviewer_base_llm
from .models import (
    MentorState,
    ReferenceCitation,
    ReferenceGameContext,
    ReferenceLookupResult,
)
from .state_utils import clean_text


class ReferenceSummaryPayload(BaseModel):
    matched_name: str = Field(default="")
    genre_tags: list[str] = Field(default_factory=list)
    core_loop_summary: str = Field(default="")
    notable_positioning: str = Field(default="")
    confidence: Literal["low", "medium", "high"] = "low"
    match_status: Literal["ok", "ambiguous", "not_found"] = "not_found"
    note: str = Field(default="")


def _get_web_search_model() -> str:
    return os.getenv("OPENAI_WEB_SEARCH_MODEL", "gpt-4.1-mini")


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_") and item is not None
        }
    return {}


def _extract_output_text(response: Any) -> tuple[str, list[dict[str, Any]]]:
    output_text = clean_text(str(getattr(response, "output_text", "")))
    annotations: list[dict[str, Any]] = []

    for item in getattr(response, "output", []) or []:
        item_dict = _as_dict(item)
        if item_dict.get("type") != "message":
            continue
        for content in item_dict.get("content", []) or []:
            content_dict = _as_dict(content)
            if content_dict.get("type") != "output_text":
                continue
            if not output_text:
                output_text = clean_text(str(content_dict.get("text", "")))
            for annotation in content_dict.get("annotations", []) or []:
                annotations.append(_as_dict(annotation))

    return output_text, annotations


def _extract_sources(response: Any) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []

    for item in getattr(response, "output", []) or []:
        item_dict = _as_dict(item)
        if item_dict.get("type") != "web_search_call":
            continue
        action = _as_dict(item_dict.get("action"))
        for source in action.get("sources", []) or []:
            source_dict = _as_dict(source)
            if source_dict:
                sources.append(source_dict)

    return sources


def _slice_snippet(text: str, start_index: Any, end_index: Any) -> str:
    if not isinstance(start_index, int) or not isinstance(end_index, int):
        return ""
    if start_index < 0 or end_index <= start_index or end_index > len(text):
        return ""
    return clean_text(text[start_index:end_index])


def _dedupe_citations(citations: list[ReferenceCitation]) -> list[ReferenceCitation]:
    deduped: list[ReferenceCitation] = []
    seen: set[tuple[str, str]] = set()
    for citation in citations:
        key = (clean_text(citation.reference_title), clean_text(citation.url))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        deduped.append(
            ReferenceCitation(
                reference_title=key[0],
                url=key[1],
                title=clean_text(citation.title),
                snippet=clean_text(citation.snippet),
            )
        )
    return deduped


def _normalize_citations(
    reference_title: str,
    output_text: str,
    annotations: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> list[ReferenceCitation]:
    citations: list[ReferenceCitation] = []

    for annotation in annotations:
        annotation_type = clean_text(str(annotation.get("type", "")))
        if annotation_type != "url_citation":
            continue
        payload = _as_dict(annotation.get("url_citation")) or annotation
        url = clean_text(str(payload.get("url", "")))
        title = clean_text(str(payload.get("title", "")))
        snippet = _slice_snippet(
            output_text,
            payload.get("start_index"),
            payload.get("end_index"),
        )
        citations.append(
            ReferenceCitation(
                reference_title=reference_title,
                url=url,
                title=title,
                snippet=snippet,
            )
        )

    for source in sources:
        url = clean_text(
            str(source.get("url") or source.get("source_website_url") or "")
        )
        title = clean_text(str(source.get("title") or source.get("name") or ""))
        snippet = clean_text(
            str(source.get("snippet") or source.get("excerpt") or source.get("summary") or "")
        )
        citations.append(
            ReferenceCitation(
                reference_title=reference_title,
                url=url,
                title=title,
                snippet=snippet,
            )
        )

    return _dedupe_citations(citations)[:4]


def _summarize_reference(
    title: str,
    search_summary: str,
    citations: list[ReferenceCitation],
) -> ReferenceSummaryPayload:
    prompt = f"""
You summarize public reference information about a game for a game design mentor.
Write the output in Korean and keep it concise.

Rules:
- Use only the supplied search summary and citation metadata.
- Decide whether the result clearly matches a specific game title.
- `match_status` must be one of `ok`, `ambiguous`, `not_found`.
- `genre_tags` should contain up to 3 short genre or positioning tags.
- `core_loop_summary` should describe the repeatable loop in one sentence.
- `notable_positioning` should describe what the game is known for in one sentence.
- `confidence` should reflect how reliable the title match and public summary look.
- `note` should be empty unless the lookup was ambiguous, partial, or otherwise limited.

Reference title from user:
{title}

Search summary:
{search_summary}

Citation metadata:
{[citation.model_dump() for citation in citations]}
""".strip()

    return get_reviewer_base_llm().with_structured_output(ReferenceSummaryPayload).invoke(prompt)


def _search_reference_summary(title: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    response = get_openai_client().responses.create(
        model=_get_web_search_model(),
        tools=[{"type": "web_search"}],
        include=["web_search_call.action.sources"],
        input=(
            "Find concise, public, factual information about the video game title below.\n"
            "Prefer the official game site, major store pages, and reliable game databases or wikis.\n"
            "Focus on what the game actually is: genre, core repeatable loop, and notable positioning.\n"
            "If the title is ambiguous or not clearly a game, say that directly.\n\n"
            f"Game title: {title}"
        ),
    )
    output_text, annotations = _extract_output_text(response)
    sources = _extract_sources(response)
    return output_text, annotations, sources


def lookup_reference_game_data(title: str) -> ReferenceLookupResult:
    normalized_title = clean_text(title)
    if not normalized_title:
        return ReferenceLookupResult(
            title="",
            status="not_found",
            note="빈 레퍼런스 제목은 조회하지 않습니다.",
        )

    try:
        search_summary, annotations, sources = _search_reference_summary(normalized_title)
        citations = _normalize_citations(normalized_title, search_summary, annotations, sources)

        if not search_summary and not citations:
            return ReferenceLookupResult(
                title=normalized_title,
                status="not_found",
                note="공개 웹에서 비교 가능한 레퍼런스 정보를 찾지 못했습니다.",
            )

        summary = _summarize_reference(normalized_title, search_summary, citations)
        if summary.match_status == "not_found":
            return ReferenceLookupResult(
                title=normalized_title,
                status="not_found",
                note=clean_text(summary.note) or "공개 웹에서 해당 게임 정보를 명확히 확인하지 못했습니다.",
                citations=citations,
            )

        context = ReferenceGameContext(
            title=normalized_title,
            matched_name=clean_text(summary.matched_name or normalized_title),
            genre_tags=[clean_text(tag) for tag in summary.genre_tags if clean_text(tag)][:3],
            core_loop_summary=clean_text(summary.core_loop_summary),
            notable_positioning=clean_text(summary.notable_positioning),
            source_notes=[
                "OpenAI web search 기반 공개 정보 요약",
                f"근거 링크 {len(citations)}건",
            ],
            confidence=summary.confidence,
        )

        status = summary.match_status
        note = clean_text(summary.note)
        if status == "ok" and summary.confidence == "low":
            status = "ambiguous"
            if not note:
                note = "검색 결과는 있었지만 정확한 게임 매칭 신뢰도는 낮았습니다."

        if status == "ambiguous" and not note:
            note = "공개 웹 기준으로 유사한 후보를 요약했습니다."

        return ReferenceLookupResult(
            title=normalized_title,
            status=status,
            context=context,
            note=note,
            citations=citations,
        )
    except Exception:
        return ReferenceLookupResult(
            title=normalized_title,
            status="error",
            note="OpenAI web search 기반 레퍼런스 조회에 실패했습니다.",
        )


@tool("lookup_reference_game")
def lookup_reference_game(title: str) -> str:
    """Look up public reference information for a game title and return a compact JSON summary."""
    return lookup_reference_game_data(title).model_dump_json(ensure_ascii=False)


def merge_reference_lookup_results(state: MentorState) -> dict:
    contexts: list[ReferenceGameContext] = []
    citations: list[ReferenceCitation] = []
    notes: list[str] = []
    statuses: list[str] = []

    for message in state.get("messages", []):
        if getattr(message, "type", "") != "tool":
            continue
        if getattr(message, "name", "") != "lookup_reference_game":
            continue
        try:
            payload = ReferenceLookupResult.model_validate_json(str(message.content))
        except Exception:
            notes.append("레퍼런스 조회 결과를 해석하지 못했습니다.")
            statuses.append("error")
            continue

        statuses.append(payload.status)
        if payload.context is not None:
            contexts.append(payload.context)
        citations.extend(payload.citations)
        if payload.note:
            notes.append(payload.note)

    if not statuses:
        lookup_status = "failed"
        notes.append("레퍼런스 조회 결과가 비어 있습니다.")
    elif all(status == "ok" for status in statuses):
        lookup_status = "ok"
    elif any(status in {"ok", "ambiguous"} for status in statuses):
        lookup_status = "partial"
    else:
        lookup_status = "failed"

    deduped_notes: list[str] = []
    for note in notes:
        cleaned = clean_text(note)
        if cleaned and cleaned not in deduped_notes:
            deduped_notes.append(cleaned)

    return {
        "reference_contexts": contexts,
        "reference_citations": _dedupe_citations(citations),
        "reference_lookup_status": lookup_status,
        "reference_lookup_notes": deduped_notes,
    }
