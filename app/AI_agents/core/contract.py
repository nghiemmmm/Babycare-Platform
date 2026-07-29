from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class HandOffNotice(BaseModel):
    """
    Payload for peer-to-peer agent hand-off.
    """
    target_agent_id: str
    reason: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class AgentContract:
    """
    Runtime contract interface for individual domain agents.
    Agents implement business logic, tool calls, and peer hand-off decisions.
    """
    agent_id: str
    display_name: str
    description: str
    intents: List[str] = []

    async def execute(self, state: dict) -> dict:
        """
        Execute domain-specific reasoning, tool calls, or emit HandOffNotice.
        Must return a dict updating OverallState (e.g. messages, tool_steps, hand_off_notice).
        """
        raise NotImplementedError("AgentContract subclasses must implement execute()")
