import streamlit as st
import asyncio

# ✅ Supervisor Graph 로드 (report 함수 제거됨)
from agents.supervisor import defined_supervisor_graph

# ✅ Streamlit 기본 설정
st.set_page_config(page_title="통합 주식 분석", layout="wide")
st.title("📊 주식 분석 에이전트 대시보드")

# ✅ 사용자 입력
user_input = st.text_input("분석할 종목명을 입력하세요", placeholder="삼성전자")

if st.button("🔍 개별 분석 실행"):
    with st.spinner("분석 중입니다..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # run_until 명시 필요 없음 (이미 generate_report 제거됨)
            state = loop.run_until_complete(
                defined_supervisor_graph.ainvoke({"input": user_input})
            )
        finally:
            loop.close()
        st.session_state["analysis_state"] = state

# 분석 결과 출력 (세션에 state가 있을 때만)
if "analysis_state" in st.session_state:
    state = st.session_state["analysis_state"]

    st.subheader("📈 차트 분석 결과")
    st.markdown(state["results"].get("chart_analyzer", "_분석 결과 없음_"))

    st.subheader("📰 뉴스 분석 결과")
    st.markdown(state["results"].get("news_analyzer", "_분석 결과 없음_"))

    st.subheader("💰 재무제표 분석 결과")
    st.markdown(state["results"].get("fundamental_analyzer", "_분석 결과 없음_"))

    st.subheader("📉 주가/시세 정보")
    st.markdown(state["results"].get("stock_info_collector", "_분석 결과 없음_"))

    st.markdown("---")
