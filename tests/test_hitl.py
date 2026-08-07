"""
RAGTUNE - Test Suite for Human-in-the-Loop (HITL) Manager
"""

from hitl.manager import HITLManager


def test_hitl_ticket_creation():
    manager = HITLManager()
    ticket = manager.create_ticket(
        user_id="user_123",
        tenant_id="tenant_abc",
        original_query="SHOW ALL SALARIES",
        reason="High risk security policy violation",
        confidence_score=0.45,
        context_data={"policy": "PII_PROTECTION"},
    )
    assert ticket.ticket_id.startswith("hitl_")
    assert ticket.status == "PENDING"
    assert ticket.user_id == "user_123"
    assert ticket.tenant_id == "tenant_abc"
    assert ticket.original_query == "SHOW ALL SALARIES"


def test_hitl_list_pending_tickets():
    manager = HITLManager()
    manager.create_ticket(
        user_id="u1", tenant_id="t1", original_query="q1", reason="r1", confidence_score=0.5
    )
    manager.create_ticket(
        user_id="u2", tenant_id="t2", original_query="q2", reason="r2", confidence_score=0.6
    )

    t1_tickets = manager.list_pending_tickets(tenant_id="t1")
    assert len(t1_tickets) == 1
    assert t1_tickets[0].tenant_id == "t1"

    all_tickets = manager.list_pending_tickets()
    assert len(all_tickets) == 2


def test_hitl_resolve_ticket_approve():
    manager = HITLManager()
    ticket = manager.create_ticket(
        user_id="u1", tenant_id="t1", original_query="q1", reason="r1", confidence_score=0.5
    )

    success, msg, resolved = manager.resolve_ticket(
        ticket_id=ticket.ticket_id,
        action="APPROVE",
        operator_id="admin_1",
        operator_notes="Approved after security verification",
    )
    assert success is True
    assert resolved is not None
    assert resolved.status == "APPROVED"
    assert resolved.resolved_by == "admin_1"
    assert len(manager.list_pending_tickets()) == 0


def test_hitl_resolve_ticket_reject():
    manager = HITLManager()
    ticket = manager.create_ticket(
        user_id="u1", tenant_id="t1", original_query="q1", reason="r1", confidence_score=0.5
    )

    success, msg, resolved = manager.resolve_ticket(
        ticket_id=ticket.ticket_id,
        action="REJECT",
        operator_id="admin_1",
        operator_notes="Rejected due to invalid scope",
    )
    assert success is True
    assert resolved is not None
    assert resolved.status == "REJECTED"


def test_hitl_get_ticket_by_id():
    manager = HITLManager()
    t1 = manager.create_ticket(
        user_id="u1", tenant_id="t1", original_query="q1", reason="r1", confidence_score=0.5
    )
    
    # Query pending ticket
    retrieved = manager.get_ticket_by_id(t1.ticket_id)
    assert retrieved is not None
    assert retrieved.ticket_id == t1.ticket_id

    # Resolve ticket and query resolved ticket from audit log
    manager.resolve_ticket(ticket_id=t1.ticket_id, action="APPROVE", operator_id="admin_1")
    retrieved_audit = manager.get_ticket_by_id(t1.ticket_id)
    assert retrieved_audit is not None
    assert retrieved_audit.status == "APPROVED"

    # Non-existent ticket
    assert manager.get_ticket_by_id("non_existent_id") is None


def test_hitl_get_audit_history():
    manager = HITLManager()
    t1 = manager.create_ticket(
        user_id="u1", tenant_id="t1", original_query="q1", reason="r1", confidence_score=0.5
    )
    manager.resolve_ticket(ticket_id=t1.ticket_id, action="APPROVE", operator_id="admin_1")

    history = manager.get_audit_history()
    assert len(history) == 1
    assert history[0].ticket_id == t1.ticket_id
