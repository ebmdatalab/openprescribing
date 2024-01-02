import re

from django.shortcuts import get_object_or_404, redirect
from frontend.models import STP


def stp_redirect_middleware(get_response):
    def middleware(request):
        path = request.get_full_path()

        # Redirect STP URLs with 9-character ONS codes
        match = re.search(r"/stp/(E\d{8})", path)
        if match:
            ons_code = match.groups()[0]
            stp = get_object_or_404(STP, ons_code=ons_code)
            new_path = path.replace(ons_code, stp.code)
            new_path = new_path.replace("/stp/", "/icb/")
            return redirect(new_path)

        # Redirect STP URLs
        if "/stp/" in path:
            new_path = path.replace("/stp/", "/icb/")
            return redirect(new_path)

        if "by_stp" in path:
            new_path = path.replace("by_stp", "by_icb")
            return redirect(new_path)

        # Redirect CCG URLs
        if "/ccg/" in path:
            new_path = path.replace("/ccg/", "/sicbl/")
            return redirect(new_path)

        if "by_ccg" in path:
            new_path = path.replace("by_ccg", "by_sicbl")
            return redirect(new_path)

        return get_response(request)

    return middleware
