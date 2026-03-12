# 09. 운영과 유지보수

## 1. 운영형 RAG의 관점

RAG는 한번 만들어 놓고 끝나는 시스템이 아니다.
실제로는 다음을 반복 관리해야 한다.

- 문서 추가/변경
- parser 교체
- 청킹 규칙 보정
- metadata schema 변경
- collection 교체
- 평가셋 재검증

---

## 2. 권장 버전 전략

### 하지 말아야 할 것
- 기존 컬렉션 즉시 삭제
- 새 컬렉션 덮어쓰기

### 권장 방식
- `v1`, `v2`, `v3` 유지
- 새 버전은 새 컬렉션에 업로드
- 테스트 후 기본 env 전환
- 충분히 안정화되면 오래된 버전 정리

---

## 3. env와 설정 관리

Qdrant URL, API key, 기본 컬렉션명은 env로 관리하는 게 좋다.

예:
```env
QDRANT_URL=...
QDRANT_API_KEY=...
QDRANT_COLLECTION_NAME=saju_v3_primary_core
```

장점:
- 스크립트 하드코딩 방지
- 테스트 env 분리 가능
- 임시 비교 컬렉션 쉽게 운용 가능

---

## 4. 운영 중 자주 생기는 문제

### parser 바뀌면 payload schema가 달라진다
해결:
- content/text/title 필드 fallback 지원

### id 포맷이 달라진다
해결:
- int 전제 금지
- string/UUID 허용

### 검색 품질이 갑자기 떨어진다
해결:
- 최근 업로드분의 chunk distribution 점검
- 추천 청크 비율 점검
- 평가셋 비교 재실행

---

## 5. 유지보수 체크리스트

- [ ] parser 출력 품질 샘플링
- [ ] 청킹 수량 확인
- [ ] low-value/drop 비율 점검
- [ ] primary/core 비율 점검
- [ ] table dominance 재점검
- [ ] rerank 규칙 회귀 확인
- [ ] 실제 사용자 질문으로 종단 테스트

---

## 6. 문서화도 운영의 일부다

운영형 RAG는 코드만 있으면 안 된다.
최소한 다음 문서는 있어야 한다.

- 아키텍처 설명
- 청킹 전략 문서
- 평가 방법 문서
- 컬렉션 버전 기록
- 장애 대응 메모

이 문서가 없으면, 시간이 지나면 누가 왜 이렇게 만들었는지 아무도 모르게 된다.
