"""
에이전트 생성 및 관리
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from typing import Literal

# prompts.py에서 프롬프트 함수들 import
from prompts import (
    get_saju_calculation_prompt,
    get_saju_interpretation_prompt,
    get_web_search_prompt,
    get_supervisor_prompt,
    get_response_generator_prompt
)

# 멤버 Agent 목록 정의
members = ["SajuAgent", "RagAgent", "WebAgent"]

# 다음 작업자 선택 옵션 목록 정의
options_for_next = ["FINISH"] + members

# 작업자 선택 응답 모델 정의: 다음 작업자를 선택하거나 작업 완료를 나타냄
class RouteResponse(BaseModel):
    next: Literal[*options_for_next]

class AgentManager:
    """에이전트 생성 및 관리 클래스"""
    
    def __init__(self):
        # 기본 LLM 설정
        self.llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    
    def create_supervisor_agent(self, tools):
        """Supervisor ReAct 에이전트 생성 - prompts.py 활용"""
        system_prompt = get_supervisor_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "위 대화를 바탕으로 다음에 어떤 에이전트가 작업해야 할까요? "
                "또는 작업을 완료해야 할까요? 다음 중에서 선택하세요: {options}",
            ),
        ]).partial(
            options=str(options_for_next), 
            members=", ".join(members)
        )
        
        # Supervisor Agent 생성 (구조화된 출력 사용)
        def supervisor_agent(state):
            supervisor_chain = prompt | self.llm.with_structured_output(RouteResponse)
            return supervisor_chain.invoke(state)
        
        return supervisor_agent
    
    def create_saju_agent(self, tools):
        """사주 계산 ReAct 에이전트 생성 - prompts.py 활용"""
        system_prompt = get_saju_calculation_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)

    def create_rag_agent(self, tools):
        """RAG 검색 ReAct 에이전트 생성 - prompts.py 활용"""
        system_prompt = get_saju_interpretation_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)

    def create_web_agent(self, tools):
        """웹 검색 ReAct 에이전트 생성 - prompts.py 활용"""
        system_prompt = get_web_search_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
 
    def create_response_generator_agent(self, tools):
        """응답 생성 ReAct 에이전트 생성 - prompts.py 활용"""
        system_prompt = get_response_generator_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
