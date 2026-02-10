from fastapi import APIRouter
from pydantic import BaseModel
import json
import logging

from pywebpush import webpush, WebPushException

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

logger = logging.getLogger(__name__)

subscriptions: list = []


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict


@router.post("/subscribe", status_code=201)
async def subscribe(sub: PushSubscription):
    sub_dict = sub.model_dump()
    for existing in subscriptions:
        if existing["endpoint"] == sub_dict["endpoint"]:
            return {"status": "already_subscribed"}
    subscriptions.append(sub_dict)
    return {"status": "subscribed"}


@router.post("/unsubscribe", status_code=200)
async def unsubscribe(sub: PushSubscription):
    global subscriptions
    subscriptions = [s for s in subscriptions if s["endpoint"] != sub.endpoint]
    return {"status": "unsubscribed"}


@router.get("/vapid-public-key")
async def get_vapid_key():
    from app.config import get_settings
    settings = get_settings()
    return {"publicKey": settings.VAPID_PUBLIC_KEY}


def send_push_to_all(title: str, body: str, url: str = "/"):
    global subscriptions
    from app.config import get_settings
    settings = get_settings()
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        return
    payload = json.dumps({"title": title, "body": body, "url": url})
    failed = []
    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_EMAIL},
            )
        except WebPushException as e:
            logger.warning(f"Push failed for {sub['endpoint']}: {e}")
            if "410" in str(e) or "404" in str(e):
                failed.append(sub["endpoint"])
        except Exception as e:
            logger.warning(f"Push error: {e}")
    if failed:
        subscriptions = [s for s in subscriptions if s["endpoint"] not in failed]
