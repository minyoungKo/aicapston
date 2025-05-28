# utils/overseas_mapper.py

def get_symbol_and_exchange_multi(query, df, exchange_code):
    """
    엑셀 DataFrame(df)에서 query에 해당하는 한국어/영어 이름 검색 후 Symbol과 거래소코드 반환
    exchange_code는 'NAS', 'NYS' 등으로 명시
    """
    try:
        matched = df[(df["Korea name"].str.contains(query, na=False)) |
                     (df["English name"].str.contains(query, case=False, na=False))]
        if matched.empty:
            return None, None, f" '{query}'에 해당하는 종목을 찾을 수 없습니다."

        row = matched.iloc[0]
        return row["Symbol"], exchange_code, None
    except Exception as e:
        return None, None, f" 오류 발생: {e}"

def get_krx_code(query,df):
    """
    krx_code.csv 파일에서 query에 해당하는 종목명을 검색한 후 그에 해당하는 종목코드를 반환
    :param query: 사용자가 원하는 종목명
    """
    try:
        result = df[(df["종목명"]==query)]

        if result.empty:
            return None, None, f" '{query}'에 해당하는 종목을 찾을 수 없습니다."


        code_raw = result.iloc[0]["종목코드"]
        code = str(code_raw).zfill(6)  # 여기서 str()로 변환한 뒤 zfill 사용
        return code, "KRX", None
    except Exception as e:
        return None, None, f" 오류 발생: {e}"
