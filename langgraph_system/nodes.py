"""
에이전트 노드들 - 간단한 함수 기반
"""

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from typing import Dict, Any
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

# Supervisor 에이전트
def create_supervisor_agent():
    """Supervisor 에이전트 생성"""
    members = ["SajuAgent", "RagAgent", "WebAgent"]
    options = ["SajuAgent", "RagAgent", "WebAgent", "FINISH"]
    
    system_prompt = f"""당신은 사주 시스템의 감독자입니다. 다음 전문 에이전트들을 관리합니다: {members}

도구들:
- SajuAgent: 생년월일시로부터 사주팔자 계산
- RagAgent: 사주 해석 및 전문 지식 검색  
- WebAgent: 일반 정보 검색

규칙:
1. 생년월일시가 포함된 질문 → SajuAgent 먼저 호출
2. 사주 해석이 필요 → RagAgent 호출
3. 일반 검색이 필요 → WebAgent 호출
4. 모든 작업 완료 → FINISH

다음 중 선택하세요: {options}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "다음에 누가 작업해야 할까요? {options} 중 선택하세요.")
    ]).partial(options=str(options))
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return prompt | llm

def supervisor(state):
    """Supervisor 노드"""
    supervisor_agent = create_supervisor_agent()
    return supervisor_agent.invoke(state)

def response_generator(state):
    """최종 응답 생성"""
    messages = state.get("messages", [])
    
    # 모든 메시지를 종합해서 최종 응답 생성
    final_response = "종합 응답:\n"
    for msg in messages:
        if hasattr(msg, 'name') and hasattr(msg, 'content'):
            final_response += f"\n{msg.name}: {msg.content}\n"
    
    return {
        **state,
        "final_response": final_response,
        "response_generated": True
    }