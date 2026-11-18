"""PBKDF2 + JWT: nenhum segredo ou senha em texto puro é armazenado no banco."""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app import config
from app.database import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return base64.urlsafe_b64encode(salt).decode() + ":" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        encoded_salt, encoded_digest = encoded.split(":", 1)
        salt = base64.urlsafe_b64decode(encoded_salt)
        expected = base64.urlsafe_b64decode(encoded_digest)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def hash_device_key(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def authenticate_device(provided: str | None, expected_hash: str) -> bool:
    return bool(provided) and hmac.compare_digest(hash_device_key(provided), expected_hash)

def create_token(user: User) -> str:
    if len(config.JWT_SECRET) < 16:
        raise RuntimeError("JWT_SECRET não configurado")
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user.id), "role": user.role, "iat": now, "exp": now + timedelta(hours=2)}, config.JWT_SECRET, algorithm="HS256")

def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticação obrigatória")
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=["HS256"])
        uid = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    user = db.get(User, uid)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Permissão insuficiente")
    return user
