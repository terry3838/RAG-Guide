# 11. 학습 노트 — 실제로 한 일과 얻은 결과

## 1. 프로젝트 한 줄 소개

이 프로젝트에서 나는 **도메인 특화 RAG 시스템의 검색 품질을 개선하는 작업**을 했다. 핵심은 단순히 벡터 DB를 붙이는 것이 아니라, **문서 전처리 → 하이브리드 청킹 → 임베딩 → Qdrant 인덱싱 → rerank → 하네스 개선 → 평가/검증**까지 전체 retrieval 파이프라인을 손본 것이다.

---

## 2. 내가 실제로 한 일

### 2.1 문서 전처리 파이프라인 정리
- Upstage Document Parse 결과물을 기반으로 문서 구조를 읽을 수 있는 형태로 정리했다.
- parser 결과에 섞여 있던 목차, 그림 목록, 표 목록, 판권, placeholder 이미지, 저가치 도입부를 걸러냈다.
- 단순 OCR 텍스트가 아니라 **문서 구조를 보존한 parsed output**을 canonical source로 사용했다.

### 2.2 하이브리드 청킹 설계
- 단순 semantic chunking 대신 **문서 구조 기반 하이브리드 청킹**을 적용했다.
- heading / paragraph / table 구조를 기준으로 1차 분할하고,
- 그 위에 규칙 기반 후처리와 도메인 태깅을 얹었다.
- 추가로:
  - `doc_type`
  - `topics`
  - `is_myeongsik_chunk`
  - `embedding_recommended`
  같은 메타데이터를 붙였다.

### 2.3 임베딩 및 Qdrant 재색인
- Upstage `embedding-query` 모델로 청크를 임베딩했다.
- 기존 raw 중심 컬렉션 대신 새 컬렉션을 병렬로 만들었다.
- 운영 전략은:
  - `saju_v2_curated`
  - `saju_v3_primary_core`
  처럼 버전 컬렉션을 나눠 구축하고, 비교 후 전환하는 방식으로 가져갔다.

### 2.4 Qdrant 리트리벌 / 리랭커 수정
- 질문도 임베딩해서 dense retrieval을 수행하도록 구성했다.
- 그 위에 lexical overlap, topic bonus, section bonus, table penalty, metadata-aware rerank를 추가했다.
- UUID 기반 point id 때문에 기존 리랭커가 깨지는 문제를 찾아 수정했다.
- payload schema가 달라져도 `content/text/title/section_title`를 fallback으로 읽도록 개선했다.

### 2.5 컬렉션 분리 전략 도입
- 본문/사례 중심 primary 컬렉션과 표/조견표 중심 secondary 컬렉션 개념을 도입했다.
- 실제로 core-primary 컬렉션을 따로 구축해서 **table dominance 문제를 줄였다.**

### 2.6 도메인 하네스 검증
- 실제 도메인 질의(사주 해석)로 종단 테스트를 수행했다.
- 단순히 검색 결과만 보는 게 아니라,
  - 근거가 읽히는지
  - 일반론 반복이 줄었는지
  - 실제 답변에 evidence가 반영되는지
  까지 확인했다.

---

## 3. 이 작업에서 해결하려고 했던 문제

처음 상태의 문제는 이랬다.

- raw chunk가 너무 많았다.
- 같은 source가 반복됐다.
- 표 chunk가 상위권을 점령했다.
- 질문 의도와 안 맞는 일반론이 자주 검색됐다.
- exact domain match보다 이상한 근접 사례가 먼저 떴다.
- 리랭커가 UUID id를 처리하지 못했다.

즉 문제의 본질은 모델이 아니라,
**데이터 구조, 청킹 전략, payload schema, retrieval 후처리**에 있었다.

---

## 4. 내가 배운 핵심 교훈

### 4.1 RAG는 프롬프트보다 데이터 설계가 먼저다
처음엔 질문 프롬프트나 답변 프롬프트를 손보는 게 중요해 보이지만,
실제로는 **문서 전처리와 청킹 설계**가 훨씬 더 큰 영향을 줬다.

### 4.2 semantic chunking만으로는 부족하다
도메인 문서, 특히 표/조견표/사례가 많은 문서는
**document structure-aware chunking**이 훨씬 중요했다.

### 4.3 dense retrieval만으로는 운영 품질이 안 나온다
질문과 청크를 임베딩해서 벡터 검색만 해도 어느 정도는 되지만,
실제 운영 수준으로 가려면 반드시 **rerank**가 필요했다.

### 4.4 metadata가 retrieval 품질을 크게 바꾼다
`doc_type`, `topics`, `is_myeongsik_chunk` 같은 metadata를 붙이고,
그걸 rerank에 반영하자 품질이 눈에 띄게 좋아졌다.

### 4.5 컬렉션은 병렬 버전 운영이 맞다
기존 컬렉션을 바로 삭제하지 않고,
새 버전을 병렬로 만들고 비교 후 전환하는 방식이 훨씬 안전했다.

---

## 5. 실제로 얻은 개선 결과

### 개선 전
- placeholder/빈 chunk/목차성 텍스트가 많이 검색됨
- 표가 너무 자주 상위 결과에 노출됨
- v1은 source 반복이 심하고 읽을 수 있는 evidence가 약했음

### 개선 후
- 본문/사례 중심 evidence가 상위에 더 잘 올라옴
- `辰辰 자형`, `화개살`, `역마살` 같은 구조 질의에서 설명형 근거가 더 잘 잡힘
- UUID 문제와 payload schema 문제를 해결해서 하네스 안정성이 올라감
- core-primary 컬렉션 도입으로 표 dominance가 줄어듦

---

## 6. 이번 작업을 한 문단으로 요약하면

이 작업의 핵심은 도메인 특화 RAG 시스템에서 검색 품질을 떨어뜨리던 병목을 ingestion과 retrieval 양쪽에서 동시에 줄인 것이다. parser 기반 구조 추출 이후 하이브리드 청킹과 메타데이터 태깅을 적용했고, Upstage 임베딩과 Qdrant 재색인을 통해 컬렉션을 버전별로 재구축했다. 이후 dense retrieval 위에 lexical/metadata-aware rerank를 얹고, UUID 및 payload schema 문제를 수정해 실제 도메인 질의에서 더 읽을 수 있는 근거가 상위에 오도록 개선했다.

---

## 7. 내가 한 일을 키워드로 요약하면

- RAG pipeline design
- document parsing
- hybrid chunking
- domain metadata tagging
- embedding pipeline
- Qdrant indexing
- retrieval quality improvement
- metadata-aware reranking
- evaluation and regression testing
- domain-specific harness design
