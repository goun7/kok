"""G42 README-pin: KOK README'sindeki rust+python test-sayilari taze-olcume-karsi.

Rust-tarafi: `cargo test --workspace --all-targets` test-result-satirlarinin
toplami. Python-tarafi: `pytest tests/ --collect-only -q` sonucu.
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _collected_total(res_stdout: str) -> int:
    m = re.search(r"(\d+)\s+tests?\s+collected", res_stdout)
    if m:
        return int(m.group(1))
    total = 0
    for mm in re.finditer(r"^tests/[\w./-]+\.py:\s*(\d+)\s*$", res_stdout, re.M):
        total += int(mm.group(1))
    return total


def test_readme_test_counts_are_not_stale():
    readme = io.open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    res = subprocess.run(
        ["cargo", "test", "--workspace", "--all-targets"],
        cwd=ROOT, capture_output=True, text=True, timeout=1800,
    )
    assert res.returncode == 0, "cargo test basarisiz: %s" % res.stderr[-400:]
    rust_total = 0
    for m in re.finditer(r"test result: ok\.\s*(\d+) passed", res.stdout):
        rust_total += int(m.group(1))
    pyp = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=900,
    )
    assert pyp.returncode == 0, "pytest collect-only basarisiz: %s" % pyp.stderr[-400:]
    python_total = _collected_total(pyp.stdout)
    mismatches = []
    for m in re.finditer(r"#\s*(\d[\d.,]*)\s*passed,\s*0\s*failed", readme):
        claimed = int(m.group(1).replace(".", "").replace(",", ""))
        if claimed == rust_total:
            continue
        if claimed == python_total:
            continue
        mismatches.append(m.group(0))
    assert not mismatches, (
        "README test-sayilari stale: %s (taze: rust=%d python=%d)"
        % (mismatches, rust_total, python_total)
    )
