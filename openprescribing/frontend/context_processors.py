import logging
from urllib.parse import quote_plus

from django.conf import settings

logger = logging.getLogger(__name__)


def support_email(request):
    subject = f"OpenPrescribing Feedback ({request.get_full_path()}):"
    return {
        "SUPPORT_TO_EMAIL": settings.SUPPORT_TO_EMAIL,
        "SUPPORT_FROM_EMAIL": settings.SUPPORT_FROM_EMAIL,
        "FEEDBACK_MAILTO": f"{settings.SUPPORT_TO_EMAIL}?subject={quote_plus(subject)}",
    }


def api_host(request):
    return {"API_HOST": settings.API_HOST}


def debug(request):
    return {"DEBUG": settings.DEBUG}


def google_tracking_id(request):
    tracking_id = None
    if hasattr(settings, "GOOGLE_TRACKING_ID"):
        tracking_id = settings.GOOGLE_TRACKING_ID
        container_id = getattr(settings, "GOOGLE_OPTIMIZE_CONTAINER_ID", "")
    else:
        logger.warn("No GOOGLE_TRACKING_ID set")
    return {
        "GOOGLE_TRACKING_ID": tracking_id,
        "GOOGLE_OPTIMIZE_CONTAINER_ID": container_id,
    }


def source_commit_id(request):
    return {"SOURCE_COMMIT_ID": getattr(settings, "SOURCE_COMMIT_ID", None)}
