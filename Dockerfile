# Python 이미지 사용
FROM python:3.10-slim

# 기본 패키지 설치
RUN apt update && apt install -y iputils-ping default-mysql-client

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY . .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# Flask 실행 포트 설정
EXPOSE 5000

# Flask 애플리케이션 실행
CMD ["python", "server.py"]
