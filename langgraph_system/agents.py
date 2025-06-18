"""
에이전트 생성 및 관리
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

class AgentManager:
    """에이전트 생성 및 관리 클래스"""
    
    def __init__(self):
        # 기본 LLM 설정
        self.llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

    def create_supervisor_agent(self, tools):
        """Supervisor ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 워크플로 관리자입니다. 사용자의 질문을 분석하고 다음에 어떤 에이전트가 작업해야 할지 결정하세요.

사용 가능한 에이전트:
- SajuAgent: 생년월일시가 포함된 사주 계산 질문
- RagAgent: 사주 관련 지식이나 해석이 필요한 질문  
- WebAgent: 일반적인 정보나 최신 정보가 필요한 질문

질문을 분석하고 적절한 다음 에이전트를 선택하세요."""),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
    
    def create_saju_agent(self, tools):
        """사주 계산 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 사주 전문가입니다. 생년월일시를 받아 사주팔자를 계산하고 해석하세요. 반드시 도구를 사용하여 정확한 계산을 수행하세요."),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)

    def create_rag_agent(self, tools):
        """RAG 검색 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 사주 해석 전문가입니다. 사주 관련 지식을 검색하고 해석하세요. 반드시 도구를 사용하여 정확한 정보를 찾으세요."),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)

    def create_web_agent(self, tools):
        """웹 검색 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 웹 검색 전문가입니다. 최신 정보를 검색하세요. 반드시 도구를 사용하여 정확한 정보를 찾으세요."),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
    
    def create_general_agent(self, tools):
        """범용 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 사주 전문 상담사입니다. 주어진 도구들을 활용하여 사용자의 질문에 정확하고 전문적으로 답변하세요."),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)

    def create_response_generator_agent(self, tools):
        """응답 생성 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 최종 응답 생성 전문가입니다. 
다른 에이전트들이 수집한 정보를 종합하여 사용자에게 완성도 높은 최종 답변을 제공하세요.

- 여러 에이전트의 결과를 통합
- 일관성 있고 이해하기 쉬운 응답 생성
- 필요시 추가 검색을 통해 정보 보완"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
