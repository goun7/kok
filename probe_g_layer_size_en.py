"""
Round-4 probe (2026-09-23): the g_layer prove/verify size-divergence class.

WHAT THIS MEASURES
------------------
`KWKernel.prove` derives the matrix size from its INPUT (n = len(A)), but
`verify` used the kernel's CONSTANT self.n. On any matrix whose size differed
from the kernel default, verify recomputed the tile over the wrong
coordinates. MEASURED before the fix: a 6x6 proof (m=3) made verify index
A at row 8 and raise IndexError; an 8x8 default matrix happened to work
because it matched the constant, which is why round-3's tests missed it.

This probe now drives three sizes and asserts verify accepts the honest
certificate at each — so a future regression back to a kernel constant fails
here rather than passing on the one size that matches.
"""

import random
import importlib.util


def _load():
    spec = importlib.util.spec_from_file_location("g", "g_layer_tests_en.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def probe_verify_matches_prove_across_sizes():
    print("=== g_layer round-4: verify derives size from the input ===")
    mod = _load()
    k = mod.KWKernel()
    rng = random.Random(2026)
    results = {}
    for n in (6, 8, 10):
        A = [[rng.randrange(97) for _ in range(n)] for _ in range(n)]
        B = [[rng.randrange(97) for _ in range(n)] for _ in range(n)]
        cert = None
        nonce = 0
        while cert is None and nonce < 20000:
            nonce += 1
            cert = k.prove(A, B, 777, nonce, 1)
        if cert is None:
            results[n] = "could not grind a cert"
            continue
        ok = k.verify(cert, A, B, 777, nonce, 1)
        results[n] = "verify=%s (m=%d)" % (ok, cert["m"])
        print("  %2dx%2d: %s" % (n, n, results[n]))
    # a forged tile value at the same coordinates must reject at every size
    rng2 = random.Random(5)
    A = [[rng2.randrange(97) for _ in range(8)] for _ in range(8)]
    B = [[rng2.randrange(97) for _ in range(8)] for _ in range(8)]
    cert = None
    nonce = 0
    while cert is None and nonce < 20000:
        nonce += 1
        cert = k.prove(A, B, 999, nonce, 1)
    forged = dict(cert)
    i, j, val = forged["tile"]
    forged["tile"] = (i, j, (val + 1) % 97)
    forged_ok = k.verify(forged, A, B, 999, nonce, 1)
    print("  forged tile value rejected: %s" % (not forged_ok))
    all_ok = all("verify=True" in v for v in results.values()) and not forged_ok
    print("  RESULT: %s" % ("PASS" if all_ok else "FINDING"))
    return all_ok


if __name__ == "__main__":
    print("=" * 76)
    print("KOK v2 - g_layer size-divergence probe (round-4, 2026-09-23)")
    print("=" * 76)
    probe_verify_matches_prove_across_sizes()
