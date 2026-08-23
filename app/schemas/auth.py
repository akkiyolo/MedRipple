from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.PATIENT
    name: str
    phone: str | None = None
    specialization: str | None = None  # Required if DOCTOR
    license_number: str | None = None  # Optional for DOCTOR

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: UserRole

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
    is_active: bool
    profile_image_key: str | None = None
