"""NEXUS Shared Enumerations for Models."""

import enum


class ActionStatus(enum.StrEnum):
    """Domain state of an Action."""

    CANDIDATE = "CANDIDATE"  # Newly extracted, awaiting human review
    BLOCKED = "BLOCKED"  # Blocked by prerequisite tasks
    READY = "READY"  # Ready for execution
    IN_PROGRESS = "IN_PROGRESS"  # Currently being worked on
    PENDING_VERIFICATION = "PENDING_VERIFICATION"  # Evidence submitted, under test
    COMPLETED = "COMPLETED"  # Formally verified and finished
    REJECTED = "REJECTED"  # Dismissed during review
    FAILED = "FAILED"  # Attempted but failed execution
    CANCELLED = "CANCELLED"  # Deprecated or cancelled
    REQUIRES_REVIEW = "REQUIRES_REVIEW"  # Requires manual review (from spec)


class ConfidenceLevel(enum.StrEnum):
    """Confidence level of AI extraction."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


class EdgeRelationType(enum.StrEnum):
    """Semantic meaning of the edge."""

    DEPENDS_ON = "depends_on"
    CREATES = "creates"
    APPLIES_TO = "applies_to"
    ASSERTS = "asserts"
    REQUIRES = "requires"
    DUE_ON = "due_on"
    COMPLETED_BY = "completed_by"
    BLOCKS = "blocks"
    SUPERSEDES = "supersedes"


class ExtractionJobStatus(enum.StrEnum):
    """Lifecycle state of an ExtractionJob."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class ExecutionState(enum.StrEnum):
    """Deterministic lifecycle of an ExecutionRequest."""

    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DENIED = "DENIED"  # Failed authorization
    REJECTED = "REJECTED"  # Failed approval


class PolicyDecision(enum.StrEnum):
    """Result of a policy evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class Capability(enum.StrEnum):
    """Explicit capabilities required by tools/executors."""

    DOCUMENT_READ = "DOCUMENT_READ"
    ACTION_CREATE = "ACTION_CREATE"
    ACTION_UPDATE = "ACTION_UPDATE"
    CALENDAR_READ = "CALENDAR_READ"
    CALENDAR_CREATE = "CALENDAR_CREATE"
    EMAIL_DRAFT = "EMAIL_DRAFT"
    EMAIL_SEND = "EMAIL_SEND"
    GITHUB_REPOSITORY_READ = "GITHUB_REPOSITORY_READ"
    GITHUB_ISSUE_READ = "GITHUB_ISSUE_READ"
    GITHUB_ISSUE_CREATE = "GITHUB_ISSUE_CREATE"
    GITHUB_ISSUE_COMMENT_CREATE = "GITHUB_ISSUE_COMMENT_CREATE"
    SYSTEM_SIMULATE = "SYSTEM_SIMULATE"  # For the simulated executor


class ApprovalDecision(enum.StrEnum):
    """Human or system decision on a pending execution."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
