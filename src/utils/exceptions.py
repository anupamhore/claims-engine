"""
WHY: Custom exception hierarchy for Claims Engine
  - Type-safe error handling
  - Distinct error types for different failures
  - Easier debugging and logging

HOW:
  - Base exception for all custom errors
  - Specific exceptions inherit from base
  - Used throughout the application

ALTERNATIVE not chosen:
  - Built-in Python exceptions: Not descriptive enough for business logic
"""


class ClaimsEngineException(Exception):
    """Base exception for all Claims Engine errors."""
    pass


class DatabaseError(ClaimsEngineException):
    """Raised when database operation fails."""
    pass


class MLModelError(ClaimsEngineException):
    """Raised when ML model inference fails."""
    pass


class LLMServiceError(ClaimsEngineException):
    """Raised when LLM (Groq/OpenAI) service fails."""
    pass


class GuardrailValidationError(ClaimsEngineException):
    """Raised when LLM guardrail validation fails (hallucination detected)."""
    pass


class ConfigurationError(ClaimsEngineException):
    """Raised when configuration is invalid."""
    pass


class AuthenticationError(ClaimsEngineException):
    """Raised when authentication fails."""
    pass


class ValidationError(ClaimsEngineException):
    """Raised when input validation fails."""
    pass


class ExternalServiceError(ClaimsEngineException):
    """Raised when external service (Kafka, etc.) fails."""
    pass
