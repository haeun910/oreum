from config import JD_DICT, SCORE_WEIGHTS

def evaluate_answer_advanced(answer, question, position):
    """
    개선된 평가 시스템 (0-100점)
    - 명확성, 전문성, 구체성, 적합성 4개 항목
    - 더 엄격한 기준 적용
    """
    
    # 기본 검증
    if not answer or len(answer.strip()) < 10:
        return 0, "⚠️ 답변이 너무 짧습니다.", {}, "최소 10자 이상 작성해주세요."
    
    # 불성실 답변 체크
    ignore_words = ["모르", "ㅋㅋ", "ㅎㅎ", "글쎄", "몰라", "아무", "대충"]
    if any(w in answer.lower() for w in ignore_words):
        return 0, "❌ 불성실한 답변입니다.", {}, "성실하게 답변해주세요."
    
    score = 0
    feedback = []
    
    # 1. 명확성 (0-25점) - 더 엄격하게
    clarity = 0
    answer_len = len(answer.strip())
    
    if answer_len >= 50: clarity += 5
    if answer_len >= 150: clarity += 7
    if answer_len >= 300: clarity += 5
    
    sentences = answer.count('.') + answer.count('!') + answer.count('?')
    if sentences >= 3: clarity += 4
    if sentences >= 5: clarity += 2
    
    # 불필요한 단어 감점
    filler_words = ["음", "어", "그", "저", "뭐"]
    filler_count = sum(answer.count(w) for w in filler_words)
    clarity -= min(filler_count * 2, 8)
    
    clarity = max(0, min(clarity, 25))
    
    # 2. 전문성 (0-25점) - 키워드 매칭 강화
    tech_keywords = JD_DICT.get(position, [])
    tech_score = 0
    
    # 직무 관련 키워드
    matched_keywords = [kw for kw in tech_keywords if kw.lower() in answer.lower()]
    tech_score += len(matched_keywords) * 4
    
    # 추가 기술 키워드
    extra_tech = ["github", "git", "aws", "docker", "k8s", "ci/cd", "agile", "scrum"]
    tech_score += sum(2 for t in extra_tech if t in answer.lower())
    
    tech_score = min(tech_score, 25)
    
    # 3. 구체성 (0-25점) - 수치, 사례 강조
    specificity = 0
    
    # 경험 키워드
    exp_keywords = ["프로젝트", "경험", "담당", "수행", "개발", "진행", "구현", "설계"]
    specificity += sum(3 for k in exp_keywords if k in answer) 
    
    # 숫자 포함 (구체적 지표)
    if any(char.isdigit() for char in answer):
        specificity += 5
    
    # 단위 포함 (%, 건, 명, 개월, 년 등)
    units = ["%", "건", "명", "개월", "년", "일", "시간", "배", "개"]
    specificity += sum(2 for u in units if u in answer)
    
    # 구체적 사례 언급
    case_words = ["예를들어", "사례", "당시", "이전", "~했을때"]
    specificity += sum(3 for w in case_words if w in answer)
    
    specificity = min(specificity, 25)
    
    # 4. 적합성 (0-25점) - 역할/기여도 평가
    relevance = 10  # 기본 점수
    
    relevance_kw = ["역할", "기여", "책임", "성과", "결과", "목표", "달성", "해결", "개선"]
    relevance += sum(2 for k in relevance_kw if k in answer)
    
    # 팀워크 언급
    if any(w in answer for w in ["팀", "협업", "함께", "동료"]):
        relevance += 3
    
    # 부정적 단어 감점
    vague_words = ["대충", "그냥", "좀", "아마"]
    relevance -= sum(3 for w in vague_words if w in answer)
    
    relevance = max(0, min(relevance, 25))
    
    # 총점 계산
    total = clarity + tech_score + specificity + relevance
    
    # 피드백 생성
    if clarity < 15:
        feedback.append("답변을 더 명확하고 구체적으로 작성하세요")
    if tech_score < 12:
        feedback.append(f"{position} 관련 기술이나 도구를 구체적으로 언급하세요")
    if specificity < 12:
        feedback.append("숫자, 기간 등 구체적 지표를 포함하세요")
    if relevance < 12:
        feedback.append("본인의 역할과 기여도를 명확히 설명하세요")
    
    # 종합 코멘트
    if total >= 80:
        comment = "⭐ 탁월한 답변입니다!"
    elif total >= 65:
        comment = "✅ 좋은 답변입니다."
    elif total >= 45:
        comment = "📝 괜찮지만 더 구체적으로 설명해주세요."
    elif total >= 25:
        comment = "⚠️ 답변이 부족합니다. 더 자세히 작성하세요."
    else:
        comment = "❌ 답변을 다시 작성해주세요."
    
    details = {
        "명확성": round(clarity, 1),
        "전문성": round(tech_score, 1),
        "구체성": round(specificity, 1),
        "적합성": round(relevance, 1)
    }
    
    feedback_text = " | ".join(feedback) if feedback else "잘 작성하셨습니다!"
    
    return round(total, 1), comment, details, feedback_text