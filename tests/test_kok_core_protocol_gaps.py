"""The last untested core-protocol functions, branch-cut on both arms.

An AST sweep of the root prototype modules (public functions whose name never
appears under tests/) left the functions below. They are not probe-layer
plumbing; they are the five areas the network is built from:

  G-layer PoW leader selection   g_layer_tests{,_en}.py
      tv1 (replay rejection), tv2 (prescribed hardness), tv3 (no easy
      instance), tv4 (phi), v1_contrast (the v1 adversary advantage the
      KW kernel removes), the JackpotToy admission controls (Pearl 5.1.1-.4:
      entry liveness, noise floor, tamed products, unpredictable summands)
      and rt_tests (difficulty retarget: convergence, the 4x clip, the
      median filter)
  U-layer utility                u_layer_prototype{,_en}.py
      tv8 (zero-demand liveness) and tv123_stub (replay rejection)
  consensus                      ghostdag_proto{,_en}.py
      tv22..tv26 (blue rule, selected parent, mergeset limit, ctx binding,
      splitter liveness)
  sequencer                      f3a_sequencer_proto{,_en}.py
      tv15..tv19 (refund guarantee, migration, dilemma, honest loop),
      tv21..tv23 (the demand meter, the end-to-end paying task, realistic
      demand) and task_harness_id
  zk                             f0b_air_proto.py
      already fully covered by tests/test_kok_proof_stack.py — nothing left

Every function is cut on BOTH arms, the honest arm (it runs on the current
module and its verdict is what its claim says) and the fault arm (the
invariant the function guards is broken by a scoped monkeypatch and the
function must NOTICE — proving the verdict is falsifiable rather than a
tautology of its own construction). The fault is always the failure the
function's own claim names:

  TV-1/TV-123  verify() stops rejecting a replayed certificate
  TV-2         cost_of_prove gains an input-content shortcut
  TV-3         a permutation matrix becomes cheaper than a dense one
  TV-4         the miner reports phi = 0 for a block carrying a paid task
  V1X          the KW kernel's cost collapses below the v1 shortcuts
  TV-11..14    the attack vector loses the structure the control detects
  RT-2         retarget() drops the 4x clip
  TV-8         validate_block() stops accepting any block
  TV-22        the blue/red coloring ignores the anticone
  TV-23        the selected parent stops being the max blue score
  TV-24        the mergeset admits the whole past, ignoring the 2k cap
  TV-25        kok_ctx() stops binding the parent-set hash
  TV-26        order() stops walking the DAG
  TV-15        next_block() stops refunding censored tasks
  TV-16        refill() stops topping the bond up after a slash
  TV-18        settle_task() settles without verification
  TV-19        settle_task() stops burning
  TV-21/22     the meter stops counting only settled tasks

Faults are applied with unittest.mock.patch.object as context managers, so
each module is restored before the next test. Where the EN and TR prototypes
carry the same interface the test is parametrized over both, and each arm is
asserted against ITS OWN module's documented outcome (the two F3a prototypes
genuinely disagree on the refund amount: the EN one refunds the full fee,
the TR one the escrow alone — each function's own assertions are what is
tested). Nothing outside this file is modified. stdlib only.
"""

import math
import random

import pytest
from unittest import mock

import f3a_sequencer_proto as f3_tr
import f3a_sequencer_proto_en as f3_en
import g_layer_tests as g_tr
import g_layer_tests_en as g_en
import ghostdag_proto as gd_tr
import ghostdag_proto_en as gd_en
import u_layer_prototype as u_tr
import u_layer_prototype_en as u_en

G_MODULES = [pytest.param(g_en, id="en"), pytest.param(g_tr, id="tr")]
U_MODULES = [pytest.param(u_en, id="en"), pytest.param(u_tr, id="tr")]
GD_MODULES = [pytest.param(gd_en, id="en"), pytest.param(gd_tr, id="tr")]
F3_MODULES = [pytest.param(f3_en, id="en"), pytest.param(f3_tr, id="tr")]


# ---------------------------------------------------------------------------
# G-LAYER — the PoW leader-selection certificate
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv1_replay_rejection_honest_arm(mod):
    status, note = mod.tv1()
    assert status == "PASS"


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv1_fails_when_verify_accepts_a_replay(mod):
    """The fault: verify() stops rejecting anything, so a certificate
    replayed under another parent is accepted and TV-1's own assert fires."""
    with mock.patch.object(mod.KWKernel, "verify",
                           new=lambda self, *a, **k: True):
        with pytest.raises(AssertionError):
            mod.tv1()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv2_prescribed_hardness_honest_arm(mod):
    costs, devs, stats, spread = mod.tv2()
    # per-attempt cost is identical across every input class
    assert max(abs(d) for d in devs.values()) < 1e-9
    # and the attempts-until-success distribution is the same population
    assert spread < 15.0
    assert set(costs) == {"dense-random", "sparse-zero-rows", "permutation",
                          "all-zeros", "identity"}


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv2_fails_when_the_kernel_has_an_input_shortcut(mod):
    """The fault: cost_of_prove gains a v1-style shortcut on the all-zeros
    input, so prescribed hardness is no longer prescribed and TV-2 fires."""
    orig = mod.cost_of_prove

    def _shortcut_cost(A, B, ctx, D):
        base = orig(A, B, ctx, D)
        if all(all(x == 0 for x in row) for row in A):
            return base // 2          # the A=0 shortcut: half the work
        return base

    with mock.patch.object(mod, "cost_of_prove", new=_shortcut_cost):
        with pytest.raises(AssertionError):
            mod.tv2()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv3_no_easy_instance_honest_arm(mod):
    m_perm, m_dense, dev = mod.tv3()
    assert m_perm > 0 and m_dense > 0
    assert dev < 15.0


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv3_fails_when_a_permutation_matrix_is_cheaper(mod):
    """The fault: attempts_to_success reports a permutation matrix as
    near-free (the O(n) v1 shortcut), so the easy-instance claim fires."""
    orig = mod.attempts_to_success

    def _cheap_perm(A, B, ctx, D, trials=200):
        counts = orig(A, B, ctx, D, trials)
        is_perm = (len(A) == len(A[0])
                   and all(sum(row) == 1 for row in A)
                   and all(x in (0, 1) for row in A for x in row))
        if is_perm:
            return [1] * trials        # a permutation is O(n) in v1
        return counts

    with mock.patch.object(mod, "attempts_to_success", new=_cheap_perm):
        with pytest.raises(AssertionError):
            mod.tv3()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv4_phi_is_zero_without_a_u_task_honest_arm(mod):
    phi_empty, phi_task = mod.tv4()
    assert phi_empty == 0.0
    assert phi_task > 0.0


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv4_fails_when_the_miner_reports_no_utility(mod):
    """The fault: the miner always reports phi = 0, so a block that carries a
    paid task is indistinguishable from an empty one and TV-4 fires."""
    orig = mod.Chain.mine_block

    def _zero_phi(self, *a, **k):
        blk = orig(self, *a, **k)
        blk["phi"] = 0.0               # the utility density is hidden
        return blk

    with mock.patch.object(mod.Chain, "mine_block", new=_zero_phi):
        with pytest.raises(AssertionError):
            mod.tv4()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_v1_contrast_honest_arm(mod):
    v = mod.v1_contrast()
    # v1 gives the adversary a real advantage on every structured input
    assert v["v1_attack_sparse_advantage"] > 1.0
    assert v["v1_attack_perm_advantage"] > 1.0
    assert v["v1_attack_zero_advantage"] > 1.0
    # the KW kernel costs the same on any input, and more than every shortcut
    kw = mod.cost_of_prove(mod.dense(8), mod.dense(8, seed=2), 0, 1 << 6)
    assert v["kw_cost_any_input"] == kw
    assert kw > (8 // 2) * 8 * 8      # the sparse shortcut
    assert kw > 8 * 8                 # the permutation shortcut
    assert kw > 8                     # the zero shortcut


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_v1_contrast_fails_when_the_kw_cost_collapses(mod):
    """The fault: the kernel's cost collapses to nothing, so it no longer
    dominates the v1 shortcuts the contrast exists to measure."""
    with mock.patch.object(mod, "cost_of_prove", new=lambda A, B, ctx, D: 1):
        v = mod.v1_contrast()
    assert v["kw_cost_any_input"] == 1
    assert v["kw_cost_any_input"] <= 8 * 8


# ---------------------------------------------------------------------------
# G-LAYER — the Pearl jackpot admission controls (the input policy)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod", G_MODULES)
def test_g_jackpot_controls_reject_the_attack_vectors(mod):
    J = mod.JackpotToy
    r = random.Random(7)

    good_a = mod._uniform_rows(r)
    good_b = mod._uniform_rows(r)
    peaked2 = mod.peaked_rows(r, m=2, v=40.0)
    peaked1 = mod.peaked_rows(r, m=1, v=40.0)
    common = mod.common_peaked_rows(r, v=64.0)
    ident = mod.identical_rows(r)

    # noise_std_row is proportional to the row RMS, and zero on a zero row
    assert J.noise_std_row([0.0] * J.K) == 0.0
    assert J.noise_std_row([3.0] * J.K) == pytest.approx(J.DELTA * 3.0)

    # 5.1.1 entry liveness: two peaks per row are idle, one is a loose net
    _, ok_bad = J.entry_liveness(peaked2)
    _, ok_good = J.entry_liveness(good_a)
    _, ok_one = J.entry_liveness(peaked1)
    assert not ok_bad and ok_good and ok_one

    # 5.1.2 noise floor: a single peaked row pins the grid, healthy rows do not
    _, ok_bad = J.noise_floor(peaked1)
    _, ok_good = J.noise_floor(good_a)
    assert not ok_bad and ok_good

    # 5.1.3 tamed products: identical (rank-1) rows are coherent, random are not
    _, ok_bad = J.tamed_products(ident, ident)
    _, ok_good = J.tamed_products(good_a, good_b)
    assert not ok_bad and ok_good

    # 5.1.4 unpredictable summands: a common peak truncates the rest
    A, B = common
    _, ok_bad = J.unpredictable_summands(A, B)
    _, ok_good = J.unpredictable_summands(good_a, good_b)
    assert not ok_bad and ok_good

    # the aggregate verdict admits healthy work and rejects the attack
    assert J.verdict(good_a, good_b)["ok"] is True
    assert J.verdict(peaked1, peaked1)["ok"] is False


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_jackpot_product_with_magnitude_matches_the_product(mod):
    """C = A B^T and M_ij bounds both the cell and its largest summand."""
    J = mod.JackpotToy
    r = random.Random(13)
    A = mod._uniform_rows(r, n=12, k=24, c=5)
    B = mod._uniform_rows(r, n=12, k=24, c=5)
    C, M = J.product_with_magnitude(A, B)
    n, m, k = len(A), len(B), len(A[0])
    for i in range(n):
        for j in range(m):
            dot = sum(A[i][u] * B[j][u] for u in range(k))
            assert C[i][j] == pytest.approx(dot)
            biggest = max(abs(A[i][u] * B[j][u]) for u in range(k))
            assert M[i][j] >= biggest - 1e-12
            assert M[i][j] >= abs(C[i][j]) - 1e-12


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_jackpot_fails_when_the_noise_model_is_inflated(mod):
    """The fault: the noise model returns a huge value, so the liveness and
    floor controls find every entry idle and the policy becomes vacuous."""
    with mock.patch.object(mod.JackpotToy, "noise_std_row",
                           new=lambda row: 1e6):
        with pytest.raises(AssertionError):
            mod.tv11()
        with pytest.raises(AssertionError):
            mod.tv12()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv11_fails_when_the_peaked_vector_keeps_one_peak(mod):
    """The fault: the attack vector carries a single peak, which the idle
    check is deliberately a loose net for — so TV-11 stops flagging it."""
    orig = mod.peaked_rows

    def _one_peak(r, m=2, v=40.0, n=None, k=None, c=3):
        return orig(r, m=1, v=v,
                    n=n if n is not None else mod.JackpotToy.N,
                    k=k if k is not None else mod.JackpotToy.K, c=c)

    with mock.patch.object(mod, "peaked_rows", new=_one_peak):
        with pytest.raises(AssertionError):
            mod.tv11()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv12_fails_when_the_rows_carry_no_peak(mod):
    """The fault: the "peaked" input is just the healthy background, so the
    noise floor has nothing to pin and TV-12 stops flagging it."""
    with mock.patch.object(mod, "peaked_rows",
                           new=lambda r, m=2, v=40.0, n=None, k=None, c=3:
                           mod._uniform_rows(
                               r, n=n or mod.JackpotToy.N,
                               k=k or mod.JackpotToy.K, c=c)):
        with pytest.raises(AssertionError):
            mod.tv12()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv13_fails_when_the_rows_are_not_identical(mod):
    """The fault: the "identical" rows are independent, so no cell is coherent
    and the tamed-products check accepts them."""
    with mock.patch.object(mod, "identical_rows",
                           new=lambda r, n=None, k=None, c=3:
                           mod._uniform_rows(
                               r, n=n or mod.JackpotToy.N,
                               k=k or mod.JackpotToy.K, c=c)):
        with pytest.raises(AssertionError):
            mod.tv13()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_tv14_fails_when_the_peak_is_not_common(mod):
    """The fault: A and B are independent backgrounds with no shared peak, so
    no cell is dominated by one summand and the check accepts them."""
    with mock.patch.object(mod, "common_peaked_rows",
                           new=lambda r, v=64.0, n=None, k=None, c=3: (
                               mod._uniform_rows(r, n=n or mod.JackpotToy.N,
                                                 k=k or mod.JackpotToy.K, c=c),
                               mod._uniform_rows(r, n=n or mod.JackpotToy.N,
                                                 k=k or mod.JackpotToy.K, c=c))):
        with pytest.raises(AssertionError):
            mod.tv14()


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_the_attack_generators_shape_their_vectors(mod):
    r = random.Random(11)

    # peaked_rows: exactly m entries per row exceed the background
    P = mod.peaked_rows(r, m=3, v=50.0, n=16, k=32, c=2)
    assert len(P) == 16
    for row in P:
        assert len(row) == 32
        assert len([x for x in row if abs(x) >= 50.0]) == 3
        assert all(abs(x) <= 2 for x in row if abs(x) < 50.0)

    # common_peaked_rows: A and B both peak at the SAME position
    A, B = mod.common_peaked_rows(r, v=64.0, n=16, k=32)
    p = 32 // 2
    for row in A + B:
        assert row[p] == 64.0
        assert all(abs(x) <= 3 for x in row if x != 64.0)

    # identical_rows: every row is a copy of the first
    ident = mod.identical_rows(r, n=16, k=32)
    assert all(row == ident[0] for row in ident)

    # the uniform background stays inside [-c, c]
    back = mod._uniform_rows(r, n=16, k=32, c=2)
    assert all(-2 <= x <= 2 for row in back for x in row)


# ---------------------------------------------------------------------------
# G-LAYER — difficulty retarget (RT-1..RT-3)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod", G_MODULES)
def test_g_rt_tests_honest_arm(mod):
    r = mod.rt_tests()
    # RT-1: constant hashrate -> D converges onto Lambda * T_b
    assert 0.7 < r["RT1_converged_D"] / r["RT1_expected"] < 1.4
    # RT-2: a 10x hashrate jump lifts D by at most 4x per window
    assert r["RT2_max_window_ratio"] <= 4.0 + 1e-9
    assert r["RT2_D_after_10x"] > r["RT1_converged_D"]
    # RT-3: noisy hashrate -> the median filter keeps D inside the band
    assert r["RT3_bound_low"] <= r["RT3_noisy_D_final"] <= r["RT3_bound_high"]


@pytest.mark.parametrize("mod", G_MODULES)
def test_g_rt_fails_when_the_clip_is_removed(mod):
    """The fault: retarget() drops the 4x clip, so a sudden hashrate jump
    lifts D without bound and RT-2's bound is violated."""
    def _uncapped_ret(self):
        W = self.retarget_window
        t_b = self.target_block_time
        n = len(self.times) - 1
        if n == 0 or n % W != 0:
            return None
        T_act = self.times[-1] - self.times[-1 - W]
        lam_hat = self.D * W / T_act
        self.window_history.append((T_act, self.D, lam_hat))
        est = sorted(h[2] for h in self.window_history[-3:])
        lam_smooth = est[len(est) // 2]
        D_old = self.D
        self.D = max(1, int(lam_smooth * t_b))       # NO 4x clip
        return {"T_act": T_act, "lam_hat": lam_hat, "lam_smooth": lam_smooth,
                "ratio": self.D / D_old, "D": self.D}

    with mock.patch.object(mod.Chain, "retarget", new=_uncapped_ret):
        r = mod.rt_tests()
    assert r["RT2_max_window_ratio"] > 4.0


# ---------------------------------------------------------------------------
# U-LAYER — zero-demand liveness and replay rejection
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod", U_MODULES)
def test_u_tv8_zero_demand_liveness_honest_arm(mod):
    assert mod.tv8() == 1000


@pytest.mark.parametrize("mod", U_MODULES)
def test_u_tv8_fails_when_blocks_are_not_validated(mod):
    """The fault: validate_block() rejects everything, so the liveness claim
    is no longer measured and TV-8's own count collapses."""
    with mock.patch.object(mod.Chain, "validate_block",
                           new=lambda self, blk, A, B: "REJECT:fault"):
        with pytest.raises(AssertionError):
            mod.tv8()


@pytest.mark.parametrize("mod", U_MODULES)
def test_u_tv123_stub_replay_rejection_honest_arm(mod):
    assert "PASS" in mod.tv123_stub()


@pytest.mark.parametrize("mod", U_MODULES)
def test_u_tv123_fails_when_verify_accepts_a_replay(mod):
    """The fault: verify() stops rejecting a certificate replayed under
    another parent, and the stub's own replay assertion fires."""
    with mock.patch.object(mod.KWKernel, "verify",
                           new=lambda self, *a, **k: True):
        with pytest.raises(AssertionError):
            mod.tv123_stub()


# ---------------------------------------------------------------------------
# CONSENSUS — GHOSTDAG parent-set selection
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv22_blue_rule_honest_arm(mod):
    status, note = mod.tv22_blue_rule()
    assert status == "PASS"


@pytest.mark.parametrize("mod", [gd_en])
def test_gd_tv22_fails_when_the_color_ignores_the_anticone(mod):
    """The fault: every mergeset member is painted blue regardless of its
    anticone, which is the historical bug the EN file documents — TV-22 then
    flags blocks the rule is supposed to exclude.

    EN-only: the EN prototype colors members from the topology, so forcing
    them all blue decouples the color from the check. The TR prototype still
    carries the historical coloring (every block is blue at its own
    insertion and the member loop skips it), so the forcing fault is a
    no-op there; its decoupling fault is the k bound (test below)."""
    orig = mod.GHOSTDAG._compute

    def _all_blue(self, bid):
        orig(self, bid)
        for b in self.mergesets.get(bid, set()):
            self.is_blue[b] = True

    with mock.patch.object(mod.GHOSTDAG, "_compute", new=_all_blue):
        with pytest.raises(AssertionError):
            mod.tv22_blue_rule()


@pytest.mark.parametrize("mod", [gd_tr])
def test_gd_tv22_tr_fails_when_the_bound_is_ignored(mod):
    """The TR prototype's coloring is the historical one the EN file
    documents as fixed: every block is blue at its own insertion and the
    member coloring loop skips it, so the color does not depend on k at all
    while TV-22's check does. Tightening k below the actual mergeset
    anticones therefore decouples the check from the (already degenerate)
    color and TV-22 fires."""
    with mock.patch.object(mod, "GHOSTDAG_K", new=1):
        with pytest.raises(AssertionError):
            mod.tv22_blue_rule()


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv23_selected_parent_is_the_max_score_honest_arm(mod):
    status, note = mod.tv23_selected_parent_max_score()
    assert status == "PASS"


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv23_fails_when_the_parent_is_not_the_max(mod):
    """The fault: the selected parent is the lowest-hash parent rather than
    the highest blue score, so TV-23's comparison finds the mismatch."""
    orig = mod.GHOSTDAG._compute

    def _wrong_sp(self, bid):
        orig(self, bid)
        scored = [p for p in self.blocks[bid].parents if p in self.blocks]
        if scored:
            self.selected[bid] = min(scored, key=lambda x: int(x, 16))

    with mock.patch.object(mod.GHOSTDAG, "_compute", new=_wrong_sp):
        with pytest.raises(AssertionError):
            mod.tv23_selected_parent_max_score()


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv24_mergeset_limit_honest_arm(mod):
    status, note = mod.tv24_mergeset_limit()
    assert status == "PASS"


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv24_fails_when_the_mergeset_is_uncapped(mod):
    """The fault: the mergeset admits the whole past instead of stopping at
    2k, so blocks exceed the limit and TV-24 fires."""
    orig = mod.GHOSTDAG._compute

    def _uncapped(self, bid):
        orig(self, bid)
        sp = self.selected.get(bid)
        if sp is None:
            return
        self.mergesets[bid] = (self.mergesets[bid]
                               | (self._past(bid) - {sp}))

    with mock.patch.object(mod.GHOSTDAG, "_compute", new=_uncapped):
        with pytest.raises(AssertionError):
            mod.tv24_mergeset_limit()


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv25_ctx_binds_the_parent_set_honest_arm(mod):
    status, note = mod.tv25_ctx_rejects_changed_parentset()
    assert status == "PASS"


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv25_fails_when_ctx_ignores_the_parent_set(mod):
    """The fault: kok_ctx() drops the parent-set hash, so the same work under
    two parent-sets yields one ctx and the T-A2 binding is open."""
    with mock.patch.object(mod, "kok_ctx",
                           new=lambda sp, miner, task_ref, height, psid,
                               nonce, psh: mod.h(sp, miner, task_ref, height,
                                                 psid, nonce)):
        with pytest.raises(AssertionError):
            mod.tv25_ctx_rejects_changed_parentset()


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv26_splitter_liveness_honest_arm(mod):
    status, note = mod.tv26_splitter_attack()
    assert status == "PASS"


@pytest.mark.parametrize("mod", GD_MODULES)
def test_gd_tv26_fails_when_the_order_ignores_the_dag(mod):
    """The fault: order() returns the block alone, so recent blocks no longer
    reach back into the DAG and the liveness bound collapses."""
    with mock.patch.object(mod.GHOSTDAG, "order", new=lambda self, bid: [bid]):
        with pytest.raises(AssertionError):
            mod.tv26_splitter_attack()


# ---------------------------------------------------------------------------
# SEQUENCER — F3a censorship resistance and the demand meter
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv15_refund_guarantee_honest_arm(mod):
    assert mod.tv15() is True


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv15_fails_when_the_refund_never_fires(mod):
    """The fault: next_block() stops refunding censored tasks, so the
    guarantee it exists to provide is gone and TV-15 fires."""
    def _no_refund(self):
        self.height += 1
        return self.height

    with mock.patch.object(mod.F3aTestnet, "next_block", new=_no_refund):
        with pytest.raises(AssertionError):
            mod.tv15()


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv16_migration_slashes_and_refills_honest_arm(mod):
    assert mod.tv16() is True


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv16_fails_when_the_bond_is_not_refilled(mod):
    """The fault: refill() does nothing, so one slash empties the bond and
    every later censorship is free — the one-shot deterrent TV-16 rules out."""
    with mock.patch.object(mod.Sequencer, "refill",
                           new=lambda self, fee, floor=None: None):
        with pytest.raises(AssertionError):
            mod.tv16()


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv18_no_verifier_dilemma_honest_arm(mod):
    assert mod.tv18() is True


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv18_fails_when_verification_is_skipped(mod):
    """The fault: settle_task() settles without verifying, so a failed
    verification no longer produces CHALLENGED and the dilemma is untracked."""
    def _settle_unverified(self, sid, tid, verify_ok=True):
        t = self.sequencers[sid].tasks.get(tid)
        if t is None:
            return False
        t.state = "SETTLED"
        return True

    with mock.patch.object(mod.F3aTestnet, "settle_task",
                           new=_settle_unverified):
        with pytest.raises(AssertionError):
            mod.tv18()


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv19_honest_loop_honest_arm(mod):
    assert mod.tv19() is True


@pytest.mark.parametrize("mod", F3_MODULES)
def test_f3_tv19_fails_when_the_burn_never_happens(mod):
    """The fault: settle_task() settles but never moves the burn, so the
    irrecoverable burn TV-19 measures is gone."""
    def _settle_no_burn(self, sid, tid, verify_ok=True):
        t = self.sequencers[sid].tasks.get(tid)
        if t is None or t.state not in ("SOLVED", "CHALLENGED"):
            return False
        if not verify_ok:
            t.state = "CHALLENGED"
            return False
        t.state = "SETTLED"
        t.escrow = 0
        t.burned = 0
        return True

    with mock.patch.object(mod.F3aTestnet, "settle_task", new=_settle_no_burn):
        with pytest.raises(AssertionError):
            mod.tv19()


def test_f3_en_tv21_demand_meter_reads_both_ways():
    zero_is_zero, named_zero, one_is_positive, count_exact = \
        f3_en.tv21_demand_meter()
    assert zero_is_zero and named_zero and one_is_positive and count_exact


def test_f3_en_tv21_fails_when_the_meter_counts_everything():
    """The fault: record_block() marks every block as carrying a paid task,
    so the demandless world reports phi = 1 and the meter cannot show its
    own zero."""
    orig = f3_en.DemandMeter.record_block

    def _inflated(self, testnet):
        orig(self, testnet)
        self.blocks_with_paid_task += 1

    with mock.patch.object(f3_en.DemandMeter, "record_block", new=_inflated):
        zero_is_zero, _named, _one, _cnt = f3_en.tv21_demand_meter()
    assert zero_is_zero is False


def test_f3_en_tv22_end_to_end_paying_task_honest_arm():
    escrow_funded, solved, settled, burn_gone, counted = \
        f3_en.tv22_end_to_end_paying_task()
    assert escrow_funded and solved and settled and burn_gone and counted


def test_f3_en_tv22_fails_when_the_task_never_settles():
    """The fault: settle_task() never settles, so no link of the paying road
    closes and the meter has nothing to count."""
    with mock.patch.object(f3_en.F3aTestnet, "settle_task",
                           new=lambda self, sid, tid, verify_ok=True: False):
        escrow_funded, solved, settled, burn_gone, counted = \
            f3_en.tv22_end_to_end_paying_task()
    assert settled is False and counted is False


def test_f3_en_tv22_censorship_does_not_inflate_phi_honest_arm():
    still_unsettled, honest_only, one = \
        f3_en.tv22_censorship_does_not_inflate_phi()
    assert still_unsettled and honest_only and one


def test_f3_en_tv22_phi_fault_when_censorship_counts_as_paid():
    """The fault: record_block() counts a censored task as paid, so the
    censoring sequencer's activity inflates phi exactly the way Pearl's
    reporting did."""
    orig = f3_en.DemandMeter.record_block

    def _count_censored(self, testnet):
        orig(self, testnet)
        for sq in testnet.sequencers.values():
            for t in sq.tasks.values():
                if t.state == "CENSORED":
                    self.paid_tasks += 1

    with mock.patch.object(f3_en.DemandMeter, "record_block",
                           new=_count_censored):
        _still, _honest, one = f3_en.tv22_censorship_does_not_inflate_phi()
    assert one is False


def test_f3_en_tv23_realistic_demand_both_ways_honest_arm():
    (zero_is_zero, demand_positive, all_arrivals_settled, phi_orders,
     r0, r1, r2) = f3_en.tv23_realistic_demand_both_ways()
    assert zero_is_zero and demand_positive
    assert all_arrivals_settled and phi_orders
    assert r0["phi_final"] == 0.0 and r0["settled"] == 0
    assert r1["phi_final"] > r2["phi_final"] > r0["phi_final"]


def test_f3_en_tv23_fails_when_no_buyer_ever_arrives():
    """The fault: arrivals_at() returns nobody, so the demanding population
    reproduces the demandless one and phi's ordering collapses."""
    with mock.patch.object(f3_en.BuyerPopulation, "arrivals_at",
                           new=lambda self, height: []):
        (zero_is_zero, demand_positive, all_arrivals_settled, phi_orders,
         r0, r1, r2) = f3_en.tv23_realistic_demand_both_ways()
    assert demand_positive is False
    assert r1["arrivals"] == 0 and r1["settled"] == 0


def test_f3_en_task_harness_id_binds_harness_and_program():
    prog = ((1, 2), (3, 4))
    first = f3_en.task_harness_id("llama-70b", prog)
    # stable for the same (harness, program)
    assert f3_en.task_harness_id("llama-70b", prog) == first
    assert len(first) == 16
    # a different harness or a different program is a different task
    assert f3_en.task_harness_id("mistral-7b", prog) != first
    assert f3_en.task_harness_id("llama-70b", ((5, 6), (7, 8))) != first


def test_f3_en_task_harness_id_fault_when_the_program_is_dropped():
    """The fault: the digest ignores the program, so two different programs
    under one harness share an id — the dedup collision the id exists to
    prevent."""
    orig = f3_en._h_short
    with mock.patch.object(f3_en, "_h_short",
                           new=lambda harness, _prog: orig(harness)):
        same = f3_en.task_harness_id("llama-70b", ((1, 2), (3, 4)))
        other = f3_en.task_harness_id("llama-70b", ((5, 6), (7, 8)))
    assert same == other
