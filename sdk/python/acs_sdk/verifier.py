from .decision import ACSDecision, ACSStatus
from .schema import AuthorityToken, ExecutionRequest, VerificationResult


class ACSVerifier:
    def verify(self, token: AuthorityToken, request: ExecutionRequest) -> VerificationResult:
        if token.revoked:
            return VerificationResult(False, ACSStatus.REVOKED, ACSDecision.HALT, "authority token revoked", token)

        if token.expired():
            return VerificationResult(False, ACSStatus.EXPIRED, ACSDecision.DENY, "authority token expired", token)

        if token.subject_agent != request.agent_id:
            return VerificationResult(False, ACSStatus.UNAUTHORIZED, ACSDecision.DENY, "agent mismatch", token)

        if token.tenant_id != request.tenant_id:
            return VerificationResult(False, ACSStatus.UNAUTHORIZED, ACSDecision.DENY, "tenant mismatch", token)

        if request.tool not in token.scope.allowed_tools:
            return VerificationResult(False, ACSStatus.UNAUTHORIZED, ACSDecision.DENY, "tool outside delegation scope", token)

        if request.action not in token.scope.allowed_actions:
            return VerificationResult(False, ACSStatus.UNAUTHORIZED, ACSDecision.DENY, "action outside delegation scope", token)

        if request.risk_score > token.scope.max_risk:
            return VerificationResult(False, ACSStatus.ACTIVE, ACSDecision.STEP_UP, "risk exceeds delegated threshold", token)

        if token.scope.max_amount is not None and request.amount is not None:
            if request.amount > token.scope.max_amount:
                return VerificationResult(False, ACSStatus.ACTIVE, ACSDecision.STEP_UP, "amount exceeds delegated limit", token)

        if token.scope.requires_human_over is not None and request.amount is not None:
            if request.amount > token.scope.requires_human_over:
                return VerificationResult(False, ACSStatus.ACTIVE, ACSDecision.DEFER, "human approval required", token)

        return VerificationResult(True, ACSStatus.ACTIVE, ACSDecision.ALLOW, None, token)


def verify(token: AuthorityToken, request: ExecutionRequest) -> VerificationResult:
    return ACSVerifier().verify(token, request)
