import sqlite3
import pandas as pd
from langchain.tools import tool


class ProfitLossSQLAgent:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path,check_same_thread=False)

    def query_pl_data(self, ticker: str) -> pd.DataFrame:
        query = f"""
        SELECT * FROM pl_statement
        WHERE corp_code = '{ticker}'
        ORDER BY bsns_year, quarter;
        """
        return pd.read_sql(query, self.conn)

    def get_real_quarter_value(self, df: pd.DataFrame, item_code: str, year: int, quarter: str) -> float | None:
        if quarter in ["1Q", "2Q", "3Q"]:
            row = df[(df["item_code"] == item_code) & (df["bsns_year"] == year) & (df["quarter"] == quarter)]
            if not row.empty and pd.notna(row.iloc[0]["current_3m"]):
                return float(row.iloc[0]["current_3m"])
        elif quarter == "4Q":
            # 4Q 단기 실적 = 4Q 누적 - (1Q + 2Q + 3Q)
            row_4q = df[(df["item_code"] == item_code) & (df["bsns_year"] == year) & (df["quarter"] == "4Q")]
            if row_4q.empty or pd.isna(row_4q.iloc[0]["current_cum"]):
                return None
            cum_4q = row_4q.iloc[0]["current_cum"]
            total = 0.0
            for q in ["1Q", "2Q", "3Q"]:
                row = df[(df["item_code"] == item_code) & (df["bsns_year"] == year) & (df["quarter"] == q)]
                if row.empty or pd.isna(row.iloc[0]["current_3m"]):
                    return None
                total += row.iloc[0]["current_3m"]
            return float(cum_4q) - total
        return None

    def get_annual_cum_value(self, df: pd.DataFrame, item_code: str, year: int) -> float | None:
        row = df[(df["item_code"] == item_code) & (df["bsns_year"] == year) & (df["quarter"] == "4Q")]
        if not row.empty and pd.notna(row.iloc[0]["current_cum"]):
            return float(row.iloc[0]["current_cum"])
        return None

    def analyze(self, ticker: str) -> str:
        df = self.query_pl_data(ticker)
        if df.empty:
            return f"{ticker}에 대한 손익계산서 데이터가 없습니다."

        df["quarter_num"] = df["quarter"].str.replace("Q", "").astype(int)
        df = df.sort_values(by=["bsns_year", "quarter_num"])
        grouped = df.groupby(["bsns_year", "quarter"])

        ITEMS = {
            "매출액": "ifrs-full_Revenue",
            "매출총이익": "ifrs-full_GrossProfit",
            "영업이익": "dart_OperatingIncomeLoss",
            "당기순이익": "ifrs-full_ProfitLoss",
            "이자비용": "ifrs-full_FinanceCosts",
            "법인세": "ifrs-full_IncomeTaxExpenseContinuingOperations"
        }

        reports = []
        annuals = {}

        for (year, quarter), group in grouped:
            summary = []
            revenue = self.get_real_quarter_value(df, ITEMS["매출액"], year, quarter)
            gross = self.get_real_quarter_value(df, ITEMS["매출총이익"], year, quarter)
            op_profit = self.get_real_quarter_value(df, ITEMS["영업이익"], year, quarter)
            net_profit = self.get_real_quarter_value(df, ITEMS["당기순이익"], year, quarter)
            interest = self.get_real_quarter_value(df, ITEMS["이자비용"], year, quarter)
            tax = self.get_real_quarter_value(df, ITEMS["법인세"], year, quarter)

            if revenue is not None:
                summary.append(f"매출액: {revenue / 1e12:.2f}조 원")
            if gross is not None and revenue:
                summary.append(f"매출총이익: {gross / 1e12:.2f}조 원 → 총이익률 {gross / revenue * 100:.1f}%")
            if op_profit is not None and revenue:
                summary.append(f"영업이익: {op_profit / 1e12:.2f}조 원 → 영업이익률 {op_profit / revenue * 100:.1f}%")
            if net_profit is not None and revenue:
                summary.append(f"당기순이익: {net_profit / 1e12:.2f}조 원 → 순이익률 {net_profit / revenue * 100:.1f}%")
            if interest is not None:
                summary.append(f"이자비용: {interest / 1e12:.2f}조 원")
            if tax is not None:
                summary.append(f"법인세비용: {tax / 1e12:.2f}조 원")

            if summary:
                reports.append(f"{year}년 {quarter} 손익 분석\n" + "\n".join(f"- {s}" for s in summary))

        # 연간 누적 요약 추가
        for year in sorted(df["bsns_year"].unique()):
            annual_revenue = self.get_annual_cum_value(df, ITEMS["매출액"], year)
            annual_profit = self.get_annual_cum_value(df, ITEMS["당기순이익"], year)
            if annual_revenue and annual_profit:
                annuals[year] = (annual_revenue, annual_profit)

        if annuals:
            reports.append(" 연간 실적 요약")
            for year, (rev, profit) in annuals.items():
                reports.append(f"- {year}년 총 매출: {rev/1e12:.2f}조 원, 순이익: {profit/1e12:.2f}조 원")

        return "\n\n".join(reports)


pl_agent = ProfitLossSQLAgent("C:/Users/school/PycharmProjects/capston/fss_origin.db")

@tool
def analyze_profit_loss_from_db(ticker: str) -> str:
    """
    지정한 종목코드의 손익계산서를 SQLite DB에서 조회하고 분기별 및 연간 분석을 수행합니다.
    """
    return pl_agent.analyze(ticker)


if __name__ == "__main__":
    test_code = "005930"
    print(analyze_profit_loss_from_db.run(test_code))