"""
CLI entry point for the ADK Java Coder.

Usage:
    python main.py "Write a Calculator class with add, subtract, multiply, divide methods"

Environment:
    GOOGLE_API_KEY — your Google AI Studio API key (set in .env or shell)
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from pipeline import root_agent
from tools.shell_tools import WORKSPACE


async def run(task: str) -> None:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="java_coder",
        user_id="user",
    )

    runner = Runner(
        agent=root_agent,
        app_name="java_coder",
        session_service=session_service,
    )

    user_message = Content(parts=[Part(text=task)], role="user")

    print(f"\n{'='*60}")
    print(f"Task: {task}")
    print(f"Workspace: {WORKSPACE.resolve()}")
    print(f"{'='*60}\n")

    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    print(f"[{event.author}] {part.text}\n")

    # Print final workspace contents
    print(f"\n{'='*60}")
    print("Final workspace files:")
    for f in sorted(WORKSPACE.rglob("*.java")):
        rel = f.relative_to(WORKSPACE)
        print(f"\n--- {rel} ---")
        print(f.read_text(encoding="utf-8"))
    print(f"{'='*60}\n")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<task description>\"")
        sys.exit(1)
    task = " ".join(sys.argv[1:])
    asyncio.run(run(task))


if __name__ == "__main__":
    main()
