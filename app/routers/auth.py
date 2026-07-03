from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schema import (
    RegistrationRequest,
    LoginRequest,
    VerifyRegistrationOTPRequest,
    ResendRegistrationOTPRequest
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_token_hash
)
from app.core.redis_service import(save_registration_data,registration_exists,get_registration_data,delete_registration_data,save_otp,get_otp,delete_otp,start_cooldown,cooldown_exists)
from app.core.otp import generate_otp, hash_otp
from app.core.email import send_otp_email
from app.core.config import OTP_RESEND_COOLDOWN
from app.core.password_validator import validate_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register/request-otp")
def request_registration_otp(
    data: RegistrationRequest,
    db: Session = Depends(get_db)
):
    # Password validation
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    validate_password(data.password)

    # Find user
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    

    # Check role
    if user.role != data.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    # Account active?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated"
        )

    # Already registered?
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered. Please login."
        )

    if user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered."
        )

    # Cooldown check
    if cooldown_exists(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {OTP_RESEND_COOLDOWN} seconds before requesting another OTP."
        )

    # Hash password
    password_hash = get_password_hash(data.password)

    # Save registration session
    save_registration_data(
        email=data.email,
        data={
            "password_hash": password_hash,
            "role": data.role.value
        }
    )

    # Generate OTP
    otp = generate_otp()
    otp_hash = hash_otp(otp)

    # Save OTP
    save_otp(
        email=data.email,
        otp_hash=otp_hash
    )

    # Start cooldown
    start_cooldown(data.email)

    # Send email
    send_otp_email(
        data.email,
        otp
    )

    return {
        "message": "OTP sent successfully."
    }
#verify OTP endpoint
@router.post("/register/verify-otp")
def verify_registration_otp(
    data: VerifyRegistrationOTPRequest,
    db: Session = Depends(get_db)
):
    # Registration session
    registration_data = get_registration_data(data.email)

    if not registration_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration session expired. Please register again."
        ) 

    # OTP
    stored_otp_hash = get_otp(data.email)

    if not stored_otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please request a new OTP."
        )

    entered_otp_hash = hash_otp(data.otp)

    if entered_otp_hash != stored_otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP."
        )

    # Find user
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
   

    # Update user
    user.password_hash = registration_data["password_hash"]
    user.email_verified = True
    user.updated_at = datetime.now(timezone.utc)

    db.commit()

    # Clear Redis
    delete_registration_data(data.email)
    delete_otp(data.email)

    return {
        "message": "Registration completed successfully."
    }

#Resend OTP

@router.post("/register/resend-otp")
def resend_registration_otp(
    data: ResendRegistrationOTPRequest
):
    registration_data=get_registration_data(data.email)
    if not registration_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration session expired. Please register again"
        )
    if cooldown_exists(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {OTP_RESEND_COOLDOWN} seconds before requesting another OTP."
        )
    otp = generate_otp()
    otp_hash = hash_otp(otp)

    save_otp(
        email=data.email,
        otp_hash=otp_hash
    )
    start_cooldown(data.email)
    send_otp_email(
        data.email,
        otp
    )
    return{
        "message":"OTP resent successfully."
    }



#  Login
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    #User exists?
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )
    #Account active?
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                             detail="Your account has been deactivated.")

    #Email verified?
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete your registration first."
        )
    
    # Verify password
    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    #Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    #Create access token
    access_token = create_access_token(
       user_id=user.user_id,
       email=user.email,
       role=user.role.value
    )
    
    refresh_token = create_refresh_token(
       user_id = user.user_id,
       email = user.email
   )
    

