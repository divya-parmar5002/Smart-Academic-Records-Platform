from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User, UserRoleEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")

    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account")

    return user


# 🔐 Teacher Only Access
def require_teacher(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRoleEnum.teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")
    return current_user


# 🎓 Student Only Access
def require_student(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRoleEnum.student:
        raise HTTPException(status_code=403, detail="Student access required")
    return current_user

from fastapi import Depends, HTTPException, status
from app.dependencies.auth_dependency import get_current_user
from app.db.models import User


def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user