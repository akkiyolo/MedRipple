import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.appointment import Appointment
from app.core.config import settings
from app.core.logging import logger

RETRY_INTERVALS_SECONDS = [30, 120, 600]  # Attempt 2: 30s, Attempt 3: 2m, Attempt 4: 10m

class NotificationService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
            logger.info(f"Email credentials not configured. Mocking email to {to_email}: {subject}")
            return True

        try:
            # If the user provides a SendGrid API key, bypass Render SMTP blocks via HTTPS REST API
            if settings.EMAIL_PASSWORD.startswith("SG."):
                import httpx
                headers = {
                    "Authorization": f"Bearer {settings.EMAIL_PASSWORD}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
                    "from": {"email": settings.EMAIL_FROM},
                    "content": [{"type": "text/plain", "value": body}]
                }
                response = httpx.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
                
                if response.status_code >= 400:
                    logger.error(f"SendGrid API Error: {response.status_code} - {response.text}")
                    return False
                return True

            # Otherwise, use standard SMTP (Which fails on Render Free Tier but works locally)
            msg = MIMEMultipart()
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            if settings.EMAIL_PORT == 465:
                # Use SSL directly for port 465
                with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                    server.send_message(msg)
            else:
                # Use STARTTLS for 587 or others
                with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    server.starttls()
                    server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
                    server.send_message(msg)
                    
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    def create_and_dispatch_notification(
        cls,
        db: Session,
        recipient: str,
        type_: str,
        subject: str,
        body: str,
        event_id: str | None = None
    ) -> Notification:
        notif = Notification(
            event_id=event_id,
            recipient=recipient,
            channel=NotificationChannel.EMAIL,
            type=type_,
            status=NotificationStatus.PENDING,
            attempt_count=1,
            last_attempt_at=datetime.now(timezone.utc)
        )
        db.add(notif)
        db.commit()

        success = cls.send_email(recipient, subject, body)
        if success:
            notif.status = NotificationStatus.SENT
        else:
            notif.status = NotificationStatus.RETRYING
            notif.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=RETRY_INTERVALS_SECONDS[0])
            notif.error_message = "SMTP delivery error on initial attempt"

        db.commit()
        db.refresh(notif)
        return notif

    @classmethod
    def retry_pending_notifications(cls, db: Session) -> int:
        now_utc = datetime.now(timezone.utc)
        retryables = db.query(Notification).filter(
            Notification.status == NotificationStatus.RETRYING,
            Notification.next_retry_at <= now_utc
        ).all()

        retried_count = 0
        for notif in retryables:
            notif.attempt_count += 1
            notif.last_attempt_at = now_utc

            success = cls.send_email(notif.recipient, f"Reminder: {notif.type}", f"Notification message body for {notif.type}")
            if success:
                notif.status = NotificationStatus.SENT
            else:
                if notif.attempt_count >= 4:
                    notif.status = NotificationStatus.FAILED
                    notif.error_message = "Max retry attempts exceeded"
                else:
                    interval_idx = min(notif.attempt_count - 1, len(RETRY_INTERVALS_SECONDS) - 1)
                    notif.next_retry_at = now_utc + timedelta(seconds=RETRY_INTERVALS_SECONDS[interval_idx])

            retried_count += 1

        db.commit()
        return retried_count

    @classmethod
    def trigger_appointment_created_event(cls, db: Session, appt: Appointment):
        if appt.patient and appt.patient.user:
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.patient.user.email,
                type_="APPOINTMENT_CONFIRMED_PATIENT",
                subject="MedRipple: Appointment Confirmation",
                body=f"Dear {appt.patient.name},\nYour appointment with Dr. {appt.doctor.name} is confirmed for {appt.start_time.strftime('%Y-%m-%d %H:%M UTC')}.\n\nThank you,\nMedRipple Team",
                event_id=f"appt_{appt.id}_p"
            )
        if appt.doctor and appt.doctor.user:
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.doctor.user.email,
                type_="APPOINTMENT_CONFIRMED_DOCTOR",
                subject="MedRipple: New Consultation Booked",
                body=f"Dear Dr. {appt.doctor.name},\nA new appointment with {appt.patient.name} has been booked for {appt.start_time.strftime('%Y-%m-%d %H:%M UTC')}.\nReason: {appt.reason or 'Not specified'}\n\nPlease review the patient brief in your dashboard.\n\nThank you,\nMedRipple Team",
                event_id=f"appt_{appt.id}_d"
            )

    @classmethod
    def trigger_appointment_cancelled_event(cls, db: Session, appt: Appointment):
        if appt.patient and appt.patient.user:
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.patient.user.email,
                type_="APPOINTMENT_CANCELLED_PATIENT",
                subject="MedRipple: Appointment Cancelled",
                body=f"Dear {appt.patient.name},\nYour appointment scheduled for {appt.start_time.strftime('%Y-%m-%d %H:%M UTC')} has been cancelled.",
                event_id=f"appt_cancel_{appt.id}_p"
            )
        if appt.doctor and appt.doctor.user:
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.doctor.user.email,
                type_="APPOINTMENT_CANCELLED_DOCTOR",
                subject="MedRipple: Consultation Cancelled",
                body=f"Dear Dr. {appt.doctor.name},\nYour appointment with {appt.patient.name} on {appt.start_time.strftime('%Y-%m-%d %H:%M UTC')} has been cancelled. This slot has been freed in your schedule.",
                event_id=f"appt_cancel_{appt.id}_d"
            )

    @classmethod
    def trigger_appointment_reminder_event(cls, db: Session, appt: Appointment):
        if appt.patient and appt.patient.user:
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.patient.user.email,
                type_="APPOINTMENT_REMINDER_PATIENT",
                subject="MedRipple Reminder: Upcoming Visit",
                body=f"Dear {appt.patient.name},\nThis is a reminder for your appointment with Dr. {appt.doctor.name} scheduled for {appt.start_time.strftime('%Y-%m-%d %H:%M UTC')}.\n\nThank you,\nMedRipple Team",
                event_id=f"appt_remind_{appt.id}_p"
            )
        if appt.doctor and appt.doctor.user:
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.doctor.user.email,
                type_="APPOINTMENT_REMINDER_DOCTOR",
                subject="MedRipple Reminder: Upcoming Consultation",
                body=f"Dear Dr. {appt.doctor.name},\nThis is a reminder for your upcoming consultation with {appt.patient.name} on {appt.start_time.strftime('%Y-%m-%d %H:%M UTC')}.",
                event_id=f"appt_remind_{appt.id}_d"
            )

    @classmethod
    def send_leave_reschedule_notification(cls, db: Session, appt: Appointment, alternative_slots: list[dict]):
        if appt.patient and appt.patient.user:
            slots_summary = "\n".join([f"- {s['doctor_name']}: {s['start_time']}" for s in alternative_slots[:3]])
            cls.create_and_dispatch_notification(
                db,
                recipient=appt.patient.user.email,
                type_="DOCTOR_LEAVE_RESCHEDULE",
                subject="MedRipple: Doctor Leave Notice & Rescheduling Options",
                body=f"Dear {appt.patient.name},\nDr. {appt.doctor.name} is on leave. Your appointment on {appt.start_time.strftime('%Y-%m-%d')} needs to be rescheduled.\n\nRecommended alternative slots:\n{slots_summary}\n\nPlease log in to select your replacement slot.",
                event_id=f"leave_resched_{appt.id}"
            )
