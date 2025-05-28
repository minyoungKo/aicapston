import sqlite3
import pandas as pd

# DB 경로
DB_PATH = "C:/Users/school/PycharmProjects/capston/fss_origin.db"

# 연결
conn = sqlite3.connect(DB_PATH)

# 테이블 목록 확인
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
print("📋 존재하는 테이블 목록:")
print(tables)

# main_financials_v2에 저장된 데이터 5건 확인
df = pd.read_sql("SELECT * FROM financial_state LIMIT 50", conn)
print("📄 financial 테이블의 일부 데이터:")
print(df)

conn.close()
