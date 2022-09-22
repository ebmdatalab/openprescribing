import re
from django.shortcuts import get_object_or_404, redirect
from frontend.models import STP


def stp_redirect_middleware(get_response):
    def middleware(request):
        match = re.search("/stp/(E\d{8})", request.path)
        if match:
            ons_code = match.groups()[0]
            stp = get_object_or_404(STP, ons_code=ons_code)
            new_path = request.path.replace(ons_code, stp.code)
            return redirect(new_path)
        return get_response(request)

    return middleware
