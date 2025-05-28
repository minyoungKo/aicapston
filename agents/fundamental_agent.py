# fundamental_agent.py (최종 통합 버전 with financial_graph + 종목명 정규화)

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from fundamental_tools.financial_graph import financial_graph_tool
from tools.stock_mapper_tool import map_stock_info  # ✅ 종목명 정규화 도구 추가

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        너는 종목명을 입력받아 해당 기업의 재무제표를 분석하는 전문 재무 분석 에이전트야.

        ### 분석 절차
        1. 사용자가 입력한 종목명이 비표준 표기(SKT, sk하이닉스, 카카오뱅크 등)일 수 있어. 이 경우, 먼저 'map_stock_info' 도구를 사용해서 **정식 회사명**으로 정규화(normalization)해야 해.
           - 예시: 'sk하이닉스' → 'SK하이닉스', '카카오 뱅크' → '카카오뱅크'

        2. 정식 종목명이 확인되면, 'financial_graph_tool'을 호출해서 PL, BS, CF 통합 분석을 수행하고 종합 보고서를 생성해.
        3. 절대 직접 추론하지 말고, 반드시 도구 실행 결과만 사용자에게 보여줘.

        ### 예시
        입력: "sk하이닉스 재무제표 분석해줘" → map_stock_info("sk하이닉스") → "SK하이닉스" → financial_graph_tool("corp_code")
        입력: "카카오 뱅크 재무제표 보여줘" → map_stock_info("카카오 뱅크") → "카카오뱅크" → financial_graph_tool("corp_code")
        """
    ),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# ✅ 정규화 + 통합 분석 도구 함께 등록
tools = [map_stock_info, financial_graph_tool]

agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

fundamental_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Supervisor 호출용 비동기 함수
async def invoke_fundamental(user_input: str) -> str:
    result = await fundamental_agent.ainvoke({"input": user_input})
    return result.get("output", "[재무 분석 실패]")