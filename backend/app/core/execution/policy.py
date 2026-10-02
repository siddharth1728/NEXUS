"""Application-owned Policy Boundary."""

from app.models.enums import Capability, PolicyDecision
from app.schemas.execution import ExecutionRequestCreate


class PolicyEngine:
    """Evaluates deterministic application rules for execution requests.
    
    The policy engine must NOT call an LLM to decide authorization.
    """

    def evaluate(self, request: ExecutionRequestCreate) -> PolicyDecision:
        """Evaluate an execution request against domain policies."""

        # Simulated Capability mapping for phase 02B:
        if request.capability in (Capability.DOCUMENT_READ, Capability.CALENDAR_READ, Capability.GITHUB_REPOSITORY_READ, Capability.GITHUB_ISSUE_READ):
            return PolicyDecision.ALLOW

        if request.capability in (Capability.EMAIL_SEND, Capability.GITHUB_ISSUE_CREATE, Capability.GITHUB_ISSUE_COMMENT_CREATE, Capability.ACTION_CREATE, Capability.ACTION_UPDATE):
            return PolicyDecision.REQUIRE_APPROVAL

        if request.capability == Capability.SYSTEM_SIMULATE:
            # By default mock tools can just be allowed or require approval based on parameters
            if request.parameters.get("requires_approval", False):
                return PolicyDecision.REQUIRE_APPROVAL
            return PolicyDecision.ALLOW

        # Deny unknown or unconfigured capabilities by default
        return PolicyDecision.DENY
