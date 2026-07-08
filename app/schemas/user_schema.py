from pydantic import BaseModel, EmailStr
from app.db.models import UserRoleEnum

#Regiatration
class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password:str
    role: UserRoleEnum

#Verify Registration OTP request
class VerifyRegistrationOTPRequest(BaseModel):
    email:EmailStr
    otp:str    

#Resend OTP
class ResendRegistrationOTPRequest(BaseModel):
    email: EmailStr       


# ✅ Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str    

class LogoutRequest(BaseModel):
    refresh_token: str    

class ForgetPasswordRequest(BaseModel):
    email: EmailStr

class VerifyForgetPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp: str    

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str



class CreateUserRequest(BaseModel):
    email: str
    password: str


class AssignSubjectRequest(BaseModel):
    subject_id: int
    teacher_id: int
    year: int
    semester: int
    section: str      