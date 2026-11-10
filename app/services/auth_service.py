import os
import hmac
import hashlib
import json
import base64
import time
from typing import Optional
import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.models.user import User

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-perpustakaan-digital-key-2026")
PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER", "SuperSecretPepperValue!#2026")
COOKIE_NAME = "access_token"
TOKEN_EXPIRE_SECONDS = 60 * 60 * 24

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

def hash_password(password: str) -> str:
    peppered = password + PASSWORD_PEPPER
    return ph.hash(peppered)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        peppered = plain_password + PASSWORD_PEPPER
        if hashed_password.startswith("$argon2"):
            return ph.verify(hashed_password, peppered)
        return bcrypt.checkpw(peppered.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, username: str, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{sig_b64}"

def verify_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
        pad = len(sig_b64) % 4
        if pad:
            sig_b64 += "=" * (4 - pad)
        given_sig = base64.urlsafe_b64decode(sig_b64)
        if not hmac.compare_digest(expected_sig, given_sig):
            return None
        payload_pad = len(payload_b64) % 4
        if payload_pad:
            payload_b64 += "=" * (4 - payload_pad)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None

def get_current_user_optional(request: Request, db: Session) -> Optional[User]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        return None
    data = verify_token(token)
    if not data:
        return None
    user_id = str(data.get("sub", ""))
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user

def get_current_user(request: Request, db: Session = next(get_db())):
    user = get_current_user_optional(request, db)
    if not user:
        if "text/html" in request.headers.get("accept", ""):
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/auth/login?next=" + request.url.path}
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Otentikasi diperlukan"
        )
    return user

def require_admin(request: Request, db: Session = next(get_db())):
    user = get_current_user(request, db)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak: Hanya administrator yang diperbolehkan"
        )
    return user
