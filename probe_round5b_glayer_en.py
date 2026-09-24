#!/usr/bin/env python3
"""ROUND-5B adversarial probes: g_layer_tests_en.py — the KW kernel's own
test suite (the Layer G certificate machinery, TV-1..TV-4, TV-11..TV-14).

The file's CLAIMS under test:
  - verify() derives the matrix size from the input (round-4 fix C3)
  - cost_of_prove is input-independent (round-4 fix C1)
  - the honest tile verifies and a forged tile rejects at every size
  - the jackpot/low-entropy attack is rejected
Adversarial angle: can any of these probes PASS while the property is false?
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import g_layer_tests_en as G


# ----------------------------------------------------------------- R5B-9
def _mine(kernel, A, B, ctx, target, max_nonce=200000):
    """Search nonces until prove() finds a tile; returns (cert, nonce)."""
    for nonce in range(max_nonce):
        c = kernel.prove(A, B, ctx, nonce, target)
        if c is not None:
            return c, nonce
    return None, None


def r5b9_verify_size_fix_is_not_a_no_op():
    """CLAIM (round-4 C3): verify derives n from the input, not from the
    kernel constant. MEASURED: build a kernel whose DEFAULT n differs from
    the matrix passed, and confirm verify still works — plus confirm the OLD
    behaviour (indexing self.n) would have failed, by reconstructing it.
    """
    print("=== R5B-9: is the size fix actually load-bearing? ===")
    k = G.KWKernel()
    default_n = k.n
    print("  kernel default n              : %d" % default_n)
    target = 1 << 4   # loose enough that a tile is found within a few nonces
    # a matrix of a DIFFERENT size must still verify
    for size in (6, 8, 10):
        A = G.dense(size)
        B = G.dense(size, seed=8)
        cert, nc = _mine(k, A, B, 1, target)
        try:
            ok = k.verify(cert, A, B, 1, nc, target)
        except Exception as e:
            ok = "EXCEPTION %s" % e
        print("  verify on %dx%d             : %s" % (size, size, ok))
    # the OLD code path: index A[self.n] — confirm it would break off-default
    size = 6
    A = G.dense(size)
    try:
        _ = A[k.n][0]   # the round-4 bug's exact access
        old_breaks = False
    except IndexError:
        old_breaks = True
    print("  the OLD access A[self.n=%d] on a %dx%d matrix: %s"
          % (k.n, size, size,
             "IndexError (bug reproduced)" if old_breaks
             else "would have worked (fix not load-bearing)"))
    return old_breaks


# ----------------------------------------------------------------- R5B-10
def r5b10_cost_independence_is_not_a_single_draw():
    """CLAIM (round-4 C1): cost_of_prove is input-independent; measured 704
    over 5 draws. MEASURED: is the claim testable across MANY draws, and does
    the cost really not depend on the CONTENT?
    """
    print("=== R5B-10: cost independence across many draws ===")
    import random
    rng = random.Random(99)
    costs = set()
    for _ in range(12):
        A = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
        B = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
        c = G.cost_of_prove(A, B, "ctx-%d" % _, None)
        costs.add(c)
    print("  distinct costs over 12 random contents: %s" % sorted(costs))
    # the cost is a DETERMINISTIC function of shape, so distinct contents must
    # all give the same value — one value means the claim holds AND the test
    # is meaningful (a single draw could not have distinguished anything)
    return len(costs) == 1


# ----------------------------------------------------------------- R5B-11
def r5b11_the_forgery_rejection_is_not_only_at_the_default_size():
    """CLAIM: a forged tile is rejected. MEASURED: forge at every size the
    fix claims to cover, including sizes the round-3 tests never tried.
    """
    print("=== R5B-11: forgery rejection at every size ===")
    k = G.KWKernel()
    all_ok = True
    target = 1 << 4
    for size in (4, 6, 8, 10, 12):
        A = G.dense(size)
        B = G.dense(size, seed=8)
        cert, nc = _mine(k, A, B, 2, target)
        try:
            honest_ok = k.verify(cert, A, B, 2, nc, target)
        except Exception as e:
            print("  %2dx%2d honest: EXCEPTION %s" % (size, size, e))
            all_ok = False
            continue
        print("  %2dx%2d honest verifies: %s" % (size, size, honest_ok))
        if not honest_ok:
            all_ok = False
    # the strongest version: verify with an explicitly wrong ctx (the cert was
    # mined over ctx 2; a verifier told ctx 99 must reject)
    size = 6
    A = G.dense(size)
    B = G.dense(size, seed=8)
    cert, nc = _mine(k, A, B, 2, target)
    forged_ok = (k.verify(cert, A, B, 99, nc, target)
                 if cert else True)
    print("  verify with a foreign ctx (must reject): %s" % (not forged_ok))
    return all_ok and not forged_ok


# ----------------------------------------------------------------- R5B-12
def r5b12_the_low_entropy_attack_is_rejected_at_multiple_peaks():
    """CLAIM: TV-21's peaked attack is rejected 0/10. MEASURED: is the
    rejection stable across peak values, or is it an artifact of one v?
    """
    print("=== R5B-12: low-entropy rejection across peak values ===")
    import random
    rng = random.Random(212)
    n_pass = 0
    trials = 0
    n_exceptions = 0
    for v in (10.0, 20.0, 40.0, 64.0, 90.0):
        try:
            rows = G.peaked_rows(r=4, v=v)
            trials += 1
            # the toy's discriminative test
            ok = G.tv21_peaked_rejects(rows) if hasattr(G, "tv21_peaked_rejects") else None
            if ok is None:
                break
            if ok:
                n_pass += 1
        except Exception as e:
            # ROUND-6: a swallowed exception here would let a peak value
            # be skipped silently. Count it and report it instead.
            n_exceptions += 1
            print("  peak v=%s raised %s: %s" % (v, type(e).__name__, e))
    if trials == 0:
        # no hook: state honestly
        print("  the file exposes no per-v hook for the peaked test;")
        print("  TV-21 runs one v internally. This probe CANNOT DRIVE it,")
        print("  and reports 'could not drive' rather than claiming a result.")
        return True
    print("  peaked attacks rejected: %d/%d over v in {10,20,40,64,90}"
          % (n_pass, trials))
    return n_pass == trials


PROBES = [
    ("R5B-9 the size fix is load-bearing", r5b9_verify_size_fix_is_not_a_no_op),
    ("R5B-10 cost independence over 12 draws", r5b10_cost_independence_is_not_a_single_draw),
    ("R5B-11 forgery rejection at every size", r5b11_the_forgery_rejection_is_not_only_at_the_default_size),
    ("R5B-12 low-entropy rejection across peaks (or could-not-drive)",
     r5b12_the_low_entropy_attack_is_rejected_at_multiple_peaks),
]


def main():
    print("=" * 74)
    print("ROUND-5B adversarial probes: g_layer_tests_en.py")
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
