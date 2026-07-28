"""
RAGTUNE Workflow Orchestration Engine - Human-in-the-Loop Approval Manager
Manages workflow suspension, approval ticket generation, operator review queues, and resumption.
"""

import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class HITLTicket(BaseModel):
    ticket_id: str
    workflow_id: str
    tenant_id: str
    workspace_id: str
    user_query: str
    reason: str
    created_at: float = Field(default_factory=time.time)
    status: str = "PENDING"  # "PENDING", "APPROVED", "REJECTED"
    operator_id: Optional[str] = None
    operator_notes: Optional[str] = None
    resolved_at: Optional[float] = None


class HumanApprovalManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._tickets: Dict[str, HITLTicket] = {}

    def create_ticket(
        self,
        workflow_id: str,
        tenant_id: str,
        workspace_id: str,
        user_query: str,
        reason: str,
        ticket_id: Optional[str] = None
    ) -> HITLTicket:
        """Creates and registers a new pending HITL review ticket."""
        with self._lock:
            t_id = ticket_id if ticket_id else f"hitl_{uuid.uuid4().hex[:8]}"
            ticket = HITLTicket(
                ticket_id=t_id,
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                user_query=user_query,
                reason=reason
            )
            self._tickets[t_id] = ticket
            return ticket

    def get_pending_tickets(self, tenant_id: Optional[str] = None) -> List[HITLTicket]:
        """Returns all pending approval tickets, optionally filtered by tenant_id."""
        with self._lock:
            pending = [t for t in self._tickets.values() if t.status == "PENDING"]
            if tenant_id:
                pending = [t for t in pending if t.tenant_id == tenant_id]
            return pending

    def submit_decision(
        self,
        ticket_id: str,
        operator_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[HITLTicket], str]:
        """Submits an operator decision ('APPROVED' or 'REJECTED') for a ticket."""
        with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket or ticket.status != "PENDING":
                return False, None, "Invalid or already resolved ticket"

            if decision not in ["APPROVED", "REJECTED"]:
                return False, None, "Decision must be 'APPROVED' or 'REJECTED'"

            ticket.status = decision
            ticket.operator_id = operator_id
            ticket.operator_notes = notes
            ticket.resolved_at = time.time()
            return True, ticket, f"Ticket {decision} successfully"
