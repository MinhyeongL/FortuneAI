"""
FortuneAI LangGraph 시스템 메인 실행 파일
Supervisor 패턴 기반 사주 계산기
"""

import os
import sys
import time
import uuid
import logging
from datetime import datetime

# httpx 로깅 비활성화 (OpenAI API 호출 로그 숨김)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage
from langgraph_system.graph import create_workflow

def print_banner():
    """시스템 배너 출력"""
    print("=" * 60)
    print("🔮 FortuneAI - LangGraph 사주 시스템 🔮")
    print("=" * 60)
    print("✨ Supervisor 패턴 기반 고성능 사주 계산기")
    print("🎯 98점 전문가 검증 완료")
    print("🚀 LangGraph 멀티 워커 시스템")
    print("-" * 60)
    print("📝 사용법:")
    print("  • 사주 계산: '1995년 8월 26일 오전 10시 15분 남자 사주'")
    print("  • 운세 상담: '1995년 8월 26일생 2024년 연애운'")
    print("  • 일반 검색: '사주에서 십신이란?'")
    print("  • 종료: 'quit' 또는 'exit'")
    print("  • 디버그: 'debug:질문' (상세 실행 정보)")
    print("  • 상세모드: 'verbose:질문' (노드별 상세 로깅)")
    print("  • 고급스트리밍: 'stream:질문' (주요 노드만 실시간 출력)")
    print("=" * 60)

def print_system_info():
    """시스템 정보 출력"""
    print("\n🔧 시스템 정보:")
    print(f"  • 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  • Python 버전: {sys.version.split()[0]}")
    print(f"  • 작업 디렉토리: {os.getcwd()}")
    print(f"  • 워커 노드: Supervisor, 사주계산, RAG검색, 웹검색, 응답생성")
    print()

def format_response(response: str) -> str:
    """응답 포맷팅"""
    if not response:
        return "❌ 응답을 생성할 수 없습니다."
    
    # 응답 앞에 구분선 추가
    formatted = "\n" + "🎯 " + "=" * 55 + "\n"
    formatted += "📋 **FortuneAI 분석 결과**\n"
    formatted += "=" * 58 + "\n\n"
    formatted += response
    formatted += "\n\n" + "=" * 58
    
    return formatted

def handle_debug_query(query: str, app, conversation_history: list) -> str:
    """디버그 쿼리 처리"""
    if not query.startswith("debug:"):
        return None
    
    actual_query = query[6:].strip()
    if not actual_query:
        return "❌ 디버그할 질문을 입력해주세요. 예: debug:1995년 8월 26일 사주"
    
    print(f"\n🔍 디버그 모드로 실행 중: '{actual_query}'")
    print("-" * 50)
    
    start_time = time.time()
    response = run_query_with_app(actual_query, app, conversation_history)
    execution_time = time.time() - start_time
    
    debug_info = f"""
🔍 **디버그 정보**
• 실행 시간: {execution_time:.2f}초
• 질문: {actual_query}

📋 **응답**
{response}
"""
    return debug_info

def handle_verbose_query(query: str, app, conversation_history: list) -> str:
    """상세 모드 쿼리 처리"""
    if not query.startswith("verbose:"):
        return None
    
    actual_query = query[8:].strip()
    if not actual_query:
        return "❌ 상세 모드로 실행할 질문을 입력해주세요. 예: verbose:1995년 8월 26일 사주"
    
    print(f"\n🔍 상세 모드로 실행 중: '{actual_query}'")
    print("=" * 60)
    
    start_time = time.time()
    response = run_query_with_app(actual_query, app, conversation_history)
    execution_time = time.time() - start_time
    
    print(f"\n⏱️  총 실행 시간: {execution_time:.2f}초")
    return response

def handle_stream_query(query: str, app, conversation_history: list) -> str:
    """고급 스트리밍 쿼리 처리 - 특정 노드만 필터링"""
    if not query.startswith("stream:"):
        return None
    
    actual_query = query[7:].strip()
    if not actual_query:
        return "❌ 고급 스트리밍할 질문을 입력해주세요. 예: stream:1995년 8월 26일 사주"
    
    print(f"\n🌊 고급 스트리밍 모드로 실행 중: '{actual_query}'")
    print("📌 주요 노드(rag_agent, response_generator)만 표시됩니다")
    print("=" * 60)
    
    start_time = time.time()
    response = run_query_with_streaming(actual_query, app, conversation_history)
    execution_time = time.time() - start_time
    
    print(f"\n⏱️  총 실행 시간: {execution_time:.2f}초")
    return response

def run_query_with_app(query: str, app, conversation_history: list) -> str:
    """LangGraph 시스템으로 쿼리 실행 - stream_graph 방식으로 실시간 출력"""
    print(f"🔍 쿼리 실행: {query}")
    
    # 새로운 사용자 메시지를 히스토리에 추가
    conversation_history.append(HumanMessage(content=query))
    
    # 현재 상태 설정 (전체 대화 히스토리 포함)
    current_state = {
        "messages": conversation_history.copy(),
        "next": None,
        "final_response": None,
        "sender": None
    }
    
    try:
        print("🚀 워크플로 실행 중...")
        
        # stream_graph 방식으로 스트리밍 출력
        final_response = ""
        prev_node = ""
        
        for chunk_msg, metadata in app.stream(current_state, stream_mode="messages"):
            curr_node = metadata["langgraph_node"]
            
            # 노드가 변경된 경우에만 구분선 출력
            if curr_node != prev_node:
                print("\n" + "=" * 50)
                print(f"🔄 Node: \033[1;36m{curr_node}\033[0m 🔄")
                print("- " * 25)
            
            # 토큰별로 실시간 출력
            if chunk_msg.content:
                print(chunk_msg.content, end="", flush=True)
            
            prev_node = curr_node
        
        print("\n" + "=" * 50)
        print("✅ 스트리밍 완료!")
        
        # 최종 응답을 얻기 위해 한 번 더 실행 (final_response 획득용)
        result = app.invoke(current_state)
        final_response = result.get("final_response")
        
        if final_response:
            # AI 응답도 히스토리에 추가
            from langchain_core.messages import AIMessage
            conversation_history.append(AIMessage(content=final_response))
            return final_response
        else:
            print("❌ 최종 응답 생성 실패")
            return "응답을 생성하지 못했습니다."
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return f"오류가 발생했습니다: {str(e)}"

def run_query_with_streaming(query: str, app, conversation_history: list) -> str:
    """향상된 스트리밍 - 특정 노드만 필터링하여 출력"""
    print(f"🔍 쿼리 실행 (고급 스트리밍): {query}")
    
    # 새로운 사용자 메시지를 히스토리에 추가
    conversation_history.append(HumanMessage(content=query))
    
    current_state = {
        "messages": conversation_history.copy(),
        "next": None,
        "final_response": None,
        "sender": None
    }
    
    try:
        print("🚀 워크플로 실행 중...")
        
        # stream_graph 방식 + 노드 필터링
        final_response = ""
        prev_node = ""
        target_nodes = ["rag_agent", "response_generator"]  # 원하는 노드만 출력
        
        for chunk_msg, metadata in app.stream(current_state, stream_mode="messages"):
            curr_node = metadata["langgraph_node"]
            
            # 특정 노드들만 출력
            if curr_node in target_nodes:
                # 노드가 변경된 경우에만 구분선 출력
                if curr_node != prev_node:
                    print("\n" + "=" * 50)
                    print(f"🔄 Node: \033[1;36m{curr_node}\033[0m 🔄")
                    print("- " * 25)
                
                # 토큰별로 실시간 출력
                if chunk_msg.content:
                    print(chunk_msg.content, end="", flush=True)
                
                prev_node = curr_node
        
        print("\n" + "=" * 50)
        print("✅ 고급 스트리밍 완료!")
        
        # 최종 응답 획득
        result = app.invoke(current_state)
        final_response = result.get("final_response")
        
        if final_response:
            from langchain_core.messages import AIMessage
            conversation_history.append(AIMessage(content=final_response))
            return final_response
        else:
            print("❌ 고급 스트리밍에서 응답을 찾을 수 없어 기본 방식으로 재시도...")
            return run_query_with_app(query, app, conversation_history[:-1])
            
    except Exception as e:
        print(f"❌ 고급 스트리밍 오류 발생: {str(e)}")
        print("🔄 기본 방식으로 재시도...")
        return run_query_with_app(query, app, conversation_history[:-1])

def main():
    """메인 실행 함수"""
    print_banner()
    print_system_info()
    
    # ✨ 시스템 시작 시 NodeManager 미리 초기화
    print("🔧 시스템 초기화 중...")
    from langgraph_system.nodes import get_node_manager
    get_node_manager()  # 싱글톤 초기화 (6-10초 소요)
    print("✅ 시스템 초기화 완료!")
    
    # ✨ 워크플로도 미리 생성
    print("⚙️ 워크플로 생성 중...")
    app = create_workflow()
    print("✅ 워크플로 준비 완료!")
    
    session_id = f"session_{int(time.time())}"
    query_count = 0
    conversation_history = []  # 🔥 대화 히스토리 초기화
    
    print("💬 질문을 입력해주세요 (종료: quit/exit):")
    
    while True:
        try:
            # 사용자 입력 받기
            user_input = input("\n🤔 질문: ").strip()
            
            # 종료 명령 처리
            if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                print("\n👋 FortuneAI를 이용해주셔서 감사합니다!")
                print("🌟 좋은 하루 되세요! 🌟")
                break
            
            # 새 세션 시작 명령 처리
            if user_input.lower() == 'new':
                session_id = str(uuid.uuid4())
                query_count = 0
                conversation_history = []  # 🔥 대화 히스토리 초기화
                print(f"\n🔄 새로운 대화를 시작합니다. (세션 ID: {session_id[:8]}...)")
                
                # 환영 메시지 생성
                welcome_response = run_query_with_app("안녕하세요! FortuneAI입니다. 무엇을 도와드릴까요?", app, conversation_history)
                print(f"🔮 FortuneAI: {welcome_response}")
                print("-" * 60)
                continue
            
            # 도움말 명령 처리
            if user_input.lower() in ['help', 'h', '도움말', '?']:
                print("""
📚 **FortuneAI 사용 가이드**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔮 **사주 계산**: '1995년 8월 26일 오전 10시 15분 남자 사주'
📖 **사주 해석**: '사주에서 십신이란 무엇인가요?'
🌐 **일반 질문**: '2024년 갑진년의 특징은?'

🛠️  **특수 명령어**:
  • new, clear      : 새로운 세션 시작
  • help, ?         : 도움말 보기
  • quit, exit      : 프로그램 종료
  • debug:질문      : 디버그 모드로 실행
  • verbose:질문    : 상세 모드로 실행
  • stream:질문     : 고급 스트리밍 (주요 노드만)

🌊 **스트리밍 설명**:
  • 기본 실행: 모든 노드의 토큰을 실시간 표시 (stream_graph 방식)
  • stream: 명령: 주요 노드(rag_agent, response_generator)만 표시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """)
                continue
            
            # 빈 입력 처리
            if not user_input:
                print("❓ 질문을 입력해주세요.")
                continue
            
            query_count += 1
            print(f"\n⏳ 분석 중... (질문 #{query_count})")
            
            # 디버그 모드 처리
            if user_input.startswith("debug:"):
                response = handle_debug_query(user_input, app, conversation_history)
                print(response)
                continue
            
            # 상세 모드 처리
            if user_input.startswith("verbose:"):
                response = handle_verbose_query(user_input, app, conversation_history)
                print(f"\n📝 **최종 응답**\n{format_response(response)}")
                continue
            
            # 스트리밍 쿼리 처리
            if user_input.startswith("stream:"):
                response = handle_stream_query(user_input, app, conversation_history)
                print(f"\n📝 **최종 응답**\n{format_response(response)}")
                continue
            
            # 일반 쿼리 실행 - 미리 생성된 워크플로 사용
            start_time = time.time()
            response = run_query_with_app(user_input, app, conversation_history)  # 대화 히스토리 전달
            execution_time = time.time() - start_time
            
            # 응답 출력
            formatted_response = format_response(response)
            print(formatted_response)
            
            # 실행 시간 표시
            print(f"\n⏱️  실행 시간: {execution_time:.2f}초")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  사용자가 중단했습니다.")
            print("👋 FortuneAI를 이용해주셔서 감사합니다!")
            break
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}")
            print("🔧 시스템을 다시 시도해보세요.")
            continue

if __name__ == "__main__":
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        if sys.argv[1] == "debug":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                # 명령행에서는 워크플로를 새로 생성
                print("🔧 시스템 초기화 중...")
                from langgraph_system.nodes import get_node_manager
                get_node_manager()
                print("⚙️ 워크플로 생성 중...")
                app = create_workflow()
                conversation_history = []
                result = handle_debug_query(f"debug:{query}", app, conversation_history)
                print(result)
            else:
                print("❌ 디버그할 질문을 입력해주세요.")
                print("사용법: python main_langgraph.py debug '1995년 8월 26일 사주'")
        else:
            # 직접 쿼리 실행
            query = " ".join(sys.argv[1:])
            print("🔧 시스템 초기화 중...")
            from langgraph_system.nodes import get_node_manager
            get_node_manager()
            print("⚙️ 워크플로 생성 중...")
            app = create_workflow()
            conversation_history = []
            response = run_query_with_app(query, app, conversation_history)
            print(format_response(response))
    else:
        # 대화형 모드
        main() 