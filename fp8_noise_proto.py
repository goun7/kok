#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - FP8 QUANTIZATION-AWARE NOISE MODEL PROTOTYPE (TV-27..TV-30)
====================================================================
Bu prototip KNOWN GAP #2'nin FP8 yonunu acar: TV-21 INT toy'da her zaman
RED vermisti; FP8'de yon TERSINE donebilir mi?

MEKANIZMA (Pearl FP8 wp SS5.1.2 + SS5.1'den cikarildi):
  INT toy'da (TV-21) noise std = DELTA * RMS(row). Peak v artinca RMS ~ v
  de buyur, noise/g orani sabit kalir (~0.707) - toy her zaman RED verir.

  FP8'de quantization bir ABSOLUTE grid koyar. Saldirgan satir magnitude'lerini
  kuculturse (c -> 0), INT-model noise'i DA kuculur (DELTA*RMS ~ c), ve bir
  noktada noise FP8 quantum'undan KUCUK olur. O zaman cikis tile'lari az
  sayida quantized degere SABITLENIR = "reduced-alphabet hardware advantage"
  (ozel devre genel FP8 kernel'inden hizli). Ticket'lar cikti tile'larini
  hashledigi icin (transcript YOK) bu dogrudan jackpot'a saldirir.

  Pearl'in savunmasi: (1) noise floor sigma_min (ABSOLUTE, magnitude'dan
  bagimsiz) + (2) entry liveness (tau_idle, epsilon_idle).

TESTLER:
- TV-27: FP8 subnormal compression - subnormal alti entry'ler 0'a flush olur
- TV-28: NEGATIF SONUC - noise floor OLMADAN low-entropy saldirisi FP8'de
  BASARILI (cikis tile'lari 1-2 bin'e sikisir). INT toy'un TERSI. Dürust
  kaydedilir: KOK v2 FP8 icin noise floor ZORUNLUDUR.
- TV-29: noise floor (sigma_min, ABSOLUTE) eklendiginde saldiri kapanir
- TV-30: entry liveness grinding - NEGATIF SONUC: DELTA=0.5 (TV-12 sabiti)
  Pearl SS5.1'e (tau_idle=8, epsilon_idle=1/64) UYMUYOR. DELTA icin
  ust sinir hesaplanir (spec duzeltmesi).

ONEMLI SINIR (dürüst):
- Sadelestirilmis FP8 (RNE + subnormal flush); IEEE-754 DEGIL. Gercek
  donanim RNE/RZ + tensor-core accumulation ile farklidir. Hawkeye
  bit-exact replay (Badash et al.) bu yuzden ZORUNLU: dogrulayici ayni
  donanimi reproduce etmek ZORUNDADIR.
- r=2 toy rank (Pearl k<=2^16 icin r=32) - asimptotik KANIT degil.
- Q(A+N) nonlineerligi tek add-then-quantize; gercek MatMul'da her MAC
  adiminda tekrarlanir.
- Saldiri cikis tile'larinda olcuktur; gercek tile n/r boyutundadir.
"""

import random
import math
from collections import Counter

# ============================================================
# FP8 MODEL (sadelestirilmis)
# ============================================================
FP8_FORMATS = {
    "E4M3": {"emax": 448.0, "subnormal_min": 2.0**-9, "mant_bits": 3, "levels": 256},
    "E5M2": {"emax": 57344.0, "subnormal_min": 2.0**-16, "mant_bits": 2, "levels": 256},
}


def fp8_quantize(x, fmt="E4M3"):
    """RNE + subnormal flush. Subnormal alti -> 0 (FP8 nonlineerligi)."""
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
DELTA = 0.5  # TV-12'den ayni sabit (TV-30 bunu sorgular)


def noise_int_model(row, delta=DELTA):
    """INT toy: sigma = DELTA * RMS(row). Magnitude ile ORANTILI (FP8'de zayif)."""
    rms = math.sqrt(sum(v * v for v in row) / len(row))
    return [delta * rms] * len(row)


def noise_fp8_aware(row, sigma_min, fmt="E4M3"):
    """
    FP8-aware: INT modeli + ABSOLUTE sigma_min floor.

    Pearl SS5 noise floor: her entry en az sigma_min * subnormal_min
    gurultu TASIMALIDIR. Bu magnitude'dan bagimsizdir - saldirgan
    magnitude'i kucultse de noise quantum'un altina DUSEMEZ.
    """
    rms = math.sqrt(sum(v * v for v in row) / len(row))
    base = DELTA * rms
    floor = sigma_min * FP8_FORMATS[fmt]["subnormal_min"]
    return [max(base, floor)] * len(row)


# ============================================================
# OUTPUT-TILE ATTACK (dogru model: saldiri cikista)
# ============================================================
def attack_rows(rng, n, k, c, jitter):
    """
    Saldirganin matrisi: n satir da ayni temel vektore COK YAKIN
    (jitter kadar fark), magnitude c. Cikis tile'lari (A@ones) bu
    yuzden ayni bin'e sikisir. Noise onlari ayirmali.
    """
    base = [rng.uniform(-c, c) for _ in range(k)]
    return [[v + rng.uniform(-jitter, jitter) for v in base] for _ in range(n)]


def output_tiles(A, B):
    """Toy MatMul: C[i] = sum_j A[i][j]*B[j]. Gercek tile n/r boyutundadir."""
    return [sum(a * b for a, b in zip(row, B)) for row in A]


# ============================================================
# TESTS
# ============================================================
def tv27_subnormal_compression():
    """TV-27: FP8 subnormal alti entry'ler 0'a flush olur (nonlineerlik)."""
    rng = random.Random(2701)
    n, k = 8, 32
    A = [[rng.uniform(-0.0005, 0.0005) for _ in range(k)] for _ in range(n)]
    Q = [quantize_vec(row, "E4M3") for row in A]
    z = sum(1 for row in Q for x in row if x == 0.0)
    frac = z / (n * k)
    assert frac > 0.5, f"TV-27: subnormal compression beklenmedi: {frac:.2f}"
    return "PASS", f"E4M3 subnormal (<2^-9) entry'lerin %{frac*100:.0f}i 0'a flush (FP8 nonlineer)"


def tv28_low_entropy_attack_succeeds():
    """
    TV-28: NEGATIF SONUC - noise floor OLMADAN FP8'de saldiri BASARILI.

    Saldirgan kucuk-magnitude, birbirine cok yakin satirlar kullanir.
    INT-model noise = DELTA*RMS magnitude ile kuculur; cikis noise'i FP8
    quantum'una dustugunde tile'lar 1-2 bin'e sikisir = low entropy.
    Ticket tile hash'i oldugu icin bu jackpot saldirisidir.

    INT toy (TV-21) her zaman RED vermisti - FP8'de yon TERSINE.
    """
    rng = random.Random(2801)
    n, k, c, jitter = 16, 32, 1e-4, 1e-6
    B = [rng.uniform(-1, 1) for _ in range(k)]
    A = attack_rows(rng, n, k, c, jitter)
    # honest miner INT modeli noise ekler (noise floor YOK)
    noisy = []
    for row in A:
        sig = noise_int_model(row)
        noisy.append([v + rng.gauss(0, s) for v, s in zip(row, sig)])
    tiles = output_tiles(noisy, B)
    Qtiles = quantize_vec(tiles, "E4M3")
    uniq = len(set(Qtiles))
    # saldiri basarili: cikis tile'lari 2'den az farkli deger (sabitlendiler)
    attack_succeeds = uniq <= 2
    if not attack_succeeds:
        return "SKIP", f"{uniq} farkli deger; saldiri bu parametrede olusmadi"
    return "FAIL-FOR-KOK", (f"NEGATIF: cikis tile'lari {uniq} degere sabitlendi "
                            f"(entropy {entropy_bits(Qtiles):.2f} bit) - saldiri BASARILI, "
                            f"noise floor ZORUNLU")


def tv29_noise_floor_closes_attack():
    """TV-29: ABSOLUTE noise floor (sigma_min) saldiriyi kapatir."""
    rng = random.Random(2901)
    n, k, c, jitter = 16, 32, 0.001, 1e-5
    B = [rng.uniform(-1, 1) for _ in range(k)]
    A = attack_rows(rng, n, k, c, jitter)
    # noise floor ILE (sigma_min = 8 quantized unit, Pearl SS5)
    noisy = []
    for row in A:
        sig = noise_fp8_aware(row, sigma_min=8.0)
        noisy.append([v + rng.gauss(0, s) for v, s in zip(row, sig)])
    tiles = output_tiles(noisy, B)
    Qtiles = quantize_vec(tiles, "E4M3")
    uniq = len(set(Qtiles))
    # floor ile cikis tile'lari yayilmali (>=8 farkli deger)
    assert uniq >= 8, f"TV-29: noise floor ile hala low entropy: {uniq} deger"
    return "PASS", f"noise floor (8 unit) ile {uniq} farkli cikis degeri - saldiri kapandi"


def tv30_entry_liveness_grinding():
    """
    TV-30: NEGATIF SONUC x2 - entry liveness grinding DELTA'yi sinar.

    Pearl SS5.1: tau_idle=8, epsilon_idle=1/64. Bir entry "idle/dwarfed"
    eger |entry| < noise/tau_idle. Saldirgan seed grinding ile bu orani
    epsilon_idle'in altina dusurmeye calisir.

    ILLERI BULGU (dürüst): ortalama-durum analizi YANLIS sinir verir.
      - DELTA=0.5 (TV-12 sabiti): ~%5.5 dwarfed -> ASAR
      - Analitik ortalama sinir DELTA <= sqrt(3)*tau*eps = 0.217: hala ~%3.7
        ASAR - cunku grinding RMS'nin DALGALANMA sonunu secer (worst-case RMS
        > ortalama RMS).
      - GERCEK grinding-direncli sinir (500 seed worst-case): DELTA <= 0.06.

    Sonuc: DELTA toy'da 0.5 -> 0.06'ya indirilmelidir. Bu spec duzeltmesidir.
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
    analytic = math.sqrt(3) * TAU_IDLE * EPSILON_IDLE  # ortalama-durum siniri
    f_analytic = dwarfed_worst(analytic)
    f_safe = dwarfed_worst(0.06)
    ok = f_safe < EPSILON_IDLE
    note = (f"DELTA=0.5 -> %{f05*100:.2f}; analitik sinir {analytic:.3f} -> "
            f"%{f_analytic*100:.2f} (hala ASAR!); gercek sinir DELTA<=0.06 -> "
            f"%{f_safe*100:.2f} ({'GECER' if ok else 'ASAR'}) - "
            f"ORTALAMA-DURUM ANALIZI YETERSIZDIR")
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
    print("  TOY SINIRLAR (dürüst):")
    print("    - Sadelestirilmis FP8 (RNE + subnormal flush); IEEE-754 DEGIL.")
    print("      Gercek donanim RNE/RZ + tensor-core accumulation ile farkli.")
    print("      Hawkeye bit-exact replay bu yuzden ZORUNLU (Badash et al.).")
    print("    - r=2 toy rank (Pearl k<=2^16 icin r=32); asimptotik KANIT degil.")
    print("    - Q(A+N) nonlineerligi tek add-then-quantize; gercek MatMul'da")
    print("      her MAC adiminda tekrarlanir.")
    print("    - Saldiri cikis tile'larinda; gercek tile n/r boyutundadir.")
    print()
    print("  SONUC:", "HEPSI GECTI" if allpass else "NEGATIF SONUCLAR VAR (yukarida) - spec guncellenmeli")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
