from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_core.prompts import SystemMessagePromptTemplate
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()

# SQLite DB 연결 (경로 수정 포함)
db_path = "sqlite:///C:/Users/school/PycharmProjects/capston/fss.db"
db = SQLDatabase.from_uri(db_path)

# 모델 설정
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# System Prompt 정의
system_prompt = SystemMessagePromptTemplate.from_template("""
너는 한국 상장기업의 재무제표 데이터를 SQL로 조회하는 전문가야.

반드시 아래 규칙을 지켜서 쿼리를 생성해야 해:

✅ 반드시 지켜야 할 규칙:

1. `company_name` 대신 반드시 `corp_code`를 사용해야 해.
2. `item_name` 대신 반드시 `item_code`를 사용해야 해.
3. `item_code`는 아래 매핑표에서 찾은 코드만 사용해야 해.
4. `report_type`은 반드시 'PL', 'BS', 'CF' 중 하나여야 해.
5. 3개월 실적(`current_3m`)을 조회할 경우에는 반드시 `report_type = 'PL'` 조건을 포함해야 해.

📎 item_code 매핑표:
- '매출액': 'ifrs-full_Revenue'
- '영업이익': 'dart_OperatingIncomeLoss'
- '당기순이익': 'ifrs-full_ProfitLoss'
- '자산총계': 'ifrs-full_Assets'
- '부채총계': 'ifrs-full_Liabilities'
- '자본총계': 'ifrs-full_Equity'
- '이익잉여금': 'ifrs-full_RetainedEarnings'
- '유동자산': 'ifrs-full_CurrentAssets'
- '유동부채': 'ifrs-full_CurrentLiabilities'
- '영업활동현금흐름': 'ifrs-full_CashFlowsFromUsedInOperatingActivities'
- '투자활동현금흐름': 'ifrs-full_CashFlowsFromUsedInInvestingActivities'
- '재무활동현금흐름': 'ifrs-full_CashFlowsFromUsedInFinancingActivities'
- '현금및현금성자산순증가': 'ifrs-full_IncreaseDecreaseInCashAndCashEquivalents'
- '현금및현금성자산': 'ifrs-full_CashAndCashEquivalents'
- '비유동성자산': 'ifrs-full_NoncurrentAssets'
- '비유동성부채': 'ifrs-full_NoncurrentLiabilities'
- '재고자산': 'ifrs-full_Inventories'
- '법인세비용': 'ifrs-full_IncomeTaxExpenseContinuingOperations'
❌ 예시 (사용 금지):
SELECT ... WHERE company_name = '삼성전자'
SELECT ... WHERE item_name = '영업이익'

✅ 예시 (정상):
SELECT current_3m FROM financial_state
WHERE corp_code = '097520' AND item_code = 'ifrs-full_Revenue' AND report_type = 'PL' AND bsns_year = 2024
""")

# SQL Toolkit 설정
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# 에이전트 생성
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True,
    system_message=system_prompt,
    return_direct=True
)

# ✅ 질의 실행: 자연어 형태로만 사용
agent_executor.invoke({
    "input": "엠씨넥스의 2024년 당기순이익 알려줘"
})

