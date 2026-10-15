"""Dal-kesen (branch-cutting) testler: ghostdag_proto.py (TR orijinal prototip).

Kapsam — GHOSTDAG ebeveyn-kume prototipinin her dali:
  * h / kok_ctx / parent_set_hash — deterministik tanimlayicilar.
  * Block.__post_init__ — bid'lerin ctx-baglamasi (TV-25 sozlesmesi).
  * GHOSTDAG.add/_compute — genesis-benzeri yol (parent yok), bilinmeyen-parent
    yolu (parent'lar DAG'da degil), secili-parent = maks blue_score, esitlik
    bozucu = en dusuk hash, mergeset = m(sp) U anticone(sp), 2k kapasi.
  * _past/_future/_anticone — DAG yapisinin sinirlari (transitive, atlanmis
    bilinmeyen id'ler, onbellek kimligi).
  * order() — bilinmeyen bid, genesis, secili-parent zinciri + mergeset.
  * mine_chain — fork olasiligi, ebeveyn sayisi siniri, blok uretim sayisi.
  * Gonderilen test vektorleri TV-22..TV-26 + main() cikis kodu.

Guvenli-saf-bellek: network/socket/subprocess YOK; tum sablonlar inline'dir.
Bu dosya production koduna DOKUNMAZ; yalnizca mevcut davranisi belgeler.
Bulgu KOK-1 (mor-yesil sinflandirma bos) bu dosyada belgelenmistir.
"""

import random

import pytest

import ghostdag_proto as gp
from ghostdag_proto import (
    GHOSTDAG,
    GHOSTDAG_K,
    MAX_BLOCK_PARENTS,
    MERGESET_SIZE_LIMIT,
    TARGET_TIME_MS,
    Block,
    h,
    kok_ctx,
    mine_chain,
    parent_set_hash,
)


# ---------------------------------------------------------------------------
# h — deterministik tanimlayici
# ---------------------------------------------------------------------------

def test_h_returns_lowercase_hex_of_pinned_width():
    v = h("a", 1, 2)
    assert isinstance(v, str)
    assert len(v) == 16
    assert all(c in "0123456789abcdef" for c in v)


def test_h_is_deterministic_for_same_arguments():
    assert h("x", 9, "y") == h("x", 9, "y")


def test_h_differs_when_any_part_differs():
    base = h("miner", 10, ("p1",))
    assert h("miner2", 10, ("p1",)) != base
    assert h("miner", 11, ("p1",)) != base
    assert h("miner", 10, ("p2",)) != base


def test_h_accepts_empty_argument_list():
    v = h()
    assert isinstance(v, str) and len(v) == 16


def test_h_accepts_mixed_python_types():
    v = h(None, 0.5, ("t", 1), ["x"], True)
    assert len(v) == 16


def test_h_uses_sha256_truncated_to_16_hex_chars():
    import hashlib
    expected = hashlib.sha256("a|1".encode()).hexdigest()[:16]
    assert h("a", 1) == expected


# ---------------------------------------------------------------------------
# Block — bid ctx-baglamasi
# ---------------------------------------------------------------------------

def test_block_bid_is_set_after_init():
    b = Block(miner="A", parents=["p1"], timestamp=7, tasks=["t1"])
    assert b.bid != "" and len(b.bid) == 16


def test_block_bid_is_order_insensitive_over_parents():
    b1 = Block(miner="A", parents=["p2", "p1"], timestamp=1, tasks=["t"])
    b2 = Block(miner="A", parents=["p1", "p2"], timestamp=1, tasks=["t"])
    assert b1.bid == b2.bid


def test_block_bid_binds_task_order():
    b1 = Block(miner="A", parents=["p1"], timestamp=1, tasks=["t1", "t2"])
    b2 = Block(miner="A", parents=["p1"], timestamp=1, tasks=["t2", "t1"])
    assert b1.bid != b2.bid


def test_block_bid_binds_task_content():
    b1 = Block(miner="A", parents=["p1"], timestamp=1, tasks=["t1"])
    b2 = Block(miner="A", parents=["p1"], timestamp=1, tasks=["t2"])
    assert b1.bid != b2.bid


def test_block_bid_binds_miner_and_timestamp():
    base = Block(miner="A", parents=["p1"], timestamp=1, tasks=["t"])
    assert Block(miner="B", parents=["p1"], timestamp=1, tasks=["t"]).bid != base.bid
    assert Block(miner="A", parents=["p1"], timestamp=2, tasks=["t"]).bid != base.bid


def test_block_empty_parents_and_default_tasks():
    b = Block(miner="A", parents=[], timestamp=0)
    assert b.tasks == []
    assert b.bid != ""


def test_block_default_task_lists_are_not_shared_between_instances():
    b1 = Block(miner="A", parents=[], timestamp=0)
    b2 = Block(miner="A", parents=[], timestamp=0)
    b1.tasks.append("tX")
    assert b2.tasks == []


# ---------------------------------------------------------------------------
# GHOSTDAG — kurulum ve genesis-benzeri yollar
# ---------------------------------------------------------------------------

def test_default_k_is_kaspa_mainnet_18():
    assert GHOSTDAG().k == GHOSTDAG_K == 18


def test_custom_k_is_honoured():
    assert GHOSTDAG(k=5).k == 5
    assert GHOSTDAG(k=0).k == 0


def test_fresh_instance_has_empty_state():
    g = GHOSTDAG()
    assert g.blocks == {} and g.mergesets == {}
    assert g.selected == {} and g.blue_score == {} and g.is_blue == {}


def test_production_parameters_are_kaspa_values():
    assert MAX_BLOCK_PARENTS == 10
    assert MERGESET_SIZE_LIMIT == 2 * GHOSTDAG_K == 36
    assert TARGET_TIME_MS == 1000


def test_genesis_like_block_has_no_selected_parent_and_score_one():
    g = GHOSTDAG()
    b = Block(miner="A", parents=[], timestamp=1, tasks=["t"])
    g.add(b)
    assert g.selected[b.bid] is None
    assert g.mergesets[b.bid] == set()
    assert g.blue_score[b.bid] == 1
    assert g.is_blue[b.bid] is True


def test_all_parents_unknown_takes_genesis_like_path():
    g = GHOSTDAG()
    b = Block(miner="A", parents=["yok1", "yok2"], timestamp=3, tasks=["t"])
    g.add(b)
    assert b.parents and b.parents[0] not in g.blocks
    assert g.selected[b.bid] is None
    assert g.mergesets[b.bid] == set()
    assert g.blue_score[b.bid] == 1
    assert g.is_blue[b.bid] is True


def test_one_known_one_unknown_parent_uses_known_parent():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    b = Block(miner="A", parents=[gen.bid, "yok"], timestamp=2, tasks=["t"])
    g.add(b)
    assert g.selected[b.bid] == gen.bid


# ---------------------------------------------------------------------------
# _past / _future / _anticone
# ---------------------------------------------------------------------------

def _straight_chain(g, n, miner="A"):
    """gen -> c1 -> c2 ... dogrusal zincir; bid listesi doner."""
    bids = []
    prev = []
    for i in range(n):
        b = Block(miner=miner, parents=prev, timestamp=i, tasks=[f"t{i}"])
        g.add(b)
        bids.append(b.bid)
        prev = [b.bid]
    return bids


def test_past_of_genesis_is_empty():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    assert g._past(gen.bid) == set()


def test_past_is_transitive_over_parents():
    g = GHOSTDAG()
    bids = _straight_chain(g, 4)
    past_tip = g._past(bids[-1])
    assert set(bids[:-1]) == past_tip
    assert bids[-1] not in past_tip


def test_past_skips_unknown_parent_ids():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=["yok"], timestamp=0)
    g.add(gen)
    assert g._past(gen.bid) == set()


def test_past_is_cached_and_returns_the_same_object():
    g = GHOSTDAG()
    bids = _straight_chain(g, 5)
    first = g._past(bids[-1])
    second = g._past(bids[-1])
    assert first is second


def test_future_of_genesis_is_every_later_block():
    g = GHOSTDAG()
    bids = _straight_chain(g, 4)
    assert g._future(bids[0]) == set(bids[1:])


def test_future_of_tip_is_empty():
    g = GHOSTDAG()
    bids = _straight_chain(g, 4)
    assert g._future(bids[-1]) == set()


def test_future_excludes_siblings_but_includes_descendants():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    c1 = Block(miner="A", parents=[gen.bid], timestamp=1, tasks=["a"])
    c2 = Block(miner="B", parents=[gen.bid], timestamp=2, tasks=["b"])
    g.add(c1)
    g.add(c2)
    gc = Block(miner="A", parents=[c1.bid], timestamp=3, tasks=["c"])
    g.add(gc)
    assert g._future(c1.bid) == {gc.bid}
    assert c2.bid not in g._future(c1.bid)


def test_anticone_of_single_block_dag_is_empty():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    assert g._anticone(gen.bid) == set()


def test_anticone_links_parallel_siblings():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    c1 = Block(miner="A", parents=[gen.bid], timestamp=1, tasks=["a"])
    c2 = Block(miner="B", parents=[gen.bid], timestamp=2, tasks=["b"])
    g.add(c1)
    g.add(c2)
    assert g._anticone(c1.bid) == {c2.bid}
    assert g._anticone(c2.bid) == {c1.bid}


def test_anticone_excludes_self_past_and_future():
    g = GHOSTDAG()
    bids = _straight_chain(g, 4)
    # ucuncu blok: gecmisi 2 blok, gelecegi 1 blok, anticone bos
    assert g._past(bids[2]) == {bids[0], bids[1]}
    assert g._future(bids[2]) == {bids[3]}
    assert g._anticone(bids[2]) == set()


# ---------------------------------------------------------------------------
# _compute — secili-parent, mergeset, blue_score
# ---------------------------------------------------------------------------

def _three_children(g, miner="A"):
    """gen + 3 cocuk (c1,c2,c3) — c1/c2/c3 birbirinin anticone'u."""
    gen = Block(miner=miner, parents=[], timestamp=0)
    g.add(gen)
    kids = []
    for i in range(3):
        c = Block(miner=miner, parents=[gen.bid], timestamp=i + 1, tasks=[f"c{i}"])
        g.add(c)
        kids.append(c)
    return gen, kids


def test_selected_parent_of_child_is_genesis():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    assert g.selected[kids[0].bid] == gen.bid


def test_selected_parent_is_the_max_blue_score_parent():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    # P: parents=[kids[0], kids[1]] -> mergeseti {kids[1], kids[2]} -> score 3
    P = Block(miner="A", parents=[kids[0].bid, kids[1].bid], timestamp=10, tasks=["P"])
    g.add(P)
    assert g.blue_score[P.bid] == 3  # 2 mavi ms uyessi + 1 kendisi
    # Q: parents=[P (score 3), kids[2] (score 1)] -> secili P
    Q = Block(miner="A", parents=[P.bid, kids[2].bid], timestamp=11, tasks=["Q"])
    g.add(Q)
    assert g.selected[Q.bid] == P.bid


def test_tie_break_picks_the_lowest_hash_int():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    # kids[0] ve kids[1] ayni score (1) -> en dusuk int(bid,16) kazanir
    expected = min(kids[0].bid, kids[1].bid, key=lambda x: int(x, 16))
    P = Block(miner="A", parents=[kids[0].bid, kids[1].bid], timestamp=10, tasks=["P"])
    g.add(P)
    assert g.selected[P.bid] == expected


def test_blue_score_counts_mergeset_blues_plus_self():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    P = Block(miner="A", parents=[kids[0].bid, kids[1].bid], timestamp=10, tasks=["P"])
    g.add(P)
    ms = g.mergesets[P.bid]
    # anticone(kids[0]) = {kids[1], kids[2]} -> mergeset 2 elemanli (kapasite
    # altinda); her iki uyessi 'mavi' isaretli -> blue_score = 2 + 1 = 3
    assert len(ms) == 2
    assert g.blue_score[P.bid] == 3


def test_mergeset_is_superset_of_selected_parent_mergeset():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    P = Block(miner="A", parents=[kids[0].bid, kids[1].bid], timestamp=10, tasks=["P"])
    g.add(P)
    sp_ms = g.mergesets.get(kids[0].bid, set())
    assert g.mergesets[P.bid] >= sp_ms


def test_mergeset_never_exceeds_2k_even_with_huge_anticone():
    g = GHOSTDAG(k=GHOSTDAG_K)
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    kids = [Block(miner="A", parents=[gen.bid], timestamp=i + 1, tasks=[f"k{i}"])
            for i in range(40)]
    for c in kids:
        g.add(c)
    B = Block(miner="B", parents=[kids[0].bid], timestamp=99, tasks=["B"])
    g.add(B)
    ms = g.mergesets[B.bid]
    assert len(ms) == MERGESET_SIZE_LIMIT == 36


def test_mergeset_takes_the_lowest_hash_ints_first_under_cap():
    g = GHOSTDAG(k=GHOSTDAG_K)
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    kids = [Block(miner="A", parents=[gen.bid], timestamp=i + 1, tasks=[f"k{i}"])
            for i in range(40)]
    for c in kids:
        g.add(c)
    B = Block(miner="B", parents=[kids[0].bid], timestamp=99, tasks=["B"])
    g.add(B)
    ac_sp = g._anticone(kids[0].bid)
    expected = set(sorted(ac_sp, key=lambda x: int(x, 16))[:MERGESET_SIZE_LIMIT])
    assert g.mergesets[B.bid] == expected


def test_every_added_block_is_marked_blue_for_itself():
    g = GHOSTDAG()
    bids = _straight_chain(g, 5)
    assert all(g.is_blue[b] for b in bids)


def test_mergeset_members_are_all_blue_current_behavior_kok1():
    """KOK-1 (bulgu, production'a dokunulmadi): _compute her eklenen blok icin
    is_blue[bid]=True koydugu icin, mergeset sinflandirma dongusundeki
    'if b in self.is_blue: continue' her zaman tetiklenir; 'len(anticone)<=k'
    mavi/kirmizi karari HIC evalueasmaz. Bu test mevcut davranisi belgeler."""
    g = GHOSTDAG(k=GHOSTDAG_K)
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    kids = [Block(miner="A", parents=[gen.bid], timestamp=i + 1, tasks=[f"k{i}"])
            for i in range(40)]
    for c in kids:
        g.add(c)
    B = Block(miner="B", parents=[kids[0].bid], timestamp=99, tasks=["B"])
    g.add(B)
    ms = g.mergesets[B.bid]
    # her ms uyessi zaten eklenmis bir blok -> is_blue True (kucuk k'da bile)
    assert all(g.is_blue.get(b) is True for b in ms)
    # kuralin evalue olmadiginin kaniti: k=0 olsa bile yine hepsi mavi
    g2 = GHOSTDAG(k=0)
    g2.add(gen)
    for c in kids:
        g2.add(Block(miner=c.miner, parents=c.parents, timestamp=c.timestamp,
                     tasks=c.tasks))
    B2 = Block(miner="B", parents=[kids[0].bid], timestamp=99, tasks=["B"])
    g2.add(B2)
    assert all(g2.is_blue.get(b) is True for b in g2.mergesets[B2.bid])


def test_k_parameter_does_not_change_marks_with_current_logic():
    g = GHOSTDAG(k=40)
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    kids = [Block(miner="A", parents=[gen.bid], timestamp=i + 1, tasks=[f"k{i}"])
            for i in range(40)]
    for c in kids:
        g.add(c)
    B = Block(miner="B", parents=[kids[0].bid], timestamp=99, tasks=["B"])
    g.add(B)
    assert all(g.is_blue.get(b) is True for b in g.mergesets[B.bid])


# ---------------------------------------------------------------------------
# order — toplam duzen
# ---------------------------------------------------------------------------

def test_order_of_unknown_bid_is_empty():
    g = GHOSTDAG()
    assert g.order("ffff0000ffff0000") == []


def test_order_of_genesis_is_just_itself():
    g = GHOSTDAG()
    gen = Block(miner="A", parents=[], timestamp=0)
    g.add(gen)
    assert g.order(gen.bid) == [gen.bid]


def test_order_follows_the_selected_parent_chain_first():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    P = Block(miner="A", parents=[kids[0].bid, kids[1].bid], timestamp=10, tasks=["P"])
    g.add(P)
    Q = Block(miner="A", parents=[P.bid, kids[2].bid], timestamp=11, tasks=["Q"])
    g.add(Q)
    out = g.order(Q.bid)
    assert out[0] == Q.bid
    assert out[1] == P.bid
    assert out[:3] == [Q.bid, P.bid, kids[0].bid]  # Q -> P -> kids[0] -> gen


def test_order_includes_mergeset_members_after_the_chain():
    g = GHOSTDAG()
    gen, kids = _three_children(g)
    P = Block(miner="A", parents=[kids[0].bid, kids[1].bid], timestamp=10, tasks=["P"])
    g.add(P)
    out = g.order(P.bid)
    assert set(out) == {P.bid, kids[0].bid, gen.bid} | g.mergesets[P.bid]
    assert len(out) == len(set(out))  # tekrarsiz


def test_order_never_empty_for_any_block():
    rng = random.Random(2300)
    g = GHOSTDAG()
    mine_chain(g, 40, rng, fork_prob=0.4)
    assert g.blocks
    assert all(len(g.order(b)) >= 1 for b in g.blocks)


def test_order_grows_for_recent_blocks():
    rng = random.Random(2301)
    g = GHOSTDAG()
    mine_chain(g, 60, rng, fork_prob=0.35)
    recent = list(g.blocks)[-10:]
    lens = [len(g.order(b)) for b in recent]
    assert min(lens) >= 1
    # en guncel bloklar DAG'in buyuklugune yaklasmali (liveness)
    assert sum(lens) / len(lens) >= 0.3 * len(g.blocks)


# ---------------------------------------------------------------------------
# kok_ctx / parent_set_hash — T-A2 replay korumasi
# ---------------------------------------------------------------------------

def test_parent_set_hash_is_order_insensitive():
    assert parent_set_hash(["p1", "p2"]) == parent_set_hash(["p2", "p1"])


def test_parent_set_hash_differs_for_different_sets():
    assert parent_set_hash(["p1", "p2"]) != parent_set_hash(["p1", "p3"])
    assert parent_set_hash([]) != parent_set_hash(["p1"])


def test_kok_ctx_binds_parent_set_hash_tv25():
    ps1 = parent_set_hash(["p1", "p2"])
    ps2 = parent_set_hash(["p1", "p3"])
    c1 = kok_ctx("p1", "A", "t1", 5, "kw-v1", 0, ps1)
    c2 = kok_ctx("p1", "A", "t1", 5, "kw-v1", 0, ps2)
    assert c1 != c2


def test_kok_ctx_differs_when_any_argument_differs():
    ps = parent_set_hash(["p1"])
    base = kok_ctx("p1", "A", "t1", 5, "kw-v1", 0, ps)
    assert kok_ctx("p2", "A", "t1", 5, "kw-v1", 0, ps) != base
    assert kok_ctx("p1", "B", "t1", 5, "kw-v1", 0, ps) != base
    assert kok_ctx("p1", "A", "t2", 5, "kw-v1", 0, ps) != base
    assert kok_ctx("p1", "A", "t1", 6, "kw-v1", 0, ps) != base
    assert kok_ctx("p1", "A", "t1", 5, "kw-v2", 0, ps) != base
    assert kok_ctx("p1", "A", "t1", 5, "kw-v1", 1, ps) != base


def test_kok_ctx_is_deterministic():
    ps = parent_set_hash(["p1", "p2"])
    assert kok_ctx("sp", "m", "t", 1, "ps1", 7, ps) == \
           kok_ctx("sp", "m", "t", 1, "ps1", 7, ps)


def test_kok_ctx_output_is_a_hex_string():
    v = kok_ctx("sp", "m", "t", 1, "ps1", 7, "abc")
    assert isinstance(v, str) and len(v) == 16


# ---------------------------------------------------------------------------
# mine_chain — DAG uretici
# ---------------------------------------------------------------------------

def test_mine_chain_produces_exactly_n_blocks_without_forks():
    rng = random.Random(2400)
    g = GHOSTDAG()
    mine_chain(g, 10, rng, fork_prob=0.0)
    assert len(g.blocks) == 10


def test_mine_chain_forks_add_extra_blocks():
    rng = random.Random(2401)
    g = GHOSTDAG()
    mine_chain(g, 20, rng, fork_prob=1.0)
    assert len(g.blocks) > 20


def test_mine_chain_fork_needs_parents_first_block_alone():
    rng = random.Random(2402)
    g = GHOSTDAG()
    mine_chain(g, 1, rng, fork_prob=1.0)
    assert len(g.blocks) == 1


def test_mine_chain_respects_max_block_parents():
    rng = random.Random(2403)
    g = GHOSTDAG()
    mine_chain(g, 40, rng, fork_prob=0.5)
    assert all(len(b.parents) <= MAX_BLOCK_PARENTS for b in g.blocks.values())


def test_mine_chain_first_block_has_no_parents():
    rng = random.Random(2404)
    g = GHOSTDAG()
    mine_chain(g, 5, rng)
    first = list(g.blocks.values())[0]
    assert first.parents == []
    assert g.selected[first.bid] is None


def test_mine_chain_fork_uses_a_different_miner():
    rng = random.Random(2405)
    g = GHOSTDAG()
    mine_chain(g, 30, rng, miners=("A", "B"), fork_prob=1.0)
    miners = {b.miner for b in g.blocks.values()}
    assert miners <= {"A", "B"}
    # fork bloklari farkli madencidendendir -> en az 2 madenci gorulmeli
    assert len(miners) == 2


# ---------------------------------------------------------------------------
# Gonderilen test vektorleri TV-22..TV-26 + main
# ---------------------------------------------------------------------------

def test_tv22_blue_rule_module_vector_passes():
    res, note = gp.tv22_blue_rule()
    assert res == "PASS"


def test_tv23_selected_parent_max_score_module_vector_passes():
    res, note = gp.tv23_selected_parent_max_score()
    assert res == "PASS"


def test_tv24_mergeset_limit_module_vector_passes():
    res, note = gp.tv24_mergeset_limit()
    assert res == "PASS"


def test_tv25_ctx_rejects_changed_parentset_module_vector_passes():
    res, note = gp.tv25_ctx_rejects_changed_parentset()
    assert res == "PASS"


def test_tv26_splitter_attack_module_vector_passes():
    res, note = gp.tv26_splitter_attack()
    assert res == "PASS"


def test_main_returns_zero_and_all_vectors_pass(capsys):
    rc = gp.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "HEPSI GECTI" in out
    assert "FAIL" not in out
