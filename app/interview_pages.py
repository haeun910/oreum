import streamlit as st
from datetime import datetime
import json

from ai_engine import analyze_document, generate_interview_question
from evaluation import evaluate_answer_advanced
from utils import load_json, save_json
from config import (
    COMPANY_DB, INTERVIEW_CODES, QUESTIONS_DB, 
    LOG_DIR, MAX_INTERVIEW_TURNS
)

def real_interview_mode():
    """실제 면접 모드 (수정사항 4: 점수 숨김)"""
    st.title(f"💼 {st.session_state.job_position} 면접")
    
    if "interview_step" not in st.session_state:
        st.session_state.interview_step = 0
    
    # Step 0: 정보 입력
    if st.session_state.interview_step == 0:
        show_interview_info_page()
    
    # Step 1: 면접 진행
    elif st.session_state.interview_step == 1:
        conduct_real_interview()
    
    # Step 2: 완료 화면 (수정사항 6: 결과 표시 개선)
    elif st.session_state.interview_step == 2:
        show_real_interview_completion()

def show_interview_info_page():
    """면접 정보 입력 페이지"""
    st.markdown("### 📋 지원자 정보")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름", st.session_state.applicant_name)
        email = st.text_input("이메일")
    with col2:
        phone = st.text_input("연락처")
        major = st.text_input("전공/학력")
    
    st.markdown("### 📄 자기소개서 / 포트폴리오 (선택)")
    uploaded = st.file_uploader("파일 업로드", type=["txt", "pdf"])
    resume_text = st.text_area("또는 직접 입력", height=200)
    
    if st.button("🚀 면접 시작", type="primary"):
        st.session_state.interview_step = 1
        st.session_state.candidate_info = {
            "name": name,
            "email": email,
            "phone": phone,
            "major": major
        }
        
        # 문서 분석
        if uploaded:
            content = uploaded.read().decode("utf-8", errors="ignore")
            st.session_state.resume_text = content
        elif resume_text:
            st.session_state.resume_text = resume_text
        else:
            st.session_state.resume_text = None
        
        if st.session_state.resume_text:
            with st.spinner("📄 문서 분석 중..."):
                st.session_state.document_analysis = analyze_document(
                    st.session_state.resume_text
                )
        else:
            st.session_state.document_analysis = None
        
        # 커스텀 질문 로드
        questions = load_json(QUESTIONS_DB)
        company_questions = questions.get(st.session_state.company_id, {})
        st.session_state.custom_questions = company_questions.get(
            st.session_state.job_position, []
        )
        
        st.session_state.conversation = []
        st.session_state.log = []
        st.session_state.turn_count = 0
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 수정사항 3: AI 실시간 면접 개선
        with st.spinner("🤖 면접 준비 중..."):
            first_q = generate_interview_question(
                [], 
                st.session_state.job_position,
                st.session_state.custom_questions,
                st.session_state.get("document_analysis"),
                0
            )
        
        st.session_state.conversation.append({
            "role": "assistant",
            "content": first_q
        })
        st.session_state.turn_count = 1
        st.rerun()

def conduct_real_interview():
    """실제 면접 진행 (수정사항 4: 점수 숨김)"""
    st.markdown(f"### 💬 면접 진행 중 (질문 {st.session_state.turn_count}/{MAX_INTERVIEW_TURNS})")
    
    # 진행률 표시
    progress = st.session_state.turn_count / MAX_INTERVIEW_TURNS
    st.progress(progress)
    
    # 대화 표시
    for msg in st.session_state.conversation:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # 답변 입력
    user_input = st.chat_input("답변을 입력하세요")
    
    if user_input:
        st.session_state.conversation.append({
            "role": "user",
            "content": user_input
        })
        
        # 평가 (수정사항 4: 점수는 저장만 하고 표시 안함)
        last_q = st.session_state.conversation[-2]["content"]
        score, comment, details, feedback = evaluate_answer_advanced(
            user_input, last_q, st.session_state.job_position
        )
        
        st.session_state.log.append({
            "turn": st.session_state.turn_count,
            "question": last_q,
            "answer": user_input,
            "score": score,
            "comment": comment,
            "feedback": feedback,
            "time": datetime.now().isoformat(),
            **details
        })
        
        # 종료 조건
        max_turns = max(MAX_INTERVIEW_TURNS, len(st.session_state.get("custom_questions", [])))
        
        if st.session_state.turn_count >= max_turns:
            end_msg = "감사합니다. 면접을 마치겠습니다."
            st.session_state.conversation.append({
                "role": "assistant",
                "content": end_msg
            })
            st.session_state.interview_step = 2
            
            # 코드 사용 처리
            codes = load_json(INTERVIEW_CODES)
            if st.session_state.interview_code in codes:
                codes[st.session_state.interview_code]["used"] = True
                codes[st.session_state.interview_code]["applicant_name"] = st.session_state.candidate_info["name"]
                save_json(INTERVIEW_CODES, codes)
            
            # 세션 저장 (수정사항 5, 6: 저장 개선)
            save_real_interview_session()
            st.rerun()
        
        # 다음 질문 (수정사항 3: AI 응답 개선)
        with st.spinner("🤔 다음 질문 준비 중..."):
            next_q = generate_interview_question(
                st.session_state.conversation,
                st.session_state.job_position,
                st.session_state.custom_questions,
                st.session_state.get("document_analysis"),
                st.session_state.turn_count
            )
        
        st.session_state.conversation.append({
            "role": "assistant",
            "content": next_q
        })
        st.session_state.turn_count += 1
        st.rerun()

def save_real_interview_session():
    """실면접 세션 저장 (수정사항 5, 6: 저장 로직 개선)"""
    try:
        scores = [x["score"] for x in st.session_state.log]
        answers = [x["answer"] for x in st.session_state.log]
        
        # JD 유사도
        from config import JD_DICT
        jd_sim = 0
        keywords = JD_DICT.get(st.session_state.job_position, [])
        text = " ".join(answers).lower()
        jd_sim = sum(kw.lower() in text for kw in keywords) * 100 / max(1, len(keywords))
        
        # 회사 정보
        companies = load_json(COMPANY_DB)
        company_name = companies.get(st.session_state.company_id, {}).get("name", "Unknown")
        
        payload = {
            "session_id": st.session_state.session_id,
            "company_id": st.session_state.company_id,
            "company_name": company_name,
            "interview_code": st.session_state.interview_code,
            "ts": datetime.now().isoformat(),
            "candidate": {
                "name": st.session_state.candidate_info["name"],
                "email": st.session_state.candidate_info.get("email", ""),
                "phone": st.session_state.candidate_info.get("phone", ""),
                "major": st.session_state.candidate_info.get("major", ""),
                "position": st.session_state.job_position
            },
            "summary": {
                "avg_score": round(sum(scores)/len(scores), 1) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "jd_similarity": round(jd_sim, 1),
                "turn_count": len(scores)
            },
            "detail": st.session_state.log,
            "conversation": st.session_state.conversation,
            "document_analysis": st.session_state.get("document_analysis")
        }
        
        fn = LOG_DIR / f"session_{st.session_state.session_id}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        print(f"세션 저장 오류: {e}")
        return False

def show_real_interview_completion():
    """면접 완료 화면 (수정사항 6: 결과 표시 개선)"""
    st.success("✅ 면접이 완료되었습니다!")
    
    st.markdown("""
    <style>
    .completion-box {
        padding: 30px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 20px 0;
    }
    </style>
    <div class="completion-box">
        <h2>🎉 수고하셨습니다!</h2>
        <p>면접 결과는 지원하신 회사에서 검토 후 개별 연락드립니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 기본 정보
    companies = load_json(COMPANY_DB)
    company_name = companies.get(st.session_state.company_id, {}).get("name", "")
    
    st.markdown("### 📋 면접 정보")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**회사명:** {company_name}")
        st.info(f"**지원 직무:** {st.session_state.job_position}")
    with col2:
        st.info(f"**지원자:** {st.session_state.candidate_info['name']}")
        st.info(f"**면접 일시:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 수정사항 4: 실제 면접에서는 점수 표시 안함
    st.markdown("### 📊 면접 진행 정보")
    c1, c2 = st.columns(2)
    c1.metric("총 질문 수", len(st.session_state.log))
    c2.metric("소요 시간", f"약 {len(st.session_state.log) * 3}분")
    
    st.markdown("---")
    st.info("💡 **결과 안내**: 면접 결과는 기업 담당자가 검토 후 등록하신 이메일 또는 연락처로 개별 연락드립니다.")
    st.caption("감사합니다!")
    
    if st.button("🏠 홈으로", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()