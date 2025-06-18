"""
NodeManager 기반 LangGraph
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from .state import SupervisorState
from .nodes import NodeManager

# 전역 NodeManager 인스턴스 (한 번만 초기화)
_node_manager = None

def get_node_manager():
    """NodeManager 싱글톤 반환"""
    global _node_manager
    if _node_manager is None:
        print("🔧 NodeManager 초기화 중...")
        _node_manager = NodeManager()
        print("✅ NodeManager 초기화 완료!")
    return _node_manager

def route_supervisor(state: SupervisorState) -> str:
    """Supervisor 결과에 따라 다음 노드 결정"""
    # Supervisor가 반환한 응답에서 다음 에이전트 추출
    messages = state["messages"]
    if messages:
        last_message = messages[-1].content
        
        if "SajuAgent" in last_message:
            return "saju_worker"
        elif "RagAgent" in last_message:
            return "rag_worker"
        elif "WebAgent" in last_message:
            return "web_worker"
        elif "FINISH" in last_message:
            return "response_generator"
    
    return "response_generator"

def create_graph():
    """NodeManager 기반 그래프 생성"""
    # 싱글톤 NodeManager 사용
    node_manager = get_node_manager()
    
    # 모든 노드 생성
    supervisor_node = node_manager.create_supervisor_node()
    saju_worker = node_manager.create_saju_node()
    rag_worker = node_manager.create_rag_node()
    web_worker = node_manager.create_web_node()
    response_generator = node_manager.create_response_generator_node()
    
    # 그래프 생성
    workflow = StateGraph(SupervisorState)
    
    # 노드 추가
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("saju_worker", saju_worker)
    workflow.add_node("rag_worker", rag_worker)
    workflow.add_node("web_worker", web_worker)
    workflow.add_node("response_generator", response_generator)
    
    # 시작점
    workflow.set_entry_point("supervisor")
    
    # Supervisor에서 조건부 라우팅
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "saju_worker": "saju_worker",
            "rag_worker": "rag_worker",
            "web_worker": "web_worker",
            "response_generator": "response_generator"
        }
    )
    
    # 모든 워커는 다시 supervisor로
    workflow.add_edge("saju_worker", "supervisor")
    workflow.add_edge("rag_worker", "supervisor")
    workflow.add_edge("web_worker", "supervisor")
    
    # 응답 생성 후 종료
    workflow.add_edge("response_generator", END)
    
    return workflow.compile()

def run_query(query: str) -> str:
    """간단한 실행 함수"""
    app = create_graph()
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next": None,
        "final_response": None,
        "response_generated": False
    }
    
    try:
        result = app.invoke(initial_state)
        return result.get("final_response", "응답 생성 실패")
    except Exception as e:
        return f"오류 발생: {str(e)}" 