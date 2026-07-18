# Game Design Mentor

초보 인디 개발자를 위한 웹 기반 게임 기획 리뷰 MVP다.

현재 구현 범위는 `LangGraph 기반 자유형 초안 입력 -> LLM 구조화 추출 -> 필수/권장 입력 검증 -> OpenAI web search 기반 유사 레퍼런스 게임 자동 발굴 및 공개 정보 조회 -> 보완 채팅 -> 3개 리뷰 축 -> 2개 방향 비교 -> 최종 요약 -> 리뷰 후속 대화`이다.

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

1. 본문 채팅에 기획 초안을 붙여넣거나 사이드바에서 `.md` 파일을 업로드한다.
2. LLM이 기획 초안을 구조화한다.
3. 앱 코드가 `emotion_goal`, `core_loop` 하드 필수값과 권장 입력을 검증한다.
4. 리뷰 가능 상태가 되면 OpenAI web search로 유사 레퍼런스 게임을 최대 3개 자동 발굴하고, 사용자가 입력한 레퍼런스와 함께 공개 정보 및 citation을 재검증한다.
5. 하드 필수값 또는 권장 입력이 비면 보완 채팅으로 전환하고, 답변을 반영해 다시 구조화한다.
6. 리뷰 가능 상태가 되면 의도 정렬, 코어 루프, MVP 범위/플레이테스트 계획을 짧게 진단한다.
7. 정확히 2개의 해석 방향과 각각의 근거, 트레이드오프를 보여준다.
8. 지금 먼저 정해야 할 것 한 줄로 마무리한다.
9. 리뷰 완료 후 본문은 후속 대화 채팅으로 쓰고, 리뷰 리포트와 요약은 접이식 영역과 사이드바에서 확인한다.
10. 사용자는 후속 대화에서 해석 오류를 정정하거나 리뷰 근거를 질문할 수 있다.
11. 정정 메시지는 원문에 누적되어 리뷰를 다시 생성하고, 단순 질문은 현재 리뷰 컨텍스트로 답변한다.
