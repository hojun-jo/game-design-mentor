# Feature 01. 기획 의도와 대상 플레이어 정렬 진단

## 1. Idea Summary

게임 콘셉트, 대상 플레이어, 의도한 감정, 레퍼런스를 입력받고 이들이 실제로 같은 방향을 가리키는지 점검하는 기능이다.

## 2. Problem This Feature Solves

- 많은 기획 초안이 장르 이름만 있고 왜 존재하는지가 약하다.
- 대상 플레이어가 넓거나 감정 목표가 비어 있으면 뒤 리뷰도 흐려진다.
- 취향 감상문 대신 기준 있는 피드백이 필요하다.

## 3. Target User and Usage Context

- 게임 개발이 익숙하지 않은 초보 인디 개발자
- 첫 프로토타입 전에 콘셉트를 정리하려는 개인 개발자

## 4. Feature Concept Definition

### Feature name

기획 의도와 대상 플레이어 정렬 진단

### One-sentence definition

게임이 누구를 위한 무엇인지 먼저 확인하는 첫 번째 멘토링 기능이다.

### Why it matters

- 좋은 기획 리뷰는 메커닉보다 앞단을 먼저 본다.
- 감정 목표가 없으면 차별화도 흐려진다.
- 제품의 첫 질문 경험을 결정한다.

### Who uses it and when

- 프로젝트 시작 직후 사용한다.

### MVP relevance

- 우선순위: P0
- 이 기능이 없으면 제품이 일반적인 아이디어 칭찬 도구처럼 보인다.

### Confirmed requirements

- 첫 질문은 항상 `어떤 플레이어에게 어떤 감정을 주고 싶나요?`여야 한다.
- 대상 플레이어, 감정 목표, 콘셉트의 연결을 점검해야 한다.
- 누락 정보가 있으면 후속 질문을 반환해야 한다.
- `대상 플레이어`는 권장 입력으로 두되, 비어 있으면 리뷰 전에 질문으로 확인해야 한다.
- 질문은 사용자가 `누구를 위한 어떤 감정인가`를 스스로 좁히도록 돕는 교육형 질문이어야 한다.
- 진단은 대상과 감정이 맞는지 판단하는 기준을 함께 설명해야 한다.

### Assumptions to keep MVP narrow

- 하나의 핵심 타깃부터 검토한다.
- 레퍼런스는 3개 이내로 시작한다.
- 세계관 상세 설정은 MVP에서 깊게 다루지 않는다.

## 5. Main User Flow and Interaction Model

### Flow A. 콘셉트 입력

1. 사용자가 콘셉트와 대상 플레이어를 입력한다.
2. 시스템이 핵심 항목 누락을 검사한다.
3. AI가 후속 질문을 만든다.

### Flow B. 정렬 진단

1. 시스템이 대상, 감정, 콘셉트, 레퍼런스를 비교한다.
2. 모순과 모호한 표현을 표시한다.
3. 수정 제안을 보여준다.

## 6. Inputs, Outputs, and States

### Inputs

- 게임 콘셉트
- 대상 플레이어
- 감정 목표
- 레퍼런스

### Outputs

- 누락 질문
- 정렬 불일치 진단
- 수정 제안
- 대상/감정 정렬 판단 기준
- 다음 기획에서 반복할 자가 점검 질문

### Progress state fields

- `target_player`
- `emotion_goal`
- `concept_statement`
- `reference_titles[]`
- `soft_missing_fields[]`
- `mentor_questions[]`
- `mentor_principles[]`

## 7. Business Rules

- 대상 플레이어가 지나치게 넓으면 축소 질문을 먼저 한다.
- 감정 목표가 기능 설명으로만 되어 있으면 경고한다.
- 레퍼런스는 복제 대상이 아니라 비교 기준으로만 쓴다.
- 대상 플레이어가 비어 있어도 전체 리뷰는 막지 않지만, 첫 질문 우선순위는 가장 높게 둔다.
- 좋은 정렬 진단은 `대상`, `감정`, `콘셉트` 중 무엇이 기준이고 무엇이 흔들리는지 구분해야 한다.
- 질문 이유는 "정보가 부족해서"가 아니라 "판단 기준을 세우기 위해"로 설명한다.

## 8. Validation and Error Handling

- 감정 목표가 비면 본 리뷰 대신 질문 중심 응답으로 전환한다.
- 입력이 너무 짧으면 예시와 함께 재입력을 요청한다.
- 불확실할 때는 단정 대신 확인 질문을 우선한다.

## 9. Edge Cases and Resolved Decisions

### Edge cases

- 대상 플레이어가 두 개 이상 섞여 있는 경우
- 감정 목표와 장르 기대가 충돌하는 경우

### Resolved decisions

- MVP는 핵심 타깃 1개를 우선 정하게 한다.
- 충돌은 실패 판정이 아니라 설계 리스크로 표기한다.
- 대상 플레이어 부재만으로 본 리뷰를 막지는 않는다.

## 10. Product Implications and Dependencies

- [Feature 02. 코어 루프와 차별화 포인트 리뷰](./feature-02-core-loop-and-differentiation-review.md)가 이 단계 기준을 바탕으로 루프를 검토한다.
- [Feature 03. MVP 범위와 플레이테스트 계획 점검](./feature-03-mvp-scope-and-playtest-plan-review.md)가 목표 검증 방향을 이어받는다.

## 11. Recommendation and Next Decision

### Recommendation

초기 MVP는 아이디어를 많이 받기보다 약한 전제를 빨리 잡아내는 데 집중하는 편이 맞다.

### Next decisions

1. 감정 목표 예시를 장르별로 얼마나 다르게 둘지 정해야 한다.
2. 레퍼런스 입력을 자유 텍스트로 둘지 선택형도 줄지 정해야 한다.

## 12. MVP Acceptance Criteria

- 콘셉트 입력 후 정렬 진단을 받을 수 있다.
- 누락 정보가 있으면 후속 질문이 나온다.
- 대상 플레이어가 비어 있으면 첫 질문에서 이를 가장 먼저 확인한다.
- 수정 제안이 `문제`, `왜 문제인지`, `다음 수정안` 구조를 따른다.
- 질문마다 `learning_goal`과 `rationale`이 포함된다.
- 사용자가 다음 콘셉트를 점검할 수 있는 자가 질문을 최소 1개 받는다.

## 13. Out of Scope

- 세계관 위키 자동 생성
- 아트 방향 피드백
- 시장 매출 분석
