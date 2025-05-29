# stock_info_collector_agent.py (LangChain Tool 기반 주가 정보 수집 에이전트)

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

from tools.stock_mapper_tool import map_stock_info
from tools.get_domestic_stock_data import get_domestic_stock_data
from tools.get_overseas_stock_data import get_overseas_stock_data
from tools.volume_rank import get_top_volume_stocks

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        너는 종목명을 입력받아 해당 종목에 대한 종합 정보를 수집하는 주식 전문 에이전트야.

        ### 기능 흐름
        1. 사용자가 입력한 종목명이 비표준 표기(SKT, sk하이닉스, 카카오뱅크 등)일 수 있어. 이 경우, 먼저 'map_stock_info' 도구를 사용해서 **정식 회사명**으로 정규화(normalization)해야 해.
           - 예시: 'sk하이닉스' → 'SK하이닉스', '카카오 뱅크' → '카카오뱅크'
        2. 먼저 map_stock_info 도구로 국내/해외 여부와 종목코드 또는 심볼/거래소 정보를 파악해.
        3. 시세 요청이면 국내는 get_domestic_stock_data, 해외는 get_overseas_stock_data를 호출해야 해.
        4. '거래량 상위' 또는 '많이 거래된' 등의 키워드가 있으면 get_top_volume_stocks를 호출해야 해.
        5. 직접 시세를 생성하거나 추론하지 말고 도구의 결과를 그대로 사용자에게 전달해.
        6. 도구 실행 실패 시 그 오류 메시지를 그대로 알려줘.

        ### 예시
        입력: "애플 주가 알려줘" → map_stock_info("애플") → get_overseas_stock_data(...)
        입력: "삼성전자 현재가" → map_stock_info("삼성전자") → get_domestic_stock_data("005930")
        입력: "오늘 거래량 많은 종목 알려줘" → get_top_volume_stocks()
        """
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

stock_info_tools = [
    Tool.from_function(
        name="map_stock_info",
        func=map_stock_info,
        description="입력된 종목명이 국내 또는 해외 주식인지 판별하고, 종목코드 또는 심볼/거래소 정보를 반환합니다."
    ),
    Tool.from_function(
        name="get_domestic_stock_data",
        func=get_domestic_stock_data,
        description="국내 주식의 종목코드를 기반으로 현재가, 시가총액, 전일대비 등 시세 정보를 조회합니다."
    ),
    Tool.from_function(
        name="get_overseas_stock_data",
        func=get_overseas_stock_data,
        description="해외 주식의 심볼과 거래소 코드를 기반으로 현재가, 환율, 시세 정보를 조회합니다."
    ),
    Tool.from_function(
        name="get_top_volume_stocks",
        func=get_top_volume_stocks,
        description="금일 기준 거래량 상위 종목(최대 10개)을 조회합니다."
    )
]

agent = create_tool_calling_agent(
    llm=llm,
    tools=stock_info_tools,
    prompt=prompt
)

stock_info_collector_agent = AgentExecutor(
    agent=agent,
    tools=stock_info_tools,
    verbose=True,
    handle_parsing_errors=True
)

#Supervisor 호출용 비동기 함수
async def invoke_stock_info_collector(user_input: str) -> str:
    result = await stock_info_collector_agent.ainvoke({"input": user_input})
    return result.get("output", "[주가 수집 실패]")