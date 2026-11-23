from rest_framework.test import APIClient


def test_isolation_and_date_filter(user_a, readings_a, readings_b):
    c = APIClient()
    c.force_authenticate(user_a)
    assert c.get("/api/v1/readings/").data["count"] == 2
    from datetime import date, timedelta
    frm = (date.today() - timedelta(days=5)).isoformat()
    assert c.get(f"/api/v1/readings/?from={frm}").data["count"] == 1
    other = readings_b[0].id
    assert c.get(f"/api/v1/readings/{other}/").status_code == 404
