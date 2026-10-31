import json
import hashlib
import random
import string
from pathlib import Path

def load_json(path, default=None):
    """JSON 파일 로드"""
    if default is None:
        default = {}
    
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def save_json(path, data):
    """JSON 파일 저장"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"저장 오류: {e}")
        return False

def hash_pw(pw):
    """비밀번호 해시화"""
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_code(length=8):
    """면접 코드 생성"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def safe_get(dictionary, key, default=None):
    """안전한 딕셔너리 접근"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, KeyError):
        return default