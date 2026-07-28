"""
RAGTUNE Enterprise Text-to-SQL Engine - Comprehensive Test Suite
Tests schema introspection, SQL generation, AST security validation, row limit capping, read-only DB execution, and result formatting.
"""

import pytest
import json
from input_security.framework.stage import SecurityRequestContainer, EnrichedSecurityRequest, TrustLevel
from auth.domain.models import SecurityContext, UserStatus
from text2sql import (
    EnterpriseText2SQLEngine, SQLValidator, SchemaIntrospector, SQLGenerator,
    SQLExecutionEngine, ResultInterpreter, TableSchema, ColumnSchema
)


def _build_dummy_security_request(query: str, permissions=None) -> EnrichedSecurityRequest:
    sec_ctx = SecurityContext(
        user_id="usr_sql_test",
        email="sql@enterprise.com",
        status=UserStatus.ACTIVE,
        org_id="org_acme",
        workspace_id="ws_main",
        permissions=permissions or {"workspace:read"}
    )

    container = SecurityRequestContainer(
        raw_body=json.dumps({"query": query}).encode("utf-8"),
        user_query=query,
        user_context=sec_ctx
    )

    return EnrichedSecurityRequest(
        request_id="req_sql_001",
        original_container=container,
        sanitized_query=query,
        sanitized_payload={"query": query},
        security_context=sec_ctx,
        trust_level=TrustLevel.HIGH,
        cumulative_risk_score=0.0,
        cleared_for_orchestration=True
    )


def test_end_to_end_text2sql_structured_query():
    engine = EnterpriseText2SQLEngine()
    req = _build_dummy_security_request("What was our total sales revenue in Q3?")

    result = engine.execute_structured_query(req)

    assert result.natural_query == "What was our total sales revenue in Q3?"
    assert "SELECT" in result.generated_sql
    assert "sales" in result.generated_sql.lower()
    assert result.row_count >= 1
    assert result.columns is not None
    assert result.metrics.total_latency_ms >= 0.0


def test_ast_validator_blocks_malicious_ddl_dml():
    validator = SQLValidator()

    # 1. DROP TABLE rejection
    val_drop = validator.validate_sql("DROP TABLE sales;")
    assert val_drop.is_valid is False
    assert "Forbidden SQL statement type detected" in val_drop.error_message

    # 2. DELETE FROM rejection
    val_del = validator.validate_sql("DELETE FROM employees WHERE employee_id = '1';")
    assert val_del.is_valid is False
    assert "Forbidden SQL statement type detected" in val_del.error_message

    # 3. UPDATE rejection
    val_upd = validator.validate_sql("UPDATE sales SET revenue = 0;")
    assert val_upd.is_valid is False
    assert "Forbidden SQL statement type detected" in val_upd.error_message

    # 4. Multi-statement injection rejection
    val_multi = validator.validate_sql("SELECT * FROM sales; DROP TABLE employees;")
    assert val_multi.is_valid is False


def test_automatic_row_limit_capper():
    validator = SQLValidator(max_row_limit=100)

    val = validator.validate_sql("SELECT * FROM sales")
    assert val.is_valid is True
    assert "LIMIT 100" in val.sanitized_sql


def test_hitl_approval_trigger_for_sensitive_salary_data():
    validator = SQLValidator()

    # User lacking 'hr:admin' permission triggers HITL requirement
    req = _build_dummy_security_request("Show employee salary records", permissions={"workspace:read"})
    val = validator.validate_sql("SELECT employee_id, salary FROM employees;", security_context=req.security_context)

    assert val.is_valid is True
    assert val.requires_hitl_approval is True
