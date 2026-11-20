# (프로젝트 이름)
## 1. 목적
바쁜 개인 투자자가 방대한 영문 어닝콜 전문을 직접 읽지 않고도, 슬랙 창에서 즉각적으로 기업의 하락 요인이나 가이던스를 파악하고 실시간 매크로 지표 도구를 함께 활용할 수 있게 돕는다.
## 2. 기능
- 기능 1: 특정 티커와 분기를 기반으로 해당 실적 발표의 핵심 요약 및 QA
- 기능 2: 에이전트를 통한 외부 도구(환율 계산기, 웹 검색 등) 자동 호출
## 3. 사용 모델과 선택 근거 ★
- 생성 모델: llama3.2:3b (Ollama 기반 로컬 구동)
- 임베딩 모델: nomic-embed-text
- 근거: (4주차 비교표 기준) 오픈소스 로컬 모델이라 실적 전문을 넣어도 토큰 과금 비용이 전혀 없으며, 금융 데이터의 외부 유출(보안) 우려가 없음
- VRAM 계산: 3.5GB (생성) + 1GB (임베딩) → 8GB 안에 들어감 ✅
## 4. 사용 스택
- LangChain: PyPDFLoader, FAISS/Chroma Vectorstore
- LangSmith: Agent의 도구 호출 성공률 및 RAG 검색 품질 추적 ★ 필수
- LangGraph: 사용자 질문 의도에 따라 RAG 검색 툴이나 일반 계산/검색 툴로 분기하는 Supervisor 노드 구현 (사용 시)
- Slack Bolt API (슬랙 봇 연동), FastAPI (웹훅 수신)
## 5. 실행 방법
(설치 → 실행까지 그대로 따라 할 수 있게)
pip install -r requirements.txt 실행

Ollama 설치 후 ollama run llama3.2:3b 명령어로 로컬 LLM 활성화

슬랙 API 콘솔에서 App 생성 후, .env 파일에 SLACK_BOT_TOKEN, SLACK_APP_TOKEN 입력

python slack_bot.py 실행하여 소켓 모드 연결 후 슬랙에서 봇 호출