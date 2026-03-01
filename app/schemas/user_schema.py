from pydantic import BaseModel, EmailStr


# ✅ Send OTP
class SendOTPRequest(BaseModel):
    email: EmailStr


# ✅ Verify OTP + Create Password
class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    password: str


# ✅ Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ✅ Forgot Password
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# ✅ Reset Password
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

#reset OTP
class ResendOTPRequest(BaseModel):
    email: EmailStr  

class CreateUserRequest(BaseModel):
    email: str
    password: str


class AssignSubjectRequest(BaseModel):
    subject_id: int
    teacher_id: int
    year: int
    semester: int
    section: str      