"""
LangGraph 시스템의 모든 노드들
사주 시스템의 워커 노드들과 응답 생성 노드를 포함
"""

import time
import functools
from typing import Dict, Any, List, Optional
from datetime import datetime

from .state import SupervisorState, WorkerResult
from saju_calculator import SajuCalculator, format_saju_analysis
from tools import ToolManager
from models import get_openai_llm

# =============================================================================
# 사주 계산 워커
# =============================================================================

class SajuWorker:
    """사주 계산 전문 워커"""
    
    def __init__(self):
        self.calculator = SajuCalculator()
        self.worker_name = "saju"
    
    def __call__(self, state: SupervisorState) -> SupervisorState:
        """사주 워커 실행"""
        # 할당된 워커가 아니면 스킵
        if self.worker_name not in state.get("assigned_workers", []):
            return state
        
        # 이미 완료된 워커면 스킵
        if self.worker_name in state.get("completed_workers", []):
            return state
        
        start_time = time.time()
        
        try:
            # 생년월일시 정보 확인 (Supervisor에서 이미 추출됨)
            birth_info = state.get("birth_info")
            
            if not birth_info:
                # 생년월일시 정보가 없으면 실패
                result = WorkerResult(
                    worker_name=self.worker_name,
                    success=False,
                    result=None,
                    error_message="생년월일시 정보가 필요합니다.",
                    execution_time=time.time() - start_time,
                    tokens_used=0
                )
            else:
                # 사주 계산 실행
                result = self._calculate_saju(birth_info, start_time)
            
            # 상태 업데이트
            return self._update_state(state, result)
            
        except Exception as e:
            # 오류 처리
            result = WorkerResult(
                worker_name=self.worker_name,
                success=False,
                result=None,
                error_message=f"사주 계산 오류: {str(e)}",
                execution_time=time.time() - start_time,
                tokens_used=0
            )
            return self._update_state(state, result)
    
    def _calculate_saju(self, birth_info: Dict[str, Any], start_time: float) -> WorkerResult:
        """사주 계산 실행"""
        try:
            # 사주 계산
            saju_chart = self.calculator.auto_calculate_saju(
                year=birth_info["year"],
                month=birth_info["month"],
                day=birth_info["day"],
                hour=birth_info["hour"],
                minute=birth_info.get("minute", 0),
                is_male=birth_info.get("is_male", True)
            )
            
            # 포맷팅된 분석 결과 생성
            formatted_analysis = format_saju_analysis(saju_chart, self.calculator)
            
            # 구조화된 결과 생성
            structured_result = {
                "saju_chart": {
                    "year_pillar": str(saju_chart.year_pillar),
                    "month_pillar": str(saju_chart.month_pillar),
                    "day_pillar": str(saju_chart.day_pillar),
                    "hour_pillar": str(saju_chart.hour_pillar),
                    "day_master": saju_chart.get_day_master()
                },
                "analysis": {
                    "elements": self.calculator.get_element_strength_with_season(saju_chart),
                    "ten_gods": self.calculator.get_ten_gods_summary(saju_chart),
                    "day_master_strength": self.calculator.analyze_day_master_strength(saju_chart),
                    "great_fortune": self.calculator.calculate_great_fortune_improved(saju_chart)
                },
                "formatted_text": formatted_analysis,
                "birth_info": birth_info
            }
            
            return WorkerResult(
                worker_name=self.worker_name,
                success=True,
                result=structured_result,
                error_message=None,
                execution_time=time.time() - start_time,
                tokens_used=None  # 사주 계산은 LLM 미사용
            )
            
        except Exception as e:
            return WorkerResult(
                worker_name=self.worker_name,
                success=False,
                result=None,
                error_message=f"사주 계산 실패: {str(e)}",
                execution_time=time.time() - start_time,
                tokens_used=0
            )
    
    def _update_state(self, state: SupervisorState, result: WorkerResult) -> SupervisorState:
        """상태 업데이트"""
        # 워커 결과 저장
        worker_results = state.get("worker_results", {})
        worker_results[self.worker_name] = result
        
        # 완료된 워커 목록에 추가
        completed_workers = state.get("completed_workers", [])
        if self.worker_name not in completed_workers:
            completed_workers.append(self.worker_name)
        
        # 사주 차트 정보 저장 (성공한 경우)
        saju_chart = None
        if result["success"] and result["result"]:
            saju_chart = result["result"]
        
        return {
            **state,
            "worker_results": worker_results,
            "completed_workers": completed_workers,
            "saju_chart": saju_chart
        }

# =============================================================================
# RAG 검색 워커
# =============================================================================

class RAGWorker:
    """RAG 검색 전문 워커"""
    
    def __init__(self):
        self.worker_name = "rag"
        # RAG 도구 초기화
        self.tool_manager = ToolManager(enable_rag=True, enable_web=False, enable_calendar=False)
        self.tool_manager.initialize()
        self.rag_tools = {tool.name: tool for tool in self.tool_manager._get_rag_tools()}
    
    def __call__(self, state: SupervisorState) -> SupervisorState:
        """RAG 워커 실행"""
        # 할당된 워커가 아니면 스킵
        if self.worker_name not in state.get("assigned_workers", []):
            return state
        
        # 이미 완료된 워커면 스킵
        if self.worker_name in state.get("completed_workers", []):
            return state
        
        start_time = time.time()
        
        try:
            # RAG 검색 실행
            result = self._search_fortune_knowledge(state, start_time)
            
            # 상태 업데이트
            return self._update_state(state, result)
            
        except Exception as e:
            # 오류 처리
            result = WorkerResult(
                worker_name=self.worker_name,
                success=False,
                result=None,
                error_message=f"RAG 검색 오류: {str(e)}",
                execution_time=time.time() - start_time,
                tokens_used=0
            )
            return self._update_state(state, result)
    
    def _search_fortune_knowledge(self, state: SupervisorState, start_time: float) -> WorkerResult:
        """RAG 기반 사주/운세 지식 검색"""
        try:
            user_query = state["user_query"]
            
            # 검색 쿼리 최적화
            search_query = self._optimize_search_query(state)
            
            # RAG 검색 실행 - smart_search_saju 도구 사용
            rag_tool = self.rag_tools.get("smart_search_saju")
            if rag_tool:
                rag_result = rag_tool.invoke({"query": search_query})
            else:
                # 대체 도구 사용
                rag_tool = self.rag_tools.get("search_saju_knowledge")
                rag_result = rag_tool.invoke({"query": search_query}) if rag_tool else "RAG 도구를 찾을 수 없습니다."
            
            # 결과 구조화
            structured_result = {
                "search_query": search_query,
                "raw_result": rag_result,
                "relevant_passages": self._extract_relevant_passages(rag_result),
                "knowledge_type": self._classify_knowledge_type(rag_result),
                "confidence": self._calculate_confidence(rag_result)
            }
            
            return WorkerResult(
                worker_name=self.worker_name,
                success=True,
                result=structured_result,
                error_message=None,
                execution_time=time.time() - start_time,
                tokens_used=self._estimate_tokens(rag_result)
            )
            
        except Exception as e:
            return WorkerResult(
                worker_name=self.worker_name,
                success=False,
                result=None,
                error_message=f"RAG 검색 실패: {str(e)}",
                execution_time=time.time() - start_time,
                tokens_used=0
            )
    
    def _optimize_search_query(self, state: SupervisorState) -> str:
        """검색 쿼리 최적화"""
        user_query = state["user_query"]
        question_type = state.get("question_type", "")
        birth_info = state.get("birth_info")
        saju_chart = state.get("saju_chart")
        
        # 기본 쿼리
        search_query = user_query
        
        # 사주 정보가 있으면 추가
        if saju_chart:
            day_master = saju_chart.get("saju_chart", {}).get("day_master", "")
            if day_master:
                search_query += f" {day_master}일간"
        
        # 질문 유형에 따른 키워드 추가
        if question_type == "fortune_consultation":
            if "연애" in user_query or "사랑" in user_query:
                search_query += " 연애운 사랑운"
            elif "재물" in user_query or "돈" in user_query:
                search_query += " 재물운 금전운"
            elif "직업" in user_query or "일" in user_query:
                search_query += " 직업운 사업운"
            elif "건강" in user_query:
                search_query += " 건강운"
        
        return search_query
    
    def _extract_relevant_passages(self, rag_result: str) -> List[str]:
        """관련 구절 추출"""
        if not rag_result:
            return []
        
        # 간단한 문장 분할 (실제로는 더 정교하게 구현)
        sentences = rag_result.split('.')
        relevant = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return relevant[:5]  # 상위 5개 구절
    
    def _classify_knowledge_type(self, rag_result: str) -> str:
        """지식 유형 분류"""
        if not rag_result:
            return "unknown"
        
        if any(keyword in rag_result for keyword in ["오행", "십신", "대운"]):
            return "saju_theory"
        elif any(keyword in rag_result for keyword in ["운세", "궁합", "택일"]):
            return "fortune_consultation"
        elif any(keyword in rag_result for keyword in ["해석", "의미", "특징"]):
            return "interpretation"
        else:
            return "general"
    
    def _calculate_confidence(self, rag_result: str) -> float:
        """검색 결과 신뢰도 계산"""
        if not rag_result:
            return 0.0
        
        # 간단한 신뢰도 계산 (길이 기반)
        length_score = min(len(rag_result) / 500, 1.0)  # 500자 기준
        
        # 전문 용어 포함 여부
        professional_terms = ["사주", "팔자", "오행", "십신", "대운", "명리"]
        term_score = sum(1 for term in professional_terms if term in rag_result) / len(professional_terms)
        
        return (length_score * 0.6 + term_score * 0.4)
    
    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정"""
        if not text:
            return 0
        # 대략적인 토큰 수 추정 (한국어 기준)
        return len(text) // 3
    
    def _update_state(self, state: SupervisorState, result: WorkerResult) -> SupervisorState:
        """상태 업데이트"""
        # 워커 결과 저장
        worker_results = state.get("worker_results", {})
        worker_results[self.worker_name] = result
        
        # 완료된 워커 목록에 추가
        completed_workers = state.get("completed_workers", [])
        if self.worker_name not in completed_workers:
            completed_workers.append(self.worker_name)
        
        # RAG 결과 저장 (성공한 경우)
        rag_results = None
        if result["success"] and result["result"]:
            rag_results = [result["result"]]
        
        return {
            **state,
            "worker_results": worker_results,
            "completed_workers": completed_workers,
            "rag_results": rag_results
        }

# =============================================================================
# 웹 검색 워커
# =============================================================================

class WebWorker:
    """웹 검색 전문 워커"""
    
    def __init__(self):
        self.worker_name = "web"
        # 웹 검색 도구 초기화
        self.tool_manager = ToolManager(enable_rag=False, enable_web=True, enable_calendar=False)
        self.tool_manager.initialize()
        self.web_tools = {tool.name: tool for tool in self.tool_manager._get_web_tools()}
    
    def __call__(self, state: SupervisorState) -> SupervisorState:
        """웹 워커 실행"""
        # 할당된 워커가 아니면 스킵
        if self.worker_name not in state.get("assigned_workers", []):
            return state
        
        # 이미 완료된 워커면 스킵
        if self.worker_name in state.get("completed_workers", []):
            return state
        
        start_time = time.time()
        
        try:
            # 웹 검색 실행
            result = self._search_web_information(state, start_time)
            
            # 상태 업데이트
            return self._update_state(state, result)
            
        except Exception as e:
            # 오류 처리
            result = WorkerResult(
                worker_name=self.worker_name,
                success=False,
                result=None,
                error_message=f"웹 검색 오류: {str(e)}",
                execution_time=time.time() - start_time,
                tokens_used=0
            )
            return self._update_state(state, result)
    
    def _search_web_information(self, state: SupervisorState, start_time: float) -> WorkerResult:
        """웹 기반 최신 정보 검색"""
        try:
            user_query = state["user_query"]
            
            # 검색 쿼리 최적화
            search_query = self._optimize_web_query(state)
            
            # 웹 검색 실행 - search_web_saju 도구 사용
            web_tool = self.web_tools.get("search_web_saju")
            if web_tool:
                web_result = web_tool.invoke({"query": search_query})
            else:
                web_result = "웹 검색 도구를 찾을 수 없습니다."
            
            # 결과 구조화
            structured_result = {
                "search_query": search_query,
                "raw_result": web_result,
                "filtered_content": self._filter_relevant_content(web_result),
                "source_urls": self._extract_source_urls(web_result),
                "information_type": self._classify_information_type(web_result),
                "freshness": self._assess_information_freshness(web_result),
                "reliability": self._assess_reliability(web_result)
            }
            
            return WorkerResult(
                worker_name=self.worker_name,
                success=True,
                result=structured_result,
                error_message=None,
                execution_time=time.time() - start_time,
                tokens_used=self._estimate_tokens(web_result)
            )
            
        except Exception as e:
            return WorkerResult(
                worker_name=self.worker_name,
                success=False,
                result=None,
                error_message=f"웹 검색 실패: {str(e)}",
                execution_time=time.time() - start_time,
                tokens_used=0
            )
    
    def _optimize_web_query(self, state: SupervisorState) -> str:
        """웹 검색 쿼리 최적화"""
        user_query = state["user_query"]
        question_type = state.get("question_type", "")
        
        # 기본 쿼리
        search_query = user_query
        
        # 질문 유형에 따른 최적화
        if question_type == "fortune_consultation":
            # 운세 관련 검색에 연도 추가
            current_year = "2024"
            if current_year not in search_query:
                search_query += f" {current_year}년"
            
            # 신뢰할 만한 사이트 우선
            search_query += " site:sajuplus.com OR site:fortuneteller.co.kr OR site:myfortune.co.kr"
        
        elif question_type == "general_search":
            # 일반 검색은 최신 정보 우선
            search_query += " 최신 정보"
        
        return search_query
    
    def _filter_relevant_content(self, web_result: str) -> List[str]:
        """관련 콘텐츠 필터링"""
        if not web_result:
            return []
        
        # 간단한 필터링 (실제로는 더 정교하게 구현)
        lines = web_result.split('\n')
        relevant_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 30:  # 너무 짧은 라인 제외
                # 광고성 내용 제외
                if not any(ad_word in line for ad_word in ["광고", "쿠폰", "할인", "이벤트"]):
                    relevant_lines.append(line)
        
        return relevant_lines[:10]  # 상위 10개 라인
    
    def _extract_source_urls(self, web_result: str) -> List[str]:
        """소스 URL 추출"""
        import re
        
        if not web_result:
            return []
        
        # URL 패턴 매칭
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, web_result)
        
        # 중복 제거 및 신뢰할 만한 도메인 우선
        trusted_domains = ["sajuplus.com", "fortuneteller.co.kr", "myfortune.co.kr", "naver.com", "daum.net"]
        trusted_urls = [url for url in urls if any(domain in url for domain in trusted_domains)]
        other_urls = [url for url in urls if not any(domain in url for domain in trusted_domains)]
        
        return list(dict.fromkeys(trusted_urls + other_urls))[:5]  # 중복 제거 후 상위 5개
    
    def _classify_information_type(self, web_result: str) -> str:
        """정보 유형 분류"""
        if not web_result:
            return "unknown"
        
        if any(keyword in web_result for keyword in ["2024년", "올해", "최신"]):
            return "current_fortune"
        elif any(keyword in web_result for keyword in ["뉴스", "기사", "보도"]):
            return "news"
        elif any(keyword in web_result for keyword in ["블로그", "후기", "경험"]):
            return "personal_experience"
        elif any(keyword in web_result for keyword in ["전문가", "명리학", "이론"]):
            return "expert_opinion"
        else:
            return "general_information"
    
    def _assess_information_freshness(self, web_result: str) -> float:
        """정보 신선도 평가"""
        if not web_result:
            return 0.0
        
        # 날짜 관련 키워드로 신선도 평가
        fresh_keywords = ["2024", "올해", "최근", "최신", "오늘", "이번"]
        old_keywords = ["2022", "2021", "작년", "예전"]
        
        fresh_score = sum(1 for keyword in fresh_keywords if keyword in web_result)
        old_score = sum(1 for keyword in old_keywords if keyword in web_result)
        
        if fresh_score + old_score == 0:
            return 0.5  # 중립
        
        return fresh_score / (fresh_score + old_score)
    
    def _assess_reliability(self, web_result: str) -> float:
        """정보 신뢰도 평가"""
        if not web_result:
            return 0.0
        
        # 신뢰할 만한 소스 키워드
        reliable_keywords = ["전문가", "명리학", "연구", "분석", "통계"]
        unreliable_keywords = ["카더라", "소문", "추측", "개인적"]
        
        reliable_score = sum(1 for keyword in reliable_keywords if keyword in web_result)
        unreliable_score = sum(1 for keyword in unreliable_keywords if keyword in web_result)
        
        if reliable_score + unreliable_score == 0:
            return 0.5  # 중립
        
        return reliable_score / (reliable_score + unreliable_score)
    
    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정"""
        if not text:
            return 0
        # 대략적인 토큰 수 추정 (한국어 기준)
        return len(text) // 3
    
    def _update_state(self, state: SupervisorState, result: WorkerResult) -> SupervisorState:
        """상태 업데이트"""
        # 워커 결과 저장
        worker_results = state.get("worker_results", {})
        worker_results[self.worker_name] = result
        
        # 완료된 워커 목록에 추가
        completed_workers = state.get("completed_workers", [])
        if self.worker_name not in completed_workers:
            completed_workers.append(self.worker_name)
        
        # 웹 결과 저장 (성공한 경우)
        web_results = None
        if result["success"] and result["result"]:
            web_results = [result["result"]]
        
        return {
            **state,
            "worker_results": worker_results,
            "completed_workers": completed_workers,
            "web_results": web_results
        }

# =============================================================================
# 응답 생성기
# =============================================================================

class ResponseGenerator:
    """최종 응답 생성기"""
    
    def __init__(self):
        self.llm = get_openai_llm()
    
    def __call__(self, state: SupervisorState) -> SupervisorState:
        """응답 생성 노드 실행"""
        start_time = time.time()
        
        try:
            # 최종 응답 생성
            final_response = self._generate_comprehensive_response(state)
            
            # 상태 업데이트
            return {
                **state,
                "final_response": final_response,
                "response_generated": True,
                "total_execution_time": time.time() - start_time
            }
            
        except Exception as e:
            # 오류 발생시 기본 응답 생성
            fallback_response = self._generate_fallback_response(state, str(e))
            
            return {
                **state,
                "final_response": fallback_response,
                "response_generated": True,
                "response_error": str(e),
                "total_execution_time": time.time() - start_time
            }
    
    def _generate_comprehensive_response(self, state: SupervisorState) -> str:
        """종합적인 응답 생성"""
        user_query = state["user_query"]
        question_type = state.get("question_type", "")
        worker_results = state.get("worker_results", {})
        
        # 워커별 결과 수집
        saju_result = self._extract_worker_result(worker_results, "saju")
        rag_result = self._extract_worker_result(worker_results, "rag")
        web_result = self._extract_worker_result(worker_results, "web")
        
        # 질문 유형에 따른 응답 생성
        if question_type == "saju_calculation":
            return self._generate_saju_response(user_query, saju_result, rag_result)
        elif question_type == "fortune_consultation":
            return self._generate_fortune_response(user_query, saju_result, rag_result, web_result)
        elif question_type == "simple_question":
            return self._generate_simple_response(user_query, state)
        elif question_type == "general_search":
            return self._generate_general_response(user_query, web_result, rag_result)
        else:
            return self._generate_mixed_response(user_query, saju_result, rag_result, web_result)
    
    def _extract_worker_result(self, worker_results: Dict[str, Any], worker_name: str) -> Optional[Dict[str, Any]]:
        """워커 결과 추출"""
        if worker_name not in worker_results:
            return None
        
        worker_result = worker_results[worker_name]
        if not worker_result.get("success", False):
            return None
        
        return worker_result.get("result")
    
    def _generate_saju_response(self, user_query: str, saju_result: Optional[Dict], rag_result: Optional[Dict]) -> str:
        """사주 계산 전용 응답 생성"""
        if not saju_result:
            return "죄송합니다. 사주 계산에 필요한 생년월일시 정보가 부족합니다. 정확한 생년월일시를 다시 알려주세요."
        
        # 기본 사주 정보
        response_parts = []
        
        # 1. 사주팔자 표시
        if "saju_chart" in saju_result:
            response_parts.append("🔮 **사주팔자**")
            chart = saju_result["saju_chart"]
            chart_text = f"""
년주: {chart.get('year_pillar', '')}
월주: {chart.get('month_pillar', '')}
일주: {chart.get('day_pillar', '')}
시주: {chart.get('hour_pillar', '')}
일간: {chart.get('day_master', '')}
"""
            response_parts.append(chart_text)
            response_parts.append("")
        
        # 2. 포맷팅된 텍스트 (있는 경우)
        if "formatted_text" in saju_result:
            response_parts.append("📊 **사주 분석**")
            response_parts.append(saju_result["formatted_text"])
            response_parts.append("")
        
        # 3. 분석 데이터 (있는 경우)
        if "analysis" in saju_result:
            analysis = saju_result["analysis"]
            if "day_master_strength" in analysis:
                response_parts.append("💪 **일간 강약**")
                response_parts.append(f"일간 강도: {analysis['day_master_strength']}")
                response_parts.append("")
        
        # 4. RAG 보완 정보
        if rag_result and rag_result.get("relevant_passages"):
            response_parts.append("📚 **전문 해석**")
            for passage in rag_result["relevant_passages"][:3]:
                response_parts.append(f"• {passage}")
            response_parts.append("")
        
        # 응답이 비어있으면 기본 메시지
        if not response_parts:
            response_parts.append("🔮 **사주 계산 완료**")
            response_parts.append("사주 계산이 완료되었습니다. 상세한 해석을 원하시면 추가 질문을 해주세요.")
        
        return "\n".join(response_parts)
    
    def _generate_fortune_response(self, user_query: str, saju_result: Optional[Dict], 
                                 rag_result: Optional[Dict], web_result: Optional[Dict]) -> str:
        """운세 상담 응답 생성"""
        response_parts = []
        
        # 1. 사주 기반 분석 (있는 경우)
        if saju_result:
            response_parts.append("🔮 **개인 사주 기반 분석**")
            if "analysis_summary" in saju_result:
                response_parts.append(saju_result["analysis_summary"])
            response_parts.append("")
        
        # 2. 전문 지식 기반 해석
        if rag_result and rag_result.get("relevant_passages"):
            response_parts.append("📚 **전문 운세 해석**")
            for passage in rag_result["relevant_passages"][:3]:
                response_parts.append(f"• {passage}")
            response_parts.append("")
        
        # 3. 최신 운세 정보
        if web_result and web_result.get("filtered_content"):
            response_parts.append("🌐 **최신 운세 정보**")
            for content in web_result["filtered_content"][:3]:
                response_parts.append(f"• {content}")
            response_parts.append("")
        
        # 4. 종합 조언
        response_parts.append("💡 **종합 조언**")
        advice = self._generate_personalized_advice(user_query, saju_result, rag_result, web_result)
        response_parts.append(advice)
        
        return "\n".join(response_parts)
    
    def _generate_simple_response(self, user_query: str, state: SupervisorState) -> str:
        """간단한 질문에 대한 직접 응답 생성"""
        from datetime import datetime
        
        current_date = datetime.now()
        
        # 날짜 관련 질문 처리
        if any(keyword in user_query.lower() for keyword in ["오늘", "날짜", "몇월", "며칠", "요일"]):
            current_date_str = current_date.strftime("%Y년 %m월 %d일 %A")
            korean_weekday = {
                'Monday': '월요일',
                'Tuesday': '화요일', 
                'Wednesday': '수요일',
                'Thursday': '목요일',
                'Friday': '금요일',
                'Saturday': '토요일',
                'Sunday': '일요일'
            }
            weekday = korean_weekday.get(current_date.strftime('%A'), current_date.strftime('%A'))
            
            return f"""📅 **현재 날짜 정보**

오늘은 {current_date.year}년 {current_date.month}월 {current_date.day}일 {weekday}입니다.

혹시 사주나 운세와 관련된 질문이 있으시면 언제든 말씀해 주세요! 🔮"""
        
        # 시간 관련 질문 처리
        elif any(keyword in user_query.lower() for keyword in ["시간", "몇시", "지금"]):
            current_time_str = current_date.strftime("%H시 %M분")
            return f"""⏰ **현재 시간 정보**

지금은 {current_time_str}입니다.

사주 계산이나 운세 상담이 필요하시면 생년월일시를 알려주세요! 🔮"""
        
        # 기타 간단한 질문
        else:
            return f"""💭 **간단한 답변**

질문해 주신 내용에 대해 간단히 답변드리겠습니다.

더 자세한 사주나 운세 상담이 필요하시면 구체적인 질문을 해주세요! 🔮"""
    
    def _generate_general_response(self, user_query: str, web_result: Optional[Dict], 
                                 rag_result: Optional[Dict]) -> str:
        """일반 검색 응답 생성"""
        response_parts = []
        has_useful_content = False
        
        # 1. 웹 검색 결과 확인 및 처리
        if web_result and web_result.get("filtered_content"):
            # 유용한 웹 검색 결과가 있는지 확인
            useful_content = [content for content in web_result["filtered_content"][:5] 
                            if content and len(content.strip()) > 10]
            if useful_content:
                response_parts.append("🔍 **검색 결과**")
                for content in useful_content:
                    response_parts.append(f"• {content}")
                response_parts.append("")
                has_useful_content = True
        
        # 2. RAG 결과 확인 및 처리 (한국어 사주 관련 내용만)
        if rag_result and rag_result.get("relevant_passages"):
            # 한국어 사주 관련 내용인지 엄격하게 확인
            korean_passages = []
            for passage in rag_result["relevant_passages"][:3]:
                if passage:
                    # 영어 내용 제외 (Tiger, Rat, Dragon 등 서양 점성술 키워드)
                    english_keywords = ["Tiger", "Rat", "Dragon", "Snake", "Horse", "Rabbit", "Monkey", "Rooster", "Dog", "Pig", "Ox", "A.M.", "P.M."]
                    has_english = any(keyword in passage for keyword in english_keywords)
                    
                    # 한국어 사주 키워드 확인
                    korean_keywords = ["오행", "십신", "사주", "팔자", "명리", "대운", "천간", "지지", "갑을병정", "자축인묘"]
                    has_korean = any(keyword in passage for keyword in korean_keywords)
                    
                    # 영어 내용이 없고 한국어 키워드가 있는 경우만 포함
                    if not has_english and has_korean:
                        korean_passages.append(passage)
            
            if korean_passages:
                response_parts.append("📚 **관련 전문 지식**")
                for passage in korean_passages:
                    response_parts.append(f"• {passage}")
                response_parts.append("")
                has_useful_content = True
        
        # 3. 유용한 내용이 없으면 기본 응답
        if not has_useful_content:
            response_parts.append("💭 **검색 결과**")
            response_parts.append("죄송합니다. 관련된 정보를 찾기 어렵습니다.")
            response_parts.append("더 구체적인 질문을 해주시면 더 나은 답변을 드릴 수 있습니다.")
        
        return "\n".join(response_parts)
    
    def _generate_mixed_response(self, user_query: str, saju_result: Optional[Dict], 
                               rag_result: Optional[Dict], web_result: Optional[Dict]) -> str:
        """혼합 응답 생성"""
        response_parts = []
        
        # 모든 가능한 정보 소스 활용
        if saju_result:
            response_parts.append("🔮 **사주 정보**")
            response_parts.append("개인 사주 정보가 포함된 분석입니다.")
            response_parts.append("")
        
        if rag_result and rag_result.get("relevant_passages"):
            response_parts.append("📚 **전문 지식**")
            for passage in rag_result["relevant_passages"][:2]:
                response_parts.append(f"• {passage}")
            response_parts.append("")
        
        if web_result and web_result.get("filtered_content"):
            response_parts.append("🌐 **최신 정보**")
            for content in web_result["filtered_content"][:2]:
                response_parts.append(f"• {content}")
            response_parts.append("")
        
        # 종합 결론
        response_parts.append("🎯 **종합 결론**")
        conclusion = self._generate_comprehensive_conclusion(user_query, saju_result, rag_result, web_result)
        response_parts.append(conclusion)
        
        return "\n".join(response_parts)
    
    def _generate_personalized_advice(self, user_query: str, saju_result: Optional[Dict], 
                                    rag_result: Optional[Dict], web_result: Optional[Dict]) -> str:
        """개인화된 조언 생성"""
        # 간단한 조언 생성 로직
        if saju_result:
            return "개인 사주를 바탕으로 한 맞춤형 조언을 참고하시기 바랍니다."
        elif rag_result:
            return "전문 지식을 바탕으로 한 일반적인 조언을 참고하시기 바랍니다."
        else:
            return "더 구체적인 정보가 있으면 더 정확한 조언을 드릴 수 있습니다."
    
    def _generate_comprehensive_conclusion(self, user_query: str, saju_result: Optional[Dict], 
                                         rag_result: Optional[Dict], web_result: Optional[Dict]) -> str:
        """종합 결론 생성"""
        return "다양한 정보를 종합하여 분석한 결과입니다. 추가 궁금한 점이 있으시면 언제든 질문해 주세요."
    
    def _generate_fallback_response(self, state: SupervisorState, error_message: str) -> str:
        """대체 응답 생성"""
        return f"""
죄송합니다. 응답 생성 중 오류가 발생했습니다.

오류 내용: {error_message}

다시 질문해 주시거나, 더 구체적인 정보를 제공해 주시면 도움이 될 것 같습니다.
        """.strip()

# =============================================================================
# 노드 함수들 (LangGraph용)
# =============================================================================

def saju_worker_node(state: SupervisorState) -> SupervisorState:
    """사주 워커 노드 실행 함수"""
    worker = SajuWorker()
    return worker(state)

def rag_worker_node(state: SupervisorState) -> SupervisorState:
    """RAG 워커 노드 실행 함수"""
    worker = RAGWorker()
    return worker(state)

def web_worker_node(state: SupervisorState) -> SupervisorState:
    """웹 워커 노드 실행 함수"""
    worker = WebWorker()
    return worker(state)

def response_generator_node(state: SupervisorState) -> SupervisorState:
    """응답 생성 노드 실행 함수"""
    generator = ResponseGenerator()
    return generator(state)

# =============================================================================
# 에이전트 노드 래퍼 (향후 확장용)
# =============================================================================

def agent_node(state, agent, name):
    """에이전트 노드 생성 헬퍼 함수"""
    from langchain_core.messages import HumanMessage
    
    # agent 호출
    agent_response = agent.invoke(state)
    # agent의 마지막 메시지를 HumanMessage로 변환하여 반환
    return {
        "messages": [
            HumanMessage(content=agent_response["messages"][-1].content, name=name)
        ]
    }

# 향후 에이전트 기반 노드로 확장할 때 사용
# manse_agent_node = functools.partial(agent_node, agent=manse_agent, name="ManseAgent")
# web_agent_node = functools.partial(agent_node, agent=web_agent, name="WebAgent")