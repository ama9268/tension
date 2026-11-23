import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ApiKey

LIST = "/api/v1/readings/"


def auth(client, key):
    client.credentials(HTTP_AUTHORIZATION=f"ApiKey {key.raw}")


def test_read_only_own_data(api_client, api_key_a, readings_a, readings_b):
    auth(api_client, api_key_a)
    r = api_client.get(LIST)
    assert r.status_code == 200
    assert r.data["count"] == 2


@pytest.mark.parametrize("path", ["stats/", "chart/", "export/"])
def test_extra_endpoints(api_client, api_key_a, readings_a, path):
    auth(api_client, api_key_a)
    assert api_client.get(LIST + path).status_code == 200


def test_write_methods_forbidden(api_client, api_key_a, readings_a):
    auth(api_client, api_key_a)
    rid = readings_a[0].id
    assert api_client.post(LIST, {"systolic": 120, "diastolic": 80, "measured_at": "2026-01-01T10:00:00Z"}).status_code == 403
    assert api_client.patch(f"{LIST}{rid}/", {"systolic": 121}).status_code == 403
    assert api_client.delete(f"{LIST}{rid}/").status_code == 403
    assert api_client.post("/api/v1/agent/analyze/", {}).status_code == 403


def test_invalid_revoked_missing(api_client, api_key_a):
    api_client.credentials(HTTP_AUTHORIZATION="ApiKey nope")
    assert api_client.get(LIST).status_code == 401
    api_client.credentials()
    assert api_client.get(LIST).status_code == 401
    api_key_a.revoked = True
    api_key_a.save()
    auth(api_client, api_key_a)
    assert api_client.get(LIST).status_code == 401


def test_hash_only_and_last_used(api_client, api_key_a):
    assert api_key_a.raw not in (api_key_a.key_hash, api_key_a.prefix)
    assert api_key_a.last_used_at is None
    auth(api_client, api_key_a)
    api_client.get(LIST)
    api_key_a.refresh_from_db()
    assert api_key_a.last_used_at is not None


def test_token_and_jwt_can_still_write(api_client, user_a):
    body = {"systolic": 120, "diastolic": 80, "measured_at": "2026-01-01T10:00:00Z"}
    t = Token.objects.create(user=user_a)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {t.key}")
    assert api_client.post(LIST, body, format="json").status_code == 201
    jwt = RefreshToken.for_user(user_a).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt}")
    assert api_client.post(LIST, body, format="json").status_code == 201


def test_web_create_shows_key_once(client, user_a):
    client.force_login(user_a)
    client.post(reverse("apikey-create"), {"name": "web"})
    page = client.get(reverse("profile"))
    key = ApiKey.objects.get(user=user_a)
    assert page.context["new_api_key"]
    assert key.key_hash == ApiKey.hash_key(page.context["new_api_key"])
    assert client.get(reverse("profile")).context["new_api_key"] is None


def test_revoke_only_own(client, user_a, user_b):
    other, _ = ApiKey.create_for(user_b, "x")
    client.force_login(user_a)
    assert client.post(reverse("apikey-revoke", args=[other.pk])).status_code == 404
    mine, _ = ApiKey.create_for(user_a, "y")
    client.post(reverse("apikey-revoke", args=[mine.pk]))
    mine.refresh_from_db()
    assert mine.revoked
