# 용어 사전

## RAG
Retrieval-Augmented Generation. 외부 지식을 검색해 LLM의 답변에 근거를 붙이는 방식.

## Ingestion
문서를 가져와서 파싱, 정제, 청킹, 임베딩, 업로드하는 입력 파이프라인 전체.

## Document Parse
PDF, 이미지, HTML 같은 복잡한 문서를 구조화 텍스트로 바꾸는 단계.

## Chunk
검색 가능한 최소 문서 단위. 너무 크면 주제가 섞이고, 너무 작으면 맥락이 사라진다.

## Semantic Chunking
문장의 의미 흐름이나 임베딩 유사도를 기준으로 나누는 방식.

## Structure-aware Chunking
문서 구조(heading, paragraph, table, section) 기준으로 나누는 방식.

## Hybrid Chunking
구조 기반 분할 + 규칙 기반 후처리 + 도메인 메타데이터를 결합한 방식.

## Metadata Tagging
각 청크에 topic, doc_type, source, page, domain label 등을 붙이는 것.

## Dense Retrieval
질문과 청크를 벡터화해 유사도 기반으로 검색하는 방식.

## Lexical Retrieval
키워드나 문자열 일치를 기반으로 검색하는 방식.

## Hybrid Retrieval
Dense retrieval 결과에 lexical/metadata score를 섞어 재정렬하거나 결합하는 방식.

## Rerank
1차 검색 결과를 더 정교한 규칙이나 모델로 다시 정렬하는 단계.

## Table Dominance
표 chunk가 키워드 밀집 때문에 검색 상위권을 과도하게 차지하는 문제.

## Core Primary Collection
설명 본문/사례 중심으로 정제한 메인 검색 컬렉션.

## Secondary Table Collection
조견표, 표, 참고형 structured chunk를 따로 모은 보조 컬렉션.

## Query Encoding
사용자 질문을 검색 친화적으로 다시 구조화하는 단계.

## Harness
검색, 재검색, 근거 조립, 최종 답변 포맷을 관리하는 도메인별 실행 로직.

## CRAG
검색 결과가 약하거나 반복될 때 query rewrite와 재검색을 수행하는 보강 흐름.

## Direct Evidence
질문과 직접 관련된 문헌/본문 근거.

## Near Evidence
완전 일치 사례는 아니지만 구조적으로 가까운 근거.
