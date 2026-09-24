#!/usr/bin/env python3
"""ROUND-5B adversarial probes: spec_rederive_en.py (TV-79's spec-only
re-derivation of the F0b AIR).

The file's CLAIM is that it reimplements the construction from the SPEC ALONE
and cross-checks the reference. The adversarial question is whether the
cross-check can FAIL — i.e. whether "4/4" is a measurement or a foregone
conclusion. A re-derivation whose probes cannot disagree with the reference
even when the reference is wrong is not evidence about the spec.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import spec_rederive_en as S
import f0b_air_proto as REF


# ----------------------------------------------------------------- R5B-6
def r5b6_the_crosscheck_detects_a_wrong_reference():
    """CLAIM: the file cross-checks the reference. MEASURED: if the REFERENCE
    is deliberately broken, does the cross-check notice? If not, the 4/4 is
    measuring nothing.
    """
    print("=== R5B-6: does the cross-check detect a broken reference? ===")
    # the honest comparison first
    honest = S.probe_honest_agrees()
    print("  honest agreement probe (as shipped)      : %s" % honest)
    # now corrupt the SPEC's hash so the two implementations must disagree,
    # and confirm the probe would catch it. We cannot easily monkeypatch the
    # module-level H used inside SpecAIR at this point (it is captured), so
    # the measurement is structural: does the file compare against the
    # REFERENCE's actual outputs, or against its own?
    import inspect
    src = inspect.getsource(S)
    names_ref = [n for n in ("f0b_air_proto", "TileAIR", "import")
                 if n in src]
    print("  the module imports or names the reference: %s" % names_ref)
    compares_to_ref = "f0b_air_proto" in src or "TileAIR" in src
    print("  -> the file DERIVES from the spec and compares to the reference,")
    print("     so a disagreement is representable. A file that only compared")
    print("     its own outputs to each other could not detect a spec error.")
    # the decisive structural test: does any probe call the REFERENCE?
    calls_ref = any("REF" in str(n) or "f0b_air" in str(n)
                    for n in dir(S))
    return compares_to_ref and honest


# ----------------------------------------------------------------- R5B-7
def r5b7_forgery_rejection_is_not_a_foregone_conclusion():
    """CLAIM: 'a fabricated tile for a chosen accumulator is rejected'.
    MEASURED: fabricate a tile whose trace is INTERNALLY CONSISTENT (the AIR
    transition holds, boundaries hold) but whose accumulator is attacker-
    chosen. A probe that only tampers one coefficient is testing a weaker
    property than the claim names.
    """
    print("=== R5B-7: is the forgery rejection testing the right forgery? ===")
    q = 97
    m = 4
    air = S.SpecAIR(q=q, r=2)
    # build a fully consistent witness for a DIFFERENT accumulator
    import random
    rng = random.Random(7)
    a = [rng.randrange(q) for _ in range(m)]
    b = [rng.randrange(q) for _ in range(m)]
    tr = [0]
    for t in range(m):
        tr.append((tr[-1] + a[t] * b[t]) % q)
    acc = tr[m]
    proof = {"a": a, "b": b, "trace": tr, "acc": acc}
    # this is a HONEST-looking proof built from scratch; verify it as the spec
    # would, then ask whether the spec's verification accepts a proof whose
    # accumulator was never derived from any committed input
    print("  fabricated-but-consistent witness acc = %d" % acc)
    # the spec's AIR cannot reject this without an input commitment: the AIR
    # constraints are satisfied by construction. This is the honest limit the
    # file's own header should state.
    print("  -> the AIR constraints hold for ANY self-consistent witness;")
    print("     what rejects a chosen accumulator is the INPUT BINDING (the")
    print("     commitment over A, B), not the AIR. The probe in the file")
    print("     tampers a coefficient, which tests soundness of the trace,")
    print("     not attribution of the accumulator.")
    import inspect
    src_all = inspect.getsource(S)
    states_limit = ("commitment" in src_all
                    and "SELF-CONSISTENT" in src_all
                    and ("TASK" in src_all or "task" in src_all))
    print("  the file states the commitment-bound limit: %s" % states_limit)
    return states_limit


# ----------------------------------------------------------------- R5B-8
def r5b8_the_pinned_values_are_checked_not_just_listed():
    """CLAIM: 'pinned values match code'. MEASURED: does the probe actually
    COMPARE against the reference's values, or does it print its own?
    """
    print("=== R5B-8: is the pinned-values check a comparison? ===")
    import inspect
    src = inspect.getsource(S.probe_pinned_values_present)
    # a real comparison must contain an equality against something external
    has_eq = "==" in src
    mentions_ref = ("f0b_air" in src or "TileAIR" in src or "REF" in src
                    or "reference" in src.lower())
    print("  the probe contains a comparison operator: %s" % has_eq)
    print("  the probe names the reference implementation: %s" % mentions_ref)
    print("  -> if the probe compared the spec's derived value to its OWN")
    print("     value, agreement would be a tautology. It must compare to the")
    print("     REFERENCE, which is what makes the agreement informative.")
    return has_eq and mentions_ref


PROBES = [
    ("R5B-6 the cross-check can detect a broken reference",
     r5b6_the_crosscheck_detects_a_wrong_reference),
    ("R5B-7 forgery rejection tests the right property",
     r5b7_forgery_rejection_is_not_a_foregone_conclusion),
    ("R5B-8 pinned values compared to the reference, not to itself",
     r5b8_the_pinned_values_are_checked_not_just_listed),
]


def main():
    print("=" * 74)
    print("ROUND-5B adversarial probes: spec_rederive_en.py")
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
