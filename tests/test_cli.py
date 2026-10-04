from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


ROOT = Path(__file__).parents[1]
CORRECT = ROOT / "fixtures/agent-loop-context.correct.json"
INCORRECT = ROOT / "fixtures/agent-loop-context.incorrect.json"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    source_path = str(ROOT / "src")
    environment["PYTHONPATH"] = source_path + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "csx.cli", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_replay_cli_is_offline_and_stable() -> None:
    first = run_cli("replay", str(CORRECT))
    second = run_cli("replay", str(CORRECT))
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert "green" in first.stdout


def test_verify_reports_failing_invariant() -> None:
    result = run_cli("verify", str(INCORRECT))
    assert result.returncode == 1
    assert '"failed_assertions": [\n    "a0",\n    "a1"\n  ]' in result.stdout


def test_compare_cli_shows_context_difference() -> None:
    result = run_cli("compare", str(CORRECT), str(INCORRECT))
    assert result.returncode == 0
    assert '"event_id": "e1"' in result.stdout
