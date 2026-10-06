"""The remaining untested 40+ line security probes, branch-cut.

The AST sweep of the 47 root prototype modules (public, non-underscore
functions of 40+ lines whose name never appears under tests/) left 21
functions. The four below are the canonical-binding and economic-security
survivors, and each maps to a Rust crate in crates/ that already carries its
own cargo suite:

  probe_round5f_air_en.r5f1_the_air_relation_is_a_real_constraint
      -> crates/kok-fri / crates/kok-proof (the AIR commitment binding the
         fri/proof crates' canonical.rs and air.rs exercise in Rust)
  probe_g_layer_size_en.probe_verify_matches_prove_across_sizes
      -> crates/kok-poum (prove/verify size parity over the PoW kernel)
  probe_blindspot_en.probe_double_settle
  probe_blindspot_en.probe_late_challenge
      -> crates/kok-u-layer (the escrow's terminal-state guards)

The underlying module logic is already covered by tests/test_kok_proof_stack.py
and tests/test_u_layer_chain.py; what was NOT covered was the probe layer
itself. That matters here because this project has been bitten repeatedly by
probes that pass without measuring anything (an `except Exception: pass` that
swallowed every run, a substring pass criterion that matched its own failure,
a return value that was discarded so the exit status was always 0). So every
probe below is cut on BOTH arms:

  - the honest arm: the probe runs on the current module and its verdict is
    what the property claims, and
  - the fault arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE — proving the verdict is earned
    rather than unfalsifiable.

Faults are applied with unittest.mock.patch.object as context managers, so
the module is restored before the next test. Nothing outside this file is
modified. stdlib only.
"""

import contextlib
import io
import random

import pytest
from unittest import mock

import f0b_air_proto as air_mod
import u_layer_prototype_en as ul
import probe_round5f_air_en as probe_air
import probe_g_layer_size_en as probe_g
import probe_blindspot_en as probe_blindspot


# ------------------------------------------------------------------ helpers
def _run(fn):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn()
    return rv, buf.getvalue()


def _drive_u_layer(seed=11):
    """The smallest honest U-layer task: enough empty blocks to seed the VRF
    epoch, then submit -> assign -> mine -> validate."""
    ch = ul.Chain()
    rng = random.Random(seed)
    q, n = 97, 8
    A = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rng.randrange(q) for _ in range(n)] for _ in range(n)]
    zero = [[0] * n for _ in range(n)]
    for _ in range(ul.EPOCH_LOOKBACK + 2):
        blk = ch.mine_block("m1", [], zero, zero)
        ch.validate_block(blk, zero, zero)
    spec = ul.TaskSpec("mm", (A, B), 64, 1000)
    t = ch.submit_task("c1", spec, 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A, B)
    ch.validate_block(blk, A, B)
    return ch, t


# ============================ R5F-1: the AIR commitment binding
def _toy_witness(seed=1, n=8, q=97):
    """A self-consistent trace[t+1] = trace[t] + a[t]*b[t] (mod q), exactly
    as the probe builds one."""
    rng = random.Random(seed)
    a = [rng.randrange(q) for _ in range(n)]
    b = [rng.randrange(q) for _ in range(n)]
    trace = [0]
    for t in range(n - 1):
        trace.append((trace[-1] + a[t] * b[t]) % q)
    acc = sum(a[t] * b[t] for t in range(n - 1)) % q
    return {"a": a, "b": b, "trace": trace}, acc


def test_r5f1_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_air.r5f1_the_air_relation_is_a_real_constraint)
    assert rv, "the R5F-1 probe must hold on the current module"


def test_r5f1_the_commitment_binds_the_witness():
    air = air_mod.MerkleTileAIR(q=97, r=2)
    proof, acc = _toy_witness()
    root = air.commit(proof)

    honest_ok = air.verify_sample(proof, root, acc, 3)
    assert honest_ok, "an honest proof must verify under its own root"

    # a forged but SELF-CONSISTENT proof: one tile changed and the trace
    # rebuilt to stay internally consistent with the changed term
    a2 = list(proof["a"])
    a2[3] = (a2[3] + 1) % 97
    trace2 = [0]
    for t in range(len(a2) - 1):
        trace2.append((trace2[-1] + a2[t] * proof["b"][t]) % 97)
    forged = {"a": a2, "b": proof["b"], "trace": trace2}

    assert air.commit(forged) != root, \
        "the commitment must change when the witness changes"
    assert not air.verify_sample(forged, root, acc, 3), \
        "a forged proof must not verify under the ORIGINAL root"


def test_r5f1_detects_a_commitment_that_ignores_the_proof():
    # the failure mode that makes an AIR cosmetic: commit() stops depending
    # on the witness, so a forged proof recomputes the same root
    with mock.patch.object(air_mod.MerkleTileAIR, "commit",
                           lambda self, proof: 42):
        rv, _ = _run(probe_air.r5f1_the_air_relation_is_a_real_constraint)
    assert not rv, \
        "R5F-1 must fail when the commitment no longer binds the witness"


def test_r5f1_detects_a_verifier_that_accepts_every_sample():
    with mock.patch.object(air_mod.MerkleTileAIR, "verify_sample",
                           lambda self, *a, **k: True):
        rv, _ = _run(probe_air.r5f1_the_air_relation_is_a_real_constraint)
    assert not rv, \
        "R5F-1 must fail when the sampled verifier never rejects"


# ==================== G-layer: prove/verify parity across matrix sizes
def test_g_layer_size_probe_passes_across_sizes_and_rejects_a_forged_tile():
    rv, _ = _run(probe_g.probe_verify_matches_prove_across_sizes)
    assert rv, \
        "verify must derive the size from the input at every size and " \
        "reject a forged tile value"


def test_g_layer_size_probe_detects_a_verifier_that_never_rejects():
    # the probe loads the kernel module by relative path and re-executes it,
    # so the fault is handed to the probe through its own _load() hook
    mod = probe_g._load()
    with mock.patch.object(mod.KWKernel, "verify", lambda self, *a, **k: True):
        with mock.patch.object(probe_g, "_load", lambda: mod):
            rv, _ = _run(probe_g.probe_verify_matches_prove_across_sizes)
    assert not rv, \
        "the size probe must fail when verify stops rejecting forgeries"


# ==================================== U-layer: the escrow terminal states
def test_double_settle_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_blindspot.probe_double_settle)
    assert rv, "the double-settle corner must hold on the current module"


def test_a_second_settle_is_a_no_op():
    ch, t = _drive_u_layer()
    task = ch.tasks[t.tid]
    assert task.state == "SOLVED"
    before = (task.escrow, task.burned)

    pay1 = ch.settle(t.tid)
    mid = (task.escrow, task.burned, task.state)
    pay2 = ch.settle(t.tid)
    after = (task.escrow, task.burned, task.state)

    assert pay1 == task.fee - task.burned == 90
    assert pay2 == 0, "a settled task must pay nothing the second time"
    assert mid == after, "the books must not move on the second settle"
    assert before != mid, "the first settle must actually move the books"


def test_double_settle_detects_a_missing_terminal_guard():
    def buggy_settle(self, tid):
        t = self.tasks[tid]
        t.state = "SETTLED"
        pay = t.fee - t.burned
        t.escrow -= pay
        return pay

    with mock.patch.object(ul.Chain, "settle", buggy_settle):
        rv, _ = _run(probe_blindspot.probe_double_settle)
    assert not rv, \
        "the double-settle corner must fail when settle() stops guarding " \
        "the terminal state"


def test_late_challenge_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_blindspot.probe_late_challenge)
    assert rv, "the late-challenge corner must hold on the current module"


def test_a_late_challenge_is_rejected_and_moves_no_books():
    ch, t = _drive_u_layer()
    task = ch.tasks[t.tid]
    ch.settle(t.tid)
    before = (task.escrow, task.burned, task.state)

    out = ch.challenge("bob", t.tid, ch.height())
    after = (task.escrow, task.burned, task.state)

    assert out[0] == "SETTLED_ALREADY", \
        "a challenge on a settled task must name the terminal outcome: %s" \
        % (out,)
    assert before == after, "the books must not move on a settled task"
    assert "bob" in ch.miners, \
        "the challenger must still be registered on the non-fraud path"


def test_late_challenge_detects_a_missing_settled_guard():
    def buggy_challenge(self, challenger, tid, height):
        # the settled short-circuit is removed: the challenge falls through
        # to the verdict path on a task that is already terminal
        self.miners.setdefault(challenger, {"bond": 0, "slashed": 0})
        self.miners[challenger]["slashed"] += 1
        return "CHALLENGE_REJECTED", 0

    with mock.patch.object(ul.Chain, "challenge", buggy_challenge):
        rv, _ = _run(probe_blindspot.probe_late_challenge)
    assert not rv, \
        "the late-challenge corner must fail when the settled guard is " \
        "removed and the outcome stops being SETTLED_ALREADY"
