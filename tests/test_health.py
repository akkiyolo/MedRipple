def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_health_db(client):
    res = client.get("/api/v1/health/db")
    assert res.status_code == 401
