import streamlit as st
import asyncio
from agents.supervisor import defined_supervisor_graph

st.set_page_config(page_title="📊 종합 주식 분석 에이전트", layout="centered")
st.title("📈 AI 기반 종합 주식 분석 시스템")

# 사용자 입력
user_input = st.text_input("🔎 분석할 종목 또는 질문을 입력하세요", placeholder="예: 삼성전자 주가 분석해줘")

# 상태 관리
if 'response' not in st.session_state:
    st.session_state.response = None

# 버튼 클릭 시 분석 수행
if st.button("분석 시작") and user_input:
    with st.spinner("📡 에이전트가 분석 중입니다..."):
        try:
            result = asyncio.run(defined_supervisor_graph.ainvoke({"input": user_input}))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(defined_supervisor_graph.ainvoke({"input": user_input}))

        st.session_state.response = result

# 결과 출력
if st.session_state.response:
    st.markdown("### 🧾 종합 분석 보고서")
    st.markdown(st.session_state.response.get("report", "[보고서 없음]"))

    # 디버깅용 JSON 응답 보기 (선택 사항)
    # st.markdown("### 🔍 Raw 결과")
    # st.json(st.session_state.response)
