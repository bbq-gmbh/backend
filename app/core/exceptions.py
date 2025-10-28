import uuid


# Base Exception
class DomainError(Exception):
    """Base class for all domain-level errors."""


# 400 Bad Request - Client errors (general)
class ValidationError(DomainError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message)


# 401 Unauthorized - Authentication errors
class AuthenticationError(DomainError):
    """Base class for authentication-related errors."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are incorrect."""

    def __init__(self):
        super().__init__("Invalid username or password")


class InvalidTokenError(AuthenticationError):
    """Raised when a JWT token cannot be decoded or is malformed."""

    def __init__(self):
        super().__init__("Invalid authentication credentials")


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""

    def __init__(self):
        super().__init__("Token has expired")


class TokenRevokedError(AuthenticationError):
    """Raised when a token has been revoked (after password change or logout-all)."""

    def __init__(self):
        super().__init__("Token has been revoked")


class UserNotAuthenticatedError(AuthenticationError):
    """Raised when authenticated user cannot be found (deleted user with valid token)."""

    def __init__(self):
        super().__init__("User not found")


# 403 Forbidden - Authorization errors
class AuthorizationError(DomainError):
    """Base class for authorization-related errors."""


class UserNotAuthorizedError(AuthorizationError):
    """Raised when a user doesn't have permission to perform an action."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message)


# 404 Not Found - Resource not found errors
class ResourceNotFoundError(DomainError):
    """Base class for resource not found errors."""


class UserNotFoundError(ResourceNotFoundError):
    """Raised when a user cannot be found by id or username."""

    def __init__(
        self, *, user_id: uuid.UUID | None = None, username: str | None = None
    ):
        ident = user_id or username or "unknown"
        super().__init__(f"User '{ident}' not found")
        self.user_id = user_id
        self.username = username


class EmployeeNotFoundError(ResourceNotFoundError):
    """Raised when an employee cannot be found."""

    def __init__(
        self, *, user_id: uuid.UUID | None = None, username: str | None = None
    ):
        ident = user_id or username or "unknown"
        super().__init__(f"Employee '{ident}' not found")
        self.user_id = user_id
        self.username = username


# 409 Conflict - Resource already exists errors
class ResourceConflictError(DomainError):
    """Base class for resource conflict errors."""


class UserAlreadyExistsError(ResourceConflictError):
    """Raised when attempting to create a user with an existing username."""

    def __init__(self, username: str):
        super().__init__(f"User '{username}' already exists")
        self.username = username


class EmployeeAlreadyExistsError(ResourceConflictError):
    """Raised when attempting to create an employee for a user that already has one."""

    def __init__(self):
        super().__init__("Employee already exists for this user")


# 422 Unprocessable Entity - Validation errors
class UnprocessableEntityError(DomainError):
    """Base class for unprocessable entity errors."""
