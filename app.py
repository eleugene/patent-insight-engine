# Streamlit 앱의 메인 실행 파일입니다.
# 전체 UI를 구성하고 사용자 입력을 받아 다른 모듈의 기능을 호출하는 역할을 합니다.

# --- 1. 기본 라이브러리 임포트 ---
import streamlit as st  # Streamlit 라이브러리 (UI 생성)
import os               # 운영체제와 상호작용 (파일 경로 등)
from dotenv import load_dotenv # .env 파일에서 환경 변수(API 키)를 로드
import math             # 수학 계산 (페이지 수 계산 등)
import time             # 시간 관련 기능 (일시 정지 등)

# --- 2. 직접 만든 기능(모듈) 임포트 ---
# src 폴더에 있는 각 핸들러 파일에서 필요한 함수들을 가져옵니다.
from src.kipris_handler import search_patents, search_all_patents, get_patent_details
from src.llm_handler import summarize_text_with_gemini, analyze_patent_data_with_gemini, analyze_detailed_data_with_gemini

# --- 3. 환경 변수 설정 ---
# .env 파일에 저장된 API 키를 로드하여 변수에 할당합니다.
load_dotenv()
KIPris_API_KEY = os.getenv("KIPRIS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 4. Streamlit 페이지 기본 설정 ---
# 페이지 레이아웃을 'wide'로 설정하여 넓게 표시합니다.
st.set_page_config(layout="wide")
# 웹 앱의 제목을 설정합니다.
st.title(" patent Insight Engine")

# --- 5. 세션 상태(Session State) 초기화 ---
# Streamlit 앱이 새로고침 되어도 유지되어야 할 변수들을 초기화합니다.
# 'st.session_state'는 앱의 메모리 역할을 합니다.
if 'patent_list' not in st.session_state:
    st.session_state.patent_list = []  # 현재 페이지의 특허 목록
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0    # 전체 검색된 특허 수
if 'page_no' not in st.session_state:
    st.session_state.page_no = 1      # 현재 보고 있는 페이지 번호
if 'keyword' not in st.session_state:
    st.session_state.keyword = ""       # 사용자가 입력한 검색어

# --- 6. UI 섹션 1: 특허 키워드 검색 ---
st.subheader("1. 특허 키워드 검색")
# 사용자로부터 텍스트를 입력받는 입력창을 생성합니다.
keyword_input = st.text_input("분석하고 싶은 특허 키워드를 입력하세요:", key="keyword_input", placeholder="예: 마이크로의료로봇")

# '특허 검색' 버튼을 생성하고, 버튼이 클릭되었을 때 아래의 로직을 실행합니다.
if st.button("특허 검색"):
    # session_state에 현재 검색어와 페이지 번호를 저장/초기화합니다.
    st.session_state.keyword = keyword_input
    st.session_state.page_no = 1
    
    # 사용자에게 작업 진행 상태를 알려주는 메시지 창을 생성합니다.
    status_message = st.empty()
    status_message.info("KIPRIS API를 호출하여 특허 목록을 검색합니다...")
    
    # kipris_handler의 search_patents 함수를 호출하여 API로부터 데이터를 받아옵니다.
    patent_list, total_count = search_patents(KIPRIS_API_KEY, st.session_state.keyword)
    
    # API 호출 결과에 따라 다른 메시지를 보여주고, session_state를 업데이트합니다.
    if patent_list:
        status_message.success(f"API 호출 성공! 총 {total_count}건의 특허를 찾았습니다.")
        st.session_state.patent_list = patent_list
        st.session_state.total_count = total_count
    else:
        status_message.error("API 호출에 실패했거나 검색 결과가 없습니다. 키워드를 확인해주세요.")
        st.session_state.patent_list = []
        st.session_state.total_count = 0
    
    # 상태 메시지를 2초간 보여준 뒤 사라지게 합니다.
    time.sleep(2)
    status_message.empty()

# --- 7. UI 섹션 2: AI 기반 심층 분석 ---
# session_state에 검색어가 저장되어 있을 때만 (즉, 검색이 한 번이라도 실행되었을 때만) 이 섹션을 보여줍니다.
if st.session_state.keyword:
    st.divider() # 시각적인 구분선
    st.subheader("2. AI 기반 특허 심층 분석")

    # '빠른 분석'과 '정밀 분석' 중 하나를 선택할 수 있는 라디오 버튼을 생성합니다.
    analysis_level = st.radio(
        "분석 수준을 선택하세요:",
        ('빠른 분석 (초록 기반)', '정밀 분석 (다중 필드 검색, 시간 소요)'),
        horizontal=True,
    )
    # 사용자가 자유롭게 분석 요청을 입력할 수 있는 여러 줄 텍스트 입력창을 생성합니다.
    analysis_query = st.text_area("검색된 특허 전체에 대해 분석하고 싶은 내용을 자유롭게 입력하세요:", height=150,
                                  placeholder="예시)\n- 최근 10년간 가장 많이 출원한 출원인 순위와 건수를 알려줘\n- '서울대학교'가 출원한 특허들의 핵심 기술 동향을 요약해줘")

    # 'AI 분석 실행' 버튼을 생성하고, 클릭되었을 때 아래 로직을 실행합니다.
    if st.button("AI 분석 실행"):
        # 라디오 버튼 선택에 따라 다른 분석 로직을 실행합니다.
        if analysis_level == '빠른 분석 (초록 기반)':
            # '수집 중'이라는 스피너(로딩 애니메이션)를 표시합니다.
            with st.spinner(f"전체 특허 약 {st.session_state.total_count}건을 수집 중입니다..."):
                all_patents = search_all_patents(api_key=KIPRIS_API_KEY, keyword=st.session_state.keyword, search_fields=["astrtCont"])
            
            if all_patents:
                st.info(f"총 {len(all_patents)}건의 특허를 기반으로 분석을 시작합니다.")
                with st.spinner("Gemini AI가 데이터를 심층 분석 중입니다..."):
                    # llm_handler의 분석 함수를 호출합니다.
                    analysis_result = analyze_patent_data_with_gemini(GEMINI_API_KEY, all_patents, analysis_query)
                st.subheader("AI 심층 분석 결과 (빠른 분석)")
                st.markdown(analysis_result) # 결과를 마크다운 형식으로 예쁘게 표시
        
        elif analysis_level == '정밀 분석 (다중 필드 검색, 시간 소요)':
            st.info(f"정밀 분석을 시작합니다. 전체 특허 약 {st.session_state.total_count}건을 수집하고 상세 정보를 조회하므로 시간이 몇 분 이상 소요될 수 있습니다.")
            
            # 넓은 범위로 전체 특허를 수집합니다.
            with st.spinner(f"전체 특허(최대 100건)를 더 넓은 범위로 수집 중입니다..."):
                all_patents = search_all_patents(api_key=KIPRIS_API_KEY, keyword=st.session_state.keyword, search_fields="inventionTitle|astrtCont|claim", max_results=100)
            
            if all_patents:
                # 진행률 표시줄(Progress Bar)을 생성합니다.
                progress_bar = st.progress(0, text="각 특허의 상세 정보를 수집 중입니다...")
                # 각 특허의 상세 정보를 추가로 조회합니다.
                for i, patent in enumerate(all_patents):
                    details = get_patent_details(KIPRIS_API_KEY, patent['app_num'])
                    if details:
                        patent.update(details) # 기존 patent 정보에 상세 정보를 추가
                    time.sleep(0.3) # API 서버에 부담을 주지 않기 위해 잠시 대기
                    # 진행률 표시줄을 업데이트합니다.
                    progress_bar.progress((i + 1) / len(all_patents), text=f"상세 정보 수집 중... ({i+1}/{len(all_patents)})")
                
                # 상세 정보가 포함된 전체 데이터로 Gemini 분석을 요청합니다.
                with st.spinner("Gemini AI가 상세 데이터를 심층 분석 중입니다..."):
                    analysis_result = analyze_detailed_data_with_gemini(GEMINI_API_KEY, all_patents, analysis_query)
                st.subheader("AI 심층 분석 결과 (정밀 분석)")
                st.markdown(analysis_result)

    # --- 8. UI 섹션 3: 검색 결과 목록 표시 ---
    # session_state에 특허 목록이 있을 경우에만 이 섹션을 보여줍니다.
    if st.session_state.patent_list:
        st.divider()
        st.subheader("검색 결과 목록")
        
        # 전체 페이지 수를 계산하고 현재 페이지를 표시합니다.
        total_pages = math.ceil(st.session_state.total_count / 10)
        st.write(f"페이지 {st.session_state.page_no} / {total_pages}")
        
        # '이전', '다음' 버튼을 위한 UI 컬럼을 생성합니다.
        col1, col2 = st.columns(2)
        if col1.button("이전 페이지", disabled=(st.session_state.page_no <= 1)):
            with st.spinner("이전 페이지를 불러오는 중..."):
                st.session_state.page_no -= 1
                # 이전 페이지 데이터를 API로 다시 요청합니다.
                st.session_state.patent_list, _ = search_patents(KIPRIS_API_KEY, st.session_state.keyword, st.session_state.page_no)
            st.rerun() # 화면을 새로고침하여 변경된 내용을 즉시 반영

        if col2.button("다음 페이지", disabled=(st.session_state.page_no >= total_pages)):
            with st.spinner("다음 페이지를 불러오는 중..."):
                st.session_state.page_no += 1
                # 다음 페이지 데이터를 API로 다시 요청합니다.
                st.session_state.patent_list, _ = search_patents(KIPRIS_API_KEY, st.session_state.keyword, st.session_state.page_no)
            st.rerun()

        # 검색된 특허 목록을 하나씩 순회하며 화면에 표시합니다.
        for i, patent in enumerate(st.session_state.patent_list):
            # st.expander는 클릭하면 내용이 펼쳐지는 UI 요소입니다.
            with st.expander(f"**{i+1}. {patent['title']}**"):
                # st.markdown을 사용해 굵은 글씨, 링크 등 서식을 적용합니다.
                st.markdown(f"**- 출원인:** {patent['applicant']}")
                st.markdown(f"**- 출원번호/일자:** {patent['app_num']} / {patent['app_date']}")
                st.markdown(f"**- 등록상태:** {patent['reg_status']}")
                st.markdown(f"**- 등록번호/일자:** {patent['reg_num']} / {patent['reg_date']}")
                st.markdown(f"**- KIPRIS 바로가기:** [상세 정보 보기]({patent['link']})")
                
                st.subheader("초록")
                st.write(patent['abstract'])
                
                # 각 특허별로 고유한 키(key)를 가진 요약 버튼을 생성합니다.
                if st.button(f"'{patent['title'][:30]}...' 요약하기", key=f"summary_btn_{i}"):
                    with st.spinner("Gemini가 특허를 분석 및 요약 중입니다..."):
                        summary = summarize_text_with_gemini(GEMINI_API_KEY, patent['abstract'])
                    st.subheader("Gemini 요약 결과")
                    st.info(summary)
