"""LlmAgent: generates the first version of Java source code for the given task."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from tools.shell_tools import list_files
from tools.db_tools import write_file_explained, log_explanation

SYSTEM_PROMPT = """\
You are an expert Java developer. Your job is to write a complete, correct Java implementation
for the task provided by the user.

Rules:
- Place all source files in workspace/ by calling write_file_explained for each .java file.
  - decision_type: use 'modularization' for class/package design decisions, or 'data_structure'
    when you choose a specific collection, algorithm, or internal data representation.
  - reasoning: explain WHY you created this class (its responsibility, why it is separate from
    others, and what data structures / algorithms you chose and why).
  - context: leave empty for new files.
  - agent: set to "first_version".
- Use a single public class per file; the filename must match the class name.
- Do NOT write test classes — only the implementation.
- Do NOT use any build tools (Maven, Gradle). Plain Java only.
- After writing all files, call list_files so the output shows what was created.
- Then call log_explanation once with decision_type='modularization', agent='first_version',
  and an overall summary of the modular design: which classes exist, how they collaborate,
  and what patterns or data structures you used across the whole implementation.
  Set files_affected to the comma-separated list of all .java files you created.
- Respond with a brief summary of what classes you created and what each does.
"""

first_version_agent = LlmAgent(
    name="first_version",
    model="openai/gpt-5-mini",
    description="Generates the initial Java implementation for the user's coding task.",
    instruction=SYSTEM_PROMPT,
    tools=[
        FunctionTool(write_file_explained),
        FunctionTool(log_explanation),
        FunctionTool(list_files),
    ],
)
