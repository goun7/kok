#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - F3a PROTOTYPE: off-protocol economics testnet (mock sequencer)
========================================================================

V2 10.1 F3a: G layer ACTIVE, central bir mock sequencer block produces,
that the task market runs BY ITSELF. This prototype tests spec A.5's
Tests the TWO censorship-resistance mechanisms defined in clause 5:

  (i) REFUND-GARANTISI  : sequencer task W_r block icinde reject-step
                        if it is not published the escrow is AUTOMATICALLY refunded
                        (the cost of censorship = its benefit = 0).
 (ii) TASK MIGRATION: the task owner sends the rejected task to an alternative
                        to the sequencer gonderir; the first sequencer's bond
                        is slashed (censorship gives a NEGATIVE return).

TEST VEKTORLERI:
  TV-15  refund-guarantee: if the rejection step does not arrive the escrow is refunded on timeout
  TV-16  task-migration: the rejected task goes to an alternative, the bond is slashed
  TV-17  pay-per-task:     the sequencer CANNOT censor (utility is separated)
  TV-18  dilemmasiz:     verifier's-dilemma tetiklenmiyor (spec A.5.2)

HONEST TOY LIMITS (spec A.10.7 style):
  - sequencer su an tek bir nesne (in production network separate nodes)
  - W_r = 3 blocks (variable in production)
  - fee/burn degerleri sembolik (toy para birimi)
  - GHOSTDAG NONE: single parent, central block production (this is F3a's definition)
  - VRF HMAC-stub (same as u_layer_prototype.py)
  - censorship "evil sequencer" olarak is modelled; in production GHOSTDAG
    protected by parent-set diversity + miner competition (spec A.5.5)
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
BOND_DEFAULT = 50 # sequencer bond (censorship slash kaynagi)


# ------------------------------------------------------------------ task
@dataclass
class TaskSpec:
    harness_id: str
    program: object             # (A, B) — toy "faydali is"
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
        self.evil = evil                    # censorship modu
        self.censor_client = censor_client  # bu client'in tasklerini censorshiple
        self.slashed = 0
        self.tasks = {}                     # tid -> Task

    def refill(self, fee, floor=BOND_DEFAULT):
        """Policy: the bond after every censorship eventindan sonra fee seviyesine is topped up.
        Otherwise bond at the first event is depleted ve subsequent censorship FREE olur
        (pass_sim 10, tablo B — modelleme hamigratendan bulunan acik)."""
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
        self.burn_address = 0          # geri harcanamaz (Demirel)
        self.refunds = 0               # refund edilen escrow
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

    # --- task gonderimi (client tarafindan sequencer is chosen) ---
    def submit_task(self, seq_id, tid, client, spec):
        return self.sequencers[seq_id].submit(
            Task(tid=tid, client=client, spec=spec, escrow=spec.escrow,
                 burned=spec.burn), self.height)

    # --- TV-16: task-migration ---
    def migrate_task(self, tid, from_seq, to_seq):
        t = self.sequencers[from_seq].tasks.get(tid)
        if t is None:
            return False
        # only CENSORED veya REJECTED taskler can be migrated
        if t.state not in ("CENSORED", "REJECTED"):
            return False
        # sequencer's bond is slashed (censorship negative yield)
        slash = min(self.sequencers[from_seq].bond, t.spec.fee)
        self.sequencers[from_seq].bond -= slash
        self.sequencers[from_seq].slashed += slash
        self.slash_events += 1
        # POLICY (pass_sim 10): bond GERI-EKLENIR — aksi halde deterrent
        # is one-shot (at the first event is depleted, the rest free).
        # Governance tarafindan fee seviyesine otomatik tamamlama.
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
        # spec A.5.2: verification is MANDATORY; the verifier cannot skip it (no dilemma)
        if not verify_ok:
            self.dilemma_triggers += 1
            t.state = "CHALLENGED"
            return False
        t.state = "SETTLED"
        self.burn_address += t.burned
        t.escrow = 0
        t.burned = 0
        return True


# =============================================================== TESTLER
def spec(harness, fee=100, burn_rate=0.3, program=None):
    return TaskSpec(harness_id=harness, program=program or ((1, 2), (3, 4)),
                    fee=fee, burn_rate=burn_rate)


def tv15():
    """TV-15: REFUND-GARANTISI. Evil sequencer reject-step does not publish
    escrow W_r blok sonunda OTOMATIK refund edilir; censorshipun its benefit yoktur."""
    random.seed(1515)
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    ok = net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    assert not ok and net.sequencers["A"].tasks["t1"].state == "CENSORED"

    # NO refund until the window elapses
    for _ in range(W_R):
        net.next_block()
        assert net.sequencers["A"].tasks["t1"].state == "CENSORED", \
            "refund-guarantee erken tetiklendi"
    # W_r'yi gecti -> otomatik refund
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
    # slash min(bond, fee) = 100; bond GERI-EKLENIR (TV-20 policy'su)
    assert net.sequencers["A"].slashed == 100, "bond kesilmedi"
    assert net.sequencers["A"].bond == bond_before, "bond uste tulenmedi (refill)"
    assert net.slash_events == 1 and net.migrations == 1
    # task artik B'de ASSIGNED
    assert net.sequencers["B"].tasks["t2"].state == "ASSIGNED"
    # cozum + settle B'de calisir
    assert net.solve_task("B", "t2", "result-hash")
    assert net.settle_task("B", "t2")
    assert net.burn_address == 30  # 100*0.3 burn gerceklesti
    print(f"  TV-16 task-migration:  REJECTION -> migrate (slash 100, bond topped up to {bond_before}) + settles in B  ACCEPT")
    return True


def tv17():
    """TV-17: CENSORSHIP-IS-FREE-FAILS. An evil sequencer's 'petty' censorship also
    the system task either refund eder either migrates; sequencer NO zaman
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
    # goc edilen 2 task A'dan SILINDI (B'de ASSIGNED); kalan 3 A'da REFUNDED
    counts = {}
    for i in range(5):
        t = net.sequencers["A"].tasks.get(f"t{i}")
        if t is not None:
            counts[t.state] = counts.get(t.state, 0) + 1
    assert counts == {"REFUNDED": 3}, counts
    # sequencer A: has 0 escrow (consumed nothing).
    # *** THE SUBTLE POINT (the real value of TV-17): since bond0=50 < fee=100
    # refill RAISES the bond to the FEE LEVEL (100). Slashes: 50 (first, bond=50)
    # + 100 (refill the rest, bond=100) = 150. Yani refill hem bond'u KORUR
    # hem de ALT SEVIYEDEN baslayan bir sequenceryi fee seviyesine cikarir. ***
    held = sum(t.escrow for t in net.sequencers["A"].tasks.values())
    assert held == 0, "sequencer escrow held escrow"
    assert net.sequencers["A"].bond == 100, "bond fee seviyesine cikmadi"
    assert net.sequencers["A"].slashed == 150, "kumulatif slash 50+100=150 olmali"
    # refund total = 3 * 70 = 210
    assert net.refunds == 210, net.refunds
    print(f"  TV-17 censorship-free: gain=0 (refund {net.refunds}), slash 50+100=150")
    print("                        (bond0=50<fee=100 -> refill raised the bond to the fee level)  ACCEPT")
    return True


def tv18():
    """TV-18: THE VERIFIER'S DILEMMA IS NOT TRIGGERED (spec A.5.2). Verification
    is MANDATORY; verify_ok=False only produces CHALLENGED, no settle.
    Honest sequencerda dilemma saeitherci zero stays."""
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
    assert net.dilemma_triggers == 1  # hala 1 (geri sayilmiyor)
    assert net.burn_address == 30
    print(f"  TV-18 no-dilemma:     mandatory verification; wrong->CHALLENGED, correct->SETTLED  ACCEPT")
    return True


def tv19():
    """TV-19: HONEST SIRA. Honest tek sequencer ile tum eithersam dongusu:
    submit -> assign -> solve -> settle; burn gerceklesir, escrow tuketilir."""
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
    """TV-20: BOND GERI-EKLEME (pass_sim 10 tablo B'nin buldugu acik).
    Geri-ekleme YOKSA deterrent is one-shot: ilk censorship bond'u tukerir,
    subsequent eventlar FREEDIR. Refill VARSA her event fee kadar keser.
    *** Bu test, ekonomi modelinin bir BUG'I bulup prototypei DUZELTTigini
    kanitlar. ***"""
    random.seed(2020)
    # (a) refill VAR (uretim policy'su): her event keser
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    bond0 = net.sequencers["A"].bond
    for i in range(3):
        net.submit_task("A", f"g{i}", "kobi", spec("llama-70b", fee=100))
        net.migrate_task(f"g{i}", "A", "B")
    # her event min(bond,fee)=100 kesildi VE geri-eklendi
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
            # refill YOK — bu eski (hatali) davranistir
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
    # ILK event bond tukendi, subsequent IKISI FREE (100, 300 degil)
    assert net2.sequencers["A"].slashed == 100, net2.sequencers["A"].slashed
    assert net2.sequencers["A"].bond == 0, "bond tukenecekti"
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
        print("BASARISIZ TESTLER:", [k for k, v in results.items() if not v])
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
