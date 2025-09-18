import requests
import os
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv("KIPRIS_API_KEY")

def test_kipris_api():
    print("🔍 KIPRIS API 상태 테스트 시작")
    print(f"🔑 API 키 확인: {'✅ 있음' if api_key else '❌ 없음'}")
    
    if not api_key:
        print("❌ .env 파일에서 KIPRIS_API_KEY를 확인하세요!")
        return
    
    print(f"🔑 API 키 앞 15자: {api_key[:15]}...")
    
    # KIPRIS API 호출
    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
    params = {
        "ServiceKey": api_key,
        "searchQuery": "AB=(배터리)",
        "numOfRows": 1,
        "pageNo": 1
    }
    
    try:
        print("📡 API 호출 중...")
        response = requests.get(url, params=params, timeout=10)
        print(f"📊 HTTP 상태: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ HTTP 연결 성공")
            
            # XML 응답 분석
            print("\n📄 API 응답 내용:")
            print("="*50)
            print(response.text)
            print("="*50)
            
            # 성공/실패 판단
            if "successYN>Y" in response.text:
                print("🎉 API 호출 완전 성공! 서비스 정상 작동 중")
            elif "resultCode>10" in response.text:
                print("❌ API 키 오류 또는 서비스 권한 만료")
            elif "resultCode>99" in response.text:
                print("❌ 검색어 입력 오류")
            else:
                print("⚠️ 기타 API 오류 - 응답 내용 확인 필요")
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text}")
    
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")

if __name__ == "__main__":
    test_kipris_api()
