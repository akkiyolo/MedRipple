from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.image_service import ImageService
from app.schemas.image import ProfileImageResponse

router = APIRouter(prefix="/profile", tags=["Profile Image"])

@router.post("/image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_bytes = await file.read()
    presigned_url = ImageService.upload_profile_image(
        db,
        user=current_user,
        file_bytes=file_bytes,
        content_type=file.content_type or "image/jpeg",
        filename=file.filename or "profile.jpg"
    )
    resp = ProfileImageResponse(
        user_id=current_user.id,
        profile_image_key=current_user.profile_image_key,
        presigned_url=presigned_url,
        content_type=current_user.profile_image_content_type,
        size=current_user.profile_image_size,
        uploaded_at=current_user.profile_image_uploaded_at
    )
    return {"success": True, "data": resp.model_dump(), "message": "Profile image uploaded successfully"}

@router.get("/image")
def get_profile_image(current_user: User = Depends(get_current_user)):
    url = ImageService.get_profile_image_url(current_user)
    resp = ProfileImageResponse(
        user_id=current_user.id,
        profile_image_key=current_user.profile_image_key,
        presigned_url=url,
        content_type=current_user.profile_image_content_type,
        size=current_user.profile_image_size,
        uploaded_at=current_user.profile_image_uploaded_at
    )
    return {"success": True, "data": resp.model_dump(), "message": "Profile image fetched"}

@router.delete("/image")
def delete_profile_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ImageService.delete_profile_image(db, current_user)
    return {"success": True, "data": None, "message": "Profile image deleted successfully"}
