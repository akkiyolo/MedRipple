from fastapi import APIRouter, Depends, Response, Cookie, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService.register_user(db, req)
    return {"success": True, "data": {"id": user.id, "email": user.email, "role": user.role.value}, "message": "Registration successful"}

@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    token_resp = AuthService.authenticate_user(db, req)
    # Set HTTP-only session cookie for web UI
    response.set_cookie(key="session_token", value=token_resp.access_token, httponly=True, max_age=86400, samesite="lax")
    
    # Determine redirect based on role
    role_val = token_resp.role.value
    redirect_url = "/doctor/dashboard" if role_val == "DOCTOR" else "/admin/dashboard" if role_val == "ADMIN" else "/patient/dashboard"
    
    return {"success": True, "data": token_resp.model_dump(), "redirect_url": redirect_url, "message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"success": True, "data": None, "message": "Logged out successfully"}

@router.post("/refresh")
def refresh(current_user: User = Depends(get_current_user)):
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(current_user.id), "email": current_user.email, "role": current_user.role.value})
    return {"success": True, "data": {"access_token": token, "token_type": "bearer"}, "message": "Token refreshed"}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AuthService.request_password_reset(db, req.email)
    return {"success": True, "data": None, "message": "If that account exists, password reset instructions have been sent."}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService.reset_password(db, req.email, req.reset_token, req.new_password)
    return {"success": True, "data": None, "message": "Password reset successfully"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": {"id": current_user.id, "email": current_user.email, "role": current_user.role.value, "is_active": current_user.is_active}, "message": "User profile fetched"}
