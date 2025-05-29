from langchain.tools import tool
from chart_tools.get_chart_data import get_chart_data
from chart_tools.chart_analyze import chart_analyze
@tool
def chart_pipeline(input_str: str) -> dict:
    """
    한국투자증권 OpenAPI를 사용하여 주식의 기간별 시세 데이터를 조회합니다.

    - 입력 형식: "종목코드|조회기간|봉구분" (예: "005930|3개월|일")
      - 예: get_chart_data("005930|3개월|일")
      - 종목코드는 6자리 숫자 (예: 005930)
      - 기간은 "30일", "3개월" 등으로 입력
      - 봉구분은 "일", "주", "월" 중 하나

    - 반환: 차트 데이터 리스트 (output2)
    """
    chart_data_json = get_chart_data(input_str)
    return chart_analyze(chart_data_json)


