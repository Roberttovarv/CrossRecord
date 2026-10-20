import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import mongomock
import pytest
from pymongo import MongoClient

from src.db.services.challenges import bounds
from src.app import create_app


@pytest.fixture
def setup():
    uri = os.environ.get("TEST_MONGO_URI")
    client = MongoClient(uri, tz_aware=True) if uri else mongomock.MongoClient(tz_aware=True)
    name = "crossrecord_test_" + __import__("uuid").uuid4().hex
    app = create_app({"TESTING": True, "JWT_SECRET_KEY": "test-key-that-is-at-least-32-bytes-long", "MONGO_CLIENT": client, "MONGO_DATABASE": name})
    yield app.test_client(), client[name], bool(uri)
    client.drop_database(name)
    client.close()


def register(client, username):
    response = client.post("/api/v1/auth/register", json={"email": username + "@example.com", "username": username, "password": "Password1!", "name": username, "last_name": "Test"})
    assert response.status_code == 201, response.json
    return response.json["user"]["id"], {"Authorization": "Bearer " + response.json["access_token"]}


def catalog(client, database, user_id, headers, kind="calisthenic"):
    database.users.update_one({"username_key": user_id.lower()}, {"$set": {"is_admin": True}})
    response = client.post("/api/v1/exercises", headers=headers, json={"name": "Exercise", "kind": kind})
    assert response.status_code == 201, response.json
    response = client.post("/api/v1/exercises/" + response.json["id"] + "/variations", headers=headers, json={"name": "Standard"})
    assert response.status_code == 201, response.json
    return response.json["id"]


def add_record(client, headers, variation, value, **extra):
    response = client.post("/api/v1/records", headers=headers, json={"variation_id": variation, "value": value, **extra})
    assert response.status_code == 201, response.json
    return response.json


def test_auth_and_permissions(setup):
    client, database, _ = setup
    uid, headers = register(client, "Robert")
    assert client.get("/api/v1/me").status_code == 401
    assert client.post("/api/v1/auth/register", json={"email": "robert@example.com", "username": "other", "password": "password1", "name": "A", "last_name": "B"}).status_code == 409
    assert client.post("/api/v1/auth/login", json={"email": "ROBERT@example.com", "password": "Password1!"}).status_code == 200
    assert client.post("/api/v1/exercises", headers=headers, json={"name": "X", "kind": "calisthenic"}).status_code == 403
    _, other = register(client, "Javi")
    profile = client.get("/api/v1/users/" + uid, headers=other).json["user"]
    assert "email" not in profile and "premium" not in profile
    assert client.patch("/api/v1/me", headers=headers, json={"premium": True, "is_admin": True}).json["premium"] is False


def test_privacy_friends_history_and_feeds(setup):
    client, database, _ = setup
    uid, headers = register(client, "Robert")
    other_id, other = register(client, "Javi")
    variation = catalog(client, database, "Robert", headers)
    client.patch("/api/v1/me", headers=headers, json={"profile_private": True})
    for n in range(1, 5):
        add_record(client, headers, variation, n, is_private=False)
    hidden = add_record(client, headers, variation, 5, is_private=True)
    history = client.get("/api/v1/me/records", headers=headers).json
    assert len(history["items"]) == 3 and history["has_more_locked"]
    assert client.get("/api/v1/me/records?offset=3", headers=headers).status_code == 403
    assert client.get("/api/v1/me/statistics?variation_id=" + variation, headers=headers).status_code == 403
    assert client.get("/api/v1/users/" + uid, headers=other).json["records"] == []
    client.post("/api/v1/users/" + uid + "/follow", headers=other)
    assert client.get("/api/v1/feed/following", headers=other).json["items"] == []
    client.post("/api/v1/users/" + other_id + "/follow", headers=headers)
    assert client.get("/api/v1/users/" + uid, headers=other).json["records"] == []
    assert len(client.get("/api/v1/feed/following", headers=other).json["items"]) == 4
    client.patch("/api/v1/records/" + hidden["id"] + "/visibility", headers=headers, json={"is_private": False})
    assert len(client.get("/api/v1/users/" + uid, headers=other).json["records"]) == 1
    assert not client.get("/api/v1/feed/global", headers=other).json["items"]
    client.delete("/api/v1/users/" + uid + "/follow", headers=other)
    assert not client.get("/api/v1/users/" + uid, headers=other).json["records"]
    database.users.update_one({"username_key": "robert"}, {"$set": {"premium": True}})
    assert client.get("/api/v1/me", headers=headers).json["show_ads"] is False
    assert len(client.get("/api/v1/me/records?limit=50", headers=headers).json["items"]) == 5
    assert client.get("/api/v1/me/statistics?variation_id=" + variation, headers=headers).json["count"] == 5


def test_bounds():
    assert bounds({"value": Decimal("8.2")}, "calisthenic")["max"] == 9
    assert bounds({"value": Decimal("8.25")}, "calisthenic")["max"] == 10
    assert bounds({"value": 10.5}, "weighted")["max"] == 11.55
    assert bounds({"value": 100}, "cardio")["min"] == 85


def test_challenge_creation_and_lifecycle(setup):
    client, database, real = setup
    uid, headers = register(client, "Robert")
    other_id, other = register(client, "Javi")
    variation = catalog(client, database, "Robert", headers)
    add_record(client, other, variation, 10, is_private=False)
    payload = {"user_id": other_id, "variation_id": variation, "target": 12}
    assert client.post("/api/v1/challenges", headers=headers, json=payload).status_code == 403
    client.post("/api/v1/users/" + other_id + "/follow", headers=headers)
    client.post("/api/v1/users/" + uid + "/follow", headers=other)
    options = client.get("/api/v1/challenges/options", headers=headers, query_string={"user_id": other_id, "variation_id": variation})
    assert options.json["limits"] == {"min": 11, "max": 12, "step": 1}
    assert client.post("/api/v1/challenges", headers=headers, json={**payload, "target": 13}).status_code == 400
    challenge = client.post("/api/v1/challenges", headers=headers, json=payload).json
    url = "/api/v1/challenges/" + challenge["id"] + "/"
    assert client.post("/api/v1/challenges", headers=headers, json=payload).status_code == 409
    assert client.post(url + "accept", headers=headers).status_code == 403
    assert client.post(url + "accept", headers=other).status_code == 200
    assert client.post(url + "complete", headers=other, json={"value": 11}).status_code == 400
    if real:
        response = client.post(url + "complete", headers=other, json={"value": 13, "is_private": False})
        assert response.status_code == 200 and response.json["record"]["value"] == 13
        assert client.post(url + "complete", headers=other, json={"value": 13}).status_code == 409
        feed = client.get("/api/v1/feed/following", headers=headers).json["items"]
        assert len(feed) == 2 and any(item["challenger"]["id"] == uid for item in feed if item["challenger"])
    else:
        pytest.skip("Transactional completion requires TEST_MONGO_URI pointing to a replica set")


def test_private_best_blocks_challenge_and_expiry(setup):
    client, database, _ = setup
    uid, headers = register(client, "Robert")
    other_id, other = register(client, "Javi")
    variation = catalog(client, database, "Robert", headers)
    client.post("/api/v1/users/" + other_id + "/follow", headers=headers)
    client.post("/api/v1/users/" + uid + "/follow", headers=other)
    add_record(client, other, variation, 10, is_private=True)
    assert client.get("/api/v1/challenges/options", headers=headers, query_string={"user_id": other_id, "variation_id": variation}).status_code == 404
    add_record(client, other, variation, 11, is_private=False)
    challenge = client.post("/api/v1/challenges", headers=headers, json={"user_id": other_id, "variation_id": variation, "target": 12}).json
    database.challenges.update_one({"status": "pending"}, {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    assert client.post("/api/v1/challenges/" + challenge["id"] + "/accept", headers=other).status_code == 409
    assert database.challenges.find_one({"status": "expired"})


def test_other_metrics_and_challenge_privacy(setup):
    client, database, _ = setup
    uid, headers = register(client, "Robert")
    other_id, other = register(client, "Javi")
    weighted = catalog(client, database, "Robert", headers, "weighted")
    cardio = catalog(client, database, "Robert", headers, "cardio")
    client.post("/api/v1/users/" + other_id + "/follow", headers=headers)
    client.post("/api/v1/users/" + uid + "/follow", headers=other)
    add_record(client, other, weighted, 10.5, is_private=False)
    record = add_record(client, other, cardio, 100, distance_m=1000, is_private=False)
    weights = client.get("/api/v1/challenges/options", headers=headers, query_string={"user_id": other_id, "variation_id": weighted})
    assert weights.json["limits"] == {"min": 10.51, "max": 11.55, "step": 0.01}
    times = client.get("/api/v1/challenges/options", headers=headers, query_string={"user_id": other_id, "variation_id": cardio, "distance_m": 1000})
    assert times.json["limits"] == {"min": 85, "max": 99, "step": 1}
    assert client.get("/api/v1/challenges/options", headers=headers, query_string={"user_id": other_id, "variation_id": cardio, "distance_m": 500}).status_code == 404
    created = client.post("/api/v1/challenges", headers=headers, json={"user_id": other_id, "variation_id": cardio, "distance_m": 1000, "target": 85})
    assert created.status_code == 201
    client.patch("/api/v1/records/" + record["id"] + "/visibility", headers=other, json={"is_private": True})
    sender_view = client.get("/api/v1/challenges", headers=headers).json["items"][0]
    assert "target" not in sender_view and "baseline" not in sender_view and "variation_id" not in sender_view
    recipient_view = client.get("/api/v1/challenges", headers=other).json["items"][0]
    assert recipient_view["target"] == 85


def test_global_and_free_feed_history_limit(setup):
    client, database, _ = setup
    _, headers = register(client, "Robert")
    other_id, other = register(client, "Javi")
    variation = catalog(client, database, "Robert", headers)
    for n in range(1, 6):
        add_record(client, headers, variation, n, is_private=False)
    add_record(client, other, variation, 1, is_private=False)
    own = [item for item in client.get("/api/v1/feed/global", headers=headers).json["items"] if item["user"]["username"] == "Robert"]
    assert len(own) == 3
    assert len(client.get("/api/v1/feed/global", headers=other).json["items"]) == 6
    client.patch("/api/v1/me", headers=other, json={"profile_private": True})
    assert all(item["user"]["id"] != other_id for item in client.get("/api/v1/feed/global", headers=headers).json["items"])


def test_own_profile_does_not_expose_old_history(setup):
    client, database, _ = setup
    uid, headers = register(client, "Robert")
    variation = catalog(client, database, "Robert", headers)
    for value in (100, 1, 2, 3):
        add_record(client, headers, variation, value, is_private=False)
    assert not client.get("/api/v1/users/" + uid, headers=headers).json["records"]
    database.users.update_one({"username_key": "robert"}, {"$set": {"premium": True}})
    assert client.get("/api/v1/users/" + uid, headers=headers).json["records"][0]["value"] == 100
