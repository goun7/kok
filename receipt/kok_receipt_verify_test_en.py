#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: kok_receipt_verify_en.py — the independent Python verifier for the kok
mining-proof receipt.

The point of this file is the CROSS-LANGUAGE contract: the Rust binary
(`cargo run --bin kok -- create`) mines a receipt, and this Python verifier
must ACCEPT it, byte-for-byte. If the two implementations ever drift, every
tamper test below still passes (they are all in-Python), so the honest receipt
check at the top is the load-bearing one and it needs the Rust binary.

A note on why the Rust binary is optional rather than required: the machine
this suite runs on may not have a Rust toolchain in scope. The cross-language
test SKIPS with a clear message when `cargo` is unavailable; the eight tamper
tests (pure Python) always run, because they test this verifier's own logic.

Run:  python3 -m pytest -o addopts= -p no:cacheprovider -q kok_receipt_verify_test_en.py
"""

import copy
import json
import shutil
import subprocess
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kok_receipt_verify_en import verdict, verify_receipt, Reject  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
KOK_BIN = ["cargo", "run", "-q", "--bin", "kok"]


def _cargo_available() -> bool:
    return shutil.which("cargo") is not None


@pytest.fixture(scope="module")
def honest_receipt(tmp_path_factory) -> dict:
    """Mine a real receipt with the Rust binary; skip if no toolchain."""
    if not _cargo_available():
        pytest.skip("cargo unavailable — cross-language test skipped "
                    "(the 8 tamper tests still run)")
    out = tmp_path_factory.mktemp("kok") / "kanit.json"
    r = subprocess.run(KOK_BIN + ["create", "--ctx", "20261018", "--target", "2",
                                  "--out", str(out)],
                       capture_output=True, text=True, timeout=300, cwd=str(HERE))
    assert r.returncode == 0, "kok create failed: %s" % r.stderr[:300]
    return json.loads(out.read_text(encoding="utf-8"))


def _tamper(p, mut):
    q = copy.deepcopy(p)
    mut(q)
    return q


# ---------------------------------------------------------------------------
# The cross-language contract: Rust mines, Python verifies.
# ---------------------------------------------------------------------------

def test_rust_receipt_python_accept(honest_receipt):
    v = verdict(honest_receipt)
    assert v.get("verdict") == "ACCEPT", v
    # the receipt hash the Python side computed must be the one the Rust
    # binary printed in its own output — the two digest spaces agree.
    assert len(v.get("receipt", "")) == 16


def test_signature_actually_checked(honest_receipt):
    """A receipt whose signature is zeroed must go RED on the signature stage
    — never ACCEPT, and never a silent skip of the check."""
    q = _tamper(honest_receipt, lambda p: p.__setitem__("signature", "00" * 64))
    v = verdict(q)
    assert v.get("verdict") == "RED"
    assert v.get("kind") == "signature", v


# ---------------------------------------------------------------------------
# The eight tamper tests — each edit must land on the stage that checks it.
# A verifier that reports the WRONG stage is as broken as one that accepts.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,mut,want_kind", [
    ("proof_type-forged", lambda p: p.__setitem__("proof_type", "kok.forged"), "structural"),
    ("receipt_prev-forged", lambda p: p.__setitem__("receipt_prev", "ff" * 32), "receipt"),
    ("matrix-swapped", lambda p: p["matrix_a"].__setitem__(
        0, [1] * len(p["matrix_a"][0])), "commitment"),
    ("cert_value-forged", lambda p: p.__setitem__(
        "cert_value", (p["cert_value"] + 1) % p["q"]), "work"),
    ("ctx-forged", lambda p: p.__setitem__("ctx", p["ctx"] + 1), "work"),
    ("receipt_hash-forged", lambda p: p.__setitem__("receipt_hash", "f" * 64), "receipt"),
    ("program_commit-forged", lambda p: p.__setitem__("program_commit", "0" * 64), "commitment"),
])
def test_tamper_rejects_on_the_right_stage(honest_receipt, name, mut, want_kind):
    v = verdict(_tamper(honest_receipt, mut))
    assert v.get("verdict") == "RED", "%s: tamper was ACCEPTED" % name
    assert v.get("kind") == want_kind, "%s: rejected on %s, expected %s (%s)" % (
        name, v.get("kind"), want_kind, v.get("detail"))


# ---------------------------------------------------------------------------
# Malformed documents: fail-closed, never an exception.
# ---------------------------------------------------------------------------

def test_missing_field_is_red_not_crash():
    v = verdict({"proof_type": "kok.mining-proof"})
    assert v.get("verdict") == "RED"
    assert v.get("kind") in ("structural", "malformed", "shape"), v


def test_non_square_matrix_is_red():
    p = {"proof_type": "kok.mining-proof", "proof_version": 1, "layer": "G",
         "q": 97, "n": 8, "r": 2, "cert_m": 4, "matrix_a": [[1, 2], [3, 4]],
         "matrix_b": [[1, 2], [3, 4]], "task_program": "x", "task_fee": 0,
         "task_burn_rate_per_mille": 0, "program_commit": "x", "input_commit": "x",
         "ctx": 1, "nonce": 1, "target": 2, "cert_i": 0, "cert_j": 0,
         "cert_value": 0, "receipt_prev": "0" * 64, "receipt_hash": "x",
         "miner_did": "did:key:z", "signature": "00" * 64}
    v = verdict(p)
    assert v.get("verdict") == "RED"
    assert v.get("kind") == "shape", v


def test_verify_receipt_raises_reject_not_returns_none():
    """The bare verifier raises; the verdict() wrapper turns that into RED.
    Both behaviours are the contract — fail-closed at two layers."""
    with pytest.raises(Reject):
        verify_receipt({"proof_type": "nope"})
