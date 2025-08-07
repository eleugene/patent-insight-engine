import streamlit as st
import os
from dotenv import load_dotenv
import math
import time

from src.kipris_handler import search_patents, search_all_patents, get_patent_details
from src.llm_handler import summarize_text_with_gemini, analyze_patent_data_with_gemini, analyze_detailed_data_with_gemini

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

st.subheader("1. 특허 키워드 검색")
keyword_input = st.text_input("분석할 특허 키워드를 입력하세요:", key="keyword_input", placeholder="예: 마이크로의료로봇")

if st.button("특허 검색"):
    st.session_state.keyword = keyword_input
    st.session_state.page_no = 1
    
    status_message = st.empty()
    status_message.info("KIPRIS API를 호출하여 특허 목록을 검색합니다...")
    
    patent_list, total_count = search_patents(KIPRIS_API_KEY, st.session_state.keyword)
    
    if patent_list:
        status_message.success(f"API 호출 성공! 총 {total_count}건의 특허를 찾았습니다.")
        st.session_state.patent_list = patent_list
        st.session_state.total_count = total_count
    else:
        status_message.error("API 호출에 실패했거나 검색 결과가 없습니다. 키워드를 확인해주세요.")
        st.session_state.patent_list = []
        st.session_state.total_count = 0
    
    time.sleep(2)
    status_message.empty()


if st.session_state.keyword:
    st.divider()
    st.subheader("2. AI 기반 특허 심층 분석")

    analysis_level = st.radio(
        "분석 수준을 선택하세요:",
        ('빠른 분석 (초록 기반)', '정밀 분석 (다중 필드 검색, 시간 소요)'),
        horizontal=True,
    )
    analysis_query = st.text_area("검색된 특허 전체에 대해 분석하고 싶은 내용을 자유롭게 입력하세요:", height=150,
                                  placeholder="예시)\n- 최근 10년간 가장 많이 출원한 출원인 순위와 건수를 알려줘\n- '서울대학교'가 출원한 특허들의 핵심 기술 동향을 요약해줘")

    if st.button("AI 분석 실행"):
        all_patents = []
        if analysis_level == '빠른 분석 (초록 기반)':
            with st.spinner("초록 필드에서 전체 특허를 수집 중입니다..."):
                all_patents = search_all_patents(api_key=KIPRIS_API_KEY, keyword=st.session_state.keyword, search_fields=["astrtCont"])
            
            if all_patents:
                st.info(f"총 {len(all_patents)}건의 특허를 기반으로 분석을 시작합니다.")
                with st.spinner("Gemini AI가 데이터를 심층 분석 중입니다..."):
                    analysis_result = analyze_patent_data_with_gemini(GEMINI_API_KEY, all_patents, analysis_query)
                st.subheader("AI 심층 분석 결과 (빠른 분석)")
                st.markdown(analysis_result)
        
        elif analysis_level == '정밀 분석 (다중 필드 검색, 시간 소요)':
            st.info("정밀 분석을 시작합니다. 제목, 초록, 청구항에서 모든 관련 특허를 수집하므로 시간이 몇 분 이상 소요될 수 있습니다.")
            
            progress_bar = st.progress(0, text="분석을 준비 중입니다...")
            def progress_callback(percentage, message):
                progress_bar.progress(percentage, text=message)

            search_fields_for_precise = ["inventionTitle", "astrtCont", "claim"]
            all_patents = search_all_patents(api_key=KIPRIS_API_KEY, keyword=st.session_state.keyword, search_fields=search_fields_for_precise, progress_callback=progress_callback)
            
            if all_patents:
                st.info(f"총 {len(all_patents)}건의 고유 특허를 기반으로 상세 정보 조회 및 분석을 시작합니다.")
                progress_bar.progress(0, text="각 특허의 상세 정보를 수집 중입니다...")
                for i, patent in enumerate(all_patents):
                    details = get_patent_details(KIPRIS_API_KEY, patent['app_num'])
                    if details:
                        patent.update(details)
                    time.sleep(0.3)
                    progress_bar.progress((i + 1) / len(all_patents), text=f"상세 정보 수집 중... ({i+1}/{len(all_patents)})")
                
                with st.spinner("Gemini AI가 상세 데이터를 심층 분석 중입니다..."):
                    analysis_result = analyze_detailed_data_with_gemini(GEMINI_API_KEY, all_patents, analysis_query)
                st.subheader("AI 심층 분석 결과 (정밀 분석)")
                st.markdown(analysis_result)
    
    if st.session_state.patent_list:
        st.divider()
        st.subheader("검색 결과 목록")
        
        total_pages = math.ceil(st.session_state.total_count / 10)
        st.write(f"페이지 {st.session_state.page_no} / {total_pages}")
        
        col1, col2 = st.columns(2)
        if col1.button("이전 페이지", disabled=(st.session_state.page_no <= 1)):
            with st.spinner("이전 페이지를 불러오는 중..."):
                st.session_state.page_no -= 1
                st.session_state.patent_list, _ = search_patents(KIPRIS_API_KEY, st.session_state.keyword, st.session_state.page_no)
            st.rerun()

        if col2.button("다음 페이지", disabled=(st.session_state.page_no >= total_pages)):
            with st.spinner("다음 페이지를 불러오는 중..."):
                st.session_state.page_no += 1
                st.session_state.patent_list, _ = search_patents(KIPRIS_API_KEY, st.session_state.keyword, st.session_state.page_no)
            st.rerun()

        for i, patent in enumerate(st.session_state.patent_list):
            with st.expander(f"**{i+1}. {patent['title']}**"):
                st.markdown(f"**- 출원인:** {patent['applicant']}")
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