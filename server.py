from flask import Flask, jsonify, request, send_from_directory, render_template
import mysql.connector
from flask_cors import CORS
from dotenv import load_dotenv
import os
import urllib.parse

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# 기본 이미지 URL
DEFAULT_MENU_PHOTO = "https://via.placeholder.com/150"

load_dotenv(dotenv_path = '.env')

db_config = {
    "host": os.getenv("MYSQL_HOST", "13.125.85.168"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "1234"),
    "database": os.getenv("MYSQL_DATABASE", "project"),
}


#루트 경로에서 kakao.html 렌더링
@app.route('/')
def home():
    return render_template('kakao.html')

# gs:// URL을 HTTP URL로 변환하는 함수
def convert_gs_to_http(gs_url):
    if gs_url.startswith("gs://"):
        bucket_name = "final-project-8f802.firebasestorage.app"  # 정확한 버킷 이름
        path = gs_url.replace(f"gs://{bucket_name}/", "")  # `gs://` 경로 제거
        encoded_path = urllib.parse.quote(path, safe="")  # URL 인코딩
        return f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media"
    return gs_url



@app.route('/markers', methods=['GET'])
def get_markers():
    cursor, conn = None, None
    try:
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(**db_config)
        print("Connected to MySQL successfully.")
        
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT s.store_id, s.store_name AS name, s.address, 
                   s.category,
                   COALESCE(a.menu_photo, %s) AS menu_photo
            FROM stores s
            LEFT JOIN analysis a ON s.store_id = a.store_id
        """
        print("Executing query...")
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"Query executed successfully. Results: {results}")

        for result in results:
            result['menu_photo'] = convert_gs_to_http(result['menu_photo'])

        return jsonify(results)
    except Exception as e:
        print(f"Error in /markers: {str(e)}")
        return jsonify({"error": "MySQL에서 문제가 발생했습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# reviews.html 파일 렌더링을 위한 라우트 추가
@app.route('/reviews.html')
def reviews_page():
    store_id = request.args.get('storeId')
    if not store_id:
        return jsonify({"error": "storeId가 제공되지 않았습니다."}), 400
    return render_template('reviews.html', store_id=store_id)


@app.route('/reviews/<int:store_id>', methods=['GET'])
def get_reviews(store_id):
    cursor, conn = None, None  # cursor와 conn 초기화
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT DATE_FORMAT(review_date, '%Y-%m') AS review_date,
                review_text,
                platform,
                naver_rating,
                kakao_rating,
                google_rating,
                stores.store_name,
                stores.address,
                stores.phone_number,
                stores.business_hours,
                stores.price_range,
                COALESCE(analysis.menu_photo, %s) AS menu_photo
            FROM reviews 
            JOIN stores ON stores.store_id = reviews.store_id
            LEFT JOIN analysis ON stores.store_id = analysis.store_id
            WHERE reviews.store_id = %s
            ORDER BY review_date DESC
        """
        cursor.execute(query, (DEFAULT_MENU_PHOTO, store_id))
        reviews = cursor.fetchall()

        if not reviews:
            return jsonify({"message": "리뷰가 없습니다."}), 404

        response = {
            "store_name": reviews[0]['store_name'].replace('_', ' '),
            "address": reviews[0]['address'],
            "phone_number": reviews[0]['phone_number'] or "-",
            "business_hours": reviews[0]['business_hours'] or "-",
            "price_range": reviews[0]['price_range'] or "-",
            "menu_photo": convert_gs_to_http(reviews[0]['menu_photo']),
            "reviews": reviews
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error in /reviews/<store_id>: {str(e)}")
        return jsonify({"error": "서버에서 문제가 발생했습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/search_reviews', methods=['GET'])
def search_reviews():
    keyword = request.args.get('keyword', '').strip()
    price_range = request.args.get('price_range', '').strip()  # 가격대 파라미터 추가

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 기본 쿼리 작성
        query = """
            SELECT stores.store_id, stores.store_name AS name, stores.address, stores.category,
                   COUNT(reviews.review_id) AS keyword_count,
                   COALESCE(analysis.menu_photo, %s) AS menu_photo
            FROM reviews
            JOIN stores ON stores.store_id = reviews.store_id
            LEFT JOIN analysis ON stores.store_id = analysis.store_id
            WHERE 1=1
        """
        params = [DEFAULT_MENU_PHOTO]

        # 키워드 필터 추가
        if keyword:
            query += " AND reviews.review_text LIKE %s"
            params.append(f"%{keyword}%")

        # 가격대 필터 추가
        if price_range:
            price_parts = price_range.split('-')
            if len(price_parts) == 2:  # 가격 범위가 주어진 경우
                query += " AND stores.price_range BETWEEN %s AND %s"
                params.extend(price_parts)
            elif price_parts[0]:  # 최소값만 주어진 경우 (예: ₩100,000 이상)
                query += " AND stores.price_range >= %s"
                params.append(price_parts[0])

        # 그룹화 및 정렬
        query += """
            GROUP BY stores.store_id, stores.store_name, stores.address, stores.category, analysis.menu_photo
        """

        # 쿼리 실행
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        for result in results:
            result['menu_photo'] = convert_gs_to_http(result['menu_photo'])

        return jsonify({"search_results": results})
    except Exception as e:
        print(f"Error in /search_reviews: {str(e)}")
        return jsonify({"error": "검색 중 문제가 발생했습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':  
    app.run(host='0.0.0.0', debug=True)
