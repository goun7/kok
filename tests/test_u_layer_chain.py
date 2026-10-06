"""Tests for u_layer_prototype_en.py: the U-layer chain, its ctx binding and
the fraud-window penalty machine.

The U-layer prototype is the pre-testnet reference implementation of the task
lifecycle: submit (escrow + bond + burn) -> VRF assignment -> mine_block
(G-layer KW certificate + U-layer proof) -> validate_block (re-derived fee,
phi and PQ schema) -> challenge / slash / settle within the W_s fraud window.
Its Rust counterparts are the kok-chain, kok-consensus and kok-ctx crates.

Covers (stdlib-only, pure state-machine logic, no external calls):
  * TaskSpec -- deterministic, content-bound program commitments.
  * Chain.submit_task -- the fee/burn/bond split and its guards.
  * Chain.mine_block -- the bond is actually posted to the miner's ledger,
    the anti-aggregation bound, the PQ schema gate and the phi accounting.
  * Chain.validate_block -- every rejection reason, including the re-derived
    fee total and phi (a self-declared field is not trusted).
  * Chain.challenge -- fraud slash + reward, the SETTLED_ALREADY /
    ALREADY_SLASHED terminal guards, the rejected malicious challenge and
    the fraud-window assertion.
  * Chain.settle -- the payout is drawn only from a SOLVED task.
  * Chain.retarget / epoch_seed -- the median-filtered difficulty retarget
    with its 4x clip, and the VRF lookback.
  * KWKernel / VRF -- the certificate binds to the computation and to the
    ctx, and the public key is a commitment rather than the secret.
  * The shipped vectors TV-5/6/7/10/34/38/39 and the kurtosis trap (TV-9),
    each called and asserted directly.
"""

import pytest

import u_layer_prototype_en as ul
from u_layer_prototype_en import (
    BOND_RATIO,
    C_FEE,
    DEADLINE_H,
    EPOCH_LOOKBACK,
    FRAUD_REWARD,
    G_FLOPS,
    PQ_SET,
    S,
    Chain,
    KWKernel,
    TaskSpec,
    VRF,
    W_s,
    kurtosis,
    tv10,
    tv34_empty_input,
    tv38_pearl_gap,
    tv39_ctx_binding,
    tv5,
    tv6,
    tv7,
    tv9_kurtosis_trap,
)

A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]


# ------------------------------------------------------------------ helpers
def _chain(height_blocks=EPOCH_LOOKBACK + 5):
    """A chain padded past the VRF lookback so epoch_seed() is callable."""
    ch = Chain()
    for _ in range(height_blocks):
        ch.blocks.append(S("empty", len(ch.blocks)))
    assert ch.height() >= EPOCH_LOOKBACK
    return ch


def _task(ch, client="c1", fee=100, burn_rate=0.2, miner="m1", program=(A, A)):
    """A task that has been submitted and VRF-assigned to `miner`."""
    t = ch.submit_task(client, TaskSpec("mm", program, 64, DEADLINE_H),
                       fee=fee, burn_rate=burn_rate)
    assert list(ch.assign_tasks(miner, [t], prob=1.0)) == [t]
    assert t.state == "ASSIGNED"
    return t


def _mined(ch, miner="m1", tasks=(), program_a=A, program_b=A, **kw):
    """A mined block over already-assigned tasks."""
    tasks = list(tasks)
    return ch.mine_block(miner, tasks, program_a, program_b, **kw)


def _mined_one(**kw):
    """The common fixture: one assigned task, mined into one block."""
    ch = _chain()
    t = _task(ch)
    blk = _mined(ch, tasks=[t], **kw)
    return ch, t, blk


# ------------------------------------------------------------ TaskSpec
def test_task_spec_program_commit_is_deterministic():
    s1 = TaskSpec("mm", (A, A), 64, DEADLINE_H)
    s2 = TaskSpec("mm", (A, A), 64, DEADLINE_H)
    assert s1.program_commit == s2.program_commit
    assert s1.public_inputs_commit == s2.public_inputs_commit


def test_task_spec_inputs_commit_binds_the_matrix_contents():
    s1 = TaskSpec("mm", (A, A), 64, DEADLINE_H)
    s2 = TaskSpec("mm", (B, A), 64, DEADLINE_H)     # different matrices
    # program_commit is harness+max_flops bound; the INPUTS commit binds the data
    assert s1.program_commit == s2.program_commit
    assert s1.public_inputs_commit != s2.public_inputs_commit


def test_task_spec_program_commit_binds_the_harness():
    s1 = TaskSpec("mm", (A, A), 64, DEADLINE_H)
    s2 = TaskSpec("other", (A, A), 64, DEADLINE_H)
    assert s1.program_commit != s2.program_commit


def test_task_spec_falls_back_for_non_matrix_program():
    s = TaskSpec("mm", "not-a-matrix", 64, DEADLINE_H)
    assert s.public_inputs_commit                      # still a digest
    assert s.public_inputs_commit == TaskSpec(
        "mm", "not-a-matrix", 64, DEADLINE_H).public_inputs_commit


# --------------------------------------------------------- submit_task
def test_submit_task_splits_fee_into_burn_escrow_and_bond():
    ch = _chain()
    t = ch.submit_task("c1", TaskSpec("mm", (A, A), 64, DEADLINE_H),
                       fee=100, burn_rate=0.2)
    assert t.burned == 20                 # int(100 * 0.2)
    assert t.escrow == 80                 # fee - burn
    assert t.bond == 100                  # fee * BOND_RATIO
    assert ch.burn_address_balance == 20  # the burn is collected at submission
    assert t.state == "COMMITTED"


def test_submit_task_burn_rate_upper_bound_is_inclusive():
    ch = _chain()
    t = ch.submit_task("c1", TaskSpec("mm", (A, A), 64, DEADLINE_H),
                       fee=100, burn_rate=0.5)
    assert t.burned == 50


@pytest.mark.parametrize("fee,burn", [(0, 0.2), (-5, 0.2), (100, 0.0),
                                      (100, 0.51), (100, 1.0)])
def test_submit_task_rejects_out_of_range_economics(fee, burn):
    ch = _chain()
    with pytest.raises(AssertionError):
        ch.submit_task("c1", TaskSpec("mm", (A, A), 64, DEADLINE_H),
                       fee=fee, burn_rate=burn)


# ------------------------------------------------------------ VRF
def test_vrf_public_key_is_a_commitment_not_the_secret():
    v = VRF("sk-m1")
    assert v.pk != "sk-m1"
    assert len(v.pk) == 64
    int(v.pk, 16)                       # hex digest, not a raw name


def test_vrf_prove_returns_a_verifiable_shape():
    v = VRF("sk-m1")
    out, proof = v.prove("seed|tid")
    assert isinstance(out, int)
    assert 0 <= out < (1 << 256)
    assert len(proof) == 64
    assert VRF.verify(v.pk, "seed|tid", out, proof) is True


def test_vrf_verify_rejects_the_old_raw_name_key():
    """The pre-fix flaw: pk was the miner's name, which the chain broadcasts."""
    assert VRF.verify("sk-m1", "msg", 1, "0" * 64) is False


@pytest.mark.parametrize("pk", ["", "zz" * 32, "ab" * 31, "ab" * 65])
def test_vrf_verify_rejects_malformed_keys(pk):
    assert VRF.verify(pk, "msg", 1, "0" * 64) is False


def test_vrf_verify_rejects_malformed_outputs():
    v = VRF("sk-m1")
    assert VRF.verify(v.pk, "msg", -1, "0" * 64) is False
    assert VRF.verify(v.pk, "msg", "not-an-int", "0" * 64) is False
    assert VRF.verify(v.pk, "msg", 5, "too-short") is False


# -------------------------------------------------------- epoch_seed
def test_epoch_seed_is_deterministic_and_lookback_bound():
    ch = _chain()
    assert ch.epoch_seed(64) == ul.H("seed", ch.blocks[0])
    assert ch.epoch_seed(64) == ch.epoch_seed(64)


def test_epoch_seed_below_lookback_is_refused():
    ch = _chain()
    with pytest.raises(AssertionError, match="lookback"):
        ch.epoch_seed(EPOCH_LOOKBACK - 1)


def test_epoch_seed_moves_with_the_tip():
    ch = _chain()
    below = ch.epoch_seed(ch.height())
    ch.blocks.append(S("empty", len(ch.blocks)))
    assert ch.epoch_seed(ch.height()) != below


# ---------------------------------------------------------- assign_tasks
def test_assign_tasks_uses_the_vrf_not_the_miners_choice():
    ch = _chain()
    t1 = _task(ch, client="c1")
    # the same task assigned again to another miner is a fresh VRF draw, but
    # the proof always verifies against that miner's public key
    assert t1.assignee == "m1"
    assert VRF.verify(VRF("sk-m1").pk, str(ch.epoch_seed(ch.height())) + "|" + t1.tid,
                      t1.vrf_out, t1.vrf_proof) is True


def test_assign_tasks_skips_non_committed_tasks():
    ch = _chain()
    t = _task(ch)                       # now ASSIGNED
    t2 = ch.submit_task("c2", TaskSpec("mm", (A, A), 64, DEADLINE_H),
                        fee=50, burn_rate=0.1)
    t2.state = "EXPIRED"
    assert list(ch.assign_tasks("m2", [t, t2], prob=1.0)) == []


def test_assign_tasks_vrf_draw_is_deterministic():
    """The same (miner, seed, task) always draws the same VRF output."""
    ch = _chain()
    t = _task(ch)
    seed = ch.epoch_seed(ch.height())
    vrf = VRF("sk-m1")
    first = vrf.prove(str(seed) + "|" + t.tid)
    second = vrf.prove(str(seed) + "|" + t.tid)
    assert first == second
    # a different miner draws a different assignment proof for the same task
    other = VRF("sk-m2").prove(str(seed) + "|" + t.tid)
    assert other != first


def test_assign_tasks_proofs_verify_for_the_assigned_miner():
    ch = _chain()
    tasks = [ch.submit_task("c%d" % i, TaskSpec("mm", (A, A), 64, DEADLINE_H),
                            fee=50, burn_rate=0.1) for i in range(8)]
    seed = ch.epoch_seed(ch.height())
    for t in tasks:
        assert list(ch.assign_tasks("m1", [t], prob=1.0)) == [t]
        assert VRF.verify(VRF("sk-m1").pk, str(seed) + "|" + t.tid,
                          t.vrf_out, t.vrf_proof) is True
        assert t.assignee == "m1"


# ------------------------------------------------------------ mine_block
def test_mine_block_posts_the_bond_to_the_miners_ledger():
    ch, t, blk = _mined_one()
    assert ch.miner_bond("m1")["bond"] == 100     # fee * BOND_RATIO
    assert t.bond == 0                            # posted, not double-counted
    assert blk["miner"] == "m1"
    assert blk["height"] == ch.height()


def test_mine_block_marks_the_task_solved_at_proof_height():
    ch, t, blk = _mined_one()
    assert t.state == "SOLVED"
    # the proof is attested at the height the block was built at
    assert t.proof_height == blk["height"] - 1
    assert t.result is not None


def test_mine_block_binds_the_certificate_to_the_tip_and_miner():
    ch = _chain()
    t = _task(ch)
    blk1 = _mined(ch, tasks=[t])
    blk2 = _mined(ch)                       # the tip moved: ctx must move too
    assert blk1["ctx"] == ul.H("ctx", ch.blocks[-3], "m1", "stark-circle-1")
    assert blk1["ctx"] != blk2["ctx"]


def test_mine_block_phi_is_derived_from_the_public_quantities():
    ch, t, blk = _mined_one()
    u_flops = sum(p["flops"] for p in blk["u_proofs"])
    expected = u_flops / (u_flops + G_FLOPS * blk["nonce"])
    assert blk["phi"] == pytest.approx(expected)
    assert 0.0 <= blk["phi"] <= 1.0


def test_mine_block_empty_task_list_is_liveness_not_failure():
    ch = _chain()
    blk = _mined(ch)
    assert blk["u_proofs"] == []
    assert blk["fee_total"] == 0
    assert blk["phi"] == 0.0
    assert ch.validate_block(blk, A, A) == "ACCEPT"


def test_mine_block_rejects_a_non_pq_proof_system():
    ch = _chain()
    with pytest.raises(AssertionError, match="outside the PQ schema"):
        _mined(ch, proof_system_id="legacy-snark-v0")


def test_mine_block_accepts_the_other_pq_schema():
    ch = _chain()
    t = _task(ch)
    blk = _mined(ch, tasks=[t], proof_system_id="stark-pq-1")
    assert blk["u_proofs"][0]["ps"] == "stark-pq-1"
    assert ch.validate_block(blk, A, A) == "ACCEPT"


def test_mine_block_enforces_the_anti_aggregation_bound():
    ch = _chain()
    tasks = [ch.submit_task("c%d" % i, TaskSpec("mm", (A, A), 64, DEADLINE_H),
                            fee=100, burn_rate=0.1) for i in range(6)]
    for t in tasks:                       # 6 * 100 = 600 > C_FEE = 500
        list(ch.assign_tasks("m1", [t], prob=1.0))
    with pytest.raises(AssertionError, match="anti-aggregation"):
        _mined(ch, tasks=tasks)


def test_mine_block_aggregation_is_legal_when_split():
    ch = _chain()
    tasks = []
    for i in range(6):
        t = ch.submit_task("c%d" % i, TaskSpec("mm", (A, A), 64, DEADLINE_H),
                           fee=100, burn_rate=0.1)
        list(ch.assign_tasks("m1", [t], prob=1.0))
        tasks.append(t)
    b1 = _mined(ch, tasks=tasks[:3])
    b2 = _mined(ch, tasks=tasks[3:])
    assert ch.validate_block(b1, A, A) == "ACCEPT"
    assert ch.validate_block(b2, A, A) == "ACCEPT"


def test_mine_block_wrong_result_still_validates_on_chain():
    """Weak on-chain verification cannot see the fraud; the challenge can."""
    ch, t, blk = _mined_one(wrong_result=True)
    assert ch.validate_block(blk, A, A) == "ACCEPT"
    assert t.result[0][0] != (A[0][0] * A[0][0] + A[0][1] * A[1][0]) % 97


# --------------------------------------------------------- validate_block
def test_validate_block_accepts_an_honest_block():
    ch, t, blk = _mined_one()
    assert ch.validate_block(blk, A, A) == "ACCEPT"


def test_validate_block_rejects_a_replayed_ctx():
    ch, t, blk = _mined_one()
    replayed = dict(blk, ctx=blk["ctx"] + 1)
    assert ch.validate_block(replayed, A, A) == "REJECT:G-cert"


def test_validate_block_rejects_a_self_declared_phi():
    ch, t, blk = _mined_one()
    assert ch.validate_block(dict(blk, phi=0.99), A, A) == "REJECT:phi-mismatch"


def test_validate_block_rejects_an_out_of_range_phi():
    ch, t, blk = _mined_one()
    assert ch.validate_block(dict(blk, phi=1.5), A, A) == "REJECT:phi-range"
    assert ch.validate_block(dict(blk, phi=-0.1), A, A) == "REJECT:phi-range"


def test_validate_block_rejects_a_declared_fee_total():
    """The fee total is re-derived from the proofs; the field is informational."""
    ch, t, blk = _mined_one()
    padded = dict(blk, fee_total=blk["fee_total"] + 1)
    assert ch.validate_block(padded, A, A) == "REJECT:fee-total-mismatch"


def test_validate_block_enforces_anti_aggregation_on_the_derived_fee():
    ch, t, blk = _mined_one()
    ch.tasks[t.tid].fee = C_FEE + 1          # derived total now exceeds the cap
    assert ch.validate_block(blk, A, A) == "REJECT:anti-aggregation"


def test_validate_block_rejects_a_pq_downgrade():
    ch, t, blk = _mined_one()
    downgraded = dict(blk, u_proofs=[dict(p, ps="legacy-snark-v0")
                                     for p in blk["u_proofs"]])
    assert ch.validate_block(downgraded, A, A) == "REJECT:PQ-schema"


def test_validate_block_rejects_an_unsolved_task():
    ch, t, blk = _mined_one()
    t.state = "COMMITTED"
    assert ch.validate_block(blk, A, A) == "REJECT:task-state"


def test_kw_kernel_verify_rejects_no_certificate():
    ch = _chain()
    assert ch.kernel.verify(None, A, A, 1, 1, ch.D) is False


# ------------------------------------------------------------ challenge
def test_challenge_proves_fraud_slashes_and_rewards():
    ch, t, blk = _mined_one(wrong_result=True)
    verdict, reward = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "SLASHED"
    assert reward == FRAUD_REWARD
    assert t.state == "SLASHED"
    # the bond is actually debited, the reward actually credited
    assert ch.miner_bond("m1")["bond"] == 0
    assert ch.miner_bond("m1")["slashed"] == 100
    assert ch.miner_bond("v1")["bond"] == FRAUD_REWARD
    assert ch.slashed_total == 100


def test_challenge_slashes_a_bond_below_the_fee():
    ch = _chain()
    t = ch.submit_task("c1", TaskSpec("mm", (A, A), 64, DEADLINE_H),
                       fee=100, burn_rate=0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    _mined(ch, tasks=[t], wrong_result=True)
    ch.miner_bond("m1")["bond"] = 30
    verdict, _ = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "SLASHED"
    assert ch.miner_bond("m1")["bond"] == 0        # floor at 0


def test_challenge_on_an_honest_result_is_rejected():
    ch, t, blk = _mined_one()
    verdict, reward = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "CHALLENGE_REJECTED"
    assert reward == 0
    assert t.state == "SOLVED"                     # unchanged
    # the malicious challenger is counted, so abuse is visible
    assert ch.miner_bond("v1")["slashed"] == 1


def test_challenge_after_settlement_is_refused():
    """SETTLED is terminal for the fraud path: no slash on an empty account."""
    ch, t, blk = _mined_one()
    assert ch.settle(t.tid) == 80
    verdict, reward = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "SETTLED_ALREADY"
    assert reward == 0
    assert ch.miner_bond("v1")["slashed"] == 1
    assert t.state == "SETTLED"


def test_challenge_twice_is_refused():
    ch, t, blk = _mined_one(wrong_result=True)
    assert ch.challenge("v1", t.tid, ch.height()) == ("SLASHED", FRAUD_REWARD)
    verdict, reward = ch.challenge("v2", t.tid, ch.height())
    assert verdict == "ALREADY_SLASHED"
    assert reward == 0
    assert ch.miner_bond("v2")["slashed"] == 1


def test_challenge_outside_the_fraud_window_is_refused():
    ch, t, blk = _mined_one(wrong_result=True)
    with pytest.raises(AssertionError, match="fraud window closed"):
        ch.challenge("v1", t.tid, t.proof_height + W_s + 1)


def test_challenge_inside_the_fraud_window_is_allowed():
    ch, t, blk = _mined_one(wrong_result=True)
    verdict, _ = ch.challenge("v1", t.tid, t.proof_height + W_s)
    assert verdict == "SLASHED"


# --------------------------------------------------------------- settle
def test_settle_pays_the_escrow_and_marks_settled():
    ch, t, blk = _mined_one()
    assert ch.settle(t.tid) == 80            # fee 100 - burned 20
    assert t.state == "SETTLED"
    assert t.escrow == 0                     # only the payable part was drawn


@pytest.mark.parametrize("state", ["COMMITTED", "ASSIGNED", "SETTLED", "SLASHED"])
def test_settle_refuses_any_non_solved_state(state):
    ch, t, blk = _mined_one()
    t.state = state
    assert ch.settle(t.tid) == 0


def test_settle_does_not_double_pay():
    ch, t, blk = _mined_one()
    assert ch.settle(t.tid) == 80
    assert ch.settle(t.tid) == 0             # SETTLED is terminal


# -------------------------------------------------------------- retarget
def test_retarget_is_a_noop_off_the_window_boundary():
    ch = Chain()
    ch.retarget_window = 4
    ch.times = [0.0, 1.0, 2.0, 3.0]          # n = 3, 3 % 4 != 0
    assert ch.retarget() is None
    assert ch.D == 1 << 6


def test_retarget_estimates_hashrate_and_resets_difficulty():
    ch = Chain()
    ch.retarget_window = 4
    ch.times = [0.0, 10.0, 20.0, 30.0, 40.0]      # T_act = 40 for 4 blocks
    r = ch.retarget()
    assert r["T_act"] == 40.0
    # lam_hat = D * W / T_act = 64 * 4 / 40
    assert r["lam_hat"] == 6.4
    assert r["lam_smooth"] == 6.4
    # D <- lam_smooth * T_b = 6.4 * 0.1 = 0.64 -> int 0 -> clipped to the floor
    assert r["D"] == 16
    assert r["ratio"] == 0.25


def test_retarget_median_filters_the_last_three_windows():
    ch = Chain()
    ch.retarget_window = 4
    ch.times = [0.0, 10.0, 20.0, 30.0, 40.0]
    assert ch.retarget()["lam_smooth"] == 6.4
    ch.times += [50.0, 60.0, 70.0, 80.0]         # lam_hat = 16*4/40 = 1.6
    r = ch.retarget()
    # median of (6.4, 1.6) with an even count takes the upper middle value
    assert r["lam_smooth"] == 6.4
    assert r["D"] == 4


def test_retarget_clips_a_rising_estimate_at_4x():
    ch = Chain()
    ch.retarget_window = 4
    # a very fast window estimates a huge hashrate: D may only rise 4x
    ch.times = [0.0, 0.01, 0.02, 0.03, 0.04]
    r = ch.retarget()
    assert r["ratio"] == 4.0
    assert r["D"] == 256


def test_retarget_never_sets_a_zero_difficulty():
    ch = Chain()
    ch.retarget_window = 2
    ch.times = [0.0, 1e9, 2e9]                    # T_act huge -> lam_hat ~ 0
    r = ch.retarget()
    assert r["D"] >= 1
    assert ch.D >= 1


def test_record_time_accumulates():
    ch = Chain()
    ch.record_time(1.5)
    ch.record_time(2.5)
    assert ch.times == [0.0, 1.5, 4.0]


# --------------------------------------------------------------- liveness
def test_zero_demand_liveness_all_blocks_valid():
    """No U-task for many blocks: every block still validates (Pearl's regime)."""
    ch = _chain()
    ok = 0
    for _ in range(60):
        blk = _mined(ch)
        if ch.validate_block(blk, A, A) == "ACCEPT":
            ok += 1
    assert ok == 60
    assert len(ch.tasks) == 0


def test_empty_input_mines_but_carries_no_utility():
    """A=B=0 still produces a certificate: the defense is economic, not G-layer."""
    ch = _chain()
    n = 8
    zero = [[0] * n for _ in range(n)]
    blk = _mined(ch, program_a=zero, program_b=zero)
    assert ch.validate_block(blk, zero, zero) == "ACCEPT"
    assert blk["phi"] == 0.0


# ------------------------------------------------------------- kurtosis
def test_kurtosis_of_a_constant_matrix_is_zero():
    assert kurtosis([[7, 7], [7, 7]]) == 0.0


def test_kurtosis_distinguishes_uniform_from_gaussian():
    rnd = __import__("random").Random(1)
    uniform = [[rnd.randint(-64, 64) for _ in range(64)] for _ in range(64)]
    nn_like = [[int(rnd.gauss(0, 3)) for _ in range(64)] for _ in range(64)]
    # uniform: kurtosis below the Gaussian value of 3
    assert kurtosis(uniform) < 3.0
    assert 2.0 <= kurtosis(nn_like) <= 4.0


# ----------------------------------------------- the shipped test vectors
def test_tv5_escrow_burn_and_sybil_cost():
    burned, escrow, sybil_cost = tv5()
    assert (burned, escrow, sybil_cost) == (30, 70, 30000)


def test_tv6_anti_aggregation():
    caught, n_blocks = tv6()
    assert caught is True
    assert n_blocks == 2


def test_tv7_fraud_slash():
    verdict, slashed, reward = tv7()
    assert verdict == "SLASHED"
    assert slashed >= 100
    assert reward == FRAUD_REWARD


def test_tv10_pq_downgrade_is_rejected():
    assert tv10() is True


def test_tv34_empty_input_attack():
    ok_g, phi0, ok_u, phi1 = tv34_empty_input()
    assert ok_g is True              # empty mining still validates (utility is 0)
    assert phi0 == 0.0
    assert ok_u is True
    assert phi1 > 0.0                # a real task carries positive utility density


def test_tv38_pearl_gap_verification_binds_the_computation():
    real, wrong_input, fabricated, forged_value = tv38_pearl_gap()
    assert real is True
    assert wrong_input is False
    assert fabricated is False
    assert forged_value is False


def test_tv39_ctx_binding_rejects_replay():
    at_home, replayed = tv39_ctx_binding()
    assert at_home is True
    assert replayed is False


def test_tv9_kurtosis_trap_is_an_honest_negative_result():
    """The adversarial N(0,18) matrix PASSES the naive kurtosis check."""
    r = tv9_kurtosis_trap()
    assert r["adversarial_passes_naive_check"] is True
    assert 2.0 <= r["adversarial"] <= 4.0
    assert r["uniform"] < 3.0
