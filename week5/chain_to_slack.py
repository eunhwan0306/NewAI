from langchain_core.runnables import RunnableLambda
from send_slack_message import send

from least_to_most import chain
def to_slack(answer: str) -> str:
    send(f"*분석 결과가 나왔습니다*\n\n{answer}")
    return answer
notified = chain | RunnableLambda(to_slack)
notified.invoke({"problem": "리뷰 50건에서 반복 불만과 개선 우선순위를 정리하라"})
