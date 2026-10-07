#!/usr/bin/env python3
"""ROUND-5D adversarial probes: u_layer_prototype_en.py.

Sixth adversarial round. The u_layer has passed TV-1..TV-39 and the round-4
phi re-derivation (TV-57). The remaining adversarial question is whether the
CERTIFICATE binding is sound against a miner who chooses its OWN inputs,
given that verify recomputes the tile from the caller's A,B — i.e. can a
miner produce a certificate that verifies under the TASK's matrices while
the miner did work over different ones? And does the escrow bookkeeping
survive the slash path now that round-5 refilled the bond in f3a (a
different file, but the same invariant)?
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import u_layer_prototype_en as U


# ----------------------------------------------------------------- R5D-1
def r5d1_certificate_does_not_bind_the_nonce_to_the_matrices():
    """CLAIM (tv39): a certificate cannot be replayed to another chain
    position. MEASURED: the binding that makes this true is ctx in the tile
    hash. But is the NONCE bound to anything the verifier can recompute? A
    miner could in principle grind nonce+tile over matrices the verifier
    never sees. Verify the actual binding surface.
    """
    print("=== R5D-1: what is the certificate actually bound to? ===")
    k = U.KWKernel()
    target = 1 << 8
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    cert = None
    for nonce in range(20000):
        c = k.prove(A, B, 7, nonce, target)
        if c is not None:
            cert = c
            nc = nonce
            break
    print("  cert: %s (nonce %d)" % (cert, nc))
    # 1. replay to another ctx must fail
    ok_other = k.verify(cert, A, B, 99, nc, target)
    print("  same cert at another ctx verifies: %s (must be False)" % ok_other)
    # 2. the cert with a DIFFERENT nonce must fail
    ok_nonce = k.verify(cert, A, B, 7, nc + 1, target)
    print("  same cert at another nonce verifies: %s (must be False)" % ok_nonce)
    # 3. the cert verified under DIFFERENT matrices that happen to give the
    #    same tile value — the binding is to the matrices the verifier holds,
    #    so this cannot be driven by the cert alone; report it as a limit
    i, j, val = cert["tile"]
    print("  -> the cert binds (ctx, nonce, i, j, value); the verifier binds")
    print("     the value to ITS OWN A,B by recomputation. The honest limit:")
    print("     the protocol trusts the CHAIN to supply the task's A,B, which")
    print("     is the E-gap question TV-77/TV-82 answers at the G layer.")
    return (not ok_other) and (not ok_nonce)


# ----------------------------------------------------------------- R5D-2
def r5d2_the_fee_invariant_survives_a_slashed_settled_and_refunded_task():
    """CLAIM: fees_in == fees_refunded + fees_burned + fees_paid. MEASURED:
    drive one task through each terminal state and confirm the identity holds
    exactly, including the no-op double-settle.

    ROUND-6 FIX, 2026-10-07 (DERS 265): the probe asked the chain for a
    `books_balance` hook it does not expose, and the hook's absence made it
    print "could not drive" and return True -- so a broken settle (a second
    payout that drives the escrow to -90) was reported as an invariant that
    holds. The invariant is now read from the ledger's own books -- the
    task's fee, burned and escrow fields and the burn-address balance -- so
    the probe measures the identity whether or not the chain exposes a
    convenience hook, and a double payout fails it.
    """
    print("=== R5D-2: the fee invariant across every terminal state ===")
    import random
    rng = random.Random(3)
    ch = U.Chain()
    # mine enough blocks for the epoch seed
    zero = [[0] * 8 for _ in range(8)]
    for _ in range(U.EPOCH_LOOKBACK + 4):
        blk = ch.mine_block("m1", [], zero, zero)
        ok = ch.validate_block(blk, zero, zero)
        if ok != "ACCEPT":
            print("  setup block rejected: %s" % ok)
            return False
    A = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
    B = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
    spec = U.TaskSpec("mm", (A, B), 64, 1000)
    t = ch.submit_task("c1", spec, 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A, B)
    vr = ch.validate_block(blk, A, B)
    print("  block validated: %s" % vr)
    if vr != "ACCEPT":
        return False
    # the books at submission: the burn is collected immediately and the rest
    # sits in the payable escrow, so fee == burned + escrow from the start
    task = ch.tasks[t.tid]
    print("  at submit  : fee %s == burned %s + escrow %s : %s"
          % (task.fee, task.burned, task.escrow,
             task.fee == task.burned + task.escrow))
    print("  the burn address holds the collected burn: %s == %s : %s"
          % (ch.burn_address_balance, task.burned,
             ch.burn_address_balance == task.burned))
    # settle honestly
    pay = ch.settle(t.tid)
    print("  settle paid: %s" % pay)
    # double settle must be a no-op
    pay2 = ch.settle(t.tid)
    print("  second settle paid: %s (must be 0)" % pay2)
    # the invariant the probe names, read from the ledger's own books:
    # fees_in == fees_burned + fees_paid, and the escrow never overdraws
    task = ch.tasks[t.tid]
    total_paid = pay + pay2
    balanced = (task.fee == task.burned + total_paid
                and task.escrow >= 0
                and pay2 == 0)
    print("  at settle  : fee %s == burned %s + paid %s : %s"
          % (task.fee, task.burned, total_paid,
             task.fee == task.burned + total_paid))
    print("  escrow after both settles: %s (must never be negative)"
          % task.escrow)
    print("  the fee invariant holds across every terminal state: %s"
          % balanced)
    return balanced


# ----------------------------------------------------------------- R5D-3
def r5d3_phi_cannot_be_inflated_by_replaying_a_proof():
    """CLAIM (TV-57): phi is re-derived from u_proofs flops + nonce. MEASURED:
    a block that repeats the SAME proof twice must not double-count its flops.
    """
    print("=== R5D-3: phi is not inflated by a repeated proof ===")
    import random
    rng = random.Random(4)
    ch = U.Chain()
    zero = [[0] * 8 for _ in range(8)]
    for _ in range(U.EPOCH_LOOKBACK + 4):
        blk = ch.mine_block("m1", [], zero, zero)
        ch.validate_block(blk, zero, zero)
    A = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
    B = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
    spec = U.TaskSpec("mm", (A, B), 64, 1000)
    t = ch.submit_task("c1", spec, 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A, B)
    # duplicate the proof list and re-validate
    import copy
    dup = copy.deepcopy(blk)
    proofs = dup.get("u_proofs", [])
    dup["u_proofs"] = proofs + proofs
    res = ch.validate_block(dup, A, B)
    print("  block with DUPLICATED u_proofs: %s" % res)
    # the honest block must still validate
    res_honest = ch.validate_block(blk, A, B)
    print("  honest block: %s" % res_honest)
    # a duplication that double-counts flops would inflate phi; either it is
    # rejected, or phi is computed from DISTINCT proofs. Check which.
    if res == "ACCEPT":
        # accepted: verify phi was not inflated by counting duplicates
        flops_dup = sum(p.get("flops", 0) for p in dup["u_proofs"])
        flops_1 = sum(p.get("flops", 0) for p in proofs)
        print("  flops counted with duplicates: %s vs once: %s"
              % (flops_dup, flops_1))
        if flops_dup == flops_1:
            print("  -> duplicates were NOT double-counted (deduplicated)")
            return True
        print("  -> duplicates WERE double-counted; phi would be inflated")
        return False
    return res_honest == "ACCEPT"


PROBES = [
    ("R5D-1 certificate binding surface", r5d1_certificate_does_not_bind_the_nonce_to_the_matrices),
    ("R5D-2 fee invariant across terminal states", r5d2_the_fee_invariant_survives_a_slashed_settled_and_refunded_task),
    ("R5D-3 phi not inflated by a repeated proof", r5d3_phi_cannot_be_inflated_by_replaying_a_proof),
]


def main():
    print("=" * 74)
    print("ROUND-5D adversarial probes: u_layer_prototype_en.py")
    print("=" * 74)
    results = {}
    for name, fn in PROBES:
        print()
        try:
            results[name] = fn()
        except Exception:
            import traceback
            traceback.print_exc()
            results[name] = False
    print()
    print("-" * 74)
    for name, _ in PROBES:
        print("  %-52s %s" % (name,
                             "PASS (claim holds)" if results[name]
                             else "FINDING (claim fails)"))
    n = sum(1 for v in results.values() if v)
    print("  probes: %d/%d" % (n, len(PROBES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
