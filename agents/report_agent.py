from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json

#LLM 정의
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

#프롬프트 템플릿 정의
report_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "너는 주식 분석 결과를 기반으로 종합 요약 보고서를 작성하는 에이전트야. "
     "분석 대상은 개인 투자자이며, 다음 내용을 포함해야 해:\n"
     "- 요청의 핵심 요지\n"
     "- 각 도구의 결과 요약\n"
     "- 종합 평가 또는 투자 참고 사항\n\n"
     "결과는 반드시 자연스러운 한국어 문장으로 작성해야 해."),
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
