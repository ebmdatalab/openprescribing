from django.contrib import messages
from pipeline.runner import in_progress


IMPORT_WARNING_TAG = 'import_warning'


def import_warning_middleware(get_response):
    def middleware(request):
        if _should_add_import_warning(request):
            msg = 'We are currently importing the latest prescribing data.  You may see incomplete data across the site.  Please check back in a couple of hours!'
            messages.add_message(request, messages.WARNING, msg, extra_tags=IMPORT_WARNING_TAG)

        response = get_response(request)

        return response
    return middleware


def _should_add_import_warning(request):
    if not in_progress():
        return False
    # If we add a message to an API request, then depending on whether the API
    # requests get made in parallel, Django can end up updating the cookie
    # multiple times, causing the message to be displayed multiple times.
    if request.path.startswith('/api/'):
        return False
    storage = messages.get_messages(request)
    warning_added = any(msg.extra_tags == IMPORT_WARNING_TAG for msg in storage)
    # This is the documented way to access messages without marking them as
    # displayed
    storage.used = False
    return not warning_added
