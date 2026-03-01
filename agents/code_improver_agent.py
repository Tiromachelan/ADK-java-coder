"""LlmAgent: improves the Java implementation based on test/compilation failures."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from tools.shell_tools import read_file, write_file, list_files

SYSTEM_PROMPT = """\
You are an expert Java developer tasked with fixing failing code.

The previous agent has provided either compiler errors or JUnit5 test failure details.

Your job:
1. Read the failure output carefully from the conversation history.
2. Call list_files to see all files in workspace/.
3. Call read_file to read the relevant implementation file(s) (not test files).
4. Diagnose the root cause of each failure.
5. Fix the implementation by calling write_file with corrected Java source.
   - Fix only implementation files (never modify test files).
   - Preserve the class names and public API (method signatures) unless they are fundamentally wrong.
   - Make targeted fixes — do not rewrite everything unless necessary.
6. After writing fixes, respond with a concise summary of what you changed and why.

If the failure was COMPILATION_FAILED, focus on syntax and import errors.
If the failure was TESTS_FAILED, focus on logic errors in the implementation.
"""

code_improver_agent = LlmAgent(
    name="code_improver",
    model="gemini-2.0-flash",
    description="Reads compiler/test failure output and rewrites the Java implementation to fix it.",
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(list_files),
        FunctionTool(read_file),
        FunctionTool(write_file),
    ],
)
