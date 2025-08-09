"""
FortuneAI LangGraph 시스템 메인 실행 파일
Supervisor 패턴 기반 사주 계산기
"""

import os
import sys
import time
import uuid
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage, AIMessage
from graph import create_workflow
from langchain_core.runnables import RunnableConfig

# utils.py에서 함수들 import
from utils import (
    print_banner, print_system_info, format_response, print_help,
    handle_debug_query, run_query_with_app
)

# 로깅 시스템 import
from logger_config import get_logger

# 로거 인스턴스 생성
logger = get_logger("Main")

def main() -> None:
    """메인 실행 함수"""
    logger.info("FortuneAI 시스템 시작")
    print_banner()
    print_system_info()
    
    try:
        logger.info("시스템 초기화 시작")

        app = create_workflow()
        logger.info("시스템 초기화 완료")
        
        conversation_history = []
        session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = f"session_{int(time.time())}"
        query_count = 0
        
        print(f"🕐 세션 시작: {session_start_time}")
        print(f"🆔 세션 ID: {session_id}")
        logger.session_info(session_id, "시작")
        
        print("💬 질문을 입력해주세요 (종료: quit/exit, 도움말: help):")
        
    except Exception as e:
        logger.error(f"시스템 초기화 중 오류: {e}")
        print("❌ 시스템 초기화 실패. 프로그램을 종료합니다.")
        return
    
    while True:
        try:
            # 사용자 입력 받기
            user_input = input("\n🤔 질문: ").strip()
            
            # 종료 명령 처리
            if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                logger.session_info(session_id, "종료")
                logger.info("사용자 요청으로 프로그램 종료")
                print("\n👋 FortuneAI를 이용해주셔서 감사합니다!")
                print("🌟 좋은 하루 되세요! 🌟")
                break
            
            # 새 세션 시작 명령 처리
            if user_input.lower() in ['new', 'clear']:
                session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session_id = f"session_{int(time.time())}"
                query_count = 0
                conversation_history = []  # 대화 히스토리 초기화
                print(f"\n🔄 새로운 대화를 시작합니다.")
                print(f"🕐 세션 시작: {session_start_time}")
                print(f"🆔 세션 ID: {session_id}")
                
                # 환영 메시지 생성
                welcome_response = run_query_with_app("안녕하세요! FortuneAI입니다. 무엇을 도와드릴까요?", app, conversation_history, session_start_time, session_id)
                print(f"🔮 FortuneAI: {welcome_response}")
                print("-" * 60)
                continue
            
            # 도움말 명령 처리
            if user_input.lower() in ['help', 'h', '도움말', '?']:
                print_help()
                continue
            
            # 빈 입력 처리
            if not user_input:
                print("❓ 질문을 입력해주세요.")
                continue
            
            query_count += 1
            logger.info(f"질문 처리 시작 - 질문 #{query_count}: {user_input}")
            print(f"\n⏳ 분석 중... (질문 #{query_count})")
            
            # 성능 분석 모드 처리
            analysis_response = handle_debug_query(user_input, app, conversation_history, session_start_time, session_id)
            if analysis_response:
                print(analysis_response)
                continue
            
            # 일반 쿼리 실행 - 상세 스트리밍 표시
            start_time = time.time()
            response = run_query_with_app(user_input, app, conversation_history, session_start_time, session_id)
            execution_time = time.time() - start_time
            
            # 실행 시간 표시
            logger.performance(f"질문 #{query_count}", execution_time, f"질문: {user_input[:50]}...")
            
        except KeyboardInterrupt:
            logger.warning("사용자가 프로그램 중단")
            print("\n\n⚠️  사용자가 중단했습니다.")
            print("👋 FortuneAI를 이용해주셔서 감사합니다!")
            break
            
        except Exception as e:
            logger.error(f"메인 루프 실행 중 오류: {e}")
            print(f"\n❌ 오류 발생: {str(e)}")
            print("🔧 시스템을 다시 시도해보세요.")
            continue

if __name__ == "__main__":
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        conversation_history = []  # 명령행 모드에서도 히스토리 초기화
        session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = f"session_{int(time.time())}"
        
        # --debug 플래그 확인
        is_debug = '--debug' in sys.argv
        if is_debug:
            sys.argv.remove('--debug')
        
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            
            # 시스템 초기화
            print("🔧 시스템 초기화 중...")
            from nodes import get_node_manager
            get_node_manager()
            print("⚙️ 워크플로 생성 중...")
            app = create_workflow()
            print(f"🕐 세션 시작: {session_start_time}")
            print(f"🆔 세션 ID: {session_id}")
            
            if is_debug:
                # 성능 분석 모드
                result = handle_debug_query(f"debug:{query}", app, conversation_history, session_start_time, session_id)
                print(result)
            else:
                # 기본 모드 - 상세 스트리밍 출력
                response = run_query_with_app(query, app, conversation_history, session_start_time, session_id)
                # 상세 스트리밍이 이미 완료됨
        else:
            print("❌ 질문을 입력해주세요.")
            print("사용법: python main.py [--debug] '질문'")
    else:
        # 대화형 모드
        main() 