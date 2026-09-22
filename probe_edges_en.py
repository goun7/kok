"""KOK v2 — adversarial edge-case probes for the F3a sequencer prototype.

These are deliberately NOT the named TV tests. The TV tests check that the
mechanism does what the spec says. These probes try to provoke the state machine
into places the spec is quiet about, and they exist because all three real f3a bugs
found in this pass (the terminal-state recount, the dead migrated_tasks counter,
and the stranded burn on timeout refund) were found by running the machine rather
than by reading it.

Each probe returns True if the behaviour is correct. A probe returning False is
either a bug to fix or a limit to document; the harness does not decide which.

TV-45..TV-49 are the probe numbers, kept separate from the TV range so that a
failure here reads as "something the spec did not consider" rather than "a spec
requirement failed".
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from f3a_sequencer_proto_en import (Sequencer, F3aTestnet, spec, H, W_R,
                                    DemandMeter)


def report(name, ok, detail=""):
    print("  %-46s %s %s" % (name, "ACCEPT" if ok else "RED", detail))
    return ok


def tv45_challenged_then_repaired():
    """A CHALLENGED task that is then repaired must SETTLE, not stick.

    Spec A.5.2 gives one repair chance: the first failed verify challenges, and
    a correct result afterwards should settle and burn. A task that can never
    leave CHALLENGED would strand the escrow forever.
    """
    net = F3aTestnet([Sequencer("A", bond=100)])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", s)
    net.solve_task("A", "t1", "res1")
    net.settle_task("A", "t1", verify_ok=False)
    st1 = net.sequencers["A"].tasks["t1"].state
    net.settle_task("A", "t1", verify_ok=True)
    st2 = net.sequencers["A"].tasks["t1"].state
    m = DemandMeter()
    net.next_block()
    m.record_block(net)
    ok = (st1 == "CHALLENGED" and st2 == "SETTLED" and m.paid_tasks == 1)
    return report("TV-45 challenged-then-repaired settles", ok,
                  "ch=%s rep=%s paid=%d" % (st1, st2, m.paid_tasks))


def tv46_partial_slash_makes_buyer_whole():
    """With bond < fee the slash is partial; the buyer must still be whole.

    The slash is min(bond, fee), so a low-bond sequencer cannot cover the fee.
    Nothing was delivered, so the buyer is owed the full fee regardless, and the
    shortfall cannot come out of the escrow alone once the burn is included.
    """
    net = F3aTestnet([Sequencer("A", bond=30)])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", s)
    net.solve_task("A", "t1", "res")
    net.settle_task("A", "t1", verify_ok=False)
    net.settle_task("A", "t1", verify_ok=False)
    t = net.sequencers["A"].tasks["t1"]
    ok = (t.state == "SLASHED" and net.refunds == 100
          and net.sequencers["A"].slashed == 30)
    return report("TV-46 partial slash, buyer whole", ok,
                  "state=%s refund=%d slashed=%d"
                  % (t.state, net.refunds, net.sequencers["A"].slashed))


def tv47_double_settle_is_noop():
    """Re-settling a SETTLED task must not double-count the burn.
    """
    net = F3aTestnet([Sequencer("A", bond=100)])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", s)
    net.solve_task("A", "t1", "res")
    net.settle_task("A", "t1", verify_ok=True)
    before = net.burn_address
    again = net.settle_task("A", "t1", verify_ok=True)
    after = net.burn_address
    ok = (after == before and again is False)
    return report("TV-47 double-settle is a no-op", ok,
                  "burn %d -> %d, return %s" % (before, after, again))


def tv48_migrate_noncensored_refused():
    """Migration is only for CENSORED or REJECTED tasks; a SOLVED task stays.
    """
    net = F3aTestnet([Sequencer("A", bond=100), Sequencer("B")])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", s)
    net.solve_task("A", "t1", "res")
    moved = net.migrate_task("t1", "A", "B")
    on_b = "t1" in net.sequencers["B"].tasks
    ok = (moved is False and not on_b)
    return report("TV-48 migrate of non-censored refused", ok,
                  "moved=%s on_B=%s" % (moved, on_b))


def tv49_phi_counts_only_settling_block():
    """A settled task must not inflate phi in the blocks that follow it.

    This is the property TV-22 claims for the honest case; the probe checks the
    arithmetic directly against the meter.
    """
    net = F3aTestnet([Sequencer("A", bond=100)])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", s)
    net.solve_task("A", "t1", "res")
    net.settle_task("A", "t1", verify_ok=True)
    m = DemandMeter()
    for _ in range(10):
        net.next_block()
        m.record_block(net)
    ok = (m.paid_tasks == 1 and m.phi() == 0.1)
    return report("TV-49 phi counts settling block only", ok,
                  "paid=%d blocks=%d phi=%.2f"
                  % (m.paid_tasks, m.total_blocks, m.phi()))


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F3a adversarial edge-case probes (TV-45..TV-49)")
    print("=" * 76)
    print("These probe the corners the spec is quiet about. A RED here means")
    print("either a bug to fix or a limit to document, never a silent pass.")
    print()
    results = [tv45_challenged_then_repaired(),
               tv46_partial_slash_makes_buyer_whole(),
               tv47_double_settle_is_noop(),
               tv48_migrate_noncensored_refused(),
               tv49_phi_counts_only_settling_block()]
    print()
    n = sum(1 for r in results if r)
    print("probes: %d/%d" % (n, len(results)))
    if n != len(results):
        print("RED PROBES REMAIN — fix the bug or document the limit.")
        raise SystemExit(1)
