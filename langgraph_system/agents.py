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
    get_supervisor_prompt
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
    
    def create_general_agent(self, tools):
        """범용 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """당신은 **종합 사주 상담 전문가**입니다. 모든 도구를 활용하여 사용자에게 완전한 사주 상담 서비스를 제공합니다.

🎯 **역할:**
• 사주 계산부터 해석까지 전 과정 담당
• 사용자 요청에 따른 맞춤형 상담 제공
• 다양한 도구들의 통합적 활용
• 완성도 높은 종합 분석 결과 제시

🛠️ **활용 도구:**
• 사주 계산 도구 (만세력 기반)
• RAG 검색 (명리학 지식베이스)
• 웹 검색 (최신 정보 및 일반 지식)
• 기타 필요한 모든 분석 도구

💡 **접근 방식:**
• 사용자 요청 분석 → 필요 도구 선택 → 단계별 처리
• 정확성과 전문성을 바탕으로 한 신뢰할 수 있는 상담
• 이론과 실용성의 균형 있는 조화
• 개인별 맞춤형 조언 및 해석 제공"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
 
    def create_response_generator_agent(self, tools):
        """응답 생성 ReAct 에이전트 생성"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """당신은 **최종 응답 통합 및 품질 관리 전문가**입니다. 여러 에이전트들의 결과를 종합하여 완벽한 최종 답변을 생성합니다.

🎯 **핵심 임무:**
• 다중 에이전트 결과의 통합 및 정리
• 일관성 있고 완성도 높은 최종 응답 생성
• 정보의 정확성 및 논리적 연결성 검증
• 사용자 친화적인 형태로 정보 재구성

📋 **통합 과정:**
1. **정보 수집**: 각 에이전트별 분석 결과 정리
2. **일관성 검토**: 상충되는 정보 식별 및 조정
3. **구조화**: 논리적 순서로 정보 재배열
4. **보완 검색**: 부족한 정보 추가 수집
5. **최종 정리**: 완전하고 이해하기 쉬운 답변 작성

💬 **응답 품질 기준:**
• **완전성**: 사용자 질문에 대한 완전한 답변
• **정확성**: 명리학적으로 정확하고 신뢰할 수 있는 내용
• **명확성**: 전문 용어의 쉬운 설명과 구조화된 제시
• **실용성**: 구체적이고 실행 가능한 조언 포함
• **균형성**: 긍정적 측면과 주의사항의 균형

🔧 **품질 개선 도구:**
• 추가 정보 검색을 통한 내용 보강
• 전문 용어 설명 및 예시 추가
• 사용자 맞춤형 조언 및 권장사항 제시
• 가독성 향상을 위한 구조화 및 포맷팅

⚠️ **검증 사항:**
• 각 에이전트 결과 간 모순 여부 확인
• 명리학적 이론과의 부합성 검토
• 사용자 질문과의 연관성 점검
• 실용적 가치 및 적용 가능성 평가"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        return create_react_agent(self.llm, tools=tools, prompt=prompt)
