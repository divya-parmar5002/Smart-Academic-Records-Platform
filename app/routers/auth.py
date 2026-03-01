from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schema import (
    SendOTPRequest,
    VerifyOTPRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendOTPRequest
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from app.core.otp import generate_otp, otp_expiry_time
from app.core.email import send_otp_email

router = APIRouter(prefix="/auth", tags=["Auth"])


# ✅ Send OTP
@router.post("/send-otp")
def send_otp(data: SendOTPRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()
    expiry = otp_expiry_time()

    user.otp_code = otp
    user.otp_expiry = expiry
    db.commit()

    send_otp_email(user.email, otp)

    return {"message": "OTP sent successfully"}


# ✅ Verify OTP + Create Password
@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.otp_expiry is None or user.otp_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")

    user.password = get_password_hash(data.password)
    user.is_active = True
    user.otp_code = None
    user.otp_expiry = None

    db.commit()

    return {"message": "Account activated successfully"}


# ✅ Login
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account not activated")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value 
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value
    }

#Forget Password
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid email")

    otp = generate_otp()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.otp_code = otp
    user.otp_expiry = expiry
    db.commit()

    send_otp_email(user.email, otp)

    return {"message": "Reset OTP sent successfully"}

#reset password

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.otp_expiry is None or user.otp_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")

    user.password = get_password_hash(data.new_password)
    user.otp_code = None
    user.otp_expiry = None

    db.commit()

    return {"message": "Password reset successful. Please login again."}


#reset OTP Route
@router.post("/resend-otp")
def resend_otp(data: ResendOTPRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔥 Generate new OTP
    otp = generate_otp()
    expiry = otp_expiry_time()

    user.otp_code = otp
    user.otp_expiry = expiry
    db.commit()

    send_otp_email(user.email, otp)

    return {"message": "New OTP sent successfully"}