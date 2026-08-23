from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import AuthenticationError, MedRippleException
from app.services.audit_service import AuditService

class AuthService:
    @staticmethod
    def request_password_reset(db: Session, email: str) -> None:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return
        token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = hash_password(token)
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()
        from app.services.notification_service import NotificationService
        NotificationService.create_and_dispatch_notification(
            db, user.email, "PASSWORD_RESET", "MedRipple password reset",
            f"Use this one-time password reset token within 30 minutes: {token}"
        )

    @staticmethod
    def reset_password(db: Session, email: str, token: str, new_password: str) -> None:
        user = db.query(User).filter(User.email == email.lower()).first()
        now = datetime.now(timezone.utc)
        expires_at = user.password_reset_expires_at if user else None
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if not user or not user.password_reset_token_hash or not expires_at or expires_at < now:
            raise AuthenticationError("Invalid or expired password reset token")
        if not verify_password(token, user.password_reset_token_hash):
            raise AuthenticationError("Invalid or expired password reset token")
        if len(new_password) < 8:
            raise MedRippleException("Password must be at least 8 characters", code="WEAK_PASSWORD", status_code=400)
        user.password_hash = hash_password(new_password)
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        db.commit()

    @staticmethod
    def register_user(db: Session, req: RegisterRequest) -> User:
        existing = db.query(User).filter(User.email == req.email.lower()).first()
        if existing:
            raise MedRippleException("User with this email already exists", code="EMAIL_EXISTS", status_code=400)

        hashed = hash_password(req.password)
        user = User(
            email=req.email.lower(),
            password_hash=hashed,
            role=req.role,
            is_active=True
        )
        db.add(user)
        db.flush()

        if req.role == UserRole.PATIENT:
            patient = Patient(
                user_id=user.id,
                name=req.name,
                phone=req.phone
            )
            db.add(patient)
        elif req.role == UserRole.DOCTOR:
            if not req.specialization:
                raise MedRippleException("Doctor specialization is required", code="MISSING_SPECIALIZATION", status_code=400)
            doctor = Doctor(
                user_id=user.id,
                name=req.name,
                specialization=req.specialization,
                license_number=req.license_number
            )
            db.add(doctor)
            db.flush()
            
            # Automatically set default Mon-Fri 9-5 schedule
            from datetime import time
            from app.models.doctor_schedule import DoctorSchedule
            for day in range(5):
                schedule = DoctorSchedule(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    is_active=True
                )
                db.add(schedule)
                
        elif req.role == UserRole.ADMIN:
            pass

        db.commit()
        db.refresh(user)
        AuditService.log(db, action="USER_REGISTERED", resource_type="User", user_id=user.id, resource_id=str(user.id))
        return user

    @staticmethod
    def authenticate_user(db: Session, req: LoginRequest) -> TokenResponse:
        user = db.query(User).filter(User.email == req.email.lower()).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        access_token = create_access_token(data=token_data)

        AuditService.log(db, action="USER_LOGGED_IN", resource_type="User", user_id=user.id, resource_id=str(user.id))
        return TokenResponse(
            access_token=access_token,
            user_id=user.id,
            email=user.email,
            role=user.role
        )
