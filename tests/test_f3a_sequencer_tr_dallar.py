"""Dal-kesen (branch-cutting) testler: f3a_sequencer_proto.py (TR orijinal).

Kapsam — F3a mock-siralamaci testnet'inin her dali (sansur direnci):
  * H/S — sha256 tabanli tanimlayicilar (8-byte / 16-hex).
  * TaskSpec — burn/escrow ozellikleri ve sinir degerleri.
  * Task — varsayilan durum makinesi degerleri.
  * Sequencer.refill — bond tamamlama policy'sinin her dali
    (bond < floor / bond >= floor / fee < floor / fee > floor).
  * Sequencer.submit — uc degerli donus: ASSIGNED / REJECTED (rastgele dal) /
    CENSORED (sansur dalinda reddetme-adimi YAYINLANMAZ).
  * F3aTestnet.next_block — iade-garantisi penceresi (> w_r, sinir dahil).
  * F3aTestnet.submit_task / migrate_task — gocunun her dali (bilinmeyen tid,
    goculemez durum, bond kesintisi min(bond, fee), refill, bond=0).
  * F3aTestnet.solve_task — ASSIGNED→SOLVED, bilinmeyen/yanlis durum redleri.
  * F3aTestnet.settle_task — SOLVED/CHALLENGED kabul, verify_ok=False→
    CHALLENGED + dilemma sayaci, bilinmeyen/yanlis durum redleri.
  * Gonderilen test vektorleri TV-15..TV-20.

Guvenli-saf-bellek: network/socket/subprocess YOK; tum sablonlar inline'dir.
Rastgele dal (Sequencer.submit'taki evil+rastsal REJECTED) monkeypatch ile
deterministik hale getirilmistir. Production koduna DOKUNULMADI.
"""

import types

import pytest

import f3a_sequencer_proto as f3
from f3a_sequencer_proto import (
    BOND_DEFAULT,
    W_R,
    F3aTestnet,
    Sequencer,
    Task,
    TaskSpec,
    H,
    S,
    spec,
)


# ---------------------------------------------------------------------------
# H / S
# ---------------------------------------------------------------------------

def test_H_returns_a_64_bit_int_and_is_deterministic():
    v = H("a", 1, 2)
    assert isinstance(v, int)
    assert 0 <= v < (1 << 64)
    assert H("a", 1, 2) == v


def test_H_matches_sha256_first_eight_bytes():
    import hashlib
    digest = hashlib.sha256("a|1".encode()).digest()
    assert H("a", 1) == int.from_bytes(digest[:8], "big")


def test_H_differs_on_any_part():
    base = H("x", 9)
    assert H("y", 9) != base
    assert H("x", 10) != base
    assert H("x") != base


def test_S_is_16_lowercase_hex_and_deterministic():
    v = S("msg", 1)
    assert len(v) == 16
    assert all(c in "0123456789abcdef" for c in v)
    assert S("msg", 1) == v
    assert S("msg", 2) != v


def test_constants():
    assert W_R == 3
    assert BOND_DEFAULT == 50


# ---------------------------------------------------------------------------
# TaskSpec / Task
# ---------------------------------------------------------------------------

def test_taskspec_burn_and_escrow_split():
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    assert s.burn == 30
    assert s.escrow == 70


def test_taskspec_burn_rate_boundary_half():
    s = spec("h", fee=100, burn_rate=0.5)
    assert s.burn == 50 and s.escrow == 50


def test_taskspec_burn_truncates_to_int():
    s = spec("h", fee=99, burn_rate=0.333)
    assert s.burn == 32 and s.escrow == 67


def test_taskspec_default_program_is_the_toy_tuple():
    s = TaskSpec(harness_id="h", program=((1, 2), (3, 4)), fee=100, burn_rate=0.1)
    assert spec("h", fee=100, burn_rate=0.1).program == ((1, 2), (3, 4))
    assert s.harness_id == "h"


def test_task_defaults():
    t = Task(tid="t1", client="c", spec=spec("h"))
    assert t.state == "COMMITTED"
    assert t.escrow == 0 and t.burned == 0
    assert t.assignee == "" and t.assigned_at == 0 and t.reject_at == 0
    assert t.result is None and t.migrated_to == ""


# ---------------------------------------------------------------------------
# Sequencer.refill — bond tamamlama policy'si
# ---------------------------------------------------------------------------

def test_refill_lifts_small_bond_to_default_floor():
    sq = Sequencer("A", bond=10, evil=False)
    sq.refill(5)  # floor=50, fee=5 -> max(50, 5) = 50
    assert sq.bond == 50


def test_refill_lifts_small_bond_to_fee_when_fee_above_floor():
    sq = Sequencer("A", bond=10, evil=False)
    sq.refill(500)
    assert sq.bond == 500


def test_refill_is_a_noop_when_bond_at_or_above_floor():
    sq = Sequencer("A", bond=100, evil=False)
    sq.refill(500)
    assert sq.bond == 100
    sq2 = Sequencer("B", bond=50, evil=False)
    sq2.refill(10)
    assert sq2.bond == 50


def test_refill_lifts_zero_bond_to_fee():
    sq = Sequencer("A", bond=0, evil=False)
    sq.refill(100)
    assert sq.bond == 100


# ---------------------------------------------------------------------------
# Sequencer.submit — ASSIGNED / REJECTED / CENSORED
# ---------------------------------------------------------------------------

def test_honest_submit_assigns_and_takes_escrow():
    sq = Sequencer("A", evil=False)
    t = Task(tid="t1", client="kobi", spec=spec("llama-70b"))
    ok = sq.submit(t, height=7)
    assert ok is True
    assert t.state == "ASSIGNED"
    assert t.assigned_at == 7
    assert t.escrow == 70
    assert sq.tasks["t1"] is t


def test_censoring_submit_silently_holds_the_task():
    sq = Sequencer("A", evil=True, censor_client="kobi")
    t = Task(tid="t1", client="kobi", spec=spec("llama-70b"))
    ok = sq.submit(t, height=3)
    assert ok is False
    assert t.state == "CENSORED"
    assert t.assigned_at == 3
    assert sq.tasks["t1"] is t


def test_censor_only_targets_the_designated_client():
    sq = Sequencer("A", evil=True, censor_client="kobi")
    t = Task(tid="t1", client="ali", spec=spec("llama-70b"))
    ok = sq.submit(t, height=1)
    assert ok is True
    assert t.state in ("REJECTED", "ASSIGNED")  # rastsal dal


def test_evil_non_matching_client_random_reject_branch(monkeypatch):
    monkeypatch.setattr(f3, "random", types.SimpleNamespace(random=lambda: 0.1))
    sq = Sequencer("A", evil=True, censor_client="kobi")
    t = Task(tid="t1", client="ali", spec=spec("llama-70b"))
    ok = sq.submit(t, height=2)
    assert ok is True
    assert t.state == "REJECTED"
    assert t.reject_at == 2


def test_evil_non_matching_client_random_assign_branch(monkeypatch):
    monkeypatch.setattr(f3, "random", types.SimpleNamespace(random=lambda: 0.9))
    sq = Sequencer("A", evil=True, censor_client="kobi")
    t = Task(tid="t1", client="ali", spec=spec("llama-70b"))
    ok = sq.submit(t, height=2)
    assert ok is True
    assert t.state == "ASSIGNED"
    assert t.assigned_at == 2


def test_evil_with_empty_censor_client_always_takes_random_branch(monkeypatch):
    monkeypatch.setattr(f3, "random", types.SimpleNamespace(random=lambda: 0.0))
    sq = Sequencer("A", evil=True, censor_client="")
    t = Task(tid="t1", client="kobi", spec=spec("llama-70b"))
    assert sq.submit(t, height=0) is True
    assert t.state == "REJECTED"


# ---------------------------------------------------------------------------
# F3aTestnet — kurulum ve blok uretimi / iade-garantisi
# ---------------------------------------------------------------------------

def test_testnet_initial_state():
    net = F3aTestnet([Sequencer("A"), Sequencer("B")])
    assert set(net.sequencers) == {"A", "B"}
    assert net.height == 0 and net.w_r == W_R
    assert net.burn_address == 0 and net.refunds == 0
    assert net.slash_events == 0 and net.migrations == 0
    assert net.dilemma_triggers == 0


def test_testnet_custom_w_r():
    net = F3aTestnet([Sequencer("A")], w_r=7)
    assert net.w_r == 7


def test_next_block_increments_height():
    net = F3aTestnet([Sequencer("A")])
    assert net.next_block() == 1
    assert net.next_block() == 2
    assert net.height == 2


def test_refund_window_boundary_not_refunded_within_w_r():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")], w_r=3)
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    for _ in range(W_R):  # height 1, 2, 3 -> 3 - 0 = 3 w_r'ye esit, ASMAZ
        net.next_block()
        assert net.sequencers["A"].tasks["t1"].state == "CENSORED"
    assert net.refunds == 0


def test_refund_fires_only_after_w_r_blocks():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")], w_r=3)
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))  # assigned_at = 0
    for _ in range(W_R + 1):  # height 1..4; 4 - 0 > 3 -> iade tetiklenir
        net.next_block()
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "REFUNDED"
    assert net.refunds == 70
    assert t.escrow == 0
    assert net.burn_address == 0  # burn henuz realize olmadi


def test_refund_is_not_double_counted():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    for _ in range(W_R + 2):
        net.next_block()
    assert net.refunds == 70  # ikinci blokta tekrar iade yok


def test_refunded_task_survives_further_blocks():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    for _ in range(W_R + 1):
        net.next_block()
    assert net.sequencers["A"].tasks["t1"].state == "REFUNDED"


def test_submit_task_creates_task_with_escrow_and_burn():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "t1", "kobi", spec("h", fee=100, burn_rate=0.3))
    t = net.sequencers["A"].tasks["t1"]
    assert t.client == "kobi"
    assert t.escrow == 70 and t.burned == 30
    assert t.state == "ASSIGNED"


def test_submit_task_to_unknown_sequencer_raises():
    net = F3aTestnet([Sequencer("A")])
    with pytest.raises(KeyError):
        net.submit_task("Z", "t1", "kobi", spec("h"))


# ---------------------------------------------------------------------------
# migrate_task — goc + bond kesintisi + refill
# ---------------------------------------------------------------------------

def test_migrate_censored_task_slashes_and_moves():
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    net.submit_task("A", "t2", "kobi", spec("h", fee=100))
    ok = net.migrate_task("t2", "A", "B")
    assert ok is True
    a, b = net.sequencers["A"], net.sequencers["B"]
    assert a.slashed == 100  # min(bond, fee) = 100
    assert a.bond == 100  # refill bond'u fee seviyesinde tuttu
    assert net.slash_events == 1 and net.migrations == 1
    assert "t2" not in a.tasks
    t2 = b.tasks["t2"]
    assert t2.state == "ASSIGNED" and t2.spec.fee == 100


def test_migrate_rejected_task_is_allowed():
    net = F3aTestnet([Sequencer("A", bond=60), Sequencer("B")])
    t = Task(tid="t1", client="kobi", spec=spec("h", fee=50))
    net.sequencers["A"].submit(t, height=0)
    t.state = "REJECTED"  # reddetme-adimi yayinlandi
    assert net.migrate_task("t1", "A", "B") is True
    assert net.slash_events == 1


def test_migrate_refuses_non_migratable_states():
    net = F3aTestnet([Sequencer("A"), Sequencer("B")])
    net.submit_task("A", "t9", "kobi", spec("h"))  # ASSIGNED
    assert net.migrate_task("t9", "A", "B") is False
    assert net.migrations == 0 and net.slash_events == 0
    net.solve_task("A", "t9", "r")  # SOLVED
    assert net.migrate_task("t9", "A", "B") is False


def test_migrate_unknown_tid_returns_false():
    net = F3aTestnet([Sequencer("A"), Sequencer("B")])
    assert net.migrate_task("yok", "A", "B") is False


def test_migrate_slash_is_bond_limited():
    net = F3aTestnet([Sequencer("A", bond=30, evil=True, censor_client="kobi"),
                      Sequencer("B")])
    net.submit_task("A", "t1", "kobi", spec("h", fee=100))
    net.migrate_task("t1", "A", "B")
    a = net.sequencers["A"]
    assert a.slashed == 30  # min(30, 100)
    assert a.bond == 100  # slash sonrasi refill fee seviyesine cikardi


def test_migrate_from_zero_bond_slashes_zero_but_refills():
    net = F3aTestnet([Sequencer("A", bond=0, evil=True, censor_client="kobi"),
                      Sequencer("B")])
    net.submit_task("A", "t1", "kobi", spec("h", fee=100))
    net.migrate_task("t1", "A", "B")
    a = net.sequencers["A"]
    assert a.slashed == 0  # bond zaten 0
    assert a.bond == 100  # refill yine de bond'u fee seviyesine cikardi
    assert net.migrations == 1


def test_migrated_task_keeps_its_spec_and_gets_fresh_escrow():
    net = F3aTestnet([Sequencer("A", bond=100, evil=True, censor_client="kobi"),
                      Sequencer("B")])
    net.submit_task("A", "t1", "kobi", spec("h", fee=100, burn_rate=0.2))
    net.migrate_task("t1", "A", "B")
    t = net.sequencers["B"].tasks["t1"]
    assert t.spec.fee == 100 and t.escrow == 80 and t.burned == 20
    assert t.state == "ASSIGNED" and t.client == "kobi"


# ---------------------------------------------------------------------------
# solve_task / settle_task
# ---------------------------------------------------------------------------

def test_solve_task_sets_result_on_assigned_task():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "t9", "kobi", spec("h"))
    assert net.solve_task("A", "t9", "result-hash") is True
    assert net.sequencers["A"].tasks["t9"].state == "SOLVED"
    assert net.sequencers["A"].tasks["t9"].result == "result-hash"


def test_solve_task_refuses_unknown_or_non_assigned():
    net = F3aTestnet([Sequencer("A")])
    assert net.solve_task("A", "yok", "r") is False
    net.submit_task("A", "t9", "kobi", spec("h"))
    net.solve_task("A", "t9", "r")
    assert net.solve_task("A", "t9", "again") is False  # zaten SOLVED


def test_settle_task_burns_and_closes_escrow():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "tA", "kobi", spec("h", fee=100, burn_rate=0.3))
    net.solve_task("A", "tA", "res")
    assert net.settle_task("A", "tA") is True
    t = net.sequencers["A"].tasks["tA"]
    assert t.state == "SETTLED"
    assert t.escrow == 0 and t.burned == 0
    assert net.burn_address == 30


def test_settle_task_accepts_challenged_after_successful_verify():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "tA", "kobi", spec("h", fee=100, burn_rate=0.3))
    net.solve_task("A", "tA", "res")
    assert net.settle_task("A", "tA", verify_ok=False) is False  # CHALLENGED
    assert net.settle_task("A", "tA", verify_ok=True) is True
    assert net.sequencers["A"].tasks["tA"].state == "SETTLED"
    assert net.burn_address == 30


def test_settle_task_failed_verify_counts_dilemma_trigger():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "tA", "kobi", spec("h"))
    net.solve_task("A", "tA", "res")
    assert net.settle_task("A", "tA", verify_ok=False) is False
    assert net.dilemma_triggers == 1
    assert net.sequencers["A"].tasks["tA"].state == "CHALLENGED"


def test_settle_task_does_not_decrement_dilemma_on_success():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "tA", "kobi", spec("h"))
    net.solve_task("A", "tA", "res")
    net.settle_task("A", "tA", verify_ok=False)
    net.settle_task("A", "tA", verify_ok=True)
    assert net.dilemma_triggers == 1


def test_settle_task_refuses_unknown_and_unsolved():
    net = F3aTestnet([Sequencer("A")])
    assert net.settle_task("A", "yok") is False
    net.submit_task("A", "tA", "kobi", spec("h"))  # ASSIGNED, henuz cozulmedi
    assert net.settle_task("A", "tA") is False
    assert net.sequencers["A"].tasks["tA"].state == "ASSIGNED"


# ---------------------------------------------------------------------------
# gonderilen test vektorleri TV-15..TV-20
# ---------------------------------------------------------------------------

def test_tv15_refund_guarantee_vector():
    assert f3.tv15() is True


def test_tv16_task_migration_vector():
    assert f3.tv16() is True


def test_tv17_censorship_is_not_free_vector():
    assert f3.tv17() is True


def test_tv18_no_dilemma_vector():
    assert f3.tv18() is True


def test_tv19_honest_lifecycle_vector():
    assert f3.tv19() is True


def test_tv20_bond_refill_regression_vector():
    """TV-20: refill YOKSA deterrent tek-seferliktir (pass_sim 10'un buldugu
    acik); refill VARSA her sansur olayi fee kadar keser."""
    assert f3.tv20() is True


def test_all_shipped_vectors_pass_together():
    # modul __main__ altinda calistirildiginda hepsi gecer; burada tek tek
    for fn in (f3.tv15, f3.tv16, f3.tv17, f3.tv18, f3.tv19, f3.tv20):
        assert fn() is True
