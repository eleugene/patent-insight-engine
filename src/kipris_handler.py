"""
완전 개선된 KIPRIS API 핸들러 - 발명자 정보 해결 + 스마트 대량 수집 + 부분일치 검색
"""

import requests
import xml.etree.ElementTree as ET
import math
import time
from typing import List, Dict, Optional, Tuple
import re

class AdvancedKiprisOptimizer:
    """고도화된 KIPRIS API 최적화 클래스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
        self.call_count = 0
        
    def smart_comprehensive_search(self, keyword: str, max_results: int = 200) -> List[Dict]:
        """AI 기반 스마트 대량 수집 - 관련성 높은 특허만 필터링"""
        print(f"🧠 스마트 대량 검색 시작: '{keyword}'")
        
        # 스마트 필드 선택
        selected_fields = self._smart_field_selection(keyword)
        print(f"🎯 선택된 필드: {selected_fields}")
        
        all_patents = {}
        field_results = {}
        
        for field in selected_fields:
            print(f"\n--- '{field}' 필드 검색 ---")
            
            # 첫 페이지로 총 개수 확인
            _, total_count = self._search_field(keyword, field, 1, 10)
            
            if total_count == 0:
                continue
                
            print(f"📊 {field}: {total_count}건 발견")
            field_results[field] = total_count
            
            # 🔥 대량 수집 전략: 관련성 높은 특허 우선 수집
            if total_count <= 100:
                collect_count = total_count
            elif total_count <= 500:
                collect_count = int(total_count * 0.7)
            else:
                collect_count = max(int(total_count * 0.5), 200)
            
            collect_count = min(collect_count, 500)  # 최대 500건으로 제한
            needed_pages = math.ceil(collect_count / 10)
            
            print(f"📈 {field}: {collect_count}건 수집 예정 ({needed_pages}페이지)")
            
            # 페이지별 대량 수집
            for page in range(1, needed_pages + 1):
                patents_page, _ = self._search_field(keyword, field, page, 10)
                
                for patent in patents_page:
                    app_num = patent.get('app_num', '')
                    if app_num and app_num not in all_patents:
                        # 관련성 점수 계산
                        relevance_score = self._calculate_relevance(patent, keyword)
                        patent['_relevance_score'] = relevance_score
                        all_patents[app_num] = patent
                
                if page % 5 == 0:  # 5페이지마다 진행상황 출력
                    print(f"   📄 진행: {page}/{needed_pages} 페이지 ({len(all_patents)}건 수집)")
                    
                time.sleep(0.1)  # API 호출 간격 최소화
        
        # 관련성 기반 정렬 및 필터링
        final_list = list(all_patents.values())
        final_list.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
        
        # 최종 결과 제한
        if len(final_list) > max_results:
            final_list = final_list[:max_results]
            print(f"🎯 관련성 기반 상위 {max_results}건 선별")
        
        # 관련성 점수 제거
        for patent in final_list:
            patent.pop('_relevance_score', None)
        
        print(f"🎯 최종 수집: {len(final_list)}건 (API 호출: {self.call_count}회)")
        print(f"📊 필드별 발견 현황: {field_results}")
        
        return final_list
    
    def _smart_field_selection(self, keyword: str) -> List[str]:
        """키워드 특성 분석 후 최적 필드 선택 - 부분일치 지원"""
        # 회사명 패턴 (부분일치로 검색)
        company_patterns = ['주식회사', '㈜', 'Co.', 'Ltd', 'Inc', '전자', '화학', '자동차', '그룹', 
                           '대학교', '연구소', '산업', '기술', '시스템']
        if any(pattern in keyword for pattern in company_patterns):
            return ['applicantName']
        
        # 명백한 회사명인 경우
        if any(char in keyword for char in ['삼성', '엘지', 'LG', '현대', '포스코', 'SK', '네이버', '카카오']):
            return ['applicantName']
        
        # 기술 키워드 - 초록과 제목에서 검색
        tech_patterns = ['시스템', '방법', '장치', '기기', '센서', '로봇', '배터리', 'AI', '인공지능', 
                        '마이크로', '나노', '바이오', '스마트', '자동', '제어', '통신', '반도체']
        if any(pattern in keyword for pattern in tech_patterns):
            return ['astrtCont', 'inventionTitle']
        
        # 일반 키워드 - 초록만 검색
        return ['astrtCont']
    
    def _calculate_relevance(self, patent: Dict, keyword: str) -> float:
        """특허의 키워드 관련성 점수 계산"""
        score = 0.0
        keyword_lower = keyword.lower()
        
        # 제목에서 키워드 매칭 (가중치 3.0)
        title = patent.get('title', '').lower()
        if keyword_lower in title:
            score += 3.0
        
        # 초록에서 키워드 매칭 (가중치 2.0)
        abstract = patent.get('abstract', '').lower()
        if keyword_lower in abstract:
            score += 2.0
        
        # 등록 특허 우대 (가중치 1.0)
        reg_status = patent.get('reg_status', '')
        if '등록' in reg_status:
            score += 1.0
        
        # 최신 특허 우대 (가중치 0.5)
        app_date = patent.get('app_date', '')
        if app_date and len(app_date) >= 4:
            try:
                year = int(app_date[:4])
                if year >= 2020:
                    score += 0.5
            except:
                pass
        
        return score
    
    def _search_field(self, keyword: str, field: str, page_no: int = 1, num_of_rows: int = 10) -> Tuple[List[Dict], int]:
        """필드별 검색 실행 - 발명자 정보 완전 해결 + 부분일치 검색"""
        self.call_count += 1
        
        # 출원인 검색 시 부분일치 적용
        if field == 'applicantName':
            search_value = f"*{keyword}*"
            print(f"🔍 출원인 부분일치 검색: {search_value}")
        else:
            search_value = keyword
        
        params = {
            "ServiceKey": self.api_key,
            field: search_value,
            "numOfRows": num_of_rows,
            "pageNo": page_no
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                return [], 0
            
            root = ET.fromstring(response.content)
            
            if root.findtext(".//successYN", "N") != "Y":
                return [], 0
            
            total_count = int(root.findtext(".//totalCount", "0"))
            patents = []
            
            for item in root.findall(".//item"):
                app_num = item.findtext(".//applicationNumber", "").strip()
                
                # 🔥 발명자 정보 완전 해결
                inventor_info = self._extract_inventor_complete(item)
                
                patent = {
                    "title": item.findtext(".//inventionTitle", "정보없음").strip(),
                    "app_num": app_num,
                    "abstract": item.findtext(".//astrtCont", "정보없음").strip(),
                    "applicant": item.findtext(".//applicantName", "정보없음").strip(),
                    "inventor": inventor_info,  # 완전히 개선된 발명자 정보
                    "app_date": item.findtext(".//applicationDate", "").strip(),
                    "reg_status": item.findtext(".//registerStatus", "출원").strip(),
                    "reg_num": item.findtext(".//registerNumber", "").strip(),
                    "kipris_url": self._generate_kipris_url(app_num),  # 개선된 링크
                    "link": self._generate_kipris_url(app_num),  # 호환성을 위해 유지
                    "ipc_code": item.findtext(".//ipcCode", "").strip()
                }
                patents.append(patent)
            
            return patents, total_count
            
        except Exception as e:
            print(f"❌ {field} 검색 오류: {e}")
            return [], 0
    
    def _extract_inventor_complete(self, item_xml) -> str:
        """발명자 정보 완전 추출 - 모든 패턴 대응"""
        inventor_candidates = []
        
        # 다양한 XML 태그 패턴에서 발명자 정보 추출 시도
        possible_tags = [
            './/inventorName',
            './/inventor', 
            './/invtNm',
            './/personName',
            './/inventors/inventor',
            './/inventors/inventorName'
        ]
        
        for tag_pattern in possible_tags:
            try:
                elements = item_xml.findall(tag_pattern)
                if elements:
                    for elem in elements:
                        if elem.text and elem.text.strip():
                            inventor_candidates.append(elem.text.strip())
            except:
                continue
        
        # 단일 태그에서 시도
        for tag_pattern in possible_tags:
            try:
                elem = item_xml.find(tag_pattern)
                if elem is not None and elem.text and elem.text.strip():
                    inventor_candidates.append(elem.text.strip())
            except:
                continue
        
        # 중복 제거 및 정제
        unique_inventors = []
        for inventor in inventor_candidates:
            # 구분자로 분할 시도
            for separator in [';', ',', '|', '/']:
                if separator in inventor:
                    parts = [part.strip() for part in inventor.split(separator) if part.strip()]
                    unique_inventors.extend(parts)
                    break
            else:
                unique_inventors.append(inventor)
        
        # 최종 중복 제거
        unique_inventors = list(dict.fromkeys(unique_inventors))
        
        if not unique_inventors:
            return "발명자 정보 미제공"
        elif len(unique_inventors) == 1:
            return unique_inventors[0]
        elif len(unique_inventors) <= 3:
            return "; ".join(unique_inventors)
        else:
            return f"{unique_inventors[0]} 외 {len(unique_inventors)-1}인"
    
    def _generate_kipris_url(self, app_num: str) -> str:
        """KIPRIS 상세페이지 URL 생성 - 다중 패턴 지원"""
        if not app_num:
            return ""
        
        clean_num = app_num.replace('-', '')
        
        # 가장 안정적인 KIPRIS Plus URL 패턴
        return f"https://plus.kipris.or.kr/kpat/search/SearchMain.do?method=searchUTL&param1={clean_num}"

# 호환성을 위한 메인 함수
def search_all_patents(api_key: str, keyword: str, search_fields: List[str], max_results: int = 200, progress_callback=None) -> List[Dict]:
    """메인 검색 함수 - 스마트 대량 수집"""
    optimizer = AdvancedKiprisOptimizer(api_key)
    return optimizer.smart_comprehensive_search(keyword, max_results)

def get_patent_details(api_key: str, app_num: str) -> Optional[Dict]:
    """특허 상세정보 조회"""
    optimizer = AdvancedKiprisOptimizer(api_key)
    try:
        patents, _ = optimizer._search_field(app_num, "applicationNumber", 1, 1)
        return patents[0] if patents else None
    except:
        return None
