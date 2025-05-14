from langchain.tools import tool
import requests
from utils.get_token import get_access_token
from utils.config_loader import APP_KEY, APP_SECRET, URL_BASE

@tool
def get_top_volume_stocks(input: str = "") -> dict:
    """
    한국투자증권 OpenAPI를 사용해 거래량 기준 국내 주식 정보를 조회합니다.
    """
    token = get_access_token()
    if not token:
        return {"error": " 토큰 발급 실패"}

    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/volume-rank"


    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHPST01710000",
    }

    params = {
        "FID_COND_MRKT_DIV_CODE":"J",
        "FID_COND_SCR_DIV_CODE":"20171",
        "FID_INPUT_ISCD":"0000",
        "FID_DIV_CLS_CODE":"0",
        "FID_BLNG_CLS_CODE":"0",
        "FID_TRGT_CLS_CODE":"111111111",
        "FID_TRGT_EXLS_CLS_CODE":"000000001101",
        "FID_INPUT_PRICE_1":"0",
        "FID_INPUT_PRICE_2":"0",
        "FID_VOL_CNT":"0",
        "FID_INPUT_DATE_1":"0"  # 꼭 빈 문자열
    }

    try:
        response = requests.get(url, headers=headers, params=params)

        if not response.text.strip():
            return {"error": " 응답이 비어 있습니다. 요청 URL, tr_id, 파라미터를 다시 확인하세요."}

        try:
            data = response.json()
        except Exception as e:
            return {"error": f" JSON 파싱 실패: {e}", "raw_response": response.text}

        if data["rt_cd"] != "0":
            return {
                "error": f" 요청 실패: {data.get('msg1', '알 수 없는 오류')}",
                "debug": data
            }

        rank_data = data.get("output", [])

        simplified = [
            {
                "순위": i + 1,
                "종목명": stock["hts_kor_isnm"],
                "현재가": stock["stck_prpr"],
                "등락률": stock["prdy_ctrt"],
                "거래량": stock["acml_vol"],
            }
            for i, stock in enumerate(rank_data)
        ]

        return {"거래량 상위 종목": simplified}

    except Exception as e:
        return {"error": f" API 요청 중 예외 발생: {e}"}
