from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json

#LLM 정의
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

#프롬프트 템플릿 정의
report_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "너는 주식 분석 결과를 종합적으로 정리하는 전문 리서치 에이전트야. "
     "사용자는 개인 투자자이며, 기술적 분석, 뉴스, 재무제표, 주가 흐름 등 다양한 정보를 기반으로 투자 인사이트를 원하고 있어.\n\n"
     "아래 내용을 포함해서 신뢰도 높은 종합 보고서를 작성해:\n"
     "1. 📌 사용자 요청 요약\n"
     "2. 🧩 각 분석 도구의 핵심 결과 요약 (도구명 명시)\n"
     "3. 🔍 종합 해석 및 투자 참고 사항 (기회 요인, 위험 요인 등)\n\n"
     "※ 작성 원칙:\n"
     "- 각 도구의 결과를 정확하고 핵심적으로 요약해야 해.\n"
     "- 단순 나열이 아니라 결과들 사이의 의미를 연결해 종합적인 판단을 제시해야 해.\n"
     "- 추측성 해석은 지양하고, 데이터에 기반한 분석을 해야 해.\n"
     "- 자연스럽고 정확한 한국어로 작성하되, 개인 투자자가 이해할 수 있도록 적절한 용어 수준을 유지해야 해."),
    ("human", "{input}")
])

#에이전트 생성
report_agent = create_tool_calling_agent(
    llm=llm,
    tools=[],
    prompt=report_prompt
)

report_executor = AgentExecutor(
    agent=report_agent,
    tools=[],
    verbose=True
)

# ✅ LangGraph용 노드 함수
def generate_report_node(state: dict) -> dict:
    query = state["input"]
    result = state["result"]

    full_prompt = (
        f"사용자 요청: {query}\n"
        f"도구 실행 결과:\n{json.dumps(result, ensure_ascii=False)}"
    )

    response = report_executor.invoke({"input": full_prompt})
    return {"report": response.get("output", response)}
