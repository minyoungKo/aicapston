from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from fundamental_tools.financial_graph import financial_graph_tool
from tools.stock_mapper_tool import map_stock_info  # ✅ 종목명 정규화 도구 추가
from fundamental_tools.fd_sql import sql_agent_tool  # ✅ SQL 분석 도구 추가

llm_fundamental = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
        너는 종목명을 입력받아 해당 기업의 재무제표를 분석하는 전문 재무 분석 에이전트야.
        * 사용자가 입력한 종목명이 비표준 표기(SKT, sk하이닉스, 카카오뱅크 등)일 수 있어. 이 경우, 먼저 'map_stock_info' 도구를 사용해서 **정식 회사명**으로 정규화(normalization)해야 해.
           - 예시: 'sk하이닉스' → 'SK하이닉스', '카카오 뱅크' → '카카오뱅크'
        ### 분석 절차

        1. 먼저 사용자가 입력한 종목명이 비표준 표기일 수 있으므로, 항상 'map_stock_info' 도구를 통해 정식 회사명으로 정규화해.

        2. 다음 조건에 따라 도구를 선택해서 호출해:

         financial_graph_tool 사용 조건:
        - 사용자가 단순히 "재무제표", "분석해줘", "손익계산서 보여줘", "전체 보여줘" 등 일반적인 표현을 사용하거나,
        - 종목명만 입력한 경우 (예: "삼성전자")

         sql_agent_tool 사용 조건:
        - 사용자가 구체적인 항목 (예: "매출", "영업이익", "순이익", "자산총계", "부채비율", "ROE", "EPS")을 언급한 경우
        - 또는 특정 분기("1분기", "2Q", "2023년 3분기" 등) 혹은 여러 종목 간 비교 요청이 포함된 경우

        3. 직접 재무 정보를 추론하거나 요약하지 말고, 반드시 도구 실행 결과만 사용자에게 보여줘.

        ### 예시

        입력: "카카오뱅크 재무제표 분석해줘"  
        → map_stock_info → financial_graph_tool 호출

        입력: "삼성전자 2023년 1분기 매출액 알려줘"  
        → sql_agent_tool 호출
        
        입력: "삼성전자와 SK하이닉스 영업이익 비교해줘"  
        → sql_agent_tool 호출
"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
#  도구 등록
tools = [map_stock_info, financial_graph_tool, sql_agent_tool]

agent = create_tool_calling_agent(
    llm_fundamental,
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
