import secrets
import uuid
from datetime import datetime, timezone, timedelta

from jose import jwt
from passlib.context import CryptContext

from src.core.settings import settings

pwd_context = CryptContext(schemes="bcrypt", deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token() -> tuple[str, str, str]:
    """
    return:
    token_id
    raw_token
    hashed_secret
    """

    token_id = str(uuid.uuid4())

    secret = secrets.token_urlsafe(64)
    raw_token = f"{token_id}:{secret}"

    token_hash = pwd_context.hash(secret)

    return token_id, raw_token, token_hash

def verify_token(secret: str, token_hash: str) -> bool:
    return pwd_context.verify(secret, token_hash)
