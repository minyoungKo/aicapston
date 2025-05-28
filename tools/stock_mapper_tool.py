from langchain.tools import tool
from langchain_openai import ChatOpenAI

import pandas as pd
import re
from utils.overseas_mapper import get_symbol_and_exchange_multi,get_krx_code

markets = {
    "NAS": pd.read_excel("data/nas_code.xlsx"),
    "NYS": pd.read_excel("data/nys_code.xlsx"),
    "KRX": pd.read_csv("data/KRX_CODE.csv")
}


llm = ChatOpenAI(model="gpt-4o", temperature=0)

@tool
def map_stock_info(query: str) -> dict:
    """
    종목명을 입력하면 해당 종목이 국내 주식인지 해외 주식인지 판별하고,
    다음 단계의 tool이 바로 사용할 수 있도록 변환된 문자열을 반환합니다.
    - 국내: {"code": "005930"}
    - 해외: {symbol|market}

    LLM이 상장 거래소를 유추하고, 해당 엑셀에서 심볼과 EXCD를 매핑하여 조회합니다.
    실패 시 LLM으로 상장사명과 거래소를 추론하고 자동 재시도합니다.

    """
    try:
        prompt_judge = (
            f"'{query}'는 주식 종목명입니다. 국내(한국 상장)면 '국내', "
            f"해외(미국 상장 포함)면 '해외'라고만 대답해줘."
        )
        market_type = llm.invoke(prompt_judge).content.strip()

        if market_type == "국내":
            code, _, err = get_krx_code(query, markets["KRX"])
            if code:
                return {"code": code}
            else:
                return {"error": f" KRX 매핑 실패: {err}"}

        elif market_type == "해외":
            prompt_market = f"'{query}'라는 종목이 어느 미국 거래소에 상장되어 있나요? 'NASDAQ'이면 NAS, 'NYSE'면 NYS로 정확히 대답해줘."
            predicted_market = llm.invoke(prompt_market).content.strip().upper()

            if "NAS" in predicted_market:
                df = markets["NAS"]
                market_code = "NAS"
            elif "NYS" in predicted_market:
                df = markets["NYS"]
                market_code = "NYS"
            else:
                return {"error": f" 거래소 추론 실패: {predicted_market}"}

            symbol, exchange, _ = get_symbol_and_exchange_multi(query, df, market_code)
            if symbol:
                return f"{symbol}|{exchange}"

            prompt_alt = f"'{query}'은 통칭일 수 있어. 정확한 상장사 이름만 알려줘."
            alt_name = llm.invoke(prompt_alt).content.strip()
            symbol, exchange, _ = get_symbol_and_exchange_multi(alt_name, df, market_code)
            if symbol:
                return f"{symbol}|{exchange}"
            return {"error": f" Symbol 매핑 실패: {query}, {alt_name}"}

        return {"error": f" 국내/해외 구분 실패: {market_type}"}

    except Exception as e:
        return {"error": f" 매핑 오류 발생: {e}"}