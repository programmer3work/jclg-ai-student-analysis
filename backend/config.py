import os

from dotenv import load_dotenv

load_dotenv()


def required_setting(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


DATABASE_URL = required_setting("DATABASE_URL")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://localhost:5500,http://127.0.0.1:3000,http://127.0.0.1:5500,http://127.0.0.1:15004,http://127.0.0.1:16004,http://16.112.236.67:15004,http://16.112.236.67:16004"
    ).split(",")
    if origin.strip()
]
SUPPORTED_LANGUAGES = [
    language.strip()
    for language in os.getenv("SUPPORTED_LANGUAGES", "English,Telugu,Hindi").split(",")
    if language.strip()
]
ANALYSIS_TYPES = [
    analysis_type.strip()
    for analysis_type in os.getenv("ANALYSIS_TYPES", "Performance Review,Risk Analysis").split(",")
    if analysis_type.strip()
]
RISK_LEVELS = [
    level.strip().lower()
    for level in os.getenv("RISK_LEVELS", "low,moderate,high").split(",")
    if level.strip()
]
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", SUPPORTED_LANGUAGES[0] if SUPPORTED_LANGUAGES else "English")
DEFAULT_ANALYSIS_TYPE = os.getenv("DEFAULT_ANALYSIS_TYPE", "Performance")
HIGH_RISK_LEVEL = os.getenv("HIGH_RISK_LEVEL", "high").lower()
IMPROVING_STATUS = os.getenv("IMPROVING_STATUS", "improving").lower()
RISK_ATTENDANCE_THRESHOLD = float(os.getenv("RISK_ATTENDANCE_THRESHOLD", "75"))
RISK_MARKS_THRESHOLD = float(os.getenv("RISK_MARKS_THRESHOLD", "60"))

if not SUPPORTED_LANGUAGES:
    raise RuntimeError("SUPPORTED_LANGUAGES must contain at least one language")
if not ANALYSIS_TYPES:
    raise RuntimeError("ANALYSIS_TYPES must contain at least one analysis type")
if not RISK_LEVELS:
    raise RuntimeError("RISK_LEVELS must contain at least one risk level")
if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
    raise RuntimeError("DEFAULT_LANGUAGE must be listed in SUPPORTED_LANGUAGES")
if not 0 <= RISK_ATTENDANCE_THRESHOLD <= 100:
    raise RuntimeError("RISK_ATTENDANCE_THRESHOLD must be between 0 and 100")
if not 0 <= RISK_MARKS_THRESHOLD <= 100:
    raise RuntimeError("RISK_MARKS_THRESHOLD must be between 0 and 100")
