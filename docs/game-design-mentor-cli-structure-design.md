# 게임 기획 멘토 CLI 구조 설계

## 1. 목적

이 문서는 MVP 기획서를 파이썬 CLI 프로토타입 관점으로 다시 정리한 문서다. 현재 합의된 MVP는 `초보 인디 개발자용 일회성 리뷰 도구`다. 핵심은 아래 5가지를 먼저 고정하는 데 있다.

- 어떤 명령 흐름으로 `마크다운 입력 -> 구조화 추출 -> 필수 입력 검증 -> 질문 생성 -> 짧은 진단 -> 범위 점검 -> 플레이테스트 질문`을 구현할지
- LLM 자유 피드백과 구조화된 리뷰 로직을 어디서 나눌지
- 질문 중심 리뷰와 2개의 방향 제시를 어떤 규칙으로 묶을지
- 초보 인디 개발자에게 필요한 최소 시스템만 남길지
- 1주 프로토타입에서 꼭 필요한 최소 시스템만 남길지

이 문서는 기능 범위를 새로 정의하지 않는다. 제품 요구사항은 아래 문서를 따른다.

- [MVP Plan](./game-design-mentor-mvp-plan.md)
- [Feature 01. 기획 의도와 대상 플레이어 정렬 진단](./features/feature-01-concept-intake-and-player-intent-diagnosis.md)
- [Feature 02. 코어 루프와 차별화 포인트 리뷰](./features/feature-02-core-loop-and-differentiation-review.md)
- [Feature 03. MVP 범위와 플레이테스트 계획 점검](./features/feature-03-mvp-scope-and-playtest-plan-review.md)
- [Feature 04. 플레이테스트 회고와 다음 버전 제안](./features/feature-04-playtest-retrospective-and-next-version-plan.md)

## 2. 구조 설계 원칙

- 가장 먼저 지켜야 할 것은 `취향 평가 대신 의도 기준 리뷰`다.
- 자유형 마크다운을 코드가 직접 파싱하려 들지 않는다. 구조화는 LLM이, 검증은 코드가 맡는다.
- LLM은 구조화 추출과 리뷰 문장 생성을 맡고, 무엇을 점검할지는 코드가 고정한다.
- AI는 직접 고친 답안을 주기보다 `2개의 선택지와 트레이드오프`를 보여줘야 한다.
- 저장형 워크스페이스보다 `한 번 읽고 바로 다음 결정을 정하게 하는 응답`이 우선이다.
- 대상 플레이어는 권장 입력으로 두되, 비어 있으면 첫 질문에서 우선 확인한다.
- 첫 릴리스는 회고 누적이나 버전 비교를 미루고 리뷰 품질 자체를 검증한다.
- 첫 릴리스는 멀티에이전트 분배 대신 단일 extractor + validator + reviewer 흐름으로 시작한다.

## 3. CLI 구조 개요

CLI 전체는 아래 5개 층으로 보면 충분하다.

| 층 | 책임 | 포함 요소 |
| --- | --- | --- |
| Flow | 명령 상태 전환 | intake, extract, validate, clarify, review, scope |
| Extraction | 자유형 입력 구조화 | markdown extractor, schema normalizer |
| Template | 기획 템플릿과 리뷰 틀 | genre templates, checklist, playtest prompts |
| Analysis | 기획 정렬과 루프 검토 | intent checker, loop reviewer, scope reducer |
| Decision Support | 선택지 비교와 판단 보조 | option builder, tradeoff mapper, confidence flagger |
| Presentation | 터미널 출력 포맷 | question block, diagnosis block, direction block, scope block |

## 4. 명령과 상태 구조

### 4.1 권장 명령 구성

```text
game-mentor review draft.md
└── LoadMarkdown
    ├── ExtractToSchema
    ├── ValidateRequired
    ├── ClarifyMissing
    ├── MentorReview
    ├── DirectionCompare
    └── ScopePlan
```

첫 릴리스에서는 대화형 TUI를 만들지 않는다. 자유형 마크다운 파일을 읽고, 먼저 LLM이 표준 스키마로 정리한 뒤, 터미널에 질문, 진단, 방향, 테스트 질문까지 한 번에 출력하는 편이 더 빠르다.

### 4.2 런타임 상태 머신

```text
ConceptIntake
└── ClarifyMissing
    └── MentorReview
        ├── DecisionCompare
        └── DesignPlanning
```

### 4.3 상태 책임

- `ConceptIntake`: 게임 콘셉트, 대상, 감정 목표, 코어 루프 입력
- `ClarifyMissing`: 핵심 정보 누락 질문
- `MentorReview`: 정렬 불일치와 약점 진단
- `DecisionCompare`: 2개 방향과 트레이드오프 비교
- `DesignPlanning`: 코어 루프와 MVP 범위, 테스트 질문 정리

## 5. 질문과 리뷰 데이터 흐름

### 5.1 핵심 원칙

`LLM이 평가 기준을 정하지 않는다.`

CLI 코드는 아래를 한다.

- 마크다운 파일 로드
- LLM extractor 결과 파싱
- 필수 입력 검증
- 리뷰 섹션 구조 결정
- 출력 순서 고정

LLM은 아래를 한다.

- 자유형 마크다운을 표준 JSON 스키마로 추출
- 질문을 자연스럽게 표현
- 정렬 불일치 설명
- 루프 약점 문장화
- 2개의 해석 방향 생성
- 방향별 장단점 설명
- 플레이테스트 질문 제안

### 5.2 권장 흐름

```text
Project Template Select
-> Markdown File Input
-> LLM Extract To JSON
-> Required Field Check
-> Clarifying Questions (if needed)
-> Review Checklist Build
-> LLM Review Draft
-> Structured Review Formatter
-> Option / Tradeoff Compare
-> Scope Plan
-> Playtest Question Output
```

### 5.3 예시 마크다운 입력

```md
# Project
짧은 세션용 모바일 퍼즐 게임

## Target Player
짧은 세션에서 머리를 쓰는 모바일 플레이어

## Emotion Goal
작은 깨달음과 성취감

## Core Loop
문제 관찰 -> 규칙 실험 -> 퍼즐 해결 -> 다음 규칙 해금

## Features
- 힌트
- 챕터 선택
- 스킨 보상
```

### 5.4 추출 목표 JSON 스키마

```json
{
  "project_title": "",
  "concept_statement": "",
  "target_player": "",
  "emotion_goal": "",
  "core_loop": "",
  "feature_list": [],
  "reference_titles": [],
  "constraints_note": "",
  "raw_notes": ""
}
```

자유형 입력이라도 reviewer는 항상 이 구조를 기준으로 받는다. `emotion_goal`, `core_loop`는 본 리뷰 필수, `target_player`는 권장 필드다.

## 6. 핵심 시스템 구조

### 6.1 Template Layer

- `ProjectTypeCatalog`: 초보 인디 개발용 분류 우선
- `GenrePromptCatalog`: 퍼즐, 액션, 시뮬, 내러티브 등 장르별 질문 세트
- `ChecklistBuilder`: 프로젝트 타입과 장르에 맞는 점검 항목 생성

### 6.2 Extraction Layer

- `MarkdownLoader`: 기획 초안 파일 읽기
- `DraftExtractor`: 자유형 마크다운을 표준 JSON으로 정리
- `SchemaNormalizer`: 누락 필드를 빈 문자열/빈 배열로 정규화
- `ExtractionGuard`: JSON shape 검사 및 fallback 에러 처리

### 6.3 Design Analysis

- `IntentAlignmentChecker`: 대상 플레이어와 감정 목표 정렬 검토
- `CoreLoopReviewer`: 반복 구조와 보상 구조 검토
- `DifferentiationChecker`: 차별화 포인트와 실제 플레이 연결 검토
- `ScopeReducer`: 범위 축소와 검증 우선순위 제안

### 6.4 Validation Layer

- `RequiredFieldValidator`: `core_loop`, `emotion_goal` 본 리뷰 가능 여부 검사
- `OptionalFieldTracker`: `target_player` 누락 여부 기록
- `ClarificationPolicy`: 질문 모드 전환 조건 결정

### 6.5 Playtest Planning

- `PlaytestQuestionBuilder`: 테스트 질문 생성
- `ObservationPromptBuilder`: 테스트 때 무엇을 관찰해야 하는지 정리

### 6.6 Decision Support

- `OptionBuilder`: 해석 방향 2개 생성
- `TradeoffMapper`: 각 방향의 장점, 비용, 리스크 비교
- `ConfidenceFlagger`: 근거 약한 제안에 낮은 확신 표시

### 6.7 Presentation

- `QuestionFormatter`: 후속 질문 출력
- `DiagnosisFormatter`: 진단 결과 출력
- `DirectionFormatter`: 2개 방향과 트레이드오프 출력
- `ScopeFormatter`: MVP 범위와 테스트 계획 출력

## 7. CLI 역할 분리

### CLI 코드가 맡을 것

- 마크다운 파일 읽기
- LLM extractor 호출
- extractor JSON shape 검사
- 필수 입력 검증
- 리뷰 섹션 구조 고정
- 장르/프로젝트 템플릿 적용
- 질문 우선순위 결정
- 두 방향 출력 형식 고정

### LLM이 맡을 것

- 자유형 마크다운 구조화
- 질문 문장 생성
- 진단 설명
- 대안별 장단점 표현

멀티에이전트 분해는 이 단계에선 과하다. `extractor 1회 + reviewer 1회 + 파이썬 validator`가 가장 싸고 안정적이다.

## 8. 데이터 설계

### 8.1 권장 데이터 파일

- `genre_prompts.json`
- `review_checklists.json`
- `playtest_prompt_sets.json`
- `direction_frames.json`

### 8.2 저장 데이터

- 첫 릴리스는 저장 데이터를 필수 전제로 두지 않는다.
- 필요하면 세션 동안만 기획 브리프와 리뷰 결과를 임시 보관한다.

실시간 협업, 에셋 업로드, 버전 히스토리, 웹 UI는 MVP에서 생략해도 된다.

## 9. 1주 프로토타입 우선순위

### Must Have

- 초보 인디용 기본 템플릿
- 장르 질문 세트 4종
- 자유형 마크다운 -> JSON extractor
- required field validator
- 기획 의도 리뷰
- 코어 루프 리뷰
- 범위 축소 제안
- 플레이테스트 질문 생성

### Nice to Have

- 좋은 예시/나쁜 예시 비교
- 포트폴리오용 PDF 내보내기

### Skip for Now

- 저장형 워크스페이스
- 버전 비교 요약
- 플레이 영상 업로드
- 팀 실시간 협업
- 시장 데이터 연동
- 아트/사운드 평가

## 10. 기술 리스크와 대응

- 리스크: 피드백이 취향 비평으로 흐를 수 있다.  
  대응: 대상 플레이어와 감정 목표 기준 체크리스트로 시작한다.

- 리스크: 장르마다 질문이 달라 범위가 커질 수 있다.  
  대응: 장르별 템플릿은 4종만 두고 공통 구조를 유지한다.

- 리스크: 응답이 질문만 많고 방향성이 없을 수 있다.  
  대응: 정확히 2개의 해석 방향과 트레이드오프를 강제한다.

## 11. 추천 폴더 구조

```text
cli/
├── main.py
├── commands/
│   └── review.py
├── extract/
│   ├── draft_extractor.py
│   └── schema_normalizer.py
├── validate/
│   └── required_fields.py
├── formatters/
│   ├── questions.py
│   ├── diagnosis.py
│   ├── directions.py
│   └── scope.py
core/
├── templates/
├── review/
└── llm/
data/
├── genre_prompts.json
├── review_checklists.json
├── playtest_prompt_sets.json
└── direction_frames.json
```
