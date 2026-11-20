import os
import sys

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 다른 import 보다 위 (LangSmith 환경변수를 먼저 읽혀야 함)

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ⚠️ 도구 호출을 지원하는 모델이어야 합니다. gemma3:4b 는 지원하지 않습니다
#    (2026-10-25 실측 — ResponseError: ... does not support tools).
#    기본값은 지원이 확인된 llama3.2:3b 입니다 — 없으면: ollama pull llama3.2:3b
#    다른 모델을 쓰려면 .env 에 TOOL_MODEL=... 을 적습니다.
#    지원 여부 확인: 원본 9week/code/tool_support_check.py
TOOL_MODEL = os.getenv("TOOL_MODEL", "llama3.2:3b")


# ── ① 도구 정의 — 독스트링이 곧 설명문 ★★ ─────────────────────
@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다. 정확한 곱셈이 필요할 때 사용한다."""
    return a * b


@tool
def get_time(timezone: str = "Asia/Seoul") -> str:
    """지정한 시간대의 현재 시각을 문자열로 반환한다."""
    from datetime import datetime, timedelta
    from datetime import timezone as fixed_tz
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        # ⚠️ Windows 에는 시간대 DB 가 없습니다 → pip install tzdata (requirements.txt 에 있음).
        #    그래도 없으면 서울 시각(UTC+9)으로 대신합니다. 모델은 이 본문을 보지 못합니다 ★
        zone = fixed_tz(timedelta(hours=9))
    return datetime.now(zone).strftime("%Y-%m-%d %H:%M:%S")


@tool
def get_weather(city: str) -> str:
    """도시 이름을 받아 해당 도시의 현재 날씨를 조회한다."""
    # 간단한 가상 날씨 데이터를 반환합니다 (필요시 외부 날씨 API로 교체 가능)
    weathers = {
        "서울": "맑음, 18°C",
        "안양": "구름 조금, 17°C",
        "부산": "흐림, 20°C",
        "제주": "비, 19°C",
    }
    return weathers.get(city, f"{city}의 날씨 정보는 찾을 수 없습니다. (기본: 맑음, 15°C)")


TOOLS = {t.name: t for t in [multiply, get_time, get_weather]}


def show_what_model_sees() -> None:
    """2교시 §2-2 — 모델에게 전달되는 것은 무엇인가. ★★

    | 코드 요소       | 모델에게 전달되는 것                          |
    | 함수 이름       | 도구 이름                                     |
    | ★★ 독스트링    | 도구 설명(언제 쓰는 도구인지)                 |
    | 타입 힌트       | 인자 스키마 (이름·타입)                       |
    | 함수 본문       | ❌ 전달되지 않음 — 모델은 모른다             |
    """
    print("── 모델이 보는 것 (함수 본문은 안 보인다) ★★ ──────────")
    for t in TOOLS.values():
        print(f"  name        : {t.name}")
        print(f"  description : {t.description}")
        print(f"  args        : {t.args}")
        print()

    print("""  ★★ 독스트링이 곧 프롬프트입니다.
        5주차 Field(description=...) 과 같은 발상입니다.

         \"\"\"도시 이름을 받아 현재 날씨를 조회한다.\"\"\"   ✅ 언제 쓰는지 명확
         \"\"\"날씨 함수.\"\"\"                                 ❌ 모델이 못 고릅니다
""")


def one_round(question: str, verbose: bool = False) -> str:
    """②~⑤ — 한 바퀴를 손으로 돌리고 최종 답변을 돌려준다. verbose 면 단계마다 찍는다."""
    llm = ChatOllama(model=TOOL_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(list(TOOLS.values()))  # ★ 이 한 줄 (4주차 .bind() 계열)

    messages = [HumanMessage(question)]

    # ── ② 1차 호출 — 여기가 오늘의 결정적 장면 ★★ ─────────────
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if verbose:
        print("content   :", repr(ai_msg.content), "  ← 비어 있다! ★")
        print("tool_calls:", ai_msg.tool_calls)

    if not ai_msg.tool_calls:
        # 모델이 도구 호출을 지원하지 않거나, 도구가 필요 없다고 판단한 경우
        if verbose:
            print(f"""
⚠️ tool_calls 가 비어 있습니다. 둘 중 하나입니다.
    ① 모델이 "도구가 필요 없다"고 판단했다 → 정상 (상식 질문이면 오히려 맞습니다)
    ② '{TOOL_MODEL}' 이 도구 호출을 지원하지 않는다 ⚠️
      → 원본 9week/code/tool_support_check.py 로 확인하고 .env 의 TOOL_MODEL 을 고치십시오.
""")
        return ai_msg.content.strip()

    # ── ③④ ★ 우리가 실행하고 ToolMessage 로 되돌린다 ★ ────────
    if verbose:
        print("\n── ③ 실행 주체는 우리 코드입니다 (아래 로그는 우리가 찍은 것) ★★ ──")
    for call in ai_msg.tool_calls:
        tool_obj = TOOLS[call["name"]]

        # 두 형태의 차이를 반드시 짚을 것 ★
        #   invoke(call["args"]) → 그냥 '결과값'          (파이썬 값)
        #   invoke(call)         → 'ToolMessage'          (tool_call_id 자동 기입)
        tool_msg = tool_obj.invoke(call)

        if verbose:
            raw_result = tool_obj.invoke(call["args"])
            print(f"  실행 {call['name']}({call['args']}) → {raw_result}")
            print(f"    args 만 넘기면 : {raw_result!r}         ← 파이썬 값")
            print(f"    call 을 넘기면 : {type(tool_msg).__name__}"
                  f"(content={tool_msg.content!r}, tool_call_id={tool_msg.tool_call_id!r})")

        messages.append(tool_msg)  # ★ tool_call_id 로 요청-결과의 짝을 맞춘다

    # ── ⑤ 다시 모델에게 — 이번엔 최종 답이 나온다 ──────────────
    final = llm_with_tools.invoke(messages)
    if verbose:
        print(f"\nmessages 길이: {len(messages) + 1}  ← 대화 이력이 쌓인다 (5주차 MessagesPlaceholder 의 자리)")
    return final.content.strip()


def main() -> None:
    verbose = "-v" in sys.argv[1:] or "--verbose" in sys.argv[1:]

    # 세 가지 도구(곱셈, 날씨, 시간)를 동시에 테스트할 수 있는 복합 질문
    question = "357 곱하기 4891은? 그리고 안양 날씨 어때? 지금 몇 시야?"

    if verbose:
        print(f"모델: {TOOL_MODEL}\n")
        show_what_model_sees()
        print("=" * 60, "\n")

    print(f"질문      : {question}")
    answer = one_round(question, verbose)
    print(f"최종 답변 : {answer}")

    if not verbose:
        return

    print("\n" + "=" * 60)
    print("""
관찰 포인트 ★

  1차 응답의 content 가 빈 문자열
        → "모델이 답을 안 했습니다. 도구를 달라고 한 겁니다"
  tool_calls 가 여러 개 (최대 3개)
        → 질문 하나에 여러 개의 도구를 동시에 요청할 수 있다
  함수 실행 로그
        → 우리 코드가 찍은 로그. 실행 주체가 우리임을 확인 ★★
  최종 답변의 계산과 정보 조합이 정확
        → LLM이 각 도구의 결과를 받아 자연스럽게 종합하여 답변합니다.

  ⚠️ 도구가 또 필요하면 우리가 또 돌려야 합니다.
     → 13주차 ToolNode 가 이 for 문을 대신합니다. ★
""")
    print("=" * 60)


if __name__ == "__main__":
    main()