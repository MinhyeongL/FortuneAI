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
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_location: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: int
    email: str
    name: str
    birth_date: Optional[str]
    birth_time: Optional[str]
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
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, name, birth_date, birth_time, birth_location, created_at, last_login, is_active, premium_until FROM users WHERE email = ?",
            (email,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "password_hash": result[2],
                "name": result[3],
                "birth_date": result[4],
                "birth_time": result[5],
                "birth_location": result[6],
                "created_at": result[7],
                "last_login": result[8],
                "is_active": result[9],
                "premium_until": result[10]
            }
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """ID로 사용자를 조회합니다."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, name, birth_date, birth_time, birth_location, created_at, last_login, is_active, premium_until FROM users WHERE id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "password_hash": result[2],
                "name": result[3],
                "birth_date": result[4],
                "birth_time": result[5],
                "birth_location": result[6],
                "created_at": result[7],
                "last_login": result[8],
                "is_active": result[9],
                "premium_until": result[10]
            }
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def create_user(user_data: UserCreate) -> Optional[Dict[str, Any]]:
    """새 사용자를 생성합니다."""
    try:
        # 이메일 중복 확인
        if get_user_by_email(user_data.email):
            return None
        
        # 패스워드 해시화
        password_hash = get_password_hash(user_data.password)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (email, password_hash, name, birth_date, birth_time, birth_location) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_data.email, password_hash, user_data.name, 
             user_data.birth_date, user_data.birth_time, user_data.birth_location)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return get_user_by_id(user_id)
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
    
    # 마지막 로그인 시간 업데이트 (한국 시간)
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (get_kst_datetime_str(), user["id"],)
        )
        conn.commit()
        conn.close()
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

def create_session_token(user_id: int) -> str:
    """세션 토큰을 생성하고 데이터베이스에 저장합니다."""
    session_token = secrets.token_urlsafe(32)
    expires_at = get_kst_now() + timedelta(days=7)  # 7일 후 만료 (한국 시간)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
            (user_id, session_token, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()
        return session_token
    except Exception as e:
        print(f"Failed to create session token: {e}")
        return None

def validate_session_token(session_token: str) -> Optional[Dict[str, Any]]:
    """세션 토큰을 검증하고 사용자 정보를 반환합니다."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT us.user_id, us.expires_at, u.id, u.email, u.name, u.birth_date, u.birth_time, 
                      u.birth_location, u.created_at, u.last_login, u.is_active, u.premium_until
               FROM user_sessions us 
               JOIN users u ON us.user_id = u.id 
               WHERE us.session_token = ? AND us.expires_at > ?""",
            (session_token, get_kst_datetime_str())
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[2],
                "email": result[3],
                "name": result[4],
                "birth_date": result[5],
                "birth_time": result[6],
                "birth_location": result[7],
                "created_at": result[8],
                "last_login": result[9],
                "is_active": result[10],
                "premium_until": result[11]
            }
        return None
    except Exception as e:
        print(f"Session validation error: {e}")
        return None

def cleanup_expired_sessions():
    """만료된 세션을 정리합니다."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_sessions WHERE expires_at < ?",
            (get_kst_datetime_str(),)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to cleanup expired sessions: {e}")