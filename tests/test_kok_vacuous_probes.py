"""The three probes DERS 265 named VACUOUS, fixed in place and pinned on
both arms.

r5d4 (round5d_ghost), r5d2 (round5d_ulayer) and r5e2 (round5e_f3a) each used
to return True through a path that measured nothing: r5d4 wrapped its
measurement in `except Exception: pass` and the loop died on its FIRST
iteration (mergesets' first key is the genesis block, whose selected parent
is None, so _anticone(None) raised KeyError), r5d2 fell back to "could not
drive" and returned True when the chain exposed no books_balance hook, and
r5e2 returned True from an early "CANNOT DRIVE" branch because the module
has no challenge(). A run that measured NOTHING was reported identically to a
run that measured zero.

ROUND-6, 2026-10-07: the three probe functions were fixed where they stood.
r5d4 skips the genesis-like block before _anticone is ever called and counts
a measurement error as a reported finding rather than a swallowed pass, and
its yardstick is TV-59's own (a mergeset member must lie in past(B)) instead
of the earlier ac(sp) & past(B) formula that reported a false excess of its
own. r5d2 reads the fee invariant from the ledger's own books -- the task's
fee/burned/escrow fields and the burn-address balance -- so it measures
whether or not the chain exposes a convenience hook. r5e2 drives the
slash-before-settle corner through settle_task's verify_ok=False arm, which
is the module's challenge surface (a first failure CHALLENGEs, a second
SLASHes and refunds the buyer).

These tests pin BOTH arms of each fix:

  1. the honest arm -- the probe passes on the unbroken module BECAUSE it
     measured, and its output proves the measurement ran (members inspected,
     books read, the corner driven) rather than asserting the verdict alone;
  2. the claimed measurement, run DIRECTLY -- the invariant the probe names
     is measured here independently, so the coverage the probe was supposed
     to provide actually lands; and
  3. the fault arm -- the measurement is broken by a scoped monkeypatch in a
     way that CANNOT be mistaken for a legitimate zero, the fault's reality
     is proven directly, and the probe is shown to now REJECT it. Before the
     fix this arm returned the identical clean bill of health; a probe that
     could not distinguish "measured 0" from "measured nothing" was
     unfalsifiable, and that is the class of defect these tests pin.

The faults are applied as context-managed monkeypatches so the modules are
restored before the next test. stdlib only.
"""

import contextlib
import inspect
import io
import random
import re

import pytest
from unittest import mock

import f3a_sequencer_proto_en as f3a_mod
import ghostdag_proto_en as ghost_mod
import probe_round5d_ghost_en as probe_ghost
import probe_round5d_ulayer_en as probe_ulayer
import probe_round5e_f3a_en as probe_f3a
import u_layer_prototype_en as ul_mod


# ------------------------------------------------------------------ helpers
def _run(fn):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn()
    return rv, buf.getvalue()


def _drive_u_layer(seed=3):
    """The smallest honest U-layer task: enough empty blocks to seed the VRF
    epoch, then submit -> assign -> mine -> validate. Mirrors r5d2's own
    setup so the comparison is like-for-like."""
    ch = ul_mod.Chain()
    rng = random.Random(seed)
    zero = [[0] * 8 for _ in range(8)]
    for _ in range(ul_mod.EPOCH_LOOKBACK + 4):
        blk = ch.mine_block("m1", [], zero, zero)
        ch.validate_block(blk, zero, zero)
    A = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
    B = [[rng.randrange(97) for _ in range(8)] for _ in range(8)]
    spec = ul_mod.TaskSpec("mm", (A, B), 64, 1000)
    t = ch.submit_task("c1", spec, 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A, B)
    ch.validate_block(blk, A, B)
    return ch, t


def _build_dag(seed, k=18):
    """A random DAG in the probe's own generator style: 12-40 blocks, one or
    two parents, so the mergeset/anticone structure is exercised."""
    rg = random.Random(seed)
    net = ghost_mod.GHOSTDAG(k=k)
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
        blk = ghost_mod.Block("m%d" % b, list(parents), b, [])
        net.add(blk)
        blocks.append(blk)
    return net


def _mergeset_outside_past(net):
    """TV-59's own invariant, as the module states it: the mergeset "only
    contains work B knows", i.e. every member must be in past(B). Before the
    2026-09-23 fix the mergeset admitted all of anticone(sp) and put 572
    order entries outside a block's own past; after it the count must be 0.
    Genesis-like blocks have no selected parent and an empty mergeset, so
    they are skipped."""
    worst = 0
    measured = 0
    for bid, ms in net.mergesets.items():
        if net.selected.get(bid) is None:
            continue
        past_b = net._past(bid)
        worst = max(worst, sum(1 for x in ms if x not in past_b))
        measured += len(ms)
    return worst, measured


def _probe_yardstick(net):
    """The formula r5d4 actually prints: mergeset members outside
    ac(sp) & past(B). This is NOT TV-59 -- it also counts mergeset members
    inherited from m(sp) that lie in past(sp) but outside anticone(sp) --
    so on a forked DAG it reports 1 where TV-59 reports 0."""
    worst = 0
    for bid, ms in net.mergesets.items():
        sp = net.selected.get(bid)
        if sp is None:
            continue
        ac_sp = net._anticone(sp)
        past_b = net._past(bid)
        worst = max(worst, sum(1 for x in ms if x not in (ac_sp & past_b)))
    return worst


# ==================================================== R5D-4: the fix
def test_r5d4_probe_passes_on_the_honest_module():
    rv, out = _run(probe_ghost.r5d4_mergeset_deviation_across_many_seeds_and_sizes)
    assert rv, "R5D-4 passes on the honest module because the deviation is 0"
    members = int(re.search(r"mergeset members inspected: (\d+)", out).group(1))
    errors = int(re.search(r"measurement errors: (\d+)", out).group(1))
    assert members > 0, \
        "the pass must come from a measurement that ran, not a swallowed loop"
    assert errors == 0


def test_r5d4_the_claimed_deviation_is_zero_when_measured_directly():
    # the measurement r5d4 NAMES (TV-59: mergeset deviation is 0), run
    # without the except-swallow: no mergeset member may lie outside past(B)
    worst = 0
    runs = 0
    measured = 0
    for seed in list(range(12)) + [20260920, 777]:
        for _ in range(2):
            net = _build_dag(seed)
            runs += 1
            w, m = _mergeset_outside_past(net)
            worst = max(worst, w)
            measured += m
    assert runs == 28, "the direct sweep must build the DAGs it reports on"
    assert measured > 0, "the sweep must actually inspect non-empty mergesets"
    assert worst == 0, \
        "TV-59 must hold when measured directly: no mergeset member may lie " \
        "outside its block's own past"


def test_r5d4s_measurement_loop_used_to_die_on_its_first_iteration():
    # WHY the probe USED TO print 0 on every run (DERS 265, fixed 2026-10-07):
    # its loop started at the genesis block, whose selected parent is None,
    # so _anticone(None) raised and the `except Exception: pass` ate the whole
    # per-DAG measurement. The fixed probe skips the genesis-like block, so
    # this is the mechanism the fix removed rather than a live defect.
    net = _build_dag(0)
    first = next(iter(net.mergesets))
    assert net.selected[first] is None, \
        "the genesis block has no selected parent, and it is mergesets' first key"
    with pytest.raises(KeyError):
        net._anticone(net.selected[first])

    # and the pass criterion the probe USED TO return was unsatisfiable by
    # its OWN printed yardstick on these honest DAGs: that formula counts
    # inherited mergeset members as excess, so worst would be >= 1, not the 0
    # the return required. The True it returned could only come from the
    # swallow. The fixed probe therefore measures TV-59's own invariant
    # (membership in past(B)) instead, which is why it can honestly report 0
    worst = 0
    for seed in list(range(12)) + [20260920, 777]:
        for _ in range(2):
            worst = max(worst, _probe_yardstick(_build_dag(seed)))
    assert worst >= 1, \
        "the old yardstick was non-zero on honest DAGs, which is why the " \
        "fixed probe no longer uses it"


class _ItemsRaiseDict(dict):
    """A mergeset/selected table whose .items() raises. add() only uses
    __getitem__/__setitem__/.get, so the DAG still builds -- only the
    probe's measurement loop, which iterates .items(), dies."""

    def items(self):
        raise RuntimeError("measurement broken")


def test_r5d4_now_rejects_a_measurement_that_raises():
    orig_init = ghost_mod.GHOSTDAG.__init__

    def patched_init(self, *a, **k):
        orig_init(self, *a, **k)
        self.mergesets = _ItemsRaiseDict(self.mergesets)
        self.selected = _ItemsRaiseDict(self.selected)

    # the fault is REAL: the DAG still builds (add() is unaffected) but the
    # exact iteration the probe's measurement loop performs now raises
    with mock.patch.object(ghost_mod.GHOSTDAG, "__init__", patched_init):
        net = _build_dag(5)
        assert len(net.blocks) > 1, "block generation must still succeed"
        try:
            net.mergesets.items()
        except RuntimeError as e:
            fault_real = str(e)
        else:
            fault_real = None
    assert fault_real == "measurement broken", \
        "the measurement path must raise while block generation still works"

    # ...and the probe no longer swallows it: the sweep still builds its DAGs
    # but inspects no mergeset member, reports every DAG as a measurement
    # error, and FAILS. Before the 2026-10-07 fix this arm printed the
    # identical clean bill of health (n_runs > 0, worst 0, verdict True)
    # because `except Exception: pass` ate the only loop that could have
    # produced a different number
    with mock.patch.object(ghost_mod.GHOSTDAG, "__init__", patched_init):
        rv, out = _run(probe_ghost.r5d4_mergeset_deviation_across_many_seeds_and_sizes)
    n_runs = int(re.search(r"generator runs across seeds and sizes: (\d+)", out).group(1))
    members = int(re.search(r"mergeset members inspected: (\d+)", out).group(1))
    errors = int(re.search(r"measurement errors: (\d+)", out).group(1))
    worst = int(re.search(r"worst mergeset excess.*?: (\d+)", out).group(1))
    assert n_runs > 0, "the DAGs still build; it is the measurement that broke"
    assert members == 0, "a broken measurement must inspect nothing"
    assert errors > 0, "the broken measurement must be reported, not swallowed"
    assert worst == 0, "the printed 0 now means 'never measured', and the probe says so"
    assert not rv, \
        "R5D-4 is no longer VACUOUS: a measurement that raises now fails the " \
        "probe instead of passing it, so its 0 can be told apart from a " \
        "measurement that never ran"


# ==================================================== R5D-2: the fix
def test_r5d2_probe_passes_on_the_honest_module():
    rv, out = _run(probe_ulayer.r5d2_the_fee_invariant_survives_a_slashed_settled_and_refunded_task)
    assert rv, "R5D-2 passes on the honest module because the invariant holds"
    assert "the fee invariant holds across every terminal state: True" in out, \
        "it passes by measuring the books, not via the could-not-drive fallback"
    assert "could not drive" not in out.lower(), \
        "the missing-hook fallback that returned True is gone"
    assert not hasattr(ul_mod.Chain, "books_balance"), \
        "the chain still exposes no books_balance hook -- the probe measures " \
        "the invariant from the ledger's own fields, which is the fix"


def test_r5d2_the_fee_invariant_holds_when_checked_directly():
    # the invariant r5d2 NAMES (fees_in == refunded + burned + paid), checked
    # without the missing-hook fallback: settle pays the escrow exactly once
    ch, t = _drive_u_layer()
    task = ch.tasks[t.tid]
    assert (task.burned, task.escrow) == (10, 90), "100 fee, 0.1 burn"
    assert ch.burn_address_balance == 10, "the burn is collected at submission"

    pay1 = ch.settle(t.tid)
    mid = (task.escrow, task.state)
    pay2 = ch.settle(t.tid)
    after = (task.escrow, task.state)

    assert pay1 == 90, "the first settle pays fee - burned"
    assert pay2 == 0, "a settled task must pay nothing the second time"
    assert mid == after == (0, "SETTLED"), "the books must not move twice"
    assert task.escrow >= 0, "the escrow must never go negative"


def _settle_without_a_terminal_guard(self, tid):
    """The bug the double-settle guard exists for: the SETTLED state is no
    longer checked, so a second settle pays the escrow again."""
    t = self.tasks[tid]
    t.state = "SETTLED"
    pay = t.fee - t.burned
    t.escrow -= pay
    return pay


def test_r5d2_now_rejects_a_broken_settle():
    # the fault is REAL: with the terminal guard gone the books go negative
    with mock.patch.object(ul_mod.Chain, "settle",
                           _settle_without_a_terminal_guard):
        ch, t = _drive_u_layer()
        pay1 = ch.settle(t.tid)
        pay2 = ch.settle(t.tid)
        task = ch.tasks[t.tid]
    assert (pay1, pay2) == (90, 90), "the second settle must pay again"
    assert task.escrow == -90, "the escrow must be driven negative"
    assert task.state == "SETTLED"

    # the probe reads the ledger's own books now, so the violation it prints
    # is the violation it ACTS ON: the imbalance is measured and the probe
    # fails with it. Before the 2026-10-07 fix the chain exposed no
    # books_balance hook, so the probe announced the violation in its own
    # output and returned PASS anyway
    with mock.patch.object(ul_mod.Chain, "settle",
                           _settle_without_a_terminal_guard):
        rv, out = _run(probe_ulayer.r5d2_the_fee_invariant_survives_a_slashed_settled_and_refunded_task)
    assert "second settle paid: 90" in out, \
        "the probe must print the violation it now acts on"
    assert "fee 100 == burned 10 + paid 180" in out, \
        "the imbalance must be measured, not assumed away"
    assert "escrow after both settles: -90" in out
    assert not rv, \
        "R5D-2 is no longer VACUOUS: a broken settle fails the probe instead " \
        "of passing it, because the invariant is read from the ledger's own " \
        "books rather than a hook the chain does not expose"


# ==================================================== R5E-2: the fix
def test_r5e2_probe_passes_on_the_honest_module():
    rv, out = _run(probe_f3a.r5e2_slash_before_settle_still_makes_the_buyer_whole)
    assert rv, "R5E-2 passes on the honest module because the buyer is made whole"
    assert "CANNOT DRIVE" not in out, \
        "the no-challenge early return that passed without measuring is gone"
    assert "refunded to the buyer: 100 (the full fee is 100)" in out, \
        "the slash-before-settle corner is now driven and its books measured"
    assert "the buyer is whole and the books balance: True" in out


def test_r5e2s_challenge_surface_is_the_settle_arm():
    # the module has no standalone challenge(): the challenge surface the
    # fixed probe drives is settle_task's verify_ok=False arm (a first failure
    # CHALLENGEs, a second SLASHes and refunds the buyer), which is why the
    # probe drives the corner through it rather than a per-task handle
    src = inspect.getsource(f3a_mod)
    assert "def challenge" not in src, \
        "the module has no challenge() -- the corner is driven through " \
        "settle_task's verify_ok=False arm, not a per-task handle"
    assert not hasattr(f3a_mod.F3aTestnet, "challenge_task")
    assert hasattr(f3a_mod.F3aTestnet, "settle_task"), \
        "the settle arm the probe drives is the one the module does expose"


def _settle_that_pays_an_undelivered_task(self, seq_id, tid, verify_ok=True):
    """The bug TV-24 names from the other direction: the buyer is NOT made
    whole -- the escrow pays the miner even though nothing was delivered."""
    t = self.sequencers[seq_id].tasks.get(tid)
    if t is None:
        return False
    t.state = "SETTLED"
    t.escrow = 0
    return 70


def test_r5e2_now_rejects_a_settle_that_mispays():
    seqs = [f3a_mod.Sequencer("A", bond=100)]
    net = f3a_mod.F3aTestnet(seqs)
    spec = f3a_mod.spec("mm", fee=100, burn_rate=0.3)
    net.submit_task("A", "t1", "buyer", spec)

    # the fault is REAL: the buyer's escrow leaves with the task unresolved
    with mock.patch.object(f3a_mod.F3aTestnet, "settle_task",
                           _settle_that_pays_an_undelivered_task):
        pay = net.settle_task("A", "t1")
    assert pay == 70, "the fault must actually mispay the buyer"

    # the probe reads the books now, so the mispay is visible and fails it:
    # the task never reaches SLASHED and nothing is refunded. Before the
    # 2026-10-07 fix the probe never reached the driving arm (no challenge()
    # => early return True), so a broken payout was invisible to it
    with mock.patch.object(f3a_mod.F3aTestnet, "settle_task",
                           _settle_that_pays_an_undelivered_task):
        rv, out = _run(probe_f3a.r5e2_slash_before_settle_still_makes_the_buyer_whole)
    assert "refunded to the buyer: 0 (the full fee is 100)" in out, \
        "the fault must show up in the books the probe measures"
    assert not rv, \
        "R5E-2 is no longer the same class as the old R5D-2/R5D-4: a settle " \
        "that pays an undelivered task now fails the probe instead of " \
        "passing it before any measurement ran"
