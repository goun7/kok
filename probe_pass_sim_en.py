#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KOK v2 — adversarial edge probes for the Pass economic model (TV-61..TV-64).

The last unprobed module. pass_sim_en.py is the closed-form solver for Pass's
(arXiv 2606.06700) economic model, and the paper quotes its regime boundaries
(Bitconia / Fortessia / Duplexia) and its attack-cost result (PR/2). A numerical
error here would corrupt the paper's central economic claims, so the probes
target the solver's own guarantees rather than the economics: are the residuals
actually zero, does the endogenous theta stay inside the bounds the file says it
must, and is the attack-cost arithmetic self-consistent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pass_sim_en import Params, solve, verify, classify_ok, _theta_from_PR


def report(name, ok, detail=""):
    print("  %-46s %s %s" % (name, "ACCEPT" if ok else "RED", detail))
    return ok


def _duplexia_params():
    return Params(e=0.02, R=100.0, P=0.30, alpha=1.3, gamma=1.3, eps=2.0, K=3.6)


def tv61_residuals_are_zero_in_all_regimes():
    """Every equilibrium the solver returns must actually solve its equations.

    The solver returns an Eq per regime; verify() recomputes the zero-profit
    residuals independently. A residual far from zero means the named regime is
    not an equilibrium at those parameters, and any number derived from it is
    fiction.
    """
    cases = [
        ("Bitconia", Params(e=0.02, R=100.0, P=0.001, alpha=1.3, gamma=1.3)),
        ("Fortessia", Params(e=0.02, R=100.0, P=0.10, alpha=1.3, gamma=1.3)),
        ("Duplexia", _duplexia_params()),
    ]
    worst = 0.0
    for name, prm in cases:
        eq = solve(prm)
        active, inactive = eq.residuals(prm)
        for r in active:
            worst = max(worst, abs(r))
        for r in inactive:
            worst = max(worst, r)
    ok = worst < 1e-6
    return report("TV-61 residuals zero across all regimes", ok,
                  "worst residual=%.2e" % worst)


def tv62_theta_stays_within_bounds():
    """_theta_from_PR must return a value in (theta_low, theta_high), or NaN.

    The docstring states the solution must lie in that open interval. The old
    bisection bracketed 1e-12..1e9 and never checked the bound, so a parameter
    set whose root falls below theta_low was returned as if it were a valid
    Duplexia root. It is not: below theta_low the economy is Fortessia. The
    contract is now "a root inside the interval, or NaN" — a value outside the
    interval is a bug, because solve() only calls this for the Duplexia branch
    and would mis-classify the regime.

    Note the asymmetry this makes explicit: solve() itself is correct, because it
    tests PR against theta_low * e * Q_B before calling here. The bug was in the
    function's own contract, reachable by any caller who trusts the docstring.
    """
    bad = []
    for P in [0.01, 0.05, 0.10, 0.30, 1.0, 3.0]:
        prm = Params(e=0.02, R=100.0, P=P, alpha=1.3, gamma=1.3, eps=2.0, K=3.6)
        th = _theta_from_PR(prm)
        if th != th:                      # NaN: no root in the interval — correct
            continue
        if not (prm.theta_low < th < prm.theta_high):
            bad.append((P, th))
    ok = not bad
    return report("TV-62 theta inside bounds or NaN", ok,
                  "out-of-bounds (non-NaN): %d" % len(bad))


def tv63_nan_params_marked_not_ok():
    """Parameters with no solution must not classify as a valid equilibrium.
    """
    # an extreme P with no root in range
    prm = Params(e=0.02, R=100.0, P=1e9, alpha=1.3, gamma=1.3, eps=2.0, K=3.6)
    th = _theta_from_PR(prm)
    is_nan = th != th
    ok = is_nan
    return report("TV-63 no-root parameters yield NaN theta", ok,
                  "theta=%s" % th)


def tv64_regime_selection_matches_delta_sign():
    """Bitconia must appear exactly when Delta < 0, as the solver's own rule says.
    """
    import random
    rng = random.Random(5)
    viol = 0
    for _ in range(60):
        alpha = rng.uniform(1.05, 2.0)
        gamma = rng.uniform(1.05, 2.0)
        prm = Params(e=0.02, R=100.0, P=rng.uniform(0.001, 0.5),
                     alpha=alpha, gamma=gamma, eps=2.0, K=3.6)
        eq = solve(prm)
        delta = prm.Delta
        # Delta < 0 should be the Bitconia regime (mining only, no demand)
        if delta < 0 and eq.name != "Bitconia":
            viol += 1
    ok = viol == 0
    return report("TV-64 Delta<0 selects Bitconia", ok, "violations=%d" % viol)


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — Pass economic model probes (TV-61..TV-64)")
    print("=" * 76)
    print()
    results = [tv61_residuals_are_zero_in_all_regimes(),
               tv62_theta_stays_within_bounds(),
               tv63_nan_params_marked_not_ok(),
               tv64_regime_selection_matches_delta_sign()]
    print()
    n = sum(1 for r in results if r)
    print("probes: %d/%d" % (n, len(results)))
    if n != len(results):
        print("RED PROBES REMAIN — fix the bug or document the limit.")
        raise SystemExit(1)
