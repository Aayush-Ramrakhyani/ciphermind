"""Centralised DRF exception handler — returns consistent error envelopes."""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        payload = {
            "error": {
                "status_code": response.status_code,
                "detail": response.data,
            }
        }
        response.data = payload
        return response

    # Unhandled server error — log and return 500
    logger.exception("Unhandled exception in view %s", context.get("view"))
    return Response(
        {"error": {"status_code": 500, "detail": "Internal server error"}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
