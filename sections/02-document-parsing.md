# 02. Document Parsing

## 1. 왜 parsing이 먼저인가

RAG 문제의 절반은 사실 검색보다 더 앞단, 즉 **문서가 어떤 형태로 추출되었는가**에서 이미 결정된다.

특히 다음 문서들은 단순 텍스트 추출로 망가지기 쉽다.
- PDF
- 스캔본
- 표가 많은 문서
- 머리말/꼬리말이 반복되는 책
- 그림/캡션/목차/조견표가 섞인 도메인 문서

이런 경우 parser는 단순 OCR이 아니라 **문서 구조 추출기** 역할을 해야 한다.

---

## 2. parser가 잘해야 하는 것

### 필수 출력
- heading
- paragraph
- list
- table
- caption
- page
- coordinates(가능하면)

### 좋은 parser의 특징
- 본문과 표를 구분한다.
- heading 계층을 보존한다.
- 페이지 단위를 유지한다.
- 스캔 문서에서도 구조를 최대한 복원한다.

---

## 3. Upstage Document Parse를 기준으로 한 구조

실전에서 Upstage Document Parse는 다음 강점이 있다.

- PDF/스캔/차트/표 입력 가능
- HTML/Markdown 같은 구조화 포맷 출력
- layout 정보 보존 가능
- 후처리 파이프라인 연결이 쉬움

즉 parser 단계에서 이미 **chunking-friendly 문서**를 만들 수 있다.

---

## 4. parser 출력물을 바로 vector DB에 넣으면 안 되는 이유

parser 결과에는 보통 이런 게 섞여 있다.
- header/footer 반복
- 목차
- 그림 목록
- 표 목록
- 판권/ISBN
- placeholder 이미지 설명
- 깨진 OCR 토큰

이걸 바로 임베딩하면 검색 결과에 이런 쓰레기가 계속 올라온다.

따라서 parser 다음에는 반드시:
- 노이즈 제거
- 문서 유형별 필터링
- 청킹 전 구조 재정리
가 들어가야 한다.

---

## 5. parsing → preprocessing 흐름

![Diagram 1](../assets/diagrams/sections__02-document-parsing__diagram_1.svg)

---

## 6. parser 선택 기준

### Upstage 같은 구조형 parser가 유리한 경우
- 책/매뉴얼/보고서
- 표가 많은 문서
- heading 구조가 중요한 문서
- 후처리와 커스텀이 필요한 경우

### VLM 계열 parser가 유리한 경우
- 레이아웃이 너무 복잡한 스캔본
- 표 의미가 OCR보다 비전 해석에 더 잘 보존되는 문서
- 슬라이드/그림 중심 문서

실무에서는 한 개만 고집하기보다:
- **구조 보존형 parser를 canonical source로**
- **VLM parser를 semantic helper로**
쓰는 방식이 가장 현실적이다.
