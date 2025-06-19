"""
노드 함수들 - NodeManager 클래스로 노드 생성 및 관리
"""

import re
import functools
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List

from .state import SajuState
from .agents import AgentManager
from tools import ToolManager

class NodeManager:
    """노드 생성 및 관리 클래스"""
    
    def __init__(self):
        # 도구 관리자 초기화
        self.tool_manager = ToolManager(
            enable_rag=True,
            enable_web=True, 
            enable_calendar=True
        )
        # 에이전트 관리자 초기화
        self.agent_manager = AgentManager()
    
    def create_saju_node(self):
        """사주 계산 노드 생성 - 사주 계산 도구만 사용"""
        calendar_tools = self.tool_manager._get_calendar_tools()
        agent = self.agent_manager.create_saju_agent(calendar_tools)
        return functools.partial(agent_node, agent=agent, name="SajuAgent")
    
    def create_rag_node(self):
        """RAG 검색 노드 생성 - RAG 도구만 사용"""
        rag_tools = self.tool_manager._get_rag_tools()
        agent = self.agent_manager.create_rag_agent(rag_tools)
        return functools.partial(agent_node, agent=agent, name="RagAgent")
    
    def create_web_node(self):
        """웹 검색 노드 생성 - 웹 도구만 사용"""
        web_tools = self.tool_manager._get_web_tools()
        agent = self.agent_manager.create_web_agent(web_tools)
        return functools.partial(agent_node, agent=agent, name="WebAgent")
    
    def create_supervisor_node(self):
        """Supervisor 노드 생성 - 워크플로 관리 에이전트"""
        # 일단 모든 도구 사용 (나중에 워크플로 전용 도구로 변경)
        all_tools = self.tool_manager.get_tools()
        agent = self.agent_manager.create_supervisor_agent(all_tools)
        return functools.partial(agent_node, agent=agent, name="Supervisor")
    
    def create_response_generator_node(self):
        """응답 생성 노드 생성 - 최종 응답 생성 에이전트"""
        # RAG 도구만 사용해서 최종 응답 생성
        rag_tools = self.tool_manager._get_rag_tools()
        agent = self.agent_manager.create_response_generator_agent(rag_tools)
        return functools.partial(agent_node, agent=agent, name="ResponseGenerator")

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
