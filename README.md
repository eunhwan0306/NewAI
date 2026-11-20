# 미국 주식 어닝콜 & 매크로 분석 LangGraph & MCP 슬랙 봇

## 1. 목적
바쁜 개인 투자자가 방대한 영문 어닝콜 트랜스크립트와 10-Q 보고서를 직접 찾아 읽지 않고도, 슬랙을 통해 즉각적으로 기업의 실적 발표 핵심 요약이나 프리마켓 변동 요인을 파악하고 실시간 환율·주가 도구를 함께 활용할 수 있게 돕는다.

## 2. 기능
* **자동 데이터 수집 및 실시간 인덱싱:** SEC EDGAR 공시 자동 수집 스크립트(`auto_ingest.py`) 및 슬랙 채널 내 PDF/MD 파일 업로드 감지를 통한 벡터 DB 자동 업데이트
* **근거 기반 실적 요약 및 QA (RAG):** 기업 티커와 분기 메타데이터 필터링을 적용해 해당 실적 발표의 핵심 요약 및 출처 표기 답변 제공
* **에이전트 기반 실시간 지표 조회 (Agentic RAG & MCP):** 질문 의도에 맞춰 별도 구축된 MCP 서버의 금융 도구(환율 조회, 실시간 주가/뉴스 검색 등)를 동적으로 호출하여 응답

## 3. 사용 모델과 선택 근거 ★
* 생성 모델: `llama3.2:3b` (Ollama 기반 로컬 구동)
* 임베딩 모델: `nomic-embed-text`
* 근거: 오픈소스 기반 로컬 모델이라 방대한 실적 전문을 처리해도 API 토큰 과금 비용이 전혀 없으며, 금융 데이터를 외부 서버로 전송하지 않아 보안성이 뛰어남 (4주차 비교표의 비용 및 보안 항목 기준)
* VRAM 계산: 3.5GB (생성) + 1.0GB (임베딩) = 4.5GB → 8GB 안에 들어감 ✅

## 4. 사용 스택
* **LangChain:** PyPDFLoader, RecursiveCharacterTextSplitter, FAISS Vectorstore
* **LangSmith:** Supervisor의 라우팅 판단, MCP 도구 호출 성공률 및 RAG 검색 품질 추적 ★ 필수
* **LangGraph:** 사용자 질문 의도에 따라 RAG Agent와 MCP Tool Agent로 분기하는 Supervisor 노드 및 상태(State) 관리 구현
* **MCP (Model Context Protocol):** 외부 금융/환율 조회 및 공시 수집 도구를 독립된 `finance_mcp_server.py`로 분리하고 LangGraph 에이전트에서 클라이언트로 연동

## 5. 실행 방법
1. 의존성 패키지 설치: `pip install -r requirements.txt`
2. Ollama 설치 및 모델 다운로드: `ollama run llama3.2:3b` 및 `ollama pull nomic-embed-text`
3. 환경 변수 설정: `.env` 파일 생성 후 `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `LANGCHAIN_API_KEY`, `SEC_USER_AGENT` 입력
4. 초기 데이터 자동 수집 및 벡터 DB 구축: `python auto_ingest.py` 실행 (SEC 공시 자동 다운로드 및 FAISS 인덱싱)
5. MCP 서버 및 슬랙 봇 실행:
   * 터미널 1: `python mcp_server/finance_mcp_server.py` (MCP 서버 구동)
   * 터미널 2: `python slack_bot.py` (슬랙 봇 소켓 모드 실행 및 파일 업로드 이벤트 대기)