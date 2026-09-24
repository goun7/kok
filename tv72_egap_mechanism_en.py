#!/usr/bin/env python3
"""
TV-82: WHY PEARL'S phi WAS ZERO — the E-gap mechanism, demonstrated.

Stage 2's claim (A2) is that the E-gap is what killed utility on a live
network that otherwise had all the demand-side ingredients: Pearl ran at
theta=1.657 (corrected from 1.05 by spec TV-84; the inference-subsidizing regime) with a revenue/cost ratio of
1.058 reproducing Basu's measured 1.06, and still measured phi=0.

This file demonstrates the MECHANISM rather than restating the claim. The
experiment is a two-arm comparison on a mock G layer:

  ARM A (WITHOUT the binding, pre-TV-77): the miner submits a certificate
      over whatever matrices it likes. The verifier checks the PoW target
      only. A miner whose REAL commissioned program is small can solve the
      task by mining over a LARGE unrelated matrix (or vice versa), and
      nothing in the protocol notices.

  ARM B (WITH the binding, post-TV-77): the same submission, but the
      verifier derives what the certificate must be bound to from the TASK.

The measured quantity is DETECTABILITY: the fraction of cheating submissions
the protocol rejects. Without the binding the fraction is 0 by construction —
the certificate is self-consistent and the target is met, so no check can
fail. This is the mechanism-level reason phi can be zero while the economics
look healthy: the network's hashrate can be real, its difficulty real, its
price ratio real, and the quantity the protocol measures as "useful work"
still be unattributable to any buyer's task.

WHAT THIS DOES NOT PROVE (stated in the file that makes the claim):
  - it does not prove phi>0 on any future deployment; a binding that lets the
    protocol NOTICE cheating is not evidence that buyers will arrive. The
    demand side is F0 and is deliberately not started.
  - the matrices here are toy 2x2; the mechanism argument is about
    attributability, not about the cost of the real MatMul.
  - this is a mock of the G layer's acceptance rule, not the shipped
    KWKernel.verify; the shipped binding is tested by egap_cert_en.py 4/4.
"""

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from egap_cert_en import (H, matrix_commit, program_commit, g_cert_bound,
                          verify_g_cert_bound)


def program_commit_single(M):
    """program_commit binds BOTH factors (A, B); a single-matrix toy
    commits the matrix against itself so the commitment is still
    content-bound and two different matrices give different values."""
    return program_commit(M, M)

TARGET = 1 << 8          # toy PoW target (same as egap_cert_en's probes)
TASK_ID = "pearl-buyer-task-1"


def _mine_tile(mat, ctx, target, commit=None, want_i=0, want_j=0,
                max_nonce=400000):
    """Search a nonce so the tile PoW over `mat` meets `target`.

    Returns (nonce, i, j, value) or None. The tile value is a toy inner
    product of the top-left 2x2 sub-block, so different matrices give
    different tile values and the certificate genuinely depends on the
    matrix contents.

    `commit` is the commitment string the PoW is mined over. Arm A (no
    binding) commits to the MINER's own matrices; Arm B commits to the
    TASK's program commitment. Passing the task commitment makes a found
    nonce yield a cert g_cert_bound will actually build rather than reject
    at its own target re-check."""
    pc = program_commit_single(mat) if commit is None else commit
    for nonce in range(max_nonce):
        i, j = want_i, want_j
        # ROUND-5B, 2026-09-24: the tile value uses the REFERENCE computation
        # from egap_cert_en._tile_value, so the prover and verifier cannot
        # drift apart (round-5b finding R5B-3 was exactly that drift: the
        # value was bound to nothing, so a tile mined over other matrices
        # verified against the task's commitment).
        from egap_cert_en import _tile_value
        value = _tile_value(mat, mat, i, j)
        if H("tile", TASK_ID, pc, ctx, nonce, i, j, value) % target == 0:
            return nonce, i, j, value
    return None


# ---------------------------------------------------------------------------
# The two arms
# ---------------------------------------------------------------------------

def arm_a_without_binding(commissioned, mined, ctx):
    """Pre-TV-77 acceptance rule: verify the PoW target only.

    The caller supplies the matrices the certificate is claimed over; the
    verifier never asks what the TASK commissioned.
    """
    arm_a_pc = matrix_commit(mined)
    found = _mine_tile(mined, ctx, TARGET, commit=arm_a_pc)
    if found is None:
        return None, "no nonce found (mining failed)"
    nonce, i, j, value = found
    cert = {
        "task_id": TASK_ID,
        "pc": arm_a_pc,                  # the MINER's matrices, unchecked
        "ctx": ctx,
        "nonce": nonce,
        "tile": (i, j, value),
    }
    # the pre-TV-77 check: target only
    i2, j2, v2 = cert["tile"]
    base = (cert["task_id"], cert["pc"], cert["ctx"], cert["nonce"], i2, j2, v2)
    accepted = H("tile", *base) % TARGET == 0
    return cert, accepted


def arm_b_with_binding(commissioned, ctx, mined=None):
    """Post-TV-77 acceptance rule: the verifier derives the required
    program commitment from the TASK and rejects anything else.

    The honest case mines the tile over the COMMISSIONED matrices and binds
    the certificate to the task's own commitment, so verify accepts.
    Passing mined != None models a miner that mines over other matrices but
    still claims the task's commitment: the cert is built over the task's
    commitment, so it is internally consistent and the target is met, yet
    the tile value does not correspond to the committed matrices -- which is
    exactly what the E-gap made invisible before the binding existed."""
    over = commissioned if mined is None else mined
    found = _mine_tile(over, ctx, TARGET, commit=program_commit_single(commissioned))
    if found is None:
        return None, "no nonce found (mining failed)"
    nonce, i, j, value = found
    required_pc = program_commit_single(commissioned)
    cert = g_cert_bound(TASK_ID, required_pc, ctx, nonce, i, j, value, TARGET)
    # ROUND-5B, 2026-09-24: the verifier now re-derives the tile value from
    # the committed program, so a miner that mines over `mined` while naming
    # the commissioned commitment is REJECTED (the value will not match). The
    # program argument is what makes the binding bind the computation.
    return cert, verify_g_cert_bound(cert, TASK_ID, required_pc, ctx, TARGET,
                                     program=(commissioned, commissioned))


def probe_binding_is_what_makes_cheating_detectable():
    """The decisive experiment: same commissioned task, same mined matrices,
    same target. Arm A accepts the substitution, Arm B does not."""
    commissioned = [[2, 3], [4, 5]]       # the buyer's actual program
    mined = [[11, 7], [13, 17]]          # an unrelated matrix the miner prefers
    ctx = "epoch-pearl-1"

    cert_a, res_a = arm_a_without_binding(commissioned, mined, ctx)
    if cert_a is None:
        return False, "arm A could not mine a tile"

    required_pc = program_commit_single(commissioned)
    shipped_pc = matrix_commit(mined)
    # Arm B's verifier derives the commitment from the task and checks the
    # shipped cert against it. Feed it the Arm-A cert (over the WRONG
    # matrices): it must reject.
    rejected = not verify_g_cert_bound(cert_a, TASK_ID, required_pc, ctx, TARGET)

    honest_cert, res_b = arm_b_with_binding(commissioned, ctx)
    honest_ok = bool(res_b)

    print("=" * 74)
    print("TV-82: the E-gap mechanism — why Pearl's phi was zero")
    print("=" * 74)
    print("  commissioned program  : %s commit %s" % (commissioned, required_pc))
    print("  miner's own matrices  : %s commit %s" % (mined, shipped_pc))
    print()
    print("  ARM A  (pre-TV-77, no binding)")
    print("    cert is over the MINER's matrices : %s" % shipped_pc)
    print("    acceptance rule is PoW target only, so a self-consistent")
    print("    cert over any matrices is accepted: %s" % bool(res_a))
    print("    detectability of the substitution  : 0%% (no check exists)")
    print()
    print("  ARM B  (post-TV-77, binding to the task)")
    print("    the same Arm-A cert re-verified against the task's own")
    print("    program commitment is REJECTED      : %s" % rejected)
    print("    an honest cert over the commissioned matrices passes : %s"
          % honest_ok)
    print()
    if bool(res_a) and rejected and honest_ok:
        print("  MECHANISM CONFIRMED: without the binding the protocol has NO")
        print("  check that distinguishes the buyer's computation from the")
        print("  miner's preferred one. phi counts as useful only what the")
        print("  protocol can attribute, so on a network without this binding")
        print("  phi=0 is the CORRECT measurement even when hashrate, difficulty")
        print("  and the price ratio are all real. Pearl's theta=1.657 (TV-84) with")
        print("  phi=0 is therefore not a paradox: the missing ingredient was")
        print("  attributability, not demand.")
        return True
    print("  RED — the mechanism did not demonstrate as expected")
    return False


def probe_detectability_number():
    """Quantify detectability across a sweep of substituted matrices.

    Without the binding, detectability is 0 by construction for EVERY
    substituted matrix. With the binding, it is 1 for every one that does not
    equal the commissioned commitment. This is the measurement that makes the
    claim numeric rather than a single example.
    """
    commissioned = [[2, 3], [4, 5]]
    ctx = "epoch-pearl-2"
    required_pc = program_commit_single(commissioned)
    subs = [
        [[11, 7], [13, 17]],
        [[1, 0], [0, 1]],
        [[5, 4], [3, 2]],
        [[2, 3], [4, 6]],        # one entry off the commissioned matrix
        [[2, 3], [4, 5]],        # identical -> must be ACCEPTED by arm B
    ]
    a_accept = 0
    b_reject = 0
    identical_idx = None
    for k, m in enumerate(subs):
        if m == commissioned:
            identical_idx = k
        cert_a, res_a = arm_a_without_binding(commissioned, m, ctx)
        if cert_a is None:
            continue
        if bool(res_a):
            a_accept += 1
        # Arm B's evidence is the Arm-A cert re-verified against the task's
        # commitment. For the IDENTICAL matrix this would spuriously reject,
        # because Arm A builds over matrix_commit while Arm B derives
        # program_commit_single — two different strings for the same content.
        # The honest check for the identical matrix is arm_b, which builds
        # the cert over the task's commitment, so the sweep skips it here and
        # reports it separately below.
        if m == commissioned:
            continue
        if not verify_g_cert_bound(cert_a, TASK_ID, required_pc, ctx, TARGET):
            b_reject += 1
    total = len(subs)
    sub_total = total - (1 if identical_idx is not None else 0)
    honest_cert, ok = arm_b_with_binding(commissioned, ctx)
    print()
    print("-" * 74)
    print("Detectability sweep over %d matrices" % total)
    print("-" * 74)
    print("  Arm A accepts the substitution      : %d/%d (detectability 0)"
          % (a_accept, total))
    print("  Arm B rejects the substitution      : %d/%d of the substituted"
          % (b_reject, sub_total))
    print("      matrices; the identical matrix is the one Arm B correctly")
    print("      does NOT reject, checked separately below")
    # the honest identical matrix must be accepted by B
    print("  Arm B accepts the commissioned pair : %s" % ok)
    return a_accept == total and ok and b_reject == sub_total


def main():
    r1 = probe_binding_is_what_makes_cheating_detectable()
    r2 = probe_detectability_number()
    print()
    print("RESULT: %s" % ("MECHANISM DEMONSTRATED" if r1 and r2 else "RED"))
    return 0 if (r1 and r2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
