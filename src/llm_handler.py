import google.generativeai as genai
import json

def summarize_text_with_gemini(api_key, text_to_summarize):
    """Gemini API를 이용해 주어진 텍스트를 요약하는 함수"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"다음 특허 초록 내용을 전문가처럼 한 문단으로 요약해 줘.\n\n초록 내용: {text_to_summarize}"
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API 호출 중 오류 발생: {e}"


def analyze_patent_data_with_gemini(api_key, patent_data_list, user_query):
    """(빠른 분석용) 전체 특허 데이터를 기반으로 사용자의 분석 요청을 처리하는 함수"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        simplified_data = []
        for patent in patent_data_list:
            simplified_data.append({
                "title": patent.get('title'),
                "applicant": patent.get('applicant'),
                "app_date": patent.get('app_date'),
                "reg_status": patent.get('reg_status')
            })
        
        data_json_string = json.dumps(simplified_data, indent=2, ensure_ascii=False)

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
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini 분석 중 오류 발생: {e}"


def analyze_detailed_data_with_gemini(api_key, patent_data_list, user_query):
    """(정밀 분석용) IPC 코드 등 상세 정보가 포함된 전체 특허 데이터를 분석하는 함수"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        simplified_data = []
        for patent in patent_data_list:
            simplified_data.append({
                "title": patent.get('title'),
                "applicant": patent.get('applicant'),
                "app_date": patent.get('app_date'),
                "ipc_code": patent.get('ipc')
            })
        
        data_json_string = json.dumps(simplified_data, indent=2, ensure_ascii=False)

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