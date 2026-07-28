"""
RAGTUNE Workflow Orchestration Engine - State Checkpointer & Persistence
Manages workflow state snapshots, history tracking, and checkpoint persistence.
"""

import copy
import threading
import time
from typing import Dict, Any, Optional, List
from orchestration.state import OrchestrationState


class WorkflowCheckpointer:
    def __init__(self):
        self._lock = threading.RLock()
        self._checkpoints: Dict[str, List[Dict[str, Any]]] = {}

    def save_checkpoint(self, workflow_id: str, state: OrchestrationState, step_name: str) -> str:
        """Saves a state snapshot for workflow_id at step_name."""
        with self._lock:
            if workflow_id not in self._checkpoints:
                self._checkpoints[workflow_id] = []

            checkpoint_id = f"ckpt_{len(self._checkpoints[workflow_id]) + 1}_{step_name}"
            snapshot = {
                "checkpoint_id": checkpoint_id,
                "workflow_id": workflow_id,
                "step_name": step_name,
                "timestamp": time.time(),
                "state": copy.deepcopy(dict(state))
            }

            self._checkpoints[workflow_id].append(snapshot)
            return checkpoint_id

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Returns the most recent checkpoint snapshot for workflow_id."""
        with self._lock:
            history = self._checkpoints.get(workflow_id)
            if history:
                return copy.deepcopy(history[-1])
            return None

    def get_checkpoint_by_id(self, workflow_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Returns a specific checkpoint snapshot by checkpoint_id."""
        with self._lock:
            history = self._checkpoints.get(workflow_id, [])
            for ckpt in history:
                if ckpt["checkpoint_id"] == checkpoint_id:
                    return copy.deepcopy(ckpt)
            return None

    def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Lists all checkpoint step names and timestamps for a workflow."""
        with self._lock:
            history = self._checkpoints.get(workflow_id, [])
            return [
                {
                    "checkpoint_id": c["checkpoint_id"],
                    "step_name": c["step_name"],
                    "timestamp": c["timestamp"],
                    "status": c["state"].get("status")
                }
                for c in history
            ]
