"""Custom exception classes for SafetyForge."""


class DocumentNotFoundError(Exception):
    """Raised when a document cannot be found in Firestore."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class CompanyNotFoundError(Exception):
    """Raised when a company cannot be found in Firestore."""

    def __init__(self, company_id: str) -> None:
        self.company_id = company_id
        super().__init__(f"Company not found: {company_id}")


class GenerationError(Exception):
    """Raised when AI document generation fails."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.detail = detail
        super().__init__(message)


class DocumentLimitExceededError(Exception):
    """Raised when the free tier document limit is exceeded."""

    def __init__(self, company_id: str, limit: int) -> None:
        self.company_id = company_id
        self.limit = limit
        super().__init__(
            f"Company {company_id} has reached the free tier limit of {limit} documents per month"
        )


class SubscriptionRequiredError(Exception):
    """Raised when a paid subscription is required for the requested action."""

    def __init__(self, message: str = "A paid subscription is required for this action") -> None:
        super().__init__(message)


class InvalidWebhookSignatureError(Exception):
    """Raised when a webhook signature cannot be verified."""

    def __init__(self) -> None:
        super().__init__("Invalid webhook signature")


class AuthenticationError(Exception):
    """Raised when Firebase token verification fails."""

    def __init__(self, message: str = "Invalid or expired authentication token") -> None:
        super().__init__(message)
