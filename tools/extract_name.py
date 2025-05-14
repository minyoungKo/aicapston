from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)

@tool
def extract_stock_name(text: str) -> str:
    """사용자 입력에서 종목명 또는 회사명만 추출합니다. 예: '삼성전자'"""
    prompt = (
        "다음 사용자 입력에서 주식 종목명 또는 회사명만 정확히 추출해줘.\n"
        "다른 단어는 제거하고, 종목명만 한 단어로 출력해.\n"
        "예: 삼성전자, LG화학, NAVER, AAPL\n"
        f"입력: {text}\n"
        "정답: "
    )
    return llm.invoke(prompt).content.strip()