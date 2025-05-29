# chart_agent.py

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

from tools.stock_mapper_tool import map_stock_info
from chart_tools.chart_pipeline import chart_pipeline

import json

# LLM (하나만 사용)
llm_chart = ChatOpenAI(model="gpt-3.5-turbo")

# 차트 분석 dict 결과를 GPT-4로 해석 (Tool 호출 X, 내부 전용)
def interpret_chart_data_from_dict(chart_data: dict) -> str:
    pretty = json.dumps(chart_data, indent=2, ensure_ascii=False)

    prompt = f"""
    너는 기술적 분석 기반 투자 전략을 제시하는 전문가야.

    다음 분석 결과를 기반으로 다음 7가지 항목으로 요약해줘:

    1. 현재 추세
    2. MACD 해석
    3. RSI 해석
    4. 이동평균선 해석
    5. 볼린저 밴드 해석
    6. 종합 판단 및 전략
    7. 유의사항

    [차트 분석 결과]
    {pretty}
    """

    return llm_chart.invoke(prompt).content

# 수집 + 해석 통합 함수 (Tool로 등록됨)
def chart_analyze(query: str) -> str:
    try:
        stock_code, period, interval = query.strip().split("|")
    except:
        return "[오류] 입력 형식은 '종목코드|조회기간|봉구분'입니다."

    print("[chart_pipeline 호출됨]")  # 디버깅용 로그
    chart_dict = chart_pipeline(query)  # 단 1회 호출

    print("[interpret_chart_data_from_dict 호출됨]")
    return interpret_chart_data_from_dict(chart_dict)

# 시스템 프롬프트
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        너는 '종목명' 또는 '종목코드'를 입력받아 차트를 수집하고 분석하는 차트 분석 전용 에이전트야.

        * 사용자가 입력한 종목명이 비표준 표기(SKT, sk하이닉스, 카카오뱅크 등)일 수 있어. 이 경우, 먼저 'map_stock_info' 도구를 사용해서 정식 회사명으로 정규화해야 해.
        * 종목명이 들어오면 map_stock_info 도구로 종목코드를 조회한 뒤, chart_analyze 도구를 호출해야 해.
        * 종목코드가 이미 입력되어 있다면 바로 chart_analyze 호출해.

        chart_analyze는 '종목코드|조회기간|봉구분' 형식으로 입력해야 하고, 조회기간이 없으면 기본값은 '3개월', 봉구분은 '일'이야.

        예시:
        - 입력: "LG전자 3개월 차트 분석" → map_stock_info("LG전자") → chart_analyze("066570|3개월|일")
        - 입력: "005930 기술적 분석" → chart_analyze("005930|3개월|일")
        - 입력: "삼성전자 일봉으로 6개월 분석해줘" → map_stock_info("삼성전자") → chart_analyze("005930|6개월|일")
        """
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# 도구 등록
chart_data_tools = [
    Tool.from_function(
        name="stock_mapper",
        func=map_stock_info,
        description="종목명을 종목코드로 변환합니다. 예: 삼성전자 → 005930"
    ),
    Tool.from_function(
        name="chart_analyze",
        func=chart_analyze,
        description="차트 분석 + 해석. '종목코드|조회기간|봉구분' 형식으로 입력. 예: '005930|3개월|일'"
    )
]

# 에이전트 구성
agent = create_tool_calling_agent(
    llm=llm_chart,
    tools=chart_data_tools,
    prompt=prompt
)

chart_data_agent = AgentExecutor(
    agent=agent,
    tools=chart_data_tools,
    verbose=True,
    handle_parsing_errors=True
)

# Supervisor 호출용 비동기 함수
async def invoke_chart_analyzer(user_input: str) -> str:
    result = await chart_data_agent.ainvoke({"input": user_input})
    return result.get("output", "[차트 분석 실패]")