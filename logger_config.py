"""
FortuneAI 구조화된 로깅 시스템
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColorFormatter(logging.Formatter):
    """컬러 출력을 위한 로그 포매터"""
    
    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',     # 청록색
        'INFO': '\033[32m',      # 녹색
        'WARNING': '\033[33m',   # 노란색
        'ERROR': '\033[31m',     # 빨간색
        'CRITICAL': '\033[35m',  # 마젠타색
        'RESET': '\033[0m'       # 리셋
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # 로그 레벨에 따른 색상 적용
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 로그 메시지 포맷팅
        log_message = super().format(record)
        return f"{color}{log_message}{reset}"


class FortuneAILogger:
    """FortuneAI 전용 로거 클래스"""
    
    def __init__(self, name: str = "FortuneAI"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 중복 핸들러 방지
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """로그 핸들러 설정"""
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 컬러 포매터 적용
        console_format = ColorFormatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # 파일 핸들러 설정
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"fortune_ai_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 파일용 포매터 (색상 없음)
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # 핸들러 추가
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """디버그 레벨 로그"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """정보 레벨 로그"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """경고 레벨 로그"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """에러 레벨 로그"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """심각한 에러 레벨 로그"""
        self.logger.critical(message, **kwargs)
    
    def agent_start(self, agent_name: str, action: str = "") -> None:
        """에이전트 시작 로그"""
        self.info(f"🚀 {agent_name} 에이전트 시작 {action}")
    
    def agent_end(self, agent_name: str, status: str = "완료") -> None:
        """에이전트 완료 로그"""
        self.info(f"✅ {agent_name} 에이전트 {status}")
    
    def tool_call(self, tool_name: str, parameters: Optional[dict] = None) -> None:
        """도구 호출 로그"""
        param_str = f" | 매개변수: {parameters}" if parameters else ""
        self.debug(f"🔧 도구 호출: {tool_name}{param_str}")
    
    def saju_calculation(self, birth_info: dict, result: dict) -> None:
        """사주 계산 전용 로그"""
        self.info(f"📊 사주 계산 완료 | 출생: {birth_info} | 결과: 년주({result.get('year_pillar', 'N/A')})")
    
    def search_query(self, query: str, result_count: int = 0) -> None:
        """검색 쿼리 로그"""
        self.info(f"🔍 검색 실행: '{query}' | 결과: {result_count}건")
    
    def session_info(self, session_id: str, action: str) -> None:
        """세션 정보 로그"""
        self.debug(f"📱 세션 {action}: {session_id}")
    
    def performance(self, operation: str, duration: float, details: str = "") -> None:
        """성능 측정 로그"""
        detail_str = f" | {details}" if details else ""
        self.info(f"⏱️  성능: {operation} | 소요시간: {duration:.2f}초{detail_str}")


# 전역 로거 인스턴스
logger = FortuneAILogger()

# 편의 함수들
def get_logger(name: str = "FortuneAI") -> FortuneAILogger:
    """로거 인스턴스 반환"""
    return FortuneAILogger(name)

def debug(message: str, **kwargs) -> None:
    logger.debug(message, **kwargs)

def info(message: str, **kwargs) -> None:
    logger.info(message, **kwargs)

def warning(message: str, **kwargs) -> None:
    logger.warning(message, **kwargs)

def error(message: str, **kwargs) -> None:
    logger.error(message, **kwargs)

def critical(message: str, **kwargs) -> None:
    logger.critical(message, **kwargs)