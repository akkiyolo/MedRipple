from datetime import datetime, timedelta, timezone

def test_hold_and_book_appointment(client, test_patient_user, test_doctor_user, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    doctor_id = test_doctor_user.doctor_profile.id
    start_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    # 1. Hold Slot
    hold_resp = client.post("/api/v1/appointments/hold", json={
        "doctor_id": doctor_id,
        "start_time": start_time
    }, headers=headers)
    assert hold_resp.status_code == 200
    hold_data = hold_resp.json()["data"]
    hold_id = hold_data["id"]

    # 2. Book Appointment using Hold
    book_resp = client.post("/api/v1/appointments", json={
        "doctor_id": doctor_id,
        "start_time": start_time,
        "hold_id": hold_id,
        "reason": "Persistent dry cough",
        "symptoms": "Cough for 3 days"
    }, headers=headers)
    assert book_resp.status_code == 200
    book_data = book_resp.json()["data"]
    assert book_data["status"] == "CONFIRMED"

def test_double_booking_prevention(client, test_patient_user, test_doctor_user, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    doctor_id = test_doctor_user.doctor_profile.id
    start_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # First booking
    res1 = client.post("/api/v1/appointments", json={
        "doctor_id": doctor_id,
        "start_time": start_time,
        "reason": "First booking"
    }, headers=headers)
    assert res1.status_code == 200

    # Second booking for same doctor & time should fail with 409 Conflict
    res2 = client.post("/api/v1/appointments", json={
        "doctor_id": doctor_id,
        "start_time": start_time,
        "reason": "Conflicting booking"
    }, headers=headers)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "SLOT_UNAVAILABLE"
