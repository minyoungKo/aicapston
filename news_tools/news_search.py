import os
import json
import requests
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

@tool
def search_news(query: str) -> str:
    """
    네이버 뉴스 검색 API를 통해 뉴스 20건을 수집합니다.
    뉴스 제목(title)에 query가 포함된 기사만 필터링하며,
    originallink 기준으로 중복을 제거합니다.
    """
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": f"{query} ",
        "display": 100,
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
    lower_query = query.lower()

    for item in items:
        title = item.get("title", "").replace("<b>", "").replace("</b>", "")
        desc = item.get("description", "").replace("<b>", "").replace("</b>", "")
        originallink = item.get("originallink")

        # 제목에 query가 포함되어 있는지 확인 (대소문자 무시)
        if lower_query not in title.lower() and lower_query not in desc.lower():
            continue

        if not originallink or originallink in seen_links:
            continue
        seen_links.add(originallink)

        results.append({
            "title": title,
            "description": desc,
            "link": originallink
        })

        if len(results) >= 20:
            break

    return json.dumps(results, ensure_ascii=False)