# 게임 기획 멘토 아키텍처 설계

## 1. 목적

이 문서는 게임 기획 멘토의 최종 MVP를 `풀스택 개발자 관점`에서 설명한다. 제품 요구사항은 [MVP Plan](./game-design-mentor-mvp-plan.md)과 `docs/features/*.md`를 따른다.

목표는 단순하다. 초보 인디 개발자가 자유형 기획 초안을 웹 앱에 넣으면, 시스템이 필요한 정보를 구조화하고, 필수값이 비면 질문으로 보완한 뒤, 최종적으로 `질문 + 짧은 진단 + 2개의 방향 + 범위/테스트 제안`을 같은 화면에서 반환하는 것이다.

이 문서에서 말하는 MVP는 `구조화 -> 검증 -> 질문 보완 -> 리뷰 축 실행 -> 방향 비교 -> 최종 출력` 전체 흐름을 포함한다. `플레이테스트 회고`는 MVP 이후 단계다.

## 2. 설계 원칙

- 제품의 중심은 범용 채팅이 아니라 `기획 리뷰 엔진`이다.
- UI, 오케스트레이션, LLM 호출, 검증 규칙의 책임을 분리한다.
- 자유형 해석은 LLM이 맡고, 분기와 정책은 애플리케이션 코드가 맡는다.
- 질문-답변은 세션 상태에 남기되, 리뷰 판단은 구조화 필드 기준으로 한다.
- 필수값이 부족하면 리뷰를 멈추고 질문 단계로 돌아간다.
- 최종 출력 구조는 항상 고정한다.
- MVP에서는 계정, DB, 장기 저장, 비동기 큐를 넣지 않는다.

## 3. 시스템 컨텍스트

```text
User
-> Browser
-> Web UI
-> Session State
-> Review Orchestrator
-> LLM Client
-> Validation / Policy
-> Review Result
-> Web UI
-> User
```

이 구조는 프론트엔드와 백엔드를 물리적으로 분리하라는 뜻이 아니다. MVP에서는 `Streamlit 단일 프로세스` 안에 모두 둘 수 있다. 다만 코드 책임은 분리해야 한다.

## 4. 풀스택 관점의 구성요소

### 4.1 Frontend Layer

- 역할
  - 텍스트 붙여넣기와 `.md` 업로드 입력 수집
  - 현재 세션 상태 표시
  - 누락 질문 입력 폼 렌더링
  - 구조화 결과와 리뷰 결과 렌더링
- 화면 책임
  - 입력 화면
  - 질문 보완 화면
  - 리뷰 결과 화면
- 비책임
  - LLM 프롬프트 조립
  - 필수값 판정
  - 리뷰 내용 생성 규칙

### 4.2 Session Layer

- 역할
  - 한 브라우저 세션 안의 대화와 구조화 상태 유지
  - 질문 단계와 리뷰 단계 전환
- 저장 범위
  - `messages`
  - `raw_input`
  - 구조화 브리프 필드
  - 누락 필드
  - 최종 리뷰 결과
- MVP 원칙
  - 세션 메모리만 사용
  - 서버 재시작 후 복구 없음
  - 사용자 계정 없음

### 4.3 Application Layer

- 역할
  - 입력 정규화
  - 유스케이스 실행
  - 그래프 또는 단계형 파이프라인 오케스트레이션
  - 노드 간 상태 병합
- 핵심 유스케이스
  - `submit_brief`
  - `answer_clarifying_questions`
  - `generate_review`

### 4.4 Domain Layer

- 역할
  - 필수 필드 규칙 정의
  - 질문 우선순위 규칙 정의
  - 리뷰 결과 shape 강제
- 핵심 규칙
  - `emotion_goal`, `core_loop`가 비면 리뷰 금지
  - `target_player`가 비면 리뷰는 가능하지만 첫 질문 우선순위 상승
  - 방향 제시는 정확히 2개만 허용
  - `플레이테스트 회고`는 MVP 범위가 아니라 `플레이테스트 계획 생성`까지만 포함

### 4.5 LLM Integration Layer

- 역할
  - 브리프 구조화 추출
  - 리뷰 문장 생성
  - 고정 schema 파싱
- 원칙
  - 구조화 출력 모델을 우선 사용
  - 애플리케이션은 LLM 자유문을 직접 신뢰하지 않고 schema로만 받는다
  - 실패 시 빈 값 또는 재시도 가능한 에러로 정규화한다

### 4.6 Review Engine Layer

- 역할
  - 질문 단계와 리뷰 단계를 분기
  - 리뷰 가능 상태에서 후속 분석 노드 실행
  - 결과를 최종 UI 계약으로 변환
- 내부 단계
  - Extract Brief
  - Validate Required Fields
  - Clarify Missing
  - Re-extract Brief
  - Re-validate Required Fields
  - Intent Alignment Review
  - Core Loop and Differentiation Review
  - MVP Scope and Playtest Plan Review
  - Direction Compare
  - Final Render Mapping

## 5. 배포 단위 기준 아키텍처

MVP에서는 아래 3개 단위만 있으면 된다.

### 5.1 Web App

- 기술
  - `Streamlit`
- 책임
  - UI 렌더링
  - 파일 업로드 수신
  - 세션 상태 유지
  - 버튼 이벤트 처리

### 5.2 App Service

- 기술
  - 파이썬 모듈
  - LangGraph 기반 메시지 중심 오케스트레이션
- 책임
  - 상태 전이
  - 정책 적용
  - LLM 호출 순서 제어

### 5.3 External LLM

- 기술
  - OpenAI chat model
- 책임
  - 자유형 텍스트를 구조화 필드로 변환
  - 리뷰 텍스트 생성

MVP에서는 API 서버를 별도 프로세스로 쪼개지 않는다. 필요해질 때만 `Frontend`와 `Backend API`를 분리한다.

## 6. 데이터 흐름

```text
1. User submits text or markdown file
2. UI normalizes it to raw_input
3. Application appends user message to session state
4. Extract Brief node fills structured fields
5. Validate Required Fields decides review_ready
6. If not review_ready:
   - UI renders clarifying questions
   - User answers
   - Application appends answers to messages
   - Extract and validate run again
7. If review_ready:
   - Review nodes generate diagnosis and directions
8. Final result is rendered in fixed sections
```

핵심은 질문 단계도 별도 임시 기능이 아니라 같은 세션 흐름 안의 정상 상태 전이라는 점이다.

## 7. 상태 모델

상태는 `LangGraph messages reducer + 구조화 필드 + 결과 필드` 혼합형으로 둔다.

```json
{
  "messages": [],
  "raw_input": "",
  "concept_statement": "",
  "target_player": "",
  "emotion_goal": "",
  "core_loop": "",
  "reward_structure": "",
  "differentiation_points": [],
  "feature_list": [],
  "development_window_weeks": 0,
  "team_composition": "",
  "mvp_goal": "",
  "test_audience": "",
  "constraints_note": "",
  "reference_titles": [],
  "missing_fields": [],
  "soft_missing_fields": [],
  "clarifying_questions": [],
  "review_ready": false,
  "intent_diagnosis": "",
  "core_loop_diagnosis": "",
  "scope_diagnosis": "",
  "playtest_hypothesis": "",
  "direction_options": [],
  "scope_recommendations": [],
  "playtest_questions": [],
  "final_summary": ""
}
```

### 상태 필드 분류

- 입력 원문
  - `raw_input`
  - `messages`
- 구조화 브리프
  - `concept_statement`
  - `target_player`
  - `emotion_goal`
  - `core_loop`
  - `reward_structure`
  - `differentiation_points`
  - `feature_list`
  - `development_window_weeks`
  - `team_composition`
  - `mvp_goal`
  - `test_audience`
  - `constraints_note`
  - `reference_titles`
- 제어 필드
  - `missing_fields`
  - `soft_missing_fields`
  - `clarifying_questions`
  - `review_ready`
- 결과 필드
  - `intent_diagnosis`
  - `core_loop_diagnosis`
  - `scope_diagnosis`
  - `playtest_hypothesis`
  - `direction_options`
  - `scope_recommendations`
  - `playtest_questions`
  - `final_summary`

## 8. 필드 계약

문서상 공통 계약은 내부적으로 `snake_case`를 기준으로 한다. feature 문서의 개별 설명도 이 계약을 따른다.

### 8.1 구조화 브리프 필드

| field | type | required level | meaning |
| --- | --- | --- | --- |
| `concept_statement` | `string` | soft | 게임 콘셉트 한 문장 |
| `target_player` | `string` | soft | 핵심 타깃 플레이어 |
| `emotion_goal` | `string` | hard | 플레이어에게 남기려는 감정 |
| `core_loop` | `string` | hard | 반복 플레이 흐름 |
| `reward_structure` | `string` | soft | 반복 동기를 만드는 보상 구조 |
| `differentiation_points` | `string[]` | optional | 차별화 포인트 목록 |
| `feature_list` | `string[]` | soft | 주요 기능 목록 |
| `development_window_weeks` | `integer` | optional | 개발 기간 주 단위 |
| `team_composition` | `string` | optional | 인원과 역할 요약 |
| `mvp_goal` | `string` | soft | 이번 MVP가 검증할 가설 |
| `test_audience` | `string` | optional | 플레이테스트 대상 |
| `constraints_note` | `string` | optional | 예산, 자산, 기술 제약 |
| `reference_titles` | `string[]` | optional | 비교 기준 레퍼런스 |

### 8.2 검증 등급

- `hard required`
  - `emotion_goal`
  - `core_loop`
- `soft required`
  - `target_player`
  - `reward_structure`
  - `mvp_goal`
  - `feature_list`
- `optional`
  - `reference_titles`
  - `development_window_weeks`
  - `team_composition`
  - `test_audience`
  - `constraints_note`
  - `differentiation_points`

### 8.3 검증 결과 규칙

- `hard required`가 비면 `mode=clarifying`로 전환하고 본 리뷰를 실행하지 않는다.
- `soft required`가 비면 리뷰는 실행하되, 질문 목록과 경고에 함께 표시한다.
- `optional`이 비어 있어도 리뷰는 진행한다.

### 8.4 질문 생성 규칙

- 첫 질문은 항상 `어떤 플레이어에게 어떤 감정을 주고 싶나요?`를 포함한다.
- `target_player`가 비어 있으면 첫 질문 묶음의 맨 앞에 둔다.
- `emotion_goal`, `core_loop` 질문은 hard block 해소용이므로 반드시 반환한다.

## 9. 프론트엔드 상태 전이

프론트엔드는 복잡한 상태머신 라이브러리까지는 필요 없다. 아래 4상태면 충분하다.

### 9.1 Idle

- 아직 입력 전

### 9.2 Extracting

- 추출 또는 재검증 실행 중
- 버튼 비활성화

### 9.3 Clarifying

- 필수값 부족
- 질문 폼 표시

### 9.4 Reviewed

- 최종 리뷰 표시 가능

이 전이는 `session_state["mode"]` 같은 단순 값으로 관리하면 충분하다.

## 10. 백엔드 오케스트레이션

### 10.1 표준 처리 흐름

```text
Normalize Input
-> Extract Brief
-> Validate Required Fields
-> if missing: Clarify Missing
-> Merge User Answers
-> Re-extract Brief
-> Re-validate Required Fields
-> Intent Alignment Review
-> Core Loop and Differentiation Review
-> MVP Scope and Playtest Plan Review
-> Direction Compare
-> Build Final Response
```

### 10.2 노드 계약

#### Extract Brief

- 입력
  - `raw_input` 또는 사용자 메시지
- 출력
  - `concept_statement`
  - `target_player`
  - `emotion_goal`
  - `core_loop`
  - `reward_structure`
  - `differentiation_points`
  - `feature_list`
  - `development_window_weeks`
  - `team_composition`
  - `mvp_goal`
  - `test_audience`
  - `constraints_note`
  - `reference_titles`

#### Validate Required Fields

- 입력
  - 구조화 브리프 필드
- 출력
  - `missing_fields`
  - `soft_missing_fields`
  - `clarifying_questions`
  - `review_ready`

#### Clarify Missing

- 입력
  - 사용자 추가 답변
  - 기존 `messages`
- 출력
  - 갱신된 `messages`
  - 필요 시 갱신된 `raw_input`

#### Intent Alignment Review

- 입력
  - `concept_statement`
  - `target_player`
  - `emotion_goal`
  - `reference_titles`
- 출력
  - `intent_diagnosis`
  - `soft_missing_fields` 기반 경고 메모

#### Core Loop and Differentiation Review

- 입력
  - `core_loop`
  - `reward_structure`
  - `feature_list`
  - `emotion_goal`
  - `differentiation_points`
- 출력
  - `core_loop_diagnosis`
  - 방향 초안에 들어갈 루프/차별화 근거 후보

#### MVP Scope and Playtest Plan Review

- 입력
  - `core_loop`
  - `feature_list`
  - `development_window_weeks`
  - `team_composition`
  - `mvp_goal`
  - `test_audience`
  - `constraints_note`
- 출력
  - `scope_diagnosis`
  - `scope_recommendations`
  - `playtest_hypothesis`
  - `playtest_questions`

#### Direction Compare

- 입력
  - `intent_diagnosis`
  - `core_loop_diagnosis`
  - `scope_diagnosis`
  - `scope_recommendations`
  - `playtest_hypothesis`
- 출력
  - `direction_options[2]`

#### Build Final Response

- 입력
  - 구조화 브리프 필드
  - 리뷰 노드 결과
  - `direction_options`
- 출력
  - 최종 UI 응답 계약 shape
## 11. UI 계약과 응답 계약

UI는 내부 상태 전체를 그대로 렌더링하지 않는다. 최종적으로는 아래 shape로 화면에 맞춘다.

```json
{
  "mode": "clarifying | reviewed",
  "questions": [
    {
      "field": "",
      "priority": "hard | soft",
      "question": ""
    }
  ],
  "brief": {
    "concept_statement": "",
    "target_player": "",
    "emotion_goal": "",
    "core_loop": "",
    "reward_structure": "",
    "differentiation_points": [],
    "feature_list": [],
    "development_window_weeks": 0,
    "team_composition": "",
    "mvp_goal": "",
    "test_audience": "",
    "constraints_note": "",
    "reference_titles": []
  },
  "diagnosis": {
    "intent": "",
    "core_loop": "",
    "scope": ""
  },
  "directions": [
    {
      "title": "",
      "reason": "",
      "tradeoff": ""
    },
    {
      "title": "",
      "reason": "",
      "tradeoff": ""
    }
  ],
  "scope": {
    "summary": "",
    "recommendations": []
  },
  "playtest_plan": {
    "hypothesis": "",
    "questions": [],
    "target_audience": ""
  },
  "final_summary": ""
}
```

### UI 규칙

- `mode=clarifying`이면 질문 입력 UI를 우선 렌더링한다.
- `mode=reviewed`이면 리뷰 블록을 전부 렌더링한다.
- `directions`는 항상 2개다.
- `brief`는 사용자가 AI 해석 결과를 바로 확인할 수 있게 항상 함께 보여준다.
- `questions`는 field와 priority를 같이 내려서 UI가 hard/soft 누락을 구분 표시할 수 있어야 한다.
- `playtest_plan`은 계획 생성이며, 테스트 후 회고 결과가 아니다.
## 12. 파일 업로드와 입력 정규화

입력 정규화는 별도 서비스로 과하게 뺄 필요 없다. 단일 함수면 충분하다.

- 입력 소스
  - textarea
  - `.md` file
- 규칙
  - 둘 다 입력되면 하나만 선택하게 막는다
  - 파일은 UTF-8 기준으로 읽고, 깨진 문자는 대체 문자로 처리한다
  - 최종 입력은 항상 하나의 `raw_input` 문자열로 통합한다
## 13. 오류 처리

### 사용자 오류

- 입력 없음
  - 실행 차단
- 텍스트와 파일 동시 입력
  - UI 경고

### 시스템 오류

- API 키 없음
  - 설정 오류 메시지 표시
- LLM 응답 파싱 실패
  - 재시도 또는 구조화 실패 메시지
- 리뷰 노드 일부 실패
  - 실패한 섹션만 비우고 나머지 표시하지 말고, 전체 리뷰 실패로 처리한다

MVP에서는 부분 성공보다 `명확한 실패`가 낫다.
## 14. 운영과 보안

### 운영

- 로컬 실행: `streamlit run app.py`
- 환경 변수: `OPENAI_API_KEY`
- 로그
  - 입력 원문 전체는 기본 로그에 남기지 않는다
  - 노드 성공/실패와 예외 종류만 남긴다

### 보안

- 업로드 파일은 메모리에서만 처리한다
- 장기 저장이 없으므로 개인정보 보존 리스크를 줄인다
- 프롬프트에 시스템 정책을 고정하고, 사용자 입력은 데이터로만 넣는다

## 14. 테스트 전략

### 단위 테스트

- 입력 정규화
- 필수값 검증
- 질문 생성
- 상태 전이

### 통합 테스트

- 정상 입력에서 `review_ready=True`
- `emotion_goal` 누락 시 질문 모드 진입
- `core_loop` 누락 시 질문 모드 진입
- 질문 답변 후 재추출/재검증을 거쳐 리뷰 모드 진입

### 수동 UI 시나리오

- 텍스트 붙여넣기
- `.md` 업로드
- 빈 입력 제출
- 질문 후 답변 제출
- 리뷰 결과 확인

## 15. 확장 기준

아래 조건이 생길 때만 구조를 더 쪼갠다.

- 세션 저장이 필요해질 때
  - DB 추가
- 여러 사용자가 동시에 써야 할 때
  - API 서버 분리
- 리뷰 시간이 길어질 때
  - 비동기 작업 큐 추가
- 리뷰 이력을 비교해야 할 때
  - 워크스페이스 모델 추가

지금 단계에서는 단일 웹 앱 + 세션 메모리 + LLM 호출만으로 충분하다.
