"""The last untested probe functions, branch-cut: 12 probes that DO measure.

An AST sweep of the root prototype modules (public, non-underscore functions
of 40+ lines whose name never appears under tests/) left 15 functions. Three
of them (r5d2, r5d4, r5e2) return True through a swallow path and measure
nothing -- they are cut separately in test_kok_vacuous_probes.py, where the
swallow itself is the thing under test. The twelve here are the probes whose
verdict is EARNED: each is cut on BOTH arms,

  - the honest arm: the probe runs on the current module and its verdict is
    what its claim says, and
  - the fault arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE -- proving the verdict is falsifiable
    rather than a tautology of its own construction.

This project has been bitten repeatedly by probes that pass without measuring
anything (an `except Exception: pass` that swallowed every run, a substring
pass criterion that matched its own failure, a return value that was
discarded). The fault arms below exist precisely because a probe that cannot
fail cannot certify anything, so each fault is chosen to be the failure the
probe's own claim names:

  F-1 / F-2 (field)   verify() stops rejecting a fabricated proof
  F-8 (field)         prove() regains the unfalsifiable identity assert
  F-5 (fri)           the file stops retracting the "logarithmic" claim
  F-7 (fri)           verify_round stops rejecting any tampered coefficient
  TV-65 (zk)          the mask stops being recomputeable from the seed
  R5D-3 (u-layer)     the chain accepts a block with duplicated proofs
  TV-21 (g-layer)     a low-entropy v passes the noise floor
  R5B-2 (e-gap)       Arm A stops accepting every self-consistent cert
  R6B-1 (paper)       a cited file's own N/M counts disagree
  R5B-7 (re-derive)   the file stops stating the commitment-bound limit

Faults are applied with unittest.mock.patch.object as context managers, so
the module is restored before the next test. The two source-text probes
(F-5, R5B-7) read a module's own source as their measurement; for them the
fault is handed through the source-reading path the probe itself uses, so
the simulated file genuinely loses the statement the probe checks for.
Nothing outside this file is modified. stdlib only.
"""

import contextlib
import inspect
import io
import os

import pytest
from unittest import mock

import f0b_air_proto as air_mod
import f0b_fri_en as fri_mod
import f0b_prod_field_en as field_mod
import g_layer_tests as g_tr
import g_layer_tests_en as g_en
import probe_f0b_zk_en as probe_zk
import probe_round5a_field_en as probe_field
import probe_round5a_fri_en as probe_fri
import probe_round5b_egap_en as probe_egap
import probe_round5b_rederive_en as probe_rederive
import probe_round5d_ulayer_en as probe_ulayer
import probe_round6b_paper_en as probe_paper
import spec_rederive_en as spec_mod
import tv72_egap_mechanism_en as egap_mod
import u_layer_prototype_en as ul_mod


# ------------------------------------------------------------------ helpers
def _run(fn):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn()
    return rv, buf.getvalue()


# ================================================ R5A-FIELD: input binding
def test_f1_field_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_field.f1_verify_ignores_its_own_binding_arguments)
    assert rv, "F-1 must confirm verify() binds the witness to the inputs"


def test_f1_field_probe_detects_a_verifier_that_accepts_every_proof():
    with mock.patch.object(field_mod.TileAIRProd, "verify",
                           lambda self, *a, **k: True):
        rv, _ = _run(probe_field.f1_verify_ignores_its_own_binding_arguments)
    assert not rv, \
        "F-1 must fail when verify() accepts a fabricated proof under every " \
        "commitment -- the binding would then live in the docstring only"


def test_f2_field_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_field.f2_toy_catches_the_same_forgery)
    assert rv, \
        "F-2 must confirm the production port rejects the toy's forgery"


def test_f2_field_probe_detects_a_verifier_that_accepts_the_forgery():
    with mock.patch.object(field_mod.TileAIRProd, "verify",
                           lambda self, *a, **k: True):
        rv, _ = _run(probe_field.f2_toy_catches_the_same_forgery)
    assert not rv, \
        "F-2 must fail when the production port accepts the forgery the toy " \
        "rejects"


# ======================================== R5A-FIELD: prove's unfalsifiables
def test_f8_field_probe_passes_on_the_honest_module():
    rv, out = _run(probe_field.f8_prove_assertions_cannot_fail)
    assert rv, "F-8 must confirm prove() carries no identity assert"


def _prove_with_an_identity_assert(self, A, B, ctx, i, j):
    """The bug F-8 guards: an assert that holds for every possible input
    (row counts always match at call sites the kernel itself controls),
    so it documents itself instead of guarding anything."""
    assert len(A) == len(B), "row counts must match"
    m = len(A) // self.r
    tr = [0] * (m + 1)
    return {"trace": tr, "acc": 0}


def test_f8_field_probe_detects_an_unfalsifiable_assert_returning():
    with mock.patch.object(field_mod.TileAIRProd, "prove",
                           _prove_with_an_identity_assert):
        # the fault is real: prove() now carries an assert, and it still
        # returns a well-formed proof for every input, exactly as the bug
        # requires (the predicate cannot fail, so nothing else changes)
        src = inspect.getsource(field_mod.TileAIRProd.prove)
        assert "assert" in src
        rv, out = _run(probe_field.f8_prove_assertions_cannot_fail)
    assert not rv, \
        "F-8 must fail when prove() regains an assert that no input can break"


# ============================================ R5A-FRI: the cost retraction
def test_f5_fri_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_fri.f5_verify_round_is_linear_in_the_field_not_logarithmic)
    assert rv, \
        "F-5 must confirm the file measures the linear cost and retracts " \
        "the logarithmic claim"


def test_f5_fri_probe_detects_the_retraction_being_removed():
    real_getsource = probe_fri.inspect_getsource
    assert "NOT logarithmic" in real_getsource(fri_mod), \
        "the honest file retracts the logarithmic claim in its own header"

    def retraction_removed(mod):
        # the file as it was before the fix: the measurement is gone and the
        # retraction with it, so the header's "logarithmic" claim stands again
        return real_getsource(mod).replace("NOT logarithmic", "NOT-logarithmic")

    with mock.patch.object(probe_fri, "inspect_getsource", retraction_removed):
        assert "NOT logarithmic" not in retraction_removed(fri_mod)
        rv, _ = _run(probe_fri.f5_verify_round_is_linear_in_the_field_not_logarithmic)
    assert not rv, \
        "F-5 must fail when the file stops retracting the logarithmic claim " \
        "while still printing the cost under a MEASURED label"


# ============================================= R5A-FRI: tamper coverage
def test_f7_fri_probe_passes_on_the_honest_module():
    rv, out = _run(probe_fri.f7_tamper_probe_only_tests_one_constant_of_one_round)
    assert rv, "F-7 must confirm every tampered coefficient of every round " \
               "is caught"


def test_f7_fri_probe_detects_a_verifier_that_never_rejects_a_tamper():
    with mock.patch.object(fri_mod.FriRecursive, "verify_round",
                           lambda self, *a, **k: True):
        rv, out = _run(probe_fri.f7_tamper_probe_only_tests_one_constant_of_one_round)
    assert not rv, \
        "F-7 must fail when verify_round accepts every tampered coefficient, " \
        "because the caught/tried coverage it reports would then be a lie"
    assert "SOME MISSED" in out, \
        "the fault must actually move the probe's own coverage print"


# ============================================== F0B-ZK: the missing hiding
def test_tv65_probe_reproduces_the_leak_on_the_honest_module():
    (ok, leaked, sound), _ = _run(probe_zk.tv65_zero_knowledge_is_absent)
    assert ok and leaked and sound, \
        "TV-65 must reproduce the leak: the verifier recovers the full " \
        "witness from its own seed while the proof still verifies " \
        "(soundness intact, zero-knowledge absent)"


def _mask_with_a_secret_key(self, proof, seed):
    """The fix TV-65 demands: a blinding factor the verifier cannot
    recompute from the seed it holds. Same shape as the real mask() so the
    probe's unmasking arithmetic still runs -- only the key changes."""
    q = self.q
    m = len(proof["a"])
    d = [air_mod.H("otp-secret", 42424242, t) % q for t in range(m + 2)]
    return {
        "trace": [(proof["trace"][t] + d[t]) % q for t in range(m + 1)],
        "a": [(proof["a"][t] + d[t + 1]) % q for t in range(m)],
        "b": [(proof["b"][t] + d[t + 2]) % q for t in range(m)],
        "d": d,
    }


def test_tv65_probe_detects_a_mask_the_verifier_cannot_recompute():
    with mock.patch.object(air_mod.ZkTileAIR, "mask", _mask_with_a_secret_key):
        (ok, leaked, sound), _ = _run(probe_zk.tv65_zero_knowledge_is_absent)
    assert not ok and not leaked, \
        "TV-65 must stop passing once the mask is no longer a function of " \
        "the verifier's seed -- the leak it certifies would then be closed " \
        "and the probe's ACCEPT would describe a different construction"


# ========================================= R5D-ULAYER: phi replay inflation
def test_r5d3_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_ulayer.r5d3_phi_cannot_be_inflated_by_replaying_a_proof)
    assert rv, "R5D-3 must confirm a replayed proof does not inflate phi"


def test_r5d3_probe_detects_a_chain_that_accepts_duplicated_proofs():
    with mock.patch.object(ul_mod.Chain, "validate_block",
                           lambda self, *a, **k: "ACCEPT"):
        rv, out = _run(probe_ulayer.r5d3_phi_cannot_be_inflated_by_replaying_a_proof)
    assert not rv, \
        "R5D-3 must fail when the chain accepts a block whose u_proofs were " \
        "replayed, because the duplicated flops would inflate phi"
    assert "duplicates WERE double-counted" in out, \
        "the fault must be the one the claim names (128 flops counted for 64)"


# ============================================ G-LAYER: the noise floor curve
def test_tv21_en_passes_and_the_attack_fails_at_every_v():
    (ok, sweep), _ = _run(g_en.tv21)
    assert ok is True, "TV-21 must pass on the honest toy model"
    assert sweep and all(not ok for _, _, ok in sweep), \
        "the peaked low-entropy attack must fail at every peak v"
    assert abs(sweep[-1][1] - 0.707) < 0.02, \
        "the noise/g ratio must pin to the ~0.707 asymptote"


def test_tv21_en_asserts_fire_when_an_attack_v_passes():
    def sweep_where_every_v_passes(v_list, *a, **k):
        return [(v, 0.5, True) for v in v_list]

    with mock.patch.object(g_en, "low_entropy_sweep",
                           sweep_where_every_v_passes):
        with pytest.raises(AssertionError, match="a v passed"):
            _run(g_en.tv21)


def test_tv21_tr_passes_and_the_attack_fails_at_every_v():
    (ok, sweep), _ = _run(g_tr.tv21)
    assert ok is True, "TV-21 (TR) must pass on the honest toy model"
    assert sweep and all(not ok for _, _, ok in sweep), \
        "the peaked low-entropy attack must fail at every peak v"
    assert abs(sweep[-1][1] - 0.707) < 0.02, \
        "the noise/g ratio must pin to the ~0.707 asymptote"


def test_tv21_tr_asserts_fire_when_an_attack_v_passes():
    def sweep_where_every_v_passes(v_list, *a, **k):
        return [(v, 0.5, True) for v in v_list]

    with mock.patch.object(g_tr, "low_entropy_sweep",
                           sweep_where_every_v_passes):
        with pytest.raises(AssertionError, match="bir v gecti"):
            _run(g_tr.tv21)


# ============================================== R5B-EGAP: Arm A's tautology
def test_r5b2_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_egap.r5b2_detectability_is_not_zero_by_a_rigged_arm_a)
    assert rv, "R5B-2 must confirm the file admits the 0% is by construction"


def _arm_a_that_rejects(commissioned, mined, ctx):
    """Arm A with an acceptance rule that CAN fail -- the 0% would then be
    an empirical result rather than a tautology of the arm's definition."""
    return object(), False


def test_r5b2_probe_detects_an_arm_a_that_rejects():
    with mock.patch.object(egap_mod, "arm_a_without_binding",
                           _arm_a_that_rejects):
        rv, out = _run(probe_egap.r5b2_detectability_is_not_zero_by_a_rigged_arm_a)
    assert not rv, \
        "R5B-2 must fail when Arm A stops accepting every self-consistent " \
        "cert, because the 'detectability 0 by construction' verdict would " \
        "no longer describe the arm"


# ============================================ R6B-PAPER: the cited scores
def test_r6b1_probe_passes_on_the_honest_module():
    if not os.path.isfile("f0b_fri_en.py"):
        pytest.skip("R6B-1 runs the cited files by relative path; needs "
                    "CWD=kok root")
    rv, out = _run(probe_paper.r6b1_paper_scores_match_the_code)
    assert rv, \
        "R6B-1 must confirm every score the paper states is still printed " \
        "by the file it names"
    assert "MATCH" in out


def test_r6b1_probe_detects_a_file_whose_counts_disagree():
    with mock.patch.object(probe_paper, "_count_in_output",
                           lambda path, pat: (1, 2)):
        rv, out = _run(probe_paper.r6b1_paper_scores_match_the_code)
    assert not rv, \
        "R6B-1 must fail when a file the paper cites prints a count whose " \
        "two halves disagree (an internal failure the paper would hide)"
    assert "COUNTS DISAGREE" in out


# ======================================== R5B-REDERIVE: the stated limit
def test_r5b7_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_rederive.r5b7_forgery_rejection_is_not_a_foregone_conclusion)
    assert rv, "R5B-7 must confirm the file states the commitment-bound limit"


def test_r5b7_probe_detects_the_limit_no_longer_being_stated():
    real_getsource = inspect.getsource
    assert "SELF-CONSISTENT" in real_getsource(spec_mod), \
        "the honest file states the limit its own probe checks for"

    def limit_removed(obj, *a, **k):
        src = real_getsource(obj)
        if obj is spec_mod:
            # the file as it was before the fix: the honest limit is gone,
            # so a reader cannot tell which property the forgery probe tests
            return src.replace("SELF-CONSISTENT", "SELFCONSISTENT")
        return src

    with mock.patch.object(inspect, "getsource", limit_removed):
        rv, _ = _run(probe_rederive.r5b7_forgery_rejection_is_not_a_foregone_conclusion)
    assert not rv, \
        "R5B-7 must fail when the file stops stating that the AIR constraints " \
        "hold for any self-consistent witness, because the probe's verdict " \
        "would then certify a text it no longer contains"
