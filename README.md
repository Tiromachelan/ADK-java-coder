# ADK Java Coder

An AI agent pipeline built with [Google ADK](https://google.github.io/adk-docs/) that autonomously develops Java programs from a natural-language description. It generates an initial implementation, writes JUnit5 unit tests, compiles and runs them, and iteratively improves the code until all tests pass.

## Architecture

```
SequentialAgent (java_coder)
├── LlmAgent: first_version       ← generates initial Java source
└── LoopAgent: tdd_loop (max 20)
    └── SequentialAgent: tdd_cycle
        ├── LlmAgent: test_writer     ← writes JUnit5 tests
        ├── LlmAgent: test_runner     ← compiles & runs tests
        └── LlmAgent: code_improver   ← fixes failures
```

The loop exits early when all tests pass, or after 20 iterations.

## Setup

**Requirements:** Python 3.11+, Java JDK (for `javac` / `java`), internet access (to download JUnit5 jar on first run).

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set your GOOGLE_API_KEY
```

Get a free API key at https://aistudio.google.com/apikey

## Usage

```bash
python main.py "Write a Calculator class with add, subtract, multiply, and divide methods"
```

Generated Java files are written to `workspace/` (gitignored). The final source is printed to stdout at the end.

## Project Layout

```
agents/               ← one file per LlmAgent
tools/shell_tools.py  ← FunctionTools: write_file, read_file, compile_java, run_tests, download_junit5
pipeline.py           ← assembles the full agent tree
main.py               ← CLI entry point
workspace/            ← runtime-generated Java files and compiled classes (gitignored)
```
