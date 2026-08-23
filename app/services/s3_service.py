import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.core.config import settings
from app.core.exceptions import S3UploadError, S3DeleteError
from app.core.logging import logger

class S3Service:
    def __init__(self):
        self._s3_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self._s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
            except Exception as e:
                logger.warning(f"S3 client initialization warning: {e}")

    def upload_file(self, file_bytes: bytes, object_key: str, content_type: str) -> str:
        if not self._s3_client:
            logger.info(f"S3 credentials not configured. Mocking upload for key {object_key}")
            return object_key
        try:
            self._s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type
            )
            return object_key
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 upload error for {object_key}: {e}")
            raise S3UploadError(f"Failed to upload object to S3: {str(e)}")

    def delete_file(self, object_key: str) -> bool:
        if not self._s3_client or not object_key:
            return True
        try:
            self._s3_client.delete_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=object_key
            )
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 delete error for {object_key}: {e}")
            raise S3DeleteError(f"Failed to delete object from S3: {str(e)}")

    def generate_presigned_url(self, object_key: str, expiration: int | None = None) -> str:
        if not object_key:
            return ""
        if not self._s3_client:
            # Fallback mock presigned URL for development/demo
            return f"/static/images/default_avatar.svg"
        if expiration is None:
            expiration = settings.AWS_S3_PRESIGNED_URL_EXPIRY
        try:
            url = self._s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.AWS_S3_BUCKET, "Key": object_key},
                ExpiresIn=expiration
            )
            return url
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Presigned URL generation error for {object_key}: {e}")
            return f"/static/images/default_avatar.svg"

    def object_exists(self, object_key: str) -> bool:
        if not self._s3_client or not object_key:
            return False
        try:
            self._s3_client.head_object(Bucket=settings.AWS_S3_BUCKET, Key=object_key)
            return True
        except ClientError:
            return False

s3_service = S3Service()
