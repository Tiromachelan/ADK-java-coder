# ADK Java Coder

An AI agent pipeline built with [Google ADK](https://google.github.io/adk-docs/) that autonomously develops Java programs from a natural-language description. It generates an initial implementation, writes JUnit5 unit tests, compiles and runs them, and iteratively improves the code until all tests pass.

At each key decision point the agents record **why** they made each design choice — modularization, data structure selection, and code fixes triggered by compilation or test failures — into a local SQLite database. A built-in web UI lets you browse every explanation and diff.

## Architecture

```
SequentialAgent (java_coder)
├── LlmAgent: first_version        ← generates initial Java source + logs design decisions
└── LoopAgent: tdd_loop (max 20)
    └── SequentialAgent: tdd_cycle
        ├── CycleTrackerAgent          ← increments explanation DB cycle counter
        ├── LlmAgent: test_writer      ← writes JUnit5 tests + logs test design rationale
        ├── LlmAgent: test_runner      ← compiles & runs tests
        ├── EscalationCheckerAgent     ← exits loop when all tests pass
        └── LlmAgent: code_improver    ← fixes failures + logs diffs & error context
```

The loop exits early when all tests pass, or after 20 iterations.

**LLM backend:** `openai/gpt-5-mini` via `OPENAI_API_KEY`. ADK routes all OpenAI calls through LiteLLM using the `openai/gpt-5-mini` model string.

### Explanation database schema

```
sessions       — one row per pipeline run (session id, task, timestamp)
explanations   — one row per decision (agent, cycle, decision_type, reasoning, error context)
file_changes   — one row per file written (filename, change_type, lines +/-, unified diff)
```

`decision_type` is one of: `modularization`, `data_structure`, `test_design`, `code_fix`.

## Setup

**Requirements:** Python 3.11+, Java JDK (for `javac` / `java`), internet access (to download the JUnit5 jar on first run).

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

Get an API key at https://platform.openai.com/api-keys

## Usage

### Run the pipeline

```bash
python main.py "Write a Calculator class with add, subtract, multiply, and divide methods"
```

Generated Java files are written to `workspace/` (gitignored). All `.java` files in the workspace are printed to stdout at the end. Explanations are appended to `explanations.db` in the project root.

### Browse explanations

```bash
python web/app.py
```

Then open **http://localhost:5000** in your browser.

| Page | URL |
|---|---|
| All sessions | `/` |
| Session detail (explanations by cycle) | `/session/<session_id>` |
| Single explanation with full diff | `/explanation/<id>` |

`explanations.db` persists across runs, so you can compare decisions across multiple tasks.

## Project Layout

```
agents/
  first_version_agent.py   ← generates initial Java source; logs modularization & data structure decisions
  test_writer_agent.py     ← writes JUnit5 tests; logs test design rationale
  test_runner_agent.py     ← compiles & runs tests
  code_improver_agent.py   ← fixes failures; logs diffs and error context
  escalation_agent.py      ← exits the TDD loop when all tests pass
  cycle_tracker_agent.py   ← increments the DB cycle counter each TDD iteration
tools/
  shell_tools.py           ← write_file, read_file, list_files, compile_java, run_tests, download_junit5
  db_tools.py              ← log_explanation, write_file_explained, init_session, increment_cycle
web/
  app.py                   ← Flask explanation browser (python web/app.py)
pipeline.py                ← assembles the full agent tree
main.py                    ← CLI entry point
explanations.db            ← SQLite explanation log (created on first run, gitignored)
workspace/                 ← runtime-generated Java files and compiled classes (gitignored)
```
