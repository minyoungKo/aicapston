# tools/get_overseas_stock_data.py

from langchain.tools import tool
from utils.get_token import get_access_token
from utils.config_loader import APP_KEY, APP_SECRET, URL_BASE
import requests

@tool
def get_overseas_stock_data(input: str) -> dict:
    """
    해외 주식의 시세를 조회합니다.
    - 입력 형식: 'TSLA|NAS' 또는 'AAPL|NYS' 와 같이 symbol과 거래소 코드를 |로 구분한 문자열
    - 예: get_overseas_stock_data("TSLA|NAS")

    """
    try:
        symbol, market = input.strip().split("|")
    except Exception:
        return {"error": " 입력 형식 오류: 'symbol|market' 형태의 문자열이어야 합니다."}

    if not symbol or not market:
        return {"error": " 'symbol' 또는 'market' 값이 누락되었습니다."}

    token = get_access_token()
    if not token:
        return {"error": " 토큰 발급 실패"}

    url = f"{URL_BASE}/uapi/overseas-price/v1/quotations/price-detail"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "HHDFS76200200"
    }
    params = {
        "AUTH": "",
        "EXCD": market,
        "SYMB": symbol,
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        if data["rt_cd"] != "0":
            return {"error": f" 종목코드 '{symbol}' 조회 실패: {data.get('msg1', '')}"}

        item = data["output"]
        return {
            "심볼": symbol,
            "거래소": market,
            "현재가": item["last"],
            "고가": item["high"],
            "저가": item["low"],
            "거래량": item["tvol"],
            "환율": item["t_rate"]
        }
    except Exception as e:
        return {"error": f" 시세 조회 중 오류 발생: {e}"}
