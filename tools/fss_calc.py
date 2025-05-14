from typing import List, Dict
import json
import pandas as pd

def fss_analyze(data: dict) -> dict:
    """
    재무제표 summary 데이터를 기반으로 주요 항목의 금액 및 증가율을 함께 분석합니다.
    """
    result = {"기업명": data.get("corp_name"), "분석결과": {}}
    summary = data.get("summary", {})

    def calc_growth(curr, prev):
        if isinstance(curr, int) and isinstance(prev, int) and prev != 0:
            return round((curr - prev) / abs(prev) * 100, 2)
        return None

    # 분석 대상 항목 (라벨은 그대로 쓰고 필드는 요약 기준으로)
    targets = {
        "영업이익": "영업이익",
        "부채총계": "부채총계",
        "자산총계": "자산총계",
        "이익잉여금": "이익잉여금"
    }

    for label, field in targets.items():
        item = summary.get(field, {})
        curr = item.get("당기")
        prev = item.get("전기")
        prev2 = item.get("전전기")

        label_result = {
            "당기": curr,
            "전기": prev,
            "전전기": prev2,
        }

        growth = calc_growth(curr, prev)
        if growth is not None:
            label_result["증가율"] = f"{growth:.2f}%"
        else:
            label_result["증가율"] = "계산 불가"

        result["분석결과"][label] = label_result

    return result
