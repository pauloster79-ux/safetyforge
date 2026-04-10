"""Custom exception classes for Kerf."""


class DocumentNotFoundError(Exception):
    """Raised when a document cannot be found in the database."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class CompanyNotFoundError(Exception):
    """Raised when a company cannot be found in the database."""

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
    """Raised when authentication token verification fails."""

    def __init__(self, message: str = "Invalid or expired authentication token") -> None:
        super().__init__(message)


class ProjectLimitExceededError(Exception):
    """Raised when the project limit for the subscription tier is exceeded."""

    def __init__(self, company_id: str, limit: int) -> None:
        self.company_id = company_id
        self.limit = limit
        super().__init__(
            f"Company {company_id} has reached the project limit of {limit}"
        )


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found in the database."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")


class WorkerNotFoundError(Exception):
    """Raised when a worker cannot be found in the database."""

    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        super().__init__(f"Worker not found: {worker_id}")


class InspectionNotFoundError(Exception):
    """Raised when an inspection cannot be found in the database."""

    def __init__(self, inspection_id: str) -> None:
        self.inspection_id = inspection_id
        super().__init__(f"Inspection not found: {inspection_id}")


class ToolboxTalkNotFoundError(Exception):
    """Raised when a toolbox talk cannot be found in the database."""

    def __init__(self, talk_id: str) -> None:
        self.talk_id = talk_id
        super().__init__(f"Toolbox talk not found: {talk_id}")


class IncidentNotFoundError(Exception):
    """Raised when an incident cannot be found in the database."""

    def __init__(self, incident_id: str) -> None:
        self.incident_id = incident_id
        super().__init__(f"Incident not found: {incident_id}")


class HazardReportNotFoundError(Exception):
    """Raised when a hazard report cannot be found in the database."""

    def __init__(self, report_id: str) -> None:
        self.report_id = report_id
        super().__init__(f"Hazard report not found: {report_id}")


class MorningBriefNotFoundError(Exception):
    """Raised when a morning brief cannot be found in the database."""

    def __init__(self, brief_id: str) -> None:
        self.brief_id = brief_id
        super().__init__(f"Morning brief not found: {brief_id}")


class OshaLogEntryNotFoundError(Exception):
    """Raised when an OSHA log entry cannot be found in the database."""

    def __init__(self, entry_id: str) -> None:
        self.entry_id = entry_id
        super().__init__(f"OSHA log entry not found: {entry_id}")


class MockInspectionNotFoundError(Exception):
    """Raised when a mock inspection result cannot be found in the database."""

    def __init__(self, inspection_id: str) -> None:
        self.inspection_id = inspection_id
        super().__init__(f"Mock inspection not found: {inspection_id}")


class EquipmentNotFoundError(Exception):
    """Raised when equipment cannot be found in the database."""

    def __init__(self, equipment_id: str) -> None:
        self.equipment_id = equipment_id
        super().__init__(f"Equipment not found: {equipment_id}")


class EnvironmentalProgramNotFoundError(Exception):
    """Raised when an environmental program cannot be found in the database."""

    def __init__(self, program_id: str) -> None:
        self.program_id = program_id
        super().__init__(f"Environmental program not found: {program_id}")


class PrequalPackageNotFoundError(Exception):
    """Raised when a prequalification package cannot be found in the database."""

    def __init__(self, package_id: str) -> None:
        self.package_id = package_id
        super().__init__(f"Prequalification package not found: {package_id}")


class MemberNotFoundError(Exception):
    """Raised when a member cannot be found in the database."""

    def __init__(self, member_id: str) -> None:
        self.member_id = member_id
        super().__init__(f"Member not found: {member_id}")


class DuplicateMemberError(Exception):
    """Raised when trying to add a member that already exists."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Member already exists: {email}")


class InsufficientPermissionError(Exception):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = "Insufficient permission") -> None:
        super().__init__(message)


class InvitationNotFoundError(Exception):
    """Raised when an invitation cannot be found in the database."""

    def __init__(self, invitation_id: str) -> None:
        self.invitation_id = invitation_id
        super().__init__(f"Invitation not found: {invitation_id}")


class InvitationExpiredError(Exception):
    """Raised when an invitation has expired."""

    def __init__(self, invitation_id: str) -> None:
        self.invitation_id = invitation_id
        super().__init__(f"Invitation has expired: {invitation_id}")


class GcRelationshipNotFoundError(Exception):
    """Raised when a GC/Sub relationship cannot be found in the database."""

    def __init__(self, relationship_id: str) -> None:
        self.relationship_id = relationship_id
        super().__init__(f"GC relationship not found: {relationship_id}")


class GcInvitationNotFoundError(Exception):
    """Raised when a GC portal invitation cannot be found in the database."""

    def __init__(self, invitation_id: str) -> None:
        self.invitation_id = invitation_id
        super().__init__(f"GC invitation not found: {invitation_id}")


class AssignmentNotFoundError(Exception):
    """Raised when a project assignment cannot be found in the database."""

    def __init__(self, assignment_id: str) -> None:
        self.assignment_id = assignment_id
        super().__init__(f"Assignment not found: {assignment_id}")


class AgentNotFoundError(Exception):
    """Raised when an agent cannot be found in the database."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}")


class AgentBudgetExceededError(Exception):
    """Raised when an agent's daily budget is exceeded."""

    def __init__(
        self, agent_id: str, name: str, spent: int, budget: int
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.spent = spent
        self.budget = budget
        super().__init__(
            f"Agent '{name}' ({agent_id}) exceeded daily budget: "
            f"spent {spent} cents of {budget} cents"
        )
