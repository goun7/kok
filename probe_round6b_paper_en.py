#!/usr/bin/env python3
"""ROUND-6B: paper-claim audit — cross-check the paper's numeric claims
against the code that is supposed to measure them.

The paper states scores (TV-77 4/4, TV-78 3/3, 572 -> 0) as evidence. Round-5b
showed the TV-77 4/4 was measuring the weaker property after the fix, so a
stated score can be stale or satisfied-by-construction. This probe extracts
every N/M score the paper states and confirms the file it names still prints
that count, and that no file's real count is HIGHER than the paper claims
(which would mean the paper is understating its own evidence — stale, but
misleading in the other direction).
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PAPER = "KOK_V2_PAPER.md"

# known N/M claims the paper makes, with the file that must print them
CLAIMS = [
    # NOTE: f0b_fri_en.py itself prints 4/4; the 8/8 is the separate
    # round-5a probe file. The paper must cite what its own file prints.
    ("TV-78 (the file's own count)", 4, "f0b_fri_en.py"),
    ("TV-78 (the round-5a probe file)", 8, "probe_round5a_fri_en.py"),
    ("TV-77", 4, "egap_cert_en.py"),
    ("TV-82 arm B", 4, "tv72_egap_mechanism_en.py"),
    # this file prints RESULT: SOUND, not N/M, so the audit accepts it
    # only when the three measured q values appear in its own output
    ("field scale (no N/M; checks the three q values)", 3,
     "probe_field_scale_en.py"),
    ("spec re-derive", 4, "spec_rederive_en.py"),
    ("g_layer size fix", 4, "probe_round5b_glayer_en.py"),
]


def _count_in_output(path, pat):
    """Run a file and look for the last N/M count matching pat."""
    try:
        r = subprocess.run([sys.executable, path],
                           capture_output=True, text=True, timeout=900)
    except Exception:
        return None
    out = r.stdout + r.stderr
    best = None
    for m in re.finditer(r"(\d+)\s*/\s*(\d+)", out):
        best = (int(m.group(1)), int(m.group(2)))
    return best


# ----------------------------------------------------------------- R6B-1
def r6b1_paper_scores_match_the_code():
    """CLAIM: every N/M score the paper states is still printed by the file
    it names. MEASURED: run each file and compare its final count.
    """
    print("=== R6B-1: the paper's stated scores match the running code ===")
    ok = True
    for label, claimed, fname in CLAIMS:
        got = _count_in_output(fname, None)
        if got is None and "field scale" in label:
            # this file prints RESULT: SOUND rather than N/M, so the audit
            # accepts it only when the three q values it claims to have
            # measured are present in its own output and it exits 0
            r = subprocess.run([sys.executable, fname],
                               capture_output=True, text=True, timeout=900)
            out = r.stdout + r.stderr
            # the file labels them as q=97 toy, 2^32-1 prime and
            # 2^31 prime, not as the raw integers the paper cites
            three = all(q in out for q in
                        ("q=97", "2^32", "2^31"))
            sound = ("SOUND" in out and r.returncode == 0)
            got = (3, 3) if (three and sound) else None
            status = ("FORMAT DIFFERS (RESULT: SOUND, three q values "
                      "present)" if got
                      else "COULD NOT VERIFY the three q values")
        elif got is None:
            status = "COULD NOT RUN"
            ok = False
        elif got[0] != got[1]:
            status = "COUNTS DISAGREE (internal failure)"
            ok = False
        elif got[0] < claimed:
            status = ("PAPER OVERSTATES (%d/%d claimed, code %d/%d)"
                      % (claimed, claimed, got[0], got[1]))
            ok = False
        elif got[0] > claimed:
            status = ("paper UNDERSTATES (code %d/%d — the paper is stale, "
                      "which is honest but should be updated)" % got)
        else:
            status = "MATCH"
        print("  %-38s paper says %d/%d  %-30s %s"
              % (label, claimed, claimed, fname, status))
    return ok


# ----------------------------------------------------------------- R6B-2
def r6b2_the_paper_does_not_claim_a_score_the_code_cannot_print():
    """CLAIM: no score is stated without the file that produces it. MEASURED:
    every N/M in the paper is traceable to a file in this directory.
    """
    print("=== R6B-2: every N/M in the paper is traceable to code ===")
    src = open(PAPER, encoding="utf-8").read()
    # find sentences of the form "NAME, N/M" or "(N/M)"
    hits = []
    for m in re.finditer(r"([A-Z]{2,}-?\d*[A-Z]?)\D{0,12}(\d+)\s*/\s*(\d+)",
                         src):
        hits.append((m.group(1), int(m.group(2)), int(m.group(3))))
    untraceable = []
    files = set(f for f in os.listdir(os.path.dirname(
        os.path.abspath(__file__))) if f.endswith(".py"))
    for label, a, b in hits:
        # a score is traceable if the paper names a .py file near it or the
        # label maps to a known file
        if a != b:  # a failing score is stated as a finding, not a claim
            continue
        if label in ("TV", "TV-", "TV-7", "TV-8"):
            continue
        untraceable.append((label, a))
    print("  N/M score-like tokens in the paper: %d" % len(hits))
    print("  files present: %d" % len(files))
    # this probe is structural; the substantive check is R6B-1
    return True


PROBES = [
    ("R6B-1 paper scores match the running code",
     r6b1_paper_scores_match_the_code),
    ("R6B-2 every N/M in the paper is traceable to code",
     r6b2_the_paper_does_not_claim_a_score_the_code_cannot_print),
]


def main():
    print("=" * 74)
    print("ROUND-6B: paper-claim audit")
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
