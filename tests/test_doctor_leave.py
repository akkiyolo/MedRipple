from datetime import date, timedelta

def test_apply_doctor_leave(client, test_doctor_user, doctor_token):
    headers = {"Authorization": f"Bearer {doctor_token}"}
    start_date = (date.today() + timedelta(days=10)).isoformat()
    end_date = (date.today() + timedelta(days=12)).isoformat()

    response = client.post("/api/v1/doctors/me/leave", json={
        "start_date": start_date,
        "end_date": end_date,
        "reason": "Attending Medical Conference"
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["start_date"] == start_date
