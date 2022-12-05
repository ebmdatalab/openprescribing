from matrixstore.db import UnknownOrgIDError
from rest_framework.exceptions import APIException, status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Convert UnknownOrgIDError into an appropriate API exception
    if isinstance(exc, UnknownOrgIDError):
        org_id = exc.args[0]
        exc = APIException(detail=f"Unknown organisation ID: {org_id}")
        exc.status_code = status.HTTP_400_BAD_REQUEST
    return exception_handler(exc, context)
