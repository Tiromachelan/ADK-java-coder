"""LlmAgent: generates the first version of Java source code for the given task."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from tools.shell_tools import write_file, list_files

SYSTEM_PROMPT = """\
You are an expert Java developer. Your job is to write a complete, correct Java implementation
for the task provided by the user.

Rules:
- Place all source files in workspace/ by calling write_file for each .java file.
- Use a single public class per file; the filename must match the class name.
- Do NOT write test classes — only the implementation.
- Do NOT use any build tools (Maven, Gradle). Plain Java only.
- After writing all files, call list_files so the output shows what was created.
- Respond with a brief summary of what classes you created and what each does.
"""

first_version_agent = LlmAgent(
    name="first_version",
    model="gemini-2.0-flash",
    description="Generates the initial Java implementation for the user's coding task.",
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(write_file),
        FunctionTool(list_files),
    ],
)
