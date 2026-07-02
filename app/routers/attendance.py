# attendance.py

from fastapi import APIRouter, Depends
from app.dependencies.auth_dependency import get_current_user
from app.db.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/test-auth")
def test_auth(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}