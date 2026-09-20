#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KÖK v2 - F3a PROTOTYPE: off-protocol economics testnet (mock sequencer)
========================================================================

V2 10.1 F3a: G layer ACTIVE, central bir mock sequencer block produces,
gorev pazarinin KENDI kendine calistigini olcer. Bu prototip spec A.5'in
Tests the TWO censorship-resistance mechanisms defined in clause 5:

  (i) REFUND-GARANTISI  : sequencer task W_r block icinde reject-step
                        yayinlamazsa escrow OTOMATIK iade edilir
                        (sansurun maliyeti = faydasi = 0).
 (ii) GOREV-GOCU      : gorev sahibi reddedilen gorevi alternatif
                        to the sequencer gonderir; the first sequencer's bond
                        kesilir (sansur NEGATIF getiri verir).

TEST VEKTORLERI:
  TV-15  iade-garantisi: reddetme-adimi gelmezse escrow zamanasimiyla iade
  TV-16  gorev-gocu:     reddedilen gorev alternatife gider, bond kesilir
  TV-17  odeme-bascagina:  siralamaci sansur YAPAMAZ (ucrumu kontrol)
  TV-18  dilemmasiz:     verifier's-dilemma tetiklenmiyor (spec A.5.2)

HONEST TOY LIMITS (spec A.10.7 style):
  - sequencer su an tek bir nesne (in production network separate nodes)
  - W_r = 3 blok (uretimde degisken)
  - fee/burn degerleri sembolik (toy para birimi)
  - GHOSTDAG NONE: single parent, central block production (this is F3a's definition)
  - VRF HMAC-stub (u_layer_prototype.py ile ayni)
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


W_R = 3           # iade-garantisi penceresi (blok)
BOND_DEFAULT = 50 # sequencer bond (censorship slash kaynagi)


# ------------------------------------------------------------------ gorev
@dataclass
class TaskSpec:
    harness_id: str
    program: object             # (A, B) — toy "faydali is"
    fee: int
    burn_rate: float            # fee'nin yuzdesi geri-alamaz burn

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
    assigned_at: int = 0        # hangi blokta atandi
    reject_at: int = 0          # hangi blokta reddetme-adimi yayinlandi
    result: object = None
    migrated_to: str = ""       # TV-16: migrated sequencer


# ------------------------------------------------------- mock sequencer
class Sequencer:
    """F3a's TEMPORARY central sequencer. 'honest' or 'censoring' mode."""

    def __init__(self, sid, bond=BOND_DEFAULT, evil=False, censor_client=""):
        self.sid = sid
        self.bond = bond
        self.evil = evil                    # sansur modu
        self.censor_client = censor_client  # bu klient'in gorevlerini sansurle
        self.slashed = 0
        self.tasks = {}                     # tid -> Task

    def refill(self, fee, floor=BOND_DEFAULT):
        """Policy: bond her sansur olayindan sonra fee seviyesine tamamlanir.
        Aksi halde bond ilk olayda tukerilir ve sonraki sansur BEDAVA olur
        (pass_sim 10, tablo B — modelleme hatasindan bulunan acik)."""
        if self.bond < floor:
            self.bond = max(floor, fee)

    def submit(self, task, height):
        """Gorev al; eger sansur modundaysa ve hedef klient ise reddet."""
        if self.evil and task.client == self.censor_client:
            # KOTU: reddetme-adimi YAYINLAMADAN beklet -> iade-garantisi tetikler
            task.state = "CENSORED"
            task.assigned_at = height
            self.tasks[task.tid] = task
            return False
        # DURUST: reddetme-adimi hemen (state=REJECTED) veya ata
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
        self.refunds = 0               # iade edilen escrow
        self.slash_events = 0
        self.migrations = 0
        self.dilemma_triggers = 0

    # --- block production (central; GHOSTDAG in F3b) ---
    def next_block(self):
        self.height += 1
        # iade-garantisi: her blokta, pencereyi asmis CENSORED gorevleri iade et
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

    # --- TV-16: gorev-gocu ---
    def migrate_task(self, tid, from_seq, to_seq):
        t = self.sequencers[from_seq].tasks.get(tid)
        if t is None:
            return False
        # yalnizca CENSORED veya REJECTED gorevler goc edilebilir
        if t.state not in ("CENSORED", "REJECTED"):
            return False
        # sequencer's bond is slashed (censorship negative yield)
        slash = min(self.sequencers[from_seq].bond, t.spec.fee)
        self.sequencers[from_seq].bond -= slash
        self.sequencers[from_seq].slashed += slash
        self.slash_events += 1
        # POLICY (pass_sim 10): bond GERI-EKLENIR — aksi halde deterrent
        # tek-seferliktir (ilk olayda tukerilir, sonrasi bedava).
        # Governance tarafindan fee seviyesine otomatik tamamlama.
        self.sequencers[from_seq].refill(t.spec.fee)
        # gorevi alternatife tasi, eskisini kapat
        t.state = "MIGRATED"
        t.migrated_to = to_seq
        del self.sequencers[from_seq].tasks[tid]
        t2 = Task(tid=tid, client=t.client, spec=t.spec, escrow=t.spec.escrow,
                  burned=t.spec.burn, state="ASSIGNED", assigned_at=self.height)
        self.sequencers[to_seq].tasks[tid] = t2
        self.migrations += 1
        return True

    # --- cozum (madenci proof verir; F3a'da dummy, kripto yok) ---
    def solve_task(self, seq_id, tid, result):
        t = self.sequencers[seq_id].tasks.get(tid)
        if t is None or t.state != "ASSIGNED":
            return False
        t.result = result
        t.state = "SOLVED"
        return True

    # --- settle: escrow ucreti, burn girer (geri-alamaz) ---
    def settle_task(self, seq_id, tid, verify_ok=True):
        t = self.sequencers[seq_id].tasks.get(tid)
        # CHALLENGED gorev, itiraz cozulduyse SETTLE olabilir (fraud window kapatma)
        if t is None or t.state not in ("SOLVED", "CHALLENGED"):
            return False
        # spec A.5.2: dogrulama ZORUNLU; verifier atlayamaz (dilemma tetiklenmez)
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
    escrow W_r blok sonunda OTOMATIK iade edilir; sansurun faydasi yoktur."""
    random.seed(1515)
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    ok = net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    assert not ok and net.sequencers["A"].tasks["t1"].state == "CENSORED"

    # pencere dolana kadar iade YOK
    for _ in range(W_R):
        net.next_block()
        assert net.sequencers["A"].tasks["t1"].state == "CENSORED", \
            "iade-garantisi erken tetiklendi"
    # W_r'yi gecti -> otomatik iade
    net.next_block()
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "REFUNDED" and net.refunds == 70, (t.state, net.refunds)
    assert t.escrow == 0 and net.burn_address == 0
    print("  TV-15 refund-guarantee:  NO-REJECTION -> automatic refund (escrow=70)  ACCEPT")
    return True


def tv16():
    """TV-16: GOREV-MIGRATIONU. Reddedilen task alternative sequencereither goes;
    the first sequencer's bond is slashed -> censorship NEGATIVE yield gives."""
    random.seed(1616)
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    net.submit_task("A", "t2", "kobi", spec("llama-70b", fee=100))
    assert net.sequencers["A"].tasks["t2"].state == "CENSORED"

    bond_before = net.sequencers["A"].bond
    migrated = net.migrate_task("t2", "A", "B")
    assert migrated
    # kesinti min(bond, fee) = 100; bond GERI-EKLENIR (TV-20 policy'su)
    assert net.sequencers["A"].slashed == 100, "bond kesilmedi"
    assert net.sequencers["A"].bond == bond_before, "bond uste tulenmedi (refill)"
    assert net.slash_events == 1 and net.migrations == 1
    # gorev artik B'de ASSIGNED
    assert net.sequencers["B"].tasks["t2"].state == "ASSIGNED"
    # cozum + settle B'de calisir
    assert net.solve_task("B", "t2", "result-hash")
    assert net.settle_task("B", "t2")
    assert net.burn_address == 30  # 100*0.3 burn gerceklesti
    print(f"  TV-16 task-migration:  REJECTION -> migrate (slash 100, bond topped up to {bond_before}) + settles in B  ACCEPT")
    return True


def tv17():
    """TV-17: CENSORSHIP-UCRETSIZLEME. Evil sequencer 'petty' censorship makesa da
    the system task either refund eder either migrates; sequencer NO zaman
    escrow'u elinde tutamaz (kazanci sifir), bond'u azalir (zarari var)."""
    random.seed(1717)
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    bond0 = net.sequencers["A"].bond
    # 5 tasks: 3 timeout-refunds, 2 migrations
    for i in range(5):
        net.submit_task("A", f"t{i}", "kobi", spec("llama-70b"))
    # 2'sini GOC ET (pencere dolmadan) -> bond kesilir
    for i in range(2):
        net.migrate_task(f"t{i}", "A", "B")
    assert net.migrations == 2 and net.slash_events == 2
    # kalan 3'u zamanasimi ile iade et
    for _ in range(W_R + 1):
        net.next_block()
    # goc edilen 2 gorev A'dan SILINDI (B'de ASSIGNED); kalan 3 A'da REFUNDED
    counts = {}
    for i in range(5):
        t = net.sequencers["A"].tasks.get(f"t{i}")
        if t is not None:
            counts[t.state] = counts.get(t.state, 0) + 1
    assert counts == {"REFUNDED": 3}, counts
    # sequencer A: 0 escrow'a sahip (no consumed nothing).
    # *** INCE NOKTA (TV-17'nin gercek degeri): bond0=50 < fee=100 oldugu icin
    # refill bond'u FEE SEVIYESINE (100) yukeltir. Kesintiler: 50 (ilk, bond=50)
    # + 100 (refill sonrasi, bond=100) = 150. Yani refill hem bond'u KORUR
    # hem de ALT SEVIYEDEN baslayan bir siralamaciyi fee seviyesine cikarir. ***
    held = sum(t.escrow for t in net.sequencers["A"].tasks.values())
    assert held == 0, "sequencer escrow held escrow"
    assert net.sequencers["A"].bond == 100, "bond fee seviyesine cikmadi"
    assert net.sequencers["A"].slashed == 150, "kumulatif kesinti 50+100=150 olmali"
    # iade toplami = 3 * 70 = 210
    assert net.refunds == 210, net.refunds
    print(f"  TV-17 censorship-free: gain=0 (refund {net.refunds}), slash 50+100=150")
    print("                        (bond0=50<fee=100 -> refill raised the bond to the fee level)  ACCEPT")
    return True


def tv18():
    """TV-18: VERIFIER'S-DILEMMA TETIKLENMIYOR (spec A.5.2). Dogrulama
    ZORUNLU; verify_ok=False sadece CHALLENGED uretir, settle olmaz.
    Honest sequencerda dilemma saeitherci zero stays."""
    random.seed(1818)
    net = F3aTestnet([Sequencer("A", evil=False)])
    net.submit_task("A", "t9", "kobi", spec("llama-70b"))
    net.solve_task("A", "t9", "r")
    # hatali dogrulama -> CHALLENGED, dilemma sayaci artar (izlenir)
    assert not net.settle_task("A", "t9", verify_ok=False)
    assert net.dilemma_triggers == 1
    assert net.sequencers["A"].tasks["t9"].state == "CHALLENGED"
    # dogru dogrulama -> SETTLED, dilemma tetiklenmedi
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
    Geri-ekleme YOKSA deterrent tek-seferliktir: ilk sansur bond'u tukerir,
    sonraki olaylar BEDAVADIR. Refill VARSA her olay fee kadar keser.
    *** Bu test, ekonomi modelinin bir BUG'I bulup prototipi DUZELTTigini
    kanitlar. ***"""
    random.seed(2020)
    # (a) refill VAR (uretim policy'su): her olay keser
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    bond0 = net.sequencers["A"].bond
    for i in range(3):
        net.submit_task("A", f"g{i}", "kobi", spec("llama-70b", fee=100))
        net.migrate_task(f"g{i}", "A", "B")
    # her olayda min(bond,fee)=100 kesildi VE geri-eklendi
    assert net.slash_events == 3
    assert net.sequencers["A"].slashed == 300, net.sequencers["A"].slashed
    assert net.sequencers["A"].bond == 100, net.sequencers["A"].bond  # refill sonrasi

    # (b) refill YOK (regression guard: eski acik):
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
    # ILK olayda bond tukendi, sonraki IKISI BEDAVA (100, 300 degil)
    assert net2.sequencers["A"].slashed == 100, net2.sequencers["A"].slashed
    assert net2.sequencers["A"].bond == 0, "bond tukenecekti"
    print(f"  TV-20 bond-refill:   3 censorship events; refill -> 300 slashed (bond {bond0}->100);")
    print("                        refill-NO -> 100 slashed (bond 100->0, 2 events FREE)")
    print("                        ACCEPT (the gap was found and closed)")
    return True


if __name__ == "__main__":
    print("=" * 72)
    print("KÖK v2 F3a PROTOTYPE - mock sequencer + censorship resistance (TV-15..TV-20)")
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
