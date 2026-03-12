# 학습 경로

이 문서는 RAG를 처음 배우는 사람부터, 실제 운영형 검색 시스템을 설계하려는 사람까지 단계별 학습 경로를 제안한다.

---

## 1. 초급 경로 — RAG의 전체 흐름 이해하기

### 목표
- RAG가 왜 필요한지 이해한다.
- 임베딩, 벡터DB, 청킹, 리랭킹의 역할을 구분한다.

### 읽을 문서
1. `README.md`
2. `sections/01-rag-overview.md`
3. `02-glossary.md`
4. `sections/05-qdrant-retrieval.md`

### 체크포인트
- 임베딩이 뭔지 설명할 수 있는가?
- 검색과 생성이 왜 분리되어야 하는지 설명할 수 있는가?
- dense retrieval과 rerank의 차이를 설명할 수 있는가?

---

## 2. 중급 경로 — 문서 전처리와 청킹 설계

### 목표
- 왜 청킹이 retrieval 품질의 핵심인지 이해한다.
- semantic chunking과 structure-aware chunking의 차이를 설명할 수 있다.

### 읽을 문서
1. `sections/02-document-parsing.md`
2. `sections/03-hybrid-chunking.md`
3. `sections/04-embedding-indexing.md`

### 체크포인트
- parser 결과를 바로 vector DB에 넣으면 왜 문제가 생기는가?
- 본문/표/목차/부록을 왜 분리해야 하는가?
- 도메인 메타데이터가 왜 retrieval 품질을 끌어올리는가?

---

## 3. 고급 경로 — 검색 품질 개선과 운영

### 목표
- 컬렉션 분리, 리랭킹, 평가셋, 운영 전환 전략까지 이해한다.
- “좋아진 것 같음”이 아니라 측정 가능한 검증 루프를 만들 수 있다.

### 읽을 문서
1. `sections/06-reranking-harness.md`
2. `sections/07-evaluation-debugging.md`
3. `sections/09-ops-and-maintenance.md`
4. `sections/10-build-your-own.md`

### 체크포인트
- table dominance 문제를 어떻게 해결할지 설명할 수 있는가?
- v1/v2/v3 컬렉션 운영 전환 방식을 설계할 수 있는가?
- 하네스가 UUID id, metadata payload, source filtering을 지원해야 하는 이유를 설명할 수 있는가?

---

## 4. 도메인 특화 경로 — 사주/전문지식 RAG

### 목표
- 일반 도메인이 아니라, 특정 전문 분야에서 구조화된 retrieval을 만드는 법을 이해한다.
- 질문 인코딩, 도메인 버킷 검색, 근거 문장 조립 방식을 익힌다.

### 읽을 문서
1. `sections/08-saju-case-study.md`
2. `sections/06-reranking-harness.md`
3. `sections/07-evaluation-debugging.md`

### 체크포인트
- 왜 전문 분야일수록 청킹보다 metadata 설계가 더 중요해지는가?
- 왜 exact match와 semantic match를 함께 봐야 하는가?
- 왜 direct evidence 0건을 명시하는 게 중요한가?

---

## 5. 학습/연구 정리 경로

### 목표
- 내가 실제로 무엇을 했는지 구조적으로 정리할 수 있다.
- 왜 그렇게 설계했는지 기술적으로 설명할 수 있다.
- 무엇이 개선됐는지 정량/정성으로 정리할 수 있다.

### 읽을 문서
1. `sections/11-study-notes-and-results.md`
2. `sections/12-research-playbook.md`
3. `sections/13-harness-engineering.md`
4. `sections/14-code-walkthrough.md`
5. `sections/07-evaluation-debugging.md`

---

## 6. 가장 빠른 실전 루트

시간 없으면 이것만 읽어도 된다.

1. `sections/03-hybrid-chunking.md`
2. `sections/05-qdrant-retrieval.md`
3. `sections/06-reranking-harness.md`
4. `sections/07-evaluation-debugging.md`
5. `sections/11-study-notes-and-results.md`
6. `sections/13-harness-engineering.md`

이 6개만 읽어도:
- 문서를 어떻게 자를지
- 어떻게 임베딩할지
- 어떻게 검색할지
- 어떻게 품질을 검증할지
- 내가 실제로 무엇을 했는지
- 하네스를 어떻게 설계했는지
대강 감이 잡힌다.
