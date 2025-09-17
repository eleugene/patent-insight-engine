# KIPRIS Open API와 통신하여 특허 정보를 검색하고 처리하는 모든 기능을 담당하는 모듈입니다.
# app.py의 요청에 따라 KIPRIS 서버에서 데이터를 가져오는 '손발' 역할을 합니다.

# --- 1. 기본 라이브러리 임포트 ---
import requests  # HTTP 요청을 보내기 위한 라이브러리
import xml.etree.ElementTree as ET  # XML 데이터를 파싱(분석)하기 위한 라이브러리
import math      # 수학 계산 (페이지 수 계산 등)
import time      # 시간 관련 기능 (API 호출 시 지연 등)

# --- 2. 1 페이지 검색 함수 (단순 검색용) ---
def search_patents(api_key, keyword, page_no=1, num_of_rows=10):
    """
    (단순 검색용) KIPRIS API를 호출하여 초록에서만 검색하는 함수입니다.
    주로 UI의 첫 화면 목록 표시에 사용됩니다.

    Args:
        api_key (str): KIPRIS+ API 인증키.
        keyword (str): 검색할 키워드.
        page_no (int): 조회할 페이지 번호.
        num_of_rows (int): 한 페이지에 가져올 특허 개수.

    Returns:
        tuple: (특허 데이터 리스트, 전체 검색 결과 수) 튜플을 반환합니다.
    """
    # KIPRIS의 '특허 실용신안 정보'를 조회하는 API의 엔드포인트 주소입니다.
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    # API 요청에 필요한 파라미터들을 딕셔너리 형태로 구성합니다.
    params = {"ServiceKey": api_key, "astrtCont": keyword, "numOfRows": num_of_rows, "pageNo": page_no}
    
    patent_list = []  # 검색된 특허 정보를 저장할 빈 리스트
    total_count = 0     # 전체 검색 결과 수를 저장할 변수
    
    try:
        # requests 라이브러리를 사용해 GET 방식으로 API에 요청을 보냅니다.
        # timeout=30은 30초 이상 응답이 없으면 오류로 처리하라는 의미입니다.
        response = requests.get(url, params=params, timeout=30)
        
        # API 서버로부터 정상적인 응답(상태 코드 200)을 받았는지 확인합니다.
        if response.status_code == 200:
            # 응답받은 XML 텍스트를 ElementTree 객체로 변환하여 파싱 준비를 합니다.
            root = ET.fromstring(response.content)
            # XML 데이터에서 './/totalCount' 태그를 찾아 전체 결과 수를 가져옵니다.
            total_count = int(root.findtext(".//totalCount", "0"))

            # './/item' 태그를 모두 찾아, 각 특허 정보를 하나씩 처리합니다.
            for item in root.findall(".//item"):
                app_num = item.findtext(".//applicationNumber", "").strip()
                # 출원번호를 이용해 KIPRIS 상세 정보 페이지로 바로 갈 수 있는 URL을 생성합니다.
                link_url = f"http://krtkpat.kipris.or.kr/kpat/biblioa.do?applno={app_num}"
                # 각 특허의 상세 정보들을 딕셔너리 형태로 정리합니다.
                patent_list.append({
                    "title": item.findtext(".//inventionTitle", "정보 없음").strip(),
                    "app_num": app_num, "abstract": item.findtext(".//astrtCont", "정보 없음").strip(),
                    "applicant": item.findtext(".//applicantName", "정보 없음").strip(),
                    "app_date": item.findtext(".//applicationDate", "정보 없음").strip(),
                    "reg_status": item.findtext(".//registerStatus", "정보 없음").strip(),
                    "reg_num": item.findtext(".//registerNumber", "정보 없음").strip(),
                    "reg_date": item.findtext(".//registerDate", "정보 없음").strip(), "link": link_url
                })
            
            # 받아온 특허 목록을 출원일(app_date) 기준으로 최신순(내림차순)으로 정렬합니다.
            patent_list.sort(key=lambda x: x['app_date'], reverse=True)
            return patent_list, total_count
            
    except Exception as e:
        # API 호출이나 데이터 처리 중 어떤 오류라도 발생하면, 터미널에 오류를 출력합니다.
        print(f"search_patents 함수 오류: {e}")
        return [], 0 # 실패 시 빈 리스트와 0을 반환
        
    return [], 0 # 정상 응답이 아닌 경우 빈 리스트와 0을 반환

# --- 3. 필드별 검색 헬퍼 함수 (내부 사용) ---
def _search_patents_by_field(api_key, keyword, field, page_no=1, num_of_rows=10):
    """지정된 단일 필드(예: 'inventionTitle')에서 특허를 검색하는 내부 헬퍼 함수입니다."""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    # field 변수를 파라미터 키로 사용하여 동적으로 검색 필드를 지정합니다.
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

# --- 4. 전체 특허 수집 함수 (정밀 분석용) ---
def search_all_patents(api_key, keyword, search_fields, max_results=100, progress_callback=None):
    """여러 필드에서 모든 특허를 개별적으로 검색하고 통합하는 함수입니다."""
    all_patents_dict = {} # 출원번호를 key로 사용하여 중복을 제거하기 위한 딕셔너리
    
    # 지정된 각 필드(예: 'inventionTitle', 'astrtCont', 'claim')에 대해 순차적으로 검색합니다.
    for i, field in enumerate(search_fields):
        page_no = 1
        print(f"--- '{field}' 필드 검색 시작 ---")
        
        # 첫 페이지를 호출하여 해당 필드의 전체 검색 결과 수를 먼저 확인합니다.
        _, total_count_for_field = _search_patents_by_field(api_key, keyword, field, page_no=1)
        if total_count_for_field == 0:
            continue # 검색 결과가 없으면 다음 필드로 넘어감
        
        # 수집할 최대 페이지 수를 계산합니다. (max_results를 넘지 않도록)
        total_pages = math.ceil(min(total_count_for_field, max_results) / 10)

        # 계산된 페이지 수만큼 반복하여 데이터를 수집합니다.
        for page in range(1, total_pages + 1):
            if progress_callback:
                # app.py에 진행 상황을 전달하기 위한 콜백 함수를 호출합니다.
                progress = (i / len(search_fields)) + (page / total_pages) * (1 / len(search_fields))
                progress_callback(progress, f"'{field}' 필드 검색 중... ({page}/{total_pages} 페이지)")

            patents_on_page, _ = _search_patents_by_field(api_key, keyword, field, page_no=page)
            if not patents_on_page:
                break
            
            # 수집된 특허를 딕셔너리에 추가하여 중복을 자동으로 제거합니다.
            for patent in patents_on_page:
                if patent['app_num'] not in all_patents_dict:
                    all_patents_dict[patent['app_num']] = patent
            
            if len(all_patents_dict) >= max_results:
                break # 수집한 특허 수가 최대치를 넘으면 중단
            time.sleep(0.3) # API 서버에 과도한 부하를 주지 않기 위해 0.3초 대기
    
    print(f"--- 총 {len(all_patents_dict)}건의 고유 특허 수집 완료 ---")
    final_list = list(all_patents_dict.values())
    final_list.sort(key=lambda x: x['app_date'], reverse=True) # 최종 결과를 최신순으로 정렬
    return final_list

# --- 5. 상세 정보 조회 함수 (정밀 분석용) ---
def get_patent_details(api_key, app_num):
    """출원번호로 특허의 상세 정보(IPC)를 조회하는 함수입니다."""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getDetailInfo"
    params = {"ServiceKey": api_key, "applicationNumber": app_num}
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            # 상세 정보에서 IPC(국제특허분류) 코드를 찾아 반환합니다.
            ipc_info = root.findtext(".//ipcCode", "")
            return {"ipc": ipc_info}
    except Exception as e:
        print(f"상세 정보 조회 중 오류: {e}")
        return {"ipc": ""}
    return {"ipc": ""}
