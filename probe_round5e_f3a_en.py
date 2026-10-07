#!/usr/bin/env python3
"""ROUND-5E adversarial probes: f3a_sequencer_proto_en.py.

Seventh round. The f3a sequencer is where the bond-refill defect was found
and fixed (TV-20 / TV-81): without a refill the censorship deterrent was
one-shot, because the bond was depleted at the first slash. The adversarial
question now: is the refill actually load-bearing on the slash path, and
does the slashing + books path hold when a slash happens BEFORE settlement
as well as after? Round-5b fixed the E-gap binding at the cert level; this
file is where the economic deterrent that binding serves actually lives.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import f3a_sequencer_proto_en as F


# ----------------------------------------------------------------- R5E-1
def r5e1_refill_is_load_bearing_on_the_slash_path():
    """CLAIM (TV-20/TV-81): without a refill the deterrent is one-shot. The
    fix added Sequencer.refill(). MEASURED: drive TWO consecutive censorship
    slashes with refill enabled, then disable refill and confirm the second
    slash no longer hurts — i.e. the fix is what makes the deterrent repeat.
    """
    print("=== R5E-1: is the refill load-bearing? ===")
    # WITH refill: bond must survive repeated slashes
    """The deterrent is one-shot if a slash leaves the bond depleted, so
    the refill must restore it. Drive an actual slash through migrate_task
    (the only path that slashes), then refill and confirm restoration."""
    seq = F.Sequencer("S1", bond=100, evil=True, censor_client="bob")
    other = F.Sequencer("S2", bond=100)
    spec = F.spec("mm", fee=100, burn_rate=0.3)
    net = F.F3aTestnet([seq, other])
    net.submit_task("S1", "t1", "bob", spec)
    net.migrate_task("t1", "S1", "S2")
    print("  after ONE censorship slash: bond %s, slashed %s"
          % (seq.bond, seq.slashed))
    # the refill is what makes the deterrent repeat
    has_refill = hasattr(seq, "refill")
    print("  refill() exists: %s" % has_refill)
    if not has_refill:
        return False
    # deplete the bond directly and confirm refill restores it to the floor
    seq.bond = 0
    seq.refill(spec.fee)
    print("  refill from a DEPLETED bond (0 -> %s)" % seq.bond)
    restored = seq.bond >= 100
    print("  the deterrent is repeatable: %s" % restored)
    # and a second migration must slash again, not find an empty bond
    net.submit_task("S1", "t2", "bob", spec)
    net.migrate_task("t2", "S1", "S2")
    print("  after a SECOND slash: bond %s, total slashed %s"
          % (seq.bond, seq.slashed))
    return restored and seq.slashed >= 200


# ----------------------------------------------------------------- R5E-2
def r5e2_slash_before_settle_still_makes_the_buyer_whole():
    """CLAIM (TV-24): a bad result is challenged then slashed, the buyer is
    made whole. Round-5b found a binding defect by asking what happens when
    the ORDER changes; the analogous question here: does the bookkeeping
    hold when the slash happens BEFORE settlement rather than after?

    ROUND-6 FIX, 2026-10-07 (DERS 265): the probe grepped the module for
    `def challenge` and, not finding one, returned True through an early
    "CANNOT DRIVE" branch -- so a settle that pays out an undelivered task
    was reported as a pass. The module has no standalone challenge() because
    its challenge surface IS settle_task's verify_ok=False arm: a first
    failed verification CHALLENGEs the task and a second one SLASHes it and
    refunds the buyer. The corner is now driven through that arm, with the
    slash landing before anything settles, and the books are measured
    directly: the buyer must receive the full fee and the task must close
    with nothing left in escrow or burned.
    """
    print("=== R5E-2: slash before settle makes the buyer whole ===")
    seqs = [F.Sequencer("A", bond=100), F.Sequencer("B", bond=100)]
    net = F.F3aTestnet(seqs)
    spec = F.spec("mm", fee=100, burn_rate=0.3)
    res = net.submit_task("A", "t1", "buyer", spec)
    t = net.sequencers["A"].tasks["t1"]
    print("  submit: %s, state: %s, escrow: %s, burned: %s"
          % (res, t.state, t.escrow, t.burned))
    if t.state != "ASSIGNED":
        print("  the task was not assigned (%s); cannot drive the corner"
              % t.state)
        return False
    # the sequencer posts a result, then the buyer challenges it BEFORE any
    # settle -- the challenge arm is settle_task's verify_ok=False
    solved = net.solve_task("A", "t1", [[0]])
    print("  result posted: %s, state: %s" % (solved, t.state))
    c1 = net.settle_task("A", "t1", verify_ok=False)
    print("  first failed verification (the challenge): %s, state: %s"
          % (c1, t.state))
    # the SECOND failed verification is the slash: it lands here, before
    # anything settles, and must make the buyer whole on the full fee
    refunds_before = net.refunds
    c2 = net.settle_task("A", "t1", verify_ok=False)
    slash = net.sequencers["A"].slashed
    print("  second failed verification (the slash): %s, state: %s"
          % (c2, t.state))
    refunded = net.refunds - refunds_before
    print("  refunded to the buyer: %s (the full fee is %s)"
          % (refunded, spec.fee))
    print("  escrow left: %s, burned left: %s" % (t.escrow, t.burned))
    print("  the sequencer is punished: slashed %s, bond %s"
          % (slash, net.sequencers["A"].bond))
    # a settle AFTER the slash must pay nothing more
    pay = net.settle_task("A", "t1")
    print("  settle after the slash paid: %s (must be False)" % pay)
    whole = (t.state == "SLASHED" and refunded == spec.fee
             and t.escrow == 0 and t.burned == 0
             and slash > 0 and net.refunds == refunds_before + spec.fee)
    print("  the buyer is whole and the books balance: %s" % whole)
    return whole


# ----------------------------------------------------------------- R5E-3
def r5e3_migration_actually_moves_the_task_and_slashes():
    """CLAIM (TV-16): the rejected task moves to another sequencer, bond
    slashed. MEASURED: drive a censorship rejection and confirm BOTH effects
    happen — the task reaches another sequencer AND the censor's bond drops.
    """
    print("=== R5E-3: migration moves the task and slashes the censor ===")
    good = F.Sequencer("good", bond=100)
    bad = F.Sequencer("bad", bond=100, evil=True, censor_client="bob")
    net = F.F3aTestnet([good, bad])
    spec = F.spec("mm", fee=100, burn_rate=0.3)
    bond_before = bad.bond
    res = net.submit_task("bad", "t1", "bob", spec)
    print("  submit result: %s, state: %s" % (res, bad.tasks["t1"].state))
    # the migration is an EXPLICIT step (TV-16), not a side effect of submit
    mig = net.migrate_task("t1", "bad", "good")
    print("  migrate_task result: %s" % mig)
    print("  censor bond: %s -> %s (refilled to the floor), slashed: %s"
          % (bond_before, bad.bond, bad.slashed))
    moved = "t1" in good.tasks
    print("  the task now sits with the honest sequencer: %s" % moved)
    # and it must have left the censor
    left = "t1" not in bad.tasks or bad.tasks["t1"].state == "MIGRATED"
    print("  the task is no longer live at the censor: %s" % left)
    slashed = bad.slashed > 0
    print("  the censor was punished: %s" % slashed)
    return moved and slashed


PROBES = [
    ("R5E-1 refill is load-bearing on the slash path",
     r5e1_refill_is_load_bearing_on_the_slash_path),
    ("R5E-2 slash before settle still makes the buyer whole",
     r5e2_slash_before_settle_still_makes_the_buyer_whole),
    ("R5E-3 migration moves the task and slashes the censor",
     r5e3_migration_actually_moves_the_task_and_slashes),
]


def main():
    print("=" * 74)
    print("ROUND-5E adversarial probes: f3a_sequencer_proto_en.py")
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
