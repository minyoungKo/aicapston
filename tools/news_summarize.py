# Tool로 사용 가능한 뉴스 분석 함수 (RAG 기반, 링크 기반 버전)

import bs4
import json

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.tools import tool

#본문 파싱 필터
domains_filter = bs4.SoupStrainer(
    "div",
    attrs={"class": [
        "newsct_article _article_body", "media_end_head_title",
        "article","view_text","news_detail_body_group","view-article view-box",
        "story-news article","cont_view"
    ]},
)

#summarize_news_links Tool 정의 (자연어 쿼리 기반)
@tool
def summarize_news_links(query: str) -> str:
    """
    사용자의 질의(예: 종목명)를 기반으로 뉴스를 검색하고,
    본문을 크롤링한 뒤 유사도 필터링을 거쳐 GPT-4o로 종합 분석합니다.
    """
    try:
        from tools.news_search import search_news
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

        #본문 크롤링 및 로딩
        loader = WebBaseLoader(web_paths=urls, bs_kwargs={"parse_only": domains_filter})
        docs = loader.load()
        if not docs:
            return "❌ 뉴스 본문 수집 실패"

        #본문 청크 분할
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=30)
        splits = splitter.split_documents(docs)
        if not splits:
            return "❌ 뉴스 본문이 너무 짧아 분석할 수 없습니다."

        #벡터스토어 및 유사도 필터링
        vectorstore = FAISS.from_documents(splits, embedding=OpenAIEmbeddings())
        query_embedding = f"{query} 관련 주식에 영향을 미치는 뉴스 요약 및 산업 분석"
        scored_results = vectorstore.similarity_search_with_score(query_embedding, k=50)
        filtered_docs = [doc for doc, score in scored_results if score <= 0.4]  # 유사도 0.7 이상만

        if not filtered_docs:
            return "❌ 유사도 높은 뉴스 본문을 찾지 못했습니다."

        #분석 문맥 구성
        merged_context = "\n\n".join(doc.page_content for doc in filtered_docs)

        #분석 프롬프트 정의
        prompt = PromptTemplate.from_template(
            """
            다음은 관련 뉴스 기사에서 추출한 문맥입니다.
            문맥을 바탕으로 다음 항목을 중심으로 분석해 주세요:

            1. 📰 핵심 요약 (10줄 이내)
            2. 📈 긍정 요인 / 📉 부정 요인
            3. 🔮 산업 및 주가 영향 요인

            #Context:
            {context}

            #Answer:
            """
        )

        #LLM 분석
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

#단독 실행 테스트
if __name__ == "__main__":
    print(summarize_news_links.invoke("삼성전자"))