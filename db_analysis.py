import mysql.connector
from firebase_admin import credentials, initialize_app, storage
from server import db_config  # MySQL 연결 설정 가져오기

# Firebase 초기화
cred = credentials.Certificate("C:/study/fintech/final_project/final-project-8f802-firebase-adminsdk-dxoaf-794617e2ee.json")
initialize_app(cred, {'storageBucket': 'final-project-8f802.firebasestorage.app'})  # 올바른 버킷 이름 사용


# Firebase 폴더 매핑
firebase_folders = {
    "menu_photo": "menu/{store_id}.png",
    "wordcloud": "1_WordCloud/{store_id}_wordcloud.png",
    "negative_ratio": "2_NegativeReview_Ratio/{store_id}_리뷰_비율.png",
    "keyword": "4_Keyword/{store_id}_keyword.png",
    "raderchart": "5_RadarChart/{store_id}_radar_chart.png"
}

# 카테고리 매핑
categoryMapping = {
    '한식': ['한식', '곰탕,설렁탕', '돼지고기구이', '낙지요리', '백반,가정식', '육류,고기요리', '순대,순댓국', '찌개,전골', '정육식당', '장어,먹장어요리', '족발,보쌈', '한식뷔페', '닭요리', '국수'],
    '중식': ['중식당'],
    '일식': ['일식당', '생선회', '초밥,롤', '돈가스'],
    '양식': ['이탈리아음식', '햄버거'],
    '카페/디저트': ['카페', '카페,디저트', '베이커리']
}

# 카테고리별 분포도 파일명
distribution_files = {
    '한식': 'korean_weighted_rating_vs_price_range_actual_values.png',
    '중식': 'chinese_weighted_rating_vs_price_range.png',
    '일식': 'japanese_weighted_rating_vs_price_range.png',
    '양식': 'western_weighted_rating_vs_price_range.png',
    '카페/디저트': 'cafe_weighted_rating_vs_price_range.png'
}

# 이미 처리된 store_id 리스트
excluded_store_ids = [10, 15, 19, 43]

# Firebase에서 파일 경로 확인
def get_file_path(file_template, store_id):
    bucket = storage.bucket()
    file_path = file_template.format(store_id=store_id)
    blob = bucket.blob(file_path)
    if blob.exists():
        return f"gs://{bucket.name}/{file_path}"
    return None

# 카테고리 매핑 함수
def map_category(raw_category):
    for key, values in categoryMapping.items():
        if raw_category in values:
            return key
    return None

# 분포도 파일 경로 가져오기
def get_distribution_path(category):
    bucket = storage.bucket()
    file_name = distribution_files.get(category)
    if file_name:
        file_path = f"3_Distribution/{file_name}"
        blob = bucket.blob(file_path)
        if blob.exists():
            return f"gs://{bucket.name}/{file_path}"
    return None

# MySQL 데이터 업데이트
def update_analysis_data():
    try:
        # MySQL 연결
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 제외된 store_id를 제외하고 store_id 및 category 가져오기
        query = f"""
            SELECT store_id, category 
            FROM stores 
            WHERE store_id NOT IN ({','.join(map(str, excluded_store_ids))})
        """
        cursor.execute(query)
        stores = cursor.fetchall()

        for store_id, raw_category in stores:
            print(f"\n처리 중인 Store ID: {store_id}, 원본 카테고리: {raw_category}")
            update_data = {}

            # 카테고리 매핑
            category = map_category(raw_category)
            if not category:
                print(f"카테고리 매핑 실패: {raw_category}")
                continue

            print(f"매핑된 카테고리: {category}")

            # 각 컬럼별로 Firebase에서 파일 경로 확인
            for column, template in firebase_folders.items():
                file_path = get_file_path(template, store_id)
                if file_path:
                    update_data[column] = file_path
                    print(f"{column} - Path: {file_path}")
                else:
                    print(f"{column} - 파일 없음")

            # 분포도 경로 확인 (매핑된 카테고리별)
            distribution_path = get_distribution_path(category)
            if distribution_path:
                update_data['distribution'] = distribution_path
                print(f"distribution - Path: {distribution_path}")
            else:
                print("distribution - 파일 없음")

            # MySQL 데이터 업데이트
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

        # 커밋 및 종료
        conn.commit()
        cursor.close()
        conn.close()
        print("\n모든 데이터 처리 완료")

    except mysql.connector.Error as err:
        print(f"MySQL 연결 에러: {err}")

if __name__ == "__main__":
    print("\n--- analysis 테이블 업데이트 시작 ---")
    update_analysis_data()
