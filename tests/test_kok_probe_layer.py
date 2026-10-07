"""The last untested layer of the KOK prototype corpus: the probes themselves.

An AST sweep of the root modules (public, non-underscore functions whose name
never appears under tests/) leaves ~120 functions in the PROBE layer -- the
round-5/round-6 adversarial probes, the E-gap certification probes, the FP8
noise probes TV-27..29, the Pass-model probes TV-61..64, the U-layer edge
probes TV-51..57 and the EN-output audit. The ~30 cut here are the most
load-bearing of that layer.

Every probe is cut on BOTH arms, the convention the two preceding waves
established (test_kok_probe_measurement.py / test_kok_vacuous_probes.py):

  - the HONEST arm: the probe runs on the unbroken module and returns the
    verdict its own claim names (measured here first, then asserted), and
  - the FAULT arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE -- its verdict must flip. A probe
    that still passes over the broken invariant is unfalsifiable, which is
    the defect class this project has been bitten by (an `except: pass` that
    swallowed every run, a self-referential comparison that could not fail,
    a verdict field read off a nonexistent attribute and therefore always
    None). Each fault below is the failure the probe's own claim names.

The faults are applied as context-managed monkeypatches so the modules are
restored before the next test. Nothing outside this file is modified.
stdlib + pytest only; no network, no disk beyond the repo.
"""

from unittest import mock

import pytest

import audit_en_output as audit
import egap_cert_en as egap
import fp8_noise_proto_en as fp8
import g_layer_tests_en as g_en
import pass_sim_en as ps
import probe_pass_sim_en as probe_ps
import probe_round5b_egap_en as probe_r5b_egap
import probe_round5b_glayer_en as probe_r5b_g
import probe_u_layer_en as probe_u
import tv72_egap_mechanism_en as tv72
import u_layer_prototype_en as u_en


# ============================================================ Pass economic model
# The solver behind the paper's Theorem-1 regime map and its PR/2 attack-cost
# claim. The probes below pin the solver's OWN guarantees (Params regime
# bounds, the residual/consistency checks, the Bitconia reference, the F3a
# recalibration hook) rather than the economics.

def test_params_regime_bounds_are_derived_not_hardcoded():
    """Params.PR/Delta/theta_low/theta_high must be live functions of the
    fields. A hardcoded bound would silently survive a change to alpha/gamma."""
    p = ps.Params(e=0.006, R=2674.0, P=0.76, alpha=1.3, gamma=1.3)
    # Pearl's calibration values, measured independently:
    # PR = 0.76 * 2674 = 2032.24; Delta = 2/1.3 - 1 = 0.53846..
    # theta_low = alpha-1 = 0.3; theta_high = 1/(gamma-1) = 3.3333..
    assert p.PR == pytest.approx(2032.24, abs=1e-6)
    assert p.Delta == pytest.approx(2.0 / 1.3 - 1.0, abs=1e-12)
    assert p.theta_low == pytest.approx(0.3, abs=1e-12)
    assert p.theta_high == pytest.approx(1.0 / 0.3, abs=1e-12)
    # FALSIFIABLE ARM: move the fields and the bounds must move with them.
    # If any bound were a literal this comparison would not change.
    q = ps.Params(e=p.e, R=p.R, P=p.P, alpha=2.0, gamma=5.0)
    assert q.PR == p.PR                      # PR does not depend on alpha/gamma
    assert q.theta_low == pytest.approx(1.0, abs=1e-12)
    assert q.theta_high == pytest.approx(0.25, abs=1e-12)
    assert q.Delta == pytest.approx(1.0 / 5.0 + 1.0 / 2.0 - 1.0, abs=1e-12)
    assert q.Delta < 0 < p.Delta             # the sign flip the Bitconia branch keys on


def test_eq_residuals_are_zero_on_a_solved_equilibrium():
    """Eq.residuals must report ~0 for a real solution and a LARGE value for a
    contradictory one. Before the round-5 fix these were identities that could
    never fail; the falsifiable arm below is the check that makes them matter."""
    prm = ps.Params(e=0.006, R=2674.0, P=0.76, alpha=1.3, gamma=1.3)
    eq = ps.solve(prm)
    active, inactive = eq.residuals(prm)
    assert active, "a Duplexia equilibrium must have at least one active side"
    assert max(abs(r) for r in active) < 1e-12
    assert all(v == 0.0 for v in inactive)
    # FALSIFIABLE ARM: an equilibrium whose S contradicts the zero-profit
    # condition must produce a residual far from zero -- the residuals measure
    # something real, they are not a constant the solver prints.
    bad = ps.Eq(eq.name, eq.M, eq.L, eq.D, eq.S * 2.0, eq.Q, eq.p, eq.P, eq.theta)
    act2, _ = bad.residuals(prm)
    assert max(abs(r) for r in act2) > 1e-4


def test_eq_input_consistency_catches_a_theta_lie():
    """Eq.input_consistency compares the solver's OUTPUT against the caller's
    INPUT PR -- the check that exposed the round-5 off-by-one exponent (the
    shipped equilibrium reproduced PR to only one part in two while the
    residual reported 0.00e+00)."""
    prm = ps.Params(e=0.006, R=2674.0, P=0.76, alpha=1.3, gamma=1.3)
    eq = ps.solve(prm)
    rel_err, theta_out = eq.input_consistency(prm)
    assert rel_err < 1e-9
    assert theta_out == pytest.approx(eq.theta)
    # FALSIFIABLE ARM: a theta that disagrees with the held p and Q is caught
    # by this comparison and by nothing else in the Eq.
    rel2, _ = ps.Eq(eq.name, eq.M, eq.L, eq.D, eq.S, eq.Q, eq.p, eq.P,
                    eq.theta * 3.0).input_consistency(prm)
    assert rel2 > 1.0


def test_bitconia_ref_is_the_same_theta_baseline_the_paper_compares_against():
    """bitconia_ref is Pass's apples-to-apples baseline (same theta => same
    PR). Its S must equal what solve() itself returns in the Bitconia regime,
    or the security-ratio column the paper quotes is not a comparison of like
    with like."""
    prm = ps.Params(e=0.02, R=100.0, P=0.001, alpha=2.5, gamma=2.5)
    assert prm.Delta < 0                                    # the Bitconia regime
    eq = ps.solve(prm)
    assert eq.name.startswith("Bitconia")
    ref = ps.bitconia_ref(prm, eq.theta)
    assert ref["S"] == pytest.approx(eq.S, rel=1e-12)
    assert ref["Q"] == pytest.approx(eq.Q, rel=1e-12)
    assert ref["p"] == pytest.approx(prm.e, abs=1e-15)
    # FALSIFIABLE ARM: the reference is a FUNCTION of theta -- PR scales
    # linearly with it (PR = theta*e*Q_B). A constant would mean the
    # "same theta" comparison compares nothing.
    ref2 = ps.bitconia_ref(prm, eq.theta * 4.0)
    assert ref2["PR"] == pytest.approx(ref["PR"] * 4.0, rel=1e-12)
    assert ref2["S"] == pytest.approx(ref["S"] * 4.0, rel=1e-12)
    assert ref2["Q"] == pytest.approx(ref["Q"], rel=1e-12)


def test_recalibrate_f3a_reproduces_pearl_and_reads_real_quantities():
    """The F3a calibration hook: predict S from eS=PR, compare with the
    measured GPU count, and compare the model's revenue/cost ratio with the
    measured one. The rev_cost field used to read `eq.rev_cost`, an attribute
    the Eq dataclass never had, so it was ALWAYS None and the comparison
    named for it compared nothing."""
    gpus = ps.PEARL["gpus"]
    measured_rc = ps.PEARL["rev_day"] / ps.PEARL["cost_day"]
    r = ps.recalibrate_f3a(gpus, measured_rc, e=ps.PEARL["e"],
                           P=ps.PEARL["rpl_usd"], R=ps.PEARL["rpl_block"])
    assert r["S_predicted"] == pytest.approx(ps.PEARL["rpl_usd"] * ps.PEARL["rpl_block"]
                                             / ps.PEARL["e"], rel=1e-9)
    assert r["S_measured"] == gpus
    assert r["deviation_pct"] < 6.0                      # the regression guard
    assert r["Theorem1_consistent"] is True
    # the rev_cost field now holds a real number (not the old perpetual None)
    assert r["rev_cost_predicted"] is not None
    assert r["rev_cost_measured"] == measured_rc
    assert r["calibration_ok"] is False                  # 0.81 predicted vs 1.058 measured
    # FALSIFIABLE ARM 1: hand the model its own predicted ratio and the field
    # must flip to True -- it is comparing two computed numbers, not a number
    # against None.
    r_ok = ps.recalibrate_f3a(gpus, r["rev_cost_predicted"], e=ps.PEARL["e"],
                              P=ps.PEARL["rpl_usd"], R=ps.PEARL["rpl_block"])
    assert r_ok["calibration_ok"] is True
    # FALSIFIABLE ARM 2: a wild measured ratio is rejected, and a None is
    # rejected while the prediction is still produced.
    assert ps.recalibrate_f3a(gpus, 5.0, e=ps.PEARL["e"], P=ps.PEARL["rpl_usd"],
                              R=ps.PEARL["rpl_block"])["calibration_ok"] is False
    r_none = ps.recalibrate_f3a(gpus, None, e=ps.PEARL["e"], P=ps.PEARL["rpl_usd"],
                                R=ps.PEARL["rpl_block"])
    assert r_none["calibration_ok"] is False and r_none["rev_cost_predicted"] is not None
    # FALSIFIABLE ARM 3: the deviation is computed from the inputs, not
    # asserted -- a fabricated measurement produces a huge deviation.
    assert ps.recalibrate_f3a(10, 1.0, e=ps.PEARL["e"], P=ps.PEARL["rpl_usd"],
                              R=ps.PEARL["rpl_block"])["deviation_pct"] > 1e5
    # FALSIFIABLE ARM 4: Theorem1_consistent comes from classify_ok over the
    # SOLVED equilibrium -- a solver that returns the wrong regime flips it.
    broken = ps.Eq("Broken", 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5)
    with mock.patch.object(ps, "solve", lambda *a, **k: broken):
        rb = ps.recalibrate_f3a(gpus, measured_rc, e=ps.PEARL["e"],
                                P=ps.PEARL["rpl_usd"], R=ps.PEARL["rpl_block"])
        assert rb["Theorem1_consistent"] is False


# ============================================================ Pass model probes

def test_tv61_residuals_are_zero_in_all_regimes():
    """HONEST: every equilibrium the solver returns solves its own equations.
   FAULT: a solver that returns a contradictory equilibrium is noticed."""
    assert probe_ps.tv61_residuals_are_zero_in_all_regimes() is True
    broken = ps.Eq("Broken", 1.0, 1.0, 1.0, 1e-4, 999.0, 1.0, 1.0, 0.5)
    with mock.patch.object(probe_ps, "solve", lambda *a, **k: broken):
        assert probe_ps.tv61_residuals_are_zero_in_all_regimes() is False


def test_tv62_theta_stays_within_bounds_or_is_nan():
    """HONEST: _theta_from_PR returns a root inside (theta_low, theta_high) or
    NaN. FAULT: an out-of-bounds root is reported as a violation."""
    assert probe_ps.tv62_theta_stays_within_bounds() is True
    for bad_theta in (10.0, 0.01):
        with mock.patch.object(probe_ps, "_theta_from_PR", lambda p, _v=bad_theta: _v):
            assert probe_ps.tv62_theta_stays_within_bounds() is False


def test_tv63_no_root_parameters_yield_nan():
    """HONEST: parameters with no root in range yield NaN, not a bogus root.
    FAULT: a non-NaN answer for the same parameters is reported."""
    assert probe_ps.tv63_nan_params_marked_not_ok() is True
    with mock.patch.object(probe_ps, "_theta_from_PR", lambda p: 1.0):
        assert probe_ps.tv63_nan_params_marked_not_ok() is False


def test_tv64_regime_selection_tracks_the_sign_of_delta():
    """HONEST: Delta<0 selects Bitconia, and the draw range really reaches
    Delta<0 (exercised>0) so the branch is not vacuously untested.
    FAULT: a solver that returns another regime for Delta<0 is caught."""
    assert probe_ps.tv64_regime_selection_matches_delta_sign() is True
    broken = ps.Eq("Duplexia (pure D)", 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5)
    with mock.patch.object(probe_ps, "solve", lambda *a, **k: broken):
        assert probe_ps.tv64_regime_selection_matches_delta_sign() is False


# ============================================================ FP8 noise model

def test_tv27_subnormal_compression_is_measured_not_assumed():
    """HONEST: TV-27 returns PASS and the majority of subnormal E4M3 entries
    really flush to 0. FAULT: if quantization stops flushing subnormals the
    probe's own assertion fires -- the PASS is earned by the nonlinearity."""
    verdict, note = fp8.tv27_subnormal_compression()
    assert verdict == "PASS"
    assert "flushed to 0" in note
    with mock.patch.object(fp8, "fp8_quantize", lambda x, fmt="E4M3": 0.0 if x != x else x):
        with pytest.raises(AssertionError):
            fp8.tv27_subnormal_compression()


def test_tv28_reports_the_negative_result_the_attack_actually_produces():
    """HONEST: without a noise floor the low-entropy attack SUCCEEDS, and the
    probe reports it honestly as FAIL-FOR-KOK rather than as a PASS. This is
    the direction reversal vs the INT toy (TV-21 always gave RED).
    FAULT: if the INT noise model stops shrinking with magnitude the attack
    no longer materializes and the probe says so (SKIP) -- the negative result
    is produced by the dynamics, not by a hardcoded string."""
    verdict, note = fp8.tv28_low_entropy_attack_succeeds()
    assert verdict == "FAIL-FOR-KOK"
    assert "attack SUCCEEDS" in note
    with mock.patch.object(fp8, "noise_int_model",
                           lambda row, delta=fp8.DELTA: [10.0] * len(row)):
        verdict2, _ = fp8.tv28_low_entropy_attack_succeeds()
        assert verdict2 != "FAIL-FOR-KOK"


def test_tv29_the_noise_floor_is_what_closes_the_attack():
    """HONEST: with sigma_min the output tiles spread and TV-29 returns PASS.
    FAULT: drop the absolute floor and the tiles pin again, so the probe's
    assertion fires -- the floor, not the assert, is the load-bearing piece."""
    verdict, note = fp8.tv29_noise_floor_closes_attack()
    assert verdict == "PASS"
    assert "noise floor" in note
    with mock.patch.object(fp8, "noise_fp8_aware",
                           lambda row, sigma_min, fmt="E4M3": fp8.noise_int_model(row)):
        with pytest.raises(AssertionError):
            fp8.tv29_noise_floor_closes_attack()


def test_attack_rows_actually_builds_a_low_entropy_matrix():
    """attack_rows is the attack TV-28/29 measure. Its rows must be
    near-identical within the jitter it is given and bounded by the magnitude
    c, or the 'collapse to one bin' measurement is measuring something else."""
    import random
    rng = random.Random(2024)
    n, k, c, jitter = 12, 8, 2.0, 0.01
    A = fp8.attack_rows(rng, n, k, c, jitter)
    assert len(A) == n and all(len(r) == k for r in A)
    # every entry is base+c-epsilon, so bounded by c+jitter
    assert all(-c - jitter <= v <= c + jitter for r in A for v in r)
    # all rows sit within 2*jitter of one another (base + uniform noise)
    spread = max(max(a, b) - min(a, b) for ra, rb in zip(A, A[1:]) for a, b in zip(ra, rb))
    assert spread <= 2 * jitter + 1e-9
    # FALSIFIABLE ARM: zero jitter must give byte-identical rows, and at the
    # attack's own parameters the quantized output tiles really do collapse
    # to a single bin -- the premise TV-28 measures.
    z1 = fp8.attack_rows(random.Random(7), 3, 3, 1.0, 0.0)
    z2 = fp8.attack_rows(random.Random(7), 3, 3, 1.0, 0.0)
    assert z1 == z2 and z1[0] == z1[1] == z1[2]
    atk = fp8.attack_rows(random.Random(3), 16, 32, 1e-4, 1e-6)
    tiles = fp8.output_tiles(atk, [(-1.0) ** i for i in range(32)])
    assert len(set(fp8.quantize_vec(tiles, "E4M3"))) <= 2


# ============================================================ E-gap certification

def test_egap_foreign_matrices_are_rejected():
    """HONEST: a cert over foreign matrices does not verify against the task's
    own commitment. FAULT: collapse program_commit to a constant and the two
    commitments become indistinguishable, so the rejection disappears --
    the rejection tracks the commitment, nothing else."""
    assert egap.probe_foreign_matrices_rejected() is True
    with mock.patch.object(egap, "program_commit", lambda A, B: "CONSTANT"):
        assert egap.probe_foreign_matrices_rejected() is not True


def test_egap_own_matrices_are_accepted():
    """HONEST: a cert ground over the task's own matrices verifies.
    FAULT: if mining can no longer produce a cert the probe reports 'could not
    drive' (None) rather than a PASS -- the verdict needs a real certificate."""
    assert egap.probe_own_matrices_accepted() is True
    with mock.patch.object(egap, "g_cert_bound", lambda *a, **k: None):
        assert egap.probe_own_matrices_accepted() is None


def test_egap_cross_task_replay_is_rejected():
    """HONEST: a cert for task-1 does not verify as task-2's work. FAULT: a
    verifier that ignores the task_id accepts the replay, so the probe goes
    RED -- the anti-replay binding is the task identity check."""
    assert egap.probe_replay_for_another_task_rejected() is True
    with mock.patch.object(egap, "verify_g_cert_bound",
                           lambda cert, tid, pc, ctx, target, program=None: True):
        assert egap.probe_replay_for_another_task_rejected() is not True


def test_egap_commitment_is_content_bound():
    """HONEST: independently-built identical matrices give the same commitment
    and a one-entry change gives a different one. FAULT: a commitment that
    ignores content makes different matrices collide, so the probe goes RED --
    the whole binding rests on this being a function of the inputs."""
    assert egap.probe_commitment_is_content_bound() is True
    with mock.patch.object(egap, "program_commit", lambda A, B: "CONSTANT"):
        assert egap.probe_commitment_is_content_bound() is not True


# ============================================================ round-5b E-gap probes

def test_r5b3_the_identical_matrix_verifies_and_one_entry_off_rejects():
    """HONEST: Arm B accepts the commissioned matrices and rejects a matrix
    differing in one entry. FAULT: an Arm B that accepts everything makes the
    one-entry-off cert pass, so the probe reports the finding."""
    assert probe_r5b_egap.r5b3_the_identical_matrix_is_not_specially_handled_to_force_a_pass() is True
    with mock.patch.object(tv72, "arm_b_with_binding", lambda comm, ctx, mined=None: ({}, True)):
        assert probe_r5b_egap.r5b3_the_identical_matrix_is_not_specially_handled_to_force_a_pass() is False


def test_r5b4_the_tile_value_and_commitment_depend_on_the_matrix():
    """HONEST: the tile value is a function of the matrix and two matrices
    equal mod 97 but different as ints still get different commitments.
    FAULT: a commitment that ignores content makes the two commits equal, so
    the binding is shown to be vacuous."""
    assert probe_r5b_egap.r5b4_the_tile_value_genuinely_depends_on_the_matrix() is True
    with mock.patch.object(tv72, "program_commit_single", lambda M: "CONSTANT"):
        assert probe_r5b_egap.r5b4_the_tile_value_genuinely_depends_on_the_matrix() is False


# ============================================================ round-5b G-layer probes

def test_r5b9_the_verify_size_fix_is_load_bearing():
    """HONEST: verify() works on matrices whose size differs from the kernel's
    default n, and the OLD access A[self.n] really does raise IndexError on a
    smaller matrix -- so the fix is not a no-op. FAULT: shrink the kernel's
    default n so A[self.n] becomes a valid index and the probe can no longer
    exhibit the bug, proving the verdict depends on the real size gap."""
    assert probe_r5b_g.r5b9_verify_size_fix_is_not_a_no_op() is True

    def tiny_n(self, q=97, n=8, r=2):
        self.q, self.n, self.r = q, 2, r

    with mock.patch.object(g_en.KWKernel, "__init__", tiny_n):
        assert probe_r5b_g.r5b9_verify_size_fix_is_not_a_no_op() is False


def test_r5b10_cost_independence_is_measured_across_many_draws():
    """HONEST: cost_of_prove is the same over 12 random contents (one distinct
    value), so the input-independence claim is tested, not assumed from a
    single draw. FAULT: a cost that depends on the content produces many
    distinct values, and the probe reports the finding."""
    assert probe_r5b_g.r5b10_cost_independence_is_not_a_single_draw() is True
    with mock.patch.object(g_en, "cost_of_prove",
                           lambda A, B, ctx, D: sum(sum(r) for r in A)):
        assert probe_r5b_g.r5b10_cost_independence_is_not_a_single_draw() is False


def test_r5b11_forgery_rejection_is_not_only_at_the_default_size():
    """HONEST: an honest tile verifies at every size and a cert verified
    against a foreign ctx is rejected. FAULT: a verify() that accepts
    everything lets the foreign ctx through, so the probe goes RED."""
    assert probe_r5b_g.r5b11_the_forgery_rejection_is_not_only_at_the_default_size() is True
    with mock.patch.object(g_en.KWKernel, "verify", lambda self, *a, **k: True):
        assert probe_r5b_g.r5b11_the_forgery_rejection_is_not_only_at_the_default_size() is False


# ============================================================ U-layer edge probes

def test_tv51_escrow_is_exactly_zero_after_settle():
    """HONEST: after settlement escrow==0, the miner is paid the payable part
    (70 of 100) and the burn address holds the 30 burned at submission.
    FAULT: reintroduce the double subtraction of the burn (t.escrow -=
    burned+pay) and the field goes to -30, exactly the bookkeeping bug this
    probe is the regression guard for."""
    assert probe_u.tv51_escrow_nonnegative_after_settle() is True

    def double_subtract(self, tid):
        t = self.tasks[tid]
        if t.state not in ("SOLVED",):
            return 0
        t.state = "SETTLED"
        pay = t.fee - t.burned
        t.escrow -= (t.burned + pay)
        return pay

    with mock.patch.object(u_en.Chain, "settle", double_subtract):
        assert probe_u.tv51_escrow_nonnegative_after_settle() is False


def test_tv52_double_settle_pays_once():
    """HONEST: the second settle pays 0. FAULT: a settle that does not mark the
    state terminal pays the miner twice for one task."""
    assert probe_u.tv52_double_settle_pays_once() is True

    def pays_twice(self, tid):
        t = self.tasks[tid]
        if t.state not in ("SOLVED", "SETTLED"):
            return 0
        t.state = "SETTLED"
        return t.fee - t.burned

    with mock.patch.object(u_en.Chain, "settle", pays_twice):
        assert probe_u.tv52_double_settle_pays_once() is False


def test_tv53_a_slashed_task_pays_the_miner_nothing():
    """HONEST: a SLASHED task pays 0, the state is terminal and the bond is
    actually debited. FAULT: a settle that ignores the terminal state pays a
    slashed task's escrow out anyway."""
    assert probe_u.tv53_slashed_task_pays_miner_nothing() is True

    def pays_regardless(self, tid):
        t = self.tasks[tid]
        t.state = "SETTLED"
        return t.fee - t.burned

    with mock.patch.object(u_en.Chain, "settle", pays_regardless):
        assert probe_u.tv53_slashed_task_pays_miner_nothing() is False


def test_tv54_the_burn_at_submission_is_irrecoverable():
    """HONEST: the burn is collected at SUBMISSION and an abandoned task never
    gets it back -- the documented difference from f3a's refund guarantee.
    FAULT: a submit_task that does not burn leaves the burn address empty, so
    the measured '30 burned, no refund path' no longer holds."""
    assert probe_u.tv54_burn_at_submission_is_irrecoverable() is True
    import inspect
    src = inspect.getsource(u_en.Chain.submit_task)
    src = src.replace("self.burn_address_balance += burn               # <-- burn HEMEN",
                      "pass  # burn disabled by the fault")
    ns = {}
    exec("def submit_task" + src[src.index("("):], dict(u_en.__dict__), ns)
    with mock.patch.object(u_en.Chain, "submit_task", ns["submit_task"]):
        assert probe_u.tv54_burn_at_submission_is_irrecoverable() is False


def test_tv55_a_challenge_past_the_fraud_window_is_refused():
    """HONEST: challenging after W_s raises and is refused. FAULT: widen the
    window without bound and the same challenge is accepted, so the refusal is
    the window and not a swallowed exception."""
    assert probe_u.tv55_challenge_after_window_refused() is True
    with mock.patch.object(u_en, "W_s", 10 ** 9):
        assert probe_u.tv55_challenge_after_window_refused() is False


def test_tv56_the_vrf_public_key_is_not_the_secret():
    """HONEST: the published pk is a digest (not the sk), a second miner's
    proof differs, the honest proof verifies and the OLD raw-name pk form is
    rejected. FAULT: publish the secret as the key, as the pre-fix chain did,
    and the probe goes RED."""
    assert probe_u.tv56_vrf_public_key_is_not_the_secret() is True
    with mock.patch.object(u_en.VRF, "__init__",
                           lambda self, sk: (setattr(self, "sk", sk),
                                             setattr(self, "pk", sk))[1]):
        assert probe_u.tv56_vrf_public_key_is_not_the_secret() is False


def test_tv57_phi_is_rederived_not_trusted():
    """HONEST: a block with a lied phi=0.99 is rejected as phi-mismatch while
    the honest block is accepted. FAULT: a verifier that skips the
    re-derivation accepts the lie, which is the round-3 finding this probe
    pins."""
    assert probe_u.tv57_phi_is_rederived_not_trusted() is True

    def verify_no_phi(self, blk, A, B):
        if not self.kernel.verify(blk["cert"], A, B, blk["ctx"], blk["nonce"], self.D):
            return "REJECT:G-cert"
        return "ACCEPT"

    with mock.patch.object(u_en.Chain, "validate_block", verify_no_phi):
        assert probe_u.tv57_phi_is_rederived_not_trusted() is False


# ============================================================ EN-output audit

def test_tr_hits_detects_unaccented_turkish_and_spares_english():
    """HONEST: clean English prose yields no hits; forbidden Turkish words are
    caught even when written WITHOUT accents (the letter-based auditor missed
    'sansur'/'gorev' five times); accented forms are normalized and caught;
    and the English words that end in a Turkish-looking suffix ('margin',
    'caller', 'produce', 'source', 'sentence', 'tolerance', 'convergence',
    'governance') are NOT hit, because the suffix rule requires a Turkish
    stem. FAULT: empty the word list and the Turkish text sails through --
    the audit's teeth are the list, not the loop."""
    assert audit.tr_hits("The quick brown fox jumps over the lazy dog. "
                         "Protocol security margin verification convergence.") == {}
    hits = audit.tr_hits("sansur gorev maliyet kritik ayni saldiri")
    assert {"sansur", "gorev", "maliyet", "kritik", "ayni", "saldiri"} <= set(hits)
    # NOTE, measured and stated rather than asserted away: the word list holds
    # "HATA" in UPPERCASE while tr_hits lowercases the text before matching, so
    # that one entry can never fire. The other entries are lowercase and do.
    assert audit.tr_hits("hata") == {}
    assert audit.tr_hits("HATA") == {}
    accented = audit.tr_hits("görev sansür kesinti")
    assert set(accented) == {"gorev", "sansur", "kesinti"}
    assert audit.tr_hits("margin caller produce source sentence tolerance "
                         "convergence governance") == {}
    with mock.patch.object(audit, "TR_WORDS", []):
        assert audit.tr_hits("sansur gorev maliyet") == {}
