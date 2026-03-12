# 06. Reranking과 Harness 설계

## 1. rerank가 필요한 이유

dense retrieval은 후보를 넓게 가져오는 데는 좋지만, 최종 검색 결과 품질은 대부분 rerank에서 갈린다.

rerank가 하는 일:
- lexical overlap 반영
- exact term hit 반영
- section/title 가중치 반영
- metadata bonus/penalty 반영
- 중복 감점

---

## 2. hybrid rerank의 구성

실전적인 rerank score 예시:

```text
final_score =
  alpha * semantic_score
+ beta  * lexical_score
+ exact_bonus
+ topic_bonus
+ section_bonus
+ domain_bonus
- table_penalty
- duplicate_penalty
```

---

## 3. metadata-aware rerank

도메인 특화 RAG는 메타데이터를 점수에 반영해야 한다.

예:
- `doc_type == table` → 감점
- `is_myeongsik_chunk == true` → 가점
- `embedding_recommended == true` → 가점
- `topics`가 질문과 맞으면 → 가점
- `section_title`가 질문 키워드 포함하면 → 가점

---

## 4. harness의 역할

harness는 단순 검색기가 아니다.
검색과 재검색, 근거 조립, 최종 답변 포맷을 관리한다.

즉 harness는:
- 질문 의도 분류
- 버킷별 query 생성
- Qdrant 호출
- rerank
- CRAG-style 재검색
- 최종 evidence 정리
를 하나의 흐름으로 묶는다.

---

## 5. 버킷형 검색

복합 질문을 한 줄로만 검색하면 일반론이 많이 뜬다.
그래서 버킷을 나눈다.

예:
- 격국
- 관계(합/충/형/파/해)
- 신살
- 십이운성
- 대운/세운
- 특정 주제(직업, 재물 등)

이 방식은 도메인 RAG에서 특히 중요하다.

---

## 6. CRAG-style 재검색

1차 검색이 약하면 재검색 조건을 발동한다.

재검색 트리거 예:
- 같은 source 반복
- table만 반복
- direct evidence 부족
- 일반론만 상위에 반복
- exact key 미매칭

재검색 액션 예:
- query rewrite
- source 제한
- primary/core 컬렉션 우선
- secondary table 컬렉션은 보조로만 사용

---

## 7. Mermaid: harness 내부 흐름

![Diagram 1](../assets/diagrams/sections__06-reranking-harness__diagram_1.svg)

---

## 8. 운영 팁

- rerank 결과에는 이유가 보여야 한다.
- `doc_type`, `topics`, `section_title`를 로그로 남겨라.
- UUID id를 int로 강제 변환하지 마라.
- qdrant env를 하드코딩보다 주입 가능하게 만들어라.
