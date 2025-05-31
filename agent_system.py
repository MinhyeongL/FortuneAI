"""
FortuneAI Agent System
확장 가능한 사주 상담 에이전트 시스템
"""

import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 환경 변수 로드
load_dotenv()

# 모델 import
from models import get_openai_llm, get_gemini_llm

# 통합 도구 시스템 import
from tools import ToolManager

class FortuneAgentSystem:
    """확장 가능한 FortuneAI Agent 시스템"""
    
    def __init__(self, use_openai: bool = False, enable_web: bool = False, enable_calendar: bool = False):
        """
        Agent 시스템 초기화
        
        Args:
            use_openai: OpenAI 모델 사용 여부 (기본값: False, Gemini 사용)
            enable_web: 웹 검색 도구 활성화 여부
            enable_calendar: 만세력 도구 활성화 여부
        """
        self.use_openai = use_openai
        self.enable_web = enable_web
        self.enable_calendar = enable_calendar
        
        self.llm = None
        self.tool_manager = None
        self.tools = []
        self.agent_executor = None
        self.agent_with_chat_history = None
        self.session_store = {}
        
        self.setup_system()
    
    def setup_system(self):
        """전체 시스템 설정"""
        self.setup_llm()
        self.setup_tools()
        self.setup_agent()
    
    def setup_llm(self):
        """LLM 모델 설정"""
        if self.use_openai:
            print("🤖 OpenAI 모델 초기화 중...")
            self.llm = get_openai_llm("gpt-4o-mini")
        else:
            print("🤖 Gemini 모델 초기화 중...")
            self.llm = get_gemini_llm("gemini-2.0-flash")
        
        print("✅ LLM 모델 초기화 완료!")
    
    def setup_tools(self):
        """도구들 설정"""
        # 통합 도구 관리자 초기화
        self.tool_manager = ToolManager(
            enable_rag=True,  # RAG는 항상 활성화
            enable_web=self.enable_web,
            enable_calendar=self.enable_calendar
        )
        
        # 도구들 가져오기
        self.tools = self.tool_manager.get_tools()
    
    def setup_agent(self):
        """Agent 설정"""
        print("🤖 Agent 설정 중...")
        
        # 현재 날짜 정보 가져오기
        current_date = datetime.now()
        today_info = f"{current_date.year}년 {current_date.month}월 {current_date.day}일 ({current_date.strftime('%A')})"
        korean_weekdays = {
            'Monday': '월요일',
            'Tuesday': '화요일', 
            'Wednesday': '수요일',
            'Thursday': '목요일',
            'Friday': '금요일',
            'Saturday': '토요일',
            'Sunday': '일요일'
        }
        today_korean = f"{current_date.year}년 {current_date.month}월 {current_date.day}일 ({korean_weekdays[current_date.strftime('%A')]})"
        
        # 도구 목록 생성
        tool_descriptions = []
        for i, tool in enumerate(self.tools, 1):
            tool_descriptions.append(f"{i}. {tool.name}: {tool.description}")
        
        tools_text = "\n".join(tool_descriptions)
        
        # Agent 프롬프트 정의
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 전문적인 사주 상담사 AI 에이전트입니다. 다음 도구들을 활용하여 사용자에게 정확하고 친절한 사주 상담을 제공하세요.

현재 날짜 정보: {today_korean}

사용 가능한 도구:
{tools_text}

상담 가이드라인:
- 사용자가 생년월일시를 제공하면 적절한 분석 도구를 사용하세요
- 특정 운세 질문이 있으면 관련 도구를 사용하여 분석하세요
- 사주 개념이나 용어 설명이 필요하면 지식 검색 도구를 사용하세요
- 실시간 정보가 필요하면 웹 검색 도구를 활용하세요
- 정확한 사주팔자 계산이 필요하면 만세력 도구를 사용하세요
- 오늘 날짜를 기준으로 운세나 분석을 제공할 때는 위의 현재 날짜 정보를 참고하세요
- 항상 친절하고 이해하기 쉽게 설명하세요
- 한 번에 너무 많은 정보를 제공하지 말고 단계적으로 진행하세요
- 사용자의 질문에 맞는 적절한 도구를 선택하여 사용하세요

대화를 시작할 때는 간단히 인사하고 어떤 도움이 필요한지 물어보세요."""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Agent 생성
        agent = create_tool_calling_agent(self.llm, self.tools, agent_prompt)
        
        # AgentExecutor 생성
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=False,  # 중간 과정 출력 숨김
            max_iterations=3,
            early_stopping_method="generate"
        )
        
        # 대화 기록을 포함한 Agent 생성
        self.agent_with_chat_history = RunnableWithMessageHistory(
            self.agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
        print("✅ Agent 설정 완료!")
    
    def get_session_history(self, session_id: str):
        """세션별 대화 기록을 관리하는 함수"""
        if session_id not in self.session_store:
            self.session_store[session_id] = ChatMessageHistory()
        return self.session_store[session_id]
    
    def chat(self, message: str, session_id: str = None) -> str:
        """사용자와 대화하는 메인 함수"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        try:
            response = self.agent_with_chat_history.invoke(
                {"input": message},
                config={"configurable": {"session_id": session_id}}
            )
            return response['output']
        except Exception as e:
            return f"죄송합니다. 오류가 발생했습니다: {str(e)}"
    
    def interactive_chat(self):
        """대화형 채팅 시스템"""
        session_id = str(uuid.uuid4())
        
        print("=== FortuneAI Agent 대화형 상담 ===")
        print("💬 언제든지 질문해주세요!")
        print("💡 종료하려면 'quit', 'exit', 'q' 중 하나를 입력하세요.")
        print("🔄 새 대화를 시작하려면 'new'를 입력하세요.")
        print(f"🛠️ 활성화된 도구: {len(self.tools)}개")
        print("-" * 60)
        
        # 첫 인사
        welcome_message = self.chat("안녕하세요", session_id)
        print(f"🔮 AI 상담사: {welcome_message}")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\n🙋 사용자: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n🌟 상담을 종료합니다. 좋은 하루 되세요! 🌟")
                    break
                    
                if user_input.lower() == 'new':
                    session_id = str(uuid.uuid4())
                    print(f"\n🔄 새로운 대화를 시작합니다. (세션 ID: {session_id[:8]}...)")
                    welcome_message = self.chat("안녕하세요", session_id)
                    print(f"🔮 AI 상담사: {welcome_message}")
                    print("-" * 60)
                    continue
                
                # AI 응답 생성
                response = self.chat(user_input, session_id)
                print(f"\n🔮 AI 상담사: {response}")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n🌟 상담을 종료합니다. 좋은 하루 되세요! 🌟")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                print("다시 질문해 주세요.")
    
    def get_system_info(self):
        """시스템 정보 출력"""
        tool_info = self.tool_manager.get_tool_info()
        
        print("\n=== FortuneAI Agent 시스템 정보 ===")
        print(f"🤖 LLM 모델: {'OpenAI GPT-4o-mini' if self.use_openai else 'Google Gemini 2.0 Flash'}")
        print(f"🛠️ 활성화된 도구 수: {tool_info['total_tools']}개")
        print(f"🔧 RAG 도구: {'활성화' if tool_info['rag_enabled'] else '비활성화'}")
        print(f"🌐 웹 검색: {'활성화' if tool_info['web_enabled'] else '비활성화'}")
        print(f"📅 만세력: {'활성화' if tool_info['calendar_enabled'] else '비활성화'}")
        print("=" * 40)

def main():
    """메인 실행 함수"""
    print("🌟 FortuneAI Agent 시스템 시작 🌟\n")
    
    # Agent 시스템 초기화 (웹 검색 도구 활성화)
    # 확장하려면: FortuneAgentSystem(use_openai=True, enable_web=True, enable_calendar=True)
    agent_system = FortuneAgentSystem(
        use_openai=False,      # Gemini 사용
        enable_web=True,       # 웹 검색 활성화
        enable_calendar=False  # 만세력 비활성화
    )
    
    # 시스템 정보 출력
    agent_system.get_system_info()
    
    # 대화형 채팅 시작
    agent_system.interactive_chat()

if __name__ == "__main__":
    main() 