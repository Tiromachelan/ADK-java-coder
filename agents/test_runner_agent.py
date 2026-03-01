"""LlmAgent: compiles Java sources, runs JUnit5 tests, and escalates when all pass."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from tools.shell_tools import list_files, compile_java, run_tests

SYSTEM_PROMPT = """\
You are a Java build and test runner agent.

Your job each cycle:
1. Call list_files to find all .java files in workspace/.
2. Call compile_java with ALL .java filenames (both implementation and test classes).
   - If compilation fails, respond with the compiler errors so the code_improver can fix them.
     Start your response with: COMPILATION_FAILED
3. Identify all test classes (filenames ending with "Test.java") from the file list.
4. For each test class, call run_tests with its class name (without .java extension).
5. Examine the test results:
   - If ALL tests passed (no failures or errors):
     Respond with exactly: ALL_TESTS_PASSED
   - If any tests failed or errored:
     Respond with: TESTS_FAILED
     Then include the full test output so the code_improver can fix the issues.

Be precise — copy the exact compiler errors and test failure messages into your response.
"""

test_runner_agent = LlmAgent(
    name="test_runner",
    model="openai/gpt-5-mini",
    description=(
        "Compiles all Java sources and runs JUnit5 tests. "
        "Responds ALL_TESTS_PASSED to signal the loop to exit, or TESTS_FAILED with details."
    ),
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(list_files),
        FunctionTool(compile_java),
        FunctionTool(run_tests),
    ],
)
