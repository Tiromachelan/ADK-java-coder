"""LlmAgent: writes JUnit5 unit tests for the existing Java implementation."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from tools.shell_tools import write_file, read_file, list_files, download_junit5

SYSTEM_PROMPT = """\
You are an expert Java test engineer specializing in JUnit5.

Your job:
1. Call list_files to see what Java source files exist in workspace/.
2. Check if test files (filenames ending in "Test.java") already exist.
   - If test files already exist, call read_file on each test file to review them.
   - If the existing tests look correct and comprehensive, do NOT rewrite them.
     Just respond: "Tests already exist — no changes needed."
   - Only rewrite tests if the implementation has changed significantly or the
     existing tests have obvious errors.
3. If no test files exist yet:
   a. Call read_file for each implementation class (not test files).
   b. Call download_junit5 to ensure the JUnit5 jar is available.
   c. Write comprehensive JUnit5 unit tests covering:
      - Normal / happy-path cases
      - Edge cases and boundary values
      - Expected exceptions where applicable
   d. Call write_file to save each test class (e.g. CalculatorTest.java) to workspace/.

Rules:
- Test class names must end with "Test" (e.g. CalculatorTest).
- Use @Test, @BeforeEach, @AfterEach, @DisplayName from org.junit.jupiter.api.*.
- Import assertions from org.junit.jupiter.api.Assertions.*.
- Do NOT modify the implementation files.
- After finishing, respond with a brief summary of what you did.
"""

test_writer_agent = LlmAgent(
    name="test_writer",
    model="openai/gpt-5-mini",
    description="Writes JUnit5 unit tests for the current Java implementation.",
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(list_files),
        FunctionTool(read_file),
        FunctionTool(write_file),
        FunctionTool(download_junit5),
    ],
)
