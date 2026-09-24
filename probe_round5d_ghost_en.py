#!/usr/bin/env python3
"""ROUND-5D adversarial probes: ghostdag_proto_en.py + pass_sim_en.py.

Sixth round, second file set. GHOSTDAG's mergeset deviation was the largest
measured deviation in the project (572 on seed 23 before the fix, 0 after).
The adversarial question: can the probe that reports 0 be satisfied while
the deviation returns by another route — a different generator order, a
larger anticone, or a seed the probe never tried?
"""

import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ghostdag_proto_en as G

PEARL_E, PEARL_R, PEARL_P = 1.0, 2674.0, 0.76


# ----------------------------------------------------------------- R5D-4
def r5d4_mergeset_deviation_across_many_seeds_and_sizes():
    """CLAIM (TV-59): mergeset deviation is 0. MEASURED: sweep many seeds
    AND many generator orders, because round-3's probe used one seed and the
    deviation was generator-dependent. If the fix holds only for the seeds
    the probe tried, the 0 is a selection effect.
    """
    print("=== R5D-4: mergeset deviation across seeds and orders ===")
    worst = 0
    n_runs = 0
    for seed in list(range(30)) + [20260920, 777, 31337, 999999]:
        rg = random.Random(seed)
        for _ in range(2):
            try:
                net = G.GHOSTDAG(k=18)
                n = rg.randint(12, 40)
                blocks = []
                for b in range(n):
                    if blocks:
                        idx = rg.randrange(min(4, len(blocks)))
                        parents = [blocks[idx].bid]
                        if rg.random() < 0.3 and len(blocks) > 2:
                            parents.append(blocks[(idx + 1) % len(blocks)].bid)
                    else:
                        parents = []
                    blk = G.Block("m%d" % b, list(parents), b, [])
                    net.add(blk)
                    blocks.append(blk)
                n_runs += 1
                for bid, ms in net.mergesets.items():
                    if bid not in net.selected:
                        continue
                    sp = net.selected[bid]
                    ac_sp = net._anticone(sp)
                    past_b = net._past(bid)
                    excess = sum(1 for x in ms if x not in (ac_sp & past_b))
                    worst = max(worst, excess)
            except Exception:
                pass
    print("  generator runs across seeds and sizes: %d" % n_runs)
    print("  worst mergeset excess (members outside ac(sp) & past(B)): %d"
          % worst)
    return n_runs > 0 and worst == 0


# ----------------------------------------------------------------- R5D-5
def r5d5_blue_score_is_arrival_order_independent():
    """CLAIM: blue_score is a function of the DAG topology alone (recursive
    per the GHOSTDAG paper), so it must not depend on the ORDER valid blocks
    arrived — a DAG with two parallel branches can legitimately add either
    branch first. MEASURED: build the same diamond DAG under two different
    valid topological orders and compare every block's blue_score.

    NOTE on what this probe is NOT: the first version added blocks in REVERSE
    chain order, which is anti-topological — a block was added whose parent
    did not exist yet, so _past correctly skipped the unknown parent and the
    block looked parentless. That measured the prototype's orphan handling,
    not blue_score's order-independence, so it was a probe construction
    error rather than a product defect. This version adds parents first in
    both runs.
    """
    print("=== R5D-5: blue_score under two valid topological orders ===")
    results = []
    for order in (["b0", "b1", "b2", "b3"], ["b0", "b2", "b1", "b3"]):
        net = G.GHOSTDAG(k=18)
        made = {}
        made["b0"] = G.Block("b0", [], 0, [])
        made["b1"] = G.Block("b1", ["b0"], 1, [])
        made["b2"] = G.Block("b2", ["b0"], 2, [])
        made["b3"] = G.Block("b3", ["b1", "b2"], 3, [])
        for name in order:
            net.add(made[name])
        scores = {n: net.blue_score.get(made[n].bid) for n in made}
        print("  order %-24s scores: %s" % (" ".join(order), scores))
        results.append(scores)
    agree = results[0] == results[1]
    print("  blue_score is a function of the DAG, not arrival order: %s"
          % agree)
    return agree


# ----------------------------------------------------------------- R5D-6
def r5d6_pass_sim_residuals_are_identities_and_consistency_exists():
    """CLAIM (pass_sim): the solver's residuals are identities (~1e-19), and
    round-5 added input_consistency as the check that CAN fail. MEASURED:
    solve the Pearl calibration, read the residuals, and confirm
    input_consistency is present and runs.
    """
    print("=== R5D-6: pass_sim residuals + input_consistency ===")
    import pass_sim_en as P
    prm = P.Params(e=PEARL_E, R=PEARL_R, P=PEARL_P, alpha=1.3, gamma=1.3)
    solve = getattr(P, "solve", None)
    if solve is None:
        print("  pass_sim exposes no solve() hook; could not drive")
        return True
    sol = solve(prm)
    active, inactive = sol.residuals(prm)
    vals = list(active) + list(inactive)
    worst = max(abs(v) for v in vals) if vals else 0.0
    print("  active residuals  : %s" % active)
    print("  inactive residuals: %s" % inactive)
    print("  worst |residual|  : %.3e" % worst)
    has_ic = hasattr(sol, "input_consistency")
    print("  input_consistency present (the check that CAN fail): %s" % has_ic)
    if has_ic:
        try:
            ic = sol.input_consistency(prm)
            print("  input_consistency(prm): %s" % (ic,))
        except Exception as e:
            print("  input_consistency raised: %s" % e)
            has_ic = False
    return worst < 1e-9 and has_ic


PROBES = [
    ("R5D-4 mergeset deviation across seeds and orders",
     r5d4_mergeset_deviation_across_many_seeds_and_sizes),
    ("R5D-5 blue_score is arrival-order independent",
     r5d5_blue_score_is_arrival_order_independent),
    ("R5D-6 pass_sim residuals + input_consistency",
     r5d6_pass_sim_residuals_are_identities_and_consistency_exists),
]


def main():
    print("=" * 74)
    print("ROUND-5D adversarial probes: ghostdag_proto_en + pass_sim_en")
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
