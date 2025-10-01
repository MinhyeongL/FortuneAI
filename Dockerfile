# Python 3.11 기반 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (Poetry 및 필수 패키지)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry==2.1.4

# Poetry 설정 - 가상환경 생성하지 않도록 설정
RUN poetry config virtualenvs.create false

# Poetry 파일들 먼저 복사 (의존성 캐싱을 위해)
COPY pyproject.toml poetry.lock ./

# 의존성 설치 (dev 의존성 제외)
RUN poetry install --only=main --no-interaction --no-ansi

# 소스코드 복사
COPY . .

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 노출 (FastAPI 기본 포트)
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# FastAPI 서버 실행
CMD ["python", "backend/main.py"]