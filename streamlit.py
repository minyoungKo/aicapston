import streamlit as st
import asyncio

# ✅ Supervisor Graph 로드 (report 함수 제거됨)
from agents.supervisor import defined_supervisor_graph

# ✅ Streamlit 기본 설정
st.set_page_config(page_title="통합 주식 분석", layout="wide")
st.title("📊 통합 주식 분석 대시보드")

# ✅ 사용자 입력
user_input = st.text_input("분석할 종목명을 입력하세요", "삼성전자")

if st.button("🔍 개별 분석 실행"):
    with st.spinner("에이전트들이 분석 중입니다..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # run_until 명시 필요 없음 (이미 generate_report 제거됨)
            state = loop.run_until_complete(
                defined_supervisor_graph.ainvoke({"input": user_input})
            )
        finally:
            loop.close()
        st.session_state["analysis_state"] = state  # ✅ 분석 결과 저장

# 분석 결과 출력 (세션에 state가 있을 때만)
if "analysis_state" in st.session_state:
    state = st.session_state["analysis_state"]

    # 🔽 기존 코드에서 이 부분 교체
    st.subheader("📈 차트 분석 결과")

    chart_result = state["results"].get("chart_analyzer", {})

    # dict가 아니고 문자열이면 오류 처리
    if isinstance(chart_result, str):
        st.markdown(chart_result)
    else:
        # 요약 해석 출력
        st.markdown(chart_result.get("summary", "_차트 분석 요약 없음_"))

        # 시각화 가능하면 시각화 출력
        if "chart_json" in chart_result:
            try:
                import pandas as pd
                import plotly.graph_objects as go
                import json

                df = pd.read_json(chart_result["chart_json"])
                df["Date"] = pd.to_datetime(df["Date"])
                df.set_index("Date", inplace=True)


                # ✅ Plotly 캔들차트 시각화 함수 정의 (간단한 버전)
                def plot_chart(df):
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name="Candlestick"
                    ))
                    # 예: SMA 추가
                    if 'SMA20' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA20", line=dict(color="orange")))
                    fig.update_layout(title="차트 시각화", xaxis_rangeslider_visible=False)
                    return fig


                st.plotly_chart(plot_chart(df), use_container_width=True)
            except Exception as e:
                st.error(f"시각화 중 오류 발생: {e}")

    st.subheader("📰 뉴스 분석 결과")
    st.markdown(state["results"].get("news_analyzer", "_분석 결과 없음_"))

    st.subheader("💰 재무제표 분석 결과")
    st.markdown(state["results"].get("fundamental_analyzer", "_분석 결과 없음_"))

    st.subheader("📉 주가/시세 정보")
    st.markdown(state["results"].get("stock_info_collector", "_분석 결과 없음_"))

    st.markdown("---")
