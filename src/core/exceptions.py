class DomainError(Exception):
    """Base class for domain-level errors."""


class UserAlreadyExistsError(DomainError):
    """Raised when attempting to create a user with an existing username."""

    def __init__(self, username: str):
        super().__init__(f"User '{username}' already exists")
        self.username = username


class UserNotFoundError(DomainError):
    """Raised when a user cannot be found by id or username."""

    def __init__(self, user_id: str | None = None, username: str | None = None):
        ident = user_id or username or "<unknown>"
        super().__init__(f"User '{ident}' not found")
        self.user_id = user_id
        self.username = username


class InvalidCredentialsError(DomainError):
    """Raised when authentication fails due to invalid credentials."""

    def __init__(self):
        super().__init__("Invalid username or password")


class TokenDecodeError(DomainError):
    """Raised when a JWT cannot be decoded or is invalid."""

    def __init__(self, reason: str = "Invalid token"):
        super().__init__(reason)
        self.reason = reason


class ValidationError(DomainError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message)
