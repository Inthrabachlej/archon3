"""Project execution state for Archon runs."""

from typing import Any


class ProjectState:
    """Lightweight run-state for Archon execution."""

    def __init__(self):
        self.completed_modules = []
        self.failed_modules = []
        self.decisions = []
        self.constraints = []
        self.retry_events = []

    def record_decision(self, module_id: str, reason: str, action: str):
        self.decisions.append(
            {
                "module_id": module_id,
                "reason": reason,
                "action": action,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed_modules": self.completed_modules,
            "failed_modules": self.failed_modules,
            "decisions": self.decisions,
            "constraints": self.constraints,
            "retry_events": self.retry_events,
        }
