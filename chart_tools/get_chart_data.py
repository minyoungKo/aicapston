from datetime import datetime, timedelta
import requests
from utils.get_token import get_access_token
from utils.config_loader import APP_KEY, APP_SECRET, URL_BASE
import json

def get_chart_data(query: str):
    """
    한국투자증권 OpenAPI를 사용하여 주식의 기간별 시세 데이터를 조회합니다.

    - 입력 형식: "종목코드|조회기간|봉구분" (예: "005930|3개월|일")
      - 예: get_chart_data("005930|3개월|일")
      - 종목코드는 6자리 숫자 (예: 005930)
      - 기간은 "30일", "3개월" 등으로 입력
      - 봉구분은 "일", "주", "월" 중 하나
      - 만약 조회기간, 봉구분이 안들어 왔ㅇ므ㅕㄴ
    - 반환: 차트 데이터 리스트 (output2)
    """

    #입력 파싱
    try:
        code, period, interval = [x.strip() for x in query.split("|")]
    except Exception:
        raise ValueError("입력 형식은 '종목코드|조회기간|봉구분' 이어야 합니다. 예: '005930|3개월|일'")

    #기간 파싱 → 시작 날짜 계산
    today = datetime.today()
    if "개월" in period:
        months = int(period.replace("개월", "").strip())
        start_date = (today - timedelta(days=months * 30)).strftime('%Y%m%d')
    elif "일" in period:
        days = int(period.replace("일", "").strip())
        start_date = (today - timedelta(days=days)).strftime('%Y%m%d')
    else:
        raise ValueError("기간은 '3개월' 또는 '30일' 형식이어야 합니다.")

    end_date = today.strftime('%Y%m%d')

    #봉 구분 변환
    interval_map = {"일": "D", "주": "W", "월": "M"}
    if interval not in interval_map:
        raise ValueError("봉 구분은 '일', '주', '월' 중 하나여야 합니다.")
    interval_code = interval_map[interval]

    #API 호출
    token = get_access_token()
    headers = {
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST03010100",
    }

    query_params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
        "fid_input_date_1": start_date,
        "fid_input_date_2": end_date,
        "fid_period_div_code": interval_code,
        "fid_org_adj_prc": "0"
    }

    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    response = requests.get(url, headers=headers, params=query_params)
    data = response.json()


    #응답 확인
    if data.get("msg_cd") != "MCA00000":
        raise RuntimeError(f"API 호출 실패: {data.get('msg1')}")
    chart_data = data.get("output2",[])
    select_data = [
        {
            "stck_bsop_date": item["stck_bsop_date"],  # 날짜
            "stck_oprc": item["stck_oprc"],            # 시가
            "stck_clpr": item["stck_clpr"],            # 종가
            "stck_hgpr": item["stck_hgpr"],            # 고가
            "stck_lwpr": item["stck_lwpr"],            # 저가
            "acml_vol": item["acml_vol"]               # 거래량
        }
        for item in chart_data
    ]
    return json.dumps(select_data)

