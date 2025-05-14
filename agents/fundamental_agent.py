#fundamental_agent.py

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

from tools.fss_pipeline import fss_pipeline

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        너는 종목명을 입력받아 해당 기업의 재무제표를 분석하는 전문 재무 분석 에이전트야.

        ### 기능 흐름
        1. 종목명이 입력되면 반드시 dart_fss 도구를 사용해 해당 기업의 재무정보를 수집하고 분석해야 해.
        2. dart_fss 도구는 종목명을 기반으로 고유 법인코드를 조회하고 DART에서 최근 재무제표 항목을 수집해.
        3. 직접 분석하거나 추론하지 말고, 도구 실행 결과를 그대로 사용자에게 보여줘.
        4. 도구 실행에 실패한 경우, 실패 메시지를 그대로 전달해줘.

        ### 예시
        입력: "삼성전자 재무제표 분석해줘" → dart_fss("삼성전자")
        입력: "네이버 재무 상태 알려줘" → dart_fss("네이버")
        """
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

fundamental_tools = [
    Tool.from_function(
        name="dart_fss",
        func=fss_pipeline,
        description="종목명을 입력받아 재무제표 데이터를 수집하고 요약합니다."
    )
]

agent = create_tool_calling_agent(
    llm=llm,
    tools=fundamental_tools,
    prompt=prompt
)

fundamental_agent = AgentExecutor(
    agent=agent,
    tools=fundamental_tools,
    verbose=True,
    handle_parsing_errors=True
)

#Supervisor 호출용 비동기 함수
async def invoke_fundamental(user_input: str) -> str:
    result = await fundamental_agent.ainvoke({"input": user_input})
    return result.get("output", "[재무 분석 실패]")
