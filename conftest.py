from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import ApiKey
from apps.readings.models import BloodPressureReading


@pytest.fixture
def user_a(db):
    return User.objects.create_user("a", password="pw12345678")


@pytest.fixture
def user_b(db):
    return User.objects.create_user("b", password="pw12345678")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_key_a(user_a):
    obj, raw = ApiKey.create_for(user_a, "test")
    obj.raw = raw
    return obj


def _mk(user, sys, dia, days_ago=0):
    return BloodPressureReading.objects.create(
        user=user, systolic=sys, diastolic=dia,
        measured_at=timezone.now() - timedelta(days=days_ago),
    )


@pytest.fixture
def readings_a(user_a):
    return [_mk(user_a, 120, 80, 0), _mk(user_a, 130, 85, 40)]


@pytest.fixture
def readings_b(user_b):
    return [_mk(user_b, 150, 95)]
