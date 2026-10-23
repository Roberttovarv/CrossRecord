"""Transactional-email adapter for Resend.

The API key is intentionally read only from application configuration; it is
never stored in MongoDB, logs, or API responses.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app

from ..common import APIError


def send(to, subject, html):
    custom = current_app.extensions.get("mail_sender")
    if custom:
        return custom(to=to, subject=subject, html=html)
    key = current_app.config.get("RESEND_API_KEY")
    sender = current_app.config.get("MAIL_FROM")
    if not key or not sender:
        raise APIError("Email delivery is not configured", 503)
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps({"from": sender, "to": [to], "subject": subject, "html": html}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, TimeoutError) as error:
        raise APIError("Email delivery failed", 503) from error
