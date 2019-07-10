import logging

from django.conf import settings

from frontend.models import PCN

logger = logging.getLogger(__name__)


def support_email(request):
    return {
        'SUPPORT_TO_EMAIL': settings.SUPPORT_TO_EMAIL,
        'SUPPORT_FROM_EMAIL': settings.SUPPORT_FROM_EMAIL,
    }


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
        'GOOGLE_OPTIMIZE_CONTAINER_ID': container_id}


_pcns_enabled = None


def pcns_enabled(request):
    """
    Add a flag indicating whether or not we should show PCN-related features in
    the UI based on whether we've imported any PCNs and associated them with
    practices

    We cache this in a global variable to avoid repeatedly doing this query on
    every page load. After importing PCN data we will need to restart the
    application anyway for the MatrixStore, so there's no additional
    invalidation to be done.

    Once we've imported PCN data for the first time this context processor and
    all references to the `pcns_enabled` flag can be removed.
    """
    global _pcns_enabled
    if _pcns_enabled is None:
        _pcns_enabled = PCN.objects.active().exists()
    return {
        'pcns_enabled': _pcns_enabled
    }
