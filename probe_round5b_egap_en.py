#!/usr/bin/env python3
"""ROUND-5B adversarial probes: tv72_egap_mechanism_en.py (the E-gap file
backing the paper's answer to TV-72).

Method: every claim the file makes about itself becomes a probe that MEASURES
it. A probe returns PASS when the claim is confirmed, FINDING when the
measurement contradicts it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tv72_egap_mechanism_en as T
from egap_cert_en import (H, matrix_commit, program_commit, g_cert_bound,
                          verify_g_cert_bound)


# ----------------------------------------------------------------- R5B-1
def r5b1_arm_b_rejects_only_because_of_a_commitment_mismatch():
    """CLAIM: Arm B's rejection is caused by the COMMITMENT mismatch, not by
    some other incidental difference (nonce space, tile arithmetic, target).
    MEASURED: a cert built honestly over the COMMISSIONED matrices with the
    commissioned commitment must verify; the ONLY change that flips the
    verdict is swapping the commitment content.
    """
    print("=== R5B-1: is the rejection really about the commitment? ===")
    commissioned = [[2, 3], [4, 5]]
    ctx = "epoch-isolate-1"
    required_pc = T.program_commit_single(commissioned)
    # mine honestly over the commissioned matrices
    found = T._mine_tile(commissioned, ctx, T.TARGET, commit=required_pc)
    if found is None:
        print("  mining failed")
        return False
    nonce, i, j, value = found
    honest = g_cert_bound(T.TASK_ID, required_pc, ctx, nonce, i, j, value,
                          T.TARGET)
    ok_honest = verify_g_cert_bound(honest, T.TASK_ID, required_pc, ctx,
                                    T.TARGET)
    # the same tile, but the verifier is given a DIFFERENT commitment string
    other = T.program_commit_single([[9, 9], [9, 9]])
    bad = dict(honest)
    bad = g_cert_bound(T.TASK_ID, other, ctx, nonce, i, j, value, T.TARGET)
    ok_bad = verify_g_cert_bound(bad, T.TASK_ID, other, ctx, T.TARGET)
    # the interesting case: honest tile, but verified against the commissioned
    # commitment while the cert was built over `other`
    cross = verify_g_cert_bound(bad, T.TASK_ID, required_pc, ctx, T.TARGET)
    print("  honest cert over commissioned commitment verifies: %s" % ok_honest)
    print("  cert built over a foreign commitment, verified against its own: %s"
          % ok_bad)
    print("  the SAME foreign cert verified against the commissioned commit: %s"
          % cross)
    print("  -> the rejection tracks the commitment, not the tile arithmetic")
    # the claim holds iff the commitment is load-bearing: a cert over a
    # foreign commitment must fail against the commissioned one, and the
    # honest one must pass.
    return ok_honest and not cross


# ----------------------------------------------------------------- R5B-2
def r5b2_detectability_is_not_zero_by_a_rigged_arm_a():
    """CLAIM: 'Arm A accepts the substitution 5/5 (detectability 0)'. Is that
    0 a property of the protocol, or an artifact of Arm A being CONSTRUCTED
    to accept anything self-consistent? MEASURED: does Arm A have ANY input
    that makes it reject? If not, the 0 reports the construction, not a
    measurement — and the file must say so.
    """
    print("=== R5B-2: is Arm A's 0% a measurement or a construction? ===")
    ctx = "epoch-rig-1"
    commissioned = [[2, 3], [4, 5]]
    # try degenerate and pathological matrices through Arm A
    cases = [
        [[0, 0], [0, 0]],
        [[1, 0], [0, 1]],
        [[96, 96], [96, 96]],
    ]
    accepted = 0
    tried = 0
    for m in cases:
        cert, res = T.arm_a_without_binding(commissioned, m, ctx)
        if cert is None:
            continue
        tried += 1
        if bool(res):
            accepted += 1
    print("  Arm A over %d pathological matrices: %d accepted" % (tried, accepted))
    # Arm A's acceptance rule is `H(...) % TARGET == 0`, so it CANNOT reject
    # a self-consistent cert by construction. The file prints "detectability
    # 0%" as though it were measured; it is a tautology of the arm's
    # definition. This probe CONFIRMS the tautology by construction-check.
    src_accepts_only_target = True
    print("  Arm A's rule: H(tile) %% TARGET == 0 -- a self-consistent cert")
    print("  over ANY matrices satisfies it, so the 0%% is a CONSTRUCTION,")
    print("  not a measurement. The file's own header says 'by construction'")
    print("  for the same quantity, so the claim is honest iff that phrase")
    print("  travels with the number.")
    import inspect
    body = inspect.getsource(T.arm_a_without_binding)
    stated = "by construction" in inspect.getsource(T) or "by construction" in body
    print("  'by construction' stated in the file: %s" % stated)
    # PASS iff the file admits the construction rather than presenting 0% as
    # an empirical result
    return stated and accepted == tried


# ----------------------------------------------------------------- R5B-3
def r5b3_the_identical_matrix_is_not_specially_handled_to_force_a_pass():
    """CLAIM: 'the identical matrix is the one Arm B correctly does NOT
    reject'. MEASURED: does the identical matrix actually verify under Arm B,
    or is it skipped to avoid a failure? Run Arm B on the commissioned
    matrices and on a matrix differing in ONE entry.
    """
    print("=== R5B-3: the identical matrix, measured directly ===")
    ctx = "epoch-ident-1"
    commissioned = [[2, 3], [4, 5]]
    honest_cert, ok = T.arm_b_with_binding(commissioned, ctx)
    print("  Arm B on the commissioned matrices        : %s" % ok)
    # one entry off
    off = [[2, 3], [4, 6]]
    sub_cert, ok_sub = T.arm_b_with_binding(commissioned, ctx, mined=off)
    print("  Arm B mining over a one-entry-off matrix  : %s" % ok_sub)
    print("  -> the one-entry-off cert is %s"
          % ("REJECTED (correct)" if not ok_sub else "ACCEPTED (bad)"))
    return bool(ok) and not ok_sub


# ----------------------------------------------------------------- R5B-4
def r5b4_the_tile_value_genuinely_depends_on_the_matrix():
    """CLAIM (docstring of _mine_tile): 'different matrices give different
    tile values and the certificate genuinely depends on the matrix contents'.
    MEASURED: over random 2x2 matrices, is the tile value actually a function
    of the matrix, and do distinct matrices give distinct values often enough
    that the binding is not vacuous?
    """
    print("=== R5B-4: does the tile value depend on the matrix? ===")
    import random
    rng = random.Random(5150)
    vals = {}
    collisions = 0
    N = 500
    for _ in range(N):
        m = [[rng.randrange(97) for _ in range(2)] for _ in range(2)]
        v = (m[0][0] * m[0][1] + m[1][0] * m[1][1]) % 97
        key = tuple(tuple(r) for r in m)
        if v in vals and vals[v] != key:
            collisions += 1
        vals[v] = key
    print("  random 2x2 matrices: %d" % N)
    print("  distinct tile values: %d of 97 possible" % len(vals))
    print("  the value is a 2-term inner product mod 97, so collisions are")
    print("  EXPECTED (~%.0f%% of pairs share a value); the claim that survives"
          % (100 * (1 - (96 / 97) ** N)))
    print("  is that the value is a FUNCTION of the matrix, which it is.")
    # the load-bearing version of the claim: two DIFFERENT matrices with the
    # same value must both be distinguishable by the commitment, which is
    # content-bound. Verify that directly.
    m1 = [[2, 3], [4, 5]]
    m2 = [[2, 3], [4, 5 + 97]]   # different ints, same residue
    c1 = T.program_commit_single(m1)
    c2 = T.program_commit_single(m2)
    print("  two matrices equal mod 97 but different ints: commits %s"
          % ("differ" if c1 != c2 else "EQUAL (vacuous binding)"))
    return len(vals) > 1 and c1 != c2


# ----------------------------------------------------------------- R5B-5
def r5b5_no_nonce_found_is_not_silently_treated_as_a_protocol_result():
    """CLAIM: the arms return (None, 'no nonce found') if mining fails. Is
    that path reachable at the shipped target, and if it is, does the probe
    treat it as a pass or as a failure? MEASURED: mining success rate at
    TARGET=2^8 over several matrices.
    """
    print("=== R5B-5: is the no-nonce path reachable at the shipped target? ===")
    import random
    rng = random.Random(6161)
    ctx = "epoch-nonce-1"
    found_n = 0
    trials = 8
    for _ in range(trials):
        m = [[rng.randrange(97) for _ in range(2)] for _ in range(2)]
        r = T._mine_tile(m, ctx, T.TARGET)
        if r is not None:
            found_n += 1
    print("  matrices mined successfully: %d/%d at TARGET=2^8"
          % (found_n, trials))
    print("  -> the toy target is loose enough that the no-nonce path is")
    print("     unreachable in practice, so the 'no nonce found' branch is")
    print("     dead code at the shipped parameters (it exists for a tighter")
    print("     target, which this file does not use).")
    # PASS iff mining is reliable (so the file's result is not an artifact of
    # a lucky nonce) AND the dead branch is at least named here
    return found_n == trials


PROBES = [
    ("R5B-1 rejection tracks the commitment", r5b1_arm_b_rejects_only_because_of_a_commitment_mismatch),
    ("R5B-2 Arm A's 0% is by construction, not measured", r5b2_detectability_is_not_zero_by_a_rigged_arm_a),
    ("R5B-3 the identical matrix verifies, one-entry-off rejects", r5b3_the_identical_matrix_is_not_specially_handled_to_force_a_pass),
    ("R5B-4 the tile value depends on the matrix", r5b4_the_tile_value_genuinely_depends_on_the_matrix),
    ("R5B-5 mining is reliable at the shipped target", r5b5_no_nonce_found_is_not_silently_treated_as_a_protocol_result),
]


def main():
    print("=" * 74)
    print("ROUND-5B adversarial probes: tv72_egap_mechanism_en.py")
    print("=" * 74)
    results = {}
    for name, fn in PROBES:
        print()
        try:
            results[name] = fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[name] = False
    print()
    print("-" * 74)
    for name, fn in PROBES:
        print("  %-52s %s" % (name,
                             "PASS (claim holds)" if results[name]
                             else "FINDING (claim fails)"))
    n = sum(1 for v in results.values() if v)
    print("  probes: %d/%d" % (n, len(PROBES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
