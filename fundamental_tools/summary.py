from langchain.tools import Tool
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

# ✅ LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# ✅ 내부 요약 함수
def generate_final_summary(pl: str, bs: str, cf: str) -> str:
    prompt = f"""
    아래는 한 기업의 재무제표 분석 결과입니다. 각 분석 내용을 바탕으로 전체적인 재무 상태에 대해 전문가 수준의 종합 평가 보고서를 작성해주세요.

    [손익계산서 분석 결과]
    {pl}

    [재무상태표 분석 결과]
    {bs}

    [현금흐름표 분석 결과]
    {cf}

    보고서에는 다음 내용을 포함해주세요:
    - 전반적인 재무 건전성
    - 수익성, 유동성, 안정성 요약
    - 투자자 관점에서 종합 의견
    """
    response = llm.invoke(prompt)
    return response.content.strip()

# ✅ Pydantic 스키마 정의
class FinancialSummaryInput(BaseModel):
    pl: str
    bs: str
    cf: str

# ✅ LangChain Tool 정의
summary_tool = Tool(
    name="generate_financial_summary",
    func=lambda x: generate_final_summary(x.pl, x.bs, x.cf),
    description="손익계산서(pl), 재무상태표(bs), 현금흐름표(cf)를 기반으로 종합 재무 요약 보고서를 생성합니다.",
    args_schema=FinancialSummaryInput
)
