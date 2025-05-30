import os
import uuid
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# from embeddings import get_bge_embeddings
from vector_store import load_vector_store, get_all_documents
from search import create_hybrid_retriever
from models import get_openai_llm, get_gemini_llm, get_bge_embeddings
from reranker import get_flashrank_reranker
from rag import RagPipeline, retrieve_and_generate

def initialize_rag_pipeline():
    """RAG 파이프라인 초기화"""
    
    # 임베딩 모델 로드
    embeddings = get_bge_embeddings()
    
    # 벡터 스토어 로드
    vectorstore = load_vector_store("saju_vectordb")
    
    # 모든 문서 가져오기
    all_docs = get_all_documents(vectorstore)
    
    # 하이브리드 검색기 초기화 (EnsembleRetriever 사용, 시맨틱 70%, BM25 30%)
    hybrid_retriever = create_hybrid_retriever(
        vectorstore=vectorstore, 
        documents=all_docs, 
        weights=[0.8, 0.2],
        top_k=20  # 명시적으로 top_k 설정
    )
    
    # LLM 모델 초기화
    # llm = get_openai_llm()
    llm = get_gemini_llm()  # Gemini 모델 사용
    
    # 리랭커 초기화
    reranker = get_flashrank_reranker()
    
    # RAG 파이프라인 생성
    pipeline = RagPipeline(hybrid_retriever, llm, reranker)
    
    return pipeline

def main():
    """메인 함수"""
    print("Fortune AI RAG 시스템 (POC 버전)")
    print("종료하려면 'q' 또는 'exit'를 입력하세요.")
    print("새 대화를 시작하려면 'new'를 입력하세요.")
    print("대화 내용은 자동으로 기억되며, 세션별로 관리됩니다.")
    print("=" * 50)
    
    # 고유한 세션 ID 생성
    session_id = str(uuid.uuid4())
    print(f"현재 세션 ID: {session_id}")
    print("=" * 50)
    
    # RAG 파이프라인 초기화
    pipeline = initialize_rag_pipeline()
    
    # 대화 루프
    while True:
        query = input("\n질문을 입력하세요: ")
        
        if query.lower() in ['q', 'exit']:
            print("프로그램을 종료합니다.")
            break
        
        if query.lower() == 'new':
            # 새 세션 시작
            session_id = str(uuid.uuid4())
            print(f"\n새 세션을 시작합니다. 세션 ID: {session_id}")
            print("=" * 50)
            continue
        
        if not query.strip():
            continue
        
        try:
            # RAG 파이프라인 실행 (세션 ID 전달)
            answer = retrieve_and_generate(query, pipeline, session_id)
            print("\n답변:")
            print(answer)
            print("=" * 50)
        except Exception as e:
            print(f"오류 발생: {e}")
            print("다시 시도해 주세요.")
            print("=" * 50)

if __name__ == "__main__":
    main() 