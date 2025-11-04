"""
Custom exception classes with Sentry integration for StoryWeave AI.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import sentry_sdk
from .sentry_config import set_fingerprint, capture_exception


class StoryWeaveException(Exception):
    """Base exception for StoryWeave AI."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        sentry_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize exception.
        
        Args:
            message: Error message
            error_code: Custom error code for categorization
            details: Additional error details
            sentry_context: Additional context for Sentry
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.sentry_context = sentry_context or {}
    
    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException for FastAPI."""
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": self.message,
                "error_code": self.error_code,
                "details": self.details
            }
        )
    
    def capture_to_sentry(self):
        """Capture exception to Sentry with custom context."""
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("error_code", self.error_code)
            scope.set_context("error_details", self.details)
            for key, value in self.sentry_context.items():
                scope.set_extra(key, value)
        
        # Set custom fingerprint for better grouping
        set_fingerprint([self.error_code, self.__class__.__name__])
        
        capture_exception(self, error_code=self.error_code, **self.details)


class StoryGenerationError(StoryWeaveException):
    """Error during story generation."""
    
    def __init__(
        self,
        message: str,
        premise: Optional[str] = None,
        genre: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="STORY_GENERATION_FAILED",
            details={"premise": premise, "genre": genre},
            sentry_context={"premise": premise, "genre": genre},
            **kwargs
        )
        # Tag in Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("error_category", "story_generation")


class LLMAPIError(StoryWeaveException):
    """Error when calling LLM API."""
    
    def __init__(
        self,
        message: str,
        api_url: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="LLM_API_ERROR",
            details={
                "api_url": api_url,
                "status_code": status_code,
                "response_body": response_body[:500] if response_body else None  # Limit length
            },
            sentry_context={
                "api_url": api_url,
                "status_code": status_code
            },
            **kwargs
        )
        # Tag in Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("error_category", "llm_api")
            scope.set_tag("llm_status_code", status_code)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException with appropriate status code."""
        status_code = self.details.get("status_code")
        http_status = (
            status.HTTP_502_BAD_GATEWAY if status_code and status_code >= 500
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return HTTPException(
            status_code=http_status,
            detail={
                "error": self.message,
                "error_code": self.error_code,
                "details": {k: v for k, v in self.details.items() if k != "response_body"}
            }
        )


class RateLimitError(StoryWeaveException):
    """Rate limit error from API."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        api_endpoint: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "retry_after": retry_after,
                "api_endpoint": api_endpoint
            },
            sentry_context={
                "retry_after": retry_after,
                "api_endpoint": api_endpoint
            },
            **kwargs
        )
        # Tag in Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("error_category", "rate_limit")
            scope.set_tag("retry_after", retry_after)
        
        # Set lower severity for rate limits (warning, not error)
        sentry_sdk.capture_message(
            f"Rate limit exceeded: {message}",
            level="warning"
        )
    
    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException with 429 status."""
        headers = {}
        if self.details.get("retry_after"):
            headers["Retry-After"] = str(self.details["retry_after"])
        
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": self.message,
                "error_code": self.error_code,
                "retry_after": self.details.get("retry_after")
            },
            headers=headers
        )


class DatabaseConnectionError(StoryWeaveException):
    """Database connection error."""
    
    def __init__(
        self,
        message: str,
        database_url: Optional[str] = None,
        **kwargs
    ):
        # Don't expose full database URL in details
        safe_url = database_url.split("@")[-1] if database_url and "@" in database_url else None
        super().__init__(
            message,
            error_code="DATABASE_CONNECTION_ERROR",
            details={"database_host": safe_url},
            sentry_context={"database_url": "[FILTERED]"},  # Never send full URL
            **kwargs
        )
        # Tag in Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("error_category", "database")
            scope.set_tag("error_type", "connection")
    
    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException with 503 status."""
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Database connection failed",
                "error_code": self.error_code
            }
        )


class VectorStoreError(StoryWeaveException):
    """Error with vector store operations."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="VECTOR_STORE_ERROR",
            details={"operation": operation},
            sentry_context={"operation": operation},
            **kwargs
        )
        # Tag in Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("error_category", "vector_store")
    
    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException."""
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": self.message,
                "error_code": self.error_code,
                "details": self.details
            }
        )


class ValidationError(StoryWeaveException):
    """Validation error for user input."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value)[:100] if value else None},
            **kwargs
        )
        # Don't capture validation errors to Sentry (they're expected)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException with 400 status."""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": self.message,
                "error_code": self.error_code,
                "details": self.details
            }
        )
