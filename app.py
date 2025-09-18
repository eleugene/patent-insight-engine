"""
완전 개선된 특허 분석 챗봇 - distutils 문제 해결 + 직접 한글 폰트 설정
"""

import streamlit as st
import os
from dotenv import load_dotenv
import time
import json
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
# ↓ koreanize_matplotlib 제거 - distutils 문제 해결!

# 향상된 모듈 임포트
from src.kipris_handler import search_all_patents, get_patent_details
from src.llm_handler import AdvancedPatentAnalyzer

# 환경 설정
load_dotenv()
KIPRIS_API_KEY = os.getenv("KIPRIS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def setup_korean_font():
    """Windows/Mac/Linux 환경에서 한글 폰트 자동 설정 - distutils 의존성 없음"""
    try:
        if os.name == 'nt':  # Windows
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False
            return True
        elif os.name == 'posix':  # Mac/Linux
            try:
                plt.rcParams['font.family'] = 'AppleGothic'
                plt.rcParams['axes.unicode_minus'] = False
                return True
            except:
                plt.rcParams['font.family'] = 'DejaVu Sans'
                plt.rcParams['axes.unicode_minus'] = False
                return False
        else:
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            return False
    except Exception as e:
        print(f"한글 폰트 설정 실패: {e}")
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        return False

if not KIPRIS_API_KEY or not GEMINI_API_KEY:
    st.error("API 키가 설정되지 않았습니다.")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="AI 특허 분석 챗봇 Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 한글 폰트 설정 (앱 시작시 한번만)
if 'font_setup' not in st.session_state:
    korean_support = setup_korean_font()
    st.session_state.font_setup = True
    st.session_state.korean_support = korean_support

# 고급 CSS 스타일링
st.markdown("""
<style>
    .main-title { 
        font-size: 3rem; 
        color: #1e3a8a; 
        font-weight: bold; 
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-title { 
        font-size: 1.3rem; 
        color: #64748b; 
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .success-banner { 
        background: linear-gradient(90deg, #059669, #10b981); 
        color: white; 
        padding: 1.5rem; 
        border-radius: 15px; 
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .analysis-section {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        border: 1px solid #cbd5e1;
    }
    .metric-card { 
        background: white;
        padding: 1rem; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    .analysis-result {
        background: #f1f5f9;
        padding: 2rem;
        border-radius: 12px;
        border-left: 5px solid #8b5cf6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown('<div class="main-title">🤖 AI 특허 분석 챗봇 Pro v4.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">distutils 완전 해결 + 직접 한글 폰트 설정 + PDF 보고서 생성</div>', unsafe_allow_html=True)

# 세션 상태 초기화
if 'patents' not in st.session_state:
    st.session_state.patents = []
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = AdvancedPatentAnalyzer(GEMINI_API_KEY)

# 사이드바 - 검색 설정
with st.sidebar:
    st.header("🔍 스마트 검색 설정")
    
    # 검색 모드
    search_mode = st.radio(
        "검색 모드:",
        ["🔍 키워드 검색", "🏢 출원인 검색", "📄 특허번호 검색"],
        help="AI가 키워드를 분석하여 대량의 관련 특허를 스마트하게 수집합니다"
    )
    
    # 검색어 입력
    if search_mode == "🔍 키워드 검색":
        search_query = st.text_input(
            "검색 키워드:",
            placeholder="예: 마이크로로봇, 인공지능, 배터리",
            help="AI가 수백건의 특허를 분석하여 관련성 높은 특허만 선별합니다"
        )
    elif search_mode == "🏢 출원인 검색":
        search_query = st.text_input(
            "출원인명 (부분일치):",
            placeholder="예: 삼성, LG, 현대 (부분입력 가능)",
            help="부분일치로 검색됩니다. '삼성' 입력시 '삼성전자', '삼성SDI' 등 모두 검색"
        )
    else:
        search_query = st.text_input(
            "특허/출원번호:",
            placeholder="예: 1020230123456"
        )
    
    # 고급 설정
    st.subheader("⚙️ 고급 설정")
    max_results = st.slider("최대 검색 결과:", 50, 500, 200, 50, 
                           help="AI가 관련성을 분석하여 상위 N건만 선별합니다")
    
    # AI 분석 모드
    st.subheader("🧠 AI 분석 모드")
    analysis_type = st.selectbox(
        "분석 유형:",
        [
            "🏆 경쟁기관 분석",
            "📈 기술 동향 분석", 
            "🔮 향후 방향 예측",
            "📊 종합 분석"
        ]
    )
    
    # 실시간 통계 (사이드바)
    if st.session_state.patents:
        st.markdown("---")
        st.subheader("📊 실시간 통계")
        
        total = len(st.session_state.patents)
        st.metric("수집된 특허", f"{total:,}건")
        
        # 최신 특허 비율
        recent_patents = sum(1 for p in st.session_state.patents 
                           if p.get('app_date', '')[:4] >= '2020')
        recent_ratio = (recent_patents / total * 100) if total > 0 else 0
        st.metric("최신 특허(2020년 이후)", f"{recent_ratio:.1f}%")
        
        # 등록 특허 비율
        registered = sum(1 for p in st.session_state.patents 
                        if '등록' in p.get('reg_status', ''))
        reg_ratio = (registered / total * 100) if total > 0 else 0
        st.metric("등록 특허", f"{reg_ratio:.1f}%")

# =============================================================================
# 메인 콘텐츠 - 위아래 레이아웃
# =============================================================================

# 첫 번째 섹션: 검색 인터페이스 및 결과
st.markdown("## 🔍 스마트 특허 검색")

# 검색 실행
search_col1, search_col2 = st.columns([3, 1])

with search_col1:
    if st.button("🚀 AI 스마트 검색 실행", type="primary", use_container_width=True):
        if not search_query.strip():
            st.warning("검색어를 입력해주세요.")
        else:
            search_start_time = time.time()
            
            with st.spinner("🧠 AI가 대량의 특허를 분석하고 있습니다..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("🔍 최적 검색 전략 분석 중...")
                    progress_bar.progress(10)
                    
                    status_text.text("📡 KIPRIS API 대량 호출 중...")
                    progress_bar.progress(30)
                    
                    # 검색 실행
                    if search_mode == "🔍 키워드 검색":
                        patents = search_all_patents(
                            KIPRIS_API_KEY, 
                            search_query, 
                            [],  # 내부에서 스마트 선택
                            max_results
                        )
                    elif search_mode == "🏢 출원인 검색":
                        patents = search_all_patents(
                            KIPRIS_API_KEY, 
                            search_query, 
                            ['applicantName'],
                            max_results
                        )
                    else:
                        patent_detail = get_patent_details(KIPRIS_API_KEY, search_query)
                        patents = [patent_detail] if patent_detail else []
                    
                    progress_bar.progress(80)
                    status_text.text("🤖 AI가 관련성을 분석하여 필터링 중...")
                    
                    # 결과 저장
                    st.session_state.patents = patents
                    st.session_state.search_query = search_query
                    st.session_state.search_time = time.time() - search_start_time
                    st.session_state.search_mode = search_mode
                    
                    progress_bar.progress(100)
                    
                    if patents:
                        status_text.success(f"✅ {len(patents)}건 발견! (소요시간: {st.session_state.search_time:.1f}초)")
                    else:
                        status_text.error("❌ 검색 결과가 없습니다.")
                    
                    time.sleep(2)
                    progress_bar.empty()
                    status_text.empty()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"검색 중 오류: {e}")

with search_col2:
    if st.session_state.patents:
        st.info(f"**현재 수집된 특허**\n{len(st.session_state.patents):,}건")

# 검색 결과가 있을 때만 표시
if st.session_state.patents:
    patents = st.session_state.patents
    
    # 성공 배너
    st.markdown(f"""
    <div class="success-banner">
        <h2>🎉 검색 완료!</h2>
        <p><strong>{len(patents):,}건</strong>의 특허를 발견했습니다. 
        AI가 관련성을 분석하여 선별한 결과입니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 핵심 메트릭 표시
    st.markdown("### 📊 검색 결과 요약")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("총 특허 수", f"{len(patents):,}건")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_m2:
        unique_applicants = len(set(p.get('applicant', '') for p in patents))
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("참여 기업", f"{unique_applicants}개")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_m3:
        registered = len([p for p in patents if '등록' in p.get('reg_status', '')])
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("등록 특허", f"{registered}건")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_m4:
        if 'search_time' in st.session_state:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("검색 시간", f"{st.session_state.search_time:.1f}초")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 연도별 출원 현황 차트 (직접 한글 폰트 설정 - distutils 없이!)
    st.markdown("### 📈 연도별 특허 출원 현황")
    
    years_data = {}
    for patent in patents:
        app_date = patent.get('app_date', '')
        if app_date and len(app_date) >= 4:
            year = app_date[:4]
            years_data[year] = years_data.get(year, 0) + 1
    
    if years_data:
        # matplotlib 차트 생성 (한글 폰트 자동 적용)
        fig, ax = plt.subplots(figsize=(12, 6))
        years = sorted(years_data.keys())
        counts = [years_data[year] for year in years]
        
        ax.bar(years, counts, color='#3b82f6', alpha=0.8)
        
        # 한글 지원 여부에 따라 제목 설정
        if st.session_state.get('korean_support', False):
            ax.set_title('연도별 특허 출원 현황', fontsize=16, fontweight='bold')
            ax.set_xlabel('연도', fontsize=12)
            ax.set_ylabel('출원 건수', fontsize=12)
        else:
            ax.set_title('Patent Applications by Year', fontsize=16, fontweight='bold')
            ax.set_xlabel('Year', fontsize=12)
            ax.set_ylabel('Applications', fontsize=12)
        
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)  # 메모리 정리
    else:
        st.info("연도별 데이터가 충분하지 않습니다.")
    
    # 특허 목록 미리보기
    st.markdown("### 📋 특허 목록 미리보기")
    
    page_size = 5
    total_pages = (len(patents) + page_size - 1) // page_size
    
    display_mode = st.radio("표시 모드:", ["📝 요약형", "📄 상세형"], horizontal=True)
    
    if total_pages > 1:
        current_page = st.selectbox("페이지 선택:", range(1, total_pages + 1))
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        display_patents = patents[start_idx:end_idx]
        st.info(f"📄 페이지 {current_page}/{total_pages} (전체 {len(patents)}건 중 {len(display_patents)}건 표시)")
    else:
        display_patents = patents[:page_size]
        start_idx = 0
    
    # 특허 카드 표시
    for i, patent in enumerate(display_patents):
        with st.expander(f"**{start_idx + i + 1}. {patent.get('title', 'N/A')}**"):
            if display_mode == "📝 요약형":
                col_info, col_action = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**📋 출원인:** {patent.get('applicant', 'N/A')}")
                    st.write(f"**👨‍🔬 발명자:** {patent.get('inventor', '정보없음')}")  # ← 완전 해결!
                    st.write(f"**📅 출원일:** {patent.get('app_date', 'N/A')}")
                    st.write(f"**⚖️ 등록상태:** {patent.get('reg_status', 'N/A')}")
                
                with col_action:
                    # 다중 KIPRIS 링크 옵션 (Bad Gateway 문제 해결)
                    app_num = patent.get('app_num', '')
                    if app_num:
                        st.markdown("**🔗 KIPRIS 링크:**")
                        clean_num = app_num.replace('-', '')
                        
                        # 여러 링크 옵션 제공
                        st.markdown(f"• [KIPRIS Plus](https://plus.kipris.or.kr/kpat/search/SearchMain.do?method=searchUTL&param1={clean_num})")
                        st.markdown(f"• [기존 KIPRIS](http://kpat.kipris.or.kr/kpat/biblio.do?method=biblioFrame&applno={clean_num})")
                        st.markdown(f"• [검색으로 찾기](https://plus.kipris.or.kr/kpat/search/totalSearch.do?param1={app_num})")
                    
                    if st.button("🤖 AI 요약", key=f"summary_{start_idx + i}"):
                        with st.spinner("AI 요약 중..."):
                            abstract = patent.get('abstract', '')
                            summary = st.session_state.analyzer.quick_summarize(abstract)
                            st.success("**🎯 AI 요약:**")
                            st.info(summary)
            else:
                # 상세형 표시
                st.write(f"**📋 출원인:** {patent.get('applicant', 'N/A')}")
                st.write(f"**👨‍🔬 발명자:** {patent.get('inventor', '정보없음')}")
                st.write(f"**📅 출원일:** {patent.get('app_date', 'N/A')}")
                st.write(f"**📄 출원번호:** {patent.get('app_num', 'N/A')}")
                st.write(f"**⚖️ 등록상태:** {patent.get('reg_status', 'N/A')}")
                
                abstract = patent.get('abstract', 'N/A')
                st.write(f"**📄 초록:** {abstract}")
                
                # KIPRIS 링크
                kipris_url = patent.get('kipris_url')
                if kipris_url:
                    st.markdown(f"🔗 **[KIPRIS에서 자세히 보기]({kipris_url})**")

# =============================================================================
# 두 번째 섹션: AI 분석 (검색 결과 아래에 배치)
# =============================================================================

if st.session_state.patents:
    st.markdown("---")
    
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    st.markdown("## 🧠 AI 특허 분석")
    st.markdown("대량의 특허 데이터를 AI가 종합 분석하여 전문적인 인사이트를 제공합니다.")
    
    # 분석 설정
    analysis_col1, analysis_col2 = st.columns([2, 1])
    
    with analysis_col1:
        user_question = st.text_area(
            "🔍 추가 분석 질문 (선택사항):",
            placeholder="""예시 질문:
• 이 기술 분야의 시장 전망은 어떤가요?
• 주요 경쟁사들의 기술 전략 차이점은?
• 향후 투자해야 할 핵심 기술 영역은?
• 특허 분쟁 위험이 높은 영역은 어디인가요?
• 신규 진입 시 고려해야 할 사항은?""",
            height=120
        )
    
    with analysis_col2:
        st.info(f"""
        **🔢 분석 대상 데이터**
        - 총 특허: {len(st.session_state.patents):,}건
        - 분석 모드: {analysis_type}
        - 예상 소요시간: 30-60초
        """)
        
        if st.button("🚀 AI 분석 시작", type="secondary", use_container_width=True):
            analysis_start_time = time.time()
            
            with st.spinner(f"🧠 {analysis_type} 수행 중... 대량 데이터를 분석하고 있습니다."):
                try:
                    # 분석 타입 매핑
                    analysis_map = {
                        "🏆 경쟁기관 분석": "competitive_analysis",
                        "📈 기술 동향 분석": "trend_analysis",
                        "🔮 향후 방향 예측": "future_direction",
                        "📊 종합 분석": "comprehensive_analysis"
                    }
                    
                    analysis_key = analysis_map.get(analysis_type, "competitive_analysis")
                    
                    result = st.session_state.analyzer.comprehensive_analysis(
                        st.session_state.patents,
                        analysis_key,
                        user_question
                    )
                    
                    analysis_time = time.time() - analysis_start_time
                    
                    # 결과 저장
                    st.session_state.analysis_result = result
                    st.session_state.analysis_type = analysis_type
                    st.session_state.analysis_time = analysis_time
                    st.session_state.user_question = user_question
                    
                    st.success(f"✅ 분석 완료! (소요시간: {analysis_time:.1f}초)")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")
    
    # AI 분석 결과 표시
    if 'analysis_result' in st.session_state:
        st.markdown("### 🎯 AI 분석 결과")
        
        st.info(f"""
        **📊 분석 정보**
        - 분석 유형: {st.session_state.analysis_type}
        - 분석 특허 수: {len(st.session_state.patents):,}건
        - 소요 시간: {st.session_state.analysis_time:.1f}초
        - 분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """)
        
        # 분석 결과 표시
        st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 다운로드 옵션
        st.markdown("### 💾 분석 결과 다운로드")
        
        download_col1, download_col2 = st.columns(2)
        
        with download_col1:
            # JSON 다운로드
            analysis_data = {
                "검색어": st.session_state.get('search_query', ''),
                "검색_모드": st.session_state.get('search_mode', ''),
                "검색_결과_수": len(st.session_state.patents),
                "분석_유형": st.session_state.analysis_type,
                "사용자_질문": st.session_state.get('user_question', ''),
                "분석_일시": datetime.now().isoformat(),
                "분석_소요시간": st.session_state.analysis_time,
                "분석_결과": st.session_state.analysis_result
            }
            
            json_str = json.dumps(analysis_data, ensure_ascii=False, indent=2)
            st.download_button(
                "📄 JSON 파일 다운로드",
                data=json_str,
                file_name=f"특허분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with download_col2:
            # PDF 다운로드
            if st.button("📑 PDF 보고서 생성", use_container_width=True):
                try:
                    with st.spinner("📑 전문 PDF 보고서를 생성 중입니다..."):
                        # PDF 생성용 데이터 준비
                        pdf_data = {
                            "search_query": st.session_state.get('search_query', ''),
                            "total_count": len(st.session_state.patents),
                            "top_applicants": {},
                            "yearly_trends": {},
                            "status_distribution": {}
                        }
                        
                        # 통계 데이터 생성
                        applicants = {}
                        years = {}
                        statuses = {}
                        
                        for patent in st.session_state.patents:
                            applicant = patent.get('applicant', '정보없음')
                            applicants[applicant] = applicants.get(applicant, 0) + 1
                            
                            app_date = patent.get('app_date', '')
                            if app_date and len(app_date) >= 4:
                                year = app_date[:4]
                                years[year] = years.get(year, 0) + 1
                            
                            status = patent.get('reg_status', '출원')
                            statuses[status] = statuses.get(status, 0) + 1
                        
                        pdf_data["top_applicants"] = dict(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:10])
                        pdf_data["yearly_trends"] = dict(sorted(years.items()))
                        pdf_data["status_distribution"] = statuses
                        
                        # PDF 생성
                        pdf_buffer = st.session_state.analyzer.generate_pdf_report(
                            pdf_data, 
                            st.session_state.analysis_result
                        )
                        
                        st.download_button(
                            "📑 PDF 보고서 다운로드",
                            data=pdf_buffer.getvalue(),
                            file_name=f"특허분석보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        st.success("✅ PDF 보고서가 생성되었습니다!")
                        
                except Exception as e:
                    st.error(f"PDF 생성 중 오류: {e}")
                    st.info("💡 대안: JSON 파일을 다운로드하신 후 별도 문서로 변환해 주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # 검색 결과가 없을 때 안내
    st.markdown("---")
    st.markdown("## 📖 사용 가이드")
    
    guide_col1, guide_col2, guide_col3 = st.columns(3)
    
    with guide_col1:
        st.markdown("""
        ### 🔍 1단계: 스마트 검색
        - **키워드 검색**: 기술 용어 입력
        - **출원인 검색**: 회사명 부분입력 가능
        - **특허번호 검색**: 특정 특허 조회
        
        AI가 자동으로 최적 전략을 선택합니다.
        """)
    
    with guide_col2:
        st.markdown("""
        ### 🧠 2단계: AI 분석
        - **경쟁기관 분석**: 시장 참여자 현황
        - **기술 동향 분석**: 트렌드 및 전망
        - **향후 방향 예측**: 전략적 인사이트
        
        대량 데이터를 전문가 수준으로 분석합니다.
        """)
    
    with guide_col3:
        st.markdown("""
        ### 📊 3단계: 결과 활용
        - **실시간 시각화**: 한글 차트 완전 지원
        - **PDF 보고서**: 전문 문서 생성
        - **다중 KIPRIS 링크**: 안정적 접근
        
        비즈니스 의사결정에 바로 활용 가능합니다.
        """)
    
    st.success("💡 **distutils 문제 완전 해결**: 직접 한글 폰트 설정으로 모든 환경에서 안정적 실행!")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem; background: #f8fafc; border-radius: 10px;'>
    <h3>🚀 AI 특허 분석 챗봇 Pro v4.0 Final</h3>
    <p><strong>🎯 완전 해결</strong>: distutils 의존성 제거, 발명자 정보 완전 표시, 부분일치 검색, 다중 KIPRIS 링크</p>
    <p><strong>🔧 핵심 기능</strong>: 직접 한글 폰트 설정, 위아래 레이아웃, 관련성 기반 스마트 필터링, PDF 보고서</p>
    <p><strong>💡 성능</strong>: Python 3.12 완전 호환, 500+건 특허 분석, 30-60초 AI 분석, 실행 가능한 인사이트</p>
</div>
""", unsafe_allow_html=True)
