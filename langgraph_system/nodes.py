"""
에이전트 노드들 - 모든 노드와 supervisor 통합 관리
"""

import re
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import functools

from .state import SupervisorState

# 기본 에이전트 노드 생성 함수
def agent_node(state, agent, name):
    """지정한 agent와 name을 사용하여 agent 노드를 생성"""
    # agent 호출
    agent_response = agent.invoke(state)
    # agent의 마지막 메시지를 HumanMessage로 변환하여 반환
    return {
        "messages": [
            HumanMessage(content=agent_response["messages"][-1].content, name=name)
        ]
    }

# 간단한 워커 에이전트들
def create_saju_agent():
    """사주 계산 에이전트 생성"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 사주 전문가입니다. 생년월일시를 받아 사주팔자를 계산하세요."),
        MessagesPlaceholder(variable_name="messages")
    ])
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    return prompt | llm

def create_rag_agent():
    """RAG 검색 에이전트 생성"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 사주 해석 전문가입니다. 사주 관련 지식을 검색하고 해석하세요."),
        MessagesPlaceholder(variable_name="messages")
    ])
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    return prompt | llm

def create_web_agent():
    """웹 검색 에이전트 생성"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 웹 검색 전문가입니다. 최신 정보를 검색하세요."),
        MessagesPlaceholder(variable_name="messages")
    ])
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    return prompt | llm

# 에이전트 인스턴스 생성
saju_agent = create_saju_agent()
rag_agent = create_rag_agent()
web_agent = create_web_agent()

# functools.partial을 사용한 노드 생성
saju_worker = functools.partial(agent_node, agent=saju_agent, name="SajuAgent")
rag_worker = functools.partial(agent_node, agent=rag_agent, name="RagAgent")
web_worker = functools.partial(agent_node, agent=web_agent, name="WebAgent")

# =============================================================================
# SUPERVISOR 관련 함수들
# =============================================================================

def _is_fortune_related(query: str) -> bool:
    """운세/사주 관련 질문 여부 판단"""
    fortune_keywords = [
        '사주', '운세', '팔자', '명리', '오행', '천간', '지지', 
        '년주', '월주', '일주', '시주', '대운', '세운', '궁합',
        '타로', '점', '운명', '미래', '점괘'
    ]
    return any(keyword in query for keyword in fortune_keywords)

def _is_simple_question(query: str) -> bool:
    """간단한 일반 질문 여부 판단"""
    simple_keywords = [
        '안녕', '오늘', '날짜', '시간', '몇시', '몇월', '며칠',
        '날씨', '인사', '감사', '고마워'
    ]
    return any(keyword in query for keyword in simple_keywords)

def _extract_birth_info(query: str) -> Dict[str, Any]:
    """생년월일시 정보 추출"""
    # 간단한 패턴 매칭으로 생년월일시 추출
    patterns = [
        r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
        r'(\d{4})\s*(\d{1,2})\s*(\d{1,2})',
        r'(\d{2,4})[./\-](\d{1,2})[./\-](\d{1,2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            year, month, day = match.groups()
            return {
                'year': int(year) if len(year) == 4 else int(year) + 2000,
                'month': int(month),
                'day': int(day),
                'found': True
            }
    
    return {'found': False}

def supervisor(state: SupervisorState) -> SupervisorState:
    """Supervisor 노드 - 중앙 제어 및 워커 관리"""
    messages = state.get("messages", [])
    if not messages:
        return state
    
    # 현재 질문 추출
    current_query = messages[-1].content if messages else ""
    
    # 현재 날짜 정보
    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 간단한 질문 체크
    if _is_simple_question(current_query):
            return {
        **state,
        "messages": state["messages"] + [
            HumanMessage(content="FINISH", name="supervisor")
        ]
    }
    
    # 생년월일시 정보 추출
    birth_info = _extract_birth_info(current_query)
    
    # 운세 관련 질문인지 확인
    is_fortune = _is_fortune_related(current_query)
    
    # 워커 할당 로직
    if birth_info['found'] and is_fortune:
        # 생년월일시가 있는 사주 질문 → 사주 계산 먼저
        next_worker = "SajuAgent"
    elif is_fortune:
        # 사주 관련이지만 생년월일시 없음 → RAG 검색
        next_worker = "RagAgent"  
    else:
        # 일반 질문 → 웹 검색
        next_worker = "WebAgent"
    
    # 이미 여러 워커가 작업했다면 종료
    worker_count = sum(1 for msg in messages if hasattr(msg, 'name') and 'Agent' in msg.name)
    if worker_count >= 2:
        next_worker = "FINISH"
    
    return {
        **state,
        "messages": state["messages"] + [
            HumanMessage(content=next_worker, name="supervisor")
        ]
    }

def response_generator(state: SupervisorState) -> SupervisorState:
    """최종 응답 생성"""
    messages = state.get("messages", [])
    
    # 첫 번째 메시지가 사용자 질문 (name이 없는 메시지)
    original_query = messages[0].content if messages else ""
    
    # 간단한 질문 처리
    if _is_simple_question(original_query):
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        
        if any(keyword in original_query for keyword in ['오늘', '날짜', '몇월', '며칠']):
            simple_response = f"오늘은 {current_date}입니다."
        else:
            simple_response = "안녕하세요! 사주 관련 질문이 있으시면 언제든 물어보세요."
        
        return {
            **state,
            "final_response": simple_response,
            "response_generated": True
        }
    
    # Agent 응답들을 수집
    agent_responses = []
    for msg in messages:
        if hasattr(msg, 'name') and hasattr(msg, 'content') and 'Agent' in str(getattr(msg, 'name', '')):
            agent_responses.append(f"{msg.name}: {msg.content}")
    
    # 최종 응답 생성
    if agent_responses:
        final_response = "종합 응답:\n" + "\n".join(agent_responses)
    else:
        # Agent 응답이 없으면 기본 응답
        final_response = f"질문 '{original_query}'에 대한 응답을 생성할 수 없습니다."
    
    return {
        **state,
        "final_response": final_response,
        "response_generated": True
    }