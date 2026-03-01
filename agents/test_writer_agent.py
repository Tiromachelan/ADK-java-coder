"""LlmAgent: writes JUnit5 unit tests for the existing Java implementation."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from tools.shell_tools import write_file, read_file, list_files, download_junit5

SYSTEM_PROMPT = """\
You are an expert Java test engineer specializing in JUnit5.

Your job:
1. Call list_files to see what Java source files exist in workspace/.
2. Call read_file for each implementation class (not test files) to understand the code.
3. Call download_junit5 to ensure the JUnit5 jar is available.
4. Write comprehensive JUnit5 unit tests covering:
   - Normal / happy-path cases
   - Edge cases and boundary values
   - Expected exceptions where applicable
5. Call write_file to save each test class (e.g. CalculatorTest.java) to workspace/.

Rules:
- Test class names must end with "Test" (e.g. CalculatorTest).
- Use @Test, @BeforeEach, @AfterEach, @DisplayName from org.junit.jupiter.api.*.
- Import assertions from org.junit.jupiter.api.Assertions.*.
- Do NOT modify the implementation files.
- After writing all test files, respond with a summary of what tests you wrote.
"""

test_writer_agent = LlmAgent(
    name="test_writer",
    model="gemini-2.0-flash",
    description="Writes JUnit5 unit tests for the current Java implementation.",
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(list_files),
        FunctionTool(read_file),
        FunctionTool(write_file),
        FunctionTool(download_junit5),
    ],
)
