"""
KIPRIS Open API와 통신하여 특허 정보를 검색하고 처리하는 모든 기능을 담당하는 모듈입니다.
app.py의 요청에 따라 KIPRIS 서버에서 데이터를 가져오는 '손발' 역할을 합니다.
"""

# --- 1. 기본 라이브러리 임포트 ---
import requests
import xml.etree.ElementTree as ET
import math
import time

# --- 2. 필드별 검색 헬퍼 함수 (내부 사용) ---
def _search_patents_by_field(api_key, keyword, field, page_no=1, num_of_rows=10):
    """
    지정된 단일 필드에서 특허를 검색하는 내부 헬퍼 함수입니다.
    KIPRIS API의 searchQuery 문법을 사용합니다.
    """
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    
    # app.py에서 받은 필드 이름을 API가 이해하는 코드로 변환합니다.
    field_code_map = {
        "astrtCont": "AB",      # 초록 (Abstract)
        "applicantName": "AP",  # 출원인 (Applicant)
        "inventionTitle": "TI", # 발명 명칭 (Title)
        "claim": "CL"           # 청구항 (Claim)
    }
    api_field_code = field_code_map.get(field, "AB") # 기본값은 초록 검색

    # API 공식 문법에 맞게 검색 쿼리를 생성합니다. 예: AP=(삼성전자)
    search_query = f"{api_field_code}=({keyword})"
    
    params = {
        "ServiceKey": api_key,
        "searchQuery": search_query,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
        "sortSpec": "applicationDate",
        "descSort": "true"
    }
    
    patent_list = []
    total_count = 0
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            total_count = int(root.findtext(".//totalCount", "0"))
            for item in root.findall(".//item"):
                app_num = item.findtext(".//applicationNumber", "").strip()
                link_url = f"https://kipris.or.kr/search/view_patent.jsp?applno={app_num.replace('-', '')}"
                patent_list.append({
                    "title": item.findtext(".//inventionTitle", "정보 없음").strip(),
                    "app_num": app_num,
                    "abstract": item.findtext(".//astrtCont", "정보 없음").strip(),
                    "applicant": item.findtext(".//applicantName", "정보 없음").strip(),
                    "inventor": item.findtext(".//inventorName", "정보 없음").strip(),
                    "app_date": item.findtext(".//applicationDate", "정보 없음").strip(),
                    "reg_status": item.findtext(".//registerStatus", "정보 없음").strip(),
                    "reg_num": item.findtext(".//registerNumber", "정보 없음").strip(),
                    "reg_date": item.findtext(".//registerDate", "정보 없음").strip(),
                    "link": link_url
                })
            return patent_list, total_count
    except Exception as e:
        print(f"'{field}' 필드 검색 중 오류: {e}")
        return [], 0
    return [], 0

# --- 3. 전체 특허 수집 함수 ---
def search_all_patents(api_key, keyword, search_fields, max_results=1000, progress_callback=None):
    """여러 필드에서 모든 특허를 개별적으로 검색하고 통합하는 함수입니다."""
    all_patents_dict = {}
    
    for i, field in enumerate(search_fields):
        page_no = 1
        print(f"--- '{field}' 필드 검색 시작 ---")
        
        _, total_count_for_field = _search_patents_by_field(api_key, keyword, field, page_no=1)
        if total_count_for_field == 0:
            continue
        
        collect_count = min(total_count_for_field, max_results)
        total_pages = math.ceil(collect_count / 10)

        for page in range(1, total_pages + 1):
            if progress_callback:
                progress = (i / len(search_fields)) + (page / total_pages) * (1 / len(search_fields))
                progress_callback(progress, f"'{field}' 필드 검색 중... ({page}/{total_pages} 페이지)")

            patents_on_page, _ = _search_patents_by_field(api_key, keyword, field, page_no=page)
            if not patents_on_page:
                break
            
            for patent in patents_on_page:
                if patent['app_num'] not in all_patents_dict:
                    all_patents_dict[patent['app_num']] = patent
            
            if len(all_patents_dict) >= max_results:
                break
            time.sleep(0.3)
    
    print(f"--- 총 {len(all_patents_dict)}건의 고유 특허 수집 완료 ---")
    final_list = list(all_patents_dict.values())
    final_list.sort(key=lambda x: x.get('app_date', '0'), reverse=True)
    return final_list

# --- 4. 상세 정보 조회 함수 (정밀 분석용) ---
def get_patent_details(api_key, app_num):
    """출원번호로 특허의 상세 정보(IPC)를 조회하는 함수입니다."""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getDetailInfo"
    params = {"ServiceKey": api_key, "applicationNumber": app_num}
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            ipc_info = root.findtext(".//ipcCode", "")
            return {"ipc": ipc_info}
    except Exception as e:
        print(f"상세 정보 조회 중 오류: {e}")
        return {"ipc": ""}
    return {"ipc": ""}