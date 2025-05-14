from langchain.tools import tool
from utils.get_token import get_access_token
from utils.config_loader import APP_KEY, APP_SECRET, URL_BASE
import requests
@tool
def get_domestic_stock_data(code: str) -> str:
    """
    6자리 종목코드(code)를 입력받아 국내 주식의 시세, 고가, 저가 정보를 자연어로 반환합니다.
    """
    token = get_access_token()
    if not token:
        return "토큰 발급 실패"

    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010100",
    }
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        if data["rt_cd"] != "0":
            return f"종목코드 '{code}' 시세 조회 실패: {data.get('msg1', '')}"

        item = data["output"]
        eps = bps = roe = None
        try:
            eps = float(item["eps"].replace(',', ''))
            bps = float(item["bps"].replace(',', ''))
        except (ValueError, KeyError):
            pass
        roe = round((eps / bps) * 100, 2) if eps and bps and bps != 0 else None

        return (
            f"[{item['stck_shrn_iscd']}] 현재가: {item['stck_prpr']}원 | "
            f"고가: {item['stck_hgpr']}원 | 저가: {item['stck_lwpr']}원 | "
            f"거래량: {item['acml_vol']}주 | 전일대비: {item['prdy_vrss']}% | 전일대비율: {item['prdy_ctrt']}"
            f"PER: {item['per']} | PBR: {item['pbr']} | "
            f"EPS: {item['eps']} | BPS: {item['bps']} | ROE: {roe if roe is not None else '계산 불가'}"
        )

    except Exception as e:
        return f"시세 조회 중 오류 발생: {e}"
