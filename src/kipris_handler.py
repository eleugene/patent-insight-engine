import requests
import xml.etree.ElementTree as ET
import math
import time

def search_patents(api_key, keyword, page_no=1, num_of_rows=10):
    """(단순 검색용) KIPRIS API를 호출하여 초록에서만 검색하는 함수"""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    params = {"ServiceKey": api_key, "astrtCont": keyword, "numOfRows": num_of_rows, "pageNo": page_no}
    patent_list = []
    total_count = 0
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            total_count = int(root.findtext(".//totalCount", "0"))
            for item in root.findall(".//item"):
                app_num = item.findtext(".//applicationNumber", "").strip()
                link_url = f"http://krtkpat.kipris.or.kr/kpat/biblioa.do?applno={app_num}"
                patent_list.append({
                    "title": item.findtext(".//inventionTitle", "정보 없음").strip(),
                    "app_num": app_num, "abstract": item.findtext(".//astrtCont", "정보 없음").strip(),
                    "applicant": item.findtext(".//applicantName", "정보 없음").strip(),
                    "app_date": item.findtext(".//applicationDate", "정보 없음").strip(),
                    "reg_status": item.findtext(".//registerStatus", "정보 없음").strip(),
                    "reg_num": item.findtext(".//registerNumber", "정보 없음").strip(),
                    "reg_date": item.findtext(".//registerDate", "정보 없음").strip(), "link": link_url
                })
            patent_list.sort(key=lambda x: x['app_date'], reverse=True)
            return patent_list, total_count
    except Exception as e:
        print(f"search_patents 함수 오류: {e}")
        return [], 0
    return [], 0

def _search_patents_by_field(api_key, keyword, field, page_no=1, num_of_rows=10):
    """지정된 단일 필드에서 특허를 검색하는 내부 헬퍼 함수"""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    params = {"ServiceKey": api_key, field: keyword, "numOfRows": num_of_rows, "pageNo": page_no}
    patent_list = []
    total_count = 0
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            total_count = int(root.findtext(".//totalCount", "0"))
            for item in root.findall(".//item"):
                app_num = item.findtext(".//applicationNumber", "").strip()
                link_url = f"http://krtkpat.kipris.or.kr/kpat/biblioa.do?applno={app_num}"
                patent_list.append({
                    "title": item.findtext(".//inventionTitle", "정보 없음").strip(),
                    "app_num": app_num, "abstract": item.findtext(".//astrtCont", "정보 없음").strip(),
                    "applicant": item.findtext(".//applicantName", "정보 없음").strip(),
                    "app_date": item.findtext(".//applicationDate", "정보 없음").strip(),
                    "reg_status": item.findtext(".//registerStatus", "정보 없음").strip(),
                    "reg_num": item.findtext(".//registerNumber", "정보 없음").strip(),
                    "reg_date": item.findtext(".//registerDate", "정보 없음").strip(), "link": link_url
                })
            return patent_list, total_count
    except Exception as e:
        print(f"'{field}' 필드 검색 중 오류: {e}")
        return [], 0
    return [], 0

def search_all_patents(api_key, keyword, search_fields, max_results=100, progress_callback=None):
    """여러 필드에서 모든 특허를 개별적으로 검색하고 통합하는 함수"""
    all_patents_dict = {}
    
    for i, field in enumerate(search_fields):
        page_no = 1
        print(f"--- '{field}' 필드 검색 시작 ---")
        
        # 첫 페이지를 호출하여 해당 필드의 전체 개수 확인
        _, total_count_for_field = _search_patents_by_field(api_key, keyword, field, page_no=1)
        if total_count_for_field == 0:
            continue
        
        total_pages = math.ceil(min(total_count_for_field, max_results) / 10)

        for page in range(1, total_pages + 1):
            if progress_callback:
                # 전체 진행률을 필드별로 나누어 표시
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
    final_list.sort(key=lambda x: x['app_date'], reverse=True)
    return final_list

def get_patent_details(api_key, app_num):
    """출원번호로 특허의 상세 정보(IPC)를 조회하는 함수"""
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