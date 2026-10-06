"""The two remaining untested 40+ line GHOSTDAG probes, branch-cut.

An AST sweep of the 47 root prototype modules (public, non-underscore
functions of 40+ lines whose name never appears under tests/) left 21
functions. These two are the consensus-ordering survivors, and each maps to
a Rust crate in crates/ that already carries its own cargo suite:

  probe_ghostdag_en.tv58_blue_score_does_not_decrease_along_selected_chain
      -> crates/kok-ghostdag (the blue-score walk the chain crate tests)
  probe_blindspot_en.probe_ghostdag_minimal_deviation
      -> crates/kok-ghostdag (the TV-59 mergeset/order containment)

The module-level invariants these probes guard are already covered by
tests/test_ghostdag_proto.py; what was NOT covered was the probe layer
itself. That matters here because this project has been bitten repeatedly by
probes that pass without measuring anything (a loop that never executed, a
violations count that was zero by construction, an exception swallowed by a
bare `except`). So every probe below is cut on BOTH arms:

  - the honest arm: the probe runs on the current module and its verdict /
    measured counts are what the property claims, and
  - the fault arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE — proving the verdict is earned
    rather than unfalsifiable.

Faults are applied with unittest.mock.patch.object as context managers, so
the module is restored before the next test. Nothing outside this file is
modified. stdlib only.
"""

import contextlib
import io
import random
import re

import pytest
from unittest import mock

import ghostdag_proto_en as gd
import probe_ghostdag_en as probe_ghostdag
import probe_blindspot_en as probe_blindspot


# ------------------------------------------------------------------ helpers
def _run(fn):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn()
    return rv, buf.getvalue()


def _forked_dag(seed=23, n=50):
    """The TV-59 generator: sparse parent sets off the growing tip set, so
    the DAG has real anticone structure (the mine_chain generator with
    fork_prob=0 is too dense to exercise the mergeset intersection)."""
    g = gd.GHOSTDAG(gd.GHOSTDAG_K)
    rng = random.Random(seed)
    genesis = gd.Block("A", [], 0)
    g.add(genesis)
    tips = [genesis.bid]
    for i in range(n):
        cnt = rng.randint(1, min(3, len(tips)))
        parents = rng.sample(tips, cnt)
        blk = gd.Block("M%d" % (i % 4), parents, i + 1)
        g.add(blk)
        tips.append(blk.bid)
    return g


def _selected_edges(g):
    """Every (block -> selected_parent) edge, walked back from each block."""
    for bid in g.blocks:
        cur, seen = bid, 0
        while g.selected.get(cur) is not None and seen < 200:
            yield bid, cur, g.selected[cur]
            cur = g.selected[cur]
            seen += 1


@contextlib.contextmanager
def _mergeset_without_past_intersection():
    """Revert the Stage-1.1 TV-59 fix: add ALL of anticone(sp) to the
    mergeset instead of anticone(sp) INTERSECT past(B). The mergeset then
    admits work the block never referenced, which is the regression both
    probes exist to surface."""
    def buggy_compute(self, bid):
        blk = self.blocks[bid]
        if not blk.parents:
            self.mergesets[bid] = set()
            self.selected[bid] = None
            self.blue_score[bid] = 1
            self.is_blue[bid] = True
            return
        scored = [(self.blue_score.get(p, 0), p) for p in blk.parents
                  if p in self.blocks]
        if not scored:
            self.mergesets[bid] = set()
            self.selected[bid] = None
            self.blue_score[bid] = 1
            self.is_blue[bid] = True
            return
        sp = max(scored, key=lambda x: (x[0], -int(x[1], 16)))[1]
        self.selected[bid] = sp
        ms = set(self.mergesets.get(sp, set()))
        ac_sp = self._anticone(sp)
        # the fault: the & self._past(bid) intersection is dropped
        for cand in sorted(ac_sp, key=lambda x: int(x, 16)):
            if len(ms) >= gd.MERGESET_SIZE_LIMIT:
                break
            ms.add(cand)
        self.mergesets[bid] = ms
        for b in ms:
            self.is_blue[b] = len(self._anticone(b) & ms) <= self.k
        self.is_blue[bid] = True
        blue = sum(1 for b in ms if self.is_blue.get(b, False))
        base = self.blue_score.get(sp, 0) if sp is not None else 0
        self.blue_score[bid] = base + blue + 1

    with mock.patch.object(gd.GHOSTDAG, "_compute", buggy_compute):
        yield


@contextlib.contextmanager
def _score_not_carried_forward():
    """Revert the blue-score carry-forward: score the block from its own
    mergeset alone instead of adding the selected parent's score. Real
    GHOSTDAG cannot do this — each child builds on its parent's score — and
    the delta along the selected chain collapses to 0."""
    original = gd.GHOSTDAG._compute

    def buggy_compute(self, bid):
        original(self, bid)
        ms = self.mergesets.get(bid, set())
        blue = sum(1 for b in ms if self.is_blue.get(b, False))
        # the fault: the selected parent's score is not added
        self.blue_score[bid] = 0 + blue + 1

    with mock.patch.object(gd.GHOSTDAG, "_compute", buggy_compute):
        yield


# ============================================ TV-58: the blue-score walk
def test_tv58_probe_passes_on_the_honest_module():
    rv, _ = _run(probe_ghostdag.tv58_blue_score_does_not_decrease_along_selected_chain)
    assert rv, "the TV-58 probe must hold on the current module"


def test_tv58_the_score_strictly_increases_toward_the_selected_parent():
    g = _forked_dag()
    deltas = [g.blue_score[child] - g.blue_score[sp]
              for _b, child, sp in _selected_edges(g)]
    assert deltas, "the DAG must produce at least one selected edge"
    assert all(d >= 1 for d in deltas), \
        "a child's blue_score must exceed its selected parent's"
    assert min(deltas) == 1


def test_tv58_detects_a_score_that_is_not_carried_forward():
    with _score_not_carried_forward():
        rv, _ = _run(
            probe_ghostdag.tv58_blue_score_does_not_decrease_along_selected_chain)
    assert not rv, \
        "TV-58 must fail when blue_score stops carrying the parent's score"


def test_tv58_the_carry_forward_is_load_bearing_on_the_walk():
    with _score_not_carried_forward():
        g = _forked_dag()
        deltas = [g.blue_score[child] - g.blue_score[sp]
                  for _b, child, sp in _selected_edges(g)]
    assert deltas
    assert not all(d >= 1 for d in deltas), \
        "dropping the carry-forward must flatten at least one edge"


# ============================== TV-59: the mergeset / order containment
def test_minimal_deviation_probe_passes_and_measures_zero_deviation():
    rv, out = _run(probe_blindspot.probe_ghostdag_minimal_deviation)
    assert rv, "the probe must complete on the current module"
    counts = [int(v) for v in re.findall(r"outside=(\d+)", out)]
    # four mine_chain sizes (5,10,20,51) + the tv59 generator at two seeds
    assert len(counts) == 6, "the probe must print six outside= measurements"
    assert all(c == 0 for c in counts), \
        "every order entry must lie inside its block's own past: %s" % (counts,)


def test_minimal_deviation_measurement_surfaces_a_regressed_mergeset():
    with _mergeset_without_past_intersection():
        rv, out = _run(probe_blindspot.probe_ghostdag_minimal_deviation)
        counts = [int(v) for v in re.findall(r"outside=(\d+)", out)]
    assert rv, "the probe still completes (it measures, it does not gate)"
    assert any(c != 0 for c in counts), \
        "a mergeset that drops the past(B) intersection must show up as " \
        "nonzero deviation in the probe's own measurements: %s" % (counts,)


def test_order_stays_within_past_plus_self_on_a_forked_dag():
    g = _forked_dag()
    outside = [(b, x) for b in g.blocks for x in g.order(b)
               if x not in g._past(b) and x != b]
    assert not outside, \
        "order(B) must be contained in past(B) U {B}; offenders: %s" \
        % (outside[:5],)


def test_order_containment_is_violated_when_the_intersection_is_dropped():
    with _mergeset_without_past_intersection():
        g = _forked_dag()
        outside = [(b, x) for b in g.blocks for x in g.order(b)
                   if x not in g._past(b) and x != b]
    assert outside, \
        "dropping the past(B) intersection must put order entries outside " \
        "the block's own past — the regression TV-59 guards"


def test_the_mergeset_limit_still_bounds_the_forked_dag():
    g = _forked_dag()
    over = [b for b, ms in g.mergesets.items()
            if len(ms) > gd.MERGESET_SIZE_LIMIT]
    assert not over, "no mergeset may exceed 2k=%d" % gd.MERGESET_SIZE_LIMIT
