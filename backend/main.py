import asyncio
import os
import signal
import sys
import time
import traceback
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.ai import AIMessageChunk
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosed


# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="saju_api.log",
    filemode="w",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    app.state.debug_mode = True
    app.state.session_store = {}
    app.state.memory = None
    app.state.compiled_graph = None

    debug_log = lambda message, level="INFO": _debug_log(message, level, app)

    debug_log("🔧 사주 AI 시스템 초기화 시작...")

    # 1단계: 모듈 임포트 확인
    debug_log("1️⃣ 단계 1: 사주 모듈 임포트 확인")
    create_workflow_func, import_success = safe_import_modules(debug_log)

    if not import_success:
        debug_log("❌ 사주 모듈 임포트 실패로 시스템 초기화 중단", "ERROR")
        yield
        return

    # 2단계: 메모리 초기화
    debug_log("2️⃣ 단계 2: 메모리 초기화")
    try:
        from langgraph.checkpoint.memory import MemorySaver
        app.state.memory = MemorySaver()
        debug_log(f"✅ 메모리 초기화 성공: {type(app.state.memory)}")
    except Exception as e:
        debug_log(f"❌ 메모리 초기화 실패: {e}", "ERROR")
        yield
        return

    # 3단계: 사주 워크플로 생성
    debug_log("3️⃣ 단계 3: 사주 워크플로 생성")
    try:
        if create_workflow_func:
            app.state.compiled_graph = create_workflow_func()
            debug_log(f"✅ 사주 워크플로 생성 성공: {type(app.state.compiled_graph)}")
        else:
            debug_log("❌ create_workflow_func가 로드되지 않음", "ERROR")
            yield
            return
    except Exception as e:
        debug_log(f"❌ 사주 워크플로 생성 실패: {e}", "ERROR")
        debug_log(f"❌ 상세 오류: {traceback.format_exc()}", "ERROR")
        yield
        return

    debug_log("✅ 사주 AI 시스템 초기화 완료!")

    yield

    # Shutdown (if needed)
    debug_log("🛑 사주 AI 시스템 종료")


# FastAPI 앱 초기화
app = FastAPI(
    title="사주 AI API",
    description="AI 기반 사주 상담 웹 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _debug_log(message: str, level: str = "INFO", app: FastAPI = None):
    if app is not None and hasattr(app, "state") and hasattr(app.state, "debug_mode"):
        debug_mode = app.state.debug_mode
    else:
        debug_mode = True
    if debug_mode:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"[{timestamp}] [{level}] {message}")

def debug_log(message: str, level: str = "INFO"):
    _debug_log(message, level)


def safe_import_modules(debug_log):
    """안전한 모듈 임포트 - 사주"""
    debug_log("📦 사주 모듈 임포트 시작...")
    try:
        from graph import create_workflow
        debug_log("✅ graph 임포트 성공")
        return create_workflow, True
    except ImportError as e:
        debug_log(f"❌ graph 임포트 실패: {e}", "ERROR")
        return None, False
    except Exception as e:
        debug_log(f"❌ graph 예상치 못한 오류: {e}", "ERROR")
        return None, False


def initialize_session(app, session_id: str) -> Dict:
    """새 세션 초기화 - 사주"""
    session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    session_data = {
        "messages": [],
        "next": "",
        "session_id": session_id,
        "session_start_time": session_start_time,
        "query_count": 0,
        "conversation_history": [],
        "is_active": True,
        "last_activity": datetime.now(),
    }

    app.state.session_store[session_id] = session_data
    _debug_log(f"🆔 새 사주 세션 생성: {session_id}", app=app)

    return session_data


def get_or_create_session(app, session_id: str) -> Dict:
    """세션 가져오기 또는 생성 - 사주"""
    if session_id not in app.state.session_store:
        return initialize_session(app, session_id)

    app.state.session_store[session_id]["last_activity"] = datetime.now()
    return app.state.session_store[session_id]


def generate_fallback_response(user_input: str, error_msg: Optional[str] = None) -> str:
    """폴백 응답 생성"""
    base_responses = [
        f"안녕하세요! '{user_input}'에 대한 사주 분석을 시작합니다.",
        f"'{user_input}'에 대해 사주를 풀어보겠습니다. 잠시만 기다려주세요.",
        f"사주 질문 '{user_input}'을 처리하고 있습니다.",
        f"'{user_input}'에 대한 사주 상담을 준비하고 있습니다.",
    ]

    import random

    response = random.choice(base_responses)

    if error_msg:
        response += f"\n\n(시스템 상태: {error_msg})"

    return response


@app.websocket("/ws/chat/saju/{session_id}")
async def chat_websocket_saju(websocket: WebSocket, session_id: str):
    debug_log = lambda message, level="INFO": _debug_log(message, level, websocket.app)
    debug_log(f"🔌 사주 WebSocket 연결 요청: {session_id}")

    try:
        await websocket.accept()
        debug_log(f"✅ 사주 WebSocket 연결 성공: {session_id}")

        session_data = get_or_create_session(websocket.app, session_id)
        message_queue = asyncio.Queue()

        # 메시지 수신 태스크
        async def receive_messages():
            while True:
                try:
                    data = await websocket.receive_text()
                    user_input = data.strip()
                    if user_input:
                        await message_queue.put(user_input)
                        debug_log(f"📝 사용자 입력 큐에 추가: {user_input}")
                except Exception as e:
                    debug_log(f"❌ 메시지 수신 오류: {e}", "ERROR")
                    break

        # 메시지 처리 태스크
        async def process_messages():
            while True:
                user_input = await message_queue.get()
                session_data["query_count"] += 1
                session_data["messages"].append(HumanMessage(content=user_input))
                debug_log(f"🔄 쿼리 #{session_data['query_count']} 처리 시작")
                send_to_frontend = False
                try:
                    compiled_graph = websocket.app.state.compiled_graph
                    
                    async for event in compiled_graph.astream_events(
                        session_data,
                        config={"configurable": {"thread_id": session_id}},
                        version="v2",
                        subgraphs=True,
                    ):
                        kind = event["event"]
                        debug_log(event)
                        if kind == "on_chat_model_start":
                            try:
                                final_message = event["data"].get('input').get("messages")[0][-1]
                                if json.loads(final_message.content).get("next") == "FINISH":
                                    debug_log(f"🔄 FINISH Detected: {final_message.content}")
                                    send_to_frontend = True
                            except Exception as e:
                                debug_log(f"❌ 메시지 처리 오류: {e}", "ERROR")
                                continue

                        if kind == "on_chat_model_stream" and send_to_frontend:
                            data = event["data"]
                            if data["chunk"].content:
                                await websocket.send_json({
                                    "type": "stream",
                                    "content": str(data["chunk"].content)
                                })
                    await websocket.send_json({
                        "type": "complete",
                        "content": f"✅ 사주 분석 완료 (질문 #{session_data['query_count']})"
                    })

                except Exception as e:
                    debug_log(f"❌ LangGraph 처리 오류: {e}", "ERROR")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"❌ 사주 분석 중 오류가 발생했습니다: {str(e)}"
                    })

        # 두 태스크를 동시에 실행
        receive_task = asyncio.create_task(receive_messages())
        process_task = asyncio.create_task(process_messages())

        # WebSocket 연결이 끊길 때까지 대기
        await receive_task
        process_task.cancel()
        debug_log("🔌 WebSocket 연결 종료 (receive_task 종료)")

    except Exception as e:
        debug_log(f"❌ WebSocket 연결 실패: {str(e)}", "ERROR")
        debug_log(f"❌ 상세 오류: {traceback.format_exc()}", "ERROR")
    finally:
        if session_id in websocket.app.state.session_store:
            websocket.app.state.session_store[session_id]["is_active"] = False
        debug_log(f"🔌 사주 WebSocket 연결 종료: {session_id}")


# API 엔드포인트들
@app.get("/api/debug/system-status")
async def system_status():
    """시스템 상태 확인"""
    from fastapi import Request
    async def _system_status(request: Request):
        app = request.app
        return {
            "timestamp": datetime.now().isoformat(),
            "system_components": {
                "memory": app.state.memory is not None,
                "compiled_graph": app.state.compiled_graph is not None,
            },
            "sessions": {
                "saju_total": len(app.state.session_store),
                "saju_active": len([s for s in app.state.session_store.values() if s["is_active"]]),
            },
            "debug_mode": app.state.debug_mode,
        }
    return await _system_status(request)


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    from fastapi import Request
    async def _health_check(request: Request):
        app = request.app
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_loaded": {
                "compiled_graph": app.state.compiled_graph is not None,
                "memory": app.state.memory is not None,
            },
        }
    return await _health_check(request)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    from fastapi import Request
    async def _root(request: Request):
        app = request.app
        return {
            "message": "🔮 사주 AI API Server",
            "version": "1.0.0",
            "debug_mode": app.state.debug_mode,
            "status": "running",
            "endpoints": {
                "saju": "/ws/chat/saju/{session_id}",
            },
        }
    return await _root(request)


# 신호 핸들러 (Ctrl+C 처리)
def signal_handler(signum, frame):
    _debug_log("🛑 종료 신호 수신 (Ctrl+C)", level="WARN")
    sys.exit(0)


if __name__ == "__main__":
    import uvicorn

    # 신호 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    debug_log("🚀 사주 AI FastAPI 서버 시작...")

    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )
    except KeyboardInterrupt:
        debug_log("🛑 서버 종료", "WARN")
    except Exception as e:
        debug_log(f"❌ 서버 실행 오류: {e}", "ERROR")