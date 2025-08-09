"""
에이전트 생성 및 관리
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, load_prompt
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_tool_calling_agent, AgentExecutor
from prompts import PromptManager
from logger_config import get_logger

# 로거 인스턴스 생성
logger = get_logger("AgentManager")

# 단순화된 tools import (노트북 방식)
from tools import (
    saju_tools,
    search_tools,
    general_qa_tools,
    supervisor_tools
)

# 멤버 Agent 목록 정의 (notebook 구조에 맞게 변경)
members = ["SajuExpert", "Search", "GeneralAnswer"]


class AgentManager:
    """에이전트 생성 및 관리 클래스"""
    
    def __init__(self) -> None:
        # 기본 LLM 설정
        self.llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
        logger.info("AgentManager 초기화 완료")
    
    def create_supervisor_agent(self, input_state: Dict[str, Any]):
        """
        Supervisor Agent를 생성합니다.
        State 정보를 동적으로 프롬프트에 주입합니다.
        """
        llm = ChatOpenAI(temperature=0, model="gpt-4.1")
        
        # Agent용 프롬프트 템플릿
        prompt = PromptManager().supervisor_system_prompt(input_state)
        
        # Agent 생성
        react_agent = create_react_agent(
            model=llm,
            tools=supervisor_tools,
            prompt=prompt
        )

        return react_agent
    
    def create_saju_expert_agent(self) -> AgentExecutor:
        """사주 전문 에이전트 생성"""
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
        prompt = PromptManager().saju_expert_system_prompt()

        agent = create_tool_calling_agent(llm, saju_tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=saju_tools,
            verbose=True,
            max_iterations=3
        )
        return agent_executor
    
    def create_search_agent(self) -> AgentExecutor:
        """Search Agent 생성 (RAG 검색 + 웹 검색 통합)"""
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
        prompt = PromptManager().search_system_prompt()
        
        agent = create_tool_calling_agent(llm, search_tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=search_tools,
            verbose=True,
            max_iterations=3
        )

        return agent_executor
    
    def create_general_answer_agent(self) -> AgentExecutor:
        """General Answer Agent 생성"""
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
        prompt = PromptManager().general_answer_system_prompt()
        
        agent = create_tool_calling_agent(llm, general_qa_tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=general_qa_tools,
            verbose=True,
            max_iterations=3
        )
        
        return agent_executor
