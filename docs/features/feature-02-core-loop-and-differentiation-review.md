# Feature 02. 코어 루프와 차별화 포인트 리뷰

## 1. Idea Summary

사용자가 적은 코어 루프, 주요 시스템, 보상 구조를 바탕으로 반복 플레이 가치와 차별화 포인트를 검토하는 기능이다.

## 2. Problem This Feature Solves

- 기능 목록이 많아도 반복 재미가 없으면 게임이 약하다.
- 차별화 포인트가 슬로건 수준이면 실제 설계 판단에 도움이 안 된다.
- 메커닉끼리 연결되지 않으면 개발만 복잡해진다.

## 3. Target User and Usage Context

- 핵심 루프를 처음 구조화하는 초보 인디 개발자
- 프로토타입 이전 설계를 점검받고 싶은 개인 개발자

## 4. Feature Concept Definition

### Feature name

코어 루프와 차별화 포인트 리뷰

### One-sentence definition

플레이가 왜 반복될 가치가 있는지와 무엇이 이 게임을 구분 짓는지 검토하는 기능이다.

### Why it matters

- 게임 기획의 중심이다.
- 반복 구조가 약하면 나머지 시스템도 힘을 잃는다.
- 차별화 포인트를 실제 플레이 경험과 묶어야 한다.

### Who uses it and when

- 콘셉트 정렬 후 설계를 구체화할 때 사용한다.

### MVP relevance

- 우선순위: P0
- 이 기능이 없으면 제품이 설정 검토 도구에 머문다.

### Confirmed requirements

- 코어 루프의 시작, 반복, 보상 구조를 분리해 검토해야 한다.
- 차별화 포인트가 실제 플레이 경험과 연결되는지 설명해야 한다.
- 기능 나열과 루프 설명을 구분해야 한다.
- 코어 루프 리뷰 결과는 `짧은 진단` 형태로 요약돼야 한다.
- 리뷰는 정확히 2개의 해석 방향을 제시하고, 각 방향에 근거와 트레이드오프를 붙여야 한다.
- 루프 진단은 사용자가 `행동 -> 피드백 -> 보상 -> 다음 선택` 관계를 배우게 해야 한다.
- 차별화 질문은 "새로운가"보다 "플레이 경험에서 어떻게 달라지는가"를 묻게 해야 한다.

### Assumptions to keep MVP narrow

- 코어 루프는 3~5단계 서술로 받는다.
- 경제 시스템과 라이브 운영은 MVP에서 깊게 다루지 않는다.
- 전 장르 공통 구조를 우선하고 세부 장르 규칙은 얕게 둔다.

## 5. Main User Flow and Interaction Model

### Flow A. 루프 입력

1. 사용자가 코어 루프와 주요 시스템을 입력한다.
2. 시스템이 루프 단계와 보상 구조를 분리한다.
3. AI가 연결 약점을 찾는다.

### Flow B. 차별화 리뷰

1. 사용자가 차별화 포인트와 레퍼런스를 적는다.
2. AI가 실제 플레이 경험과 연결되는지 검토한다.
3. AI가 짧은 진단과 2개의 해석 방향을 보여준다.

## 6. Inputs, Outputs, and States

### Inputs

- 코어 루프
- 주요 시스템
- 보상 구조
- 차별화 포인트

### Outputs

- 루프 약점 진단
- 반복성 피드백
- 2개의 해석 방향
- 루프/보상 판단 기준
- 루프를 다시 점검할 성찰 질문

### Progress state fields

- `core_loop`
- `reward_structure`
- `differentiation_points[]`
- `core_loop_diagnosis`
- `mentor_questions[]`
- `mentor_principles[]`

## 7. Business Rules

- 코어 루프는 플레이어 행동과 보상 관계로 설명돼야 한다.
- 차별화 포인트는 미학 문구가 아니라 경험 차이로 설명돼야 한다.
- 루프에 없는 기능은 우선순위를 낮춘다.
- 진단은 기능을 늘리는 방향보다 반복 구조를 선명하게 하는 방향을 우선한다.
- 질문은 사용자가 직접 루프 단계 사이의 인과관계를 설명하게 만들어야 한다.

## 8. Validation and Error Handling

- 루프 설명이 너무 짧으면 단계 분해 질문을 먼저 한다.
- 보상 구조가 비면 반복 동기 질문을 반환한다.
- 차별화 포인트가 레퍼런스 이름뿐이면 추가 설명을 요청한다.
- 코어 루프가 비면 본 리뷰 대신 질문 중심 응답으로 전환한다.

## 9. Edge Cases and Resolved Decisions

### Edge cases

- 의도적으로 단조로운 경험을 노리는 미니멀 게임인 경우
- 차별화 포인트가 메커닉보다 테마에서 나오는 경우

### Resolved decisions

- MVP는 장르 의도를 먼저 확인하고 같은 잣대를 강요하지 않는다.
- 테마 차별화도 플레이 경험 연결이 없으면 약점으로 본다.

## 10. Product Implications and Dependencies

- [Feature 01. 기획 의도와 대상 플레이어 정렬 진단](./feature-01-concept-intake-and-player-intent-diagnosis.md)이 대상과 감정 기준을 제공한다.
- [Feature 03. MVP 범위와 플레이테스트 계획 점검](./feature-03-mvp-scope-and-playtest-plan-review.md)가 루프 우선순위를 바탕으로 범위를 줄인다.

## 11. Recommendation and Next Decision

### Recommendation

초기 MVP는 새로움 평가보다 반복성 검토를 더 강하게 보는 편이 실무적이다.

### Next decisions

1. 장르별 루프 예시를 얼마나 제공할지 정해야 한다.
2. 차별화 포인트를 텍스트 외 태그형 입력도 받을지 정해야 한다.

## 12. MVP Acceptance Criteria

- 코어 루프 약점을 진단할 수 있다.
- 차별화 포인트를 플레이 경험 기준으로 다시 설명할 수 있다.
- 기능 나열과 루프 설명을 구분해 피드백할 수 있다.
- 2개의 해석 방향과 각 방향의 근거, 트레이드오프를 보여줄 수 있다.
- 코어 루프를 판단한 설계 원칙이 최소 1개 포함된다.
- 사용자가 자기 루프를 다시 검토할 수 있는 성찰 질문이 포함된다.

## 13. Out of Scope

- 상세 전투 수치 밸런싱
- 라이브 서비스 경제 분석
- 코드 구조 리뷰
