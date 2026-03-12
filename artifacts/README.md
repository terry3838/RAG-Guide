# Artifacts

이 디렉토리는 RAG-Guide 문서에서 설명하는 실제 엔지니어링 아티팩트를 모아둔 곳이다.

이 코드는 개인 환경 경로를 하드코딩하지 않도록 정리되어 있으며, 실행 시에는 환경변수나 예시 설정 파일을 통해 경로와 시크릿을 주입하는 방식을 전제로 한다.

## 구성

- `harness/`
  - 도메인 하네스 및 구조 계산 스크립트
- `chunking/`
  - 하이브리드 청킹, tier 분리, core-primary 생성 스크립트
- `embedding/`
  - 임베딩 생성 스크립트
- `retrieval/`
  - Qdrant 업로드 및 rerank 스크립트

## 주의

이 디렉토리에는 학습/연구를 위해 공개 가능한 코드만 포함한다.
다음은 포함하지 않는다.

- `.env.local`
- API 키 / 시크릿
- Qdrant secret
- 사용자 민감 데이터
- 세션 로그 원본

## 설정 방법

예시 설정은 아래 파일을 참고하면 된다.

- `config/qdrant.env.example`
- `config/openclaw.json.example`

또는 환경변수 사용:

- `RAG_GUIDE_PROJECT_ROOT`
- `RAG_GUIDE_DATA_ROOT`
- `QDRANT_ENV_FILE`
- `OPENCLAW_CONFIG_FILE`

즉 이 폴더는 **재현 가능한 엔지니어링 아티팩트**만 담는 것을 목표로 한다.
