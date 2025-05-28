import sqlite3
import pandas as pd
from langchain.tools import tool


class BalanceSheetSQLAgent:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path,check_same_thread=False)

    def query_bs_data(self, ticker: str) -> pd.DataFrame:
        query = f"""
        SELECT * FROM bs_statement
        WHERE corp_code = '{ticker}'
        ORDER BY bsns_year, quarter;
        """
        return pd.read_sql(query, self.conn)

    def analyze(self, ticker: str) -> str:
        df = self.query_bs_data(ticker)
        if df.empty:
            return f"{ticker}에 대한 재무상태표 데이터가 없습니다."

        # 분기 정렬
        df["quarter_num"] = df["quarter"].str.replace("Q", "").astype(int)
        df = df.sort_values(by=["bsns_year", "quarter_num"])

        # 분기별 그룹핑
        grouped = df.groupby(["bsns_year", "quarter"])
        reports = []

        for (year, quarter), group in grouped:
            def get_item(name):
                row = group[group["item_name"] == name]
                return float(row.iloc[0]["current_cum"]) if not row.empty else None

            # 항목 추출
            total_assets = get_item("자산총계")
            total_liabilities = get_item("부채총계")
            equity = get_item("자본총계")
            current_assets = get_item("유동자산")
            current_liabilities = get_item("유동부채")
            cash = get_item("현금및현금성자산")
            inventory = get_item("재고자산")
            retained = get_item("이익잉여금") or get_item("이익잉여금(결손금)")

            summary = []

            # 기본 항목
            if total_assets: summary.append(f"자산총계: {total_assets / 1e12:.2f}조 원")
            if total_liabilities: summary.append(f"부채총계: {total_liabilities / 1e12:.2f}조 원")
            if equity: summary.append(f"자본총계: {equity / 1e12:.2f}조 원")

            # 비율 분석
            if total_assets and total_liabilities:
                debt_ratio = (total_liabilities / total_assets) * 100
                summary.append(f"부채비율: {debt_ratio:.1f}%")

            if current_assets and current_liabilities:
                current_ratio = (current_assets / current_liabilities) * 100
                summary.append(f"유동비율: {current_ratio:.1f}%")

            # 기타 항목
            if cash: summary.append(f"현금및현금성자산: {cash / 1e12:.2f}조 원")
            if inventory: summary.append(f"재고자산: {inventory / 1e12:.2f}조 원")
            if retained: summary.append(f"이익잉여금: {retained / 1e12:.2f}조 원")

            if summary:
                reports.append(f"📘 {year}년 {quarter} 재무상태표 분석\n" + "\n".join(f"- {s}" for s in summary))

        return "\n\n".join(reports)


# ✅ 에이전트 인스턴스 생성
bs_agent = BalanceSheetSQLAgent("C:/Users/school/PycharmProjects/capston/fss_origin.db")


# ✅ LangChain Tool 등록
@tool
def analyze_balance_sheet_from_db(ticker: str) -> str:
    """
    지정한 종목코드의 재무상태표를 SQLite DB에서 조회하고 분기별로 분석합니다.
    """
    return bs_agent.analyze(ticker)


# ✅ 단독 실행용
if __name__ == "__main__":
    result = analyze_balance_sheet_from_db.run("005380")
    print(result)
