from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.tools import Tool

# ✅ DB 및 LLM 설정
sqlite_path = "sqlite:///C:/Users/school/PycharmProjects/capston/fss_new.db"
db = SQLDatabase.from_uri(
    sqlite_path,
    include_tables=["bs_statement", "cf_statement", "pl_statement"],
    sample_rows_in_table_info=5
)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# ✅ SQL 도구 및 프롬프트 설정
sql_tools = SQLDatabaseToolkit(db=db, llm=llm).get_tools()

prompt = ChatPromptTemplate.from_messages([
    ("system", """
    ### 전체 흐름
    1. SQL 쿼리는 sql_db_query 도구로 실행해.
       - 반드시 current_cum IS NOT NULL 조건을 포함할 것.
       - quarter는 1,2,3,4가 아닌 '1Q','2Q','3Q','4Q' 이런식으로 들어갈 것
       - 만약 특정 quarter의 데이터를 갖고 오라고 요청하지 않았으면 quarter='4Q'로 설정할 것
       - quarter가 '1Q', '2Q', '3Q'인 경우 → 반드시 `current_3m IS NOT NULL` 조건 사용
       - quarter가 '4Q'인 경우 → 반드시 `current_cum IS NOT NULL` 조건 사용
       - 분기가 명시되지 않은 경우 → 기본값은 '4Q'이며, 이때는 current_cum 사용
       - GROUP BY 또는 집계 함수(SUM, MAX 등)를 사용할 경우에도 반드시 current_cum IS NOT NULL 조건을 포함할 것.
       - GROUP BY를 사용할 때는 SELECT에 포함된 다른 컬럼은 반드시 집계 함수로 감싸야 해.
       - 매출 1등 기업, 최대값 등 단일 결과를 원할 경우에는 GROUP BY를 사용하지 않고,
         ORDER BY {{컬럼}} DESC LIMIT 형태로 쿼리할 것.    

    2. 사용자가 특정 재무제표 명칭을 지정한 경우에는 해당 테이블 전체를 조회해야 해:
       - "재무상태표" → bs_statement
       - "손익계산서" → pl_statement
       - "현금흐름표" → cf_statement


    3. 사용자가 단순히 "재무제표"라고 말하거나 "종목명"만 들어온 경우:
       - 세 가지 테이블 모두 조회해야 해 (bs_statement, pl_statement, cf_statement)
       - 조회 시에는 반드시 다음 조건을 포함해야 해:
       - bsns_year IN (2022, 2023, 2024)
       - quarter = '4Q'
       - current_cum IS NOT NULL 
       - SELECT 시에는 반드시 bsns_year, item_name, current_cum 컬럼만 조회할 것
       + 세 테이블에 대해 각각 쿼리하고, 결과를 통합하여 분석해줘

    4. 사용자가 특정 항목을 말한 경우(예: "매출액", "영업이익", "자산총계" 등):
       - item_name 컬럼을 기준으로 직접 SQL 쿼리를 생성하면 돼.
       - item_code로 변환하거나 매핑할 필요 없음.
       - SELECT 시에는 반드시 item_name과 만약 '4Q'면 current_cum '1Q','2Q','3Q'면 current_3m 포함해야할 것

    5. 사용자가 종목명을 명시하지 않고 전체 비교나 최대값 등을 묻는 경우:
       - company_name을 기준으로 GROUP BY와 집계함수를 사용해야 해.
       - 이때는 map_stock_info 도구는 사용하지 않아도 돼. 특정 종목명 정규화가 필요 없기 때문이야  

    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# ✅ SQL Agent 생성
sql_agent = create_tool_calling_agent(
    llm=llm,
    tools=sql_tools,
    prompt=prompt
)

executor = AgentExecutor(
    agent=sql_agent,
    tools=sql_tools,
    verbose=True,
    handle_parsing_errors=True
)

# ✅ Tool로 wrapping
sql_agent_tool = Tool.from_function(
    name="sql_agent_tool",
    func=lambda query: executor.invoke({"input": query}).get("output", "[SQL 분석 실패]"),
    description="특정 재무 항목(예: 매출액, 자산총계 등)에 대해 SQL 분석을 수행합니다."
)