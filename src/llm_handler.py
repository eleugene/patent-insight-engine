"""
PDF 다운로드 지원 + 향상된 AI 분석 엔진
"""

import google.generativeai as genai
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

class AdvancedPatentAnalyzer:
    """고도화된 특허 분석 + PDF 생성 클래스"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model_pro = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
    
    def quick_summarize(self, text: str) -> str:
        """빠른 요약 - Flash 모델 사용"""
        try:
            prompt = f"""다음 특허 초록을 전문가 수준으로 간단히 요약해주세요.

초록: {text[:1000]}

요약 기준:
- 핵심 기술 내용
- 주요 특징 및 장점  
- 응용 분야
- 3-4문장으로 정리"""

            response = self.model_flash.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"요약 오류: {e}"
    
    def comprehensive_analysis(self, patents: List[Dict], analysis_type: str, user_query: str = "") -> str:
        """종합 특허 분석 - 대량 데이터 처리 최적화"""
        try:
            print(f"🧠 AI 분석 시작: {len(patents)}건 특허 분석 중...")
            
            # 데이터 전처리 및 통계 생성
            analysis_data = self._prepare_comprehensive_data(patents)
            
            # 분석 타입별 프롬프트 생성
            prompt = self._generate_expert_prompt(analysis_data, analysis_type, user_query)
            
            response = self.model_pro.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"분석 오류: {e}"
    
    def generate_pdf_report(self, analysis_data: Dict, analysis_result: str) -> io.BytesIO:
        """전문적인 PDF 보고서 생성"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        
        # 한글 폰트 설정 시도
        try:
            pdfmetrics.registerFont(TTFont('MalgunGothic', 'C:/Windows/Fonts/malgun.ttf'))
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName='MalgunGothic')
            header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontName='MalgunGothic')
            normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontName='MalgunGothic')
        except:
            title_style = styles['Title']
            header_style = styles['Heading2']
            normal_style = styles['Normal']
        
        # 문서 내용 구성
        story = []
        
        # 제목
        story.append(Paragraph("🤖 AI 특허 분석 보고서", title_style))
        story.append(Spacer(1, 12))
        
        # 기본 정보
        story.append(Paragraph("📋 분석 개요", header_style))
        story.append(Paragraph(f"검색어: {analysis_data.get('search_query', 'N/A')}", normal_style))
        story.append(Paragraph(f"분석 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}", normal_style))
        story.append(Paragraph(f"총 특허 수: {analysis_data.get('total_count', 0):,}건", normal_style))
        story.append(Spacer(1, 12))
        
        # 주요 통계
        story.append(Paragraph("📊 주요 통계", header_style))
        
        # 출원인 TOP 5
        top_applicants = analysis_data.get('top_applicants', {})
        if top_applicants:
            story.append(Paragraph("주요 출원인:", normal_style))
            for i, (name, count) in enumerate(list(top_applicants.items())[:5], 1):
                story.append(Paragraph(f"{i}. {name}: {count}건", normal_style))
            story.append(Spacer(1, 12))
        
        # 연도별 동향
        yearly_data = analysis_data.get('yearly_trends', {})
        if yearly_data:
            story.append(Paragraph("연도별 출원 현황:", normal_style))
            for year, count in yearly_data.items():
                story.append(Paragraph(f"• {year}년: {count}건", normal_style))
            story.append(Spacer(1, 12))
        
        # AI 분석 결과
        story.append(PageBreak())
        story.append(Paragraph("🧠 AI 분석 결과", header_style))
        
        # 분석 결과를 문단별로 나누어 추가
        analysis_paragraphs = analysis_result.split('\n\n')
        for para in analysis_paragraphs:
            if para.strip():
                cleaned_para = para.replace('**', '').replace('##', '').replace('#', '').strip()
                if cleaned_para:
                    story.append(Paragraph(cleaned_para, normal_style))
                    story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _prepare_comprehensive_data(self, patents: List[Dict]) -> Dict:
        """대량 특허 데이터 종합 분석용 전처리"""
        applicants = {}
        years = {}
        statuses = {}
        ipc_codes = {}
        
        for patent in patents:
            # 출원인 통계
            applicant = patent.get('applicant', '정보없음')[:50]
            applicants[applicant] = applicants.get(applicant, 0) + 1
            
            # 연도별 통계
            app_date = patent.get('app_date', '')
            if app_date and len(app_date) >= 4:
                year = app_date[:4]
                years[year] = years.get(year, 0) + 1
            
            # 등록상태 통계
            status = patent.get('reg_status', '출원')
            statuses[status] = statuses.get(status, 0) + 1
            
            # IPC 코드 분석
            ipc = patent.get('ipc_code', '')
            if ipc:
                ipc_main = ipc.split()[0][:4] if ipc.split() else ipc[:4]
                ipc_codes[ipc_main] = ipc_codes.get(ipc_main, 0) + 1
        
        return {
            'total_count': len(patents),
            'top_applicants': dict(sorted(applicants.items(), key=lambda x: x[1], reverse=True)[:15]),
            'yearly_trends': dict(sorted(years.items())),
            'status_distribution': statuses,
            'ipc_distribution': dict(sorted(ipc_codes.items(), key=lambda x: x[1], reverse=True)[:10]),
            'patents_sample': patents[:3]
        }
    
    def _generate_expert_prompt(self, data: Dict, analysis_type: str, user_query: str) -> str:
        """전문가 수준의 분석 프롬프트 생성"""
        
        base_context = f"""# 특허 빅데이터 분석 보고서

## 📊 분석 데이터 규모
- **총 분석 특허**: {data['total_count']:,}건
- **분석 완료 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **주요 기술 분야**: {len(data.get('ipc_distribution', {}))}개 IPC 코드

## 🏢 시장 참여자 현황
{self._format_market_analysis(data)}

## 📈 기술 발전 트렌드  
{self._format_trend_analysis(data)}

## ⚖️ 특허 권리 현황
{self._format_rights_analysis(data)}
"""

        expert_prompts = {
            "competitive_analysis": f"""{base_context}

## 🏆 심화 경쟁 분석 요청

위 대규모 특허 데이터를 바탕으로 다음 관점에서 **전략컨설팅 수준**의 경쟁 분석을 수행하세요:

### 1. 시장 지배력 구조 분석
- 특허 포트폴리오 규모별 기업 계층화
- 기술 영향력 지수 및 핵심 플레이어 식별
- 시장 진입 장벽 및 기술적 해자 분석

### 2. 기술 경쟁 인텐시티 맵핑
- IPC 코드별 경쟁 밀도 및 혁신 활발도
- 특허 분쟁 리스크가 높은 핫존 식별
- 기술 융합 및 경계 확장 패턴

### 3. 전략적 포지셔닝 인사이트
- 각 주요 기업의 기술 전략 방향성
- 협력 vs 경쟁 구도 및 에코시스템 분석
- M&A 및 라이선싱 기회 영역

**🎯 최종 결과물**: C-Level 경영진 대상 전략 의사결정용 핵심 인사이트""",

            "trend_analysis": f"""{base_context}

## 📈 기술 트렌드 예측 분석

### 1. 기술 라이프사이클 분석
- 현재 기술 성숙도 및 S-Curve 상의 위치
- 신기술 도입기 vs 성숙기 기술 구분
- 차세대 기술로의 전환 시점 예측

### 2. 혁신 패턴 및 동력 분석
- 기술 혁신의 주요 동력원 (정책, 시장, 기술)
- 파괴적 혁신 vs 점진적 혁신 패턴
- 글로벌 기술 트렌드와의 연관성

### 3. 미래 기술 발전 로드맵
- 5년 후 기술 지형 예측
- 새로운 기회 영역 및 성장 동력
- 기술 수렴 및 융합 트렌드""",

            "future_direction": f"""{base_context}

## 🔮 미래 방향성 및 전략 제안

### 1. 기술 기회 발굴 및 우선순위화
- 특허 공백지대 및 블루오션 영역
- 투자 대비 효과가 높은 기술 영역
- 단기/중기/장기 기회 매트릭스

### 2. 특허 전략 로드맵 수립
- 방어적 vs 공격적 특허 전략 균형
- 핵심 원천기술 vs 응용기술 포트폴리오
- 글로벌 출원 전략 및 지역별 우선순위

### 3. 실행 계획 및 자원 배분
- 특허 확보를 위한 투자 우선순위
- 내부 R&D vs 외부 협력 전략
- 위험 관리 및 컨틴전시 플랜"""
        }

        prompt = expert_prompts.get(analysis_type, expert_prompts["competitive_analysis"])
        
        if user_query:
            prompt += f"\n\n## 🔍 추가 분석 요청\n{user_query}\n\n**이 질문을 중심으로 위 분석을 더욱 구체화하고 실용적인 답변을 제시하세요.**"
        
        prompt += "\n\n**📋 보고서 작성 기준**: 각 섹션별 명확한 제목, 핵심 포인트는 굵은 글씨, 실행 가능한 구체적 제안, 의사결정 지원용 명확한 결론"
        
        return prompt
    
    def _format_market_analysis(self, data: Dict) -> str:
        """시장 참여자 현황 포매팅"""
        lines = []
        for i, (name, count) in enumerate(list(data['top_applicants'].items())[:5], 1):
            percentage = (count / data['total_count']) * 100
            lines.append(f"{i}. **{name}**: {count:,}건 ({percentage:.1f}%)")
        return "\n".join(lines)
    
    def _format_trend_analysis(self, data: Dict) -> str:
        """기술 발전 트렌드 포매팅"""
        yearly = data['yearly_trends']
        if len(yearly) < 2:
            return "• 연도별 데이터 부족으로 트렌드 분석 제한"
        
        years = list(yearly.keys())
        recent_year = years[-1]
        prev_year = years[-2] if len(years) > 1 else years[-1]
        
        recent_count = yearly[recent_year]
        prev_count = yearly[prev_year]
        
        if prev_count > 0:
            growth_rate = ((recent_count - prev_count) / prev_count) * 100
            trend = "증가" if growth_rate > 0 else "감소"
            lines = [
                f"• **최근 출원 동향**: {recent_year}년 {recent_count:,}건",
                f"• **전년 대비**: {abs(growth_rate):.1f}% {trend}",
                f"• **활발 기간**: {min(yearly.keys())}년~{max(yearly.keys())}년"
            ]
        else:
            lines = [f"• **최근 출원**: {recent_year}년 {recent_count:,}건"]
        
        return "\n".join(lines)
    
    def _format_rights_analysis(self, data: Dict) -> str:
        """권리 현황 포매팅"""
        statuses = data['status_distribution']
        total = sum(statuses.values())
        
        lines = []
        for status, count in statuses.items():
            percentage = (count / total) * 100 if total > 0 else 0
            lines.append(f"• **{status}**: {count:,}건 ({percentage:.1f}%)")
        
        return "\n".join(lines)

# 호환성 함수들
def summarize_text_with_gemini(api_key: str, text: str) -> str:
    analyzer = AdvancedPatentAnalyzer(api_key)
    return analyzer.quick_summarize(text)

def analyze_patent_data_with_gemini(api_key: str, patent_data: List[Dict], user_query: str) -> str:
    analyzer = AdvancedPatentAnalyzer(api_key)
    return analyzer.comprehensive_analysis(patent_data, "competitive_analysis", user_query)

def analyze_detailed_data_with_gemini(api_key: str, patent_data: List[Dict], user_query: str) -> str:
    analyzer = AdvancedPatentAnalyzer(api_key)
    return analyzer.comprehensive_analysis(patent_data, "future_direction", user_query)
