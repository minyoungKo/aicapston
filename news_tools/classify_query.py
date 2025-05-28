import os

from dotenv import load_dotenv

from langchain.tools import tool
from openai import OpenAI as OpenAI_Client

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@tool
def classify_query(query: str) -> str:
    """자연어 질의가 종목 기반인지 산업군 기반인지 분류하고, 필요시 산업군을 추론합니다."""
    client = OpenAI_Client(api_key=OPENAI_API_KEY)
    prompt = f"""
    다음은 사용자의 뉴스 질의입니다. 쉼표로 구분된 여러 종목명이 입력될 수 있습니다.

    당신은 각 종목에 대해 다음을 분류해야 합니다:
    1. 입력이 종목 기반인지 산업군 기반인지 판단
    2. 종목 기반이라면 종목명을 그대로 반환
    3. 산업군 기반이라면 어떤 산업군인지 추론하여 명시

    입력 예시:
    입력: "삼성전자, 현대차, LG화학"
    출력:
    [
      {{ "유형": "종목", "키워드": "삼성전자" }},
      {{ "유형": "종목", "키워드": "현대차" }},
      {{ "유형": "종목", "키워드": "LG화학" }}
    ]

    입력: "{query}"
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()