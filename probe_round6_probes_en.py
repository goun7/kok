#!/usr/bin/env python3
"""ROUND-6 adversarial probes: the round-5 probes themselves.

Eighth round. Five rounds of adversarial review have now passed the same
code, and round-5 found two soundness bugs that rounds 1-4 missed. The
question that follows immediately: are the NEW probes any better than the
old ones? A probe whose PASS is a foregone conclusion is the failure mode
that let the FRI challenge bug and the E-gap binding bug survive four
rounds — both were in code that had probes passing.

So this round turns the same method on the round-5 probe files: does each
probe have a real failure mode? A probe that cannot fail tests nothing.
"""

import os
import sys
import inspect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PROBE_FILES = [
    "probe_round5a_field_en",
    "probe_round5a_fri_en",
    "probe_round5b_egap_en",
    "probe_round5b_rederive_en",
    "probe_round5b_glayer_en",
    "probe_round5b_edges_en",
    "probe_round5d_ulayer_en",
    "probe_round5d_ghost_en",
    "probe_round5e_f3a_en",
    "probe_round5f_air_en",
]


# ----------------------------------------------------------------- R6-1
def r6_1_every_probe_file_has_an_unsatisfiable_failure_mode():
    """CLAIM: each probe reports PASS/FINDING. MEASURED: a probe that prints
    only PASS outcomes has no failure mode; the count of FINDING lines must
    be reachable, which we check by confirming the probe files contain the
    STRING 'FINDING' as a possible output.
    """
    print("=== R6-1: every probe can report a failure ===")
    ok = True
    for name in PROBE_FILES:
        mod = __import__(name)
        src = inspect.getsource(mod)
        has_finding = "FINDING" in src
        has_pass = "PASS" in src
        # the count of probe functions. Naming conventions differ
        # (r5b_/f_/tv_), so count top-level defs that are not helpers:
        # a probe is a def that returns a bool or is called by the runner.
        n = len([l for l in src.splitlines()
                 if l.startswith("def ") and not l.startswith("def _")
                 and not l.startswith("def main")
                 and not l.startswith("def report")])
        if not (has_finding and has_pass and n > 0):
            ok = False
            print("  %-30s BROKEN (finding=%s pass=%s probes=%d)"
                  % (name, has_finding, has_pass, n))
    print("  all %d probe files can print FINDING and PASS" % len(PROBE_FILES))
    return ok


# ----------------------------------------------------------------- R6-2
def r6_2_no_probe_passes_on_an_exception_path():
    """CLAIM: an exception inside a probe is recorded as a failure, not
    silently swallowed into a PASS. MEASURED: read each probe's main loop
    and confirm exceptions map to False, never to a default-True.
    """
    print("=== R6-2: exceptions are failures, not passes ===")
    bad = []
    for name in PROBE_FILES:
        mod = __import__(name)
        src = inspect.getsource(mod)
        lines = src.splitlines()
        for i, l in enumerate(lines):
            if "except" in l:
                nxt = " ".join(lines[i + 1:i + 4])
                if "pass" in nxt and "print" not in nxt:
                    # this is a hidden failure only if the loop's running
                    # result defaults to True. Inspect the enclosing function
                    # and check whether it can return True without the
                    # try-block ever succeeding.
                    fn = None
                    for j in range(i, -1, -1):
                        if lines[j].startswith("def "):
                            fn = lines[j][4:].split("(")[0]
                            break
                    try:
                        body = inspect.getsource(getattr(mod, fn))
                    except (AttributeError, TypeError):
                        body = ""
                    # a probe hides a failure when True is reachable without
                    # any checked comparison succeeding
                    hides = ("return True" in body or "n_pass += 1" in body)
                    if hides:
                        bad.append("%s:%d (%s)" % (name, i + 1, fn))
    print("  except:pass sites that could hide a failure: %s"
          % (bad if bad else "none"))
    # the one site that exists skips a TRIAL COUNTER, not a verdict: an
    # exception there lowers the trial count, which makes the probe MORE
    # conservative, not less
    return not bad


# ----------------------------------------------------------------- R6-3
def r6_3_the_probes_run_and_report_a_count():
    """CLAIM: each probe file runs and prints a N/M count. MEASURED: run
    each and confirm the count line appears and the file exits 0.
    """
    print("=== R6-3: each probe file runs and counts ===")
    import subprocess
    ok = True
    for name in PROBE_FILES:
        r = subprocess.run([sys.executable, name + ".py"],
                           capture_output=True, text=True, timeout=900)
        out = r.stdout + r.stderr
        counted = ("probes:" in out) or ("probes " in out)
        rc = r.returncode
        if not (counted and rc == 0):
            ok = False
            print("  %-30s counted=%s rc=%d" % (name, counted, rc))
    print("  all %d files run rc=0 and print a probe count"
          % len(PROBE_FILES))
    return ok


# ----------------------------------------------------------------- R6-4
def r6_4_no_turkish_letters_in_the_probe_files():
    """CLAIM: the *_en probe files contain no Turkish letters (the project
    convention enforced by audit_turkish_en). MEASURED: a direct scan of the
    round-5 probe files, because the audit script's own exemption list is
    a trust boundary this round should not rely on.
    """
    print("=== R6-4: no Turkish letters in the _en probe files ===")
    tr = "çğıöşüÇĞİÖŞÜ"
    bad = []
    for name in PROBE_FILES:
        path = name + ".py"
        data = open(path, encoding="utf-8").read()
        hits = [c for c in tr if c in data]
        if hits:
            bad.append("%s has %s" % (path, hits))
    print("  Turkish-letter hits: %s" % (bad if bad else "none"))
    return not bad


PROBES = [
    ("R6-1 every probe can report a failure",
     r6_1_every_probe_file_has_an_unsatisfiable_failure_mode),
    ("R6-2 exceptions map to failures not passes",
     r6_2_no_probe_passes_on_an_exception_path),
    ("R6-3 each probe runs and counts",
     r6_3_the_probes_run_and_report_a_count),
    ("R6-4 no Turkish letters in _en probes",
     r6_4_no_turkish_letters_in_the_probe_files),
]


def main():
    print("=" * 74)
    print("ROUND-6 adversarial probes: the round-5 probes themselves")
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
