"""
Pipeline assembly for the ADK Java Coder.

Structure:
    SequentialAgent (root)
    ├── LlmAgent: first_version          — generates initial Java implementation
    └── LoopAgent (max 20 cycles)
        └── SequentialAgent (inner)
            ├── LlmAgent: test_writer        — writes JUnit5 tests (skips if already up to date)
            ├── LlmAgent: test_runner        — compiles & runs tests; responds ALL_TESTS_PASSED on success
            ├── EscalationCheckerAgent       — exits the loop when test_runner says ALL_TESTS_PASSED
            └── LlmAgent: code_improver      — fixes implementation on failures

The LoopAgent exits when:
  - EscalationCheckerAgent emits escalate=True (all tests passed)
  - OR max_iterations (20) is reached
"""

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent

from agents.first_version_agent import first_version_agent
from agents.test_writer_agent import test_writer_agent
from agents.test_runner_agent import test_runner_agent
from agents.code_improver_agent import code_improver_agent
from agents.escalation_agent import escalation_checker


# Inner sequence: write tests → run tests → check escalation → improve code
inner_sequence = SequentialAgent(
    name="tdd_cycle",
    description="One TDD iteration: write tests, run them, escalate on pass, or improve the code.",
    sub_agents=[
        test_writer_agent,
        test_runner_agent,
        escalation_checker,   # exits the loop early when ALL_TESTS_PASSED
        code_improver_agent,
    ],
)

# LoopAgent wraps the TDD cycle, exits early if tests pass
tdd_loop = LoopAgent(
    name="tdd_loop",
    description="Repeatedly runs the TDD cycle until tests pass or 20 cycles are exhausted.",
    sub_agents=[inner_sequence],
    max_iterations=20,
)

# Root pipeline: generate first version, then enter the TDD loop
root_agent = SequentialAgent(
    name="java_coder",
    description="Generates a Java program from a task description and iteratively tests and improves it.",
    sub_agents=[
        first_version_agent,
        tdd_loop,
    ],
)
