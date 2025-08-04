import streamlit as st
import os
from dotenv import load_dotenv

from src.kipris_handler import search_patents
from src.llm_handler import summarize_text_with_gemini

load_dotenv()
KIPRIS_API_KEY = os.getenv("KIPRIS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

st.title(" patent Insight Engine (프로토타입)")

keyword = st.text_input("분석하고 싶은 특허 키워드를 입력하세요:")

if st.button("특허 요약 실행"):
    if keyword:
        with st.spinner("KIPRIS에서 특허를 검색 중입니다..."):
            patent_abstract = search_patents(KIPRIS_API_KEY, keyword)

        st.info("검색된 특허 초록:")
        st.write(patent_abstract)

        # --- 핵심 개선 부분 ---
        # 유효한 초록이 있을 때만 Gemini를 호출하도록 변경
        if "초록 정보를 찾을 수 없습니다" not in patent_abstract and "검색 결과가 없습니다" not in patent_abstract:
            with st.spinner("Gemini가 특허 초록을 요약 중입니다..."):
                summary = summarize_text_with_gemini(GEMINI_API_KEY, patent_abstract)

            st.success("Gemini 요약 결과:")
            st.write(summary)
        else:
            st.error("유효한 초록 정보가 없어 요약을 진행할 수 없습니다.")
    else:
        st.warning("키워드를 입력해주세요.")