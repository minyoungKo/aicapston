
import requests
import json
import os
from utils.config_loader import API_KEY

# 주요 재무 항목과 account_id 매핑
TARGET_ITEMS = {
    '매출액': ['ifrs-full_Revenue'],
    '영업이익': ['dart_OperatingIncomeLoss'],
    '당기순이익': ['ifrs-full_ProfitLoss'],
    '자산총계': ['ifrs-full_Assets'],
    '부채총계': ['ifrs-full_Liabilities'],
    '자본총계': ['ifrs-full_Equity'],
    '이익잉여금': ['ifrs-full_RetainedEarnings'],
    '유동자산': ['ifrs-full_CurrentAssets'],
    '유동부채': ['ifrs-full_CurrentLiabilities'],
    '영업활동현금흐름': ['ifrs-full_CashFlowsFromUsedInOperatingActivities'],
    '투자활동현금흐름': ['ifrs-full_CashFlowsFromUsedInInvestingActivities'],
    '재무활동현금흐름': ['ifrs-full_CashFlowsFromUsedInFinancingActivities']
}


def get_corp_code(corp_name, json_path=None):
    if json_path is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(base_dir, "corp_codes.json")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            corp_dict = json.load(f)
        return corp_dict.get(corp_name)
    except:
        return None


def get_financials(corp_code, bsns_year="2024", reprt_code="11011"):
    url = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
    params = {
        'crtfc_key': API_KEY,
        'corp_code': corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code,
        'fs_div': 'CFS'
    }
    res = requests.get(url, params=params).json()
    if res.get('status') != '000':
        return []
    return res.get('list', [])


def extract_main_items(data):
    result = {}
    for label, ids in TARGET_ITEMS.items():
        for item in data:
            if item.get('account_id') in ids:
                def parse(value):
                    try:
                        value = value.replace(',', '').replace(' ', '').replace('\xa0', '')
                        return int(value) if value.replace('-', '').isdigit() else value
                    except:
                        return value

                result[label] = {
                    "당기": parse(item.get("thstrm_amount", "")),
                    "전기": parse(item.get("frmtrm_amount", "")),
                    "전전기": parse(item.get("bfefrmtrm_amount", ""))
                }
                break
    return result



def get_dart_financials(corp_name: str) -> dict:
    """
    DART OpenAPI를 통해 국내 기업의 최신 재무제표 주요 항목을 조회합니다.

    Args:
        corp_name: 기업 이름 (예: 삼성전자)

    Returns:
        주요 재무제표 항목 딕셔너리
    """
    bsns_year = "2024"
    reprt_code = "11011"  # 사업보고서

    corp_code = get_corp_code(corp_name)
    if not corp_code:
        return {"error": f"'{corp_name}'에 해당하는 법인코드를 찾을 수 없습니다."}

    raw_data = get_financials(corp_code, bsns_year, reprt_code)
    if not raw_data:
        return {"error": f"'{corp_name}'의 재무정보 조회 실패."}

    summary = extract_main_items(raw_data)
    return {
        "corp_name": corp_name,
        "year": bsns_year,
        "report": reprt_code,
        "summary": summary
    }
