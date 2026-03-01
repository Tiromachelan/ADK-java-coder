"""Shell-based tools for compiling and running Java code with JUnit5."""

import os
import subprocess
import urllib.request
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent / "workspace"
LIB_DIR = WORKSPACE / "lib"
JUNIT_JAR = LIB_DIR / "junit-platform-console-standalone.jar"
JUNIT_URL = (
    "https://repo1.maven.org/maven2/org/junit/platform/"
    "junit-platform-console-standalone/1.10.2/"
    "junit-platform-console-standalone-1.10.2.jar"
)


def write_file(filename: str, content: str) -> str:
    """Write content to a file inside workspace/. filename is relative to workspace/.

    Args:
        filename: Relative path inside workspace/ (e.g. 'Calculator.java').
        content: Full text content to write.

    Returns:
        Confirmation message with absolute path written.
    """
    target = WORKSPACE / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written: {target}"


def read_file(filename: str) -> str:
    """Read a file from workspace/.

    Args:
        filename: Relative path inside workspace/ (e.g. 'Calculator.java').

    Returns:
        File contents as a string, or an error message if not found.
    """
    target = WORKSPACE / filename
    if not target.exists():
        return f"ERROR: File not found: {target}"
    return target.read_text(encoding="utf-8")


def list_files() -> str:
    """List all files currently in workspace/.

    Returns:
        Newline-separated list of relative file paths.
    """
    if not WORKSPACE.exists():
        return "workspace/ does not exist yet."
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    return "\n".join(files) if files else "workspace/ is empty."


def download_junit5() -> str:
    """Download the JUnit5 Platform Console Standalone jar to workspace/lib/ if not present.

    Returns:
        Status message indicating whether it was downloaded or already existed.
    """
    if JUNIT_JAR.exists():
        return f"JUnit5 jar already present: {JUNIT_JAR}"
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(JUNIT_URL, JUNIT_JAR)
        return f"Downloaded JUnit5 jar to {JUNIT_JAR}"
    except Exception as e:
        return f"ERROR downloading JUnit5 jar: {e}"


def compile_java(filenames: list[str]) -> str:
    """Compile one or more Java source files in workspace/ using javac.

    Args:
        filenames: List of .java filenames relative to workspace/ to compile.

    Returns:
        Compiler stdout+stderr output. Empty string means success.
    """
    if not filenames:
        return "ERROR: No filenames provided."

    sources = [str(WORKSPACE / f) for f in filenames]
    classpath = str(JUNIT_JAR) if JUNIT_JAR.exists() else "."
    cmd = ["javac", "-cp", classpath, "-d", str(WORKSPACE)] + sources

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return f"Compilation successful.\n{output}".strip()
    return f"Compilation failed (exit {result.returncode}):\n{output}"


def run_tests(test_class: str) -> str:
    """Run a JUnit5 test class using the console standalone launcher.

    Args:
        test_class: Fully qualified class name of the JUnit5 test (e.g. 'CalculatorTest').

    Returns:
        Combined stdout+stderr from the test runner including pass/fail summary.
    """
    if not JUNIT_JAR.exists():
        return "ERROR: JUnit5 jar not found. Call download_junit5() first."

    classpath = f"{WORKSPACE}{os.pathsep}{JUNIT_JAR}"
    cmd = [
        "java", "-cp", classpath,
        "org.junit.platform.console.ConsoleLauncher",
        "--select-class", test_class,
        "--details", "verbose",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORKSPACE))
    return (result.stdout + result.stderr).strip()
