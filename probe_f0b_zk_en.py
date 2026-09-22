#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KOK v2 — F0b zero-knowledge adversarial probe (TV-65).

THE FINDING: TV-43 is not zero-knowledge, and the proof is one line of code.

The file's docstring for tv43 says "the real trace values are never transmitted".
That is true as a statement about the bytes on the wire. It is false as a
statement about what the VERIFIER learns, because verify_zk reconstructs the
secret values in the clear:

    real_diff = (lhs - ddiff) % q
    real_a    = (ma - H("mask", seed, x + 1)) % q
    real_b    = (mb - H("mask", seed, x + 2)) % q

The mask d(t) = H("mask", seed, t) is a deterministic function of a seed the
VERIFIER supplied, so the verifier recomputes d from the seed it already knows
and subtracts it. Every masked value it receives becomes the plaintext. The
"mask" hides the trace from nobody. This is not a weak one-time pad; a one-time
pad whose key is handed to the reader is not a pad at all.

Why this matters beyond the file: the paper's reason (b) — that a buyer can
prove a result without revealing model weights or sensitive data — rests on F0b
delivering zero-knowledge. The paper already says F0b is "a promise rather than
a proof" and lists "one-time-pad hiding rather than Schwartz-Zippel" as the
remaining gap. That framing is now too generous: the gap is not that the hiding
is non-standard, it is that the construction as written does not hide.

This probe does not fix the construction — a real masking scheme (a blinding
factor the verifier cannot recompute, or Schwartz-Zippel over a random
evaluation point) is design work that belongs to F0b proper. It converts the
claim into a measured, reproducing fact, so the paper cannot continue to
describe this file as demonstrating zero-knowledge at toy scale.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
from f0b_air_proto import ZkTileAIR, H


def tv65_zero_knowledge_is_absent():
    """The verifier recovers the secret trace values from the seed it already has.

    Construct an honest proof, mask it, strip the mask d as the protocol does,
    then act as a malicious verifier: recompute d from the seed and unmask.
    If the recovered values match the real witness, zero-knowledge is absent.
    """
    rnd = random.Random(7)
    q, r, n = 97, 2, 8
    A = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[rnd.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx = 555
    E = [[H("E", ctx, a, b) % q for b in range(n)] for a in range(n)]
    F = [[H("F", ctx, a, b) % q for b in range(n)] for a in range(n)]
    i, j = 1, 1
    m = n // r
    acc = 0
    for l in range(m):
        acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
               (B[l * r][j * r] + F[l * r][j * r])) % q

    air = ZkTileAIR(q, r)
    honest = air.prove(A, B, E, F, ctx, i, j, acc)
    seed = 12345
    masked = air.mask(honest, seed)
    masked["seed"] = seed
    transmitted = {k: v for k, v in masked.items() if k != "d"}

    # a malicious verifier knows the seed and the transmitted values only.
    # it recomputes the mask and unmask everything it was sent.
    recovered_trace = [(transmitted["trace"][t]
                        - H("mask", seed, t) % q) % q
                       for t in range(len(transmitted["trace"]))]
    recovered_a = [(transmitted["a"][t]
                    - H("mask", seed, t + 1) % q) % q
                   for t in range(len(transmitted["a"]))]
    recovered_b = [(transmitted["b"][t]
                    - H("mask", seed, t + 2) % q) % q
                   for t in range(len(transmitted["b"]))]

    leaked = (recovered_trace == honest["trace"]
              and recovered_a == honest["a"]
              and recovered_b == honest["b"])
    # the honest proof must still verify (this is a privacy leak, not a
    # correctness break): soundness is intact, zero-knowledge is not
    ok_acc = air.verify_zk(transmitted, acc, list(range(m)))
    return (leaked and ok_acc), leaked, ok_acc


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F0b zero-knowledge probe (TV-65)")
    print("=" * 76)
    print()
    ok, leaked, sound = tv65_zero_knowledge_is_absent()
    print("  verifier recovers the full secret witness from its own seed: %s"
          % ("YES — zero-knowledge is ABSENT" if leaked else "no"))
    print("  the honest masked proof still verifies (soundness intact): %s"
          % ("YES" if sound else "no"))
    print()
    # the probe PASSES when the leak is demonstrated: the finding is the result,
    # not a failure to fix. It would FAIL if the mask ever became secret, which
    # is exactly the fix this file needs.
    ok = leaked and sound
    print("  probe status: %s" % ("ACCEPT (leak reproduced)" if ok else "RED"))
    if not ok:
        raise SystemExit(1)
    print()
    print("  CONSEQUENCE FOR THE PAPER: this file demonstrates a working AIR,")
    print("  a working commitment and a working low-degree check — but it does")
    print("  NOT demonstrate zero-knowledge, even at toy scale. The paper's")
    print("  reason (b) (prove a result without revealing the inputs) has no")
    print("  prototype support until the mask is made verifier-unknowable.")
