"""Custom BaseAgent: escalates out of the LoopAgent when all tests have passed."""

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.events.event_actions import EventActions


class EscalationCheckerAgent(BaseAgent):
    """Reads the most recent test_runner response and escalates if all tests passed.

    Must be placed immediately after test_runner in the inner SequentialAgent.
    The LoopAgent will stop iterating when this agent emits escalate=True.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Walk session events in reverse to find the latest agent text response
        last_text = ""
        for event in reversed(ctx.session.events):
            if event.author == "test_runner" and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        last_text = part.text
                        break
            if last_text:
                break

        should_escalate = "ALL_TESTS_PASSED" in last_text

        if should_escalate:
            yield Event(
                author=self.name,
                content=None,
                actions=EventActions(escalate=True),
            )
        else:
            # Yield a no-op event so the LoopAgent sees we ran and continues
            yield Event(
                author=self.name,
                content=None,
                actions=EventActions(escalate=False),
            )


escalation_checker = EscalationCheckerAgent(
    name="escalation_checker",
    description="Escalates out of the loop when test_runner signals ALL_TESTS_PASSED.",
)
