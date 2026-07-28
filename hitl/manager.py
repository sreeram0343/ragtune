"""
RAGTUNE - Human-in-the-Loop (HITL) Workflow Manager
Maintains review queue for flagged queries, low confidence outputs, or high-risk actions.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HITLRequestItem(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"hitl_{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)
    user_id: str
    tenant_id: str
    original_query: str
    reason: str
    confidence_score: float
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, MODIFIED
    context_data: Dict[str, Any] = Field(default_factory=dict)
    operator_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[float] = None


class HITLManager:
    def __init__(self):
        self.pending_queue: Dict[str, HITLRequestItem] = {}
        self.audit_log: List[HITLRequestItem] = []

    def create_ticket(
        self,
        user_id: str,
        tenant_id: str,
        original_query: str,
        reason: str,
        confidence_score: float,
        context_data: Optional[Dict[str, Any]] = None
    ) -> HITLRequestItem:
        """Creates and enqueues a new HITL review ticket."""
        ticket = HITLRequestItem(
            user_id=user_id,
            tenant_id=tenant_id,
            original_query=original_query,
            reason=reason,
            confidence_score=confidence_score,
            context_data=context_data or {}
        )
        self.pending_queue[ticket.ticket_id] = ticket
        return ticket

    def list_pending_tickets(self, tenant_id: Optional[str] = None) -> List[HITLRequestItem]:
        """Returns active pending HITL tickets."""
        tickets = list(self.pending_queue.values())
        if tenant_id:
            tickets = [t for t in tickets if t.tenant_id == tenant_id]
        return sorted(tickets, key=lambda x: x.timestamp, reverse=True)

    def resolve_ticket(
        self,
        ticket_id: str,
        action: str,  # APPROVE or REJECT
        operator_id: str,
        operator_notes: Optional[str] = None,
        modified_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[HITLRequestItem]]:
        """Resolves a pending ticket with operator approval or rejection."""
        if ticket_id not in self.pending_queue:
            return False, f"Ticket '{ticket_id}' not found in pending queue", None

        ticket = self.pending_queue.pop(ticket_id)
        ticket.status = "APPROVED" if action.upper() == "APPROVE" else "REJECTED"
        ticket.resolved_by = operator_id
        ticket.resolved_at = time.time()
        ticket.operator_notes = operator_notes

        if modified_data:
            ticket.context_data.update(modified_data)
            if action.upper() == "APPROVE":
                ticket.status = "MODIFIED"

        self.audit_log.append(ticket)
        return True, f"Ticket '{ticket_id}' resolved as {ticket.status}", ticket

    def get_audit_history(self, limit: int = 50) -> List[HITLRequestItem]:
        """Returns history of resolved HITL tickets."""
        return sorted(self.audit_log, key=lambda x: x.resolved_at or 0.0, reverse=True)[:limit]
