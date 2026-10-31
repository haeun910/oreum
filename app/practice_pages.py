import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

from ai_engine import analyze_document, generate_interview_question
from evaluation import evaluate_answer_advanced
from utils import load_json, save_json
from config import LOG_DIR, JD_DICT, MAX_INTERVIEW_TURNS, MESSAGES

def practice_mode():
    """연습 모드 메인"""
    with st.sidebar:
        st.title(f"👤 {st.session_state.applicant_name}")
        
        menu = st.radio(
            "메뉴",
            ["🎭 연습 면접", "📊 점수 분석", "💡 피드백", "🎯 직무 추천", "📝 자소서 분석"],
            label_visibility="collapsed"
        )
        
        st.divider()
        if st.button("로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    if menu == "🎭 연습 면접":
        practice_interview_page()
    elif menu == "📊 점수 분석":
        practice_score_analysis()
    elif menu == "💡 피드백":
        practice_feedback_page()
    elif menu == "🎯 직무 추천":
        practice_job_recommendation()
    elif menu == "📝 자소서 분석":
        practice_resume_analysis()

def practice_interview_page():
    """연습 면접 (수정사항 5: 기록 저장 개선)"""
    st.title("🎭 면접 연습")
    
    if "practice_step" not in st.session_state:
        st.session_state.practice_step = 0
    
    if st.session_state.practice_step == 0:
        st.info("💡 실제 면접처럼 연습해보세요. 답변은 저장되어 분석됩니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 연습 시작", type="primary", use_container_width=True):
                st.session_state.practice_step = 1
                st.session_state.conversation = []
                st.session_state.log = []
                st.session_state.turn_count = 0
                st.session_state.session_id = f"practice_{st.session_state.applicant_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 첫 질문
                with st.spinner("🤖 준비 중..."):
                    first_q = generate_interview_question(
                        [], st.session_state.job_position, None, None, 0
                    )
                
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": first_q
                })
                st.session_state.turn_count = 1
                st.rerun()
        
        with col2:
            if st.button("← 뒤로", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
    
    elif st.session_state.practice_step == 1:
        conduct_practice_interview()
    
    elif st.session_state.practice_step == 2:
        show_practice_completion()

def conduct_practice_interview():
    """연습 면접 진행"""
    st.markdown(f"### 💬 연습 중 (질문 {st.session_state.turn_count}/{MAX_INTERVIEW_TURNS})")
    
    # 진행률
    progress = st.session_state.turn_count / MAX_INTERVIEW_TURNS
    st.progress(progress)
    
    # 대화
    for msg in st.session_state.conversation:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # 입력
    user_input = st.chat_input("답변을 입력하세요")
    
    if user_input:
        st.session_state.conversation.append({
            "role": "user",
            "content": user_input
        })
        
        # 평가
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
        
        # 즉시 피드백 표시 (연습 모드에서만)
        with st.chat_message("assistant"):
            st.write(f"**{comment}** ({score}점)")
            if feedback:
                st.caption(f"💡 {feedback}")
        
        # 종료 조건
        if st.session_state.turn_count >= MAX_INTERVIEW_TURNS:
            st.session_state.practice_step = 2
            
            # 수정사항 5: 저장 로직 개선
            save_practice_session()
            st.rerun()
        
        # 다음 질문
        with st.spinner("🤔"):
            next_q = generate_interview_question(
                st.session_state.conversation,
                st.session_state.job_position,
                None, None,
                st.session_state.turn_count
            )
        
        st.session_state.conversation.append({
            "role": "assistant",
            "content": next_q
        })
        st.session_state.turn_count += 1
        st.rerun()

def save_practice_session():
    """연습 세션 저장 (수정사항 5: 저장 개선)"""
    try:
        scores = [x["score"] for x in st.session_state.log]
        answers = [x["answer"] for x in st.session_state.log]
        
        jd_sim = 0
        keywords = JD_DICT.get(st.session_state.job_position, [])
        text = " ".join(answers).lower()
        jd_sim = sum(kw.lower() in text for kw in keywords) * 100 / max(1, len(keywords))
        
        payload = {
            "session_id": st.session_state.session_id,
            "type": "practice",
            "username": st.session_state.applicant_name,
            "ts": datetime.now().isoformat(),
            "candidate": {
                "name": st.session_state.applicant_name,
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
            "conversation": st.session_state.conversation
        }
        
        fn = LOG_DIR / f"session_{st.session_state.session_id}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        print(f"연습 세션 저장 오류: {e}")
        return False

def show_practice_completion():
    """연습 완료 화면"""
    st.success("✅ 연습 완료!")
    
    scores = [x["score"] for x in st.session_state.log]
    avg = sum(scores)/len(scores) if scores else 0
    
    # 수정사항 4: 연습 모드에서는 점수 표시
    st.markdown("### 📊 연습 결과")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("평균 점수", f"{avg:.1f}점")
    c2.metric("최고 점수", f"{max(scores)}점")
    c3.metric("최저 점수", f"{min(scores)}점")
    c4.metric("합격 여부", "✅ 합격" if avg >= 60 else "⚠️ 불합격")
    
    # 상세 피드백
    st.markdown("### 💡 답변별 피드백")
    for log in st.session_state.log:
        with st.expander(f"질문 {log['turn']}: {log['score']}점 - {log['comment']}"):
            st.write(f"**Q:** {log['question']}")
            st.write(f"**A:** {log['answer']}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("명확성", f"{log.get('명확성', 0)}/25")
            col2.metric("전문성", f"{log.get('전문성', 0)}/25")
            col3.metric("구체성", f"{log.get('구체성', 0)}/25")
            col4.metric("적합성", f"{log.get('적합성', 0)}/25")
            
            if log['feedback']:
                st.warning(f"💡 **개선점:** {log['feedback']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 연습", type="primary", use_container_width=True):
            st.session_state.practice_step = 0
            st.rerun()
    with col2:
        if st.button("📊 분석 보기", use_container_width=True):
            st.session_state.practice_step = 0
            st.rerun()

def practice_score_analysis():
    """점수 분석 (수정사항 5: 기록 표시 개선)"""
    st.title("📊 나의 연습 점수 분석")
    
    # 내 연습 기록 로드
    sessions = []
    try:
        for p in LOG_DIR.glob("session_practice_*.json"):
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
                if s.get("username") == st.session_state.applicant_name:
                    sessions.append(s)
    except Exception:
        pass
    
    if not sessions:
        st.info(MESSAGES["no_practice_records"])
        return
    
    # 통계
    scores = [s["summary"]["avg_score"] for s in sessions]
    st.markdown("### 📈 전체 통계")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 연습 수", len(sessions))
    c2.metric("평균 점수", f"{sum(scores)/len(scores):.1f}")
    c3.metric("최고 점수", f"{max(scores):.1f}")
    c4.metric("최근 점수", f"{scores[-1]:.1f}")
    
    # 추이 그래프
    fig = px.line(
        x=range(1, len(scores)+1),
        y=scores,
        labels={"x": "연습 회차", "y": "평균 점수"},
        title="📈 점수 추이"
    )
    fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="합격선 (60점)")
    fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="우수 (80점)")
    st.plotly_chart(fig, use_container_width=True)
    
    # 연습 기록 리스트
    st.markdown("### 📋 연습 기록")
    records = []
    for s in sessions:
        records.append({
            "날짜": s["ts"][:10],
            "시간": s["ts"][11:16],
            "직무": s["candidate"]["position"],
            "평균점수": s["summary"]["avg_score"],
            "질문수": s["summary"]["turn_count"]
        })
    
    df = pd.DataFrame(records)
    st.dataframe(df.sort_values("날짜", ascending=False), use_container_width=True)

def practice_feedback_page():
    """종합 피드백"""
    st.title("💡 종합 피드백")
    
    sessions = []
    try:
        for p in LOG_DIR.glob("session_practice_*.json"):
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
                if s.get("username") == st.session_state.applicant_name:
                    sessions.append(s)
    except Exception:
        pass
    
    if not sessions:
        st.info(MESSAGES["no_practice_records"])
        return
    
    # 최근 세션 분석
    latest = sessions[-1]
    
    st.markdown("### 🎯 최근 연습 분석")
    
    # 카테고리별 평균
    categories = {"명확성": [], "전문성": [], "구체성": [], "적합성": []}
    for log in latest["detail"]:
        for cat in categories:
            categories[cat].append(log.get(cat, 0))
    
    cat_avg = {k: sum(v)/len(v) if v else 0 for k, v in categories.items()}
    
    # 강점과 약점
    sorted_cats = sorted(cat_avg.items(), key=lambda x: x[1])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ 강점")
        for cat, score in sorted_cats[-2:]:
            st.success(f"**{cat}**: {score:.1f}점")
    
    with col2:
        st.markdown("#### ⚠️ 개선 필요")
        for cat, score in sorted_cats[:2]:
            st.warning(f"**{cat}**: {score:.1f}점")
            
            if cat == "명확성":
                st.write("💡 답변을 더 길고 명확하게 작성하세요")
            elif cat == "전문성":
                st.write(f"💡 {st.session_state.job_position} 관련 기술을 구체적으로 언급하세요")
            elif cat == "구체성":
                st.write("💡 숫자, 기간 등 구체적 지표를 포함하세요")
            elif cat == "적합성":
                st.write("💡 본인의 역할과 기여도를 명확히 하세요")

def practice_job_recommendation():
    """직무 추천"""
    st.title("🎯 맞춤 직무 추천")
    
    st.info("💡 연습 결과를 분석하여 적합한 직무를 추천합니다")
    
    sessions = []
    try:
        for p in LOG_DIR.glob("session_practice_*.json"):
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
                if s.get("username") == st.session_state.applicant_name:
                    sessions.append(s)
    except Exception:
        pass
    
    if not sessions:
        st.warning(MESSAGES["no_practice_records"])
        return
    
    # 전체 답변 분석
    all_answers = []
    for s in sessions:
        for log in s["detail"]:
            all_answers.append(log["answer"])
    
    text = " ".join(all_answers).lower()
    
    # 직무별 매칭 점수
    position_scores = {}
    for position, keywords in JD_DICT.items():
        score = sum(kw.lower() in text for kw in keywords) * 10
        position_scores[position] = min(score, 100)
    
    # 상위 3개
    top = sorted(position_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    st.markdown("### 📋 추천 직무")
    for i, (pos, score) in enumerate(top, 1):
        if i == 1:
            st.success(f"**{i}. {pos}** - 적합도 {score}% 🏆")
        else:
            st.info(f"**{i}. {pos}** - 적합도 {score}%")

def practice_resume_analysis():
    """자소서 분석"""
    st.title("📝 자기소개서 분석 및 피드백")
    
    resume_text = st.text_area("자기소개서를 입력하세요", height=300)
    
    if st.button("🔍 분석하기", type="primary"):
        if resume_text:
            with st.spinner("📄 분석 중..."):
                analysis = analyze_document(resume_text)
            
            st.success("✅ 분석 완료!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✨ 강점")
                for s in analysis.get("강점", []):
                    st.success(f"✓ {s}")
                
                st.markdown("### 🎯 핵심역량")
                for s in analysis.get("핵심역량", []):
                    st.info(f"• {s}")
            
            with col2:
                st.markdown("### ⚠️ 보완점")
                for s in analysis.get("보완점", []):
                    st.warning(f"• {s}")
                
                st.markdown("### 💼 추천직무")
                for s in analysis.get("추천직무", []):
                    st.success(f"→ {s}")
        else:
            st.warning("⚠️ 자기소개서를 입력해주세요")