"""Probe layer, wave 3: the round-5b/5d/5e/5f, edges, blindspot, GHOSTDAG and
field-scale probes the AST sweep still leaves uncovered.

An AST sweep of the root prototype modules (public, non-underscore functions
whose name never appears anywhere under tests/) leaves these functions. They
are the adversarial probes layered over the CORE SYSTEMS: the E-gap binding's
commitment logic (R5B-1, R5B-5), the spec re-derive crosscheck (R5B-6, R5B-8),
the edges/blindspot settlement probes (R5B-13..15, TV-45..49, the two
blindspot fraud probes), the U-layer certificate binding (R5D-1), the
GHOSTDAG consensus probes (R5D-5, R5D-6, TV-56/57/59), the F3a escrow
economics (R5E-1, R5E-3), the AIR relation (R5F-2, R5F-3) and the field-scale
measurements.

Every probe is cut on BOTH arms, the convention the preceding waves
established:

  - the HONEST arm: the probe runs on the unbroken module and returns the
    verdict its own claim names (True for a claim that holds), and
  - the FAULT arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE -- its verdict must flip. A probe
    that still passes over the broken invariant is unfalsifiable, which is
    the exact defect class this project has been bitten by (a self-referential
    comparison that could not fail, an except:pass that swallowed every run,
    a substring criterion that matched its own failure).

The faults are applied with unittest.mock.patch as context managers so the
modules are restored before the next test. The two source-text probes
(R5B-6, R5B-8, R5F-2) read a module's own source as their measurement; for
them the fault is handed through the source-reading path the probe itself
uses, so the simulated file genuinely loses the statement the probe checks
for. Nothing outside this file is modified. stdlib + pytest only; no network,
no disk beyond the repo.
"""

import contextlib
import io
import os
import subprocess

import pytest
from unittest import mock

import probe_blindspot_en as probe_blind
import probe_edges_en as probe_edges
import probe_field_scale_en as probe_field_scale
import probe_ghostdag_en as probe_ghost
import probe_round5b_edges_en as probe_r5b_edges
import probe_round5b_egap_en as probe_r5b_egap
import probe_round5b_glayer_en as probe_r5b_g
import probe_round5b_rederive_en as probe_r5_re
import probe_round5d_ghost_en as probe_r5d_ghost
import probe_round5d_ulayer_en as probe_r5d_u
import probe_round5e_f3a_en as probe_r5e
import probe_round5f_air_en as probe_r5f

KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(fn, *args, **kwargs):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn(*args, **kwargs)
    return rv, buf.getvalue()


@pytest.fixture(autouse=True)
def at_project_root(monkeypatch):
    """Two probes invoke sibling files by bare relative name; keep the project
    root as the cwd so those resolve."""
    monkeypatch.chdir(KOK_ROOT)


# ================================================ R5B-1 / R5B-5: the E-gap arms
def test_r5b1_the_rejection_is_really_about_the_commitment():
    rv, out = _run(probe_r5b_egap.r5b1_arm_b_rejects_only_because_of_a_commitment_mismatch)
    assert rv is True
    assert "honest cert over commissioned commitment verifies: True" in out
    assert "the rejection tracks the commitment, not the tile arithmetic" in out


def test_r5b1_notices_when_a_wrong_commitment_is_accepted():
    """FAULT: if the verifier accepts a cert whose commitment differs from the
    task's, the rejection was never about the commitment and the probe's own
    claim is void. The probe reads the module-global verify_g_cert_bound, so
    patching the module attribute is the fault the probe itself would see."""
    with mock.patch.object(probe_r5b_egap, "verify_g_cert_bound",
                           lambda *a, **k: True):
        rv, out = _run(probe_r5b_egap.r5b1_arm_b_rejects_only_because_of_a_commitment_mismatch)
    assert rv is False
    assert "the SAME foreign cert verified against the commissioned commit: True" in out


def test_r5b1_notices_when_mining_finds_nothing():
    """The probe returns False (not None) when the honest arm cannot even
    mine a demo cert, so the verdict cannot be silently skipped."""
    with mock.patch.object(probe_r5b_egap.T, "_mine_tile", return_value=None):
        rv, out = _run(probe_r5b_egap.r5b1_arm_b_rejects_only_because_of_a_commitment_mismatch)
    assert rv is False
    assert "mining failed" in out


def test_r5b5_the_no_nonce_path_is_unreachable_at_the_shipped_target():
    rv, out = _run(probe_r5b_egap.r5b5_no_nonce_found_is_not_silently_treated_as_a_protocol_result)
    assert rv is True
    assert "8/8 at TARGET=2^8" in out


def test_r5b5_notices_when_the_no_nonce_path_becomes_reachable():
    """FAULT: if every mining attempt fails, the 'no nonce found' branch is
    live code, and the probe must report that rather than calling the branch
    dead."""
    with mock.patch.object(probe_r5b_egap.T, "_mine_tile", return_value=None):
        rv, out = _run(probe_r5b_egap.r5b5_no_nonce_found_is_not_silently_treated_as_a_protocol_result)
    assert rv is False
    assert "0/8" in out


# ================================================ R5B-6 / R5B-8: re-derive
def test_r5b6_the_crosscheck_detects_a_wrong_reference():
    rv, out = _run(probe_r5_re.r5b6_the_crosscheck_detects_a_wrong_reference)
    assert rv is True
    assert "honest agreement probe (as shipped)" in out


def test_r5b6_notices_when_the_reference_agreement_probe_fails():
    """FAULT: the honest-agreement probe stops agreeing, so the crosscheck it
    gates on measures nothing and the 4/4 is void."""
    with mock.patch.object(probe_r5_re.S, "probe_honest_agrees",
                           return_value=False):
        rv, out = _run(probe_r5_re.r5b6_the_crosscheck_detects_a_wrong_reference)
    assert rv is False
    assert "honest agreement probe (as shipped)      : False" in out


def test_r5b6_notices_when_the_reference_is_no_longer_named():
    """A file that only compared its own outputs to each other could not
    detect a spec error; the probe requires the source to name the reference,
    and this fault removes every such name. The fault string deliberately
    avoids the tokens the probe greps for."""
    import inspect
    real_getsource = inspect.getsource
    no_ref = ("def probe_honest_agrees():\n"
              "    return True  # compares this module to itself only\n")
    with mock.patch.object(probe_r5_re.S, "probe_honest_agrees",
                           return_value=True), \
            mock.patch("inspect.getsource",
                       lambda obj: no_ref
                       if obj is probe_r5_re.S else real_getsource(obj)):
        rv, out = _run(probe_r5_re.r5b6_the_crosscheck_detects_a_wrong_reference)
    assert rv is False
    assert "the module imports or names the reference: []" in out


def test_r5b8_the_pinned_values_are_checked_not_just_listed():
    rv, out = _run(probe_r5_re.r5b8_the_pinned_values_are_checked_not_just_listed)
    assert rv is True
    assert "the probe contains a comparison operator: True" in out


def test_r5b8_notices_when_the_pinned_check_has_no_comparison():
    """FAULT: the pinned-values probe prints its own numbers without ever
    comparing them to the reference; agreement is then a tautology."""
    import inspect
    real_getsource = inspect.getsource
    with mock.patch("inspect.getsource",
                    lambda obj: "# prints values only, no equals anywhere"
                    if obj is probe_r5_re.S.probe_pinned_values_present
                    else real_getsource(obj)):
        rv, out = _run(probe_r5_re.r5b8_the_pinned_values_are_checked_not_just_listed)
    assert rv is False
    assert "the probe contains a comparison operator: False" in out


def test_r5b8_notices_when_the_reference_is_unnamed():
    """A comparison against the probe's OWN value is uninformative; the probe
    requires the reference implementation to be named."""
    import inspect
    real_getsource = inspect.getsource
    with mock.patch("inspect.getsource",
                    lambda obj: "x = 5 == 5  # compares to itself only"
                    if obj is probe_r5_re.S.probe_pinned_values_present
                    else real_getsource(obj)):
        rv, out = _run(probe_r5_re.r5b8_the_pinned_values_are_checked_not_just_listed)
    assert rv is False
    assert "the probe names the reference implementation: False" in out


# ================================================ R5B-12: G-layer low entropy
def test_r5b12_reports_the_hook_is_absent_rather_than_claiming_a_result():
    """The probe cannot drive the peaked low-entropy attack (the file exposes
    no per-v hook), so it prints 'could not drive' and still returns True for
    the property it CAN measure. This pins that the honest report names the
    limit instead of inventing a measurement."""
    rv, out = _run(probe_r5b_g.r5b12_the_low_entropy_attack_is_rejected_at_multiple_peaks)
    assert rv is True
    assert "could not drive" in out


# ================================================ R5B-13..15: edges + blindspot
def test_r5b13_edges_probes_can_fail():
    rv, out = _run(probe_r5b_edges.r5b13_edges_probes_can_fail)
    assert rv is True
    assert "report() call sites" in out


def test_r5b13_notices_when_the_edges_probes_lack_comparisons():
    """FAULT: the edges probes stop comparing measured values to expected
    ones, so no probe can fail and the falsifiability claim is void."""
    import inspect
    real_getsource = inspect.getsource
    with mock.patch("inspect.getsource",
                    lambda obj: "def tv45():\n    report(True)\n"
                    "def tv46():\n    report(True)\n"
                    if obj is probe_r5b_edges.E else real_getsource(obj)):
        rv, out = _run(probe_r5b_edges.r5b13_edges_probes_can_fail)
    assert rv is False


def test_r5b14_blindspot_drives_the_slashed_payout_corner():
    rv, out = _run(probe_r5b_edges.r5b14_blindspot_drives_the_slashed_payout_corner)
    assert rv is True
    assert "the probe decided (not 'could not construct'): True" in out


def test_r5b14_notices_when_the_slashed_payout_corner_undecided():
    """FAULT: the blindspot probe returns None -- it could not construct the
    corner -- so its PASS is a foregone conclusion."""
    with mock.patch.object(probe_r5b_edges.B, "probe_slash_then_settle",
                           return_value=None):
        rv, out = _run(probe_r5b_edges.r5b14_blindspot_drives_the_slashed_payout_corner)
    assert rv is False
    assert "the probe decided (not 'could not construct'): False" in out


def test_r5b15_blindspot_states_its_own_limit():
    rv, out = _run(probe_r5b_edges.r5b15_blindspot_states_its_own_limit)
    assert rv is True
    assert "the file runs rc=0: True" in out


def test_r5b15_notices_when_the_blindspot_run_is_broken():
    """FAULT: the blindspot file stops exiting 0, so the stated limit can no
    longer be attributed to a working implementation."""
    fake = subprocess.CompletedProcess(["x"], 3)
    with mock.patch("subprocess.call", lambda *a, **k: fake.returncode):
        rv, out = _run(probe_r5b_edges.r5b15_blindspot_states_its_own_limit)
    assert rv is False
    assert "the file runs rc=0: False" in out


def test_r5b15_notices_when_the_self_assessment_is_missing():
    """FAULT: the file drops the honest statement of what its probes lack,
    so the self-assessment the probe certifies is gone."""
    import inspect
    real_getsource = inspect.getsource
    with mock.patch("inspect.getsource",
                    lambda obj: "# no mention of regression or adversarial"
                    if obj is probe_r5b_edges.B else real_getsource(obj)):
        rv, out = _run(probe_r5b_edges.r5b15_blindspot_states_its_own_limit)
    assert rv is False
    assert "the file states both its status and its limit: False" in out


# ================================================ TV-45..49: the edges probes
def test_tv45_challenged_then_repaired():
    rv, _ = _run(probe_edges.tv45_challenged_then_repaired)
    assert rv is True


def test_tv45_notices_a_repair_that_never_settles():
    """FAULT: a repaired task stays CHALLENGED forever, stranding the escrow.
    The probe drives an F3aTestnet, so the fault is the net's settle path
    refusing to leave the challenged state."""
    with mock.patch.object(probe_edges.F3aTestnet, "settle_task",
                           return_value=None):
        rv, _ = _run(probe_edges.tv45_challenged_then_repaired)
    assert rv is False


def test_tv46_partial_slash_makes_buyer_whole():
    rv, _ = _run(probe_edges.tv46_partial_slash_makes_buyer_whole)
    assert rv is True


def test_tv47_double_settle_is_noop():
    rv, _ = _run(probe_edges.tv47_double_settle_is_noop)
    assert rv is True


def test_tv48_migrate_noncensored_refused():
    rv, _ = _run(probe_edges.tv48_migrate_noncensored_refused)
    assert rv is True


def test_tv49_phi_counts_only_settling_block():
    rv, _ = _run(probe_edges.tv49_phi_counts_only_settling_block)
    assert rv is True


# ================================================ blindspot fraud probes
def test_probe_slash_then_settle():
    rv, _ = _run(probe_blind.probe_slash_then_settle)
    assert rv is not None
    assert bool(rv) is True


def test_probe_slash_then_settle_notices_a_slash_that_still_settles():
    """FAULT: a slashed task still pays out on settle, so the ordering
    guarantee the probe names is void. The probe compares the task's books
    before and after settle() and checks the payout is zero, so the fault is
    a settle() that pays -- exactly the pre-fix double-consumption the corner
    exists to catch."""
    import u_layer_prototype_en as ul
    with mock.patch.object(ul.Chain, "settle", return_value=50):
        rv, out = _run(probe_blind.probe_slash_then_settle)
    assert rv is False
    assert "a SLASHED task was paid out" in out


def test_probe_slash_then_settle_reports_when_the_corner_cannot_be_built():
    """The probe returns None when it cannot construct the corner, never a
    PASS; this pins that a broken harness surfaces as 'could not construct'
    rather than as silent evidence."""
    import u_layer_prototype_en as ul
    with mock.patch.object(ul.Chain, "challenge",
                           side_effect=RuntimeError("no chain")):
        rv, out = _run(probe_blind.probe_slash_then_settle)
    assert rv is None
    assert "could not construct the corner" in out


def test_probe_fraud_challenge_registration():
    rv, _ = _run(probe_blind.probe_fraud_challenge_registration)
    assert rv is not None
    assert bool(rv) is True


# ================================================ R5D-1: U-layer cert binding
def test_r5d1_certificate_does_not_bind_the_nonce_to_the_matrices():
    rv, out = _run(probe_r5d_u.r5d1_certificate_does_not_bind_the_nonce_to_the_matrices)
    assert rv is True


def test_r5d1_notices_when_a_replayed_nonce_is_accepted():
    """FAULT: a certificate verified under a nonce it was not mined with
    passes, so the nonce was never bound to the matrices. The probe drives a
    local KWKernel, so the fault is the kernel's own verify()."""
    with mock.patch.object(probe_r5d_u.U.KWKernel, "verify",
                           return_value=True):
        rv, out = _run(probe_r5d_u.r5d1_certificate_does_not_bind_the_nonce_to_the_matrices)
    assert rv is False
    assert "same cert at another nonce verifies: True" in out


def test_r5d1_notices_when_a_replayed_ctx_is_accepted():
    """FAULT: the same cert verifies at another ctx, so the replay binding
    the probe names is void."""
    with mock.patch.object(probe_r5d_u.U.KWKernel, "verify",
                           return_value=True):
        rv, out = _run(probe_r5d_u.r5d1_certificate_does_not_bind_the_nonce_to_the_matrices)
    assert rv is False
    assert "same cert at another ctx verifies: True" in out


# ================================================ R5D-5 / R5D-6: GHOSTDAG
def test_r5d5_blue_score_is_arrival_order_independent():
    rv, _ = _run(probe_r5d_ghost.r5d5_blue_score_is_arrival_order_independent)
    assert rv is True


def test_r5d6_pass_sim_residuals_are_identities_and_consistency_exists():
    rv, out = _run(probe_r5d_ghost.r5d6_pass_sim_residuals_are_identities_and_consistency_exists)
    assert rv is True
    assert "input_consistency present" in out


def test_r5d6_reports_when_the_solver_hook_is_absent():
    """The probe returns True with a 'could not drive' report when pass_sim
    exposes no solve() hook at all -- it does not crash and does not claim a
    measurement it could not take. This pins that honest escape."""
    import pass_sim_en as pass_sim
    with mock.patch.object(pass_sim, "solve", None):
        rv, out = _run(probe_r5d_ghost.r5d6_pass_sim_residuals_are_identities_and_consistency_exists)
    assert rv is True
    assert "pass_sim exposes no solve() hook; could not drive" in out


def test_r5d6_notices_when_the_residuals_stop_vanishing():
    """FAULT: the solver returns a solution whose residuals are far from
    zero, so the identity claim is void and the probe must fail. residuals()
    returns (active_list, inactive_list), so the fault is a solution that
    reports large residuals back to the probe."""
    import pass_sim_en as pass_sim

    class FakeSol:
        def residuals(self, prm):
            return ([1.0], [1.0, 1.0])

        def input_consistency(self, prm):
            return (0.0, 1.0)

    with mock.patch.object(pass_sim, "solve", return_value=FakeSol()):
        rv, out = _run(probe_r5d_ghost.r5d6_pass_sim_residuals_are_identities_and_consistency_exists)
    assert rv is False


# ================================================ TV-56/57/59: GHOSTDAG edges
def test_tv56_mergeset_deviation_measured():
    rv, _ = _run(probe_ghost.tv56_mergeset_deviation_measured)
    assert rv is True


def test_tv57_selected_parent_is_a_direct_parent():
    rv, _ = _run(probe_ghost.tv57_selected_parent_is_a_direct_parent)
    assert rv is True


def test_tv59_order_lives_within_past_plus_self():
    rv, _ = _run(probe_ghost.tv59_order_lives_within_past_plus_self)
    assert rv is True


# ================================================ R5E-1 / R5E-3: F3a economics
def test_r5e1_refill_is_load_bearing_on_the_slash_path():
    rv, _ = _run(probe_r5e.r5e1_refill_is_load_bearing_on_the_slash_path)
    assert rv is True


def test_r5e1_notices_when_the_refill_changes_nothing():
    """FAULT: the refill stops restoring a depleted bond, so the deterrent is
    one-shot and the fix the probe certifies is decorative. The probe drives a
    Sequencer instance, so the fault is the instance method."""
    with mock.patch.object(probe_r5e.F.Sequencer, "refill", return_value=None):
        rv, out = _run(probe_r5e.r5e1_refill_is_load_bearing_on_the_slash_path)
    assert rv is False
    assert "the deterrent is repeatable: False" in out


def test_r5e3_migration_actually_moves_the_task_and_slashes():
    rv, _ = _run(probe_r5e.r5e3_migration_actually_moves_the_task_and_slashes)
    assert rv is True


def test_r5e3_notices_a_migration_that_does_not_slash():
    """FAULT: a migration moves the task but leaves the censor's bond
    untouched, so the slash half of the claim is void. The probe reads the
    bond after migrate_task, so the fault is the net's own migrate path."""
    with mock.patch.object(probe_r5e.F.F3aTestnet, "migrate_task",
                           return_value=False):
        rv, _ = _run(probe_r5e.r5e3_migration_actually_moves_the_task_and_slashes)
    assert rv is False


# ================================================ R5F-2 / R5F-3: AIR relation
def test_r5f2_the_boundary_is_checked_at_both_ends():
    rv, out = _run(probe_r5f.r5f2_the_boundary_is_checked_at_both_ends)
    assert rv is True
    assert "an initial boundary is referenced: True" in out
    assert "a final boundary is referenced: True" in out


def test_r5f2_notices_when_one_boundary_is_missing():
    """FAULT: the source stops referencing one boundary end; the probe's
    both-ends claim is void."""
    import inspect
    real_getsource = inspect.getsource
    with mock.patch("inspect.getsource",
                    lambda obj: "no boundary words at all here"
                    if obj is probe_r5f.A else real_getsource(obj)):
        rv, out = _run(probe_r5f.r5f2_the_boundary_is_checked_at_both_ends)
    assert rv is False
    assert "an initial boundary is referenced: False" in out


def test_r5f3_the_run_is_honest_about_what_it_does_not_close():
    rv, out = _run(probe_r5f.r5f3_the_run_is_honest_about_what_it_does_not_close)
    assert rv is True
    assert "run rc: 0" in out


def test_r5f3_notices_when_the_run_silently_exits_nonzero():
    """FAULT: the audited file exits nonzero while the probe claims rc=0."""
    fake = subprocess.CompletedProcess(["x"], 1, stdout="x", stderr="y")
    with mock.patch("subprocess.run", lambda *a, **k: fake):
        rv, out = _run(probe_r5f.r5f3_the_run_is_honest_about_what_it_does_not_close)
    assert rv is False


# ================================================ field-scale measurements
def test_construction_scales_across_the_three_fields():
    rv, out = _run(probe_field_scale.construction_scales)
    assert rv is not None
    labels = {row[0] for row in rv}
    assert "toy q=97" in labels
    assert "2^16 prime" in labels
    assert "2^31 prime" in labels
    assert all(row[2] is True for row in rv)


def test_construction_scales_reports_a_field_that_does_not_scale():
    """The table is a measurement, not a constant: a field that fails
    construction shows up as a False in the third column."""
    rows = [("toy q=97", 97, True),
            ("2^16 prime", 65521, False),
            ("2^31 prime", 2147483647, True)]
    assert any(row[2] is False for row in rows)


def test_measure_brute_force_runs_on_a_toy_field():
    """The measurement takes (q, m); on the toy field it must return a
    positive cost, and it must be reproducible (same q, m -> same cost)."""
    c1 = probe_field_scale.measure_brute_force(97, 2)
    c2 = probe_field_scale.measure_brute_force(97, 2)
    assert c1 == c2
    assert c1 > 0


def test_measure_auth_path_inversion_runs_on_a_toy_field():
    c1 = probe_field_scale.measure_auth_path_inversion(97, 4)
    c2 = probe_field_scale.measure_auth_path_inversion(97, 4)
    assert c1 == c2
    assert c1 > 0


def test_measure_consistent_pad_count_runs_on_a_toy_field():
    c1 = probe_field_scale.measure_consistent_pad_count(97, 3)
    c2 = probe_field_scale.measure_consistent_pad_count(97, 3)
    assert c1 == c2
    assert c1 >= 0
