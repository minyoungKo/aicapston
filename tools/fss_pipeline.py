from langchain.tools import tool
from tools.dart_fss import get_dart_financials
from tools.fss_calc import fss_analyze

@tool
def fss_pipeline(input_str: str) -> dict:
    """
    DART API를 사용하여 주식의 재무제표 데이터를 조회합니다
    :param input_str:
    :return:
    """

    fss_data_json = get_dart_financials(input_str)
    return fss_analyze(fss_data_json)