"""
Audit trail middleware and utilities for the Dance Studio Management System.

Records model changes (CREATE/UPDATE/DELETE) in the AuditLog table for
compliance and debugging. Attaches the requesting user and a summary of
changes to each audit entry.
"""

import json

from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.utils import timezone


def log_audit_change(
    user,
    action: str,
    model_name: str,
    object_id,
    change_summary: str | None = None,
    request: HttpRequest | None = None,
):
    """
    Create an AuditLog entry for a model change.

    Args:
        user: The authenticated user who made the change (or None for system actions)
        action: One of 'CREATE', 'UPDATE', 'DELETE'
        model_name: Django model name (e.g. 'students.Student')
        object_id: Primary key of the affected object
        change_summary: Human-readable description of what changed
        request: Optional HttpRequest for extracting IP/user-agent info
    """
    from billing.models import AuditLog  # avoid circular import at module level

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        change_summary=change_summary or '',
        ip_address=(request.META.get('REMOTE_ADDR') if request else None),
        user_agent=(request.META.get('HTTP_USER_AGENT')[:500] if request else None),
        timestamp=timezone.now(),
    )


class AuditMiddleware:
    """
    Middleware that attaches the current user to the request for audit logging.

    Ensures every request has `request.user_audit` available as the
    authenticated user object (or None for anonymous requests), so view code
    can call ``AuditMiddleware.log_change(...)`` without additional imports.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.user_audit = getattr(request, 'user', None)
        response = self.get_response(request)
        return response