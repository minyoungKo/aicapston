import json

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.tools import tool

@tool
def summarize_news_links(query: str) -> str:
    """
    사용자의 질의(예: 종목명)를 기반으로 뉴스를 검색하고,
    본문을 크롤링한 뒤 유사도 필터링을 거쳐 GPT-4o로 종합 분석합니다.
    """
    try:
        from news_tools.news_search import search_news
        raw = search_news.invoke(query)
        results = json.loads(raw)
        urls = [
            item.get("originallink") or item.get("link")
            for item in results
            if item.get("originallink") or item.get("link")
        ]
        print("[DEBUG] 분석 대상 링크 수:", len(urls))
        print("[DEBUG] 링크: ", urls)
        if not urls:
            return "❌ 유효한 뉴스 링크가 없습니다."

        # 본문 크롤링 및 로딩 (SoupStrainer 제거 → 전체 HTML 파싱)
        loader = WebBaseLoader(web_paths=urls)
        docs = loader.load()
        if not docs:
            return "❌ 뉴스 본문 수집 실패"

        # 디버깅 출력
        print(f"[DEBUG] 수집된 문서 수: {len(docs)}")
        for i, doc in enumerate(docs):
            preview = doc.page_content[:200].replace("\n", " ").strip()
            print(f"[DEBUG] 문서 {i+1}: 길이={len(doc.page_content)} / 미리보기: {preview}")

        # 본문 청크 분할
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=30)
        splits = splitter.split_documents(docs)
        if not splits:
            return "❌ 뉴스 본문이 너무 짧아 분석할 수 없습니다."

        # 벡터스토어 및 유사도 필터링
        vectorstore = FAISS.from_documents(splits, embedding=OpenAIEmbeddings())
        query_embedding = f"{query} 주식에 영향을 미치는 뉴스 요약 및 산업 분석"
        scored_results = vectorstore.similarity_search_with_score(query_embedding, k=50)
        keyword = query.strip()
        filtered_docs = [doc for doc, score in scored_results if score <= 0.3 and keyword in doc.page_content]

        if not filtered_docs:
            return "❌ 유사도 높은 뉴스 본문을 찾지 못했습니다."

        # 분석 문맥 구성
        merged_context = "\n\n".join(doc.page_content for doc in filtered_docs)

        # 분석 프롬프트 정의
        prompt = PromptTemplate.from_template(
            f"""
            다음은 뉴스 기사에서 추출한 문맥입니다. 반드시 '{query}' 관련 내용만 분석하세요.
            다른 기업, 산업은 언급하더라도 분석에는 포함하지 마세요.

            1. 📰 핵심 요약 (10줄 이내)
            2. 📈 긍정 요인 / 📉 부정 요인
            3. 🔮 산업 및 주가 영향 요인

            #Context:
            {{context}}

            #Answer:
            """
        )

        # LLM 분석
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        chain = (
            RunnablePassthrough.assign(context=lambda _: merged_context)
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke({})

    except Exception as e:
        return f"❌ 뉴스 분석 중 오류 발생: {e}"

# 단독 실행 테스트
if __name__ == "__main__":
    print(summarize_news_links.invoke("삼성전자"))