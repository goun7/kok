#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - FP8 QUANTIZATION-AWARE NOISE MODEL PROTOTYPE (TV-27..TV-30)
====================================================================
This prototype opens the FP8 direction of KNOWN GAP #2: TV-21 always gave
RED in the INT toy; can the direction REVERSE in FP8?

MECHANISM (derived from Pearl FP8 wp SS5.1.2 + SS5.1):
  In the INT toy (TV-21) noise std = DELTA * RMS(row). As the peak v grows,
  RMS ~ v grows too, so the noise/g ratio stays constant (~0.707) - the toy
  always gives RED.

  In FP8, quantization imposes an ABSOLUTE grid. If the attacker shrinks the
  row magnitudes (c -> 0), the INT-model noise shrinks TOO (DELTA*RMS ~ c),
  and at some point the noise becomes SMALLER than the FP8 quantum. Then the
  output tiles get PINNED to a few quantized values = the "reduced-alphabet
  hardware advantage" (special circuits faster than a general FP8 kernel).
  Since tickets hash the output tiles directly (NO transcript), this attacks
  the jackpot directly.

  Pearl's defense: (1) a noise floor sigma_min (ABSOLUTE, independent of
  magnitude) + (2) entry liveness (tau_idle, epsilon_idle).

TESTS:
- TV-27: FP8 subnormal compression - entries below subnormal flush to 0
- TV-28: NEGATIVE RESULT - WITHOUT a noise floor the low-entropy attack
  SUCCEEDS in FP8 (output tiles pinned to 1-2 bins). The REVERSE of the INT
  toy. Recorded honestly: a noise floor is MANDATORY for FP8 in KOK v2.
- TV-29: with the noise floor (sigma_min, ABSOLUTE) added, the attack closes
- TV-30: entry liveness grinding - NEGATIVE RESULT: DELTA=0.5 (the TV-12
  constant) does NOT satisfy Pearl SS5.1 (tau_idle=8, epsilon_idle=1/64).
  An upper bound on DELTA is derived (spec correction).

IMPORTANT LIMITS (honest):
- Simplified FP8 (RNE + subnormal flush); NOT IEEE-754. Real hardware
  differs with RNE/RZ + tensor-core accumulation. This is why Hawkeye
  bit-exact replay (Badash et al.) is MANDATORY: the verifier MUST
  reproduce the same hardware.
- r=2 toy rank (Pearl recommends r=32 for k<=2^16) - NOT an asymptotic proof.
- Q(A+N) nonlinearity is modeled as a single add-then-quantize; in a real
  MatMul it repeats at every MAC step.
- The attack is measured on output tiles; a real tile has size n/r.
"""

import random
import math
from collections import Counter

# ============================================================
# FP8 MODEL (simplified)
# ============================================================
FP8_FORMATS = {
    "E4M3": {"emax": 448.0, "subnormal_min": 2.0**-9, "mant_bits": 3, "levels": 256},
    "E5M2": {"emax": 57344.0, "subnormal_min": 2.0**-16, "mant_bits": 2, "levels": 256},
}


def fp8_quantize(x, fmt="E4M3"):
    """RNE + subnormal flush. Below subnormal -> 0 (FP8 nonlinearity)."""
    f = FP8_FORMATS[fmt]
    if abs(x) < f["subnormal_min"]:
        return 0.0
    if x == 0:
        return 0.0
    s = math.copysign(1.0, x)
    mag = abs(x)
    if mag > f["emax"]:
        return s * f["emax"]
    exp = math.floor(math.log2(mag))
    frac = mag / (2.0**exp) - 1.0
    lv = 2**f["mant_bits"]
    m = round(frac * lv)
    if m >= lv:
        exp += 1
        m = 0
    return s * 2.0**exp * (1.0 + m / lv)


def quantize_vec(vals, fmt="E4M3"):
    return [fp8_quantize(v, fmt) for v in vals]


def entropy_bits(vals):
    cnt = Counter(vals)
    n = len(vals)
    return -sum((c / n) * math.log2(c / n) for c in cnt.values())


# ============================================================
# NOISE MODELS
# ============================================================
DELTA = 0.5  # same constant as TV-12 (TV-30 questions it)


def noise_int_model(row, delta=DELTA):
    """"INT toy: sigma = DELTA * RMS(row). PROPORTIONAL to magnitude (weak in FP8)."""""
    rms = math.sqrt(sum(v * v for v in row) / len(row))
    return [delta * rms] * len(row)


def noise_fp8_aware(row, sigma_min, fmt="E4M3"):
    """
    FP8-aware: INT the model + ABSOLUTE sigma_min floor.

    Pearl SS5 noise floor: every entry must CARRY at least
    sigma_min * subnormal_min of noise. This is independent of magnitude -
    even if the attacker shrinks the magnitude, the noise cannot fall
    below the quantum.
    """
    rms = math.sqrt(sum(v * v for v in row) / len(row))
    base = DELTA * rms
    floor = sigma_min * FP8_FORMATS[fmt]["subnormal_min"]
    return [max(base, floor)] * len(row)


# ============================================================
# OUTPUT-TILE ATTACK (correct model: the attack is at the output)
# ============================================================
def attack_rows(rng, n, k, c, jitter):
    """
    The attacker's matrix: all n rows are VERY CLOSE to the same base
    vector (differ by jitter), magnitude c. The output tiles (A@ones)
    therefore collapse into the same bin. Noise must separate them.
    """
    base = [rng.uniform(-c, c) for _ in range(k)]
    return [[v + rng.uniform(-jitter, jitter) for v in base] for _ in range(n)]


def output_tiles(A, B):
    """Toy MatMul: C[i] = sum_j A[i][j]*B[j]. A real tile has size n/r."""
    return [sum(a * b for a, b in zip(row, B)) for row in A]


# ============================================================
# TESTS
# ============================================================
def tv27_subnormal_compression():
    """TV-27: FP8 entries below subnormal flush to 0 (nonlinearity)."""
    rng = random.Random(2701)
    n, k = 8, 32
    A = [[rng.uniform(-0.0005, 0.0005) for _ in range(k)] for _ in range(n)]
    Q = [quantize_vec(row, "E4M3") for row in A]
    z = sum(1 for row in Q for x in row if x == 0.0)
    frac = z / (n * k)
    assert frac > 0.5, f"TV-27: subnormal compression was not expected: {frac:.2f}"
    return "PASS", f"{frac*100:.0f}% of E4M3 subnormal (<2^-9) entries flushed to 0 (FP8 nonlinear)"


def tv28_low_entropy_attack_succeeds():
    """
    TV-28: NEGATIVE RESULT - WITHOUT a noise floor the attack SUCCEEDS in FP8.

    The attacker uses small-magnitude, near-identical rows.
    INT-model noise = DELTA*RMS shrinks with magnitude; when the output noise
    falls below the FP8 quantum the tiles pin to 1-2 bins = low entropy.
    Since the ticket is a tile hash, this is a jackpot attack.

    The INT toy (TV-21) always gave RED - in FP8 the direction REVERSES.
    """
    rng = random.Random(2801)
    n, k, c, jitter = 16, 32, 1e-4, 1e-6
    B = [rng.uniform(-1, 1) for _ in range(k)]
    A = attack_rows(rng, n, k, c, jitter)
    # the honest miner's INT model adds noise (NO noise floor)
    noisy = []
    for row in A:
        sig = noise_int_model(row)
        noisy.append([v + rng.gauss(0, s) for v, s in zip(row, sig)])
    tiles = output_tiles(noisy, B)
    Qtiles = quantize_vec(tiles, "E4M3")
    uniq = len(set(Qtiles))
    # attack succeeded: the output tiles take fewer than 2 distinct values (they were pinned)
    attack_succeeds = uniq <= 2
    if not attack_succeeds:
        return "SKIP", f"{uniq} distinct values; the attack did not materialize at these parameters"
    return "FAIL-FOR-KOK", (f"NEGATIVE: output tiles pinned to {uniq} value(s) "
                            f"(entropy {entropy_bits(Qtiles):.2f} bit) - attack SUCCEEDS, "
                            f"noise floor MANDATORY")


def tv29_noise_floor_closes_attack():
    """TV-29: the ABSOLUTE noise floor (sigma_min) closes the attack."""
    rng = random.Random(2901)
    n, k, c, jitter = 16, 32, 0.001, 1e-5
    B = [rng.uniform(-1, 1) for _ in range(k)]
    A = attack_rows(rng, n, k, c, jitter)
    # WITH the noise floor (sigma_min = 8 quantized units, Pearl SS5)
    noisy = []
    for row in A:
        sig = noise_fp8_aware(row, sigma_min=8.0)
        noisy.append([v + rng.gauss(0, s) for v, s in zip(row, sig)])
    tiles = output_tiles(noisy, B)
    Qtiles = quantize_vec(tiles, "E4M3")
    uniq = len(set(Qtiles))
    # with the floor, the output tiles must spread (>=8 distinct values)
    assert uniq >= 8, f"TV-29: noise floor ile hala low entropy: {uniq} deger"
    return "PASS", f"with the noise floor (8 units), {uniq} distinct output values - attack closed"


def tv30_entry_liveness_grinding():
    """
    TV-30: NEGATIVE RESULT x2 - entry liveness grinding tests DELTA.

    Pearl SS5.1: tau_idle=8, epsilon_idle=1/64. An entry is "idle/dwarfed"
    if |entry| < noise/tau_idle. The attacker grinds seeds to push this
    fraction below epsilon_idle.

    DEEPER FINDING (honest): average-case analysis gives the WRONG bound.
      - DELTA=0.5 (the TV-12 constant): ~5.5% dwarfed -> EXCEEDS
      - The analytic average-case bound DELTA <= sqrt(3)*tau*eps = 0.217:
        still ~3.7% and EXCEEDS - because grinding selects the FLUCTUATION
        TAIL of RMS (worst-case RMS > average RMS).
      - The REAL grinding-resistant bound (500-seed worst case): DELTA <= 0.06.

    Conclusion: DELTA must be lowered from 0.5 to 0.06 in the toy. This is a
    spec correction, and it shows average-case bounds are NOT sufficient for
    grinding-resistant parameters.
    """
    n, k, c = 8, 64, 1.0
    TAU_IDLE = 8.0
    EPSILON_IDLE = 1.0 / 64.0

    def dwarfed_worst(delta, trials=500):
        r = random.Random(4242)
        worst = 0.0
        for _ in range(trials):
            A = [[r.uniform(-c, c) for _ in range(k)] for _ in range(n)]
            rms = math.sqrt(sum(v * v for v in A[0]) / k)
            thr = delta * rms / TAU_IDLE
            d = sum(1 for row in A for v in row if abs(v) < thr)
            worst = max(worst, d / (n * k))
        return worst

    f05 = dwarfed_worst(0.5)
    analytic = math.sqrt(3) * TAU_IDLE * EPSILON_IDLE  # average-case bound
    f_analytic = dwarfed_worst(analytic)
    f_safe = dwarfed_worst(0.06)
    ok = f_safe < EPSILON_IDLE
    note = (f"DELTA=0.5 -> {f05*100:.2f}%; analytic bound {analytic:.3f} -> "
            f"{f_analytic*100:.2f}% (still EXCEEDS!); real bound DELTA<=0.06 -> "
            f"{f_safe*100:.2f}% ({'PASSES' if ok else 'EXCEEDS'}) - "
            f"AVERAGE-CASE ANALYSIS IS INSUFFICIENT")
    return ("PASS" if ok else "FAIL-FOR-KOK"), note


# ============================================================
def main():
    print("=" * 72)
    print("KOK v2 - FP8 QUANTIZATION-AWARE NOISE MODEL (TV-27..TV-30)")
    print("=" * 72)
    print("  FP8: E4M3 (subnormal min 2^-9), E5M2 (2^-16)")
    print("  INT noise: DELTA*RMS(row) | FP8-aware: + sigma_min floor (ABSOLUTE)")
    print()
    tests = [tv27_subnormal_compression, tv28_low_entropy_attack_succeeds,
             tv29_noise_floor_closes_attack, tv30_entry_liveness_grinding]
    allpass = True
    for t in tests:
        try:
            res, note = t()
            mark = "  " if res == "PASS" else "!!"
            print(f"{mark} {t.__name__:40} {res}")
            print(f"     {note}")
            if res != "PASS":
                allpass = False
        except AssertionError as e:
            print(f"!! {t.__name__:40} FAIL: {e}")
            allpass = False
    print()
    print("  TOY LIMITS (honest):")
    print("    - Simplified FP8 (RNE + subnormal flush); NOT IEEE-754.")
    print("      Real hardware differs with RNE/RZ + tensor-core accumulation.")
    print("      This is why Hawkeye bit-exact replay is MANDATORY (Badash et al.).")
    print("    - r=2 toy rank (Pearl: r=32 for k<=2^16); NOT an asymptotic proof.")
    print("    - Q(A+N) nonlinearity is a single add-then-quantize; in a real MatMul")
    print("      it repeats at every MAC step.")
    print("    - Attack measured on output tiles; a real tile has size n/r.")
    print()
    print("  RESULT:", "ALL PASSED" if allpass else "NEGATIVE RESULTS FOUND (above) - spec must be updated")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
