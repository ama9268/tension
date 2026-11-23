import pytest

ORIGIN = "https://app1.com"


@pytest.fixture(autouse=True)
def cors(settings):
    settings.CORS_ALLOWED_ORIGINS = [ORIGIN]


def test_allowed_origin(client):
    r = client.get("/api/v1/readings/", HTTP_ORIGIN=ORIGIN)
    assert r["Access-Control-Allow-Origin"] == ORIGIN


def test_unlisted_origin(client):
    r = client.get("/api/v1/readings/", HTTP_ORIGIN="https://evil.com")
    assert "Access-Control-Allow-Origin" not in r


def test_preflight(client):
    r = client.options(
        "/api/v1/readings/", HTTP_ORIGIN=ORIGIN,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
    )
    assert r["Access-Control-Allow-Origin"] == ORIGIN
    assert "authorization" in r["Access-Control-Allow-Headers"].lower()


def test_non_api_path_no_cors(client):
    r = client.get("/health/", HTTP_ORIGIN=ORIGIN)
    assert "Access-Control-Allow-Origin" not in r
