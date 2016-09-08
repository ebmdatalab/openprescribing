from django.conf import settings


def support_email(request):
    return {'SUPPORT_EMAIL': settings.SUPPORT_EMAIL}
