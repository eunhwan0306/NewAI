## 대상 문서 / 데이터
- 무엇을: 주요 빅테크 기업(Apple, MS, NVIDIA 등)의 최근 분기 어닝콜 트랜스크립트, 10-Q 재무보고서 및 FOMC 의사록
- 몇 건: 핵심 기업 최근 4개 분기 + 최신 FOMC 문서 (초기 20~25건 적재 후 자동 수집·슬랙 업로드로 지속 확장)
- 형식: PDF / MD

## 분할·메타데이터 설계 ★
- 분할 방식: 재귀(RecursiveCharacterTextSplitter) → 이유: 재무 지표와 경영진의 문맥(Context)이 중간에 잘리지 않고 의미 단락 단위로 유지되어야 정확한 검색이 가능하기 때문
- chunk_size / overlap: 1000 / 200
- 심을 메타데이터:
source / page / ticker(종목코드) / quarter(분기)

## 처리 흐름
[수집 파이프라인] SEC EDGAR 자동 수집(`auto_ingest.py`) & 슬랙 파일 업로드 감지 → 자동 청킹 및 FAISS 벡터 DB 실시간 증분 적재
[질의응답 파이프라인] 슬랙 질문 → LangGraph Supervisor (라우터) → [문서 분석: RAG Agent(FAISS) / 실시간 지표·수집: MCP Tool Agent(MCP Server)] → LLM 요약 → 슬랙 답변

## 범위 밖 (안 하는 것) ★
- 실시간 주식 호가 창 연동 및 자동 매매 주문
- 직접적인 투자 종목 추천 및 매수/매도 리딩