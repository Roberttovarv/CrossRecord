"""Notifications are stored in the same transaction as the event."""
from ..connection import db, now


def notify_challenge(challenge, event, session, recipients=None):
    recipients = recipients or (challenge["challenger_id"], challenge["challenged_id"])
    db().notifications.insert_many([
        {"user_id": user_id, "challenge_id": challenge["_id"], "type": event,
         "created_at": now(), "read_at": None}
        for user_id in recipients
    ], session=session)
