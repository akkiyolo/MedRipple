from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.appointment import Appointment
from app.core.config import settings

class GoogleCalendarService:
    @staticmethod
    def get_credentials(user: User):
        if not user.google_access_token or not user.google_refresh_token:
            return None
            
        return Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

    @staticmethod
    def create_event(db: Session, user: User, appointment: Appointment):
        creds = GoogleCalendarService.get_credentials(user)
        if not creds:
            return False
            
        try:
            service = build("calendar", "v3", credentials=creds)
            
            end_time = appointment.end_time
            if not end_time:
                # Default 30 mins
                import datetime as dt
                end_time = appointment.start_time + dt.timedelta(minutes=30)
                
            event = {
                "summary": f"Medical Appointment with Dr. {appointment.doctor.name}" if user.role.value == "PATIENT" else f"Consultation with Patient {appointment.patient.name}",
                "location": "MedRipple Telehealth" if appointment.appointment_type.value == "VIRTUAL" else "MedRipple Clinic",
                "description": f"Notes: {appointment.notes or 'No notes provided.'}",
                "start": {
                    "dateTime": appointment.start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},
                        {"method": "popup", "minutes": 30},
                    ],
                },
            }
            
            created_event = service.events().insert(calendarId="primary", body=event).execute()
            
            # Save the google event id to the appointment model if we want to sync updates/deletes later
            # For now just return true
            return True
            
        except Exception as e:
            from app.core.logging import logger
            logger.error(f"Error creating Google Calendar event for user {user.id}: {e}")
            return False
