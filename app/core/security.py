from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta,timezone
from uuid import uuid4
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 OAuth2 scheme (IMPORTANT)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# 🔐 Hash password
def get_password_hash(password: str):
    return pwd_context.hash(password)


# 🔎 Verify password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def generate_jti():
    return str(uuid4())

#Create Token
def create_access_token(
        *,
        user_id: int,
        email: str,
        role: str
):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "user_id": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        "jti": generate_jti()
    }
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def create_refresh_token(
        *,
        user_id: int,
        email: str
):
    now = datetime.now(timezone.utc)
    payload ={
        "sub": email,
        "user_id": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS

        ),
        "jti": generate_jti()
    }
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_token_hash(token: str):
    return pwd_context.hash(token)

def verify_token_hash(
        plain_token: str,
        hashed_token: str
):
    return pwd_context.verify(
        plain_token,
        hashed_token
    )
# 🔓 Decode JWT token
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# 👤 Get current user (THIS IS WHAT PROTECTED ROUTES USE)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    email = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email"
        )

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user