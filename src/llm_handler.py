"""
Gemini API와 통신하는 모든 기능을 담당하는 모듈입니다.
사용자의 질문과 참고 자료를 조합하여 AI에게 분석 및 생성을 요청하는 '두뇌' 역할을 합니다.
"""

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
        주어진 [데이터]와 [분석 요청사항]을 바탕으로, 반드시 아래 [출력 형식]에 맞는 유효한 JSON 객체 하나만 응답으로 생성해야 해.
        JSON 객체 외에 다른 설명이나 텍스트를 절대 포함하면 안 돼.

        [데이터]:
        {data_json_string}

        [분석 요청사항]:
        {user_query}

        [출력 형식]:
        {{
          "analysis_summary": "데이터와 요청사항을 종합하여 분석한 내용을 여기에 마크다운 형식으로 작성.",
          "top_applicants": [
            {{"applicant": "가장 많이 출원한 출원인 이름", "count": 출원 건수}},
            {{"applicant": "두 번째로 많이 출원한 출원인 이름", "count": 출원 건수}}
          ],
          "keywords": ["분석 결과에서 도출된 핵심 기술 키워드 5~10개"]
        }}
        """
        
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return cleaned_response
    except Exception as e:
        # 오류 발생 시에도 JSON 형식을 유지하여 app.py에서 에러 처리를 용이하게 함
        return json.dumps({"error": f"Gemini 분석 중 오류 발생: {e}"})

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
        주어진 [데이터]와 [분석 요청사항]을 바탕으로, 반드시 아래 [출력 형식]에 맞는 유효한 JSON 객체 하나만 응답으로 생성해야 해.
        IPC 코드, 출원인, 연도별 추세를 종합적으로 고려해서 분석해.
        JSON 객체 외에 다른 설명이나 텍스트를 절대 포함하면 안 돼.

        [데이터]:
        {data_json_string}

        [분석 요청사항]:
        {user_query}

        [출력 형식]:
        {{
          "analysis_summary": "데이터와 요청사항을 종합하여 분석한 내용을 여기에 마크다운 형식으로 작성.",
          "top_applicants": [
            {{"applicant": "가장 많이 출원한 출원인 이름", "count": 출원 건수}},
            {{"applicant": "두 번째로 많이 출원한 출원인 이름", "count": 출원 건수}}
          ],
          "keywords": ["분석 결과에서 도출된 핵심 기술 키워드 5~10개"]
        }}
        """
        
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return cleaned_response
    except Exception as e:
        return json.dumps({"error": f"Gemini 분석 중 오류 발생: {e}"})