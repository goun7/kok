#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - BOND-MARGIN MEASUREMENT PROTOTYPE (TV-31..TV-33)
=========================================================
This prototype closes KNOWN GAP #3: "The economic weight of TV-17 is partially
open - the margin of bond=fee+margin will be measured in f3a; pass_sim §10
only gave the threshold equation."

pass_sim §10 gave the threshold equation but left one modeling detail
unresolved: the per-event slash = min(bond, fee), i.e. it is CAPPED AT FEE.
This prototype MEASURES the margin and extracts the effect of that cap.

ECONOMIC MODEL (same as pass_sim §10 + 2 slash modes):
  Censorship event: task rejected -> the bond is slashed. Slash amount:
    "capped" (f3a's actual behavior): slash = min(bond, fee)
      -> the deterrent is BOUNDED BY FEE; raising bond above fee is USELESS
    "full"   (spec A.5.5's intent, "bond = fee + margin"): slash = bond
      -> the deterrent scales with bond; margin = B_out - fee works

  refill=True: the bond is topped back up after every event
  refill=False: the bond is depleted -> later events are FREE (one-shot)

  Censorship net payoff (per event, with refill):
    capped: net = B_out - min(bond, fee)
    full:   net = B_out - bond

TESTS:
- TV-31: in CAPPED mode the deterrent is BOUNDED BY FEE - bond > fee is inert
  (SPEC CORRECTION: "bond = fee + margin" only holds in the "full" mode)
- TV-32: FULL modda margin = B_out - fee lineer; esik denklemi dogrulanir
- TV-33: without refill the "free censorship window" = bond/fee events;
  refill closes the window

HONEST LIMITS:
- This is a GAME model; B_out is hidden from the protocol (the margin must be
  ESTIMATED by governance). This prototype measures how accurate that estimate
  must be and which slash mode to use.
- fee/bond are symbolic toy values (production: chain.params).
- N=20 events, B_out in [60,500] - not an asymptotic proof.
- The "full" slash mode does NOT exist in the protocol (f3a used capped);
  this prototype PROPOSES it - it must be added to spec A.5.5.
"""

import random
import math


# ============================================================
def censor_net(fee, bond, b_out, n_events, refill=True, slash_mode="capped"):
    """
    Total net payoff of N censorship events (from the sequencer view).

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
    """The smallest fee that stops censorship in CAPPED mode (= B_out)."""
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
    """The smallest margin (bond - fee) that stops censorship in FULL mode."""
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
    """TV-31: in CAPPED mode the deterrent is BOUNDED BY FEE - raising bond is useless."""
    fee, b_out = 100.0, 60.0
    net_bond_100 = censor_net(fee, 100.0, b_out, 1, refill=True, slash_mode="capped")
    net_bond_500 = censor_net(fee, 500.0, b_out, 1, refill=True, slash_mode="capped")
    net_bond_2000 = censor_net(fee, 2000.0, b_out, 1, refill=True, slash_mode="capped")
    # in all of them the slash = min(bond, fee) = fee = 100 -> the same net
    assert abs(net_bond_100 - net_bond_500) < 1e-9, "TV-31: bond 100->500 effective"
    assert abs(net_bond_500 - net_bond_2000) < 1e-9, "TV-31: bond 500->2000 effective"
    # critical fee = B_out
    cf = critical_fee_capped(b_out)
    assert abs(cf - b_out) < 1.0, f"TV-31: critical fee {cf:.1f} != B_out {b_out}"
    return "PASS", (f"capped: bond 100/500/2000 give the same net ({net_bond_100:.0f}) - the slash "
                    f"saturates at fee={fee}; critical fee = B_out = {cf:.0f}. "
                    f"SPEC CORRECTION: 'bond=fee+margin' only holds in FULL slash mode")


def tv32_full_margin_linear():
    """TV-32: in FULL mode margin = B_out - fee; threshold equation verified."""
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
    return "PASS", (f"FULL mode: margin = B_out - fee (max error {max_err:.2f}); "
                    f"R^2={r2:.4f}; fee=100, B_out=300 -> margin={pts[3][1]:.0f}")


def tv33_free_censorship_window():
    """""TV-33: without refill the free-censorship window = bond/fee events."""
    fee, bond, b_out = 100.0, 300.0, 60.0
    n = 20
    # no refill: bond 300/100 stops 3 events, then FREE
    net_noref = censor_net(fee, bond, b_out, n, refill=False, slash_mode="capped")
    net_ref = censor_net(fee, bond, b_out, n, refill=True, slash_mode="capped")
    window = bond / fee
    # without refill the total slash = bond (300); with refill: n*fee (2000)
    assert abs(net_noref - (b_out * n - bond)) < 1.0, f"TV-33: net without refill {net_noref}"
    assert abs(net_ref - (b_out * n - n * fee)) < 1.0, f"TV-33: refill'li net {net_ref}"
    return "PASS", (f"bond={bond}, fee={fee}: free window = {window:.0f} events; "
                    f"N={n}: NO refill net={net_noref:.0f} (profitable!), WITH refill "
                    f"net={net_ref:.0f} (a loss) - refill closes the window")


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
    print("  TOY LIMITS (honest):")
    print("    - GAME model; B_out is hidden from the protocol (margin must be")
    print("      ESTIMATED by governance - this measures the required accuracy).")
    print("    - fee/bond are symbolic toy values (production: chain.params).")
    print("    - N=20 events, B_out uniform - not an asymptotic proof.")
    print("    - the 'full' slash mode does NOT exist in the protocol (f3a used capped);")
    print("      this prototype PROPOSES it - it must be added to spec A.5.5.")
    print()
    print("  RESULT:", "ALL PASSED" if allpass else "FAILED")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
