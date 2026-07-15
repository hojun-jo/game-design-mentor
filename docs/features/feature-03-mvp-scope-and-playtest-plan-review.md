# Feature 03. MVP 범위와 플레이테스트 계획 점검

## 1. Idea Summary

현재 팀 규모와 개발 기간을 기준으로 기획 범위를 줄이고, 무엇을 먼저 플레이테스트로 검증해야 하는지 정리하는 기능이다.

## 2. Problem This Feature Solves

- 많은 기획이 재미보다 범위에서 먼저 무너진다.
- MVP가 무엇을 증명하려는지 없으면 개발 우선순위가 흐려진다.
- 플레이테스트 질문이 모호하면 회고도 약해진다.

## 3. Target User and Usage Context

- 첫 프로토타입 범위를 정해야 하는 초보 인디 개발자
- 혼자서 무엇을 빼고 무엇을 먼저 테스트할지 정해야 하는 개인 개발자

## 4. Feature Concept Definition

### Feature name

MVP 범위와 플레이테스트 계획 점검

### One-sentence definition

무엇을 먼저 만들고 무엇을 나중으로 미룰지, 그리고 무엇을 테스트해야 하는지 정리하는 기능이다.

### Why it matters

- 기획을 실제 실행으로 옮기는 다리다.
- 범위 축소는 기획 역량의 핵심이다.
- 테스트 질문이 좋아야 뒤 판단도 좋아진다.

### Who uses it and when

- 코어 루프를 정리한 뒤 개발 계획을 세울 때 사용한다.

### MVP relevance

- 우선순위: P0
- 이 기능이 없으면 멘토가 현실성을 다루지 못한다.

### Confirmed requirements

- 최소 1개의 핵심 검증 가설과 2개의 테스트 질문을 도출해야 한다.
- 현재 범위에서 제외할 항목을 제안할 수 있어야 한다.
- 팀 규모와 기간을 고려한 범위 피드백이 있어야 한다.
- 범위 점검은 긴 계획서보다 `지금 무엇을 빼야 하는지`를 짧게 보여주는 편이 우선이다.
- 범위 질문은 사용자가 `무엇을 만들 수 있는가`보다 `무엇을 먼저 배워야 하는가`를 판단하게 해야 한다.
- 플레이테스트 질문은 관찰 가능한 행동과 연결된 이유를 함께 설명해야 한다.

### Assumptions to keep MVP narrow

- 일정은 주 단위로 단순 입력한다.
- 인원은 역할 중심으로만 입력한다.
- 외주와 예산 관리는 MVP에서 깊게 다루지 않는다.

## 5. Main User Flow and Interaction Model

### Flow A. 범위 입력

1. 사용자가 기간, 인원, 기능 목록을 입력한다.
2. 시스템이 핵심 루프와 주변 기능을 구분한다.
3. AI가 과한 범위를 지적한다.

### Flow B. 테스트 계획 정리

1. 사용자가 검증하고 싶은 질문을 적는다.
2. AI가 테스트 질문과 관찰 포인트를 정리한다.
3. MVP 범위와 테스트 계획을 함께 출력한다.

## 6. Inputs, Outputs, and States

### Inputs

- 개발 기간
- 팀 인원
- 기능 목록
- MVP 목표
- 테스트 대상

### Outputs

- 범위 축소 제안
- 우선 검증 항목
- 플레이테스트 질문
- 범위 축소 판단 기준
- 첫 테스트에서 배워야 할 것의 요약

### Progress state fields

- `team_composition`
- `development_window_weeks`
- `feature_list[]`
- `mvp_goal`
- `test_audience`
- `playtest_hypothesis`
- `playtest_questions[]`
- `mentor_questions[]`
- `mentor_principles[]`

## 7. Business Rules

- 핵심 루프 검증과 직접 관련 없는 기능은 우선순위를 낮춘다.
- 테스트 질문은 관찰 가능한 행동으로 번역돼야 한다.
- 범위 축소는 단순 삭제가 아니라 검증 목적 유지와 함께 제안돼야 한다.
- 팀 규모나 일정이 비어 있어도 질문을 던지면서 임시 범위 축소 제안은 제공할 수 있어야 한다.
- 범위 축소 제안은 항상 어떤 학습 가설을 보호하는지 설명해야 한다.
- 테스트 질문은 "재미있었나요?" 같은 감상 질문보다 관찰 가능한 선택과 행동을 우선한다.

## 8. Validation and Error Handling

- 일정이나 인원 정보가 비면 보수적 가정 위에서 임시 범위 제안을 하고, 추가 질문을 함께 던진다.
- 기능 목록이 너무 넓으면 분류 질문을 먼저 던진다.
- 테스트 목표가 모호하면 관찰 질문 예시를 제공한다.

## 9. Edge Cases and Resolved Decisions

### Edge cases

- 팀은 작지만 재사용 가능한 기존 코드가 있는 경우
- 플레이테스트 없이 내부 감으로만 진행하려는 경우

### Resolved decisions

- MVP는 기존 자산 여부를 추가 질문으로만 확인한다.
- 테스트 계획이 없으면 제출 전에 경고한다.

## 10. Product Implications and Dependencies

- [Feature 02. 코어 루프와 차별화 포인트 리뷰](./feature-02-core-loop-and-differentiation-review.md)가 핵심 루프 우선순위를 제공한다.
- [Feature 04. 플레이테스트 회고와 다음 버전 제안](./feature-04-playtest-retrospective-and-next-version-plan.md)는 후속 단계에서 이 단계 테스트 계획을 회고 기준으로 사용한다.

## 11. Recommendation and Next Decision

### Recommendation

초기 MVP는 정교한 일정 추정기보다 `뭘 빼야 하는지`와 `뭘 테스트해야 하는지`를 잘 말해 주는 편이 낫다.

### Next decisions

1. 범위 축소 제안을 역할별로 나눌지 기능군별로 나눌지 정해야 한다.
2. 테스트 계획 템플릿을 장르별로 분화할지 정해야 한다.

## 12. MVP Acceptance Criteria

- 범위 축소 제안을 받을 수 있다.
- 핵심 검증 가설과 테스트 질문을 도출할 수 있다.
- 최소 2개의 플레이테스트 질문을 짧은 리뷰 응답 안에 포함할 수 있다.
- 각 플레이테스트 질문에는 무엇을 배우기 위한 질문인지가 포함된다.
- 사용자가 다음 MVP 범위를 정할 때 쓸 수 있는 자가 점검 질문이 포함된다.

## 13. Out of Scope

- 상세 스프린트 스케줄러
- 예산 산정기
- QA 버그 추적 시스템
