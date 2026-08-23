from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_image_key: str | None = None
    created_at: datetime
