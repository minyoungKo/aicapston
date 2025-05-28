import pandas as pd
import sqlite3
import os
import re

ROOT_DIR = "C:/Users/school/PycharmProjects/capston/data/financial"
DB_PATH = "C:/Users/school/PycharmProjects/capston/fss_origin.db"

# 추출 대상 항목
TARGET_IDS = {
    '매출액': 'ifrs-full_Revenue',
    '매출총이익': 'ifrs-full_GrossProfit',
    '영업이익': 'dart_OperatingIncomeLoss',
    '당기순이익': 'ifrs-full_ProfitLoss',
    '자산총계': 'ifrs-full_Assets',
    '부채총계': 'ifrs-full_Liabilities',
    '자본총계': 'ifrs-full_Equity',
    '이익잉여금': 'ifrs-full_RetainedEarnings',
    '유동자산': 'ifrs-full_CurrentAssets',
    '유동부채': 'ifrs-full_CurrentLiabilities',
    '영업활동현금흐름': 'ifrs-full_CashFlowsFromUsedInOperatingActivities',
    '투자활동현금흐름': 'ifrs-full_CashFlowsFromUsedInInvestingActivities',
    '재무활동현금흐름': 'ifrs-full_CashFlowsFromUsedInFinancingActivities',
    '현금및현금성자산순증가': 'ifrs-full_IncreaseDecreaseInCashAndCashEquivalents',
    '현금및현금성자산': 'ifrs-full_CashAndCashEquivalents',
    '비유동성자산': 'ifrs-full_NoncurrentAssets',
    '비유동성부채': 'ifrs-full_NoncurrentLiabilities',
    '재고자산': 'ifrs-full_Inventories',
    '법인세비용': 'ifrs-full_IncomeTaxExpenseContinuingOperations'
}
TARGET_ID_SET = set(TARGET_IDS.values())

def parse_number(val):
    if pd.isna(val): return None
    val = str(val).replace(",", "").replace(" ", "").replace("\xa0", "")
    return int(val) if val.lstrip('-').isdigit() else None

def parse_quarter_info(quarter_str, report_date_str):
    try:
        year = pd.to_datetime(report_date_str).year
    except:
        year = None
    if "1분기" in quarter_str:
        q = "1Q"
    elif "반기" in quarter_str or "2분기" in quarter_str:
        q = "2Q"
    elif "3분기" in quarter_str:
        q = "3Q"
    elif "4분기" in quarter_str or "사업" in quarter_str:
        q = "4Q"
    else:
        q = "UNKNOWN"
    return year, q

def match_column(cols, keywords):
    for col in cols:
        if all(k in col for k in keywords):
            return col
    return None

# DB 연결 및 테이블 분리 생성
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS pl_statement (
    corp_code TEXT NOT NULL,
    company_name TEXT NOT NULL,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    bsns_year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    current_3m REAL,
    prior_3m REAL,
    current_cum REAL,
    prior_cum REAL,
    prior_prior_cum REAL,
    PRIMARY KEY (corp_code, item_code, bsns_year, quarter)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS bs_statement (
    corp_code TEXT NOT NULL,
    company_name TEXT NOT NULL,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    bsns_year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    current_cum REAL,
    prior_cum REAL,
    prior_prior_cum REAL,
    PRIMARY KEY (corp_code, item_code, bsns_year, quarter)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS cf_statement (
    corp_code TEXT NOT NULL,
    company_name TEXT NOT NULL,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    bsns_year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    current_cum REAL,
    prior_cum REAL,
    prior_prior_cum REAL,
    PRIMARY KEY (corp_code, item_code, bsns_year, quarter)
)
""")

inserted_keys = {
    "PL": set(),
    "BS": set(),
    "CF": set()
}

# 파일 탐색 및 삽입
for root, _, files in os.walk(ROOT_DIR):
    for file in files:
        if not file.endswith(".txt") or "연결" not in file:
            continue

        file_path = os.path.join(root, file)

        try:
            df = pd.read_csv(file_path, sep="\t", encoding="cp949", low_memory=False)
        except Exception as e:
            print(f"❌ 파일 로딩 실패: {file_path} → {e}")
            continue

        df.columns = df.columns.str.strip()

        if "손익" in file:
            report_type = "PL"
        elif "재무상태표" in file:
            report_type = "BS"
        elif "현금흐름표" in file:
            report_type = "CF"
        else:
            continue

        cols = df.columns.tolist()

        for _, row in df.iterrows():
            item_code = str(row.get("항목코드", "")).strip()
            if item_code not in TARGET_ID_SET:
                continue

            try:
                corp_code = str(row.get("종목코드", "")).replace("[", "").replace("]", "").strip()
                company = str(row.get("회사명", "")).strip()
                item_name = str(row.get("항목명", "")).strip()
                year, quarter = parse_quarter_info(str(row.get("보고서종류", "")), str(row.get("결산기준일", "")))

                key = (corp_code, item_code, year, quarter)
                if key in inserted_keys[report_type]:
                    continue
                inserted_keys[report_type].add(key)

                if report_type == "PL":
                    current_3m = prior_3m = current_cum = prior_cum = prior_prior_cum = None
                    if quarter == "4Q":
                        col_current = match_column(cols, ["당기"])
                        col_prior = match_column(cols, ["전기"])
                        col_prior_prior = match_column(cols, ["전전기"])
                        current_cum = parse_number(row.get(col_current))
                        prior_cum = parse_number(row.get(col_prior))
                        prior_prior_cum = parse_number(row.get(col_prior_prior))
                    else:
                        col_current = match_column(cols, ["당기", "3개월"])
                        col_prior = match_column(cols, ["전기", "3개월"])
                        current_3m = parse_number(row.get(col_current))
                        prior_3m = parse_number(row.get(col_prior))

                    cur.execute("""
                        INSERT OR REPLACE INTO pl_statement (
                            corp_code, company_name, item_code, item_name,
                            bsns_year, quarter, current_3m, prior_3m,
                            current_cum, prior_cum, prior_prior_cum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        corp_code, company, item_code, item_name,
                        year, quarter, current_3m, prior_3m,
                        current_cum, prior_cum, prior_prior_cum
                    ))

                elif report_type == "BS":
                    col_current = match_column(cols, ["당기"])
                    col_prior = match_column(cols, ["전기"])
                    col_prior_prior = match_column(cols, ["전전기"])
                    current_cum = parse_number(row.get(col_current))
                    prior_cum = parse_number(row.get(col_prior))
                    prior_prior_cum = parse_number(row.get(col_prior_prior))

                    cur.execute("""
                        INSERT OR REPLACE INTO bs_statement (
                            corp_code, company_name, item_code, item_name,
                            bsns_year, quarter, current_cum, prior_cum, prior_prior_cum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        corp_code, company, item_code, item_name,
                        year, quarter, current_cum, prior_cum, prior_prior_cum
                    ))

                elif report_type == "CF":
                    col_current = match_column(cols, ["당기"])
                    col_prior = match_column(cols, ["전기"])
                    col_prior_prior = match_column(cols, ["전전기"])
                    current_cum = parse_number(row.get(col_current))
                    prior_cum = parse_number(row.get(col_prior))
                    prior_prior_cum = parse_number(row.get(col_prior_prior))

                    cur.execute("""
                        INSERT OR REPLACE INTO cf_statement (
                            corp_code, company_name, item_code, item_name,
                            bsns_year, quarter, current_cum, prior_cum, prior_prior_cum
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        corp_code, company, item_code, item_name,
                        year, quarter, current_cum, prior_cum, prior_prior_cum
                    ))

            except Exception as e:
                print(f"❌ 행 처리 실패 ({file}): {e}")
                continue

conn.commit()
conn.close()
print("✅ 테이블 3개로 분리 저장 완료 (pl_statement, bs_statement, cf_statement)")
