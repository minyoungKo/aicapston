from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Optional

from fundamental_tools.pl_statement import analyze_profit_loss_from_db
from fundamental_tools.bs_statement import analyze_balance_sheet_from_db
from fundamental_tools.cf_statement import analyze_cash_flow_from_db
from fundamental_tools.summary import generate_final_summary

# ✅ 1. 상태 정의
class FinancialState(TypedDict):
    corp_name: str
    pl: Optional[str]
    bs: Optional[str]
    cf: Optional[str]
    summary: Optional[str]

# ✅ 2. 각 노드를 Runnable로 래핑

analyze_pl_node = RunnableLambda(lambda state: {
    **state,
    "pl": analyze_profit_loss_from_db.invoke(state["corp_name"])
})

analyze_bs_node = RunnableLambda(lambda state: {
    **state,
    "bs": analyze_balance_sheet_from_db.invoke(state["corp_name"])
})

analyze_cf_node = RunnableLambda(lambda state: {
    **state,
    "cf": analyze_cash_flow_from_db.invoke(state["corp_name"])
})

summarize_node = RunnableLambda(lambda state: {
    **state,
    "summary": generate_final_summary(state["pl"], state["bs"], state["cf"])
})

# ✅ 3. LangGraph 구성

graph = StateGraph(FinancialState)

graph.set_entry_point("analyze_pl")

graph.add_node("analyze_pl", analyze_pl_node)
graph.add_node("analyze_bs", analyze_bs_node)
graph.add_node("analyze_cf", analyze_cf_node)
graph.add_node("summarize", summarize_node)

graph.add_edge("analyze_pl", "analyze_bs")
graph.add_edge("analyze_bs", "analyze_cf")
graph.add_edge("analyze_cf", "summarize")
graph.add_edge("summarize", END)

# ✅ 4. 컴파일된 LangGraph 객체
compiled_financial_graph = graph.compile()

# ✅ 5. LangChain Tool로 wrapping
from langchain.tools import Tool

financial_graph_tool = Tool.from_function(
    name="financial_graph_tool",
    func=lambda corp_name: compiled_financial_graph.invoke({"corp_name": corp_name}),
    description="종목명을 입력받아 손익계산서, 재무상태표, 현금흐름표를 분석하고 종합 보고서를 생성합니다."
)