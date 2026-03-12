# 10. 직접 만들기

## 1. 최소 구현 순서

1. parser 선택
2. parsed output 샘플링
3. 전처리 규칙 설계
4. 청킹 규칙 설계
5. metadata schema 설계
6. 임베딩 입력 구성
7. vector DB 업로드
8. retrieval + rerank 구현
9. 평가셋 구축
10. 운영 전환

---

## 2. 최소 파일 구조 예시

```text
my-rag-project/
├── parsed/
├── chunking/
│   ├── chunks.all.jsonl
│   ├── chunks.primary.jsonl
│   └── chunks.secondary_table.jsonl
├── embeddings/
├── scripts/
│   ├── chunk_documents.py
│   ├── embed_chunks.py
│   ├── upload_qdrant.py
│   └── rerank.py
├── eval/
│   └── query-set.json
└── docs/
    ├── architecture.md
    ├── chunking.md
    └── operations.md
```

---

## 3. 최소 구현 질문

시작하기 전에 먼저 답해야 하는 질문:

- 내 문서는 구조가 중요한가?
- 표와 본문을 분리해야 하는가?
- 질문은 짧고 모호한가, 길고 구체적인가?
- exact keyword match가 중요한가?
- 결과를 사람이 직접 읽는가, LLM이 읽는가?

이 질문에 답하면 chunking과 retrieval 방식이 거의 정해진다.

---

## 4. 처음부터 너무 크게 하지 마라

처음엔 아래처럼 단순하게 시작해도 된다.

### v0
- 단일 parser
- 단일 청킹
- 단일 컬렉션
- dense retrieval

### v1
- metadata tagging 추가
- rerank 추가

### v2
- primary/secondary 분리
- 버킷형 query encoding
- 평가셋 운영

### v3
- 도메인 하네스 추가
- CRAG-style 재검색
- 컬렉션 병렬 운영

---

## 5. 가장 중요한 조언

- 데이터를 먼저 고쳐라.
- 청킹을 설명할 수 있어야 한다.
- 평가셋 없이 운영 전환하지 마라.
- 기존 컬렉션은 바로 지우지 마라.
- 문서화를 같이 하라.

---

## 6. 최종 한 줄

**좋은 RAG는 검색 모델의 성능보다, 문서를 어떻게 쪼개고 어떤 단위로 검색할지를 설계하는 능력에서 나온다.**
