import os
import json
import requests
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# ✅ 신뢰할 수 있는 언론사 도메인 리스트
TRUSTED_DOMAINS = [
    "fnnews.com", "etnews.com", "yna.co.kr", "hankyung.com",
    "mk.co.kr", "biz.heraldcorp.com", "imnews.imbc.com",
    "mt.co.kr", "news.kbs.co.kr", "news.sbs.co.kr", "goodkyung.com", "naver.com"
]

@tool
def search_news(query: str) -> str:
    """
    네이버 뉴스 검색 API를 통해 신뢰할 수 있는 언론사의 뉴스 20건을 수집합니다.
    originallink 기반으로 도메인 필터링을 적용하며, 한번에 최대 100개까지 받아옵니다.
    """
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": f"{query} 산업",
        "display": 30,
        "start": 1,
        "sort": "date"
    }

    try:
        response = requests.get("https://openapi.naver.com/v1/search/news.json", headers=headers, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
    except Exception as e:
        return json.dumps({"error": f"뉴스 검색 실패: {e}"}, ensure_ascii=False)

    results = []
    seen_links = set()

    for item in items:
        title = item["title"].replace("<b>", "").replace("</b>", "")
        desc = item["description"].replace("<b>", "").replace("</b>", "")
        originallink = item.get("originallink")

        # 중복 제거
        if originallink in seen_links:
            continue
        seen_links.add(originallink)

        # 도메인 필터링
        if not originallink or not any(domain in originallink for domain in TRUSTED_DOMAINS):
            continue

        results.append({
            "title": title,
            "description": desc,
            "link": originallink
        })

        if len(results) >= 20:
            break

    return json.dumps(results, ensure_ascii=False)
