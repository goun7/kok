#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - BOND-MARGIN MEASUREMENT PROTOTYPE (TV-31..TV-33)
=========================================================
Bu prototip KNOWN GAP #3'u kapatir: "The economic weight of TV-17 is partially
open - the margin of bond=fee+margin will be measured in f3a; pass_sim §10
only gave the threshold equation."

pass_sim §10 ESIT denklemini VERDI ama bir modelleme ayrintisini netlestirmedi:
her sansur olayinda kesinti = min(bond, fee) - yani FEE ILE KAPALI. Bu
prototip margin'i OLCER ve bu kapanin etkisini cikarir.

EKONOMIK MODEL (pass_sim §10 ile ayni + 2 kesinti modu):
  Sansur olayi: gorev red -> bond kesilir. Kesinti miktari:
    "capped" (f3a'nin gercek davranisi): slash = min(bond, fee)
      -> DETERRENT FEE ILE SINIRLI; bond'u fee'nin ustune cikarmak BOS
    "full"   (spec A.5.5'in "bond = fee + margin" niyeti): slash = bond
      -> deterrent bond ile olceklenir; margin = B_out - fee calisir

  refill=True: bond her olay sonrasi tam seviyeye tamamlanir
  refill=False: bond tukerilir -> sonraki olaylar BEDAVA (tek-seferlik)

  Sansur net kazanci (olay basina, refill ile):
    capped: net = B_out - min(bond, fee)
    full:   net = B_out - bond

TESTLER:
- TV-31: CAPPED modda deterrent FEE ILE SINIRLI - bond > fee etkisizdir
  (SPEC DUZELTMESI: "bond = fee + margin" ancak "full" modda gecerlidir)
- TV-32: FULL modda margin = B_out - fee lineer; esik denklemi dogrulanir
- TV-33: Refill'siz "bedava sansur penceresi" = bond/fee olay; refill
  pencereyi kapatir

DURUST SINIR:
- Bu bir OYUN modeli; B_out protokole gizlidir (margin GOVERNANCE ile
  tahmin edilmeli). Bu prototip tahminin NE KADAR HASSAS olmasi gerektigini
  ve hangi modun kullanilacagini olcer.
- fee/bond sembolik toy degerler (production: chain.params).
- N=25 olay, B_out in [10,200] - asimptotik kanit degil.
- "full" mod protokolde YOK (f3a capped kullandi); bu prototip onerir.
"""

import random
import math


# ============================================================
def censor_net(fee, bond, b_out, n_events, refill=True, slash_mode="capped"):
    """
    N sansur olayinin TOPLAM net kazanci (siralamaci acisindan).

    slash_mode="capped": slash = min(bond, fee)  [f3a gercek davranisi]
    slash_mode="full":   slash = bond            [spec A.5.5 niyeti]
    """
    cur = bond
    total_slash = 0.0
    for _ in range(n_events):
        if slash_mode == "capped":
            slash = min(cur, fee)
        else:
            slash = min(cur, bond)  # full: bond'un tumu (tukenene kadar)
        total_slash += slash
        cur -= slash
        if refill:
            cur = bond
    return b_out * n_events - total_slash


def critical_fee_capped(b_out):
    """CAPPED modda sansuru durduran en kucuk fee (= B_out)."""
    lo, hi = 0.0, b_out * 2 + 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        net = censor_net(mid, mid * 3, b_out, 1, refill=True, slash_mode="capped")
        if net > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def critical_margin_full(fee, b_out):
    """FULL modda sansuru durduran en kucuk margin (bond - fee)."""
    lo, hi = 0.0, b_out + 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        net = censor_net(fee, fee + mid, b_out, 1, refill=True, slash_mode="full")
        if net > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ============================================================
def tv31_capped_deterrent_bounded_by_fee():
    """TV-31: CAPPED modda deterrent FEE ILE SINIRLI - bond'u artirmak BOS."""
    fee, b_out = 100.0, 60.0
    net_bond_100 = censor_net(fee, 100.0, b_out, 1, refill=True, slash_mode="capped")
    net_bond_500 = censor_net(fee, 500.0, b_out, 1, refill=True, slash_mode="capped")
    net_bond_2000 = censor_net(fee, 2000.0, b_out, 1, refill=True, slash_mode="capped")
    # hepsinde kesinti = min(bond, fee) = fee = 100 -> ayni net
    assert abs(net_bond_100 - net_bond_500) < 1e-9, "TV-31: bond 100->500 etkili"
    assert abs(net_bond_500 - net_bond_2000) < 1e-9, "TV-31: bond 500->2000 etkili"
    # kritik fee = B_out
    cf = critical_fee_capped(b_out)
    assert abs(cf - b_out) < 1.0, f"TV-31: kritik fee {cf:.1f} != B_out {b_out}"
    return "PASS", (f"capped: bond 100/500/2000 ayni net ({net_bond_100:.0f}) - "
                    f"kesinti fee={fee}'de doygun; kritik fee = B_out = {cf:.0f}. "
                    f"SPEC DUZELTMESI: 'bond=fee+margin' ancak FULL kesinti modunda gecerli")


def tv32_full_margin_linear():
    """TV-32: FULL modda margin = B_out - fee; esit denklemi dogrulanir."""
    fee = 100.0
    pts = []
    for b_out in [120, 150, 200, 300, 500]:
        m = critical_margin_full(fee, b_out)
        pts.append((b_out, m))
    max_err = max(abs(m - (b - fee)) for b, m in pts)
    assert max_err < 1.0, f"TV-32: margin B_out-fee'den sapar: {max_err:.2f}"
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
    r2 = (sxy ** 2) / (sxx * syy)
    return "PASS", (f"FULL modda margin = B_out - fee (max hata {max_err:.2f}); "
                    f"R^2={r2:.4f}; fee=100, B_out=300 -> margin={pts[3][1]:.0f}")


def tv33_free_censorship_window():
    """TV-33: Refill'siz bedava-sansur penceresi = bond/fee olay."""
    fee, bond, b_out = 100.0, 300.0, 60.0
    n = 20
    # refill yok: bond 300/100 = 3 olayi engeller, sonra BEDAVA
    net_noref = censor_net(fee, bond, b_out, n, refill=False, slash_mode="capped")
    net_ref = censor_net(fee, bond, b_out, n, refill=True, slash_mode="capped")
    window = bond / fee
    # refill'siz: toplam kesinti = bond (300); refill'da: n*fee (2000)
    assert abs(net_noref - (b_out * n - bond)) < 1.0, f"TV-33: refill'siz net {net_noref}"
    assert abs(net_ref - (b_out * n - n * fee)) < 1.0, f"TV-33: refill'li net {net_ref}"
    return "PASS", (f"bond={bond}, fee={fee}: bedava pencere = {window:.0f} olay; "
                    f"N={n}: refill YOK net={net_noref:.0f} (kârli!), refill VAR "
                    f"net={net_ref:.0f} (zarar) - refill pencereyi kapatir")


# ============================================================
def main():
    print("=" * 72)
    print("KOK v2 - BOND-MARGIN MEASUREMENT (TV-31..TV-33)")
    print("=" * 72)
    print("  capped: slash=min(bond,fee) [f3a] | full: slash=bond [spec A.5.5]")
    print("  fee=100, B_out in [60,500], N in [1,20] (toy)")
    print()
    tests = [tv31_capped_deterrent_bounded_by_fee, tv32_full_margin_linear,
             tv33_free_censorship_window]
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
    print("    - OYUN modeli; B_out protokole gizlidir (margin GOVERNANCE ile")
    print("      tahmin edilmeli - bu prototip tahminin hassasiyetini olcer).")
    print("    - fee/bond sembolik toy degerler (production: chain.params).")
    print("    - N=20 olay, B_out uniform - asimptotik kanit degil.")
    print("    - 'full' kesinti modu protokolde YOK (f3a capped kullandi);")
    print("      bu prototip onerir - spec A.5.5'e eklenmelidir.")
    print()
    print("  SONUC:", "HEPSI GECTI" if allpass else "BASARISIZ")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
