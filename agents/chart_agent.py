#chart_agent.py (LangChain Tool 기반 차트 분석 에이전트)

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

from tools.stock_mapper_tool import map_stock_info
from chart_tools.chart_pipeline import chart_pipeline

llm = ChatOpenAI(model="gpt-3.5-turbo")

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        너는 '종목명' 또는 '종목코드'를 입력받아 차트를 수집하고 분석하는 차트 분석 전용 에이전트야.

        ### 기능 흐름
        1. 먼저 종목명을 입력받으면 map_stock_info 도구로 종목코드를 추론해.
        2. 종목코드가 이미 입력되어 있으면 그대로 chart_analyze 도구를 호출해.

        ### 사용 규칙
        - chart_analyze 호출 시 반드시 '종목코드|조회기간|봉구분' 형식으로 넘겨야 해.
        - 조회기간이 없으면 기본값은 '3개월', 봉구분이 없으면 기본값은 '일'이야.

        ### 예시
        입력: "LG전자 3개월 차트 분석" → map_stock_info("LG전자") → chart_analyze("066570|3개월|일")
        입력: "005930 기술적 분석" → chart_analyze("005930|3개월|일")
        입력: "삼성전자 일봉으로 6개월 분석해줘" → map_stock_info("삼성전자") → chart_analyze("005930|6개월|일")
        """
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

chart_data_tools = [
    Tool.from_function(
        name="stock_mapper",
        func=map_stock_info,
        description="종목명을 종목코드로 변환합니다. 예: 삼성전자 → 005930"
    ),
    Tool.from_function(
        name="chart_analyze",
        func=chart_pipeline,
        description="차트 분석 도구. '종목코드|조회기간|봉구분' 형식으로 입력. 디폴트는 '3개월|일'. 예: '005930|3개월|일'"
    )
]

agent = create_tool_calling_agent(
    llm=llm,
    tools=chart_data_tools,
    prompt=prompt
)

chart_data_agent = AgentExecutor(
    agent=agent,
    tools=chart_data_tools,
    verbose=True,
    handle_parsing_errors=True
)

#Supervisor 호출용 비동기 함수
async def invoke_chart_analyzer(user_input: str) -> str:
    result = await chart_data_agent.ainvoke({"input": user_input})
    return result.get("output", "[차트 분석 실패]")
