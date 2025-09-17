# Gemini API와 통신하는 모든 기능을 담당하는 모듈입니다.
# 사용자의 질문과 참고 자료를 조합하여 AI에게 분석 및 생성을 요청하는 '두뇌' 역할을 합니다.

# --- 1. 기본 라이브러리 임포트 ---
import google.generativeai as genai  # Google Gemini API 라이브러리
import json                         # 파이썬 딕셔너리를 JSON 문자열로 변환하기 위해 사용

# --- 2. 개별 특허 초록 요약 함수 ---
def summarize_text_with_gemini(api_key, text_to_summarize):
    """
    Gemini API를 이용해 주어진 텍스트(특허 초록)를 요약하는 함수입니다.

    Args:
        api_key (str): Gemini API 키.
        text_to_summarize (str): 요약할 원본 텍스트.

    Returns:
        str: Gemini가 생성한 요약 텍스트 또는 오류 메시지.
    """
    try:
        # API 키를 사용하여 Gemini 라이브러리를 설정합니다.
        genai.configure(api_key=api_key)
        # 사용할 AI 모델을 지정합니다. 'gemini-1.5-flash'는 빠르고 경제적인 최신 모델입니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # AI에게 어떤 역할을 해야 할지, 무엇을 해야 할지 지시하는 '프롬프트'를 생성합니다.
        prompt = f"다음 특허 초록 내용을 전문가처럼 한 문단으로 요약해 줘.\n\n초록 내용: {text_to_summarize}"
        
        # 생성된 프롬프트를 AI 모델에 보내고 응답을 받습니다.
        response = model.generate_content(prompt)
        # 응답 받은 내용에서 텍스트 부분만 추출하여 반환합니다.
        return response.text
    except Exception as e:
        # API 호출 중 문제가 발생하면, 사용자에게 오류 메시지를 반환합니다.
        return f"Gemini API 호출 중 오류 발생: {e}"

# --- 3. 빠른 분석 함수 ---
def analyze_patent_data_with_gemini(api_key, patent_data_list, user_query):
    """
    (빠른 분석용) 여러 특허의 기본 데이터를 기반으로 사용자의 분석 요청을 처리하는 함수입니다.

    Args:
        api_key (str): Gemini API 키.
        patent_data_list (list): 분석할 특허 데이터가 담긴 딕셔너리 리스트.
        user_query (str): 사용자가 입력한 분석 요청 내용.

    Returns:
        str: Gemini가 생성한 분석 리포트 또는 오류 메시지.
    """
    try:
        # API 키 설정 및 모델 지정
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # AI에게 전달할 데이터를 가볍게 만들기 위해, 각 특허에서 핵심 정보만 추출합니다.
        # 긴 초록 내용은 제외하여 API 토큰 사용량을 줄이고 분석의 핵심에 집중하도록 합니다.
        simplified_data = []
        for patent in patent_data_list:
            simplified_data.append({
                "title": patent.get('title'),
                "applicant": patent.get('applicant'),
                "app_date": patent.get('app_date'),
                "reg_status": patent.get('reg_status')
            })
        
        # 파이썬 리스트/딕셔너리 데이터를 AI가 이해하기 쉬운 JSON 문자열 형태로 변환합니다.
        # indent=2는 가독성을 높여주고, ensure_ascii=False는 한글이 깨지지 않게 합니다.
        data_json_string = json.dumps(simplified_data, indent=2, ensure_ascii=False)

        # AI에게 역할을 부여하고, 참고 자료(데이터)와 사용자의 요청을 명확히 전달하는 프롬프트를 생성합니다.
        prompt = f"""
        너는 최고의 특허 데이터 분석 전문가(Patent Analyst)야.

        아래는 특정 키워드로 검색된 특허 데이터 목록 전체야.
        ---
        [데이터]
        {data_json_string}
        ---

        이 전체 데이터를 바탕으로, 아래의 [분석 요청사항]을 심층적으로 분석하고, 그 결과를 명확하고 이해하기 쉽게 정리해서 답변해 줘.

        [분석 요청사항]
        {user_query}
        """
        
        # 프롬프트를 모델에 보내고 응답을 받아 텍스트를 반환합니다.
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini 분석 중 오류 발생: {e}"

# --- 4. 정밀 분석 함수 ---
def analyze_detailed_data_with_gemini(api_key, patent_data_list, user_query):
    """
    (정밀 분석용) IPC 코드 등 상세 정보가 포함된 전체 특허 데이터를 분석하는 함수입니다.

    Args:
        api_key (str): Gemini API 키.
        patent_data_list (list): 상세 정보가 포함된 특허 데이터 리스트.
        user_query (str): 사용자가 입력한 분석 요청 내용.

    Returns:
        str: Gemini가 생성한 심층 분석 리포트 또는 오류 메시지.
    """
    try:
        # API 키 설정 및 모델 지정
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 정밀 분석을 위해 'ipc_code'와 같은 추가 정보를 포함하여 데이터를 가공합니다.
        simplified_data = []
        for patent in patent_data_list:
            simplified_data.append({
                "title": patent.get('title'),
                "applicant": patent.get('applicant'),
                "app_date": patent.get('app_date'),
                "ipc_code": patent.get('ipc') # 기술 분류 코드 정보 추가
            })
        
        data_json_string = json.dumps(simplified_data, indent=2, ensure_ascii=False)

        # 프롬프트를 '정밀 분석'에 맞게 더 구체적으로 지시합니다.
        # IPC 코드, 연도별 추세 등을 종합적으로 고려하라고 명시하여 더 높은 수준의 분석을 유도합니다.
        prompt = f"""
        너는 최고의 특허 데이터 분석 전문가(Patent Analyst)야.

        아래는 특정 키워드로 검색된 특허 데이터 목록 전체야. 각 특허는 IPC 기술 분류 코드를 포함하고 있어.
        ---
        [데이터]
        {data_json_string}
        ---

        이 전체 데이터를 바탕으로, 아래의 [분석 요청사항]을 IPC 기술 분류 동향, 출원인 동향, 연도별 추세 등을 종합적으로 고려하여 심층적으로 분석하고, 그 결과를 전문가 리포트 형식으로 작성해 줘.

        [분석 요청사항]
        {user_query}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini 분석 중 오류 발생: {e}"
