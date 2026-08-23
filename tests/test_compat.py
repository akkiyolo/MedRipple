import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from main import app
from app.core.database import Base, engine, get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.core.security import hash_password, create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_compat_auth_register_and_login():
    import uuid
    unique_email = f"user_{uuid.uuid4().hex[:8]}@medripple.com"
    # 1. Test POST /api/auth/register
    reg_payload = {
        "email": unique_email,
        "password": "Password123!",
        "role": "PATIENT",
        "name": "Compat Patient",
        "phone": "555-0199"
    }
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code in (200, 201)

    # 2. Test POST /api/auth/login
    login_payload = {
        "email": unique_email,
        "password": "Password123!"
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200

def test_compat_slots_and_booking():
    import uuid
    db = next(get_db())
    doc_email = f"doc_{uuid.uuid4().hex[:8]}@medripple.com"
    pat_email = f"pat_{uuid.uuid4().hex[:8]}@medripple.com"

    doc_user = User(email=doc_email, password_hash=hash_password("Pass123!"), role=UserRole.DOCTOR)
    db.add(doc_user)
    db.commit()
    db.refresh(doc_user)

    doctor = Doctor(user_id=doc_user.id, name="Doc Compat", specialization="General Medicine", slot_duration=30)
    db.add(doctor)
    
    pat_user = User(email=pat_email, password_hash=hash_password("Pass123!"), role=UserRole.PATIENT)
    db.add(pat_user)
    db.commit()
    db.refresh(pat_user)

    patient = Patient(user_id=pat_user.id, name="Pat Compat")
    db.add(patient)
    db.commit()

    # 1. Test GET /api/appointments/slots
    date_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    slots_res = client.get(f"/api/appointments/slots?doctor_id={doctor.id}&date={date_str}")
    assert slots_res.status_code == 200
    res_data = slots_res.json()
    assert "slots" in res_data or "data" in res_data

    # 2. Test POST /api/appointments/book with cookie
    token = create_access_token({"sub": str(pat_user.id), "role": pat_user.role.value})
    client.cookies.set("session_token", token)

    slot_time = f"{date_str}T09:00:00Z"
    book_res = client.post("/api/appointments/book", json={
        "doctor_id": doctor.id,
        "slot_id": slot_time,
        "symptoms": "Test symptoms for compat"
    })
    assert book_res.status_code == 200
    appt_id = book_res.json().get("appointment_id") or book_res.json()["data"]["id"]

    # 3. Test POST /api/intake/{appointment_id}
    intake_res = client.post(f"/api/intake/{appt_id}", json={"symptoms": "Sharp chest tightness"})
    assert intake_res.status_code == 200
    assert "chief_complaint" in intake_res.json() or "summary" in intake_res.json()

    # 4. Test GET /api/doctor/copilot/{appointment_id}
    doc_token = create_access_token({"sub": str(doc_user.id), "role": doc_user.role.value})
    client.cookies.set("session_token", doc_token)
    copilot_res = client.get(f"/api/doctor/copilot/{appt_id}")
    assert copilot_res.status_code == 200

    # 5. Test POST /api/doctor/consultation/{appointment_id}/finalize
    finalize_res = client.post(f"/api/doctor/consultation/{appt_id}/finalize", json={
        "clinical_notes": "Patient has mild bronchitis.",
        "medication": {"name": "Amoxicillin", "dosage": "500mg", "frequency": "Twice daily", "duration": "7 days"}
    })
    assert finalize_res.status_code == 200
