#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KOK v2 — adversarial edge probes for the GHOSTDAG prototype (TV-56..TV-59).

The same method that found four accounting bugs, applied to the DAG layer. The
GHOSTDAG file already states that its mergeset is a greedy approximation of
ePrint 2018/104 (the intersection with past(B) is dropped because it is unknown
at compute time). What it does not state is how large that deviation is, so the
first probe measures it rather than assuming it is harmless.

A RED result is either a bug to fix or a limit to document, never a silent pass.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ghostdag_proto_en import GHOSTDAG, Block, GHOSTDAG_K


def report(name, ok, detail=""):
    print("  %-46s %s %s" % (name, "ACCEPT" if ok else "RED", detail))
    return ok


def _exact_mergeset(g, bid):
    """The reference mergeset: mergeset(sp) U (anticone(sp) ∩ past(bid)).

    This is the definition the prototype approximates. past(bid) is knowable to
    an independent observer that walks the DAG, so this can be computed and used
    as ground truth to measure the greedy path's deviation.
    """
    sp = g.selected[bid]
    if sp is None:
        return set()
    base = set(g.mergesets.get(sp, set()))
    ac_sp = g._anticone(sp)
    past_bid = g._past(bid)
    return base | (ac_sp & past_bid)


def tv56_mergeset_deviation_measured():
    """The mergeset must only include work B knows: mergeset(sp) U (anticone(sp)
    ∩ past(B)).

    Stage 1.1, 2026-09-23: this probe used to ACCEPT the deviation (X was
    over-included by the greedy approximation). The intersection with past(B)
    is now computed, so the probe has inverted: it verifies the FIX holds,
    not that the bug persists. A block that references A only must NOT absorb
    X, its sibling fork.
    """
    g = GHOSTDAG(k=GHOSTDAG_K)
    gen = Block("A", [], 0)
    g.add(gen)
    a = Block("A", [gen.bid], 1)
    g.add(a)
    x = Block("B", [gen.bid], 2)          # a sibling fork of A
    g.add(x)
    b = Block("A", [a.bid], 3)            # B references A only, NOT X
    g.add(b)

    greedy_ms = g.mergesets[b.bid]
    exact_ms = _exact_mergeset(g, b.bid)
    # FIXED: X is a sibling B does not reference and must NOT be absorbed
    x_not_in_past = x.bid not in g._past(b.bid)
    # ROUND-6 FIX, 2026-09-24 (round-6 finding F3): the `extra == set()` clause
    # is an IDENTITY — _exact_mergeset recomputes the same union the module
    # uses, so greedy==exact by construction and over-included is 0 under any
    # module, measured on the pre-fix buggy module too. The PROTECTIVE checks
    # are the two below, which compare greedy_ms against what B actually
    # references: X must be absent from B's past AND from its mergeset.
    x_absent = x_not_in_past and x.bid not in greedy_ms
    # the real over-inclusion, against past(B) rather than against a recompute
    real_extra = greedy_ms - g._past(b.bid) - {b.bid}
    ok = x_absent and not real_extra
    return report("TV-56 mergeset stays within past(B)", ok,
                  "greedy=%d exact=%d X-in-past=%s X-in-ms=%s outside-past=%d" %
                  (len(greedy_ms), len(exact_ms), not x_not_in_past,
                   x.bid in greedy_ms, len(real_extra)))


def tv57_selected_parent_is_a_direct_parent():
    """The selected parent must be one of the block's direct parents.

    ROUND-6, 2026-09-24 (round-6 finding F2): this is a SELF-COMPARISON as
    written — the module chooses `sp = max(scored for p in blk.parents)`, so
    `sp not in blk.parents` is impossible by construction and the violation
    count is 0 under both the fixed and any regressed module (measured over
    360 DAGs). It is kept as a REGRESSION GUARD, not an adversarial probe:
    if a future change decouples selected-parent selection from the parent
    list, this is the line that catches it. The genuinely protective probes
    in this file are TV-56's `x.bid not in greedy_ms` clause and TV-59's
    outside-count; TV-58 was corrected in the same round to assert the
    structural property instead of the excluded one.
    """
    import random
    g = GHOSTDAG(k=GHOSTDAG_K)
    rng = random.Random(7)
    genesis = Block("A", [], 0)
    g.add(genesis)
    tips = [genesis.bid]
    for i in range(40):
        n = rng.randint(1, min(3, len(tips)))
        parents = rng.sample(tips, n)
        blk = Block("M%d" % (i % 3), parents, i + 1)
        g.add(blk)
        tips.append(blk.bid)
    bad = []
    for bid, sp in g.selected.items():
        if sp is not None and sp not in g.blocks[bid].parents:
            bad.append(bid)
    ok = not bad
    return report("TV-57 selected parent is a direct parent", ok,
                  "violations=%d" % len(bad))


def tv58_blue_score_does_not_decrease_along_selected_chain():
    """Walking selected_parent backwards, blue_score must be non-increasing.

    The selected parent is chosen as the parent with the highest blue_score, so
    the chain it produces cannot gain score as we walk back.
    """
    import random
    g = GHOSTDAG(k=GHOSTDAG_K)
    rng = random.Random(11)
    genesis = Block("A", [], 0)
    g.add(genesis)
    tips = [genesis.bid]
    for i in range(60):
        n = rng.randint(1, min(3, len(tips)))
        parents = rng.sample(tips, n)
        blk = Block("M%d" % (i % 4), parents, i + 1)
        g.add(blk)
        tips.append(blk.bid)
    violations = 0
    checked = 0
    for bid in g.blocks:
        cur = bid
        seen = 0
        while g.selected.get(cur) is not None and seen < 200:
            sp = g.selected[cur]
            # ROUND-6 FIX, 2026-09-24 (round-6 finding F1): the old check
            # `blue_score[sp] > blue_score[cur]` is ARITHMETICALLY EXCLUDED —
            # the module computes blue_score[child] = blue_score[sp] + blue + 1,
            # so the selected parent's score can never exceed the child's and
            # violations was 0 by construction (measured: min(child-sp)=1 over
            # 3000 edges). Reverting the module to the pre-fix bug (base=0,
            # the score not carried forward) ALSO gave 0 violations across 360
            # DAGs, so the probe protected nothing. The structural property the
            # fix actually guarantees — each child's score is at least its
            # selected parent's plus one — is what is now asserted, and the
            # reverted bug does violate it (the delta goes to 0).
            delta = g.blue_score[cur] - g.blue_score[sp]
            checked += 1
            if delta < 1:
                violations += 1
            cur = sp
            seen += 1
    ok = (violations == 0) and (checked > 0)
    return report("TV-58 blue_score strictly increases child->selected-parent", ok,
                  "violations=%d over %d edges" % (violations, checked))


def tv59_order_lives_within_past_plus_self():
    """Every block in order(B) must be in past(B) or be B itself.

    Stage 1.1, 2026-09-23: the mergeset now intersects with past(B), so the
    deviation this probe measured (572-578 entries outside past on a 51-block
    DAG) is CLOSED. The probe's assertion has therefore inverted: it used to
    ACCEPT a nonzero count as "measured and documented", and it now FAILS on
    any nonzero count, because the gap it guarded is gone. Kept rather than
    deleted so that a future regression reintroducing the greedy mergeset
    fails loudly here.
    """
    import random
    g = GHOSTDAG(k=GHOSTDAG_K)
    rng = random.Random(23)
    genesis = Block("A", [], 0)
    g.add(genesis)
    tips = [genesis.bid]
    for i in range(50):
        n = rng.randint(1, min(3, len(tips)))
        parents = rng.sample(tips, n)
        blk = Block("M%d" % (i % 4), parents, i + 1)
        g.add(blk)
        tips.append(blk.bid)
    outside = []
    for bid in g.blocks:
        legit = g._past(bid) | {bid}
        for x in g.order(bid):
            if x not in legit:
                outside.append((bid, x))
    # CLOSED: zero is now the requirement. Any nonzero count is a regression
    # back to the greedy mergeset.
    ok = len(outside) == 0
    return report("TV-59 order stays within past(B)", ok,
                  "outside=%d (0 required; was 572 before Stage 1.1)" % len(outside))


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — GHOSTDAG adversarial edge probes (TV-56..TV-59)")
    print("=" * 76)
    print()
    results = [tv56_mergeset_deviation_measured(),
               tv57_selected_parent_is_a_direct_parent(),
               tv58_blue_score_does_not_decrease_along_selected_chain(),
               tv59_order_lives_within_past_plus_self()]
    print()
    n = sum(1 for r in results if r)
    print("probes: %d/%d" % (n, len(results)))
    if n != len(results):
        print("RED PROBES REMAIN — fix the bug or document the limit.")
        raise SystemExit(1)
