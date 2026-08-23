class MedRippleException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(MedRippleException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401)

class AuthorizationError(MedRippleException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR", status_code=403)

class ResourceNotFoundError(MedRippleException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, code="RESOURCE_NOT_FOUND", status_code=404)

class SlotUnavailableError(MedRippleException):
    def __init__(self, message: str = "The selected appointment slot is no longer available"):
        super().__init__(message=message, code="SLOT_UNAVAILABLE", status_code=409)

class AppointmentConflictError(MedRippleException):
    def __init__(self, message: str = "Appointment timing conflict detected"):
        super().__init__(message=message, code="APPOINTMENT_CONFLICT", status_code=409)

class AIServiceError(MedRippleException):
    def __init__(self, message: str = "AI processing service currently unavailable"):
        super().__init__(message=message, code="AI_SERVICE_ERROR", status_code=503)

class CalendarSyncError(MedRippleException):
    def __init__(self, message: str = "Calendar synchronization failed"):
        super().__init__(message=message, code="CALENDAR_SYNC_ERROR", status_code=502)

class NotificationError(MedRippleException):
    def __init__(self, message: str = "Failed to deliver notification"):
        super().__init__(message=message, code="NOTIFICATION_ERROR", status_code=500)

class S3UploadError(MedRippleException):
    def __init__(self, message: str = "S3 file upload failed"):
        super().__init__(message=message, code="S3_UPLOAD_ERROR", status_code=500)

class S3DeleteError(MedRippleException):
    def __init__(self, message: str = "S3 file deletion failed"):
        super().__init__(message=message, code="S3_DELETE_ERROR", status_code=500)

class InvalidImageError(MedRippleException):
    def __init__(self, message: str = "Invalid image file provided"):
        super().__init__(message=message, code="INVALID_IMAGE_ERROR", status_code=400)
