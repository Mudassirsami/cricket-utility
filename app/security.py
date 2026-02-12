import bcrypt
import logging
from fastapi import Header, HTTPException, status
from app.config import get_settings

logger = logging.getLogger(__name__)


def hash_pin(pin: str) -> str:
    """Hash PIN with bcrypt"""
    if not pin or len(pin) < 4:
        raise ValueError("PIN must be at least 4 characters long")
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify PIN against hash"""
    if not hashed_pin or not plain_pin:
        logger.warning("PIN verification failed: missing PIN or hash")
        return False
    try:
        return bcrypt.checkpw(plain_pin.encode("utf-8"), hashed_pin.encode("utf-8"))
    except Exception as e:
        logger.error(f"PIN verification error: {e}")
        return False


def require_manager_pin(x_manager_pin: str = Header(..., alias="X-Manager-PIN")):
    """Require valid manager PIN"""
    settings = get_settings()
    if not verify_pin(x_manager_pin, settings.MANAGER_PIN_HASH):
        logger.warning("Invalid manager PIN attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing Manager PIN.",
        )
    return x_manager_pin


def require_scorer_pin(x_scorer_pin: str = Header(..., alias="X-Scorer-PIN")):
    """Require valid scorer PIN"""
    settings = get_settings()
    if not verify_pin(x_scorer_pin, settings.SCORER_PIN_HASH):
        logger.warning("Invalid scorer PIN attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing Scorer PIN.",
        )
    return x_scorer_pin
