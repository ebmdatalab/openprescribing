import logging

from django.conf import settings

from common import utils

logger = logging.getLogger(__name__)


def support_email(request):
    return {'SUPPORT_EMAIL': settings.SUPPORT_EMAIL}


def google_user_id(request):
    return {'GOOGLE_USER_ID': utils.google_user_id(request.user)}


def api_host(request):
    return {'API_HOST': settings.API_HOST}


def debug(request):
    return {'DEBUG': settings.DEBUG}


def google_tracking_id(request):
    tracking_id = None
    if hasattr(settings, 'GOOGLE_TRACKING_ID'):
        tracking_id = settings.GOOGLE_TRACKING_ID
        container_id = getattr(settings, 'GOOGLE_OPTIMIZE_CONTAINER_ID', '')
    else:
        logger.warn("No GOOGLE_TRACKING_ID set")
    return {
        'GOOGLE_TRACKING_ID': tracking_id,
        'GOOGLE_OPTIMIZE_CONTAINER_ID': container_id
    }
