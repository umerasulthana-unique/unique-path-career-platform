import os, base64, hashlib, hmac
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY=os.getenv('SECRET_KEY','development-secret-change-me')
ALGORITHM='HS256'

def hash_password(password: str) -> str:
    salt=os.urandom(16)
    digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 120000)
    return base64.b64encode(salt+digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        raw=base64.b64decode(stored.encode()); salt, digest=raw[:16], raw[16:]
        check=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 120000)
        return hmac.compare_digest(check,digest)
    except Exception: return False

def create_token(user_id:int, role:str):
    payload={'sub':str(user_id),'role':role,'exp':datetime.now(timezone.utc)+timedelta(hours=12)}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def decode_token(token:str):
    return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
