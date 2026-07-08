# Feature 04. 플레이테스트 회고와 다음 버전 제안

## 1. Idea Summary

플레이테스트 메모, 관찰 결과, 버전 변경 기록을 받아 초기 의도와 비교하고 다음 버전에서 무엇을 바꿔야 할지 제안하는 기능이다. 다만 현재 합의된 첫 릴리스에는 포함하지 않고 후속 확장 단계로 둔다.

## 2. Problem This Feature Solves

- 많은 팀이 플레이테스트를 해도 배운 점을 다음 버전에 제대로 옮기지 못한다.
- 감상과 관찰이 섞이면 회고가 흔들린다.
- 한 번의 테스트 결과를 과하게 일반화하는 실수가 잦다.

## 3. Target User and Usage Context

- 첫 릴리스 이후 회고 기능이 필요해진 초보 인디 개발자
- 반복 테스트 루프를 구조화하려는 후속 사용자

## 4. Feature Concept Definition

### Feature name

플레이테스트 회고와 다음 버전 제안

### One-sentence definition

플레이 후 얻은 관찰을 다음 수정안으로 연결하는 기능이다.

### Why it matters

- 장기적으로는 기획 멘토의 완성 단계다.
- 반복 개선 도구로서의 가치는 여기서 나온다.
- 버전 변화 학습을 남길 수 있다.

### Who uses it and when

- 플레이테스트 직후 또는 주간 회고 시 사용한다.

### MVP relevance

- 우선순위: P2
- 첫 릴리스에서는 제외한다. 현재 MVP는 플레이테스트 질문 생성까지를 범위로 둔다.

### Confirmed requirements

- 플레이테스트 결과와 초기 의도를 비교해야 한다.
- 다음 수정안이 구체적 행동 항목으로 나와야 한다.
- 관찰과 해석을 구분해 다뤄야 한다.
- 이 기능은 질문 중심 리뷰 품질이 검증된 뒤 다음 단계로 붙인다.

### Assumptions to keep MVP narrow

- 테스트 결과는 텍스트와 숫자 메모로 입력한다.
- 버전 비교는 직전 버전 1개까지만 본다.
- 영상과 로그 자동 분석은 하지 않는다.

## 5. Main User Flow and Interaction Model

### Flow A. 회고 입력

1. 사용자가 관찰 메모와 플레이어 반응을 입력한다.
2. 시스템이 기존 테스트 질문과 연결한다.
3. AI가 회고 초안을 만든다.

### Flow B. 다음 버전 제안

1. 초기 의도와 실제 반응 차이를 본다.
2. 원인 후보와 수정 우선순위를 본다.
3. 다음 버전 액션 항목을 확정한다.

## 6. Inputs, Outputs, and States

### Inputs

- 테스트 메모
- 이탈 지점
- 플레이어 반응
- 버전 변경 기록

### Outputs

- 회고 요약
- 원인 후보
- 다음 버전 수정안

### Progress state fields

- `observationNotes[]`
- `dropOffPoints[]`
- `playerQuotes[]`
- `nextActions[]`

## 7. Business Rules

- 회고는 초기 의도와 테스트 질문 기준 위에서 해석한다.
- 관찰 메모가 부족하면 강한 결론 대신 추가 테스트를 권한다.
- 다음 수정안은 실행 가능한 항목 수로 제한한다.

## 8. Validation and Error Handling

- 테스트 질문이 없으면 회고 전에 기준 수립을 요청한다.
- 관찰 없이 감상만 있으면 추가 사실 입력을 요청한다.
- 버전 기록이 비면 현재 결과만 기준으로 제한된 회고를 제공한다.

## 9. Edge Cases and Resolved Decisions

### Edge cases

- 플레이어 반응이 서로 상반되는 경우
- 개선은 있었지만 왜 좋아졌는지 불명확한 경우

### Resolved decisions

- MVP 이후 단계에서는 상반된 반응을 분리 표기하고 공통 패턴만 추린다.
- 확신이 낮을 때는 원인 확정보다 다음 실험안을 우선 제안한다.

## 10. Product Implications and Dependencies

- [Feature 03. MVP 범위와 플레이테스트 계획 점검](./feature-03-mvp-scope-and-playtest-plan-review.md)가 테스트 질문과 검증 가설을 제공한다.
- [Feature 01. 기획 의도와 대상 플레이어 정렬 진단](./feature-01-concept-intake-and-player-intent-diagnosis.md)이 초기 의도 기준을 제공한다.

## 11. Recommendation and Next Decision

### Recommendation

첫 릴리스는 플레이테스트를 요약하지 말고 `나중에 무엇을 테스트해야 하는지`를 잘 묻는 데 집중하는 편이 낫다.

### Next decisions

1. 다음 액션 항목 수를 3개 이하로 제한할지 정해야 한다.
2. 버전 비교 요약을 표로 보여줄지 문장으로 보여줄지 정해야 한다.

## 12. MVP Acceptance Criteria

- 현재 첫 릴리스 범위에는 포함하지 않는다.
- 질문 중심 리뷰 품질이 검증된 뒤 다시 포함 여부를 평가한다.

## 13. Out of Scope

- 플레이 영상 자동 태깅
- 세션 리플레이 분석
- 팀 협업 코멘트 시스템
