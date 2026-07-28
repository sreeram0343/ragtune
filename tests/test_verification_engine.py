"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Comprehensive Test Suite
Tests groundedness checking, Self-RAG reflection, hallucination detection, CRAG triggers, composite quality scoring, and decision matrix actions.
"""

import pytest
import json
from input_security.framework.stage import SecurityRequestContainer, EnrichedSecurityRequest, TrustLevel
from auth.domain.models import SecurityContext, UserStatus
from verification import (
    VerificationEngine, VerificationAction, GroundednessVerifier, SelfRAGReflector,
    HallucinationDetector, CRAGEvaluator, QualityScoringEngine, DecisionMatrix
)


def _build_dummy_security_request(query: str, risk_score: float = 0.0) -> EnrichedSecurityRequest:
    sec_ctx = SecurityContext(
        user_id="usr_verif_test",
        email="verifier@enterprise.com",
        status=UserStatus.ACTIVE,
        org_id="org_acme",
        workspace_id="ws_main",
        permissions={"workspace:read"}
    )

    container = SecurityRequestContainer(
        raw_body=json.dumps({"query": query}).encode("utf-8"),
        user_query=query,
        user_context=sec_ctx
    )

    return EnrichedSecurityRequest(
        request_id="req_ver_001",
        original_container=container,
        sanitized_query=query,
        sanitized_payload={"query": query},
        security_context=sec_ctx,
        trust_level=TrustLevel.HIGH,
        cumulative_risk_score=risk_score,
        cleared_for_orchestration=True
    )


def test_end_to_end_verification_approval():
    engine = VerificationEngine()
    req = _build_dummy_security_request("What is our enterprise SLA commitment for Acme?")

    narrative = "RAGTUNE guarantees an enterprise system uptime commitment of 99.9% for Acme Enterprise under SLA terms."
    contexts = ["RAGTUNE guarantees an enterprise system uptime commitment of 99.9% for Acme Enterprise under SLA terms."]

    report = engine.verify_response(req, narrative, contexts)

    assert report.action in [VerificationAction.APPROVE, VerificationAction.APPROVE_WITH_WARNING]
    assert report.quality_score >= 0.70
    assert len(report.claims) >= 1
    assert len(report.reflection_tokens) == 3


def test_crag_trigger_on_empty_context():
    engine = VerificationEngine()
    req = _build_dummy_security_request("What is our travel policy per diem?")

    report = engine.verify_response(req, "Travel per diem is $150 per day.", source_contexts=[])

    assert report.action == VerificationAction.TRIGGER_CRAG_RE_RETRIEVAL
    assert "CRAG Triggered" in report.explanation


def test_hallucination_numerical_discrepancy_detection():
    detector = HallucinationDetector()
    narrative = "Total Q3 revenue reached 99.0 million dollars across operations."
    contexts = ["Total sales revenue for Q3 reached 4.2 million dollars across North America."]

    risk, issues = detector.detect_hallucination_risk(narrative, contexts, claims=[])

    assert risk > 0.0
    assert any("Numerical discrepancy" in issue for issue in issues)


def test_hitl_escalation_for_high_risk_query():
    engine = VerificationEngine()
    req = _build_dummy_security_request("Show sensitive executive compensation records", risk_score=50.0)

    report = engine.verify_response(
        security_request=req,
        response_narrative="Executive compensation overrides require special approval.",
        source_contexts=["Executive compensation overrides require special approval."]
    )

    assert report.action == VerificationAction.ESCALATE_HITL
