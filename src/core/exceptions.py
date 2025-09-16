class DomainError(Exception):
    """Base domain-level error."""


class UserAlreadyExistsError(DomainError):
    def __init__(self, username: str):
        super().__init__(f"User '{username}' already exists")
        self.username = username


class UserNotFoundError(DomainError):
    def __init__(self, user_id: str | None = None, username: str | None = None):
        ident = user_id or username or "<unknown>"
        super().__init__(f"User '{ident}' not found")
        self.user_id = user_id
        self.username = username


class InvalidCredentialsError(DomainError):
    def __init__(self):
        super().__init__("Invalid username or password")


class TokenDecodeError(DomainError):
    def __init__(self, reason: str = "invalid token"):
        super().__init__(reason)
        self.reason = reason


class ValidationError(DomainError):
    """Domain-level validation error (mapped to 422)."""

    def __init__(self, message: str):
        super().__init__(message)
