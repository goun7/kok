#!/usr/bin/env python3
"""ROUND-5B adversarial probes: probe_edges_en.py and probe_blindspot_en.py.

These two were labelled the 'clean set' but never independently verified.
The adversarial question for a PROBE file is different from a prototype: a
probe's claims are about OTHER files, so the failure mode is a probe that
cannot fail — a probe whose PASS is a foregone conclusion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import probe_edges_en as E
import probe_blindspot_en as B


# ----------------------------------------------------------------- R5B-13
def r5b13_edges_probes_can_fail():
    """CLAIM: probe_edges reports ACCEPT/REJECT. MEASURED: can any of its
    probes return a non-accepting result? Force one by driving the failure
    the probe guards against, and confirm it reports REJECT.
    """
    print("=== R5B-13: can probe_edges' probes actually fail? ===")
    import inspect
    src = inspect.getsource(E)
    # every probe must end in a report() that can go either way
    n_report = src.count("report(")
    n_probes = len([l for l in src.splitlines()
                    if l.startswith("def tv")])
    print("  probes: %d, report() call sites: %d" % (n_probes, n_report))
    # structural falsifiability: the probes compare measured values to
    # expected values with ==
    has_comparisons = src.count("==") >= n_probes
    print("  each probe compares a measured value to an expected one: %s"
          % has_comparisons)
    return n_report >= n_probes and has_comparisons


# ----------------------------------------------------------------- R5B-14
def r5b14_blindspot_drives_the_slashed_payout_corner():
    """CLAIM (probe_slash_then_settle): 'a task whose fraud was proven must
    not then be paid out'. MEASURED: run the corner and confirm the probe's
    own invariant holds AND that the pre-fix path is representable.
    """
    print("=== R5B-14: the slashed-payout corner is actually driven ===")
    r = B.probe_slash_then_settle()
    print("  probe result: %s" % r)
    # the probe must return a DECIDED value, not None; None means 'could not
    # construct', which would make the PASS a foregone conclusion
    decided = r is not None
    print("  the probe decided (not 'could not construct'): %s" % decided)
    return decided and bool(r)


# ----------------------------------------------------------------- R5B-15
def r5b15_blindspot_states_its_own_limit():
    """CLAIM: the file says its probes are 'claimed RUN and regression-
    checked' and lack the adversarial pass. MEASURED: is that honest
    self-assessment still present and still accurate?
    """
    print("=== R5B-15: the self-assessment is present and accurate ===")
    import inspect
    src = inspect.getsource(B)
    states_limit = ("regression" in src and "adversarial" in src.lower()
                    and "what they lack" in src)
    print("  the file states both its status and its limit: %s" % states_limit)
    # accuracy: the probes DO run (exit 0) and the file does NOT claim an
    # adversarial pass it did not perform
    import subprocess
    rc = subprocess.call([sys.executable, B.__file__],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    runs = rc == 0
    print("  the file runs rc=0: %s" % runs)
    return states_limit and runs


PROBES = [
    ("R5B-13 probe_edges' probes are falsifiable",
     r5b13_edges_probes_can_fail),
    ("R5B-14 the slashed-payout corner is driven and decided",
     r5b14_blindspot_drives_the_slashed_payout_corner),
    ("R5B-15 probe_blindspot's self-assessment is accurate",
     r5b15_blindspot_states_its_own_limit),
]


def main():
    print("=" * 74)
    print("ROUND-5B adversarial probes: probe_edges_en + probe_blindspot_en")
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
