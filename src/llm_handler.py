import google.generativeai as genai

def summarize_text_with_gemini(api_key, text_to_summarize):
    """Gemini API를 이용해 주어진 텍스트를 요약하는 함수"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')

        prompt = f"다음 특허 초록 내용을 전문가처럼 한 문단으로 요약해 줘.\n\n초록 내용: {text_to_summarize}"

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API 호출 중 오류 발생: {e}"