import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import pytz

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# Supabase database 임포트
from database import (
    get_user_by_email as db_get_user_by_email,
    get_user_by_id as db_get_user_by_id,
    create_user_db,
    update_user_last_login,
    create_session,
    get_session_by_token,
    delete_expired_sessions,
    create_saju_info,
    get_saju_info_by_user_id
)

# 패스워드 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

# 데이터베이스 경로
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_info.db")

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    """현재 한국 시간 반환"""
    return datetime.now(KST)

def get_kst_datetime_str():
    """현재 한국 시간을 문자열로 반환"""
    return get_kst_now().strftime('%Y-%m-%d %H:%M:%S')

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    # 출생 정보 (필수)
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    birth_minute: int = 0
    is_male: bool
    is_leap_month: bool = False
    birth_location: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: str  # UUID
    email: str
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    birth_minute: int
    is_male: bool
    is_leap_month: bool
    birth_location: Optional[str]
    created_at: str
    last_login: Optional[str]
    is_active: bool
    premium_until: Optional[str]

def get_password_hash(password: str) -> str:
    """패스워드를 해시화합니다."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """패스워드를 검증합니다."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """이메일로 사용자를 조회합니다."""
    return db_get_user_by_email(email)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """ID로 사용자를 조회합니다."""
    return db_get_user_by_id(user_id)

def create_user(user_data: UserCreate) -> Optional[Dict[str, Any]]:
    """새 사용자를 생성하고 사주를 계산합니다."""
    try:
        # 이메일 중복 확인
        if get_user_by_email(user_data.email):
            return None

        # 패스워드 해시화
        password_hash = get_password_hash(user_data.password)

        # 사용자 생성
        user = create_user_db(
            email=user_data.email,
            password_hash=password_hash,
            name=user_data.name,
            birth_year=user_data.birth_year,
            birth_month=user_data.birth_month,
            birth_day=user_data.birth_day,
            birth_hour=user_data.birth_hour,
            birth_minute=user_data.birth_minute,
            is_male=user_data.is_male,
            is_leap_month=user_data.is_leap_month,
            birth_location=user_data.birth_location
        )

        if not user:
            return None

        # 사주 계산 및 저장
        try:
            from saju_calculator import SajuCalculator
            calculator = SajuCalculator()
            saju_chart = calculator.calculate_saju(
                year=user_data.birth_year,
                month=user_data.birth_month,
                day=user_data.birth_day,
                hour=user_data.birth_hour,
                minute=user_data.birth_minute,
                is_male=user_data.is_male,
                is_leap_month=user_data.is_leap_month
            )

            # 사주 정보 DB에 저장
            create_saju_info(
                user_id=user["id"],
                year_pillar=str(saju_chart.year_pillar),
                month_pillar=str(saju_chart.month_pillar),
                day_pillar=str(saju_chart.day_pillar),
                hour_pillar=str(saju_chart.hour_pillar),
                day_master=saju_chart.get_day_master(),
                age=saju_chart.age,
                korean_age=saju_chart.korean_age
            )
        except Exception as e:
            print(f"Failed to calculate saju: {e}")
            # 사주 계산 실패해도 사용자 생성은 성공으로 처리

        return user
    except Exception as e:
        print(f"Database error: {e}")
        return None

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """사용자 인증을 수행합니다."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user["is_active"]:
        return None

    # 마지막 로그인 시간 업데이트
    try:
        update_user_last_login(user["id"])
    except Exception as e:
        print(f"Failed to update last login: {e}")

    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """현재 로그인된 사용자를 반환합니다."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user

def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """현재 활성 사용자를 반환합니다."""
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def create_session_token(user_id: str) -> str:
    """세션 토큰을 생성하고 데이터베이스에 저장합니다."""
    session_token = secrets.token_urlsafe(32)
    expires_at = get_kst_now() + timedelta(days=7)  # 7일 후 만료 (한국 시간)

    try:
        create_session(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at.isoformat()
        )
        return session_token
    except Exception as e:
        print(f"Failed to create session token: {e}")
        return None

def validate_session_token(session_token: str) -> Optional[Dict[str, Any]]:
    """세션 토큰을 검증하고 사용자 정보를 반환합니다."""
    try:
        session = get_session_by_token(session_token)
        if not session:
            return None

        # 세션 만료 확인
        expires_at = datetime.fromisoformat(session["expires_at"])
        if expires_at < get_kst_now():
            return None

        # 사용자 정보 조회
        user = get_user_by_id(session["user_id"])
        return user
    except Exception as e:
        print(f"Session validation error: {e}")
        return None

def cleanup_expired_sessions():
    """만료된 세션을 정리합니다."""
    try:
        delete_expired_sessions()
    except Exception as e:
        print(f"Failed to cleanup expired sessions: {e}")