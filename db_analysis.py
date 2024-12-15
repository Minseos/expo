import mysql.connector
from firebase_admin import credentials, initialize_app, storage
from server import db_config  # MySQL 연결 설정 가져오기

# Firebase 초기화
cred = credentials.Certificate("C:/study/fintech/final_project/final-project-8f802-firebase-adminsdk-dxoaf-794617e2ee.json")
initialize_app(cred, {'storageBucket': 'final-project-8f802.firebasestorage.app'})  # Firebase 버킷 설정

# Firebase 폴더 매핑
firebase_folders = {
    "menu_photo": "menu/{store_id}.png",
    "wordcloud": "1_WordCloud/{store_id}_wordcloud.png",
    "negative_ratio": "2_NegativeReview_Ratio/{store_id}_리뷰_비율.png",
    "distribution": "3_Distribution/{store_id}__Distribution.png",
    "keyword": "4_Keyword/{store_id}_keyword.png",
    "raderchart": "5_RadarChart/{store_id}_radar_chart.png"
}

# Firebase에서 파일 경로 확인
def get_file_path(file_template, store_id):
    """
    Firebase 경로를 확인하고 존재하는 경우 전체 경로를 반환합니다.
    """
    bucket = storage.bucket()
    file_path = file_template.format(store_id=store_id)
    blob = bucket.blob(file_path)
    if blob.exists():
        return f"gs://{bucket.name}/{file_path}"
    return None

# MySQL 데이터 업데이트
def update_analysis_data():
    """
    stores 테이블의 모든 store_id에 대해 Firebase 파일 경로를 확인하고
    analysis 테이블을 업데이트합니다.
    """
    try:
        # MySQL 연결
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # stores 테이블에서 모든 store_id 가져오기
        query = "SELECT store_id, category FROM stores"
        cursor.execute(query)
        stores = cursor.fetchall()

        # 각 store_id에 대한 Firebase 파일 경로 확인 및 MySQL 업데이트
        for store_id, category in stores:
            print(f"\n처리 중인 Store ID: {store_id}")
            update_data = {}

            # Firebase 각 폴더에 대한 경로 확인
            for column, template in firebase_folders.items():
                file_path = get_file_path(template, store_id)
                if file_path:
                    update_data[column] = file_path
                    print(f"{column} - Path: {file_path}")
                else:
                    print(f"{column} - 파일 없음")

            # analysis 테이블에 데이터 삽입 또는 업데이트
            cursor.execute("""
                INSERT INTO analysis (store_id, menu_photo, wordcloud, negative_ratio, keyword, raderchart, distribution)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    menu_photo = VALUES(menu_photo),
                    wordcloud = VALUES(wordcloud),
                    negative_ratio = VALUES(negative_ratio),
                    keyword = VALUES(keyword),
                    raderchart = VALUES(raderchart),
                    distribution = VALUES(distribution)
            """, (
                store_id,
                update_data.get("menu_photo"),
                update_data.get("wordcloud"),
                update_data.get("negative_ratio"),
                update_data.get("keyword"),
                update_data.get("raderchart"),
                update_data.get("distribution")
            ))

            print(f"Store ID {store_id} 데이터 업데이트 완료")

        # 커밋 및 연결 종료
        conn.commit()
        cursor.close()
        conn.close()
        print("\n모든 데이터 처리 완료")

    except mysql.connector.Error as err:
        print(f"MySQL 연결 에러: {err}")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    print("\n--- analysis 테이블 업데이트 시작 ---")
    update_analysis_data()
