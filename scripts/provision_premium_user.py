"""Create or promote one verified premium account without exposing credentials."""
import argparse
import os
import sys
from pathlib import Path

from pymongo import MongoClient
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.connection import now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--password-env", default="CROSSRECORD_PROVISION_PASSWORD")
    args = parser.parse_args()
    password = os.environ.get(args.password_env)
    uri = os.environ.get("MONGO_URI")
    if not uri or not password:
        sys.exit("MONGO_URI and the password environment variable are required")
    email, username = args.email.strip().lower(), args.username.strip()
    client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=15000)
    database = client[os.environ.get("MONGO_DATABASE", "crossrecord")]
    database.client.admin.command("ping")
    by_email = database.users.find_one({"email_key": email.casefold()})
    by_username = database.users.find_one({"username_key": username.casefold()})
    if by_email and by_username and by_email["_id"] != by_username["_id"]:
        sys.exit("Email and username belong to different accounts; no changes made")
    existing = by_email or by_username
    if existing:
        database.users.update_one({"_id": existing["_id"]}, {"$set": {"premium": True, "email_verified": True, "deactivated_at": None}})
        print("updated existing account: premium enabled")
        return
    document = {"email": email, "email_key": email.casefold(), "username": username, "username_key": username.casefold(), "password_hash": generate_password_hash(password), "name": args.name.strip(), "last_name": args.last_name.strip(), "profile_picture": None, "profile_private": False, "weight": None, "premium": True, "is_admin": False, "email_verified": True, "session_version": 0, "record_revision": 0, "created_at": now()}
    database.users.insert_one(document)
    print("created verified premium account")


if __name__ == "__main__":
    main()
