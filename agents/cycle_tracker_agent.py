"""Custom BaseAgent: increments the DB cycle counter at the start of each TDD iteration."""

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.events.event_actions import EventActions

import tools.db_tools as db_tools


class CycleTrackerAgent(BaseAgent):
    """Increments the db_tools cycle counter each time the TDD loop runs.

    Place this as the first agent in the inner SequentialAgent so the cycle
    counter stays in sync with the actual loop iteration.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        db_tools.increment_cycle()
        yield Event(
            author=self.name,
            content=None,
            actions=EventActions(escalate=False),
        )


cycle_tracker = CycleTrackerAgent(
    name="cycle_tracker",
    description="Increments the explanation DB cycle counter at the start of each TDD loop iteration.",
)
