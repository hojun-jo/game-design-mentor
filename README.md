# Game Design Mentor

초보 인디 개발자를 위한 웹 기반 게임 기획 리뷰 MVP다.

현재 구현 범위는 `LangGraph 기반 자유형 초안 입력 -> LLM 구조화 추출 -> OpenAI web search 기반 레퍼런스 게임 공개 정보 조회 -> 필수/권장 입력 검증 -> 질문 보완 -> 3개 리뷰 축 -> 2개 방향 비교 -> 최종 요약`이다.

## Run

```bash
uv sync
streamlit run app.py
```

`OPENAI_API_KEY`가 필요하다.

## Docs

- [MVP Plan](/Users/hojun/Development/game-design-mentor/docs/game-design-mentor-mvp-plan.md)
- [Architecture](/Users/hojun/Development/game-design-mentor/docs/game-design-mentor-architecture.md)
- [Implementation Plan](/Users/hojun/Development/game-design-mentor/docs/game-design-mentor-implementation-plan.md)

## Current Flow

1. 텍스트를 붙여넣거나 `.md` 파일을 업로드한다.
2. LLM이 기획 초안을 구조화한다.
3. `reference_titles[]`가 있으면 ToolNode가 OpenAI web search 기반 공개 레퍼런스 요약과 citation을 조회한다.
4. 앱 코드가 `emotion_goal`, `core_loop` 하드 필수값과 권장 입력을 검증한다.
5. 핵심 정보가 비면 보완 질문을 먼저 보여주고, 답변을 반영해 다시 구조화한다.
6. 리뷰 가능 상태가 되면 의도 정렬, 코어 루프, MVP 범위/플레이테스트 계획을 짧게 진단한다.
7. 정확히 2개의 해석 방향과 각각의 근거, 트레이드오프를 보여준다.
8. 지금 먼저 정해야 할 것 한 줄로 마무리한다.
