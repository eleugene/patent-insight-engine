import requests
import xml.etree.ElementTree as ET

def search_patents(api_key, keyword, page_no=1, num_of_rows=10):
    """KIPRIS API를 호출하여 여러 특허를 검색하고, 상세 정보와 전체 개수를 반환하는 함수"""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"

    params = {
        "ServiceKey": api_key,
        "astrtCont": keyword,
        "numOfRows": num_of_rows,
        "pageNo": page_no
    }

    patent_list = []
    total_count = 0

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            total_count = int(root.findtext(".//totalCount", "0"))

            for item in root.findall(".//item"):
                app_num = item.findtext(".//applicationNumber", "").strip()

                # 3. KIPRIS 바로가기 링크 URL 구조 수정
                link_url = f"http://krtkpat.kipris.or.kr/kpat/biblioa.do?applno={app_num}"

                patent_data = {
                    "title": item.findtext(".//inventionTitle", "정보 없음").strip(),
                    "app_num": app_num,
                    "abstract": item.findtext(".//astrtCont", "정보 없음").strip(),
                    "applicant": item.findtext(".//applicantName", "정보 없음").strip(),
                    # 2. 발명자 정보는 API가 제공하지 않으므로 우선 제외
                    "app_date": item.findtext(".//applicationDate", "정보 없음").strip(),
                    "reg_status": item.findtext(".//registerStatus", "정보 없음").strip(),
                    "reg_num": item.findtext(".//registerNumber", "정보 없음").strip(),
                    "reg_date": item.findtext(".//registerDate", "정보 없음").strip(),
                    "link": link_url
                }
                patent_list.append(patent_data)

            # 1. API가 정렬을 지원하지 않으므로, 파이썬으로 직접 최신순 정렬
            patent_list.sort(key=lambda x: x['app_date'], reverse=True)

            return patent_list, total_count

    except Exception as e:
        print(f"API 호출 또는 데이터 처리 중 오류 발생: {e}")
        return [], 0

    return [], 0