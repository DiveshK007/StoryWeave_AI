"""
Sentry configuration and utilities for error tracking and monitoring.
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration, EventHandler
from sentry_sdk.scope import Scope
from sentry_sdk.tracing import Transaction
from typing import Optional, Dict, Any
from .settings import settings
from .logger import logger


def init_sentry(dsn: Optional[str] = None, environment: Optional[str] = None):
    """
    Initialize Sentry SDK for error tracking and performance monitoring.
    
    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Environment name (defaults to settings.ENVIRONMENT)
    """
    dsn = dsn or os.getenv("SENTRY_DSN")
    environment = environment or settings.ENVIRONMENT
    
    if not dsn:
        logger.warning("Sentry DSN not provided. Error tracking disabled.")
        return
    
    # Filter sensitive data
    def before_send(event, hint):
        """Filter sensitive data before sending to Sentry."""
        if event.get("request"):
            # Remove sensitive headers
            headers = event["request"].get("headers", {})
            sensitive_headers = ["authorization", "cookie", "x-api-key", "api-key"]
            for header in sensitive_headers:
                headers.pop(header, None)
                headers.pop(header.lower(), None)
                headers.pop(header.upper(), None)
            
            # Remove sensitive query params
            if "query_string" in event["request"]:
                query_string = event["request"]["query_string"]
                sensitive_params = ["password", "token", "api_key", "secret"]
                for param in sensitive_params:
                    if param in query_string:
                        event["request"]["query_string"] = query_string.replace(param, "[FILTERED]")
        
        # Filter sensitive data from extra context
        if event.get("extra"):
            for key in list(event["extra"].keys()):
                if any(sensitive in key.lower() for sensitive in ["password", "token", "secret", "key", "api_key"]):
                    event["extra"][key] = "[FILTERED]"
        
        return event
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=1.0 if environment == "development" else 0.1,  # 100% in dev, 10% in prod
        profiles_sample_rate=1.0 if environment == "development" else 0.1,
        send_default_pii=False,  # Don't send PII by default
        before_send=before_send,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            HttpxIntegration(),
            AsyncioIntegration(),
            LoggingIntegration(
                level=None,  # Capture all logs
                event_level=None  # Send all log events
            ),
        ],
        release=os.getenv("SENTRY_RELEASE", "1.0.0"),
    )
    
    logger.info(f"Sentry initialized for environment: {environment}")


def set_user_context(user_id: Optional[int] = None, email: Optional[str] = None, **kwargs):
    """
    Set user context in Sentry scope.
    
    Args:
        user_id: User ID
        email: User email
        **kwargs: Additional user attributes
    """
    with sentry_sdk.configure_scope() as scope:
        scope.user = {
            "id": str(user_id) if user_id else None,
            "email": email,
            **kwargs
        }


def set_request_context(request_id: Optional[str] = None, story_id: Optional[int] = None, **kwargs):
    """
    Set request context in Sentry scope.
    
    Args:
        request_id: Request ID for tracking
        story_id: Story ID if applicable
        **kwargs: Additional context
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("request_id", request_id)
        scope.set_tag("story_id", story_id)
        scope.set_context("request", {
            "request_id": request_id,
            "story_id": story_id,
            **kwargs
        })


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: Optional[Dict[str, Any]] = None):
    """
    Add a breadcrumb to the Sentry scope.
    
    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Breadcrumb level (debug, info, warning, error, fatal)
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def capture_exception(error: Exception, **context):
    """
    Capture an exception with additional context.
    
    Args:
        error: Exception to capture
        **context: Additional context to attach
    """
    with sentry_sdk.configure_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
    
    sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **context):
    """
    Capture a message with additional context.
    
    Args:
        message: Message to capture
        level: Message level (debug, info, warning, error, fatal)
        **context: Additional context to attach
    """
    with sentry_sdk.configure_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
    
    sentry_sdk.capture_message(message, level=level)


def start_transaction(name: str, op: str = "http.server") -> Transaction:
    """
    Start a performance transaction.
    
    Args:
        name: Transaction name
        op: Operation type
    
    Returns:
        Transaction object
    """
    transaction = sentry_sdk.start_transaction(name=name, op=op)
    return transaction


def set_fingerprint(fingerprint: list):
    """
    Set custom fingerprint for error grouping.
    
    Args:
        fingerprint: List of strings for fingerprinting
    """
    sentry_sdk.set_tag("custom_fingerprint", "-".join(fingerprint))
    with sentry_sdk.configure_scope() as scope:
        scope.fingerprint = fingerprint
