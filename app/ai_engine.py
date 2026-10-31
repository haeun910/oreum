import json
import google.generativeai as genai
from config import GEMINI_API_KEY, JD_DICT

# Gemini 설정
try:
    genai.configure(api_key=GEMINI_API_KEY)
    AI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ AI 설정 오류: {e}")
    AI_AVAILABLE = False

def get_default_analysis():
    """기본 분석 결과"""
    return {
        "핵심역량": ["문서 분석 중..."],
        "주요경험": [],
        "기술스택": [],
        "강점": ["자기소개서를 작성해주세요"],
        "보완점": ["구체적인 경험을 추가하세요"],
        "추천직무": []
    }

def analyze_document(text, doc_type="자기소개서"):
    """문서 분석 (자기소개서/포트폴리오)"""
    if not AI_AVAILABLE or not text:
        return get_default_analysis()
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""다음 {doc_type}를 분석하세요:

{text[:2000]}

반드시 다음 JSON 형식으로만 출력하세요:
{{
    "핵심역량": ["역량1", "역량2", "역량3"],
    "주요경험": ["경험1", "경험2"],
    "기술스택": ["기술1", "기술2"],
    "강점": ["강점1", "강점2"],
    "보완점": ["보완점1", "보완점2"],
    "추천직무": ["직무1", "직무2"]
}}

JSON만 출력하고 다른 설명은 하지 마세요."""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # JSON 추출
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        
        return json.loads(result)
    
    except Exception as e:
        print(f"문서 분석 오류: {e}")
        return get_default_analysis()

def generate_interview_question(conversation, position, custom_questions=None, document_analysis=None, turn=0):
    """AI 면접 질문 생성"""
    
    # 첫 질문
    if turn == 0:
        if custom_questions and len(custom_questions) > 0:
            return custom_questions[0]
        
        if document_analysis:
            skills = ', '.join(document_analysis.get('핵심역량', [])[:3])
            if skills and skills != "문서 분석 중...":
                return f"안녕하세요. {position} 직무에 지원하셨는데, {skills} 관련 경험을 간단히 소개해주세요."
        
        return f"안녕하세요. {position} 직무에 지원하게 된 동기를 말씀해주세요."
    
    # 커스텀 질문 사용
    if custom_questions and turn < len(custom_questions):
        return custom_questions[turn]
    
    # AI 질문 생성
    if not AI_AVAILABLE:
        return get_fallback_question(position, turn)
    
    try:
        # 이전 답변 추출
        last_answer = ""
        for msg in reversed(conversation):
            if msg["role"] == "user":
                last_answer = msg["content"]
                break
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""당신은 {position} 직무 면접관입니다.

지원자의 이전 답변: "{last_answer}"

다음 규칙을 따라 질문하세요:
1. 답변이 짧으면 구체적 사례를 요구하세요
2. 프로젝트가 언급되면 역할과 기여도를 물어보세요
3. 기술이 언급되면 실제 사용 경험을 물어보세요
4. 50자 이내로 간결하게 질문하세요
5. 한국어로 작성하세요

질문만 출력하고 다른 설명은 하지 마세요."""
        
        response = model.generate_content(prompt)
        question = response.text.strip()
        
        # 불필요한 문자 제거
        question = question.replace('"', '').replace("'", '').strip()
        
        return question
    
    except Exception as e:
        print(f"질문 생성 오류: {e}")
        return get_fallback_question(position, turn)

def get_fallback_question(position, turn):
    """AI 실패 시 기본 질문"""
    fallback_questions = {
        "백엔드 개발": [
            "간단히 자기소개를 해주세요.",
            "최근 진행한 백엔드 프로젝트를 설명해주세요.",
            "API 설계 경험이 있나요?",
            "데이터베이스 최적화 경험을 말씀해주세요.",
            "가장 어려웠던 기술적 문제는 무엇이었나요?"
        ],
        "프론트엔드 개발": [
            "간단히 자기소개를 해주세요.",
            "React나 Vue 사용 경험이 있나요?",
            "반응형 웹 디자인 구현 경험을 말씀해주세요.",
            "성능 최적화를 위해 어떤 노력을 했나요?",
            "가장 어려웠던 UI 구현은 무엇이었나요?"
        ],
        "데이터 분석": [
            "간단히 자기소개를 해주세요.",
            "Python으로 진행한 분석 프로젝트를 설명해주세요.",
            "어떤 시각화 도구를 사용해봤나요?",
            "데이터 전처리 경험을 말씀해주세요.",
            "통계 지식을 실무에 어떻게 적용했나요?"
        ]
    }
    
    default_questions = [
        "간단히 자기소개를 해주세요.",
        "최근 프로젝트를 설명해주세요.",
        "가장 자신있는 기술이나 역량은 무엇인가요?",
        "팀 프로젝트 경험을 말씀해주세요.",
        "이 직무에 지원한 이유는 무엇인가요?"
    ]
    
    questions = fallback_questions.get(position, default_questions)
    return questions[min(turn, len(questions) - 1)]