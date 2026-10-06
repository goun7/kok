"""Tests for ghostdag_proto_en.py: the blockDAG's ctx binding and ordering.

This is the chain layer. The KOK v2 addition to GHOSTDAG is that a block's
identity binds the parent-set hash (T-A2), so a block replayed against a
different parent-set produces a different, unconnected id rather than being
silently re-anchored. The parameters are Kaspa mainnet's real production
values (k=18, max 10 parents, mergeset limit 2k=36).

Covers (stdlib-only, pure functions, no external calls):
  * h / parent_set_hash / kok_ctx — the deterministic identifiers.
  * Block.__post_init__ — the bid's ctx binding (the TV-25 contract).
  * GHOSTDAG.add / order / blue_score — the DAG structure the ordering rests
    on, at shapes small enough to reason about by hand.
"""

import pytest

import ghostdag_proto_en as gp
from ghostdag_proto_en import GHOSTDAG_K, MAX_BLOCK_PARENTS, MERGESET_SIZE_LIMIT, Block, GHOSTDAG, h, kok_ctx, parent_set_hash


# ---------------------------------------------------------------------------
# h — the deterministic identifier hash
# ---------------------------------------------------------------------------


def test_h_is_a_hex_string_of_the_pinned_width():
    v = h("a", 1, 2)
    assert isinstance(v, str)
    assert len(v) == 16
    int(v, 16)


def test_h_is_deterministic():
    assert h("a", 1) == h("a", 1)


def test_h_distinguishes_inputs():
    assert h("a", 1) != h("a", 2)
    assert h("a", 1) != h("b", 1)


# ---------------------------------------------------------------------------
# parent_set_hash — order-insensitive by construction
# ---------------------------------------------------------------------------


def test_parent_set_hash_is_order_insensitive():
    # the parents are sorted before hashing, so the same set in any order is
    # the same hash — two miners citing the same parents in different orders
    # build on the same parent-set
    assert parent_set_hash(["b", "a", "c"]) == parent_set_hash(["a", "c", "b"])


def test_parent_set_hash_is_content_bound():
    assert parent_set_hash(["a", "b"]) != parent_set_hash(["a", "c"])


def test_parent_set_hash_binds_the_set_size():
    assert parent_set_hash(["a", "b"]) != parent_set_hash(["a", "b", "c"])


def test_parent_set_hash_is_deterministic():
    assert parent_set_hash(["a", "b"]) == parent_set_hash(["a", "b"])


# ---------------------------------------------------------------------------
# kok_ctx — the mining context (T-A2 replay protection)
# ---------------------------------------------------------------------------


def test_kok_ctx_is_deterministic():
    psh = parent_set_hash(["p1"])
    a = kok_ctx("sp1", "minerA", "task1", 5, "psys", 7, psh)
    b = kok_ctx("sp1", "minerA", "task1", 5, "psys", 7, psh)
    assert a == b


def test_kok_ctx_changes_with_every_binding_field():
    psh = parent_set_hash(["p1"])
    base = kok_ctx("sp1", "minerA", "task1", 5, "psys", 7, psh)
    assert base != kok_ctx("sp2", "minerA", "task1", 5, "psys", 7, psh)
    assert base != kok_ctx("sp1", "minerB", "task1", 5, "psys", 7, psh)
    assert base != kok_ctx("sp1", "minerA", "task2", 5, "psys", 7, psh)
    assert base != kok_ctx("sp1", "minerA", "task1", 6, "psys", 7, psh)
    assert base != kok_ctx("sp1", "minerA", "task1", 5, "other", 7, psh)
    assert base != kok_ctx("sp1", "minerA", "task1", 5, "psys", 8, psh)
    # the parent-set hash is the TV-25 addition
    assert base != kok_ctx("sp1", "minerA", "task1", 5, "psys", 7, parent_set_hash(["p2"]))


def test_kok_ctx_binds_the_parent_set_hash():
    # TV-25: the same work under a different parent-set is a different ctx,
    # which is what makes a replay detectable rather than merely re-runnable
    p1 = kok_ctx("sp", "m", "t", 1, "p", 1, parent_set_hash(["a"]))
    p2 = kok_ctx("sp", "m", "t", 1, "p", 1, parent_set_hash(["b"]))
    assert p1 != p2


# ---------------------------------------------------------------------------
# Block — the bid's ctx binding (the TV-25 contract)
# ---------------------------------------------------------------------------


def test_a_blocks_bid_binds_its_ctx():
    # the same content under a different parent-set hash is a DIFFERENT block
    psh1 = parent_set_hash(["p1"])
    psh2 = parent_set_hash(["p2"])
    b1 = Block("m1", ["p1"], 100, ctx=psh1)
    b2 = Block("m1", ["p1"], 100, ctx=psh2)
    assert b1.bid != b2.bid


def test_the_same_ctx_gives_the_same_bid():
    psh = parent_set_hash(["p1"])
    assert Block("m1", ["p1"], 100, ctx=psh).bid == Block("m1", ["p1"], 100, ctx=psh).bid


def test_a_block_without_a_ctx_gets_a_ctx_less_bid():
    psh = parent_set_hash(["p1"])
    assert Block("m1", ["p1"], 100).bid != Block("m1", ["p1"], 100, ctx=psh).bid


def test_parent_order_does_not_change_the_bid():
    # the parents are sorted inside __post_init__, so citation order is not
    # part of the identity — only the parent SET is
    psh = parent_set_hash(["p1", "p2"])
    assert Block("m1", ["p2", "p1"], 100, ctx=psh).bid == Block("m1", ["p1", "p2"], 100, ctx=psh).bid


def test_the_bid_binds_the_miner_and_timestamp():
    psh = parent_set_hash(["p1"])
    base = Block("m1", ["p1"], 100, ctx=psh)
    assert base.bid != Block("m2", ["p1"], 100, ctx=psh).bid
    assert base.bid != Block("m1", ["p1"], 101, ctx=psh).bid


def test_the_bid_binds_the_tasks():
    psh = parent_set_hash(["p1"])
    base = Block("m1", ["p1"], 100, tasks=["t1"], ctx=psh)
    assert base.bid != Block("m1", ["p1"], 100, tasks=["t2"], ctx=psh).bid


# ---------------------------------------------------------------------------
# GHOSTDAG — the structure
# ---------------------------------------------------------------------------


def test_the_production_parameters_are_kaspa_mainnets():
    # the real values from rusty-kaspa bps.rs at BPS=1, pinned because the
    # ordering's security argument is parameterised by k
    assert GHOSTDAG_K == 18
    assert MAX_BLOCK_PARENTS == 10
    assert MERGESET_SIZE_LIMIT == 2 * GHOSTDAG_K == 36


def test_a_genesis_block_has_no_parents_and_score_one():
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    assert g.selected[gen.bid] is None
    assert g.blue_score[gen.bid] == 1
    assert g.is_blue[gen.bid] is True
    assert g.mergesets[gen.bid] == set()


def test_blue_score_is_monotone_along_the_selected_chain():
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    c1 = Block("m", [gen.bid], 1)
    g.add(c1)
    c2 = Block("m", [c1.bid], 2)
    g.add(c2)
    # each child adds to its selected parent's score, never subtracts
    assert g.blue_score[c2.bid] > g.blue_score[c1.bid] > g.blue_score[gen.bid]


def test_the_selected_parent_is_the_highest_scoring_parent():
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    # a chain of two: gen -> a -> aa, so aa carries a deeper score
    a = Block("m", [gen.bid], 1)
    g.add(a)
    aa = Block("m", [a.bid], 2)
    g.add(aa)
    # b is a direct child of the genesis: shallower score
    b = Block("m", [gen.bid], 3)
    g.add(b)
    assert g.blue_score[aa.bid] > g.blue_score[b.bid]
    child = Block("m", [b.bid, aa.bid], 4)
    g.add(child)
    # the deeper-scoring parent is selected regardless of citation order
    assert g.selected[child.bid] == aa.bid


def test_ties_break_on_the_lowest_hash():
    # the documented rule: among equally-scoring parents the lowest hash
    # (as an integer) wins, so the choice is deterministic across nodes
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    # two siblings of the genesis, both scoring the same
    f1 = Block("mA", [gen.bid], 1)
    f2 = Block("mB", [gen.bid], 2)
    g.add(f1)
    g.add(f2)
    assert g.blue_score[f1.bid] == g.blue_score[f2.bid]
    child = Block("m", [f2.bid, f1.bid], 3)
    g.add(child)
    want = min(f1.bid, f2.bid, key=lambda x: int(x, 16))
    assert g.selected[child.bid] == want
    # and the tie-break is stable: rebuilding the same DAG selects the same
    g2 = GHOSTDAG()
    g2.add(gen)
    g2.add(f1)
    g2.add(f2)
    c2 = Block("m", [f2.bid, f1.bid], 3)
    g2.add(c2)
    assert g2.selected[c2.bid] == want


def test_order_returns_the_selected_chain_first():
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    c1 = Block("m", [gen.bid], 1)
    g.add(c1)
    c2 = Block("m", [c1.bid], 2)
    g.add(c2)
    out = g.order(c2.bid)
    # the selected chain comes first, tip to genesis
    assert out[0] == c2.bid
    assert out[-1] == gen.bid
    assert c1.bid in out


def test_order_of_an_unknown_block_is_empty():
    g = GHOSTDAG()
    assert g.order("does-not-exist") == []


def test_order_covers_every_block_in_a_small_dag():
    # liveness: every block in the DAG appears in the tip's ordering
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    blocks = [gen]
    for i in range(1, 8):
        blk = Block("m", [blocks[-1].bid], i)
        g.add(blk)
        blocks.append(blk)
    out = g.order(blocks[-1].bid)
    assert set(out) == {b.bid for b in blocks}
    assert len(out) == len(blocks)


def test_a_fork_produces_two_distinct_bids_but_one_ordering():
    # the splitter case in miniature: two blocks on the same parent are
    # distinct identities, and the tip still orders them both
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    f1 = Block("mA", [gen.bid], 1)
    f2 = Block("mB", [gen.bid], 1)
    g.add(f1)
    g.add(f2)
    assert f1.bid != f2.bid
    tip = Block("m", [f1.bid, f2.bid], 2)
    g.add(tip)
    out = g.order(tip.bid)
    assert f1.bid in out and f2.bid in out
    assert gen.bid in out


def test_the_mergeset_never_exceeds_the_limit():
    # 2k = 36 on a DAG wide enough to approach it
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    # a fan of siblings off the genesis, all referenced by one wide block
    sibs = []
    for i in range(40):
        s = Block("m%d" % i, [gen.bid], i)
        g.add(s)
        sibs.append(s)
    wide = Block("m", [s.bid for s in sibs], 100)
    g.add(wide)
    assert len(g.mergesets[wide.bid]) <= MERGESET_SIZE_LIMIT


def test_a_block_referencing_an_unknown_parent_still_has_an_order():
    # robustness: a parent that was never added does not break the DAG
    g = GHOSTDAG()
    gen = Block("m", [], 0)
    g.add(gen)
    blk = Block("m", [gen.bid, "ghost-parent"], 1)
    g.add(blk)
    assert isinstance(g.order(blk.bid), list)
    assert gen.bid in g.order(blk.bid)
