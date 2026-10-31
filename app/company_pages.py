import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import uuid
from datetime import datetime
from pathlib import Path

from config import *
from utils import *

def company_dashboard():
    """기업 대시보드 메인"""
    # 사이드바
    with st.sidebar:
        st.title(f"🏢 {st.session_state.company_name}")
        
        menu = st.radio(
            "메뉴",
            ["📊 지원자 현황", "🔍 지원자 비교", "🎯 지원자 추천", 
             "📄 채용 공고", "⚖️ 편향성 관리", "❓ 질문 관리", "🔑 면접 코드"],
            label_visibility="collapsed"
        )
        
        st.divider()
        if st.button("로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    # 메인 컨텐츠
    if menu == "📊 지원자 현황":
        applicant_status_page()
    elif menu == "🔍 지원자 비교":
        applicant_comparison_page()
    elif menu == "🎯 지원자 추천":
        applicant_recommendation_page()
    elif menu == "📄 채용 공고":
        job_posting_page()
    elif menu == "⚖️ 편향성 관리":
        bias_management_page()
    elif menu == "❓ 질문 관리":
        question_management_page()
    elif menu == "🔑 면접 코드":
        interview_code_management()

def applicant_status_page():
    """지원자 현황"""
    st.title("📊 지원자 현황")
    
    # 날짜 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("시작일", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("종료일", datetime.now())
    with col3:
        position_filter = st.multiselect("직무 필터", list(JD_DICT.keys()), list(JD_DICT.keys()))
    
    # 데이터 로드
    sessions = []
    try:
        for p in sorted(LOG_DIR.glob("session_*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    s = json.load(f)
                    if s.get("company_id") == st.session_state.company_id:
                        sessions.append(s)
            except:
                continue
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return
    
    # 필터링
    filtered = []
    for s in sessions:
        try:
            ts = datetime.fromisoformat(s["ts"])
            if start_date <= ts.date() <= end_date:
                if s["candidate"]["position"] in position_filter:
                    filtered.append(s)
        except:
            continue
    
    if not filtered:
        st.info(MESSAGES["no_applicants"])
        return
    
    # 통계
    st.markdown("### 📈 요약")
    c1, c2, c3, c4 = st.columns(4)
    scores = [s["summary"]["avg_score"] for s in filtered]
    c1.metric("총 지원자", len(filtered))
    c2.metric("평균 점수", f"{sum(scores)/len(scores):.1f}")
    c3.metric("합격 기준 이상", len([s for s in scores if s >= 60]))
    c4.metric("JD 평균 유사도", f"{sum([s['summary']['jd_similarity'] for s in filtered])/len(filtered):.1f}%")
    
    # 테이블
    rows = []
    for s in filtered:
        c = s["candidate"]
        rows.append({
            "ID": s["session_id"],
            "이름": c["name"],
            "직무": c["position"],
            "점수": s["summary"]["avg_score"],
            "JD유사도": f"{s['summary']['jd_similarity']}%",
            "날짜": s["ts"][:10]
        })
    
    df = pd.DataFrame(rows).sort_values("점수", ascending=False)
    st.dataframe(df, use_container_width=True, height=400)
    
    # 엑셀 다운로드
    if st.button("📥 엑셀 다운로드"):
        excel_file = f"applicants_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            st.download_button(
                "💾 다운로드",
                f,
                file_name=excel_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # 상세 보기
    if st.checkbox("지원자 상세 보기"):
        if len(df) > 0:
            sid = st.selectbox("선택", df["ID"].tolist())
            show_applicant_detail(sid)

def show_applicant_detail(session_id):
    """지원자 상세 정보"""
    try:
        session_file = LOG_DIR / f"session_{session_id}.json"
        if not session_file.exists():
            st.error("세션 파일을 찾을 수 없습니다.")
            return
        
        with open(session_file, "r", encoding="utf-8") as f:
            s = json.load(f)
        
        st.markdown("---")
        st.markdown(f"### 👤 {s['candidate']['name']} - {s['candidate']['position']}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("평균 점수", s["summary"]["avg_score"])
        c2.metric("JD 유사도", f"{s['summary']['jd_similarity']}%")
        c3.metric("대화 수", s["summary"]["turn_count"])
        c4.metric("최고 점수", s["summary"]["max_score"])
        
        # 문서 분석
        if s.get("document_analysis"):
            with st.expander("📄 자기소개서 분석"):
                st.json(s["document_analysis"])
        
        # 대화 기록
        st.markdown("#### 💬 면접 대화")
        for msg in s["conversation"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # 답변별 점수
        st.markdown("#### 📊 답변별 평가")
        df = pd.DataFrame(s["detail"])
        st.dataframe(df, use_container_width=True)
        
        # 다운로드
        st.download_button(
            "📥 리포트 다운로드",
            json.dumps(s, ensure_ascii=False, indent=2),
            f"interview_{session_id}.json"
        )
    except Exception as e:
        st.error(f"오류 발생: {e}")

def applicant_comparison_page():
    """지원자 비교"""
    st.title("🔍 지원자 비교")
    
    sessions = []
    try:
        for p in LOG_DIR.glob("session_*.json"):
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
                if s.get("company_id") == st.session_state.company_id:
                    sessions.append(s)
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return
    
    if len(sessions) < 2:
        st.info("비교할 지원자가 부족합니다 (최소 2명)")
        return
    
    # 직무별 그룹화
    position = st.selectbox("비교할 직무", list(JD_DICT.keys()))
    
    position_sessions = [s for s in sessions if s["candidate"]["position"] == position]
    
    if len(position_sessions) < 2:
        st.warning("해당 직무 지원자가 2명 미만입니다")
        return
    
    # 비교 데이터
    data = []
    for s in position_sessions:
        try:
            detail_scores = {
                "명확성": sum([d.get("명확성", 0) for d in s["detail"]]) / len(s["detail"]),
                "전문성": sum([d.get("전문성", 0) for d in s["detail"]]) / len(s["detail"]),
                "구체성": sum([d.get("구체성", 0) for d in s["detail"]]) / len(s["detail"]),
                "적합성": sum([d.get("적합성", 0) for d in s["detail"]]) / len(s["detail"])
            }
            
            data.append({
                "이름": s["candidate"]["name"],
                "평균점수": s["summary"]["avg_score"],
                "JD유사도": s["summary"]["jd_similarity"],
                **detail_scores
            })
        except:
            continue
    
    if not data:
        st.warning("비교 가능한 데이터가 없습니다")
        return
    
    df = pd.DataFrame(data)
    
    # 막대 차트
    fig1 = px.bar(df, x="이름", y="평균점수", title=f"{position} 지원자 평균 점수")
    st.plotly_chart(fig1, use_container_width=True)
    
    # 레이더 차트
    st.markdown("### 🎯 역량 비교 (상위 3명)")
    top3 = df.nlargest(3, "평균점수")
    
    fig2 = go.Figure()
    for idx, row in top3.iterrows():
        fig2.add_trace(go.Scatterpolar(
            r=[row["명확성"], row["전문성"], row["구체성"], row["적합성"], row["JD유사도"]],
            theta=["명확성", "전문성", "구체성", "적합성", "JD유사도"],
            name=row["이름"]
        ))
    fig2.update_layout(polar=dict(radialaxis=dict(range=[0, 100])))
    st.plotly_chart(fig2, use_container_width=True)

def applicant_recommendation_page():
    """지원자 추천"""
    st.title("🎯 지원자 추천 및 직무 매칭")
    
    st.info("💡 지원자의 역량을 분석하여 가장 적합한 직무를 추천합니다")
    
    sessions = []
    try:
        for p in LOG_DIR.glob("session_*.json"):
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
                if s.get("company_id") == st.session_state.company_id:
                    sessions.append(s)
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return
    
    if not sessions:
        st.info(MESSAGES["no_applicants"])
        return
    
    # 직무별 적합도 분석
    recommendations = []
    for s in sessions:
        try:
            applied_position = s["candidate"]["position"]
            
            # 모든 직무에 대한 적합도 계산
            position_scores = {}
            for position, keywords in JD_DICT.items():
                # 답변에서 키워드 매칭
                answers = " ".join([d["answer"] for d in s["detail"]])
                score = sum(kw.lower() in answers.lower() for kw in keywords) * 10
                position_scores[position] = min(score, 100)
            
            # 상위 3개 추천
            top_positions = sorted(position_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            recommendations.append({
                "이름": s["candidate"]["name"],
                "지원직무": applied_position,
                "추천직무1": top_positions[0][0],
                "적합도1": f"{top_positions[0][1]}%",
                "추천직무2": top_positions[1][0],
                "적합도2": f"{top_positions[1][1]}%",
                "추천직무3": top_positions[2][0],
                "적합도3": f"{top_positions[2][1]}%"
            })
        except:
            continue
    
    if recommendations:
        df = pd.DataFrame(recommendations)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("분석 가능한 데이터가 없습니다")

def job_posting_page():
    """채용 공고 관리"""
    st.title("📄 채용 공고 관리")
    
    companies = load_json(COMPANY_DB)
    company_data = companies.get(st.session_state.company_id, {})
    postings = company_data.get("job_postings", [])
    
    # 공고 등록
    with st.expander("➕ 새 공고 등록"):
        title = st.text_input("공고 제목")
        position = st.selectbox("직무", list(JD_DICT.keys()))
        description = st.text_area("상세 설명")
        
        if st.button("등록", type="primary"):
            if title and description:
                new_posting = {
                    "id": str(uuid.uuid4())[:8],
                    "title": title,
                    "position": position,
                    "description": description,
                    "created": datetime.now().isoformat()
                }
                postings.append(new_posting)
                company_data["job_postings"] = postings
                companies[st.session_state.company_id] = company_data
                save_json(COMPANY_DB, companies)
                st.success("✅ 등록 완료!")
                st.rerun()
            else:
                st.warning("⚠️ 모든 항목을 입력하세요")
    
    # 공고 목록
    st.markdown("### 📋 현재 공고")
    if postings:
        for p in postings:
            with st.expander(f"{p['title']} - {p['position']}"):
                st.write(p['description'])
                st.caption(f"등록일: {p['created'][:10]}")
                if st.button("🗑️ 삭제", key=f"del_{p['id']}"):
                    postings.remove(p)
                    company_data["job_postings"] = postings
                    companies[st.session_state.company_id] = company_data
                    save_json(COMPANY_DB, companies)
                    st.rerun()
    else:
        st.info("등록된 공고가 없습니다")

def bias_management_page():
    """편향성 관리"""
    st.title("⚖️ AI 면접 편향성 관리")
    
    st.markdown("""
    ### 📌 편향성 관리 모드
    AI 면접 시 발생할 수 있는 편향을 최소화하기 위한 설정입니다.
    """)
    
    companies = load_json(COMPANY_DB)
    company_data = companies.get(st.session_state.company_id, {})
    
    bias_mode = st.radio(
        "편향성 관리 수준",
        ["일반", "강화", "최대"],
        index=["normal", "strong", "maximum"].index(company_data.get("bias_mode", "normal"))
    )
    
    st.markdown("""
    - **일반**: 기본 설정
    - **강화**: 성별, 나이 등 민감 정보 제외
    - **최대**: 이름까지 익명화하여 평가
    """)
    
    if st.button("저장", type="primary"):
        mode_map = {"일반": "normal", "강화": "strong", "최대": "maximum"}
        company_data["bias_mode"] = mode_map[bias_mode]
        companies[st.session_state.company_id] = company_data
        save_json(COMPANY_DB, companies)
        st.success("✅ 저장 완료!")

def question_management_page():
    """질문 관리"""
    st.title("❓ 직무별 면접 질문 관리")
    
    questions = load_json(QUESTIONS_DB)
    company_questions = questions.get(st.session_state.company_id, {})
    
    position = st.selectbox("직무 선택", list(JD_DICT.keys()))
    
    # 질문 목록
    position_questions = company_questions.get(position, [])
    
    st.markdown(f"### 📝 {position} 질문 목록")
    
    if position_questions:
        for i, q in enumerate(position_questions):
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(f"{i+1}. {q}")
            with col2:
                if st.button("❌", key=f"del_q_{i}"):
                    position_questions.pop(i)
                    company_questions[position] = position_questions
                    questions[st.session_state.company_id] = company_questions
                    save_json(QUESTIONS_DB, questions)
                    st.rerun()
    else:
        st.info("등록된 질문이 없습니다")
    
    # 새 질문 추가
    with st.expander("➕ 질문 추가"):
        new_q = st.text_input("새 질문")
        if st.button("추가", type="primary"):
            if new_q:
                position_questions.append(new_q)
                company_questions[position] = position_questions
                questions[st.session_state.company_id] = company_questions
                save_json(QUESTIONS_DB, questions)
                st.success("✅ 추가 완료!")
                st.rerun()
            else:
                st.warning("⚠️ 질문을 입력하세요")

def interview_code_management():
    """면접 코드 관리"""
    st.title("🔑 면접 코드 생성 및 관리")
    
    codes = load_json(INTERVIEW_CODES)
    
    # 새 코드 생성
    with st.expander("➕ 새 면접 코드 생성"):
        position = st.selectbox("직무", list(JD_DICT.keys()))
        count = st.number_input("생성 개수", 1, 50, 1)
        
        if st.button("생성", type="primary"):
            for _ in range(count):
                code = generate_code()
                codes[code] = {
                    "company_id": st.session_state.company_id,
                    "position": position,
                    "created": datetime.now().isoformat(),
                    "used": False,
                    "applicant_name": ""
                }
            save_json(INTERVIEW_CODES, codes)
            st.success(f"✅ {count}개 코드 생성 완료!")
            st.rerun()
    
    # 코드 목록
    st.markdown("### 📋 생성된 코드")
    company_codes = {k: v for k, v in codes.items() if v.get("company_id") == st.session_state.company_id}
    
    if not company_codes:
        st.info("생성된 코드가 없습니다")
        return
    
    rows = []
    for code, info in company_codes.items():
        rows.append({
            "코드": code,
            "직무": info["position"],
            "지원자": info.get("applicant_name", "-"),
            "상태": "사용됨" if info["used"] else "미사용",
            "생성일": info["created"][:10]
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    
    # 코드 삭제
    if st.checkbox("🗑️ 코드 삭제"):
        code_to_delete = st.selectbox("삭제할 코드", list(company_codes.keys()))
        if st.button("삭제 확인", type="secondary"):
            del codes[code_to_delete]
            save_json(INTERVIEW_CODES, codes)
            st.success("✅ 삭제 완료!")
            st.rerun()
    
    # 엑셀 다운로드
    if st.button("📥 코드 목록 엑셀 다운로드"):
        excel_file = f"codes_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            st.download_button(
                "💾 다운로드",
                f,
                file_name=excel_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )