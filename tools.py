"""
FortuneAI Tools
모든 사주 상담 도구들을 통합 관리
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.tools import tool, Tool
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus
import re

# 기존 모듈들 import
from vector_store import load_vector_store, get_all_documents
from search import create_hybrid_retriever
from reranker import get_flashrank_reranker, rerank_documents

# 사주 계산 모듈 import
from saju_calculator import SajuCalculator, format_saju_analysis

class WebSearcher:
    """웹 검색 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """DuckDuckGo를 사용한 웹 검색"""
        try:
            # DuckDuckGo 검색 URL
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # 검색 결과 파싱
            for result in soup.find_all('div', class_='result')[:max_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
            
            return results
            
        except Exception as e:
            print(f"웹 검색 오류: {e}")
            return []
    
    def get_page_content(self, url: str, max_chars: int = 1000) -> str:
        """웹 페이지 내용 가져오기"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            
            # 텍스트 추출
            text = soup.get_text(separator=' ', strip=True)
            
            # 길이 제한
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return text
            
        except Exception as e:
            return f"페이지 내용을 가져올 수 없습니다: {e}"

class ToolManager:
    """도구 관리자 클래스"""
    
    def __init__(self, enable_rag: bool = True, enable_web: bool = False, enable_calendar: bool = False):
        """
        도구 관리자 초기화
        
        Args:
            enable_rag: RAG 도구 활성화 여부
            enable_web: 웹 검색 도구 활성화 여부
            enable_calendar: 만세력 도구 활성화 여부
        """
        self.enable_rag = enable_rag
        self.enable_web = enable_web
        self.enable_calendar = enable_calendar
        
        # RAG 컴포넌트들
        self.vectorstore = None
        self.hybrid_retriever = None
        self.reranker = None
        self.all_docs = None
        
        # 웹 검색 컴포넌트들
        self.web_searcher = None
        
        # 만세력 컴포넌트들
        self.calendar_api = None
        
        self.tools = []
        self.initialize()
    
    def initialize(self):
        """모든 활성화된 도구들 초기화"""
        print("🛠️ 도구 시스템 초기화 중...")
        
        if self.enable_rag:
            self._initialize_rag()
        
        if self.enable_web:
            self._initialize_web()
        
        if self.enable_calendar:
            self._initialize_calendar()
        
        self._setup_tools()
        print(f"✅ 총 {len(self.tools)}개 도구 초기화 완료!")
    
    def _initialize_rag(self):
        """RAG 컴포넌트들 초기화"""
        print("🔧 RAG 도구 초기화 중...")
        
        # 벡터 스토어 로드
        self.vectorstore = load_vector_store("saju_vectordb")
        
        # 모든 문서 가져오기
        self.all_docs = get_all_documents(self.vectorstore)
        
        # 하이브리드 검색기 초기화
        self.hybrid_retriever = create_hybrid_retriever(
            vectorstore=self.vectorstore, 
            documents=self.all_docs, 
            weights=[0.8, 0.2],
            top_k=20
        )
        
        # 리랭커 초기화
        self.reranker = get_flashrank_reranker()
        
        print("✅ RAG 도구 초기화 완료!")
    
    def _initialize_web(self):
        """웹 검색 도구 초기화"""
        print("🌐 웹 검색 도구 초기화 중...")
        self.web_searcher = WebSearcher()
        print("✅ 웹 검색 도구 초기화 완료!")
    
    def _initialize_calendar(self):
        """만세력 도구 초기화"""
        print("📅 만세력 도구 초기화 중...")
        # TODO: 만세력 API 클라이언트 초기화
        print("✅ 만세력 도구 초기화 완료!")
    
    def _setup_tools(self):
        """활성화된 도구들 설정"""
        self.tools = []
        
        if self.enable_rag:
            self.tools.extend(self._get_rag_tools())
        
        if self.enable_web:
            self.tools.extend(self._get_web_tools())
        
        if self.enable_calendar:
            self.tools.extend(self._get_calendar_tools())
    
    def _get_rag_tools(self) -> List[Tool]:
        """RAG 기반 도구들 반환"""
        
        @tool
        def search_saju_knowledge(query: str) -> str:
            """사주팔자, 운세, 오행, 십신 등에 대한 전문 지식을 검색합니다. 사주 관련 질문이나 개념 설명이 필요할 때 사용하세요."""
            try:
                # 하이브리드 검색 수행
                docs = self.hybrid_retriever.invoke(query)
                
                # 리랭킹 수행
                reranked_docs = rerank_documents(self.reranker, docs, query)
                
                # 상위 5개 문서만 사용
                top_docs = reranked_docs[:5]
                
                # 컨텍스트 생성
                context = "\n\n".join([doc.page_content for doc in top_docs])
                
                return f"검색된 사주 지식:\n{context}"
            except Exception as e:
                return f"검색 중 오류 발생: {str(e)}"
        
        @tool
        def analyze_birth_info(birth_info: str) -> str:
            """생년월일시 정보를 바탕으로 정확한 사주팔자를 계산하고 분석합니다. 생년월일시가 주어졌을 때 사용하세요."""
            try:
                # 생년월일시 정보 파싱
                birth_data = self._parse_birth_info(birth_info)
                if not birth_data:
                    return "생년월일시 정보를 정확히 파악할 수 없습니다. 예: 1995년 8월 26일 오전 10시 15분"
                
                # 사주 계산기 초기화
                calculator = SajuCalculator()
                
                # 사주팔자 계산
                saju_chart = calculator.calculate_saju(
                    year=birth_data['year'],
                    month=birth_data['month'], 
                    day=birth_data['day'],
                    hour=birth_data['hour'],
                    minute=birth_data['minute'],
                    is_male=birth_data.get('is_male', True)
                )
                
                # 분석 결과 포맷팅
                analysis_result = format_saju_analysis(saju_chart, calculator)
                
                # 추가 사주 지식 검색
                day_master = saju_chart.get_day_master()
                knowledge_query = f"사주 {day_master} 일간 성격 특성 운세"
                knowledge = search_saju_knowledge.invoke(knowledge_query)
                
                return f"{analysis_result}\n\n=== 추가 사주 해석 ===\n{knowledge}"
                
            except Exception as e:
                return f"사주 분석 중 오류 발생: {str(e)}"
        
        @tool
        def get_fortune_reading(topic: str, birth_info: str = "", context_info: str = "") -> str:
            """특정 주제(직업운, 재물운, 건강운, 애정운 등)에 대한 운세를 사주 기반으로 분석합니다."""
            try:
                result_parts = []
                
                # 생년월일시가 있으면 사주 기반 분석
                if birth_info:
                    birth_data = self._parse_birth_info(birth_info)
                    if birth_data:
                        calculator = SajuCalculator()
                        saju_chart = calculator.calculate_saju(
                            year=birth_data['year'], month=birth_data['month'], 
                            day=birth_data['day'], hour=birth_data['hour'],
                            minute=birth_data['minute'], is_male=birth_data.get('is_male', True)
                        )
                        
                        day_master = saju_chart.get_day_master()
                        ten_gods = calculator.analyze_ten_gods(saju_chart)
                        elements = calculator.get_element_strength(saju_chart)
                        
                        # 사주 기반 운세 분석
                        saju_analysis = f"""
=== 사주 기반 {topic} 분석 ===
일간: {day_master}
오행 강약: {elements}
십신 배치: {ten_gods}
                        """
                        result_parts.append(saju_analysis)
                
                # 전통 사주 지식 검색
                query = f"{topic} 운세 분석 {context_info} 사주 오행 십신 {birth_info}"
                knowledge = search_saju_knowledge.invoke(query)
                result_parts.append(f"=== 전통 사주 지식 ===\n{knowledge}")
                
                return "\n\n".join(result_parts)
                
            except Exception as e:
                return f"운세 분석 중 오류 발생: {str(e)}"
        
        return [search_saju_knowledge, analyze_birth_info, get_fortune_reading]
    
    def _parse_birth_info(self, birth_info: str) -> Dict:
        """생년월일시 정보 파싱"""
        try:
            # 정규식으로 생년월일시 추출
            # 예: "1995년 8월 26일 오전 10시 15분", "1995-08-26 10:15"
            
            # 년도 추출
            year_match = re.search(r'(\d{4})년?', birth_info)
            if not year_match:
                return None
            year = int(year_match.group(1))
            
            # 월 추출
            month_match = re.search(r'(\d{1,2})월', birth_info)
            if not month_match:
                return None
            month = int(month_match.group(1))
            
            # 일 추출
            day_match = re.search(r'(\d{1,2})일', birth_info)
            if not day_match:
                return None
            day = int(day_match.group(1))
            
            # 시간 추출
            hour = 12  # 기본값
            minute = 0  # 기본값
            
            # 오전/오후 처리
            if '오전' in birth_info or 'AM' in birth_info.upper():
                hour_match = re.search(r'오전\s*(\d{1,2})시?', birth_info)
                if hour_match:
                    hour = int(hour_match.group(1))
                    if hour == 12:
                        hour = 0
            elif '오후' in birth_info or 'PM' in birth_info.upper():
                hour_match = re.search(r'오후\s*(\d{1,2})시?', birth_info)
                if hour_match:
                    hour = int(hour_match.group(1))
                    if hour != 12:
                        hour += 12
            else:
                # 24시간 형식
                hour_match = re.search(r'(\d{1,2})시', birth_info)
                if hour_match:
                    hour = int(hour_match.group(1))
            
            # 분 추출
            minute_match = re.search(r'(\d{1,2})분', birth_info)
            if minute_match:
                minute = int(minute_match.group(1))
            
            # 성별 추출
            is_male = True  # 기본값
            if '여자' in birth_info or '여성' in birth_info or '여' in birth_info:
                is_male = False
            elif '남자' in birth_info or '남성' in birth_info or '남' in birth_info:
                is_male = True
            
            return {
                'year': year, 'month': month, 'day': day,
                'hour': hour, 'minute': minute, 'is_male': is_male
            }
            
        except Exception as e:
            print(f"생년월일시 파싱 오류: {e}")
            return None
    
    def _get_web_tools(self) -> List[Tool]:
        """웹 검색 기반 도구들 반환"""
        
        @tool
        def search_web_fortune(query: str) -> str:
            """현재 운세나 최신 점성술 정보를 웹에서 검색합니다. 실시간 정보나 최신 운세 트렌드가 필요할 때 사용하세요."""
            try:
                # 한국어 운세 관련 키워드 추가
                search_query = f"{query} 운세 사주 점성술"
                results = self.web_searcher.search_duckduckgo(search_query, max_results=3)
                
                if not results:
                    return "웹 검색 결과를 찾을 수 없습니다."
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   {result['snippet']}\n"
                        f"   출처: {result['url']}"
                    )
                
                return f"웹 검색 결과:\n\n" + "\n\n".join(formatted_results)
                
            except Exception as e:
                return f"웹 검색 중 오류 발생: {str(e)}"
        
        @tool
        def get_current_horoscope(sign_or_date: str) -> str:
            """특정 별자리나 날짜의 최신 운세를 웹에서 검색합니다."""
            try:
                search_query = f"{sign_or_date} 오늘 운세 별자리 horoscope"
                results = self.web_searcher.search_duckduckgo(search_query, max_results=3)
                
                if not results:
                    return "운세 정보를 찾을 수 없습니다."
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   {result['snippet']}\n"
                        f"   출처: {result['url']}"
                    )
                
                return f"{sign_or_date} 운세 검색 결과:\n\n" + "\n\n".join(formatted_results)
                
            except Exception as e:
                return f"운세 검색 중 오류 발생: {str(e)}"
        
        @tool
        def search_fortune_trends(topic: str) -> str:
            """운세나 사주 관련 최신 트렌드와 정보를 검색합니다."""
            try:
                search_query = f"{topic} 2025 트렌드 사주 운세 점성술"
                results = self.web_searcher.search_duckduckgo(search_query, max_results=3)
                
                if not results:
                    return "관련 트렌드 정보를 찾을 수 없습니다."
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   {result['snippet']}\n"
                        f"   출처: {result['url']}"
                    )
                
                return f"{topic} 관련 최신 트렌드:\n\n" + "\n\n".join(formatted_results)
                
            except Exception as e:
                return f"트렌드 검색 중 오류 발생: {str(e)}"
        
        return [search_web_fortune, get_current_horoscope, search_fortune_trends]
    
    def _get_calendar_tools(self) -> List[Tool]:
        """만세력 기반 도구들 반환"""
        
        @tool
        def calculate_saju_pillars(birth_year: int, birth_month: int, birth_day: int, birth_hour: int, is_lunar: bool = False) -> str:
            """생년월일시를 바탕으로 정확한 사주팔자를 계산합니다."""
            # TODO: 실제 만세력 API 연동
            return f"사주팔자 계산 결과 (미구현): {birth_year}년 {birth_month}월 {birth_day}일 {birth_hour}시"
        
        @tool
        def get_lunar_calendar(solar_date: str) -> str:
            """양력 날짜를 음력으로 변환합니다."""
            # TODO: 음력 변환 API 연동
            return f"음력 변환 결과 (미구현): {solar_date}"
        
        @tool
        def calculate_compatibility(person1_birth: str, person2_birth: str) -> str:
            """두 사람의 사주팔자 궁합을 계산합니다."""
            # TODO: 궁합 계산 로직 구현
            return f"궁합 계산 결과 (미구현): {person1_birth} vs {person2_birth}"
        
        return [calculate_saju_pillars, get_lunar_calendar, calculate_compatibility]
    
    def get_tools(self) -> List[Tool]:
        """모든 활성화된 도구들 반환"""
        return self.tools
    
    def get_tool_info(self) -> Dict[str, Any]:
        """도구 정보 반환"""
        return {
            "total_tools": len(self.tools),
            "rag_enabled": self.enable_rag,
            "web_enabled": self.enable_web,
            "calendar_enabled": self.enable_calendar,
            "tool_names": [tool.name for tool in self.tools]
        } 