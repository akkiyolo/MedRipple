from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProfileImageResponse(BaseModel):
    user_id: int
    profile_image_key: str | None = None
    presigned_url: str | None = None
    content_type: str | None = None
    size: int | None = None
    uploaded_at: datetime | None = None
