from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.database import get_db
from app.db.models import User,UserSession
from app.schemas.user_schema import (
    RegistrationRequest,
    LoginRequest,
    VerifyRegistrationOTPRequest,
    ResendRegistrationOTPRequest,
    RefreshTokenRequest,
    LogoutRequest,
    ForgetPasswordRequest,
    VerifyForgetPasswordOTPRequest,
    ResetPasswordRequest
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_token_hash,
    verify_token_hash,
    decode_token
)
from app.core.redis_service import(
     save_registration_data,
     registration_exists,
     get_registration_data,
     delete_registration_data,
     save_otp,
     get_otp,delete_otp,
     start_cooldown,
     cooldown_exists,
     get_login_attempts,
     increment_login_attempt,
     clear_login_attempts,
     get_login_lock_time,
     save_forget_password_session,
     forget_password_exists,
     save_password_reset_verified,
     password_reset_verified_exists,
     delete_password_reset_verified,
     delete_forget_password_session)
from app.core.otp import generate_otp, hash_otp
from app.core.email import send_otp_email
from app.core.config import OTP_RESEND_COOLDOWN,REFRESH_TOKEN_EXPIRE_DAYS,LOGIN_MAX_ATTEMPTS
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
    attempts = get_login_attempts(data.email)
    if attempts >= LOGIN_MAX_ATTEMPTS:
         raise HTTPException(
              status_code = status.HTTP_429_TOO_MANY_REQUESTS,
              detail=f"Too many failed login attempts. Try again after {get_login_lock_time(data.email)}seconds"
         )

    user = db.query(User).filter(User.email == data.email).first()

    #User exists?
    if not user:
        attempts = increment_login_attempt(data.email)
        if attempts >= LOGIN_MAX_ATTEMPTS:
             raise HTTPException(
                  status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                  detail=f"Too many failed login attempts. Try again {get_login_lock_time(data.email)} seconds."
             )
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
        attempts = increment_login_attempt(data.email)
        if attempts >= LOGIN_MAX_ATTEMPTS:
             raise HTTPException(
                  status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                  detail=f"Too many failed login attempts. Try again {get_login_lock_time(data.email)} seconds."
             )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    #Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    clear_login_attempts(data.email)

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
    
    hashed_refresh_token = get_token_hash(refresh_token)
    session = UserSession(
        user_id = user.user_id,
        refresh_token_hash=hashed_refresh_token,
        expires_at=datetime.now(timezone.utc)+ timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()
    return{
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

#verify refresh token and give new access token 
@router.post("/refresh")
def refresh_access_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    payload = decode_token(data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    user_id = payload.get("user_id")
    email = payload.get("sub")
    jti = payload.get("jti")

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    sessions=db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).all()
    
    matched_session = None
    for session in sessions:
        if verify_token_hash(
            data.refresh_token,
            session.refresh_token_hash 
        ):
            matched_session = session
            break

    if matched_session is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Invalid refresh token"
            )
    if matched_session.expires_at < datetime.now(timezone.utc):
            matched_session.is_active = False
            db.commit()

            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
    matched_session.last_used_at = datetime.now(timezone.utc)
    db.commit()
    new_access_token = create_access_token(
            user_id = user.user_id,
            email = user.email,
            role = user.role.value
        )
    return{
            "access_token": new_access_token,
            "token_type": "bearer"
        }

#Logout
@router.post("/logout")
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db)
):
    payload =decode_token(data.refresh_token)
    if  payload is None:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    payload.get('type')=="refresh"
    user_id = payload.get("user_id")
    user = db.query(User).filter(
            User.user_id == user_id
        ).first()

    sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.isactive == True
        ).all()
    matched_session = None
    for session in sessions:
            if verify_token_hash(
                data.refresh_token,
                session.refresh_token_hash
            ):
                matched_session = session
                break
    if matched_session is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Invalid refresh token"
            )
    matched_session.is_active = False
    db.commit()
    return{
            "message": "Logout successful"
        }

#forget password
@router.post("/forget-password")
def forget_password(
     data: ForgetPasswordRequest,
     db: Session = Depends(get_db)
):
     user = db.query(User).filter(
          User.email == data.email

     ).first()
     if not user:
            raise HTTPException(
                 status_code = status.HTTP_404_NOT_FOUND,
                 detail="User not found"
            )
     if not user.is_active:
          raise HTTPException(
               status_code = status.HTTP_403_FORBIDDEN,
               detail="Your account has been deactivated"
          )  
     if not user.email_verified:
            raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Please complete registration first"
            )
     if cooldown_exists(data.email):
          raise HTTPException(
               status_code = status.HTTP_429_TOO_MANY_REQUESTS,
               detail=f"Please wait { OTP_RESEND_COOLDOWN} seconds before requesting another OTP"
          )
     save_forget_password_session(
          data.email
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
          "message":"OTP sent successfully"
     }

@router.post("/verify-forget-password-otp")
def verify_forget_password_otp(
     data: VerifyForgetPasswordOTPRequest,
     db: Session = Depends(get_db)
):
     if not forget_password_exists(data.email):
          raise HTTPException(
               status_code = status.HTTP_400_BAD_REQUEST,
               detail = "Forget password session expired."
          )
     stored_otp_hash = get_otp(data.email)
     if not stored_otp_hash:
          raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="OTP expired"
          )
     entered_otp_hash = hash_otp(data.otp)
     if entered_otp_hash != stored_otp_hash:
          raise HTTPException(
               status_code = status.HTTP_400_BAD_REQUEST,
               detail="Invalid OTP"
          )
     save_password_reset_verified(data.email)
     return{
          "message": "OTP verified successfully"
     }

@router.post("/reset-password")
def reset_password(
     data: ResetPasswordRequest,
     db: Session = Depends(get_db)
):
     if data.new_password != data.confirm_password:
            raise HTTPException(
                 status_code= status.HTTP_400_BAD_REQUEST,
                 detail = "Password do not match"
            )
     validate_password(data.new_password)
     if not password_reset_verified_exists(data.email):
            raise HTTPException(
                 status_code = status.HTTP_400_BAD_REQUEST,
                 detail="OTP verification required"
            )
     user = db.query(User).filter(
          User.email == data.email
     ).first()
     if not user:
            raise HTTPException(
                 status_code = status.HTTP_404_NOT_FOUND,
                 detail = "User not found"
            )
     new_password_hash = get_password_hash(
          data.new_password
     )
     user.password_hash = new_password_hash
     user.updated_at = datetime.now(timezone.utc)
     db.commit()
     db.query(UserSession).filter(
          UserSession.user_id == user.user_id,
          UserSession.is_active == True
     ).update(
          {
               UserSession.is_active: False
          },
          synchronize_session=False
     )
     db.commit()
     delete_password_reset_verified(data.email)
     delete_forget_password_session(data.email)
     delete_otp(data.email)
     return{
          "message": "Password reset successfully. Please login again"
     }
