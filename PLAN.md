# ADK Java Coder — Implementation Plan

## Problem
Build a Python ADK project that autonomously develops Java programs from a CLI prompt. The pipeline generates an initial implementation, writes JUnit5 tests, compiles and runs them, and iteratively improves the code until all tests pass or 20 cycles are exhausted.

## Agent Structure

```
SequentialAgent
├── LlmAgent: "first_version"       # generates initial Java source
└── LoopAgent (max_iterations=20)
    └── SequentialAgent (inner)
        ├── LlmAgent: "test_writer"    # writes JUnit5 unit tests
        ├── LlmAgent: "test_runner"    # compiles & runs tests via MCP tools; escalates on pass
        └── LlmAgent: "code_improver"  # reads failures, rewrites Java source
```

**Loop exit:** LoopAgent stops when `test_runner` escalates (all tests pass) OR when 20 iterations are reached.

## Key Decisions
- **Build tool:** plain `javac` / `java` (no Maven/Gradle)
- **JUnit5:** downloaded once to `workspace/lib/` as `junit-platform-console-standalone.jar`
- **Entry point:** `main.py` — CLI prompt, passed as user task to the pipeline
- **MCP tools:** shell/subprocess-based, implemented as ADK `FunctionTool`s (not a separate MCP server process — ADK tools are Python functions the agents call directly)
- **Workspace:** `workspace/` directory holds generated `.java` files, compiled `.class` files, and the JUnit5 jar

## Project Layout

```
ADK-java-coder/
├── main.py                        # CLI entry point
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── first_version_agent.py
│   ├── test_writer_agent.py
│   ├── test_runner_agent.py
│   └── code_improver_agent.py
├── pipeline.py                    # assembles all agents into SequentialAgent
├── tools/
│   ├── __init__.py
│   └── shell_tools.py             # write_file, read_file, compile_java, run_tests, download_junit5
└── workspace/                     # runtime-generated; not committed
    └── lib/                       # JUnit5 jar lives here
```

## Todos

1. **setup-project** — Create directory structure, requirements.txt (google-adk, requests), __init__ files, .gitignore for workspace/
2. **shell-tools** — Implement `tools/shell_tools.py`: `write_file`, `read_file`, `compile_java`, `run_tests`, `download_junit5` as ADK FunctionTools using subprocess
3. **first-version-agent** — `agents/first_version_agent.py`: LlmAgent that reads the user task and writes initial Java class(es) to workspace/ via write_file tool
4. **test-writer-agent** — `agents/test_writer_agent.py`: LlmAgent that reads the Java source and writes JUnit5 test class(es), downloading JUnit5 jar if not present
5. **test-runner-agent** — `agents/test_runner_agent.py`: LlmAgent that calls compile_java then run_tests; if all pass, sets `escalate=True` to break the loop
6. **code-improver-agent** — `agents/code_improver_agent.py`: LlmAgent that reads test failure output from session state and rewrites the Java source
7. **pipeline** — `pipeline.py`: assembles inner SequentialAgent, LoopAgent, outer SequentialAgent
8. **entrypoint** — `main.py`: parses CLI prompt, creates ADK Runner, runs pipeline, prints final Java source
9. **update-docs** — Update README.md and .github/copilot-instructions.md with build/run commands and architecture

## Dependencies
- shell-tools must be done before test-runner-agent
- first-version-agent, test-writer-agent, test-runner-agent, code-improver-agent must be done before pipeline
- pipeline must be done before entrypoint
