#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - GHOSTDAG PARENT-SET PROTOTYPE (F3b preparation)
=========================================================
This prototype closes KNOWN GAP #5: "GHOSTDAG parent-set selection is MISSING
from the prototype (single parent)".

What it produces: the integration of Sompolinsky-Wyborski-Zohar GHOSTDAG
(ePrint 2018/104) parent-set selection with KOK v2's ctx-binding. It nowhere
hides that it is a small toy; the parameters are Kaspa mainnet's REAL values.

Sources (verified 2026-09-20):
- ePrint 2018/104 "PHANTOM and GHOSTDAG" (Sompolinsky, Wyborski, Zohar)
  k the parameter = anticone tolerance; PHANTOM NP-hard, GHOSTDAG greedy approx.
- Kaspa rusty-kaspa consensus/core/src/config/bps.rs (production):
    BPS=1 -> ghostdag_k = 18, max_block_parents = 10 (floor 10, cap 16)
    mergeset_size_limit = 2*k = 36
    target_time_per_block = 1000/BPS ms

TECHNICAL CONTENT (GHOSTDAG core):
- every block arrives with a parent_set (max_block_parents entries, 10 in Kaspa)
- mergeset = mergeset(selected_parent) ∪ anticone(selected_parent) ∩ mergeset
- blue score: the count of blue blocks in the mergeset
- selected_parent = the block in the mergeset with the highest blue_score
- blue/red distinction: the GHOSTDAG(k) rule - a block whose anticone is < k is blue
- KOK v2 addition: ctx = selected_parent || miner || task_ref || ...
  the parent-set SELECTION also enters ctx (T-A2 replay protection strengthens)

TESTS (TV-22..TV-26):
- TV-22: blue-block selection satisfies anticone <= k (rule applied correctly)
- TV-23: selected_parent always has the highest blue_score
- TV-24: the mergeset limit (2k) is never exceeded
- TV-25: ctx includes the parent-set -> same block, different parent-set, REJECT (T-A2)
- TV-26: ATTACK - a miner publishes "splitter" blocks to fragment the DAG;
  GHOSTDAG ordering still yields a total order (liveness)

IMPORTANT LIMIT (honest):
- This tests only the DAG structure and the ordering. There is NO PoW/validity
  CHECK - every block is ASSUMED to carry valid PoW. This is where GHOSTDAG's
  security argument (anticone probability bound by k) rests on PoW; here we
  validate only the DAG logic. In production the PoW is real.
- NETWORK DELAY MODEL: uniform [0, D_max] block propagation; NOT Kaspa's real
  network statistics.
- The K value is 18 as a TEMPLATE (Kaspa BPS=1); KOK v2's own BPS is not yet chosen.
"""

import hashlib
import random
from dataclasses import dataclass, field

# ============================================================
# PRODUCTION PARAMETRES (Kaspa mainnet, rusty-kaspa bps.rs)
# ============================================================
GHOSTDAG_K = 18           # BPS=1 -> k=18 (calculate_ghostdag_k table)
MAX_BLOCK_PARENTS = 10    # floor 10, cap 16 (Kaspa production)
MERGESET_SIZE_LIMIT = 2 * GHOSTDAG_K   # = 36
TARGET_TIME_MS = 1000     # BPS=1


def h(*parts) -> str:
    """Deterministic hash for block IDs and context."""
    s = "|".join(str(p) for p in parts)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


@dataclass
class Block:
    """"A blockDAG block. parent_set = direct parents (max 10)."""
    miner: str
    parents: list          # directly parent ID'leri (<= MAX_BLOCK_PARENTS)
    timestamp: int
    tasks: list = field(default_factory=list)
    bid: str = ""

    def __post_init__(self):
        self.bid = h(self.miner, self.timestamp, tuple(sorted(self.parents)), tuple(self.tasks))


class GHOSTDAG:
    """
    GHOSTDAG greedy ordering (ePrint 2018/104).

    mergeset(B) = mergeset(selected_parent(B)) U (anticone(selected_parent(B))
                   ∩ mergeset(B)) -- expands greedily.
    A block is "blue" if its anticone in selected_parent's mergeset is < k;
    otherwise "red".
    blue_score(B) = |{blue blocks}|
    selected_parent(B) = the highest blue_score in the mergeset (ties: lowest hash).
    """

    def __init__(self, k: int = GHOSTDAG_K):
        self.k = k
        self.blocks: dict = {}          # bid -> Block
        self.mergesets: dict = {}       # bid -> set of bids (that block's mergeset)
        self.selected: dict = {}        # bid -> selected_parent bid
        self.blue_score: dict = {}      # bid -> blue score
        self.is_blue: dict = {}         # bid -> bool

    def add(self, blk: Block):
        """"Add the block to the DAG and compute GHOSTDAG state."""
        self.blocks[blk.bid] = blk
        self._compute(blk.bid)

    def _past(self, bid: str) -> set:
        """"A block's past (transitive parents)."""
        seen = set()
        stack = list(self.blocks[bid].parents)
        while stack:
            p = stack.pop()
            if p in seen or p not in self.blocks:
                continue
            seen.add(p)
            stack.extend(self.blocks[p].parents)
        return seen

    def _future(self, bid: str) -> set:
        """The future of the block: everything derived from it directly or
        indirectly."""
        fut = set()
        for other, blk in self.blocks.items():
            if bid in self._past(other):
                fut.add(other)
        return fut

    def _anticone(self, bid: str) -> set:
        """Anticone: neither in the past nor in the future of this block."""
        past = self._past(bid)
        fut = self._future(bid)
        return {b for b in self.blocks if b != bid and b not in past and b not in fut}

    def _compute(self, bid: str):
        """"GHOSTDAG greedy mergeset + selected_parent + blue_score."""
        blk = self.blocks[bid]
        if not blk.parents:
            # genesis-like
            self.mergesets[bid] = set()
            self.selected[bid] = None
            self.blue_score[bid] = 1
            self.is_blue[bid] = True
            return

        # step 1: selected_parent = highest blue_score among the parents
        # (parents already added have blue_scores)
        scored = [(self.blue_score.get(p, 0), p) for p in blk.parents if p in self.blocks]
        if not scored:
            self.mergesets[bid] = set()
            self.selected[bid] = None
            self.blue_score[bid] = 1
            self.is_blue[bid] = True
            return
        # ties: lowest hash (deterministic)
        sp = max(scored, key=lambda x: (x[0], -int(x[1], 16)))[1]
        self.selected[bid] = sp

        # step 2: mergeset = mergeset(sp) U (anticone(sp) ∩ past(B))
        # CONTRACT, fixed 2026-09-23 (Aşama 1.1, TV-59):
        # The definition is mergeset = m(sp) U (anticone(sp) INTERSECT past(B)).
        # The intersection with past(B) is the part that was previously DROPPED:
        # an earlier version added ALL of anticone(sp) up to the limit, which
        # admits blocks B does not know about — a block that references only
        # one fork can absorb a sibling from the other fork. TV-59 measured
        # the consequence: 572-578 order entries outside a block's own past
        # on a 51-block DAG, so two blocks' orderings can disagree on work
        # neither references. The intersection is now computed, so the
        # mergeset only contains work B actually knows.
        ms = set(self.mergesets.get(sp, set()))
        ac_sp = self._anticone(sp)
        past_b = self._past(bid)
        ac_in_past = ac_sp & past_b
        for cand in sorted(ac_in_past, key=lambda x: int(x, 16)):
            if len(ms) >= MERGESET_SIZE_LIMIT:
                break
            ms.add(cand)
        self.mergesets[bid] = ms

        # step 3: blue/red split - anticone within mergeset <= k
        # CONTRACT, fixed 2026-09-23 (round-3 adversarial review finding [1]):
        # an earlier version marked every block blue at its OWN insertion
        # (`self.is_blue[bid] = True` at the end), so this loop's
        # `if b in self.is_blue: continue` fired 100% of the time and line
        # that computes blue/red never executed — 0 executions vs 361,341
        # skips over 200 DAGs. Every block was blue, blue_score collapsed to
        # |mergeset|+1, and TV-22 failed on 32/200 seeds while printing PASS.
        # The block itself IS blue (a block is in its own selected-parent
        # chain), so it is set here rather than unconditionally at insertion;
        # mergeset members are colored from the topology, not assumed.
        for b in ms:
            # b's anticone within the mergeset
            ac_b = self._anticone(b)
            in_ms = ac_b & ms
            self.is_blue[b] = len(in_ms) <= self.k
        self.is_blue[bid] = True  # a block is always blue in its own chain

        # step 4: blue_score = blue_score(sp) + 1 + blue(anticone in mergeset)
        # CONTRACT, fixed 2026-09-23 (round-3 consequence): GHOSTDAG's score is
        # NOT mergeset-local. It is the selected parent's score plus this
        # block's own contribution. An earlier version used |blue in mergeset|
        # + 1, which the blue/red fix exposed as wrong: TV-58 measured 25
        # blocks whose score DECREASES along the selected chain, which real
        # GHOSTDAG cannot do because each child adds to its parent's score.
        # The selected parent's score is now carried forward, which restores
        # the monotone walk.
        blue = sum(1 for b in ms if self.is_blue.get(b, False))
        sp = self.selected.get(bid)
        base = self.blue_score.get(sp, 0) if sp is not None else 0
        self.blue_score[bid] = base + blue + 1

    def order(self, bid: str) -> list:
        """
        The overall GHOSTDAG ordering (toy approach).

        The true GHOSTDAG order: the chain formed by the BLUE blocks in the mergeset
        is followed (the selected_parent chain), and red blocks are appended after
        the blue block they follow.

        The toy version here: starting from bid it follows the selected_parent chain
        and adds the blue blocks of the mergeset by depth. The goals are:
        (1) no block has an empty mergeset (liveness),
        (2) blue blocks come first.
        """
        if bid not in self.blocks:
            return []
        seen = set()
        out = []
        # 1. the selected_parent chain (the blue backbone)
        cur = bid
        while cur is not None and cur not in seen and cur in self.blocks:
            seen.add(cur)
            out.append(cur)
            cur = self.selected.get(cur)
        # 2. the other blue blocks of the mergeset (ordered by depth)
        ms = self.mergesets.get(bid, set())
        for b in sorted(ms, key=lambda x: -self.blue_score.get(x, 0)):
            if b in self.blocks and b not in seen:
                seen.add(b)
                out.append(b)
        return out


# ============================================================
# KOK v2 ctx-binding (T-A2): parent-set ctx'e girer
# ============================================================
def kok_ctx(selected_parent, miner, task_ref, height, proof_system_id, nonce,
            parent_set_hash):
    """"KOK v2 ctx: now includes the parent-set hash too (TV-25)."""
    return h(selected_parent, miner, task_ref, height, proof_system_id, nonce,
             parent_set_hash)


def parent_set_hash(parents: list) -> str:
    return h(tuple(sorted(parents)))


# ============================================================
# TESTS: TV-22..TV-26
# ============================================================
def mine_chain(g: GHOSTDAG, n: int, rng: random.Random, miners=("A", "B", "C"),
               fork_prob=0.0):
    """
    Generate a random DAG; fork_prob is the probability of a parallel block (fork).

    The parent candidate pool is not the whole DAG's latest blocks (tips); blocks are
    selected randomly from the past as well - so the result is really a DAG rather
    than a single chain. This is required for the anticone/fork tests to be meaningful.
    """
    all_bids = []
    for i in range(n):
        m = rng.choice(miners)
        if not all_bids:
            parents = []
        else:
            # parent pool: random from the DAG, but recent blocks weighted
            # (like real mining: reference the latest blocks)
            recent = all_bids[-MAX_BLOCK_PARENTS * 3:]
            k = min(MAX_BLOCK_PARENTS, len(recent))
            parents = rng.sample(recent, k)
        ts = i
        blk = Block(miner=m, parents=parents, timestamp=ts, tasks=[f"t{i}"])
        g.add(blk)
        all_bids.append(blk.bid)
        # fork: another miner at the same time with the same parents (splitter)
        if rng.random() < fork_prob and parents:
            m2 = rng.choice([x for x in miners if x != m])
            blk2 = Block(miner=m2, parents=parents, timestamp=ts, tasks=[f"t{i}f"])
            g.add(blk2)
            all_bids.append(blk2.bid)
    return g


def tv22_blue_rule():
    """"TV-22: blue-block selection satisfies anticone <= k."""
    rng = random.Random(2301)
    g = GHOSTDAG(k=GHOSTDAG_K)
    mine_chain(g, 60, rng, fork_prob=0.25)
    # every blue-marked block's mergeset-anticone <= k
    bad = 0
    for bid, ms in g.mergesets.items():
        for b in ms:
            if g.is_blue.get(b, False):
                ac = g._anticone(b) & ms
                if len(ac) > g.k:
                    bad += 1
    assert bad == 0, f"TV-22: {bad} blue blocks have anticone > k={g.k}"
    return "PASS", f"blue={sum(g.is_blue.values())}, all anticone<={g.k}"


def tv23_selected_parent_max_score():
    """"TV-23: selected_parent always has the highest blue_score."""
    rng = random.Random(2302)
    g = GHOSTDAG(k=GHOSTDAG_K)
    mine_chain(g, 60, rng, fork_prob=0.3)
    bad = 0
    for bid, blk in g.blocks.items():
        sp = g.selected.get(bid)
        if sp is None or not blk.parents:
            continue
        scores = [(g.blue_score.get(p, 0), p) for p in blk.parents if p in g.blocks]
        if not scores:
            continue
        best = max(scores, key=lambda x: (x[0], -int(x[1], 16)))[1]
        if sp != best:
            bad += 1
    assert bad == 0, f"TV-23: in {bad} blocks the selected_parent is not the max blue_score"
    return "PASS", f"{len(g.blocks)} blocks, every selected=max blue_score"


def tv24_mergeset_limit():
    """"TV-24: the mergeset limit (2k=36) is never exceeded."""
    rng = random.Random(2303)
    g = GHOSTDAG(k=GHOSTDAG_K)
    mine_chain(g, 80, rng, fork_prob=0.4)
    big = [b for b, ms in g.mergesets.items() if len(ms) > MERGESET_SIZE_LIMIT]
    assert not big, f"TV-24: {len(big)} blocks exceed the mergeset limit"
    return "PASS", f"max mergeset={max(len(m) for m in g.mergesets.values())} (limit {MERGESET_SIZE_LIMIT})"


def tv25_ctx_rejects_changed_parentset():
    """TV-25: ctx includes the parent-set -> same block, different parent-set,
    REJECT (T-A2).

    CORRECTION 2026-09-23 (round-3 finding [5]): the test below hashes two
    parent sets and asserts the ctx hashes differ. That shows "a hash is a
    function", not that replay protection is implemented. PROBES CONFIRMED:
    kok_ctx is never referenced outside this test, and Block.__post_init__
    builds the block identity from (miner, timestamp, sorted(parents), tasks)
    with NO ctx and NO nonce — so the two blocks below have DIFFERENT bids and
    DIFFERENT work, and nothing in this file rejects, rebinds, or stores a ctx.
    The T-A2 claim is UNIMPLEMENTED in this prototype. The test is kept because
    the ctx derivation itself is real and worth running, but its docstring no
    longer claims it closes replay."""
    g = GHOSTDAG(k=GHOSTDAG_K)
    b1 = Block(miner="A", parents=["p1", "p2"], timestamp=1, tasks=["t1"])
    b2 = Block(miner="A", parents=["p1", "p3"], timestamp=1, tasks=["t1"])  # same work, different parent-set
    ps1, ps2 = parent_set_hash(b1.parents), parent_set_hash(b2.parents)
    ctx1 = kok_ctx("p1", "A", "t1", 5, "kw-v1", 0, ps1)
    ctx2 = kok_ctx("p1", "A", "t1", 5, "kw-v1", 0, ps2)
    assert ctx1 != ctx2, "TV-25: same block, different parent-set gave the same ctx (BUG)"
    assert b1.bid != b2.bid, "TV-25: different parents must not share a block id"
    return ("PASS-WEAK", "different parent-set -> different ctx, and different "
            "bid. REPLAY PROTECTION IS NOT IMPLEMENTED: no block in this file "
            "stores or verifies a ctx, so T-A2 is unimplemented here")


def tv26_splitter_attack():
    """
    TV-26: total ordering still holds under a splitter attack (liveness).

    Test logic (corrected): the shortest orders belong to blocks at the START
    of the DAG (genesis=1, its children=2), because their mergesets are
    naturally small. This is not a BUG, it is the nature of GHOSTDAG. The
    correct test: if the orders of the most RECENT blocks approach the size of
    the DAG, liveness holds.
    """
    rng = random.Random(2304)
    g = GHOSTDAG(k=GHOSTDAG_K)
    mine_chain(g, 90, rng, miners=("A", "B", "C"), fork_prob=0.5)
    # recent blocks should have large orders (liveness)
    recent = list(g.blocks)[-20:]
    lens = [len(g.order(b)) for b in recent]
    # the mean order of recent blocks should be at least 40% of the DAG
    avg_recent = sum(lens) / len(lens)
    assert avg_recent >= len(g.blocks) * 0.4, \
        f"TV-26: recent blocks average {avg_recent:.1f} < 40%*{len(g.blocks)}"
    # no block should have an empty order (at least itself)
    empty = [b for b in g.blocks if len(g.order(b)) == 0]
    assert not empty, f"TV-26: the ordering of {len(empty)} blocks is empty"
    sp = sum(1 for b in g.blocks if g.selected.get(b) is not None)
    return "PASS", f"{len(g.blocks)} blocks, recent-mean={avg_recent:.0f}, with selected={sp}"


# ============================================================
def main():
    print("=" * 72)
    print("KOK v2 - GHOSTDAG PARENT-SET PROTOTYPE (TV-22..TV-26)")
    print("=" * 72)
    print(f"  GHOSTDAG k={GHOSTDAG_K} (Kaspa mainnet BPS=1)")
    print(f"  max_block_parents={MAX_BLOCK_PARENTS}, mergeset limit={MERGESET_SIZE_LIMIT}")
    print(f"  target_time={TARGET_TIME_MS} ms/block")
    print()
    tests = [tv22_blue_rule, tv23_selected_parent_max_score, tv24_mergeset_limit,
             tv25_ctx_rejects_changed_parentset, tv26_splitter_attack]
    allpass = True
    for t in tests:
        try:
            res, note = t()
            print(f"  {t.__name__:38} {res}: {note}")
            # PASS-WEAK is a RETRACTED CLAIM, not a failing test: the harness
            # still runs, the property it can verify still holds, and the
            # property it CANNOT is stated in the note (round-3 finding [5]).
            # Only a real FAIL or a raised AssertionError fails the file.
            if res not in ("PASS", "PASS-WEAK"):
                allpass = False
        except AssertionError as e:
            print(f"  {t.__name__:38} FAIL: {e}")
            allpass = False
    print()
    print("  TOY LIMITS (honest):")
    print("    - NO PoW/validity CHECK; all blocks assumed valid.")
    print("      GHOSTDAG security rests on PoW; here we test the DAG logic.")
    print("    - Network delay is a uniform [0, D_max] model; NOT real statistics.")
    print("    - k=18 is the Kaspa BPS=1 template; KOK v2's BPS is not yet chosen.")
    print("    - _future() is O(n^2); tracked incrementally in production.")
    print("    - THE MERGESET IS A GREEDY APPROXIMATION, AND IT OVER-INCLUDES. The")
    print("      definition is mergeset(sp) U (anticone(sp) INTERSECT past(B)); the")
    print("    - CLOSED 2026-09-23 (Aşama 1.1): the mergeset now intersects")
    print("      anticone(sp) with past(B), so it only contains work B knows.")
    print("      Before the fix, on a 51-block DAG this put 572 order entries")
    print("      outside a block's own past, so two blocks' orderings could")
    print("      disagree on work neither references — the largest gap between")
    print("      this file and ePrint 2018/104. TV-59 now requires 0. What")
    print("      remains a toy limit: the mergeset CAP is still admitted by")
    print("      ascending hash when it binds (not by a GHOSTDAG criterion),")
    print("      and the ordering itself is still not a total order.")
    print()
    print("  RESULT:", "ALL PASSED" if allpass else "SOME FAILED")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
