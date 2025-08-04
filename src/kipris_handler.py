import requests
import xml.etree.ElementTree as ET

def search_patents(api_key, keyword):
    """KIPRIS API를 호출하여 특허를 검색하고 초록을 반환하는 함수"""
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    
    # 검색 파라미터를 'astrtCont'로 지정
    params = {
        "ServiceKey": api_key,
        "astrtCont": keyword,
        "numOfRows": 10
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            # --- !! 핵심 수정 부분 !! ---
            # 'abstract'가 아니라 'astrtCont'를 찾도록 변경
            abstract_text = root.findtext(".//astrtCont") 
            
            if abstract_text:
                return abstract_text.strip()
            return "검색 결과는 있으나, 초록(astrtCont) 정보가 없습니다."
            
    except Exception as e:
        return f"API 호출 또는 데이터 처리 중 오류 발생: {e}"
        
    return "검색 결과가 없습니다."