"""
Streamlit 앱의 메인 실행 파일입니다.
전체 UI를 구성하고 사용자 입력을 받아 다른 모듈의 기능을 호출하는 역할을 합니다.
"""

# --- 1. 기본 라이브러리 임포트 ---
import streamlit as st
import os
from dotenv import load_dotenv
import math
import time
import json
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import requests
from io import BytesIO

# --- 2. 직접 만든 기능(모듈) 임포트 ---
from src.kipris_handler import search_all_patents, get_patent_details
from src.llm_handler import summarize_text_with_gemini, analyze_patent_data_with_gemini, analyze_detailed_data_with_gemini

# --- 3. 환경 변수 설정 및 상수 정의 ---
load_dotenv()
KIPRIS_API_KEY = os.getenv("KIPRIS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ROWS_PER_PAGE = 10  # 페이지당 표시할 특허 개수를 10으로 정의

# --- API 키 유효성 검사 ---
if not KIPRIS_API_KEY or not GEMINI_API_KEY:
    st.error("`.env` 파일에 KIPRIS_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다. 파일을 확인해주세요.")
    st.stop()

# --- 4. Streamlit 페이지 기본 설정 ---
st.set_page_config(layout="wide")
st.title(" KIPRIS & GEMINI API 기반 특허분석엔진")

# --- 5. 페이지 상태(session_state) 초기화 ---
if 'all_patents' not in st.session_state:
    st.session_state.all_patents = [] # 전체 특허 목록을 저장할 공간
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0
if 'page_no' not in st.session_state:
    st.session_state.page_no = 1
if 'keyword' not in st.session_state:
    st.session_state.keyword = ""
if 'search_type' not in st.session_state:
    st.session_state.search_type = "키워드 (초록)"
if 'selected_applicants' not in st.session_state:
    st.session_state.selected_applicants = []

# --- 페이지 변경을 처리하는 함수 ---
def handle_page_change(page_number):
    st.session_state.page_no = page_number

# --- 6. UI: 특허 키워드 검색 ---
st.subheader("1. 특허 검색")

# 검색 기준 선택 (키워드 vs 출원인)
search_type = st.radio(
    "검색 기준을 선택하세요:",
    ("키워드 (초록)", "출원인"),
    horizontal=True,
    key='search_type_radio'
)
st.session_state.search_type = search_type

keyword_input = st.text_input("검색어를 입력하세요:", key="keyword_input", placeholder="예: 로봇 또는 삼성전자")

if st.button("특허 검색"):
    st.session_state.keyword = keyword_input
    st.session_state.page_no = 1
    st.session_state.selected_applicants = []
    
    # 선택된 검색 기준에 따라 API가 이해하는 필드 이름으로 변환
    search_field_map = {
        "키워드 (초록)": ["astrtCont"],
        "출원인": ["applicantName"]
    }
    search_fields_to_use = search_field_map[st.session_state.search_type]
    
    status_message = st.empty()
    with st.spinner(f"KIPRIS에서 '{st.session_state.search_type}' 기준으로 전체 특허 목록을 수집 중입니다..."):
        all_patents_list = search_all_patents(KIPRIS_API_KEY, st.session_state.keyword, search_fields=search_fields_to_use)

    if all_patents_list:
        st.session_state.all_patents = all_patents_list
        st.session_state.total_count = len(all_patents_list)
        status_message.success(f"API 호출 성공! 총 {st.session_state.total_count}건의 특허를 찾았습니다.")
        time.sleep(1)
        status_message.empty()
    else:
        status_message.error("API 호출에 실패했거나 검색 결과가 없습니다.")
        st.session_state.all_patents = []
        st.session_state.total_count = 0

# --- 7. UI: AI 분석 및 필터 ---
if st.session_state.all_patents:
    st.divider()
    st.subheader("필터 및 AI 심층 분석")
    
    # --- 출원인 필터 기능 ---
    applicant_set = set()
    for p in st.session_state.all_patents:
        applicants = [name.strip() for name in p['applicant'].split('|')]
        applicant_set.update(applicants)
    all_applicants = sorted(list(applicant_set))
    
    selected_applicants = st.multiselect(
        "특정 출원인의 특허만 보려면 선택하세요 (기본: 전체):",
        options=all_applicants,
        default=st.session_state.selected_applicants
    )
    st.session_state.selected_applicants = selected_applicants

    # 필터링된 특허 리스트 생성
    if selected_applicants:
        filtered_patents = []
        for p in st.session_state.all_patents:
            patent_applicants = [name.strip() for name in p['applicant'].split('|')]
            if any(applicant in selected_applicants for applicant in patent_applicants):
                filtered_patents.append(p)
    else:
        filtered_patents = st.session_state.all_patents
    
    # AI 분석
    analysis_level = st.radio(
        "분석 수준을 선택하세요:",
        ('빠른 분석 (기본 정보)', '정밀 분석 (상세 정보 포함, 시간 소요)'),
        horizontal=True,
    )
    analysis_query = st.text_area("필터링된 특허에 대해 분석하고 싶은 내용을 자유롭게 입력하세요:", height=150,
                                  placeholder="예시)\n- 필터링된 특허들의 최근 10년간 기술 동향을 요약해줘\n- 주요 기술(IPC) 분야는 무엇인지 분석해줘")
    
    if st.button("AI 분석 실행"):
        analysis_status = st.empty()
        analysis_function = None
        # AI 분석은 현재 필터링된 데이터를 기반으로 수행
        patents_for_analysis = filtered_patents
        
        if not patents_for_analysis:
            st.warning("분석할 특허가 없습니다. 필터 조건을 확인해주세요.")
        else:
            if analysis_level == '빠른 분석 (기본 정보)':
                analysis_function = analyze_patent_data_with_gemini
                analysis_status.info(f"필터링된 특허 {len(patents_for_analysis)}건을 기반으로 분석을 시작합니다...")
            
            elif analysis_level == '정밀 분석 (상세 정보 포함, 시간 소요)':
                analysis_function = analyze_detailed_data_with_gemini
                patents_to_get_details = patents_for_analysis[:100]
                analysis_status.info(f"필터링된 {len(patents_for_analysis)}건 중, 최신 {len(patents_to_get_details)}건의 상세 정보를 조회합니다...")
                
                progress_bar = st.progress(0, text=f"상세 정보 수집 중... (0/{len(patents_to_get_details)})")
                for i, patent in enumerate(patents_to_get_details):
                    details = get_patent_details(KIPRIS_API_KEY, patent['app_num'])
                    if details:
                        patent.update(details)
                    time.sleep(0.4)
                    progress_bar.progress((i + 1) / len(patents_to_get_details), text=f"상세 정보 수집 중... ({i+1}/{len(patents_to_get_details)})")
                progress_bar.empty()

            if patents_for_analysis and analysis_function:
                analysis_status.info(f"총 {len(patents_for_analysis)}건의 특허를 기반으로 Gemini AI 분석을 시작합니다...")
                analysis_result_str = analysis_function(GEMINI_API_KEY, patents_for_analysis, analysis_query)
                analysis_status.empty()
                
                try:
                    analysis_data = json.loads(analysis_result_str)
                    st.subheader(f"AI 심층 분석 결과 ({analysis_level.split(' ')[0]})")

                    st.markdown("#### 📄 분석 요약")
                    st.markdown(analysis_data.get("analysis_summary", "분석 요약을 생성하지 못했습니다."))

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### 📊 주요 출원인 분석")
                        top_applicants = analysis_data.get("top_applicants")
                        if top_applicants:
                            df = pd.DataFrame(top_applicants).set_index("applicant")
                            st.bar_chart(df)
                        else:
                            st.warning("출원인 분석 데이터를 생성하지 못했습니다.")
                    with col2:
                        st.markdown("#### ☁️ 핵심 기술 키워드")
                        keywords = analysis_data.get("keywords")
                        if keywords and isinstance(keywords, list):
                            text = " ".join(keywords)
                            font_path = "fonts/NanumGothic-Regular.ttf"
                            if not os.path.exists(font_path):
                                st.error(f"폰트 파일이 없습니다: '{font_path}' 경로를 확인해주세요.")
                            else:
                                wordcloud = WordCloud(font_path=font_path, width=800, height=400, background_color="white").generate(text)
                                fig, ax = plt.subplots()
                                ax.imshow(wordcloud, interpolation='bilinear')
                                ax.axis("off")
                                st.pyplot(fig)
                        else:
                            st.warning("키워드 데이터를 생성하지 못했습니다.")

                except (json.JSONDecodeError, KeyError):
                    st.error("AI가 유효한 분석 결과를 생성하지 못했습니다. 원본 응답을 확인하세요:")
                    st.code(analysis_result_str)
                except Exception as e:
                    st.error(f"결과를 표시하는 중 오류가 발생했습니다: {e}")
            else:
                analysis_status.error("분석할 특허 데이터를 수집하지 못했습니다.")
    
# --- 8. UI: 검색 결과 목록 및 페이지네이션 ---
if 'filtered_patents' in locals() and filtered_patents:
    st.divider()
    st.subheader("검색 결과 목록")
    
    total_filtered_count = len(filtered_patents)
    total_pages = math.ceil(total_filtered_count / ROWS_PER_PAGE)
    current_page = st.session_state.page_no

    if current_page > total_pages:
        st.session_state.page_no = 1
        current_page = 1
    
    st.write(f"총 {total_filtered_count}건 | 페이지 {current_page} / {total_pages}")
    
    # --- 페이지네이션 UI ---
    cols = st.columns(11) 
    if cols[0].button("◀ 이전", disabled=(current_page <= 1), use_container_width=True):
        handle_page_change(current_page - 1)
        st.rerun()

    page_start = max(1, current_page - 5)
    page_end = min(total_pages, page_start + 9)
    if total_pages > 10 and current_page > total_pages - 5:
        page_start = total_pages - 9
        page_end = total_pages
    
    page_range = list(range(page_start, page_end + 1))
    button_cols_indices = list(range(1, len(page_range) + 1))

    for i, page_num in enumerate(page_range):
        if cols[button_cols_indices[i]].button(f"{page_num}", type=("secondary" if page_num != current_page else "primary"), use_container_width=True):
            handle_page_change(page_num)
            st.rerun()

    if cols[10].button("다음 ▶", disabled=(current_page >= total_pages), use_container_width=True):
        handle_page_change(current_page + 1)
        st.rerun()

    # --- 특허 목록 표시 ---
    start_index = (current_page - 1) * ROWS_PER_PAGE
    end_index = start_index + ROWS_PER_PAGE
    patents_to_display = filtered_patents[start_index:end_index]

    for i, patent in enumerate(patents_to_display):
        with st.expander(f"**{start_index + i + 1}. {patent['title']}**"):
            details_line_1 = (
                f"**출원인:** {patent.get('applicant', '정보 없음')} | "
                f"**발명자:** {patent.get('inventor', '정보 없음')}"
            )
            st.markdown(details_line_1)
            details_line_2 = (
                f"**출원번호:** {patent.get('app_num', '정보 없음')} ({patent.get('app_date', '정보 없음')}) | "
                f"**상태:** {patent.get('reg_status', '정보 없음')}"
            )
            st.markdown(details_line_2)
            st.markdown(f"[KIPRIS에서 상세 정보 보기]({patent.get('link', '#')})")
            st.markdown("---")
            
            st.write(patent['abstract'])
            
            if st.button(f"'{patent['title'][:30]}...' 요약하기", key=f"summary_btn_{i}"):
                with st.spinner("Gemini가 특허를 분석 및 요약 중입니다..."):
                    summary = summarize_text_with_gemini(GEMINI_API_KEY, patent['abstract'])
                st.subheader("Gemini 요약 결과")
                st.info(summary)