
from typing import List, Dict
import pandas as pd
import talib
import json



def chart_analyze(chart_json_str: str) -> Dict:
    """
    get_chart_data로부터 받은 차트 데이터를 JSON 문자열로 입력받아 기술적 분석(MACD, RSI, SMA, EMA)을 수행합니다.

    - 입력: chart_json_str (JSON 문자열, 즉 output2 리스트)
    - 출력: 분석 결과 (dict)
    """

    # ✅ JSON 문자열 → Python 객체로 파싱
    try:
        chart_data: List[Dict] = json.loads(chart_json_str)
    except json.JSONDecodeError:
        raise ValueError("유효한 JSON 문자열이 아닙니다.")

    if not chart_data or len(chart_data) < 35:
        raise ValueError("기술 분석을 위한 데이터가 부족합니다 (최소 35일 이상 필요).")

    # ✅ DataFrame 변환 및 정제
    df = pd.DataFrame(chart_data)
    df = df[['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df = df.sort_values('date').reset_index(drop=True)
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
    print(df[['date', 'close']])
    close = df['close']

    # ✅ 기술적 지표 계산
    macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    rsi = talib.RSI(close, timeperiod=14)
    sma20 = talib.SMA(close, timeperiod=20)
    ema20 = talib.EMA(close, timeperiod=20)

    latest_idx = -1
    latest_date = df['date'].iloc[latest_idx]

    result = {
        "분석일자": latest_date,
        "종가": float(close.iloc[latest_idx]),
        "MACD": {
            "MACD": float(macd.iloc[latest_idx]),
            "Signal": float(macdsignal.iloc[latest_idx]),
            "Hist": float(macdhist.iloc[latest_idx]),
            "상태": "상승 추세" if macd.iloc[latest_idx] > macdsignal.iloc[latest_idx] else "하락 추세"
        },
        "RSI": {
            "값": float(rsi.iloc[latest_idx]),
            "상태": "과매수" if rsi.iloc[latest_idx] > 70 else "과매도" if rsi.iloc[latest_idx] < 30 else "중립"
        },
        "이동평균선": {
            "SMA20": float(sma20.iloc[latest_idx]),
            "EMA20": float(ema20.iloc[latest_idx]),
            "SMA20_위에_있는가": bool(close.iloc[latest_idx] > sma20.iloc[latest_idx]),
            "EMA20_위에_있는가": bool(close.iloc[latest_idx] > ema20.iloc[latest_idx]),
        }
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return result
