"""
FortuneAI LangGraph 시스템 메인 실행 파일
Supervisor 패턴 기반 사주 계산기
"""

import os
import sys
import time
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_system.graph import run_query

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

def handle_debug_query(query: str) -> str:
    """디버그 쿼리 처리"""
    if not query.startswith("debug:"):
        return None
    
    actual_query = query[6:].strip()
    if not actual_query:
        return "❌ 디버그할 질문을 입력해주세요. 예: debug:1995년 8월 26일 사주"
    
    print(f"\n🔍 디버그 모드로 실행 중: '{actual_query}'")
    print("-" * 50)
    
    start_time = time.time()
    response = run_query(actual_query)  # 기본 함수 사용
    execution_time = time.time() - start_time
    
    debug_info = f"""
🔍 **디버그 정보**
• 실행 시간: {execution_time:.2f}초
• 질문: {actual_query}

📋 **응답**
{response}
"""
    return debug_info

def handle_verbose_query(query: str) -> str:
    """상세 모드 쿼리 처리"""
    if not query.startswith("verbose:"):
        return None
    
    actual_query = query[8:].strip()
    if not actual_query:
        return "❌ 상세 모드로 실행할 질문을 입력해주세요. 예: verbose:1995년 8월 26일 사주"
    
    print(f"\n🔍 상세 모드로 실행 중: '{actual_query}'")
    print("=" * 60)
    
    start_time = time.time()
    response = run_query(actual_query)  # 기본 함수 사용
    execution_time = time.time() - start_time
    
    print(f"\n⏱️  총 실행 시간: {execution_time:.2f}초")
    return response

def main():
    """메인 실행 함수"""
    print_banner()
    print_system_info()
    
    session_id = f"session_{int(time.time())}"
    query_count = 0
    
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
            
            # 빈 입력 처리
            if not user_input:
                print("❓ 질문을 입력해주세요.")
                continue
            
            query_count += 1
            print(f"\n⏳ 분석 중... (질문 #{query_count})")
            
            # 디버그 모드 처리
            if user_input.startswith("debug:"):
                response = handle_debug_query(user_input)
                print(response)
                continue
            
            # 상세 모드 처리
            if user_input.startswith("verbose:"):
                response = handle_verbose_query(user_input)
                print(f"\n📝 **최종 응답**\n{format_response(response)}")
                continue
            
            # 일반 쿼리 실행
            start_time = time.time()
            response = run_query(user_input)
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

def test_system():
    """시스템 테스트 함수"""
    print("🧪 시스템 테스트 시작...")
    
    test_queries = [
        "1995년 8월 26일 오전 10시 15분 남자 사주 봐주세요",
        "사주에서 십신이란 무엇인가요?",
        "2024년 갑진년 운세는 어떤가요?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: {query}")
        print("-" * 50)
        
        start_time = time.time()
        response = run_query(query)
        execution_time = time.time() - start_time
        
        print(f"✅ 응답 생성 완료 ({execution_time:.2f}초)")
        print(f"📝 응답 길이: {len(response)}자")
        print(f"🎯 응답 미리보기: {response[:100]}...")
        
    print("\n🎉 시스템 테스트 완료!")

if __name__ == "__main__":
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_system()
        elif sys.argv[1] == "debug":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                result = handle_debug_query(f"debug:{query}")
                print(result)
            else:
                print("❌ 디버그할 질문을 입력해주세요.")
                print("사용법: python main_langgraph.py debug '1995년 8월 26일 사주'")
        else:
            # 직접 쿼리 실행
            query = " ".join(sys.argv[1:])
            response = run_query(query)
            print(format_response(response))
    else:
        # 대화형 모드
        main() 