import os
import json
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from requests.exceptions import SSLError, RequestException

load_dotenv()

#안전하게 문서 로딩하는 함수 (SSL 예외 제거)
def safe_load_documents(urls: list[str]) -> list:
    valid_docs = []
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            if docs:
                valid_docs.extend(docs)
        except SSLError as e:
            print(f"[SSL 제외] {url} → {e}")
        except RequestException as e:
            print(f"[요청 실패 제외] {url} → {e}")
        except Exception as e:
            print(f"[기타 예외 제외] {url} → {e}")
    return valid_docs

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
        if not urls:
            return "❌ 유효한 뉴스 링크가 없습니다."

        # ✅ 안전하게 문서 로딩
        docs = safe_load_documents(urls)
        if not docs:
            return "❌ 유효한 뉴스 본문을 수집하지 못했습니다."

        print(f"[DEBUG] 수집된 문서 수: {len(docs)}")

        # 본문 청크 분할
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=30)
        splits = splitter.split_documents(docs)
        if not splits:
            return "❌ 뉴스 본문이 너무 짧아 분석할 수 없습니다."

        print(f"[DEBUG] 총 청크 수: {len(splits)}")

        # 벡터스토어 및 유사도 필터링
        vectorstore = FAISS.from_documents(splits, embedding=OpenAIEmbeddings())
        query_embedding = f"{query} 주식에 영향을 미치는 뉴스 요약 및 분석"
        scored_results = vectorstore.similarity_search_with_score(query_embedding, k=50)
        keyword = query.strip()
        filtered_docs = [doc for doc, score in scored_results if score <= 0.35 and keyword in doc.page_content]
        if not filtered_docs:
            return "❌ 유사도 높은 뉴스 본문을 찾지 못했습니다."

        # 분석 문맥 구성
        merged_context = "\n\n".join(doc.page_content for doc in filtered_docs)

        # 프롬프트 정의
        # 프롬프트 정의
        prompt = PromptTemplate.from_template(
            f"""
        당신은 금융 리서치 센터의 전문 애널리스트입니다.  
        다음은 특정 기업 또는 산업에 대한 뉴스 문맥(Context)입니다.

        🎯 분석 대상 키워드: **'{query}'**

        🛑 분석 지침:
        - 문맥에 등장하는 다른 기업이나 산업이 있다 하더라도, **'{query}'와 직접적으로 관련된 내용만 분석 대상에 포함**하세요.
        - **추측은 금지**하며, **문맥 내 명시된 사실**에 기반해 분석하세요.
        - **문단 요약은 금지**하며, **각 항목은 명확한 포인트 기반 bullet 형식으로 작성**하세요.
        - 어조는 **객관적이고 분석적이며**, **투자자 리포트 형식에 준하도록 정제된 표현**을 사용하세요.

        분석은 아래 항목 순서에 따라 작성하세요:

        ---

        ### 1. 🧾 핵심 요약 (최대 10줄, bullet point)
        - 날짜 기반 또는 흐름 기반으로 주요 사실을 정리하세요.
        - 절대로 문단 요약 형태로 작성하지 마세요.

        ### 2. ✅ 우호적 요인 (긍정적 요인, 최소 5가지)
        - 기업 또는 산업에 긍정적으로 작용할 수 있는 팩트 또는 시사점을 bullet로 작성하세요.

        ### 3. ⚠️ 위험 요인 (부정적 요인, 최소 5가지)
        - 잠재적 리스크나 시장 반응 가능성을 bullet로 작성하세요.

        ### 4. 📊 산업 및 주가 영향 요인 (최소 5가지)
        - 뉴스가 산업/주가에 미칠 수 있는 단기적 또는 중장기적 영향 요인을 분석하세요.
        - **단기 vs 중장기 구분**이 가능하면 명시하세요.

        ---

        #Context:
        {{context}}
        """
        )

        # 분석 체인
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        chain = (
            RunnablePassthrough.assign(context=lambda _: merged_context)
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke({})

    except Exception as e:
        return f"❌ 뉴스 분석 중 예외 발생: {type(e).__name__}: {e}"

# 테스트용 실행
if __name__ == "__main__":
    print(summarize_news_links.invoke("삼성전자"))