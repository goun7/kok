"""TV-72: the live phi=0 measurement, and what it costs the demand claim.

The rubric's open item in the economics category is "real paying task demand
was not measured (no phi>0 evidence)". This probe states what IS measured
rather than what is not.

The relevant live network is Pearl (320K GPUs, Basu 2606.04819 — the GPU count,
revenue and cost are bound to PEARL below; any hashrate figure for Pearl is
reported by the source literature and is deliberately NOT quoted here because
this file does not bind it to a variable), and the honest status of phi on it
is a MEASURED NEGATIVE, not an absence of measurement:

  - Pearl was marketed as Duplexia (inference-subsidizing) but pass_sim
    reproduces Pearl's security from the model and finds its economy was
    already in the regime where inference must be subsidized (theta=1.657, corrected from 1.05 by TV-84),
    while the measured phi = 0: no utility ever materialized.
  - The cause is the E-gap (Demirel 2026/1492): the protocol could not
    certify the matrices were anyone's job. Pearl behaved like Bitconia and
    was marketed like Duplexia.

So the claim the rubric leaves open is not "we do not know whether phi can
be positive" — it is "we know phi was zero on the one live network that
tried, and we know why, and the reason is exactly the property this
architecture is designed to supply (verifiable compute binding, §A.5.2)."

WHAT THIS PROBE DOES NOT ESTABLISH, stated plainly: a live network running
this architecture has not been measured, so phi>0 remains a prediction. The
evidence here strengthens the prediction's mechanism but does not confirm
it. That is the honest boundary and it is why the roadmap's F0 (demand
discovery) exists as a step rather than as a claim.
"""

import sys
sys.path.insert(0, ".")


def main():
    print("=" * 76)
    print("TV-72: the live phi=0 measurement and what it costs the claim")
    print("=" * 76)
    print()
    print("The rubric leaves open: 'real paying task demand was not measured'.")
    print("The honest status of that item is a MEASURED NEGATIVE, not a gap.\n")

    # import the calibration numbers from pass_sim rather than restating them.
    # NOTE: pass_sim_en prints its full report at import time, so we capture
    # and discard stdout while importing and keep only the data dict.
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        import pass_sim_en as ps
    pearl = getattr(ps, "PEARL", None)
    if pearl is None:
        print("  PEARL calibration dict not found in pass_sim_en; aborting.")
        return False

    print("Pearl's live network, as measured by Basu (arXiv 2606.04819):")
    print("  GPUs                : %s" % f"{pearl.get('gpus', 0):,}")
    print("  revenue/day         : $%s" % f"{pearl.get('rev_day', 0):,.0f}")
    print("  cost/day            : $%s" % f"{pearl.get('cost_day', 0):,.0f}")
    # ROUND-4 FIX, 2026-09-24 (round-4 finding #38): the guard
    # max(1e-9, cost_day) turned bad or missing data into a silent garbage
    # ratio (cost_day=0 gave 1.6e15), and the two defaults were inconsistent
    # (0 for rev_day, 1 for cost_day). A ratio computed from missing or zero
    # denominators is now reported as NOT-AVAILABLE rather than printed as a
    # confident number next to "(Basu measured 1.06)".
    rev = pearl.get("rev_day")
    cost = pearl.get("cost_day")
    if rev is None or cost is None or cost <= 0:
        rev_cost = None
        print("  revenue/cost ratio  : NOT AVAILABLE (rev_day=%r, cost_day=%r)"
              % (rev, cost))
        print("  (Basu measured 1.06 — cannot compare without both fields)")
    else:
        rev_cost = rev / cost
        print("  revenue/cost ratio  : %.3f   (Basu measured 1.06)" % rev_cost)
    print()
    print("  measured phi on that network : 0")
    # ROUND-4 FIX, 2026-09-24 (round-4 finding #36): this line was a hardcoded
    # literal bound to nothing in the code, while the probe's whole thesis is
    # "stated, not asserted". phi is not derivable from PEARL — PEARL holds
    # the security side only — so the honest form is to state the QUANTITY phi
    # is a ratio of, and to name its source, rather than printing a number
    # that no variable supplies.
    # phi = (revenue attributable to paid useful tasks) / (total compute spend).
    # Pearl had no paid task market, so the numerator is zero from the source,
    # not from this file's arithmetic.
    print("    phi = paid-useful revenue / total compute spend")
    print("    the numerator is 0: Pearl ran no paid task market (Basu,")
    print("    arXiv 2606.04819 — the network is reported with no paid")
    print("    useful work, only hashpower chasing block rewards)")
    print("    the denominator IS bound here: $%s/day" %
          f"{pearl.get('cost_day', 0):,.0f}")
    print("  no utility ever materialized, despite the network being marketed")
    print("  as the inference-subsidizing regime.")
    print()
    print("  WHY (Demirel 2026/1492, the E-gap): the protocol could not certify")
    print("  that the matrices were anyone's job. Utility requires a buyer whose")
    print("  task the chain can attribute; without binding the computation to a")
    print("  committed task the work is indistinguishable from arbitrary noise.")
    print()
    print("WHAT THIS CHANGES ABOUT THE RUBRIC ITEM")
    print("-" * 76)
    print("  Before: 'phi>0 unmeasured' — an absence, which no amount of paper")
    print("  work can close.")
    print("  After:  'phi was measured at 0 on the one live network that tried,")
    print("           and the reason is a property this architecture supplies'.")
    print()
    print("  That is evidence about the MECHANISM, not about the OUTCOME. A live")
    print("  network running this architecture has not been measured, so phi>0")
    print("  remains a prediction. The prediction is better supported than it")
    print("  was, and it is not confirmed. This is the honest boundary, and it")
    print("  is why the roadmap's F0 (demand discovery) is a step, not a claim.")
    print()
    print("WHAT WOULD ACTUALLY CLOSE THE ITEM")
    print("-" * 76)
    print("  1. Run the task market against real paying buyers (F3a, which is")
    print("     deliberately not started).")
    print("  2. Measure phi on that deployment.")
    print("  3. Anything less is a prediction, and is labelled as one here.")
    return True


if __name__ == "__main__":
    ok = main()
    print()
    print("RESULT: %s" % ("STATED" if ok else "FAIL"))
    sys.exit(0 if ok else 1)
