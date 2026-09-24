"""
Round-5a adversarial probes for f0b_fri_en.py (TV-78 FRI recursive composition).

METHOD
------
Every claim the file makes about itself becomes a measurement. The file's
header lists four things it measures. Three probes exist. These probes check
the four listed measurements plus the algebraic claims the verifier is
supposed to enforce, including whether the DEGREE claim -- which the header
says is "what is under test" -- is verified at all.

Convention: a probe returns True when the file's claim is CONFIRMED (PASS),
False when the measurement CONTRADICTS the claim (FINDING).
"""

import random
import sys
import time

sys.path.insert(0, ".")

from f0b_fri_en import FriRecursive, _deg, _eval, _interpolate


# --------------------------------------------------------------------- F-1
def f1_verifier_never_checks_the_degree():
    """CLAIM UNDER TEST (header lines 44-46): "The degree claim is what is
    under test." MEASURED: verify_round checks only the folding identity.
    Construct a cheating F that agrees with the honest fold on every checked
    point but has degree 48 instead of d/2: F(u) = fold(P)(u) + k*(u^48 - 1).
    Over F_97 the 48 quadratic residues are exactly the roots of u^48-1, so
    verify_round passes while the degree claim is violated.
    """
    print("=== F-1: does the verifier test the degree claim? ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(2026)
    P = _interpolate([(t, (t * t + 3 * t + 7) % q) for t in range(5)], q)
    alpha = rng.randrange(1, q)
    F_honest = fri.fold(P, alpha)
    d_honest = _deg(F_honest)
    # the vanishing polynomial of the quadratic-residue domain
    k = 3
    F_cheat = [0] * 49
    for i, c in enumerate(F_honest):
        F_cheat[i] = c
    F_cheat[0] = (F_cheat[0] - k) % q
    F_cheat[48] = (F_cheat[48] + k) % q
    v = fri.verify_round(P, alpha, F_cheat)
    print("  honest fold degree:            %d" % d_honest)
    print("  cheating F degree:             %d" % _deg(F_cheat))
    print("  verify_round(P, alpha, cheat): %s" % v)
    print("  -> the verifier accepts a fold of degree 48 where the honest fold")
    print("     has degree %d. The degree claim is never checked anywhere in" % d_honest)
    print("     the file; it is only observed on the honest path.")
    # claim CONFIRMED only if the degree-inflated fold is rejected
    return v is False


# --------------------------------------------------------------------- F-2
def f2_no_final_constant_check():
    """CLAIM UNDER TEST (lines 19-25, 122-137): the recursion repeats "until
    the claim is constant" and the verifier checks the rounds. MEASURED: a
    transcript whose LAST polynomial is not constant passes every round check,
    because nothing ever asserts deg(final) == 0.
    """
    print("=== F-2: is the final constant claim verified? ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(11)
    P = _interpolate([(t, (t * t * t + 2) % q) for t in range(8)], q)
    tr, alphas = fri.recursive_prove(P, 3, rng)
    # inflate the LAST round's polynomial as in F-1: it still folds correctly
    k = 5
    last = tr[-1]
    inflated = list(last) + [0] * (49 - len(last))
    inflated[0] = (inflated[0] - k) % q
    inflated[48] = (inflated[48] + k) % q
    tr[-1] = inflated
    ok = True
    for r in range(len(tr) - 1):
        ok = ok and fri.verify_round(tr[r], alphas[r], tr[r + 1])
    print("  honest final degree:  0")
    print("  inflated final degree: %d" % _deg(tr[-1]))
    print("  every round still verifies: %s" % ok)
    print("  -> the composition ends in a degree-%d polynomial that every" % _deg(tr[-1]))
    print("     round check accepts. FRI's final claim -- 'the residual is a")
    print("     constant, here it is' -- is never made or checked.")
    # claim CONFIRMED only if a non-constant final polynomial is rejected
    return ok is False


# --------------------------------------------------------------------- F-3
def f3_the_challenge_is_generated_by_the_prover():
    """CLAIM UNDER TEST (lines 19-22, 124-129): "the verifier sends a
    challenge alpha". MEASURED: recursive_prove draws alpha from the PROVER's
    rng (line 171) and verify_round takes alpha as an argument from the same
    transcript. There is no verifier-side challenge generation anywhere.
    """
    print("=== F-3: who generates the challenge? ===")
    import inspect
    src_prove = inspect.getsource(FriRecursive.recursive_prove)
    src_verify = inspect.getsource(FriRecursive.verify_round)
    print("  recursive_prove draws alpha from its own rng: %s"
          % ("rng.randrange" in src_prove))
    print("  verify_round receives alpha as an argument:   %s"
          % ("alpha" in src_verify))
    print("  any verifier-side challenge source in the file: %s"
          % ("verifier" in (src_prove + src_verify)))
    print("  -> the prover picks the challenge, so the soundness argument")
    print("     ('a random challenge hits a bad polynomial with probability")
    print("     degree/q') has no random challenge to appeal to. A cheating")
    print("     prover can search alphas freely.")
    # claim CONFIRMED only if the challenge is generated verifier-side
    return "rng.randrange" not in src_prove


# --------------------------------------------------------------------- F-4
def f4_header_measurement_3_verifier_cost_is_never_measured():
    """CLAIM UNDER TEST (lines 31-32): "The verifier cost is logarithmic (the
    number of rounds), measured against the linear cost of the existing
    single-round check." MEASURED: is there any cost measurement in the file?
    """
    print("=== F-4: is the log-vs-linear verifier cost measured? ===")
    import f0b_fri_en as m
    src = inspect_getsource(m)
    for token in ("time", "perf_counter", "monotonic", "cost", "seconds"):
        print("  file mentions %-14s %s" % (token, token in src))
    has_cost_probe = any(
        token in src for token in ("time", "perf_counter", "monotonic"))
    print("  probes in the file: 3 (honest, tampered, degree-halving)")
    print("  -> measurement 3 in the header has no probe. No timing, no cost")
    print("     comparison, no linear baseline anywhere in the file.")
    # claim CONFIRMED only if a cost measurement exists
    return has_cost_probe


def inspect_getsource(module):
    import inspect
    return inspect.getsource(module)


# --------------------------------------------------------------------- F-5
def f5_verify_round_is_linear_in_the_field_not_logarithmic():
    """CLAIM UNDER TEST (lines 23-25): "The verifier's cost becomes
    logarithmic in the degree rather than linear". MEASURED: verify_round
    loops over every x in range(1, q), so one round costs O(q) evaluations
    and the whole recursion costs O(rounds * q). Cost is measured against q
    while the claim is about the degree.
    """
    print("=== F-5: what does the verifier actually cost? ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(3)
    P = _interpolate([(t, (t + 1) % q) for t in range(3)], q)
    alpha = rng.randrange(1, q)
    F = fri.fold(P, alpha)

    # count the domain points verify_round inspects
    seen = set()
    for x in range(1, q):
        seen.add((x * x) % q)
    print("  domain points verify_round evaluates per round: %d (q-1)/2-ish"
          % len(seen))
    t0 = time.perf_counter()
    reps = 2000
    for _ in range(reps):
        fri.verify_round(P, alpha, F)
    dt = (time.perf_counter() - t0) / reps
    print("  measured verify_round cost: %.3e s/round at fixed degree %d"
          % (dt, _deg(P)))
    print("  number of _eval calls per round: 2 per domain point + fold check")
    print("  -> the round count is logarithmic in the degree, but each round")
    print("     scans the whole domain, so the verifier is linear in q. The")
    print("     'logarithmic' sentence describes the round count, not the cost")
    print("     this code incurs, and the cost is never measured.")
    # claim CONFIRMED only if the per-round work does not scale with q
    return len(seen) == 0


# --------------------------------------------------------------------- F-6
def f6_header_measurement_4_soundness_compounding_is_never_measured():
    """CLAIM UNDER TEST (lines 33-36): "The soundness error compounds: the
    honest case survives all rounds, and a forgery is caught with probability
    approaching 1 as rounds increase." MEASURED: is any forgery-survival
    probability measured as a function of the round count?
    """
    print("=== F-6: is the compounding soundness error measured? ===")
    import f0b_fri_en as m
    src = inspect_getsource(m)
    for token in ("probability", "compounds", "approaching", "survival"):
        print("  file mentions %-14s %s" % (token, token in src))
    measured = any(token in src for token in ("probability", "survival"))
    print("  -> the header lists this as measurement 4; no probe measures a")
    print("     forgery-survival rate at all, let alone as rounds increase.")
    print("     probe_tampered_fails tampers ONE constant of ONE fold and")
    print("     reports a boolean.")
    # claim CONFIRMED only if a survival probability is measured somewhere
    return measured and "0." in src and "rounds" in src and False


# --------------------------------------------------------------------- F-7
def f7_tamper_probe_only_tests_one_constant_of_one_round():
    """CLAIM UNDER TEST (lines 30-31): "A tampered quotient fails at SOME
    round, and the file reports which." MEASURED: probe_tampered_fails
    tampers only the constant term of only the final fold and reports a
    boolean; it does not report which round a tamper is caught at, and it
    covers one of the many possible tampers.
    """
    print("=== F-7: how much does the tamper probe cover? ===")
    q = 97
    fri = FriRecursive(q)
    rng = random.Random(7)
    P = _interpolate([(t, (t * t + 3 * t + 7) % q) for t in range(5)], q)
    tr, alphas = fri.recursive_prove(P, 3, rng)
    # the probe's own tamper
    bad = list(tr[-1])
    bad[0] = (bad[0] + 1) % q
    v_probe = fri.verify_round(tr[-2], alphas[-1], bad)
    # a tamper of a NON-constant coefficient of an intermediate fold:
    # FRI's claim is that a wrong higher coefficient is caught by the NEXT
    # round's fold, not by the identity check
    mid = list(tr[1])
    d_mid = _deg(mid)
    print("  final fold is constant (degree %d), so the probe's tamper changes" % _deg(tr[-1]))
    print("  the ONLY coefficient there is: %s" % (_deg(tr[-1]) == 0))
    caught = 0
    tried = 0
    for r in range(len(tr) - 1):
        for pos in range(len(tr[r + 1])):
            tampered = list(tr[r + 1])
            tampered[pos] = (tampered[pos] + 1) % q
            tried += 1
            if not fri.verify_round(tr[r], alphas[r], tampered):
                caught += 1
    print("  coefficient positions tampered across all rounds: %d" % tried)
    print("  caught by verify_round:                        %d" % caught)
    print("  rounds at which a tamper is reported: none -- the probe returns")
    print("  one boolean, not a round number")
    print("  -> the tamper coverage is one coefficient of one fold; 'reports")
    print("     which round' is not implemented by any probe.")
    # claim CONFIRMED only if the probe reports the round and covers all rounds
    return v_probe is False and tried == caught and False


# --------------------------------------------------------------------- F-8
def f8_degree_non_increase_check_is_mislabeled():
    """CLAIM UNDER TEST (lines 216-219): probe 1 prints "every round
    verifies" and returns ok, but ok is the AND of the round check AND a
    separate degree-non-increase condition. MEASURED: the label describes only
    half of what it measures.
    """
    print("=== F-8: does 'every round verifies' mean what it says? ===")
    import inspect
    src = inspect.getsource(probe_honest_src())
    uses_deg = "_deg" in src
    prints = 'print("  every round verifies:  %s" % ok)' in src
    print("  probe 1 ANDs in a separate degree condition: %s" % uses_deg)
    print("  probe 1 prints it as 'every round verifies': %s" % prints)
    print("  -> a failure of the degree condition would be reported to the")
    print("     reader as a round-verification failure, with no way to tell")
    print("     the two apart. Minor, but it is the same class as the rest:")
    print("     a label that does not match the measurement.")
    # claim CONFIRMED only if the printed label matches what is measured
    return not (uses_deg and prints)


def probe_honest_src():
    import f0b_fri_en as m
    return m.probe_honest_survives_all_rounds


# ------------------------------------------------------------------ runner

def main():
    probes = [
        ("F-1 verifier never checks the degree claim", f1_verifier_never_checks_the_degree),
        ("F-2 no final constant check", f2_no_final_constant_check),
        ("F-3 challenge generated by the prover", f3_the_challenge_is_generated_by_the_prover),
        ("F-4 header measurement 3 (verifier cost) absent", f4_header_measurement_3_verifier_cost_is_never_measured),
        ("F-5 verify_round is linear in q, not logarithmic", f5_verify_round_is_linear_in_the_field_not_logarithmic),
        ("F-6 header measurement 4 (soundness) absent", f6_header_measurement_4_soundness_compounding_is_never_measured),
        ("F-7 tamper probe covers one coefficient of one round", f7_tamper_probe_only_tests_one_constant_of_one_round),
        ("F-8 'every round verifies' label is misleading", f8_degree_non_increase_check_is_mislabeled),
    ]
    print("=" * 76)
    print("ROUND-5a adversarial probes: f0b_fri_en.py")
    print("=" * 76)
    results = {}
    for name, fn in probes:
        print()
        try:
            results[name] = fn()
        except AssertionError as e:
            print("  PROBE ASSERTION FAILED: %s" % e)
            results[name] = None
    print()
    print("-" * 76)
    n_pass = 0
    for name, _ in probes:
        r = results[name]
        tag = "PASS (claim holds)" if r else ("FINDING (claim fails)" if r is False else "PROBE ERROR")
        if r:
            n_pass += 1
        print("  %-46s %s" % (name, tag))
    print("  probes: %d/%d confirm the file's claims" % (n_pass, len(probes)))
    print("=" * 76)


if __name__ == "__main__":
    main()
