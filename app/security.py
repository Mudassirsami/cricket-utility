import bcrypt
from fastapi import Header, HTTPException, status
from app.config import get_settings


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    if not hashed_pin:
        return False
    return bcrypt.checkpw(plain_pin.encode("utf-8"), hashed_pin.encode("utf-8"))


def require_manager_pin(x_manager_pin: str = Header(..., alias="X-Manager-Pin")):
    settings = get_settings()
    if not verify_pin(x_manager_pin, settings.MANAGER_PIN_HASH):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing Manager PIN.",
        )


def require_scorer_pin(x_scorer_pin: str = Header(..., alias="X-Scorer-Pin")):
    settings = get_settings()
    if not verify_pin(x_scorer_pin, settings.SCORER_PIN_HASH):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing Scorer PIN.",
        )
