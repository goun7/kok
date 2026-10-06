"""Tests for f3a_sequencer_proto_en.py: the F3a task market's ledger machine.

The F3a prototype is the mock-sequencer testnet that studies the task market on
its own (spec V2 10.1 / clause A.5): a central sequencer produces blocks, and
two censorship-resistance mechanisms -- the refund guarantee and task
migration with a bond slash -- keep the sequencer honest. Underneath sits the
penalty/settlement state machine that the kok-ledger and kok-consensus crates
implement in Rust.

Covers (stdlib-only, pure state-machine logic, no external calls):
  * TaskSpec -- the fee/burn split and its range validation.
  * Sequencer.refill / submit -- the bond top-up policy and the
    three-valued submit return (ASSIGNED / REJECTED / CENSORED).
  * F3aTestnet -- the refund-guarantee window, settle_task's
    challenge-then-slash state machine, migrate_task's slash + refill,
    and the VRF assignment stub.
  * DemandMeter -- phi, the utilization ratio, its verdicts, and the
    once-only counting of terminal tasks (TV-50's regression guard).
  * run_demand_scenario -- the demandless vs demanding populations.
  * The shipped test vectors TV-17 / TV-20 / TV-24 / TV-25 / TV-44 /
    TV-50 / TV-69 / TV-81, each called and asserted directly.
"""

import random

import pytest

import f3a_sequencer_proto_en as f3a
from f3a_sequencer_proto_en import (
    BOND_DEFAULT,
    W_R,
    BuyerPopulation,
    DemandMeter,
    F3aTestnet,
    Sequencer,
    TaskSpec,
    run_demand_scenario,
    spec,
)


# ---------------------------------------------------------------- helpers
def _evil_net(client="kobi", bond=BOND_DEFAULT, bond_b=None):
    """A two-sequencer net: A censors `client`, B is honest."""
    return F3aTestnet([Sequencer("A", bond=bond, evil=True, censor_client=client),
                       Sequencer("B", bond=bond_b, evil=False)])


# ------------------------------------------------------------- TaskSpec
def test_task_spec_burn_and_escrow_split():
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    assert s.burn == 30          # int(100 * 0.3)
    assert s.escrow == 70        # fee - burn
    assert s.fee == 100


def test_task_spec_burn_rate_zero_and_one_boundaries():
    assert spec("h", fee=100, burn_rate=0.0).burn == 0
    assert spec("h", fee=100, burn_rate=0.0).escrow == 100
    assert spec("h", fee=100, burn_rate=1.0).burn == 100
    assert spec("h", fee=100, burn_rate=1.0).escrow == 0


def test_task_spec_rejects_negative_fee():
    with pytest.raises(ValueError, match="fee must be non-negative"):
        TaskSpec(harness_id="h", program=((1, 2), (3, 4)), fee=-1, burn_rate=0.3)


@pytest.mark.parametrize("bad", [-0.1, 1.5, 2.0])
def test_task_spec_rejects_burn_rate_out_of_range(bad):
    with pytest.raises(ValueError, match=r"burn_rate must be in \[0,1\]"):
        TaskSpec(harness_id="h", program=((1, 2), (3, 4)), fee=100, burn_rate=bad)


# ------------------------------------------------------- Sequencer.refill
def test_refill_raises_bond_to_floor_when_below():
    sq = Sequencer("A", bond=10)
    sq.refill(100)                     # floor defaults to BOND_DEFAULT=50
    assert sq.bond == 100              # max(floor=50, fee=100) = 100


def test_refill_is_a_noop_when_bond_at_or_above_floor():
    sq = Sequencer("A", bond=60)
    sq.refill(100)
    assert sq.bond == 60               # 60 >= floor: untouched


def test_refill_sub_bond_trap_floor_wins_over_fee():
    """bond 0, fee 10, floor 50 -> 50, not the fee (the documented rule)."""
    sq = Sequencer("A", bond=0)
    sq.refill(10, floor=50)
    assert sq.bond == 50


def test_refill_never_lowers_the_bond():
    sq = Sequencer("A", bond=200)
    sq.refill(5, floor=50)
    assert sq.bond == 200


# ------------------------------------------------------ Sequencer.submit
def test_submit_honest_assigns_and_locks_escrow():
    net = F3aTestnet([Sequencer("A")])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    verdict = net.submit_task("A", "t1", "buyer", s)
    assert verdict == "ASSIGNED"
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "ASSIGNED"
    assert t.escrow == 70
    assert t.burned == 30


def test_submit_censoring_client_is_censored():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    assert net.submit_task("A", "t1", "kobi", spec("llama-70b")) == "CENSORED"
    assert net.sequencers["A"].tasks["t1"].state == "CENSORED"


def test_submit_censoring_client_records_assignment_height():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    assert net.sequencers["A"].tasks["t1"].assigned_at == net.height


def test_submit_rejects_duplicate_censored_tid():
    """A duplicate tid would overwrite a live task and lose its escrow."""
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    net.submit_task("A", "dup", "kobi", spec("llama-70b"))
    with pytest.raises(ValueError, match="duplicate tid"):
        net.submit_task("A", "dup", "kobi", spec("llama-70b"))


def test_submit_evil_but_not_targeted_either_rejects_or_assigns(monkeypatch):
    """The evil sequencer's random rejection branch is still a recorded state."""
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    outcomes = set()
    for seed in range(40):
        random.seed(seed)
        out = net.submit_task("A", "t%d" % seed, "someone-else", spec("llama-70b"))
        outcomes.add(out)
        assert net.sequencers["A"].tasks["t%d" % seed].state == out
    assert outcomes <= {"ASSIGNED", "REJECTED"}
    # both branches are reachable: the coin flip is live
    assert "REJECTED" in outcomes and "ASSIGNED" in outcomes


def test_submit_rejected_branch_records_reject_height(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.4)   # < 0.5 -> REJECTED
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    net.height = 7
    out = net.submit_task("A", "t1", "other", spec("llama-70b"))
    assert out == "REJECTED"
    t = net.sequencers["A"].tasks["t1"]
    assert t.reject_at == 7
    assert t.state == "REJECTED"


def test_submit_assigned_branch_does_not_set_reject_height(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.6)   # >= 0.5 -> ASSIGNED
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    out = net.submit_task("A", "t1", "other", spec("llama-70b"))
    assert out == "ASSIGNED"
    assert net.sequencers["A"].tasks["t1"].reject_at == 0


# ---------------------------------------------------------- the testnet
def test_testnet_rejects_window_below_one_block():
    with pytest.raises(ValueError, match=r"w_r .* must be >= 1"):
        F3aTestnet([Sequencer("A")], w_r=0)
    with pytest.raises(ValueError, match=r"w_r .* must be >= 1"):
        F3aTestnet([Sequencer("A")], w_r=-5)


def test_testnet_window_is_stored():
    net = F3aTestnet([Sequencer("A")], w_r=11)
    assert net.w_r == 11


def test_next_block_increments_height_and_returns_it():
    net = F3aTestnet([Sequencer("A")])
    assert net.next_block() == 1
    assert net.next_block() == 2
    assert net.height == 2


def test_refund_guarantee_holds_inside_the_window():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    for _ in range(W_R):
        net.next_block()
        assert net.sequencers["A"].tasks["t1"].state == "CENSORED"
    assert net.refunds == 0


def test_refund_guarantee_fires_one_block_past_the_window():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "kobi", s)
    for _ in range(W_R):
        net.next_block()
    net.next_block()
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "REFUNDED"
    # the FULL fee is returned: escrow AND the earmarked burn
    assert net.refunds == 100
    assert t.escrow == 0 and t.burned == 0
    # nothing was delivered, so nothing is burned
    assert net.burn_address == 0


def test_refund_guarantee_respects_the_configured_window():
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi")], w_r=1)
    net.submit_task("A", "t1", "kobi", spec("llama-70b"))
    net.next_block()                       # height 1: 1 - 0 > 1 is False
    assert net.sequencers["A"].tasks["t1"].state == "CENSORED"
    net.next_block()                       # height 2: 2 - 0 > 1 is True
    assert net.sequencers["A"].tasks["t1"].state == "REFUNDED"


# ------------------------------------------------------------ settle_task
def test_settle_happy_path_burns_and_clears_the_escrow():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "t1", "buyer", spec("llama-70b", fee=100, burn_rate=0.3))
    assert net.solve_task("A", "t1", "result")
    assert net.settle_task("A", "t1")
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "SETTLED"
    assert net.burn_address == 30
    assert t.escrow == 0 and t.burned == 0


def test_settle_requires_solved_or_challenged_state():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "t1", "buyer", spec("llama-70b"))
    assert net.settle_task("A", "t1") is False     # still ASSIGNED
    assert net.solve_task("A", "t1", "r")
    assert net.settle_task("A", "t1") is True


def test_settle_unknown_task_is_false():
    net = F3aTestnet([Sequencer("A")])
    assert net.settle_task("A", "nope") is False


def test_settle_first_failure_challenges_and_burns_nothing():
    net = F3aTestnet([Sequencer("A", bond=100)])
    net.submit_task("A", "t1", "buyer", spec("llama-70b"))
    net.solve_task("A", "t1", "r")
    burn_before = net.burn_address
    assert net.settle_task("A", "t1", verify_ok=False) is False
    t = net.sequencers["A"].tasks["t1"]
    assert t.state == "CHALLENGED"
    assert net.burn_address == burn_before      # nothing burned on a warning
    assert net.slash_events == 0                # ...and nothing slashed
    assert net.dilemma_triggers == 1


def test_settle_second_failure_slashes_refunds_and_refills():
    net = F3aTestnet([Sequencer("A", bond=100)])
    s = spec("llama-70b", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", s)
    net.solve_task("A", "t1", "r")
    net.settle_task("A", "t1", verify_ok=False)             # CHALLENGED
    assert net.settle_task("A", "t1", verify_ok=False) is False
    t = net.sequencers["A"].tasks["t1"]
    sq = net.sequencers["A"]
    assert t.state == "SLASHED"
    # the bond is cut by min(bond, fee) and REFILLED so the next event bites
    assert sq.slashed == 100
    assert sq.bond == 100
    assert net.slash_events == 1
    # the buyer is made whole on the full fee; nothing is burned
    assert net.refunds == 100
    assert net.burn_address == 0
    assert t.escrow == 0 and t.burned == 0


def test_settle_slash_is_capped_by_the_bond():
    net = F3aTestnet([Sequencer("A", bond=40)])
    net.submit_task("A", "t1", "buyer", spec("llama-70b", fee=100))
    net.solve_task("A", "t1", "r")
    net.settle_task("A", "t1", verify_ok=False)
    net.settle_task("A", "t1", verify_ok=False)
    assert net.sequencers["A"].slashed == 40    # min(40, 100)
    # refill restores to max(floor, fee): the bond can absorb the next slash
    assert net.sequencers["A"].bond == max(BOND_DEFAULT, 100)


def test_settle_challenged_task_can_still_settle():
    """A challenge is a repair window, not a death sentence (spec A.5.2)."""
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "t1", "buyer", spec("llama-70b"))
    net.solve_task("A", "t1", "r")
    net.settle_task("A", "t1", verify_ok=False)             # CHALLENGED
    assert net.settle_task("A", "t1", verify_ok=True)       # repair -> SETTLED
    assert net.sequencers["A"].tasks["t1"].state == "SETTLED"
    assert net.burn_address == 30


def test_solve_task_requires_assigned_state():
    net = F3aTestnet([Sequencer("A")])
    net.submit_task("A", "t1", "buyer", spec("llama-70b"))
    assert net.solve_task("A", "t1", "r") is True
    # a second solve on a SOLVED task is refused
    assert net.solve_task("A", "t1", "r2") is False
    assert net.solve_task("A", "ghost", "r") is False


# ------------------------------------------------------------ migrate_task
def test_migrate_slashes_refills_and_reassigns():
    net = _evil_net(bond=100, bond_b=100)
    net.submit_task("A", "t2", "kobi", spec("llama-70b", fee=100))
    assert net.migrate_task("t2", "A", "B") is True
    a, b = net.sequencers["A"], net.sequencers["B"]
    assert a.slashed == 100
    assert a.bond == 100                 # refilled after the slash
    assert a.tasks == {}                 # the old task is closed on A
    assert b.tasks["t2"].state == "ASSIGNED"
    assert net.slash_events == 1 and net.migrations == 1
    # the migrated task walks the rest of the road on B
    assert net.solve_task("B", "t2", "r")
    assert net.settle_task("B", "t2")
    assert net.burn_address == 30


def test_migrate_slash_is_capped_by_the_bond():
    net = _evil_net(bond=20)
    net.submit_task("A", "t2", "kobi", spec("llama-70b", fee=100))
    net.migrate_task("t2", "A", "B")
    assert net.sequencers["A"].slashed == 20


@pytest.mark.parametrize("state", ["SETTLED", "ASSIGNED", "COMMITTED", "SOLVED"])
def test_migrate_refuses_non_censorable_states(state):
    net = _evil_net()
    s = spec("llama-70b")
    net.submit_task("B", "t9", "buyer", s)
    net.sequencers["B"].tasks["t9"].state = state
    assert net.migrate_task("t9", "B", "A") is False
    assert net.slash_events == 0 and net.migrations == 0


def test_migrate_unknown_task_is_false():
    net = _evil_net()
    assert net.migrate_task("ghost", "A", "B") is False
    assert net.migrations == 0


# ---------------------------------------------------------- assign_by_vrf
def test_vrf_assignment_is_deterministic():
    def _one():
        net = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
        net.height = 7
        return net.assign_by_vrf("task-z", "buyer-1",
                                 spec("h", fee=100, burn_rate=0.3))

    assert _one() == _one()


def test_vrf_assignment_spreads_over_all_sequencers():
    net = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
    hits = {}
    for i in range(80):
        sid = net.assign_by_vrf("t-%d" % i, "buyer-x",
                                spec("h%d" % i, fee=100, burn_rate=0.3))
        hits[sid] = hits.get(sid, 0) + 1
    assert set(hits) == {"sq0", "sq1", "sq2", "sq3"}
    assert all(v > 0 for v in hits.values())


def test_vrf_assignment_mixes_the_client_identity():
    """A buyer cannot steer a task by picking a task id: the client is in the mix."""
    def _with(client):
        net = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
        net.height = 3
        return net.assign_by_vrf("task-w", client,
                                 spec("h", fee=100, burn_rate=0.3))

    assert _with("buyer-1") != _with("buyer-2")


def test_vrf_assignment_respects_the_height():
    def _at(height):
        net = F3aTestnet([Sequencer("sq%d" % i) for i in range(4)])
        return net.assign_by_vrf("task-q", "buyer-1",
                                 spec("h", fee=100, burn_rate=0.3), height=height)

    assert _at(1) == _at(1)
    # the height is an explicit input, so moving it can move the assignment
    assert isinstance(_at(1), str) and isinstance(_at(2), str)


def test_vrf_assignment_on_empty_pool_raises():
    net = F3aTestnet([])
    with pytest.raises(ValueError, match="no sequencer is registered"):
        net.assign_by_vrf("t1", "buyer", spec("h"))


def test_vrf_assignment_submits_the_task_to_the_chosen_sequencer():
    net = F3aTestnet([Sequencer("sq%d" % i) for i in range(3)])
    sid = net.assign_by_vrf("t1", "buyer", spec("h"))
    assert net.sequencers[sid].tasks["t1"].state == "ASSIGNED"


# ------------------------------------------------------------ DemandMeter
def _meter_with_refunded_slashed():
    """A net holding one REFUNDED and one SLASHED terminal task."""
    net = F3aTestnet([Sequencer("A", evil=True, censor_client="kobi"),
                      Sequencer("B", evil=False)])
    net.submit_task("A", "c1", "kobi", spec("llama-70b"))
    for _ in range(W_R + 2):
        net.next_block()
    assert net.sequencers["A"].tasks["c1"].state == "REFUNDED"
    net.submit_task("B", "s1", "ali", spec("llama-70b"))
    net.solve_task("B", "s1", "res")
    net.settle_task("B", "s1", verify_ok=False)
    net.settle_task("B", "s1", verify_ok=False)
    assert net.sequencers["B"].tasks["s1"].state == "SLASHED"
    return net


def test_demand_meter_phi_is_zero_with_no_blocks():
    m = DemandMeter()
    assert m.phi() == 0.0
    assert "NO DATA" in m.verdict()


def test_demand_meter_phi_is_zero_in_a_demandless_world():
    net = F3aTestnet([Sequencer("sq0")])
    m = DemandMeter()
    for _ in range(20):
        net.next_block()
        m.record_block(net)
    assert m.phi() == 0.0
    assert m.paid_tasks == 0
    assert "PEARL" in m.verdict()


def test_demand_meter_phi_rises_with_a_settled_task():
    sq = Sequencer("sq1")
    net = F3aTestnet([sq])
    m = DemandMeter()
    paid = 0
    for i in range(20):
        net.height += 1
        if i == 5:
            t = sq.tasks["t1"] = f3a.Task(tid="t1", client="b", spec=spec("h"))
            t.state = "SETTLED"
            paid += 1
        m.record_block(net)
    assert m.paid_tasks == paid == 1
    assert m.phi() > 0.0
    assert "demand is real" in m.verdict() or "marginal" in m.verdict()


def test_demand_meter_verdict_marginal_band():
    sq = Sequencer("sq1")
    net = F3aTestnet([sq])
    m = DemandMeter()
    # exactly one settled task in 20 blocks: phi = 0.05 < 0.10 threshold
    t = sq.tasks["t1"] = f3a.Task(tid="t1", client="b", spec=spec("h"))
    t.state = "SETTLED"
    for _ in range(20):
        net.height += 1
        m.record_block(net)
    assert m.phi() == pytest.approx(0.05)
    assert "marginal" in m.verdict()


def test_demand_meter_counts_terminal_states_once():
    """TV-50's regression guard: lingering terminal tasks are not recounted."""
    net = _meter_with_refunded_slashed()
    m = DemandMeter()
    for _ in range(30):
        net.next_block()
        m.record_block(net)
    assert m.refunded_tasks == 1
    assert m.slashed_tasks == 1
    assert m.paid_tasks == 0 and m.phi() == 0.0


def test_demand_meter_reads_migrations_from_the_event_counter():
    net = _evil_net()
    m = DemandMeter()
    net.submit_task("A", "c2", "kobi", spec("llama-70b"))
    net.migrate_task("c2", "A", "B")
    net.next_block()
    m.record_block(net)
    # MIGRATED is never observable by state; the network counter is the source
    assert m.migrated_tasks == 1


# --------------------------------------------------- run_demand_scenario
def test_run_demand_scenario_demandless_is_phi_zero():
    rng = random.Random(7)
    nobody = [("ghost-%d" % i, 0.0, 100, 0.3) for i in range(5)]
    r = run_demand_scenario(rng, nobody, 200)
    assert r["arrivals"] == 0
    assert r["settled"] == 0
    assert r["phi_final"] == 0.0
    assert r["fees_paid"] == 0
    assert all(p == 0.0 for p in r["phi_path"])


def test_run_demand_scenario_settles_every_arrival():
    rng = random.Random(31415)
    # a single buyer with one fixed fee, so the fee accounting is exact
    some = [("lab-1", 0.2, 177, 0.3)]
    r = run_demand_scenario(rng, some, 200)
    assert r["arrivals"] > 0
    assert r["settled"] == r["arrivals"]
    assert r["phi_final"] > 0.0
    assert r["fees_paid"] == r["settled"] * 177


def test_run_demand_scenario_phi_path_length_equals_blocks():
    rng = random.Random(11)
    r = run_demand_scenario(rng, [("x", 0.0, 100, 0.3)], 37)
    assert len(r["phi_path"]) == 37
    assert r["blocks"] == 37


def test_buyer_population_arrivals_follow_the_rate():
    rng = random.Random(99)
    pop = BuyerPopulation(rng, [("a", 1.0, 100, 0.3), ("b", 0.0, 100, 0.3)])
    a_hits = sum(1 for _ in range(50) if pop.arrivals_at(_))
    # rate 1.0 always arrives, rate 0.0 never does
    assert a_hits == 50
    assert all(pop.arrivals_at(h) == [("a", 100, 0.3)] for h in range(3))


# ------------------------------------------------- the shipped test vectors
def test_tv17_censorship_is_not_free():
    """TV-17: 3 timeout-refunds + 2 migrations; the bond is slashed and raised."""
    assert f3a.tv17() is True


def test_tv20_bond_refill_is_not_one_shot():
    """TV-20: with refill every event slashes; without it the rest are free."""
    assert f3a.tv20() is True


def test_tv24_slashing_attack_case():
    """TV-24: challenge -> slash -> full refund, nothing burned, not settled."""
    (first_fail, challenged, nothing_burned_yet,
     slashed, buyer_refunded, nothing_burned, not_settled) = \
        f3a.tv24_slashing_attack_case()
    assert (first_fail, challenged, nothing_burned_yet) == (True, True, True)
    assert slashed is True
    assert buyer_refunded is True
    assert nothing_burned is True
    assert not_settled is True


def test_tv69_refund_rate_measured_books_balance():
    """TV-69: across a mixed load the books balance exactly."""
    r = f3a.tv69_refund_rate_measured()
    assert r["tasks"] == 300
    assert r["fees_in"] == 30000
    assert r["books_balance"] is True
    assert 0.0 < r["refund_rate"] < 1.0
    # the slashed bond is a penalty, tracked apart from the fee books
    assert r["slashed_bonds"] > 0
    assert (r["fees_refunded"] + r["fees_burned"] + r["fees_paid"]) == r["fees_in"]


def test_tv25_vrf_assignment_vector():
    spread, deterministic, identity_matters, hits = f3a.tv25_vrf_assignment()
    assert spread is True
    assert deterministic is True
    assert identity_matters is True
    assert sum(hits.values()) == 80


def test_tv50_terminal_states_counted_once():
    assert f3a.tv50_terminal_states_counted_once() is True


def test_tv81_slash_is_not_oneshot():
    """TV-81: five consecutive failures punish five times, bond stays healthy."""
    assert f3a.tv81_slash_is_not_oneshot() is True


def test_tv44_refund_books_balance():
    """TV-44: a timed-out task refunds the FULL fee, books included."""
    assert f3a.tv44_refund_books_balance() is True
