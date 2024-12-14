import mysql.connector
from server import db_config

try:
    # db_config에서 MySQL 연결 설정 사용
    conn = mysql.connector.connect(**db_config)
    print("MySQL 연결 성공!")

    # 커서 생성
    cursor = conn.cursor()

    # 테이블 목록 가져오기
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print("테이블 목록:")
    for table in tables:
        print(table)

    # 커서와 연결 닫기
    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"MySQL 연결 에러: {err}")
