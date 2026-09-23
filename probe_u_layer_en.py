#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KOK v2 — adversarial edge probes for the u_layer L1 prototype (TV-51..TV-55).

The f3a probes found three real accounting bugs, so the same method is applied
here. These probe the corners the TV tests do not cover. A RED result is either a
bug to fix or a design limit to document, never a silent pass.

The u_layer burns the earmarked portion at SUBMISSION time, not at settlement
(L182 of u_layer_prototype_en.py). That is a deliberate difference from f3a,
which burns at settlement. It has a consequence worth probing: the buyer's
escrow field is initialised to fee - burn, so the burn is already absent from
it, and settle() must therefore draw only the payable part. An earlier version
did t.escrow -= (burned + pay), subtracting the burn a second time and driving
the field to -30; that double subtraction was FIXED (2026-09-23: settle() now
does t.escrow -= pay) and TV-51 below is the regression guard that keeps it
fixed.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from u_layer_prototype_en import (Chain, TaskSpec, C_FEE, BOND_RATIO,
                                  W_s, FRAUD_REWARD, DEFAULT_PS,
                                  EPOCH_LOOKBACK)


M = [[1, 2], [3, 4]]


def spec(program=None):
    # program is the (A, B) matrix pair that "useful work" stands in for here;
    # the miner computes the harness product, so these must be real matrices.
    return TaskSpec(harness_id="probe", deadline=1000,
                    program=program or (M, M), max_flops=1000)


def warm(ch):
    """Advance past the VRF lookback so epoch_seed can be computed.

    The seed is read from EPOCH_LOOKBACK blocks ago (grinding resistance), so no
    task can be assigned until the chain is that tall. The TV tests do the same.
    """
    for _ in range(EPOCH_LOOKBACK + 5):
        ch.sim_block(1.0)


def report(name, ok, detail=""):
    print("  %-46s %s %s" % (name, "ACCEPT" if ok else "RED", detail))
    return ok


def tv51_escrow_nonnegative_after_settle():
    """The escrow field must be exactly 0 after settlement, never negative.

    submit_task sets t.escrow = fee - burn (70 of a 100 fee, burn_rate 0.3),
    because the burn is collected at submission and is therefore already absent
    from the escrow. settle() draws only that payable part, t.escrow -= pay, so
    the field ends at exactly 0 while the miner is paid 70 and the burn address
    holds 30.

    FIXED (2026-09-23): an earlier settle() did t.escrow -= (burned + pay),
    subtracting the burn a second time and driving the field to -30 even though
    every coin was accounted for correctly elsewhere. The money flow was right;
    the bookkeeping field was wrong, and any code reading t.escrow to report
    health would have reported a shortfall that did not exist. This probe is the
    regression guard for that fix: it goes RED the moment the double subtraction
    returns.
    """
    ch = Chain()
    warm(ch)
    t = ch.submit_task("kobi", spec(), fee=100, burn_rate=0.3)
    ch.miner_bond("A")["bond"] = 1000
    t2 = list(ch.assign_tasks("A", [t]))
    blk = ch.mine_block("A", t2, M, M)
    assert ch.validate_block(blk, M, M) == "ACCEPT"
    pay = ch.settle(t.tid)
    escrow_after = t.escrow
    ok = (escrow_after == 0 and pay == 70 and ch.burn_address_balance == 30)
    return report("TV-51 escrow non-negative after settle", ok,
                  "escrow=%d pay=%d burn_addr=%d" % (escrow_after, pay,
                                                     ch.burn_address_balance))


def tv52_double_settle_pays_once():
    """Settling an already-SETTLED task must not pay the miner twice.
    """
    ch = Chain()
    warm(ch)
    t = ch.submit_task("kobi", spec(), fee=100, burn_rate=0.3)
    ch.miner_bond("A")["bond"] = 1000
    t2 = list(ch.assign_tasks("A", [t]))
    blk = ch.mine_block("A", t2, M, M)
    assert ch.validate_block(blk, M, M) == "ACCEPT"
    first = ch.settle(t.tid)
    second = ch.settle(t.tid)
    ok = (first == 70 and second == 0)
    return report("TV-52 double settle pays once", ok,
                  "first=%d second=%d" % (first, second))


def tv53_slashed_task_pays_miner_nothing():
    """A SLASHED task must pay the miner nothing, and the state must be final.
    """
    ch = Chain()
    warm(ch)
    t = ch.submit_task("kobi", spec(), fee=100, burn_rate=0.3)
    ch.miner_bond("A")["bond"] = 1000
    t2 = list(ch.assign_tasks("A", [t]))
    blk = ch.mine_block("A", t2, M, M, wrong_result=True)
    assert ch.validate_block(blk, M, M) == "ACCEPT"
    res, reward = ch.challenge("C", t.tid, ch.height())
    pay = ch.settle(t.tid)
    slashed = ch.miners["A"]["slashed"]
    ok = (res == "SLASHED" and pay == 0 and t.state == "SLASHED"
          and slashed == int(100 * BOND_RATIO))
    return report("TV-53 slashed task pays miner nothing", ok,
                  "res=%s pay=%d slashed=%d" % (res, pay, slashed))


def tv54_burn_at_submission_is_irrecoverable():
    """u_layer burns at submission, so an abandoned task's burn is already gone.

    This is the deliberate design difference from f3a (f3a burns at settlement
    and refunds the full fee on timeout). Here there is no REFUNDED state: if a
    task is never mined, the burn has already been collected and the buyer does
    not get it back. The probe does not call this a bug — it measures it, so the
    two prototypes are not silently conflated. u_layer is the L1 mechanics; f3a
    is the economics, and only f3a has the refund-guarantee.
    """
    ch = Chain()
    t = ch.submit_task("kobi", spec(), fee=100, burn_rate=0.3)
    burn_at_submit = ch.burn_address_balance
    # the task is never assigned or mined; the chain moves on
    ch.sim_block(1.0)
    ch.sim_block(1.0)
    ok = (burn_at_submit == 30 and t.state == "COMMITTED"
          and ch.burn_address_balance == 30)
    return report("TV-54 burn at submission, no refund path", ok,
                  "burn_addr=%d state=%s (documented, not fixed)"
                  % (ch.burn_address_balance, t.state))


def tv55_challenge_after_window_refused():
    """A challenge past the fraud window W_s must be refused.
    """
    ch = Chain()
    warm(ch)
    t = ch.submit_task("kobi", spec(), fee=100, burn_rate=0.3)
    ch.miner_bond("A")["bond"] = 1000
    t2 = list(ch.assign_tasks("A", [t]))
    blk = ch.mine_block("A", t2, M, M, wrong_result=True)
    assert ch.validate_block(blk, M, M) == "ACCEPT"
    proof_h = t.proof_height
    refused = False
    try:
        ch.challenge("C", t.tid, proof_h + W_s + 1)
    except AssertionError:
        refused = True
    ok = refused
    return report("TV-55 challenge past fraud window refused", ok,
                  "W_s=%d" % W_s)


def tv56_vrf_public_key_is_not_the_secret():
    """Stage 1.4 (2026-09-23): knowing a miner's public identity must not let
    you forge its assignment proof.

    Before the fix the chain published pk = "sk-<name>" — the SECRET itself —
    and verify() recomputed the HMAC keyed by that string. So anyone who read
    the chain could produce a valid proof for any miner. The public key is now
    a digest of the secret, and prove() signs over (pk, msg).

    HONEST LIMIT, measured and stated rather than hidden: this probe measures
    the PROVER side exactly — a second miner's proof over the same message
    differs, and the old raw-name pk form no longer verifies. The VERIFIER
    side cannot be closed in a hash-based toy: without sk the verifier cannot
    recompute the HMAC, so verify() is a structural check on shape and range.
    A real fix is ECVRF (the document's own roadmap item), where the public
    key verifies the signature without the secret. What this does prove is
    that the specific published flaw — the chain broadcasting the secret —
    is gone.
    """
    from u_layer_prototype_en import VRF
    m1 = VRF("sk-m1")
    m2 = VRF("sk-m2")
    pk_is_secret = (m1.pk == "sk-m1")
    msg = "seed|task-1"
    out1, proof1 = m1.prove(msg)
    out2, _ = m2.prove(msg)
    forge_reproduces = (out2 == out1)
    accepts_honest = VRF.verify(m1.pk, msg, out1, proof1)
    # the old raw-name pk form must be rejected outright
    rejects_old_form = not VRF.verify("sk-m1", msg, out1, proof1)
    ok = (not pk_is_secret and not forge_reproduces and accepts_honest
          and rejects_old_form)
    return report("TV-56 VRF public key is not the secret", ok,
                  "pk==secret=%s forge_reproduces=%s honest=%s old-form-rejected=%s"
                  % (pk_is_secret, forge_reproduces, accepts_honest,
                     rejects_old_form))


def tv57_phi_is_rederived_not_trusted():
    """Round-4 (2026-09-23), round-3 finding [16]: phi was only range-checked
    against the miner's claim, so a miner could declare phi=0.99 while doing
    zero useful work. The verifier now re-derives phi from the proofs' flops
    and the nonce; this probe drives the lie directly.
    """
    ch = Chain()
    warm(ch)
    t = ch.submit_task("kobi", spec(), fee=100, burn_rate=0.3)
    ch.miner_bond("A")["bond"] = 1000
    t2 = list(ch.assign_tasks("A", [t]))
    blk = ch.mine_block("A", t2, M, M)
    honest = ch.validate_block(blk, M, M)
    honest_phi = blk["phi"]
    # the lie: same block, phi claimed as if the block were almost all useful
    import copy
    lie = copy.deepcopy(blk)
    lie["phi"] = 0.99
    lied = None
    try:
        lied = ch.validate_block(lie, M, M)
    except Exception as e:
        lied = "raised %s" % type(e).__name__
    ok = (honest == "ACCEPT" and lied == "REJECT:phi-mismatch")
    return report("TV-57 phi re-derived, not trusted", ok,
                  "honest=%s honest_phi=%.4f lied=%s"
                  % (honest, honest_phi, lied))


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — u_layer L1 adversarial edge probes (TV-51..TV-57)")
    print("=" * 76)
    print()
    results = [tv51_escrow_nonnegative_after_settle(),
               tv52_double_settle_pays_once(),
               tv53_slashed_task_pays_miner_nothing(),
               tv54_burn_at_submission_is_irrecoverable(),
               tv55_challenge_after_window_refused(),
               tv56_vrf_public_key_is_not_the_secret(),
               tv57_phi_is_rederived_not_trusted()]
    print()
    n = sum(1 for r in results if r)
    print("probes: %d/%d" % (n, len(results)))
    if n != len(results):
        print("RED PROBES REMAIN — fix the bug or document the limit.")
        raise SystemExit(1)
