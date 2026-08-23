import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.s3_service import s3_service
from app.core.exceptions import InvalidImageError
from app.services.audit_service import AuditService

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

class ImageService:
    @staticmethod
    def validate_image(file_bytes: bytes, content_type: str, filename: str):
        if len(file_bytes) > MAX_FILE_SIZE:
            raise InvalidImageError("File size exceeds maximum limit of 5 MB.")
        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise InvalidImageError("Invalid content type. Only JPEG, PNG, and WEBP images are allowed.")

        # Magic byte signature check
        if content_type == "image/jpeg" and not file_bytes.startswith(b"\xff\xd8\xff"):
            raise InvalidImageError("File content does not match JPEG format.")
        elif content_type == "image/png" and not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise InvalidImageError("File content does not match PNG format.")
        elif content_type == "image/webp" and not (file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"):
            raise InvalidImageError("File content does not match WEBP format.")

    @classmethod
    def upload_profile_image(
        cls,
        db: Session,
        user: User,
        file_bytes: bytes,
        content_type: str,
        filename: str
    ) -> str:
        cls.validate_image(file_bytes, content_type, filename)

        # Generate safe UUID key
        ext = "jpg" if content_type == "image/jpeg" else ("png" if content_type == "image/png" else "webp")
        role_folder = "doctors" if user.role.value == "DOCTOR" else "users"
        object_key = f"{role_folder}/{user.id}/profile/{uuid.uuid4()}.{ext}"

        # Delete previous image key if safe
        old_key = user.profile_image_key

        # Upload to S3
        s3_service.upload_file(file_bytes, object_key, content_type)

        # Update DB state
        user.profile_image_key = object_key
        user.profile_image_content_type = content_type
        user.profile_image_size = len(file_bytes)
        user.profile_image_uploaded_at = datetime.now(timezone.utc)
        db.commit()

        # Delete old key after database commit success
        if old_key:
            try:
                s3_service.delete_file(old_key)
            except Exception:
                pass

        AuditService.log(db, action="PROFILE_IMAGE_UPLOADED", resource_type="User", user_id=user.id, resource_id=str(user.id))
        return s3_service.generate_presigned_url(object_key)

    @classmethod
    def get_profile_image_url(cls, user: User) -> str:
        if not user.profile_image_key:
            return "/static/images/default_avatar.svg"
        return s3_service.generate_presigned_url(user.profile_image_key)

    @classmethod
    def delete_profile_image(cls, db: Session, user: User) -> bool:
        if not user.profile_image_key:
            return True
        old_key = user.profile_image_key
        s3_service.delete_file(old_key)
        user.profile_image_key = None
        user.profile_image_content_type = None
        user.profile_image_size = None
        user.profile_image_uploaded_at = None
        db.commit()

        AuditService.log(db, action="PROFILE_IMAGE_DELETED", resource_type="User", user_id=user.id, resource_id=str(user.id))
        return True
