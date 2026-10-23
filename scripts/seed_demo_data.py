"""Create isolated, repeatable demo data for manual frontend/API testing."""
import os
import sys
from datetime import timedelta
from pathlib import Path

from pymongo import MongoClient
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db.connection import now

TAG = "crossrecord_demo_v1"
PEOPLE = [("ana", "Ana", "Martín"), ("javi", "Javi", "Ruiz"), ("carla", "Carla", "Díaz"), ("lucas", "Lucas", "Vega"), ("maria", "María", "Gil"), ("david", "David", "Sanz"), ("laura", "Laura", "Mora"), ("pablo", "Pablo", "León"), ("sofia", "Sofía", "Cano"), ("diego", "Diego", "Ramos"), ("elena", "Elena", "Navas"), ("marcos", "Marcos", "Iglesias"), ("nora", "Nora", "Soto"), ("hugo", "Hugo", "Prieto"), ("ines", "Inés", "Vidal")]


def run(database):
    robert = database.users.find_one({"username_key": "robert"})
    if not robert:
        sys.exit("Create the premium user 'robert' before running demo data")
    demo_users = []
    for index, (username, name, last_name) in enumerate(PEOPLE):
        email = f"{username}.demo@crossrecord.test"
        doc = {"email": email, "email_key": email, "username": username, "username_key": username, "password_hash": generate_password_hash("DemoCrossRecord!2026"), "name": name, "last_name": last_name, "profile_picture": f"https://i.pravatar.cc/256?u=crossrecord-{username}", "profile_private": username in {"nora", "hugo"}, "weight": 58 + index * 2, "premium": username in {"ana", "carla", "sofia"}, "is_admin": False, "email_verified": True, "session_version": 0, "record_revision": 0, "seed_tag": TAG, "created_at": now()}
        database.users.update_one({"username_key": username}, {"$set": doc}, upsert=True)
        demo_users.append(database.users.find_one({"username_key": username}))
    ids = {u["username"]: u["_id"] for u in demo_users}
    demo_ids = list(ids.values())
    # Regenerate only tagged demo documents, never real user data.
    old_challenges = [x["_id"] for x in database.challenges.find({"seed_tag": TAG}, {"_id": 1})]
    database.notifications.delete_many({"$or": [{"seed_tag": TAG}, {"challenge_id": {"$in": old_challenges}}]})
    database.challenges.delete_many({"seed_tag": TAG})
    database.records.delete_many({"seed_tag": TAG})
    database.follows.delete_many({"seed_tag": TAG})
    variations = {v["slug"]: v for v in database.variations.find({"slug": {"$in": ["air-squat", "barbell-deadlift", "strict-pull-up", "outdoor-run"]}})}
    if len(variations) != 4:
        sys.exit("Run seed_crossfit_catalog.py before this demo seed")
    start = now() - timedelta(days=45)
    def add_records(user, offset):
        specs = [("air-squat", [12 + offset, 15 + offset, 18 + offset], None), ("barbell-deadlift", [70 + offset * 2, 80 + offset * 2, 90 + offset * 2], None), ("strict-pull-up", [3 + offset // 2, 5 + offset // 2, 7 + offset // 2], None), ("outdoor-run", [360 - offset * 2, 345 - offset * 2, 330 - offset * 2], 1000)]
        created = {}
        for slug, values, distance in specs:
            variation = variations[slug]
            for n, value in enumerate(values):
                time = start + timedelta(days=offset + n * 8)
                record = {"user_id": user["_id"], "exercise_id": variation["exercise_id"], "variation_id": variation["_id"], "kind": variation["kind"], "value": value, "distance_m": distance, "performed_at": time, "created_at": time, "is_private": user["username"] == "nora" and n == 2, "bodyweight": user.get("weight"), "challenge_id": None, "is_best": True, "seed_tag": TAG}
                record["_id"] = database.records.insert_one(record).inserted_id
                created[slug] = record
        return created
    marks = {"robert": add_records(robert, 10)}
    for i, user in enumerate(demo_users): marks[user["username"]] = add_records(user, i + 1)
    all_users = [robert] + demo_users
    def follow(a, b): database.follows.update_one({"follower_id": a, "followed_id": b}, {"$set": {"follower_id": a, "followed_id": b, "seed_tag": TAG, "created_at": now()}}, upsert=True)
    for friend in demo_users[:6]: follow(robert["_id"], friend["_id"]); follow(friend["_id"], robert["_id"])
    for i, user in enumerate(demo_users): follow(user["_id"], demo_users[(i + 1) % len(demo_users)]["_id"]); follow(demo_users[(i + 1) % len(demo_users)]["_id"], user["_id"])
    def challenge(sender, receiver, slug, target, status, active=False, completed_record=None):
        base = marks[receiver["username"]][slug]; variation = variations[slug]; created = now() - timedelta(days=3)
        doc = {"challenger_id": sender["_id"], "challenged_id": receiver["_id"], "variation_id": variation["_id"], "exercise_id": variation["exercise_id"], "kind": variation["kind"], "distance_m": base["distance_m"], "baseline": base["value"], "baseline_record_id": base["_id"], "target": target, "message": "Demo challenge", "status": status, "active": active, "created_at": created, "expires_at": now() + timedelta(days=4) if status != "expired" else now() - timedelta(days=1), "accepted_at": created + timedelta(hours=1) if status in {"accepted", "completed"} else None, "completed_at": now() if status == "completed" else None, "improvement_ratio": "0.1", "seed_tag": TAG}
        doc["_id"] = database.challenges.insert_one(doc).inserted_id
        if completed_record:
            database.records.update_one({"_id": completed_record["_id"]}, {"$set": {"challenge_id": doc["_id"]}})
        for recipient, event in ((sender, status), (receiver, "received")):
            database.notifications.insert_one({"user_id": recipient["_id"], "challenge_id": doc["_id"], "type": event, "created_at": now(), "read_at": None, "seed_tag": TAG})
    challenge(demo_users[0], robert, "air-squat", marks["robert"]["air-squat"]["value"] + 2, "pending", True)
    challenge(demo_users[1], robert, "barbell-deadlift", marks["robert"]["barbell-deadlift"]["value"] + 5, "accepted", True)
    challenge(robert, demo_users[2], "strict-pull-up", marks["carla"]["strict-pull-up"]["value"], "completed", False, marks["carla"]["strict-pull-up"])
    challenge(demo_users[3], demo_users[4], "air-squat", marks["maria"]["air-squat"]["value"] + 1, "rejected")
    challenge(demo_users[5], demo_users[6], "strict-pull-up", marks["laura"]["strict-pull-up"]["value"] + 1, "cancelled")
    challenge(demo_users[7], demo_users[8], "outdoor-run", marks["sofia"]["outdoor-run"]["value"] - 10, "expired")
    return {"demo_users": len(demo_users), "records": database.records.count_documents({"seed_tag": TAG}), "challenges": database.challenges.count_documents({"seed_tag": TAG}), "notifications": database.notifications.count_documents({"seed_tag": TAG})}


if __name__ == "__main__":
    uri = os.environ.get("MONGO_URI")
    if not uri: sys.exit("MONGO_URI is required")
    client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=15000)
    client.admin.command("ping")
    print(run(client[os.environ.get("MONGO_DATABASE", "crossrecord")]))
