import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path

# 모듈 임포트
from config import *
from utils import *
from auth import *
from ai_engine import *
from evaluation import *
from company_pages import *
from interview_pages import *
from practice_pages import *

# ==================== 페이지 설정 ====================

st.set_page_config(
    page_title="flex AI 채용 플랫폼",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 메인 앱 ====================

def main():
    """메인 애플리케이션"""
    
    # 세션 초기화
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    # 로그인 상태 확인
    if not st.session_state.logged_in:
        if "login_mode" not in st.session_state or st.session_state.login_mode is None:
            main_login_page()
        elif st.session_state.login_mode == "company":
            company_login_page()
        elif st.session_state.login_mode == "applicant":
            applicant_login_page()
        return
    
    # 사용자 타입별 라우팅
    if st.session_state.user_type == "company":
        company_dashboard()
    elif st.session_state.user_type == "applicant_real":
        real_interview_mode()
    elif st.session_state.user_type == "applicant_practice":
        practice_mode()

# ==================== 실행 ====================

if __name__ == "__main__":
    main()