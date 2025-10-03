"""
Supabase 데이터베이스 연결 및 헬퍼 함수
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Supabase 클라이언트 초기화
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==================== Users ====================

def create_user_db(
    email: str,
    password_hash: str,
    name: str,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    is_male: bool,
    is_leap_month: bool = False,
    birth_location: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """새 사용자를 생성합니다."""
    try:
        response = supabase.table("users").insert({
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "birth_year": birth_year,
            "birth_month": birth_month,
            "birth_day": birth_day,
            "birth_hour": birth_hour,
            "birth_minute": birth_minute,
            "is_male": is_male,
            "is_leap_month": is_leap_month,
            "birth_location": birth_location,
        }).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """이메일로 사용자를 조회합니다."""
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """ID로 사용자를 조회합니다."""
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by id: {e}")
        return None


def update_user_last_login(user_id: str) -> bool:
    """마지막 로그인 시간을 업데이트합니다."""
    try:
        response = supabase.table("users").update({
            "last_login": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error updating last login: {e}")
        return False


# ==================== Saju Info ====================

def create_saju_info(
    user_id: str,
    year_pillar: str,
    month_pillar: str,
    day_pillar: str,
    hour_pillar: str,
    day_master: str,
    age: int,
    korean_age: int,
    element_strength: Optional[Dict] = None,
    ten_gods: Optional[Dict] = None,
    great_fortunes: Optional[List] = None,
    yearly_fortunes: Optional[List] = None,
    useful_gods: Optional[List] = None,
    taboo_gods: Optional[List] = None
) -> Optional[Dict[str, Any]]:
    """사주 정보를 생성합니다."""
    try:
        response = supabase.table("saju_info").insert({
            "user_id": user_id,
            "year_pillar": year_pillar,
            "month_pillar": month_pillar,
            "day_pillar": day_pillar,
            "hour_pillar": hour_pillar,
            "day_master": day_master,
            "age": age,
            "korean_age": korean_age,
            "element_strength": element_strength,
            "ten_gods": ten_gods,
            "great_fortunes": great_fortunes,
            "yearly_fortunes": yearly_fortunes,
            "useful_gods": useful_gods,
            "taboo_gods": taboo_gods,
        }).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating saju_info: {e}")
        return None


def get_saju_info_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """사용자 ID로 사주 정보를 조회합니다."""
    try:
        response = supabase.table("saju_info").select("*").eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting saju_info: {e}")
        return None


def update_saju_info(user_id: str, **kwargs) -> bool:
    """사주 정보를 업데이트합니다."""
    try:
        kwargs["updated_at"] = datetime.now().isoformat()
        response = supabase.table("saju_info").update(kwargs).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error updating saju_info: {e}")
        return False


# ==================== User Sessions ====================

def create_session(user_id: str, session_token: str, expires_at: str) -> Optional[Dict[str, Any]]:
    """세션을 생성합니다."""
    try:
        response = supabase.table("user_sessions").insert({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at
        }).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating session: {e}")
        return None


def get_session_by_token(session_token: str) -> Optional[Dict[str, Any]]:
    """토큰으로 세션을 조회합니다."""
    try:
        response = supabase.table("user_sessions").select("*").eq("session_token", session_token).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting session: {e}")
        return None


def delete_expired_sessions() -> bool:
    """만료된 세션을 삭제합니다."""
    try:
        now = datetime.now().isoformat()
        response = supabase.table("user_sessions").delete().lt("expires_at", now).execute()
        return True
    except Exception as e:
        print(f"Error deleting expired sessions: {e}")
        return False


# ==================== Conversations ====================

def create_conversation(
    user_id: str,
    session_id: str,
    title: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """대화 세션을 생성합니다."""
    try:
        response = supabase.table("conversations").insert({
            "user_id": user_id,
            "session_id": session_id,
            "title": title
        }).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None


def get_conversation_by_session_id(session_id: str) -> Optional[Dict[str, Any]]:
    """세션 ID로 대화를 조회합니다."""
    try:
        response = supabase.table("conversations").select("*").eq("session_id", session_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting conversation: {e}")
        return None


def get_user_conversations(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """사용자의 대화 목록을 조회합니다."""
    try:
        response = supabase.table("conversations").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting user conversations: {e}")
        return []


def update_conversation_query_count(conversation_id: str) -> bool:
    """대화의 쿼리 카운트를 증가시킵니다."""
    try:
        # 현재 값 조회
        response = supabase.table("conversations").select("query_count").eq("id", conversation_id).execute()
        if response.data:
            current_count = response.data[0].get("query_count", 0)
            supabase.table("conversations").update({
                "query_count": current_count + 1,
                "last_message_at": datetime.now().isoformat()
            }).eq("id", conversation_id).execute()
            return True
        return False
    except Exception as e:
        print(f"Error updating conversation query count: {e}")
        return False


# ==================== Messages ====================

def create_message(
    conversation_id: str,
    role: str,
    content: str,
    query_type: Optional[str] = None,
    agent_name: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """메시지를 생성합니다."""
    try:
        response = supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "query_type": query_type,
            "agent_name": agent_name,
            "metadata": metadata
        }).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating message: {e}")
        return None


def get_conversation_messages(conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """대화의 메시지 목록을 조회합니다."""
    try:
        response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []
