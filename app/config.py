import os
from pathlib import Path

# ==================== 디렉토리 설정 ====================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

COMPANY_DB = Path("companies.json")
INTERVIEW_CODES = Path("interview_codes.json")
QUESTIONS_DB = Path("custom_questions.json")

# ==================== API 설정 ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ==================== 직무 정의 (JD) ====================
JD_DICT = {
    "백엔드 개발": ["API", "DB", "서버", "Spring", "Node.js", "REST", "SQL", "Docker", "Kubernetes"],
    "프론트엔드 개발": ["React", "Vue", "JavaScript", "TypeScript", "CSS", "HTML", "Next.js", "Webpack"],
    "데이터 분석": ["Python", "SQL", "Pandas", "통계", "시각화", "머신러닝", "Tableau"],
    "데이터 엔지니어": ["Spark", "Hadoop", "Kafka", "Airflow", "ETL", "AWS", "GCP"],
    "기획": ["요구사항", "분석", "PRD", "PM", "기획서", "와이어프레임", "로드맵"],
    "마케팅": ["캠페인", "SEO", "SNS", "분석", "고객", "브랜딩", "퍼포먼스"],
    "디자인": ["UI", "UX", "Figma", "Sketch", "프로토타입", "사용자경험"]
}

# ==================== 면접 설정 ====================
MAX_INTERVIEW_TURNS = 5  # 면접 질문 수
PASS_SCORE = 60  # 합격 기준 점수

# ==================== 평가 기준 ====================
SCORE_WEIGHTS = {
    "명확성": 25,
    "전문성": 25,
    "구체성": 25,
    "적합성": 25
}

# ==================== UI 메시지 ====================
MESSAGES = {
    "no_applicants": "📭 아직 지원자가 없습니다.",
    "no_practice_records": "🎭 연습 기록이 없습니다. 면접을 연습해보세요!",
    "invalid_code": "❌ 유효하지 않은 면접 코드입니다.",
    "code_used": "❌ 이미 사용된 면접 코드입니다.",
    "login_failed": "❌ 아이디 또는 비밀번호가 올바르지 않습니다.",
    "signup_success": "✅ 회원가입이 완료되었습니다! 로그인해주세요.",
}