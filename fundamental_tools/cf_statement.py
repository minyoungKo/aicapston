import sqlite3
import pandas as pd
from langchain.tools import tool


# ✅ 1. SQLite 기반 현금흐름 분석 Agent
class CashFlowSQLAgent:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path,check_same_thread=False)

    def query_cf_data(self, ticker: str) -> pd.DataFrame:
        query = f"""
        SELECT * FROM cf_statement
        WHERE corp_code = '{ticker}'
        ORDER BY bsns_year, quarter;
        """
        return pd.read_sql(query, self.conn)

    def analyze(self, ticker: str) -> str:
        df = self.query_cf_data(ticker)

        if df.empty:
            return f"{ticker}에 대한 현금흐름표 데이터가 존재하지 않습니다."

        # 분석 대상 항목
        activities = [
            "영업활동현금흐름", "영업활동 현금흐름",
            "투자활동현금흐름", "투자활동 현금흐름",
            "재무활동현금흐름", "재무활동 현금흐름",
            "현금및현금성자산의 증가(감소)", "현금및현금성자산의순증감", "현금및현금성자산의 순증감"
        ]

        # 연도+분기 기준으로 정렬
        df["quarter_num"] = df["quarter"].str.replace("Q", "").astype(int)
        df = df.sort_values(by=["bsns_year", "quarter_num"])

        # 분기별로 그룹핑
        grouped = df.groupby(["bsns_year", "quarter"])

        reports = []

        for (year, quarter), group_df in grouped:
            summary = []
            for activity in activities:
                sub_df = group_df[group_df["item_name"] == activity]
                if sub_df.empty:
                    continue

                value = sub_df.iloc[0]["current_cum"]
                if pd.isna(value):
                    continue

                formatted = f"{value / 1e12:.2f}조 원"

                if "영업활동" in activity:
                    평가 = "영업 현금창출 양호" if value > 0 else "영업 흐름 주의"
                elif "투자활동" in activity:
                    평가 = "투자 활발" if value < 0 else "투자 축소"
                elif "재무활동" in activity:
                    평가 = "배당/상환 중심" if value < 0 else "자금 조달"
                elif "현금및현금성자산" in activity:
                    평가 = "현금 증가" if value > 0 else "현금 감소"
                else:
                    평가 = "해석 불가"

                summary.append(f"{activity}: {formatted} → {평가}")

            if summary:
                reports.append(f"📅 {year}년 {quarter} 분석\n" + "\n".join(f"- {s}" for s in summary))

        return "\n\n".join(reports)

        return "\n\n".join(report)


# ✅ 2. 에이전트 인스턴스 생성 (DB 경로 수정 필요)
agent = CashFlowSQLAgent("C:/Users/school/PycharmProjects/capston/fss_origin.db")


# ✅ 3. LangChain Tool 등록
@tool
def analyze_cash_flow_from_db(ticker: str) -> str:
    """
    지정한 종목코드의 현금흐름표를 SQLite DB에서 조회하고 분석합니다.
    """
    return agent.analyze(ticker)


# ✅ 4. 테스트 실행 (단독 실행 시)
if __name__ == "__main__":
    test_code = "005930"  # 삼성전자 등 테스트 종목코드
    result = analyze_cash_flow_from_db.run(test_code)
    print(result)
