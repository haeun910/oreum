import streamlit as st
import time
from datetime import datetime
from utils import load_json, save_json, hash_pw
from config import COMPANY_DB, INTERVIEW_CODES, MESSAGES

def main_login_page():
    """메인 로그인 선택 화면"""
    st.markdown("""
    <style>
    .big-title {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 50px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    <div class="big-title">🤖 flex AI 채용 플랫폼</div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 로그인 유형을 선택하세요")
        
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("🏢 기업용 로그인", use_container_width=True, type="primary"):
                st.session_state.login_mode = "company"
                st.rerun()
        
        with c2:
            if st.button("👤 지원자 로그인", use_container_width=True, type="secondary"):
                st.session_state.login_mode = "applicant"
                st.rerun()

def company_login_page():
    """기업용 로그인 (개선됨)"""
    st.title("🏢 기업용 로그인")
    
    companies = load_json(COMPANY_DB)
    
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    
    with tab1:
        st.markdown("### 로그인")
        company_id = st.text_input("기업 ID", key="login_id")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("로그인", type="primary", use_container_width=True):
                if not company_id or not password:
                    st.warning("⚠️ 모든 항목을 입력해주세요")
                elif company_id in companies and companies[company_id]["password"] == hash_pw(password):
                    st.session_state.logged_in = True
                    st.session_state.user_type = "company"
                    st.session_state.company_id = company_id
                    st.session_state.company_name = companies[company_id]["name"]
                    st.success("✅ 로그인 성공!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(MESSAGES["login_failed"])
        
        with col2:
            # 수정사항 1: 회원가입 탭으로 이동 버튼
            if st.button("회원가입", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()
        
        with col3:
            if st.button("← 뒤로", use_container_width=True):
                st.session_state.login_mode = None
                st.rerun()
    
    with tab2:
        st.markdown("### 기업 회원가입")
        new_id = st.text_input("기업 ID", key="new_id")
        company_name = st.text_input("회사명", key="company_name")
        new_pw = st.text_input("비밀번호", type="password", key="new_pw")
        new_pw2 = st.text_input("비밀번호 확인", type="password", key="new_pw2")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("가입하기", type="primary", use_container_width=True):
                if not all([new_id, company_name, new_pw, new_pw2]):
                    st.warning("⚠️ 모든 항목을 입력해주세요")
                elif new_pw != new_pw2:
                    st.error("❌ 비밀번호가 일치하지 않습니다")
                elif len(new_pw) < 6:
                    st.warning("⚠️ 비밀번호는 6자 이상이어야 합니다")
                elif new_id in companies:
                    st.error("❌ 이미 존재하는 기업 ID입니다")
                else:
                    companies[new_id] = {
                        "password": hash_pw(new_pw),
                        "name": company_name,
                        "created": datetime.now().isoformat(),
                        "bias_mode": "normal",
                        "job_postings": []
                    }
                    save_json(COMPANY_DB, companies)
                    st.success(MESSAGES["signup_success"])
                    time.sleep(1)
                    st.rerun()
        
        with col2:
            # 로그인 탭으로 이동
            if st.button("로그인하기", use_container_width=True):
                st.rerun()

def applicant_login_page():
    """지원자 로그인 (개선됨 - 오류 메시지 개선)"""
    st.title("👤 지원자 로그인")
    
    tab1, tab2 = st.tabs(["실제 면접", "연습 면접"])
    
    with tab1:
        st.markdown("### 🎯 실제 면접")
        st.info("💡 기업으로부터 받은 면접 코드를 입력하세요")
        
        interview_code = st.text_input("면접 코드 (8자리)", max_chars=8, key="real_code")
        applicant_name = st.text_input("이름", key="real_name")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("면접 시작", type="primary", use_container_width=True):
                if not interview_code or not applicant_name:
                    st.warning("⚠️ 면접 코드와 이름을 모두 입력해주세요")
                else:
                    codes = load_json(INTERVIEW_CODES)
                    
                    if interview_code not in codes:
                        # 수정사항 2: 오류 코드 숨기고 친절한 메시지
                        st.error(MESSAGES["invalid_code"])
                    elif codes[interview_code].get("used"):
                        st.error(MESSAGES["code_used"])
                    else:
                        code_info = codes[interview_code]
                        st.session_state.logged_in = True
                        st.session_state.user_type = "applicant_real"
                        st.session_state.interview_code = interview_code
                        st.session_state.applicant_name = applicant_name
                        st.session_state.company_id = code_info["company_id"]
                        st.session_state.job_position = code_info["position"]
                        st.success("✅ 면접을 시작합니다!")
                        time.sleep(0.5)
                        st.rerun()
        
        with col2:
            if st.button("← 뒤로", use_container_width=True):
                st.session_state.login_mode = None
                st.rerun()
    
    with tab2:
        st.markdown("### 🎭 연습 면접")
        st.info("💡 면접 연습을 통해 실력을 향상시키세요")
        
        practice_name = st.text_input("이름", key="practice_name")
        practice_position = st.selectbox("연습할 직무", list(JD_DICT.keys()), key="practice_position")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("연습 시작", type="primary", use_container_width=True):
                if not practice_name:
                    st.warning("⚠️ 이름을 입력해주세요")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_type = "applicant_practice"
                    st.session_state.applicant_name = practice_name
                    st.session_state.job_position = practice_position
                    st.success("✅ 연습 모드를 시작합니다!")
                    time.sleep(0.5)
                    st.rerun()
        
        with col2:
            if st.button("← 뒤로", use_container_width=True):
                st.session_state.login_mode = None
                st.rerun()