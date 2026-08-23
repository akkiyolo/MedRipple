import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorSchedule
from app.core.security import hash_password

def seed():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Patient
        patient_email = "patient@medripple.com"
        patient_user = db.query(User).filter(User.email == patient_email).first()
        if not patient_user:
            patient_user = User(
                email=patient_email,
                password_hash=hash_password("Password123!"),
                role=UserRole.PATIENT,
                is_active=True
            )
            db.add(patient_user)
            db.flush()

            patient = Patient(
                user_id=patient_user.id,
                name="John Doe",
                phone="+15550199",
                gender="Male"
            )
            db.add(patient)
            print(f"Created Patient Account: {patient_email}")

        # 2. Seed Doctor
        doctor_email = "doctor@medripple.com"
        doctor_user = db.query(User).filter(User.email == doctor_email).first()
        if not doctor_user:
            doctor_user = User(
                email=doctor_email,
                password_hash=hash_password("Password123!"),
                role=UserRole.DOCTOR,
                is_active=True
            )
            db.add(doctor_user)
            db.flush()

            doctor = Doctor(
                user_id=doctor_user.id,
                name="Sarah Connor",
                specialization="Pulmonology",
                license_number="MD-887799",
                bio="Board-certified Pulmonologist specializing in respiratory disorders.",
                slot_duration=30
            )
            db.add(doctor)
            db.flush()

            # Seed default weekly schedule for Doctor (Mon - Fri, 9am - 5pm)
            from datetime import time
            for day in range(5):  # 0: Mon ... 4: Fri
                sched = DoctorSchedule(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    is_active=True
                )
                db.add(sched)
            print(f"Created Doctor Account: {doctor_email}")

        # 3. Seed Admin
        admin_email = "admin@medripple.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                password_hash=hash_password("Password123!"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            print(f"Created Admin Account: {admin_email}")

        db.commit()
        print("\nDatabase Seeding Complete! Demo Accounts Ready:")
        print("--------------------------------------------------")
        print("Patient:  patient@medripple.com  / Password123!")
        print("Doctor:   doctor@medripple.com   / Password123!")
        print("Admin:    admin@medripple.com    / Password123!")
        print("--------------------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
