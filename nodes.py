"""
노드 함수들 - NodeManager 클래스로 노드 생성 및 관리
"""
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import add_messages
import re
import json

from agents import AgentManager


class NodeManager:
    """노드 생성 및 관리 클래스"""
    
    def __init__(self):
        # 에이전트 관리자 초기화 (단순화)
        self.agent_manager = AgentManager()
        
    def supervisor_agent_node(self, state):
        """Supervisor React Agent 노드"""
        print("🔧 Supervisor 노드 실행")

        input_state = {
            "question": state.get("question", ""),
            "current_time": state.get("current_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "session_id": state.get("session_id", "unknown"),
            "session_start_time": state.get("session_start_time", "unknown"),
            "birth_info": state.get("birth_info"),
            "saju_result": state.get("saju_result"),
            "query_type": state.get("query_type", "unknown"),
            "retrieved_docs": state.get("retrieved_docs", []),
            "web_search_results": state.get("web_search_results", []),
            "request": state.get("request", ""),
        }
        
        supervisor_agent = self.agent_manager.create_supervisor_agent(input_state)
        
        response = supervisor_agent.invoke({
            "messages": state.get("messages", [HumanMessage(content=state.get("question", ""))]),
        })
        
        updated_state = state.copy()

        decision_data = None
        for msg in reversed(response["messages"]):
            if hasattr(msg, 'name') and msg.name == "make_supervisor_decision":
                try:
                    decision_data = json.loads(msg.content)
                    break
                except Exception:
                    continue
            if isinstance(msg.content, str) and "Action: make_supervisor_decision" in msg.content:
                match = re.search(r'Action Input:\s*({.*})', msg.content, re.DOTALL)
                if match:
                    try:
                        decision_data = json.loads(match.group(1))
                        break
                    except Exception:
                        continue

        updated_state["next"] = decision_data.get("next")
        updated_state["request"] = decision_data.get("request")
        updated_state["birth_info"] = decision_data.get("birth_info")
        updated_state["query_type"] = decision_data.get("query_type")
        updated_state["final_answer"] = decision_data.get("final_answer")
        updated_state["messages"] = response["messages"]

        return updated_state

    def saju_expert_agent_node(self, state):
        """Saju Expert Agent 노드"""
        print("🔧 Saju Expert 노드 실행")
        
        current_time = state.get("current_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        session_id = state.get("session_id", "unknown")
        session_start_time = state.get("session_start_time", "unknown")
        messages = state.get("messages", [])
        request = state.get("request", "")

        year = state.get("birth_info", {}).get("year")
        month = state.get("birth_info", {}).get("month")
        day = state.get("birth_info", {}).get("day")
        hour = state.get("birth_info", {}).get("hour")
        minute = state.get("birth_info", {}).get("minute")
        gender = "남자" if state.get("birth_info", {}).get("is_male") else "여자"
        is_leap_month = state.get("birth_info", {}).get("is_leap_month")

        saju_result = state.get("saju_result", "")

        saju_expert_agent = self.agent_manager.create_saju_expert_agent()

        response = saju_expert_agent.invoke({
            "current_time": current_time,
            "session_id": session_id,
            "session_start_time": session_start_time,
            "request": request,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "gender": gender,
            "is_leap_month": is_leap_month,
            "saju_result": saju_result,
            "messages": messages,
        })
       
        output = json.loads(response["output"]) if isinstance(response["output"], str) else response["output"]

        updated_state = state.copy()
        
        updated_state["request"] = output.get("request")
        output.pop("request")
        
        updated_state["saju_result"] = output
        updated_state["next"] = "Supervisor"
        updated_state["messages"].append(AIMessage(content=output.get("saju_analysis")))
        
        return updated_state

    def search_agent_node(self, state):
        """Search Agent 노드 (RAG + 웹검색 통합)"""
        print("🔧 Search 노드 실행")

        current_time = state.get("current_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        session_id = state.get("session_id", "unknown")
        session_start_time = state.get("session_start_time", "unknown")
        messages = state.get("messages", [])
        question = state.get("question", "")
        request = state.get("request", "")
        saju_result = state.get("saju_result", "")

        search_agent = self.agent_manager.create_search_agent()

        response = search_agent.invoke({
            "current_time": current_time,
            "session_id": session_id,
            "session_start_time": session_start_time,
            "request": request,
            "question": question,
            "saju_result": saju_result,
            "messages": messages,
        })

        output = json.loads(response["output"]) if isinstance(response["output"], str) else response["output"]

        updated_state = state.copy()
        updated_state["retrieved_docs"] = output.get("retrieved_docs", [])
        updated_state["web_search_results"] = output.get("web_search_results", [])
        updated_state["request"] = output.get("request")
        updated_state["messages"].append(AIMessage(content=output.get("generated_result")))

        return updated_state

    def general_answer_agent_node(self, state):
        """General Answer Agent 노드"""
        print("🔧 General Answer 노드 실행")

        current_time = state.get("current_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        session_id = state.get("session_id", "unknown")
        session_start_time = state.get("session_start_time", "unknown")
        messages = state.get("messages", [])
        question = state.get("question", "")
        request = state.get("request", "")
        saju_result = state.get("saju_result", "")

        general_answer_agent = self.agent_manager.create_general_answer_agent()

        response = general_answer_agent.invoke({
            "current_time": current_time,
            "session_id": session_id,
            "session_start_time": session_start_time,
            "request": request,
            "question": question,
            "messages": messages,
            "saju_result": saju_result,
        })

        output = json.loads(response["output"]) if isinstance(response["output"], str) else response["output"]

        updated_state = state.copy()
        updated_state["general_answer"] = output.get("general_answer")
        updated_state["request"] = output.get("request")
        updated_state["messages"].append(AIMessage(content=output.get("general_answer")))

        return updated_state


# 전역 NodeManager 인스턴스
_node_manager = None

def get_node_manager():
    """싱글톤 NodeManager 인스턴스 반환"""
    global _node_manager
    if _node_manager is None:
        _node_manager = NodeManager()
    return _node_manager 