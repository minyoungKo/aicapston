from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict, Optional, List, Dict
import asyncio
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from tools.wrapped_agents import (
    invoke_stock_info_collector,
    invoke_news_analyzer,
    invoke_chart_analyzer,
    invoke_fundamental
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 상태 스키마 정의
class SupervisorState(TypedDict):
    input: str
    routes: List[str]
    results: Dict[str, str]
    report: Optional[str]

# 라우터 노드
async def multi_router_node(state: SupervisorState) -> SupervisorState:
    user_input = state["input"]
    prompt = (
        "다음 사용자 입력에 대해 어떤 도구들을 함께 사용할지 판단하세요.\n"
        "반드시 아래 도구 이름들 중 필요한 것만 골라서 Python 리스트 형식으로 반환하세요.\n"
        "- stock_info_collector: 주가, 시세, 거래량 등\n"
        "- news_analyzer: 종목 관련 뉴스 수집 및 분석\n"
        "- chart_analyzer: 차트 기반 기술적 분석\n"
        "- fundamental_analyzer: 재무제표 기반 분석(매출액,당기순이익,재무상태표,현금흐름표,손익계산서)\n\n"
        f"입력: {user_input}\n"
        "출력 예시: ['stock_info_collector', 'chart_analyzer']"
    )
    response = await llm.ainvoke(prompt)
    try:
        routes = eval(response.content.strip())
    except:
        routes = []
    return {"routes": routes, "input": user_input, "results": {}, "report": None}

# 병렬 실행 함수
async def run_parallel_tools(user_input: str, routes: list[str]) -> dict:
    route_to_func = {
        "stock_info_collector": invoke_stock_info_collector,
        "chart_analyzer": invoke_chart_analyzer,
        "news_analyzer": invoke_news_analyzer,
        "fundamental_analyzer": invoke_fundamental,
    }

    coroutines = []
    for route in routes:
        func = route_to_func.get(route)
        if func:
            coroutine = func(user_input)
            coroutines.append((route, coroutine))

    results_raw = await asyncio.gather(
        *[c for _, c in coroutines], return_exceptions=True
    )

    results = {}
    for (route, _), result in zip(coroutines, results_raw):
        if isinstance(result, Exception):
            results[route] = f"[{route}] 에러: {str(result)}"
        else:
            results[route] = result

    return results

# 병렬 실행 노드
async def parallel_node(state: SupervisorState) -> SupervisorState:
    results = await run_parallel_tools(state["input"], state["routes"])
    return {
        "input": state["input"],
        "routes": state["routes"],
        "results": results,
        "report": None  # 이제 report는 사용하지 않음
    }

# 그래프 구성
builder = StateGraph(SupervisorState)

builder.add_node("router", multi_router_node)
builder.add_node("parallel_executor", parallel_node)

builder.set_entry_point("router")
builder.add_edge("router", "parallel_executor")
builder.set_finish_point("parallel_executor")

# 컴파일
defined_supervisor_graph = builder.compile()

# 실행 예시 (비동기)
if __name__ == "__main__":
    async def main():
        while True:
            query = input("\n무엇을 도와드릴까요? ")
            if query.lower() in ["exit", "quit"]:
                break
            result = await defined_supervisor_graph.ainvoke({"input": query})
            print("\n[개별 분석 결과]")
            for key, value in result["results"].items():
                print(f"\n🔹 {key}\n{value}")

    asyncio.run(main())
