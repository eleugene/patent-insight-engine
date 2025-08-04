import streamlit as st
import os
from dotenv import load_dotenv
import math

from src.kipris_handler import search_patents
from src.llm_handler import summarize_text_with_gemini

load_dotenv()
KIPRIS_API_KEY = os.getenv("KIPRIS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(layout="wide")
st.title(" patent Insight Engine")

if 'patent_list' not in st.session_state:
    st.session_state.patent_list = []
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0
if 'page_no' not in st.session_state:
    st.session_state.page_no = 1
if 'keyword' not in st.session_state:
    st.session_state.keyword = ""

keyword_input = st.text_input("분석하고 싶은 특허 키워드를 입력하세요:")
if st.button("특허 검색"):
    st.session_state.keyword = keyword_input
    st.session_state.page_no = 1

if st.session_state.keyword:
    with st.spinner("KIPRIS에서 특허 목록을 검색 중입니다..."):
        st.session_state.patent_list, st.session_state.total_count = search_patents(KIPRIS_API_KEY, st.session_state.keyword, st.session_state.page_no)
    
    if st.session_state.patent_list:
        st.success(f"'{st.session_state.keyword}'에 대한 특허 총 {st.session_state.total_count}건 중, {len(st.session_state.patent_list)}건을 표시합니다.")
        
        total_pages = math.ceil(st.session_state.total_count / 10)
        st.subheader(f"페이지 {st.session_state.page_no} / {total_pages}")
        
        col1, col2 = st.columns(2)
        if col1.button("이전 페이지", disabled=(st.session_state.page_no <= 1)):
            st.session_state.page_no -= 1
            st.rerun()

        if col2.button("다음 페이지", disabled=(st.session_state.page_no >= total_pages)):
            st.session_state.page_no += 1
            st.rerun()

        for i, patent in enumerate(st.session_state.patent_list):
            with st.expander(f"**{i+1}. {patent['title']}**"):
                st.markdown(f"**- 출원인:** {patent['applicant']}")
                # st.markdown(f"**- 발명자:** {patent['inventor']}") # 이 라인을 삭제하거나 주석 처리
                st.markdown(f"**- 출원번호/일자:** {patent['app_num']} / {patent['app_date']}")
                st.markdown(f"**- 등록상태:** {patent['reg_status']}")
                st.markdown(f"**- 등록번호/일자:** {patent['reg_num']} / {patent['reg_date']}")
                st.markdown(f"**- KIPRIS 바로가기:** [상세 정보 보기]({patent['link']})")
                
                st.subheader("초록")
                st.write(patent['abstract'])
                
                if st.button(f"'{patent['title'][:30]}...' 요약하기", key=f"summary_btn_{i}"):
                    with st.spinner("Gemini가 특허를 분석 및 요약 중입니다..."):
                        summary = summarize_text_with_gemini(GEMINI_API_KEY, patent['abstract'])
                    st.subheader("Gemini 요약 결과")
                    st.info(summary)
    else:
        st.error("해당 키워드로 검색된 특허가 없습니다.")