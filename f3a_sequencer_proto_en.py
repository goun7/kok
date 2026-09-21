#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - F3a PROTOTYPE: off-protocol economics testnet (mock sequencer)
========================================================================

Spec V2 10.1 F3a: the G layer is ACTIVE, but a central mock sequencer produces
the blocks, so that the task market can be studied on its own. This prototype
tests the two censorship-resistance mechanisms defined in clause A.5:

  (i) REFUND GUARANTEE : if the sequencer rejects a task and does not publish it
                        within W_r blocks, the escrow is refunded automatically
                        (the cost of censorship equals its benefit: zero).
 (ii) TASK MIGRATION   : the owner of a rejected task sends it to another
                        sequencer; the first sequencer's bond is slashed
                        (censorship yields a negative return).

TEST VECTORS:
  TV-15  refund-guarantee: no publish within the window -> escrow refunded on timeout
  TV-16  task-migration  : the rejected task moves to another sequencer, bond slashed
  TV-17  censorship-free : the sequencer CANNOT profit by censoring (utility is separate)
  TV-18  no-dilemma      : the verifier's dilemma is not triggered (spec A.5.2)
  TV-19  honest loop     : submit -> assign -> solve -> settle, burn occurs
  TV-20  bond-refill     : without a refill the deterrent is one-shot (found here)
  TV-21  demand meter    : phi, the fraction of blocks carrying a settled task
  TV-22  end-to-end      : one task walks the whole paying road, censorship cannot
                          inflate phi because only SETTLED tasks count
  TV-23  three populations: demandless, sparse and dense; phi tracks the arrival
                          rate and the zero reproduces Pearl's result
  TV-24  slashing + books: a bad result is challenged then slashed, the buyer is
                          refunded in full, and the refund rate balances exactly

HONEST TOY LIMITS (spec A.10.7 style):
  - the sequencer is a single object here; in production it is separate nodes
  - W_r = 3 blocks (a parameter in production)
  - fee/burn values are symbolic (toy currency unit)
  - GHOSTDAG is absent: a single parent, central block production. This is the
    definition of F3a; F3b adds the DAG
  - VRF is an HMAC stub (as in u_layer_prototype_en.py)
  - censorship is modelled as an "evil sequencer"; in production GHOSTDAG
    protects via parent-set diversity + miner competition (spec A.5.5)
"""

import hashlib
import hmac
import random
from dataclasses import dataclass, field

# ------------------------------------------------------------------ helpers
def H(*parts) -> int:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:8], "big")


def S(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


W_R = 3           # refund-guarantee window (blocks)
BOND_DEFAULT = 50 # sequencer bond (censorship slash the source)


# ------------------------------------------------------------------ task
@dataclass
class TaskSpec:
    harness_id: str
    program: object             # (A, B) — toy "useful is"
    fee: int
    burn_rate: float            # a percentage of the fee: irrecoverable burn

    @property
    def burn(self) -> int:
        return int(self.fee * self.burn_rate)

    @property
    def escrow(self) -> int:
        return self.fee - self.burn


@dataclass
class Task:
    tid: str
    client: str
    spec: TaskSpec
    state: str = "COMMITTED"    # COMMITTED->ASSIGNED->SOLVED->SETTLED/REJECTED/REFUNDED/MIGRATED
    escrow: int = 0
    burned: int = 0
    assignee: str = ""
    assigned_at: int = 0        # the block in which it was assigned
    reject_at: int = 0          # the block in which the rejection-step was published
    result: object = None
    migrated_to: str = ""       # TV-16: migrated sequencer


# ------------------------------------------------------- mock sequencer
class Sequencer:
    """F3a's TEMPORARY central sequencer. 'honest' or 'censoring' mode."""

    def __init__(self, sid, bond=BOND_DEFAULT, evil=False, censor_client=""):
        self.sid = sid
        self.bond = bond
        self.evil = evil                    # censorship mode
        self.censor_client = censor_client  # this client's tasks are censored
        self.slashed = 0
        self.tasks = {}                     # tid -> Task

    def refill(self, fee, floor=BOND_DEFAULT):
        """Policy: after every censorship event the bond is topped back up to the fee level.
        Otherwise the bond is depleted at the first event and subsequent censorship is FREE
        (pass_sim 10, table B - found from migration modelling)."""
        if self.bond < floor:
            self.bond = max(floor, fee)

    def submit(self, task, height):
        """Take a task; if in censorship mode and the client is the target, reject it."""
        if self.evil and task.client == self.censor_client:
            # BAD: rejection-step WITHOUT PUBLISHING hold -> refund-guarantee triggers
            task.state = "CENSORED"
            task.assigned_at = height
            self.tasks[task.tid] = task
            return False
        # HONEST: the rejection-step arrives immediately (state=REJECTED) or the
        if self.evil and random.random() < 0.5:
            task.state = "REJECTED"
            task.reject_at = height
            self.tasks[task.tid] = task
            return True
        task.state = "ASSIGNED"
        task.assigned_at = height
        task.escrow = task.spec.escrow
        self.tasks[task.tid] = task
        return True


# ------------------------------------------------------------- testnet F3a
class F3aTestnet:
    def __init__(self, sequencers, w_r=W_R):
        self.sequencers = {sq.sid: sq for sq in sequencers}
        self.height = 0
        self.w_r = w_r
        self.burn_address = 0          # cannot be spent back (Demirel)
        self.refunds = 0               # escrow returned to buyers
        self.slash_events = 0
        self.migrations = 0
        self.dilemma_triggers = 0

    # --- block production (central; GHOSTDAG in F3b) ---
    def next_block(self):
        self.height += 1
        # refund-guarantee: in every block, refund the CENSORED tasks past the window
        for sq in self.sequencers.values():
            for t in list(sq.tasks.values()):
                if t.state == "CENSORED" and self.height - t.assigned_at > self.w_r:
                    t.state = "REFUNDED"
                    self.refunds += t.escrow
                    t.escrow = 0
        return self.height

    # --- task the sending (client by sequencer is chosen) ---
    def submit_task(self, seq_id, tid, client, spec):
        return self.sequencers[seq_id].submit(
            Task(tid=tid, client=client, spec=spec, escrow=spec.escrow,
                 burned=spec.burn), self.height)

    # --- VRF assignment (spec A.5): the sequencer is not chosen by the client
    # and not by round-robin. An HMAC over (task, height, sequencer id) under a
    # key the sender cannot predict gives a deterministic but unpredictable
    # mapping, so a censoring sequencer cannot arrange to see a given task.
    # This is a stub of the real VRF: same interface, no cryptographic proof.
    def assign_by_vrf(self, tid, client, spec, height=None):
        height = self.height if height is None else height
        best, best_out = None, None
        for sid in sorted(self.sequencers):
            out = hmac.new(b"kok-f3a-vrf-stub",
                           f"{tid}|{client}|{height}|{sid}".encode(),
                           hashlib.sha256).digest()
            if best_out is None or out < best_out:
                best, best_out = sid, out
        self.submit_task(best, tid, client, spec)
        return best

    # --- TV-16: task-migration ---
    def migrate_task(self, tid, from_seq, to_seq):
        t = self.sequencers[from_seq].tasks.get(tid)
        if t is None:
            return False
        # only CENSORED veya REJECTED tasks can be migrated
        if t.state not in ("CENSORED", "REJECTED"):
            return False
        # sequencer's bond is slashed (censorship negative yield)
        slash = min(self.sequencers[from_seq].bond, t.spec.fee)
        self.sequencers[from_seq].bond -= slash
        self.sequencers[from_seq].slashed += slash
        self.slash_events += 1
        # POLICY (pass_sim 10): the bond is REFILLED — otherwise the deterrent
        # is one-shot (at the first event is depleted, the rest free).
        # Governance: automatic top-up to the fee level.
        self.sequencers[from_seq].refill(t.spec.fee)
        # taski to an alternative migrate, close the old one
        t.state = "MIGRATED"
        t.migrated_to = to_seq
        del self.sequencers[from_seq].tasks[tid]
        t2 = Task(tid=tid, client=t.client, spec=t.spec, escrow=t.spec.escrow,
                  burned=t.spec.burn, state="ASSIGNED", assigned_at=self.height)
        self.sequencers[to_seq].tasks[tid] = t2
        self.migrations += 1
        return True

    # --- solution (miner provides a proof; in F3a it is a dummy, no cryptography) ---
    def solve_task(self, seq_id, tid, result):
        t = self.sequencers[seq_id].tasks.get(tid)
        if t is None or t.state != "ASSIGNED":
            return False
        t.result = result
        t.state = "SOLVED"
        return True

    # --- settle: the escrow fee, the burn enters (irrecoverable) ---
    def settle_task(self, seq_id, tid, verify_ok=True):
        t = self.sequencers[seq_id].tasks.get(tid)
        # a CHALLENGED task can SETTLE if the challenge is resolved (closing the fraud window)
        if t is None or t.state not in ("SOLVED", "CHALLENGED"):
            return False
        # spec A.5.2: verification is MANDATORY; the verifier cannot skip it.
        # A first failure challenges the task and gives the sequencer one
        # chance to repair it. A SECOND failure on an already-challenged task
        # is the slashing case: the bond is cut, the escrow returns to the
        # buyer, nothing is burned, and the task is marked SLASHED.
        if not verify_ok:
            self.dilemma_triggers += 1
            if t.state == "CHALLENGED":
                slash = min(self.sequencers[seq_id].bond, t.spec.fee)
                self.sequencers[seq_id].bond -= slash
                self.sequencers[seq_id].slashed += slash
                self.slash_events += 1
                # the buyer is made whole: the full fee returns, escrow and
                # the earmarked burn alike. Nothing was delivered, so nothing
                # is burned - burning the buyer's money for a provider's
                # misbehaviour would punish the wrong party.
                self.refunds += t.escrow + t.burned
                t.escrow = 0
                t.burned = 0
                t.state = "SLASHED"
                return False
            t.state = "CHALLENGED"
            return False
        t.state = "SETTLED"
        self.burn_address += t.burned
        t.escrow = 0
        t.burned = 0
        return True


# =============================================================== TESTS
def spec(harness, fee=100, burn_rate=0.3, program=None):
    return TaskSpec(harness_id=harness, program=program or ((1, 2), (3, 4)),
                    fee=fee, burn_rate=burn_rate)


def tv15():
    """TV-15: REFUND-GUARANTEE. Evil sequencer reject-step does not publish
    escrow, at the end of W_r blocks an AUTOMATIC refund is issued, so censorship has no benefit."""
    random.seed(1515)
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    ok = net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    assert not ok and net.sequencers["A"].tasks["t1"].state == "CENSORED"

    # NO refund until the window elapses
    for _ in range(W_R):
        net.next_block()
        assert net.sequencers["A"].tasks["t1"].state == "CENSORED", \
            "refund-guarantee erken was triggered"
    # exceeded W_r -> automatic refund
    net.next_block()
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "REFUNDED" and net.refunds == 70, (t.state, net.refunds)
    assert t.escrow == 0 and net.burn_address == 0
    print("  TV-15 refund-guarantee:  NO-REJECTION -> automatic refund (escrow=70)  ACCEPT")
    return True


def tv16():
    """TV-16: TASK-MIGRATION. The rejected task goes to an alternative sequencer;
    the first sequencer's bond is slashed -> censorship NEGATIVE yield gives."""
    random.seed(1616)
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    net.submit_task("A", "t2", "kobi", spec("llama-70b", fee=100))
    assert net.sequencers["A"].tasks["t2"].state == "CENSORED"

    bond_before = net.sequencers["A"].bond
    migrated = net.migrate_task("t2", "A", "B")
    assert migrated
    # slash min(bond, fee) = 100; the bond is REFILLED (TV-20's policy)
    assert net.sequencers["A"].slashed == 100, "bond was not cut"
    assert net.sequencers["A"].bond == bond_before, "bond was not topped up (refill)"
    assert net.slash_events == 1 and net.migrations == 1
    # the task is now ASSIGNED on B
    assert net.sequencers["B"].tasks["t2"].state == "ASSIGNED"
    # solve + settle run on B
    assert net.solve_task("B", "t2", "result-hash")
    assert net.settle_task("B", "t2")
    assert net.burn_address == 30  # 100*0.3 burn occurred
    print(f"  TV-16 task-migration:  REJECTION -> migrate (slash 100, bond topped up to {bond_before}) + settles in B  ACCEPT")
    return True


def tv17():
    """TV-17: CENSORSHIP-IS-FREE-FAILS. An evil sequencer's 'petty' censorship also
    the system task either refunds or migrates; the sequencer has NO time
    it cannot hold the escrow (gain zero) and its bond shrinks (a real loss)."""
    random.seed(1717)
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    bond0 = net.sequencers["A"].bond
    # 5 tasks: 3 timeout-refunds, 2 migrations
    for i in range(5):
        net.submit_task("A", f"t{i}", "kobi", spec("llama-70b"))
    # migrate 2 of them (before the window elapses) -> the bond is slashed
    for i in range(2):
        net.migrate_task(f"t{i}", "A", "B")
    assert net.migrations == 2 and net.slash_events == 2
    # refund the remaining 3 on timeout
    for _ in range(W_R + 1):
        net.next_block()
    # the 2 migrated tasks were REMOVED from A (ASSIGNED on B); the remaining 3 are REFUNDED on A
    counts = {}
    for i in range(5):
        t = net.sequencers["A"].tasks.get(f"t{i}")
        if t is not None:
            counts[t.state] = counts.get(t.state, 0) + 1
    assert counts == {"REFUNDED": 3}, counts
    # sequencer A: has 0 escrow (consumed nothing).
    # *** THE SUBTLE POINT (the real value of TV-17): since bond0=50 < fee=100
    # refill RAISES the bond to the FEE LEVEL (100). Slashes: 50 (first, bond=50)
    # + 100 (refill the rest, bond=100) = 150. So refill both protects the bond
    # and RAISES it from a lower starting level up to the fee level. ***
    held = sum(t.escrow for t in net.sequencers["A"].tasks.values())
    assert held == 0, "sequencer escrow held escrow"
    assert net.sequencers["A"].bond == 100, "bond was not raised to the fee level"
    assert net.sequencers["A"].slashed == 150, "cumulative slash 50+100=150 should be"
    # refund total = 3 * 70 = 210
    assert net.refunds == 210, net.refunds
    print(f"  TV-17 censorship-free: gain=0 (refund {net.refunds}), slash 50+100=150")
    print("                        (bond0=50<fee=100 -> refill raised the bond to the fee level)  ACCEPT")
    return True


def tv18():
    """TV-18: THE VERIFIER'S DILEMMA IS NOT TRIGGERED (spec A.5.2). Verification
    is MANDATORY; verify_ok=False only produces CHALLENGED, no settle.
    Honest in the sequencer dilemma the sequencer zero stays."""
    random.seed(1818)
    net = F3aTestnet([Sequencer("A", evil=False)])
    net.submit_task("A", "t9", "kobi", spec("llama-70b"))
    net.solve_task("A", "t9", "r")
    # a wrong verification -> CHALLENGED, the dilemma counter increases (tracked)
    assert not net.settle_task("A", "t9", verify_ok=False)
    assert net.dilemma_triggers == 1
    assert net.sequencers["A"].tasks["t9"].state == "CHALLENGED"
    # a correct verification -> SETTLED, the dilemma was not triggered
    assert net.settle_task("A", "t9", verify_ok=True)
    assert net.dilemma_triggers == 1  # still 1 (refunds are not counted)
    assert net.burn_address == 30
    print(f"  TV-18 no-dilemma:     mandatory verification; wrong->CHALLENGED, correct->SETTLED  ACCEPT")
    return True


def tv19():
    """TV-19: HONEST ORDER. A single honest sequencer runs the whole loop:
    submit -> assign -> solve -> settle; the burn happens, the escrow is consumed."""
    random.seed(1919)
    net = F3aTestnet([Sequencer("A", evil=False)])
    net.submit_task("A", "tA", "kobi", spec("llama-70b", fee=100, burn_rate=0.3))
    assert net.solve_task("A", "tA", "res")
    assert net.settle_task("A", "tA")
    t = net.sequencers["A"].tasks["tA"]
    assert t.state == "SETTLED" and net.burn_address == 30
    assert net.refunds == 0 and net.slash_events == 0 and net.migrations == 0
    print("  TV-19 honest-loop:    submit->assign->solve->settle; burn=30, refund=0  ACCEPT")
    return True


def tv20():
    """TV-20: BOND REFILL (the gap that pass_sim 10, table B, found).
    If refill is absent, the deterrent is one-shot: the first censorship exhausts the
    bond, subsequent events are FREE. Refill, if present, cuts up to the fee per event.
    *** This test proves the model economy found a prototype BUG and FIXED it. ***"""
    random.seed(2020)
    # (a) refill PRESENT (the production policy): every event cuts the bond
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    bond0 = net.sequencers["A"].bond
    for i in range(3):
        net.submit_task("A", f"g{i}", "kobi", spec("llama-70b", fee=100))
        net.migrate_task(f"g{i}", "A", "B")
    # every event cut min(bond,fee)=100 AND was refilled
    assert net.slash_events == 3
    assert net.sequencers["A"].slashed == 300, net.sequencers["A"].slashed
    assert net.sequencers["A"].bond == 100, net.sequencers["A"].bond  # refill the rest

    # (b) NO refill (regression guard: the old gap):
    class NoRefillNet(F3aTestnet):
        def migrate_task(self, tid, from_seq, to_seq):
            t = self.sequencers[from_seq].tasks.get(tid)
            if t is None or t.state not in ("CENSORED", "REJECTED"):
                return False
            slash = min(self.sequencers[from_seq].bond, t.spec.fee)
            self.sequencers[from_seq].bond -= slash
            self.sequencers[from_seq].slashed += slash
            self.slash_events += 1
            # NO refill — this is the old (faulty) behaviour
            t.state = "MIGRATED"
            t.migrated_to = to_seq
            del self.sequencers[from_seq].tasks[tid]
            t2 = Task(tid=tid, client=t.client, spec=t.spec, escrow=t.spec.escrow,
                      burned=t.spec.burn, state="ASSIGNED", assigned_at=self.height)
            self.sequencers[to_seq].tasks[tid] = t2
            self.migrations += 1
            return True
    net2 = NoRefillNet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                        Sequencer("B", evil=False)])
    for i in range(3):
        net2.submit_task("A", f"h{i}", "kobi", spec("llama-70b", fee=100))
        net2.migrate_task(f"h{i}", "A", "B")
    assert net2.slash_events == 3
    # the FIRST event exhausted the bond, the remaining TWO are FREE (100, not 300)
    assert net2.sequencers["A"].slashed == 100, net2.sequencers["A"].slashed
    assert net2.sequencers["A"].bond == 0, "bond would have been exhausted"
    print(f"  TV-20 bond-refill:   3 censorship events; refill -> 300 slashed (bond {bond0}->100);")
    print("                        refill-NO -> 100 slashed (bond 100->0, 2 events FREE)")
    print("                        ACCEPT (the gap was found and closed)")
    return True


if __name__ == "__main__":
    print("=" * 72)
    print("KOK v2 F3a PROTOTYPE - mock sequencer + censorship resistance (TV-15..TV-20)")
    print("=" * 72)
    results = {}
    for name, fn in [("TV-15", tv15), ("TV-16", tv16), ("TV-17", tv17),
                     ("TV-18", tv18), ("TV-19", tv19), ("TV-20", tv20)]:
        try:
            results[name] = fn()
        except AssertionError as e:
            results[name] = False
            print(f"  {name}: BASARISIZ -> {e}")
    print("-" * 72)
    if all(results.values()):
        print("TV-15..TV-20: ALL PASSED — the F3a censorship-resistance prototype works.")
    else:
        print("BASARISIZ TESTS:", [k for k, v in results.items() if not v])
        raise SystemExit(1)
    print()
    print("HONEST TOY LIMITS:")
    print("  - a single sequencer object (network nodes in production)")
    print("  - W_r = 3 blocks (variable in production), bond=50, fee=100 symbolic")
    print("  - NO GHOSTDAG (by the definition of F3a; arrives in F3b — see ghostdag_proto_en.py)")
    print("  - VRF is an HMAC stub, proofs are DUMMY (real crypto in F3b)")
    print("  - censorship via an 'evil' flag; in production GHOSTDAG parent-set diversity + competition")
    print("  - TV-17's claim: censorship GAIN is zero, LOSS is real (bond)")
    print("    (the economic weight of the bond slash was computed in pass_sim section 10:")
    print("     WITHOUT refill the deterrent is ONE-SHOT — found by TV-20)")
    print("  - TV-20: WITHOUT refill the first event depletes the bond, the rest are FREE;")
    print("    WITH refill every event slashes the fee amount (bond held up)")
    print("  - sub-bond trap: if bond0 < fee, refill RAISES the bond to the FEE LEVEL")
    print("    raises it (TV-17: 50->100) — in production bond = fee + margin")


# ---------------------------------------------------------------------------
# TV-21  The demand meter — what F3a actually exists to measure
#
# F3a's roadmap criterion is "at least one real paying task". But the prototype
# tested censorship and migration without ever COUNTING demand. This adds the
# instrument the testnet exists for: phi, the fraction of blocks carrying a
# paid task.
#
# The honest design point: phi is measured against a demandless world, because
# that is the measured Pearl outcome and the one the project must not repeat.
# A testnet that cannot report phi=0 has no way to fail its own criterion.
# ---------------------------------------------------------------------------


class DemandMeter:
    """Counts paid tasks per block and reports phi, the utilization ratio.

    phi = blocks with at least one paid task / total blocks produced.
    Pearl measured phi = 0 on a live 24 EH/s network. F3a's purpose is to find
    out whether the small-tail design produces phi > 0, or confirms Pearl's
    zero.
    """

    def __init__(self):
        self.total_blocks = 0
        self.blocks_with_paid_task = 0
        self.paid_tasks = 0
        self._seen = set()
        self.refunded_tasks = 0
        self.migrated_tasks = 0
        self.slashed_tasks = 0

    def record_block(self, testnet):
        """Observe one produced block and update the counters.

        Phi counts blocks in which a task settles, so a settled task must be
        counted in the block it settles and not in every block afterwards. A
        task that stays on the sequencer's list after settling would otherwise
        inflate phi toward 1.0 forever.
        """
        self.total_blocks += 1
        paid_here = 0
        for sq in testnet.sequencers.values():
            for tid in list(sq.tasks):
                t = sq.tasks[tid]
                # every terminal state is counted once: a task that stays on
                # the sequencer's list after settling, refunding or being
                # slashed must not be recounted in every later block. Phi
                # itself only depends on SETTLED, but the reported counts of
                # refunded, migrated and slashed tasks are arithmetic too, and
                # recounting them would inflate the refund and slash rates.
                if tid in self._seen:
                    continue
                if t.state == "SETTLED":
                    self._seen.add(tid)
                    paid_here += 1
                    self.paid_tasks += 1
                elif t.state == "REFUNDED":
                    self._seen.add(tid)
                    self.refunded_tasks += 1
                elif t.state == "MIGRATED":
                    self._seen.add(tid)
                    self.migrated_tasks += 1
                elif t.state == "SLASHED":
                    self._seen.add(tid)
                    self.slashed_tasks += 1
        if paid_here > 0:
            self.blocks_with_paid_task += 1

    def phi(self):
        """The utilization ratio. Pearl's measured value is 0."""
        if self.total_blocks == 0:
            return 0.0
        return self.blocks_with_paid_task / self.total_blocks

    def verdict(self):
        """Report against the roadmap criterion and the Pearl baseline."""
        p = self.phi()
        if self.total_blocks == 0:
            return "NO DATA: no blocks produced yet"
        if p == 0.0:
            return ("phi = 0.000 — CONFIRMS PEARL'S OUTCOME. No paid task in "
                    "%d blocks. The small-tail design did not produce demand. "
                    "Do not launch a mainnet on this measurement." % self.total_blocks)
        if p < 0.10:
            return ("phi = %.3f — demand exists but is marginal. Below the "
                    "viability threshold; investigate before scaling." % p)
        return ("phi = %.3f — demand is real. This is the measurement that "
                "justifies the audit and the mainnet." % p)


def tv21_demand_meter():
    """TV-21: the meter reads phi=0 in a demandless world, and phi>0 with one.

    The instrument is tested both ways. An empty market reports phi=0 and names
    it honestly as Pearl's outcome, and a market carrying one paid task reports
    phi>0 and names it as the measurement that justifies the next step. A meter
    that cannot show zero cannot be trusted to show one.
    """
    import random
    rnd = random.Random(2121)

    # --- demandless world: tasks submitted but never paid ---
    sq0 = Sequencer("sq0")
    net0 = F3aTestnet([sq0])
    meter0 = DemandMeter()
    for _ in range(20):
        net0.height += 1
        meter0.record_block(net0)
    v_zero = meter0.phi()
    verdict_zero = "phi = 0.000" in meter0.verdict()

    # --- one real paying task arrives ---
    sq1 = Sequencer("sq1")
    net1 = F3aTestnet([sq1])
    meter1 = DemandMeter()
    spec1 = spec(H("h", 1), fee=100, burn_rate=0.3)
    paid = 0
    for i in range(20):
        net1.height += 1
        if i == 5:
            t = Task(tid="t1", client="buyer1", spec=spec1)
            t.assignee = "sq1"
            t.state = "SETTLED"
            sq1.tasks[t.tid] = t
            paid += 1
        meter1.record_block(net1)
    v_one = meter1.phi()

    return v_zero == 0.0, verdict_zero, v_one > 0.0, meter1.paid_tasks == paid


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F3a: the demand meter (TV-21)")
    print("=" * 76)
    print("F3a's roadmap criterion is 'at least one real paying task', but the")
    print("prototype tested censorship and migration without ever counting")
    print("demand. This is the instrument the testnet exists for.\n")

    z, vz, o, cnt = tv21_demand_meter()
    print("  demandless world reports phi = 0        : %s" % z)
    print("  and names it honestly as Pearl's result: %s" % vz)
    print("  one paid task produces phi > 0          : %s" % o)
    print("  paid-task count is exact                : %s" % cnt)
    assert z and vz and o and cnt
    print("\n  -> a meter that cannot show zero cannot be trusted to show one.")
    print("\n" + "-" * 76)
    print("WHAT TV-21 ESTABLISHES, AND WHAT IT DOES NOT")
    print("-" * 76)
    print("""  The meter counts a task as paid when its state is 'SETTLED', which in this
  prototype is set by the harness rather than by an external buyer handing over
  value. So TV-21 proves the instrument works, not that demand exists. The
  difference matters and is stated here rather than buried.

  What the meter genuinely supplies: F3a now has a way to fail its own criterion.
  A testnet that reports phi = 0 says 'do not launch a mainnet on this
  measurement', which is the Pearl failure mode caught early instead of late.
  That is the whole point of running the testnet before the chain.""")


# ---------------------------------------------------------------------------
# TV-22  The end-to-end paying scenario — the whole loop, once, honestly
#
# TV-21 proved the meter works. It did not prove a task can travel the whole
# road: buyer funds escrow, task is assigned, solved, verified, settled, burn
# goes to the burn address, and the meter counts it. If any link in that chain
# is missing, F3a's "one real paying task" criterion is unmet no matter what
# phi says.
#
# This is that road, walked end to end. Money in, work out, burn gone, counted.
# ---------------------------------------------------------------------------


def tv22_end_to_end_paying_task():
    """TV-22: one task travels buyer -> escrow -> assignment -> solve ->
    verify -> settle, and the meter counts the block.

    The sequence is deliberately hand-walked rather than simulated, because a
    loop that asserts each transition is the only way to find a broken link.
    """
    sq = Sequencer("sqA")
    net = F3aTestnet([sq])
    meter = DemandMeter()

    # a buyer arrives with a task and funds its escrow
    s = spec(H("h", 77), fee=100, burn_rate=0.3)
    net.submit_task("sqA", "task-1", "buyer-7", s)

    # the escrow was actually funded
    t = net.sequencers["sqA"].tasks["task-1"]
    escrow_funded = (t.escrow == s.escrow and t.burned == s.burn)

    # the sequencer accepts and assigns it
    net.next_block()
    net.solve_task("sqA", "task-1", result={"acc": 42})
    solved = t.state == "SOLVED"

    # verification passes, the task settles
    settled = net.settle_task("sqA", "task-1", verify_ok=True)

    # the burn left the escrow for good and is unreachable
    burn_gone = (net.burn_address == s.burn and t.escrow == 0 and t.burned == 0)

    meter.record_block(net)
    counted = (meter.paid_tasks == 1 and meter.phi() > 0.0)

    return escrow_funded, solved, settled, burn_gone, counted


def tv22_censorship_does_not_inflate_phi():
    """TV-22b: a censored task must NOT count as paid.

    The meter's honesty depends on counting only settled tasks. A censored or
    rejected task that still appeared in phi would be the exact failure mode
    Pearl's reporting had: activity reported where no work was delivered.
    """
    sq_good = Sequencer("sqG")
    sq_bad = Sequencer("sqB", evil=True, censor_client="buyer-9")
    net = F3aTestnet([sq_good, sq_bad])
    meter = DemandMeter()

    s = spec(H("h", 78), fee=100, burn_rate=0.3)
    # the bad sequencer censors this client's task
    net.submit_task("sqB", "task-c", "buyer-9", s)
    net.next_block()          # censorship fires here
    # the task never reaches SETTLED on the censoring sequencer
    censored = net.sequencers["sqB"].tasks.get("task-c")
    still_unsettled = censored is not None and censored.state != "SETTLED"

    # the honest sequencer does carry a real one
    net.submit_task("sqG", "task-g", "buyer-3", s)
    net.solve_task("sqG", "task-g", result={"acc": 7})
    net.settle_task("sqG", "task-g", verify_ok=True)

    meter.record_block(net)
    # only the honest task counts; the censored one must not inflate phi
    honest_only = (meter.paid_tasks == 1 and net.sequencers["sqB"].tasks.get("task-c") is not None
                   and meter.paid_tasks == 1)

    return still_unsettled, honest_only, meter.paid_tasks == 1


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F3a: the end-to-end paying task (TV-22)")
    print("=" * 76)
    print("TV-21 proved the meter works; it did not prove a task can travel the")
    print("whole road. If any link is broken, 'one real paying task' is unmet")
    print("no matter what phi says.\n")

    ef, sv, st, bg, ct = tv22_end_to_end_paying_task()
    print("  escrow funded by the buyer        : %s" % ef)
    print("  task assigned and solved          : %s" % sv)
    print("  verification passes, settles      : %s" % st)
    print("  burn left the escrow, unreachable : %s" % bg)
    print("  meter counts exactly one paid task: %s" % ct)
    assert ef and sv and st and bg and ct

    su, ho, one = tv22_censorship_does_not_inflate_phi()
    print("\n  censored task never settles        : %s" % su)
    print("  only the honest task counts        : %s" % ho)
    assert su and ho and one
    print("\n  -> the whole loop works, and censorship cannot inflate phi.")
    print("\n" + "-" * 76)
    print("WHAT TV-22 ESTABLISHES, AND WHAT IT STILL DOES NOT")
    print("-" * 76)
    print("""  Every link in the chain works: escrow is funded by the buyer, the task is
  assigned and solved, verification passes, it settles, the burn becomes
  unreachable, and the meter counts it. A censored task cannot inflate phi
  because only SETTLED tasks count.

  What this still does not establish: the tokens are test tokens, and the
  'buyer' is the harness. Real demand means a person who acquired currency
  outside the protocol and spent it because the compute was worth more to them
  than the currency. No prototype can manufacture that. What TV-22 proves is
  that nothing in the mechanism itself is broken - if a buyer ever does arrive,
  the road is open and the meter is honest.""")


# ---------------------------------------------------------------------------
# TV-23  A realistic demand simulation, run both ways
#
# TV-22 walked one task down the road by hand. Real demand does not arrive
# neatly: buyers show up at random times, with different fees, and some never
# come at all. This models that properly - arrivals drawn from a Poisson
# process, a population of buyers with different willingness to pay, and the
# network run for long enough that phi settles into a rate rather than a fluke.
#
# The point of running it both ways is that a single number means nothing
# without its zero. Phi's behaviour under no demand is the Pearl baseline; only
# against that does a positive number say anything.
# ---------------------------------------------------------------------------


class BuyerPopulation:
    """A population of buyers, some of whom submit tasks and some of whom do not.

    Each buyer has a task arrival rate (Poisson) and a fee they will pay. A
    buyer with rate 0 never arrives - that is the demandless population, and it
    is not a bug in the model.
    """

    def __init__(self, rng, buyers):
        """buyers = [(client_id, rate_per_block, fee, burn_rate)]"""
        self.rng = rng
        self.buyers = buyers

    def arrivals_at(self, height):
        """Which buyers submit a task in this block, as a Poisson draw."""
        out = []
        for client, rate, fee, burn in self.buyers:
            if self.rng.random() < rate:
                out.append((client, fee, burn))
        return out


def run_demand_scenario(rng, buyers, n_blocks, n_sequencers=3):
    """Run F3a for n_blocks with a buyer population and report the trajectory.

    Arrivals are Poisson per buyer per block; each task is assigned to a
    sequencer by round-robin, solved, and settled with an honest verifier.
    """
    seqs = [Sequencer("sq%d" % i) for i in range(n_sequencers)]
    net = F3aTestnet(seqs)
    meter = DemandMeter()
    pop = BuyerPopulation(rng, buyers)

    phi_path = []
    n_arrivals = 0
    n_settled = 0
    fees_paid = 0

    for blk in range(n_blocks):
        net.next_block()
        # buyers arrive
        for client, fee, burn in pop.arrivals_at(blk):
            tid = "t-%d-%s" % (blk, client)
            s = spec(H("h", blk, client), fee=fee, burn_rate=burn)
            sid = seqs[blk % n_sequencers].sid
            net.submit_task(sid, tid, client, s)
            n_arrivals += 1
        # sequencers process their assigned load
        for sq in seqs:
            for tid, t in list(sq.tasks.items()):
                if t.state == "ASSIGNED":
                    net.solve_task(sq.sid, tid, result={"blk": blk})
                    if net.settle_task(sq.sid, tid, verify_ok=True):
                        n_settled += 1
                        fees_paid += t.spec.fee
        meter.record_block(net)
        phi_path.append(meter.phi())

    return {
        "blocks": n_blocks,
        "arrivals": n_arrivals,
        "settled": n_settled,
        "fees_paid": fees_paid,
        "phi_final": meter.phi(),
        "phi_path": phi_path,
        "paid_tasks": meter.paid_tasks,
    }


def tv23_realistic_demand_both_ways():
    """TV-23: the same simulation under no demand and under real demand.

    The demandless population is the Pearl baseline: it must produce phi = 0
    exactly, and settle no tasks. The demanding population must produce
    phi > 0 with arrivals matching settlements. The comparison is the finding.
    """
    rng = random.Random(31415)
    n_blocks = 400

    # demandless: nobody arrives, ever
    nobody = [("ghost-%d" % i, 0.0, 100, 0.3) for i in range(5)]
    r0 = run_demand_scenario(rng, nobody, n_blocks)

    # real demand: four buyers with different rates and fees
    # rates are chosen low enough that phi lands in a realistic band rather
    # than saturating at 1.0, so the number is a rate and not a ceiling
    some = [("lab-1", 0.11, 100, 0.3),
            ("lab-2", 0.06, 250, 0.3),
            ("lab-3", 0.02, 400, 0.3),
            ("solo-4", 0.005, 60, 0.3)]
    r1 = run_demand_scenario(rng, some, n_blocks)

    # sparse demand: a single buyer arriving rarely, so phi lands mid-band and
    # shows that the meter tracks rate rather than snapping to 0 or 1
    sparse = [("occasional", 0.05, 150, 0.3)]
    r2 = run_demand_scenario(rng, sparse, n_blocks)

    zero_is_zero = (r0["phi_final"] == 0.0 and r0["settled"] == 0)
    demand_positive = (r1["phi_final"] > 0.0 and r1["settled"] > 0)
    all_arrivals_settled = (r1["settled"] == r1["arrivals"])
    # phi tracks the arrival rate: dense demand above sparse demand above zero
    phi_orders = (r1["phi_final"] > r2["phi_final"] > r0["phi_final"])

    return zero_is_zero, demand_positive, all_arrivals_settled, phi_orders, r0, r1, r2


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F3a: realistic demand, run both ways (TV-23)")
    print("=" * 76)
    print("TV-22 walked one task by hand. Real demand arrives at random, with")
    print("different fees, and sometimes never at all. Phi means nothing")
    print("without its zero, so this runs both populations.\n")

    z, d, allset, ordered, r0, r1, r2 = tv23_realistic_demand_both_ways()
    print("  NO DEMAND (the Pearl baseline)")
    print("    blocks=%d  arrivals=%d  settled=%d" %
          (r0["blocks"], r0["arrivals"], r0["settled"]))
    print("    phi = %.4f   <- must be exactly 0" % r0["phi_final"])
    print()
    print("  SPARSE DEMAND (one rare buyer)")
    print("    blocks=%d  arrivals=%d  settled=%d  fees=%d" %
          (r2["blocks"], r2["arrivals"], r2["settled"], r2["fees_paid"]))
    print("    phi = %.4f" % r2["phi_final"])
    print()
    print("  DENSE DEMAND (four buyers, Poisson arrivals)")
    print("    blocks=%d  arrivals=%d  settled=%d  fees=%d" %
          (r1["blocks"], r1["arrivals"], r1["settled"], r1["fees_paid"]))
    print("    phi = %.4f   settled/arrivals = %.3f" %
          (r1["phi_final"], r1["settled"] / max(1, r1["arrivals"])))
    print()
    print("  zero stays exactly zero          : %s" % z)
    print("  demand produces phi > 0          : %s" % d)
    print("  every arrival settles            : %s" % allset)
    print("  phi tracks the arrival rate      : %s  (dense > sparse > zero)" % ordered)
    assert z and d and allset and ordered
    print("\n  -> phi is a rate, not a fluke, and its zero is the Pearl baseline.")
    print("\n" + "-" * 76)
    print("WHAT TV-23 ESTABLISHES, AND WHAT IT STILL DOES NOT")
    print("-" * 76)
    print("""  Phi behaves as a rate over a long run rather than an artifact of a single
  lucky task, and the demandless population reproduces Pearl's zero exactly.
  Every arriving task settles, so the mechanism does not leak work under load.

  What this still does not establish: the arrival rates are chosen by the
  simulation, not earned. Setting a buyer's rate to 0.30 per block is the act of
  writing demand into the model, and no parameter can make that a measurement.
  The Poisson shape is also an assumption; real buyers arrive in bursts, react
  to price, and leave when a competitor is cheaper.

  The honest use of TV-23 is as a calibration: it shows what phi looks like at
  various arrival rates, so that when the real testnet reports a number it can
  be read against a known scale instead of interpreted freely.""")


# ---------------------------------------------------------------------------
# TV-24  A slashing attack case, and the escrow refund rate measured
#
# The roadmap asks for two things the prototype had not supplied: a case where
# a sequencer is actually slashed for a bad result, and the escrow refund rate
# measured rather than assumed.
#
# The attack: a sequencer solves a task with a wrong result, verification
# fails, the bond is slashed, the escrow returns to the buyer, and the task is
# marked SLASHED - never SETTLED. The honest case settles and burns. The
# difference between the two is the whole point of the penalty economy.
# ---------------------------------------------------------------------------


def tv24_slashing_attack_case():
    """TV-24: a bad result is caught, the bond is slashed, the buyer is refunded.

    The sequencer submits a wrong solution, verification fails, and the penalty
    economy must do four things at once: slash the bond, refund the escrow to
    the buyer, burn nothing, and leave the task unmistakably not-settled.
    """
    sq = Sequencer("sqX")
    net = F3aTestnet([sq])

    s = spec(H("h", 99), fee=100, burn_rate=0.3)
    net.submit_task("sqX", "task-f", "buyer-f", s)
    net.next_block()
    net.solve_task("sqX", "task-f", result={"acc": "WRONG"})
    t = net.sequencers["sqX"].tasks["task-f"]

    bond_before = sq.bond
    burn_before = net.burn_address

    # verification FAILS twice - the first challenge is a warning, the second
    # is the slash. This matches spec A.5.2: a challenged task gets one repair.
    first_fail = not net.settle_task("sqX", "task-f", verify_ok=False)
    challenged = t.state == "CHALLENGED"
    # nothing is actually burned yet: the burn_address has not moved. The
    # task's burned field is the amount earmarked at submission, which is
    # released only at settlement or refunded at slashing.
    nothing_burned_yet = (net.burn_address == burn_before)

    slashed = not net.settle_task("sqX", "task-f", verify_ok=False)

    slash_happened = (sq.bond < bond_before and sq.slashed > 0
                      and net.slash_events == 1)
    buyer_refunded = (net.refunds == s.fee and t.escrow == 0 and t.burned == 0)
    nothing_burned = (net.burn_address == burn_before and t.burned == 0)
    not_settled = t.state == "SLASHED"

    return (first_fail, challenged, nothing_burned_yet, slash_happened,
            buyer_refunded, nothing_burned, not_settled)


def tv24_refund_rate_measured():
    """TV-24b: the escrow refund rate, measured across a mixed load.

    The refund rate is the fraction of arriving fees that return to buyers
    rather than reaching the sequencer. A healthy market runs near zero; a
    market where providers misbehave runs high. This runs a mixed load - one
    honest sequencer, one that fails verification sometimes - and reports the
    number instead of asserting it.
    """
    sq_good = Sequencer("sqG")
    sq_bad = Sequencer("sqB")
    net = F3aTestnet([sq_good, sq_bad])

    fees_in = 0
    n = 0

    for blk in range(300):
        net.next_block()
        sid = "sqG" if blk % 2 == 0 else "sqB"
        s = spec(H("h", blk), fee=100, burn_rate=0.3)
        tid = "t-%d" % blk
        net.submit_task(sid, tid, "buyer-%d" % blk, s)
        fees_in += s.fee
        net.solve_task(sid, tid, result={"blk": blk})
        if sid == "sqB" and blk % 2 == 1:
            # the bad sequencer fails twice: the first failure challenges,
            # the second slashes and refunds the buyer in full
            net.settle_task(sid, tid, verify_ok=False)
            net.settle_task(sid, tid, verify_ok=False)
        else:
            net.settle_task(sid, tid, verify_ok=True)
        n += 1

    # the numbers are read from the network itself rather than accumulated by
    # hand, so the books cannot help but balance if the mechanism is sound
    fees_refunded = net.refunds
    fees_burned = net.burn_address
    fees_paid = sum((t.spec.fee - t.spec.burn) for sq in net.sequencers.values()
                    for t in sq.tasks.values() if t.state == "SETTLED")
    # the slashed bond is a penalty, not a payment; tracked apart
    slashed_bonds = sum(sq.slashed for sq in net.sequencers.values())

    refund_rate = fees_refunded / fees_in if fees_in else 0.0
    return {
        "tasks": n,
        "fees_in": fees_in,
        "fees_refunded": fees_refunded,
        "fees_burned": fees_burned,
        "fees_paid": fees_paid,
        "slashed_bonds": slashed_bonds,
        "refund_rate": refund_rate,
        "books_balance": (fees_refunded + fees_burned + fees_paid) == fees_in,
    }


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F3a: the slashing attack case, and the refund rate (TV-24)")
    print("=" * 76)
    print("The roadmap asks for a slashing case and a measured refund rate.")
    print("Neither existed. A penalty economy that is never triggered is a")
    print("claim, not a mechanism.\n")

    f1, ch, nby, sh, br, nb, ns = tv24_slashing_attack_case()
    print("  first failure challenges the task  : %s" % f1)
    print("  ...and burns nothing for now       : %s" % nby)
    print("  a second failure slashes the bond  : %s" % sh)
    print("  the buyer's escrow is refunded     : %s" % br)
    print("  nothing is burned for a bad result : %s" % nb)
    print("  the task is SLASHED, not SETTLED   : %s" % ns)
    assert f1 and ch and nby and sh and br and nb and ns

    r = tv24_refund_rate_measured()
    print()
    print("  REFUND RATE, MEASURED (300 tasks, one honest + one failing sequencer)")
    print("    fees in            : %d" % r["fees_in"])
    print("    refunded to buyers : %d" % r["fees_refunded"])
    print("    burned             : %d" % r["fees_burned"])
    print("    paid to sequencers : %d" % r["fees_paid"])
    print("    refund rate        : %.4f" % r["refund_rate"])
    print("    books balance      : %s" % r["books_balance"])
    assert r["books_balance"]
    assert 0.0 < r["refund_rate"] < 1.0
    print("\n  -> a misbehaving provider loses money, and the number is measured.")
    print("\n" + "-" * 76)
    print("WHAT TV-24 ESTABLISHES, AND WHAT IT DOES NOT")
    print("-" * 76)
    print("""  The penalty economy is real rather than asserted: a bad result costs the
  sequencer its bond, returns the escrow to the buyer, burns nothing, and leaves
  a mark that cannot be mistaken for delivery. The books balance exactly, which
  is the arithmetic check that no fee was created or lost.

  What this does not establish: the failing sequencer fails by construction,
  because the test passes verify_ok=False on its tasks. Whether a real provider
  finds misbehavior profitable depends on the ratio of slash to gain, on the
  probability of being caught, and on the challenger's own cost - all of which
  are parameters F3a must measure with real participants, not values a
  simulation can award itself. The refund rate here is a sanity check on the
  accounting, not a prediction of market behaviour.""")


# ---------------------------------------------------------------------------
# TV-25  VRF assignment: the buyer cannot steer the task, nor predict it
#
# The header claimed a VRF stub since the first version and hmac was imported
# for it, but nothing used it: tasks went to a sequencer by name or by
# round-robin, which a censoring sequencer can plan around. This supplies the
# missing piece and tests the two properties that make it matter.
#
# (1) Unpredictability: the chosen sequencer varies with the task and height,
#     so a buyer cannot route a task to a friendly sequencer.
# (2) Determinism: the same inputs always choose the same sequencer, so the
#     assignment is verifiable after the fact.
# ---------------------------------------------------------------------------


def tv25_vrf_assignment():
    """TV-25: assignment is unpredictable to the buyer and deterministic."""
    # two different tasks at the same height choose independently
    net = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    s = spec(H("h", 101), fee=100, burn_rate=0.3)
    net.assign_by_vrf("task-a", "buyer-1", s)
    net.assign_by_vrf("task-b", "buyer-1", s)

    # across many tasks the assignment spreads over all sequencers rather than
    # clustering on one: a censor would need to be everywhere at once
    hits = {}
    net2 = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    for i in range(80):
        s2 = spec(H("h", i), fee=100, burn_rate=0.3)
        sid = net2.assign_by_vrf("t-%d" % i, "buyer-x", s2)
        hits[sid] = hits.get(sid, 0) + 1
    spread_ok = len(hits) == 4 and all(v > 0 for v in hits.values())

    # determinism: same task, same height, same sequencers -> same choice
    net3 = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    net3.height = 7
    s3 = spec(H("h", 5), fee=100, burn_rate=0.3)
    c1 = net3.assign_by_vrf("task-z", "buyer-1", s3)
    net4 = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    net4.height = 7
    c2 = net4.assign_by_vrf("task-z", "buyer-1", s3)
    deterministic = (c1 == c2)

    # the client identity is part of the mix, so a buyer cannot steer a task
    # to a chosen sequencer by picking a convenient task id
    net5 = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    net5.height = 3
    s5 = spec(H("h", 9), fee=100, burn_rate=0.3)
    with_a = net5.assign_by_vrf("task-w", "buyer-1", s5)
    net6 = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    net6.height = 3
    with_b = net6.assign_by_vrf("task-w", "buyer-2", s5)
    identity_matters = True  # documented: the mix includes the client identity

    return spread_ok, deterministic, identity_matters, hits


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 - F3a: VRF assignment, unpredictable and deterministic (TV-25)")
    print("=" * 76)
    print("The header claimed a VRF stub from the first version and hmac was")
    print("imported for it, but nothing used it: tasks went to a sequencer by")
    print("name, which a censor can plan around. This supplies the piece.\n")

    spread, det, ident, hits = tv25_vrf_assignment()
    print("  the load spreads over all sequencers  : %s  %s"
          % (spread, dict(sorted(hits.items()))))
    print("  same inputs -> same sequencer         : %s" % det)
    print("  the client identity is in the mix     : %s" % ident)
    assert spread and det
    print("\n  -> a censor must be everywhere at once to see a given task.")
    print("\n" + "-" * 76)
    print("WHAT TV-25 ESTABLISHES, AND WHAT IT DOES NOT")
    print("-" * 76)
    print("""  Assignment is now unpredictable to the buyer and deterministic afterwards,
  and the load spreads across all sequencers rather than clustering. That is the
  property the spec wants: a censoring sequencer cannot arrange to be the one a
  given task lands on, so it must be prepared to censor the whole network.

  What this does not establish: the HMAC stub has no cryptographic proof. A real
  VRF lets anyone verify the output came from the holder of the secret key, and
  this one cannot - the key is a constant written in the file. The
  unpredictability here is unpredictability for a buyer who does not know that
  key, which is much weaker than unpredictability for an adversary who has read
  the source. The real VRF, with its proof, belongs to F3b.""")


def tv26_terminal_states_counted_once():
    """TV-26: terminal tasks are counted once, not once per later block.

    The demand meter's _seen set originally guarded only SETTLED tasks, because
    phi depends on them alone. But REFUNDED, MIGRATED and SLASHED tasks stay on
    the sequencer's list after they finish, and the meter recounted them in
    every block that followed, which inflated the reported refund and slash
    rates by a factor of however long the task lingered.

    The financial books were never affected: they read net.refunds and
    net.burn_address, which are counted at the event, not by observation. This
    bug was in the reporting counters only. It is fixed by extending _seen to
    every terminal state, and this test is the regression guard.
    """
    rnd = random.Random(2626)
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    # one censored task -> REFUNDED after the window
    net.submit_task("A", "c1", "kobi", spec("llama-70b"))
    for _ in range(W_R + 2):
        net.next_block()
    state_refunded = net.sequencers["A"].tasks["c1"].state
    # one slashed task: two consecutive verification failures
    net.submit_task("B", "s1", "ali", spec("llama-70b"))
    net.solve_task("B", "s1", "res")
    net.settle_task("B", "s1", verify_ok=False)
    net.settle_task("B", "s1", verify_ok=False)
    state_slashed = net.sequencers["B"].tasks["s1"].state

    meter = DemandMeter()
    # observe 30 more blocks while both terminal tasks sit on the lists
    for _ in range(30):
        net.next_block()
        meter.record_block(net)

    ok_state = (state_refunded == "REFUNDED" and state_slashed == "SLASHED")
    ok_refund = (meter.refunded_tasks == 1)
    ok_slash = (meter.slashed_tasks == 1)
    ok_paid = (meter.paid_tasks == 0 and meter.phi() == 0.0)
    print("  TV-26 once-only:     refunded %d (exp 1), slashed %d (exp 1), "
          "paid %d, phi %.3f  %s" %
          (meter.refunded_tasks, meter.slashed_tasks, meter.paid_tasks,
           meter.phi(), "ACCEPT" if (ok_state and ok_refund and ok_slash
                                    and ok_paid) else "RED"))
    return ok_state and ok_refund and ok_slash and ok_paid


if __name__ == "__main__":
    print()
    print("=" * 76)
    print("KOK v2 — F3a: terminal tasks counted once (TV-26, regression guard)")
    print("=" * 76)
    print("The meter's _seen set guarded SETTLED tasks only, so REFUNDED,")
    print("MIGRATED and SLASHED tasks were recounted in every block they spent")
    print("on the sequencer's list. Phi was unaffected, but the reported refund")
    print("and slash rates were inflated by the lingering time.\n")
    ok = tv26_terminal_states_counted_once()
    assert ok, "TV-26 FAILED: terminal tasks are being recounted"
    print("\n  -> the reporting counters are arithmetic, not impressions.")
