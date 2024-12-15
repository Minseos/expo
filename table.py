import pymysql
import pandas as pd
from server import db_config  # server.py에서 db_config 가져오기

# 내보내기할 SQL 쿼리
query = "SELECT * FROM reviews;"

# MySQL에서 데이터 가져오기 및 CSV 파일로 저장
try:
    # pymysql을 사용하여 MySQL 연결
    connection = pymysql.connect(**db_config)
    print("MySQL 연결 성공!")

    # pandas를 사용해 SQL 실행 결과 가져오기
    df = pd.read_sql(query, connection)
    
    # 데이터프레임을 UTF-8로 CSV 파일로 저장
    output_file = r"C:\study\fintech\final_project\data\review_utf8.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")  # UTF-8로 저장
    print(f"데이터가 {output_file} 파일로 저장되었습니다.")
    
except Exception as e:
    print(f"에러 발생: {e}")
finally:
    if connection:
        connection.close()
        print("MySQL 연결 종료!")
