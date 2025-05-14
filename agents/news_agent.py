#news_search_agent.py (LangChain Tool 기반 뉴스 분석 에이전트)

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

from tools.classify_query import classify_query
from tools.news_summarize import summarize_news_links  # 🔄 뉴스 본문 요약 도구 (RAG 기반)

llm = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        너는 종목명 또는 산업군 이름을 입력받아 뉴스 수집 및 분석을 수행하는 뉴스 분석 전용 에이전트야.

        ### 기능 흐름
        1. 먼저 classify_query 도구를 사용해 입력이 종목 기반인지 산업군 기반인지 판단해.
        2. 그런 다음 summarize_news_links 도구를 사용해서 관련 뉴스 원문을 검색하고 종합 분석 결과를 생성해.

        ### 사용 규칙
        - 입력이 2개 이상 종목이면 각각에 대해 summarize_news_links를 따로 호출해.
        - 뉴스 결과가 없으면 사용자에게 명확히 알려줘.

        ### 예시
        입력: "삼성전자 뉴스 분석해줘" → classify_query → summarize_news_links("삼성전자")
        입력: "반도체 업계 뉴스 요약" → classify_query → summarize_news_links("반도체")
        """
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

news_search_tools = [
    Tool.from_function(
        name="classify_query",
        func=classify_query,
        description="사용자의 질의가 종목 기반인지 산업군 기반인지 판단합니다. 출력은 '종목' 또는 '산업군'입니다."
    ),
    Tool.from_function(
        name="summarize_news_links",
        func=summarize_news_links,
        description="종목명 또는 산업군 이름을 입력받아 관련 뉴스 원문을 수집하고 분석하여 종합 요약 결과를 생성합니다. (RAG 기반)"
    )
]

agent = create_tool_calling_agent(
    llm=llm,
    tools=news_search_tools,
    prompt=prompt
)

news_search_agent = AgentExecutor(
    agent=agent,
    tools=news_search_tools,
    verbose=True,
    handle_parsing_errors=True
)

#Supervisor 호출용 비동기 함수
async def invoke_news_analyzer(user_input: str) -> str:
    result = await news_search_agent.ainvoke({"input": user_input})
    return result.get("output", "[뉴스 분석 실패]")
