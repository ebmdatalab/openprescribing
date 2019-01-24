from django.contrib import messages
from pipeline.runner import in_progress


def import_warning_middleware(get_response):
    def middleware(request):
        if in_progress() and not request.path.startswith('/api/'):
            # If we add a message to an API request, then depending on whether
            # the API requests get made in parallel, Django can end up updating
            # the cookie multiple times, causing the message to be displayed
            # multiple times.
            msg = 'We are currently importing the latest prescribing data.  You may see incomplete data across the site.  Please check back in a couple of hours!'
            messages.add_message(request, messages.WARNING, msg)

        response = get_response(request)

        return response
    return middleware
