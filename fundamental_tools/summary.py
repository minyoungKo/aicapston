from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# ✅ LangChain LLM 객체 생성 (gpt-4o)
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# ✅ 요약 함수: LangChain Runnable 형식으로 wrapping

def generate_final_summary(pl: str, bs: str, cf: str) -> str:
    """
    손익계산서, 재무상태표, 현금흐름표 분석 결과를 받아 종합 요약 보고서를 생성합니다.
    """
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

# ✅ Tool 또는 Runnable 등록 시에는 아래 방식 사용 가능
summarize_financials_tool = RunnableLambda(generate_final_summary)
