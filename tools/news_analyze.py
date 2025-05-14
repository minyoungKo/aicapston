import os

from dotenv import load_dotenv

from langchain.tools import tool
from openai import OpenAI as OpenAI_Client

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 뉴스 분석 Tool
@tool
def analyze_news(news_text: str) -> str:
    """하나의 종목 또는 산업군에 대한 뉴스들만 분석하세요.
    여러 종목을 한 번에 분석하지 마세요. 뉴스 목록이 없으면 분석하지 않습니다."""
    client = OpenAI_Client(api_key=OPENAI_API_KEY)
    prompt = f"""
    다음 뉴스들을 종합하여 하나의 종목 또는 산업군에 대해 다음을 분석하세요 (한글로):

    1. 뉴스 핵심 요약
    2. 해당 종목/산업군에 미칠 긍정/부정적 영향
    3. 향후 이슈 예측

    뉴스 목록:
    {news_text}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()