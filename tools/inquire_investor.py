from langchain.tools import tool
from utils.get_token import get_access_token
from utils.config_loader import APP_KEY, APP_SECRET, URL_BASE
import requests

@tool
def inquire_investor(code:str)->dict:
    """종목코드 6자리를 입력받아 개인, 기관, 외국인 순매수 수량을 반환합니다."""
    token = get_access_token()
    if not token:
        return {"error": " 토큰 발급 실패"}
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-investor"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010900",
    }
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code
    }
    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        if data["rt_cd"] != "0":
            return {"error": f" 종목코드 '{code}' 시세 조회 실패: {data.get('msg1', '')}"}

        item = data.get("output1",[])
        return{
            "개인 순매수 수량": item["prsn_ntby_qty"],
            "기관 순매수 수량": item["orgn_ntby_qty"],
            "외국인 순매수 수량": item["frgn_ntby_qty"]
        }
    except Exception as e:
        return {"error": f" 조회 오류: {e}"}

