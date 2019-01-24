from django.contrib import messages
from pipeline.runner import in_progress


class ImportWarningMiddleware(object):
    def process_request(self, request):
        if in_progress():
            msg = 'We are currently importing the latest prescribing data.  You may see incomplete data across the site.  Please check back in a couple of hours!'
            messages.add_message(request, messages.WARNING, msg)
