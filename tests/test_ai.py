def test_ai_intake_fallback_and_schema(client, test_patient_user, patient_token):
    res = client.post("/api/v1/ai/intake", json={
        "raw_symptoms": "Mild shortness of breath and chest pressure for 2 days"
    }, headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "chief_complaint" in data
    assert "urgency" in data
    assert "adaptive_questions" in data
    assert isinstance(data["adaptive_questions"], list)

def test_visit_summary_ai(client, test_doctor_user, doctor_token):
    res = client.post("/api/v1/ai/visit-summary", json={
        "clinical_notes": "Patient presents with acute bronchitis. Prescribed amoxicillin 500mg. Advised 5 days rest.",
        "prescriptions_raw": "Amoxicillin 500mg (Twice daily)"
    }, headers={"Authorization": f"Bearer {doctor_token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "patient_friendly_summary" in data
    assert "doctor_instructions" in data
