"""Dal-kesen (branch-cutting) testler: u_layer_prototype.py (TR orijinal prototip).

Kapsam — U-katmani ekonomi/ceza makinesinin her dali:
  * H/S — sha3_256 tabanli deterministik tanimlayicilar (EN ikizinden farkli).
  * KWKernel — noise onbellegi, prove() basari/target-ulasilamaz yollari,
    verify() dogrulama, replay-reddi (farkli ctx/nonce) ve bozuk cert yollari.
  * VRF — HMAC-stub prove/verify roundtrip ve her red dalı.
  * TaskSpec — program/public-input commit'leri.
  * Chain.submit_task — fee/burn/bond ayrismasi ve giris korumlari (fee>0,
    0 < burn_rate <= 0.5 sinirlari dahil).
  * Chain.epoch_seed / assign_tasks — lookback, atama, atama-disi durum.
  * Chain.mine_block — PQ-schema korkulugu, KW cert, u_proof uretimi,
    wrong_result dali, anti-aggregation korkulugu, phi formulu.
  * Chain.validate_block — her RED sebebi + ACCEPT.
  * Chain.challenge — fraud slash, fraud-pencere siniri, kotu niyetli itiraz.
  * Chain.settle — SOLVED odemesi.
  * Chain.retarget/sim_block/record_time — Z=W penceresi, lam_hat formulu,
    medyan filtre, 4x klips, D>=1 tabani.
  * kurtosis (TV-9) ve gonderilen test vektorleri TV-5..TV-10 + tv123_stub.

Guvenli-saf-bellek: network/socket/subprocess YOK; tum sablonlar inline'dir.
Production koduna DOKUNULMADI; asagidaki bulgular mevcut davranisi belgeler:
  KOK-2: settle() escrow'u negatife goturur (burn iki kez sayilir).
  KOK-3: assign_tasks, VRF lottesini kaybeden COMMITTED task icin assert patlatir.
  KOK-4: challenge(), miners icinde kayitli olmayan kotu-niyetli itirazcida KeyError.
  KOK-5: verify() bozuk tile indeksli cert'te IndexError doner (False degil).
  KOK-6: validate_block(), bilinmeyen tid'li u_proof icin KeyError doner.
  KOK-7: tile dogrulamasi sadece A[0][0]*B[0][0] kose girisini kontrol eder;
    tile'in diger girisleri (A[1][0]/B[1][0]) HIC kontrol edilmez.
"""

import hashlib
import math

import pytest

import u_layer_prototype as ul
from u_layer_prototype import (
    BOND_RATIO,
    C_FEE,
    DEFAULT_PS,
    DEADLINE_H,
    EPOCH_LOOKBACK,
    FRAUD_REWARD,
    G_FLOPS,
    PQ_SET,
    RETARGET_WINDOW,
    SEED,
    T_B,
    W_s,
    Chain,
    KWKernel,
    Task,
    TaskSpec,
    VRF,
    H,
    S,
    kurtosis,
)

A2 = [[1, 2], [3, 4]]
B2 = [[5, 6], [7, 8]]


def _chain_with_lookback(n=EPOCH_LOOKBACK + 5):
    """Atama icin lookback'i asan bos-bloklarla dolu Chain."""
    ch = Chain()
    for i in range(n):
        ch.blocks.append(S("empty", len(ch.blocks)))
    return ch


# ---------------------------------------------------------------------------
# H / S
# ---------------------------------------------------------------------------

def test_H_returns_a_big_int_and_is_deterministic():
    v = H("a", 1, 2)
    assert isinstance(v, int)
    assert v > 0
    assert H("a", 1, 2) == v


def test_H_matches_sha3_256_with_trailing_separator():
    expected = int.from_bytes(hashlib.sha3_256("a|1".encode() + b"|").digest(), "big")
    assert H("a", 1) == expected


def test_H_differs_on_any_part():
    base = H("x", 9)
    assert H("y", 9) != base
    assert H("x", 10) != base
    assert H("x") != base


def test_S_is_32_hex_lowercase_and_bounded_to_128_bits():
    v = S("anything", 1)
    assert len(v) == 32
    assert all(c in "0123456789abcdef" for c in v)
    assert int(v, 16) < (1 << 128)


def test_S_is_deterministic_and_differs_on_input():
    assert S("a") == S("a")
    assert S("a") != S("b")


# ---------------------------------------------------------------------------
# KWKernel
# ---------------------------------------------------------------------------

def test_kernel_defaults():
    kw = KWKernel()
    assert (kw.q, kw.n, kw.r) == (97, 8, 2)


def test_noise_is_deterministic_per_ctx_and_cached():
    kw = KWKernel()
    e1, f1 = kw._noise("ctx-1", 8)
    e2, f2 = kw._noise("ctx-1", 8)
    assert e1 is e2 and f1 is f2
    hit = KWKernel._noise_cache[("ctx-1", 8, 97)]
    assert hit[0] is e1 and hit[1] is f1


def test_noise_differs_for_different_ctx():
    kw = KWKernel()
    e1, _ = kw._noise("ctx-1", 8)
    e2, _ = kw._noise("ctx-2", 8)
    assert e1 != e2


def test_noise_values_are_reduced_modulo_q():
    kw = KWKernel()
    E, F = kw._noise("ctx-q", 8)
    assert all(0 <= v < 97 for row in E for v in row)
    assert all(0 <= v < 97 for row in F for v in row)


def _mine_cert(kw, A, B, ctx, target=1 << 6, max_nonce=5000):
    """prove() tek nonce dener; Chain.mine_block'taki gibi nonce taranir."""
    for nonce in range(1, max_nonce + 1):
        cert = kw.prove(A, B, ctx, nonce, target)
        if cert is not None:
            return cert, nonce
    raise AssertionError("cert bulunamadi (target cok mu zor?)")


def test_prove_returns_certificate_dict_on_success():
    kw = KWKernel()
    cert, _ = _mine_cert(kw, A2, B2, 4242)
    assert cert is not None
    assert set(cert) == {"tile", "m"}
    i, j, val = cert["tile"]
    assert (i, j) == (0, 0)
    assert 0 <= val < 97
    assert cert["m"] == len(A2) // kw.r


def test_prove_returns_none_when_target_unreachable():
    kw = KWKernel()
    cert = kw.prove(A2, B2, 7, 1, 1 << 250)
    assert cert is None


def test_verify_accepts_its_own_certificate():
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    assert kw.verify(cert, A2, B2, 99, nonce, 1 << 6) is True


def test_verify_rejects_none_certificate():
    kw = KWKernel()
    assert kw.verify(None, A2, B2, 99, 1, 1 << 6) is False


def test_verify_rejects_tampered_tile_value():
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    bad = dict(cert)
    i, j, val = cert["tile"]
    bad["tile"] = (i, j, (val + 1) % 97)
    assert kw.verify(bad, A2, B2, 99, nonce, 1 << 6) is False


def test_verify_rejects_replay_under_a_different_ctx():
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    assert kw.verify(cert, A2, B2, 99, nonce, 1 << 6) is True
    assert kw.verify(cert, A2, B2, 12345, nonce, 1 << 6) is False


def test_verify_rejects_a_different_nonce():
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    assert kw.verify(cert, A2, B2, 99, nonce + 1, 1 << 6) is False


def test_verify_rejects_modified_matrices():
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    A2p = [[A2[0][0] + 1, A2[0][1]], list(A2[1])]
    B2p = [[B2[0][0] + 1, B2[0][1]], list(B2[1])]  # B[0][0] tile kosesi
    assert kw.verify(cert, A2p, B2, 99, nonce, 1 << 6) is False
    assert kw.verify(cert, A2, B2p, 99, nonce, 1 << 6) is False


def test_verify_ignores_entries_outside_the_tile_corner_kok7():
    """KOK-7 (bulgu: dogrulama eksigi): tile (0,0) dogrulamasi yalnizca
    A[i*r][l*r] * B[l*r][j*r] koselerini yeniden turetir (r=2, m=1 icin
    A[0][0]*B[0][0]); tile'in diger 3 girisi HIC kontrol edilmez. Kotu
    niyetli madenci bu girilerde rastgele deger tasiyabilir. Production'a
    dokunulmadi; bu test mevcut davranisi belgeler."""
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    A2_bad = [list(A2[0]), [999, A2[1][1]]]          # A[1][0] tile disinda
    B2_bad = [list(B2[0]), [999, B2[1][1]]]          # B[1][0] tile disinda
    assert kw.verify(cert, A2_bad, B2, 99, nonce, 1 << 6) is True
    assert kw.verify(cert, A2, B2_bad, 99, nonce, 1 << 6) is True


def test_verify_raises_on_out_of_range_tile_kok5():
    """KOK-5 (bulgu): cert icindeki tile indeksleri kontrol edilmiyor;
    kotu niyetli bir madenci i/j'yi disa tasarsa verify IndexError firlatir,
    False donmez -> validate_block REJECT yerine crash."""
    kw = KWKernel()
    cert, nonce = _mine_cert(kw, A2, B2, 99)
    bad = dict(cert)
    i, j, val = cert["tile"]
    bad["tile"] = (99, j, val)
    with pytest.raises(IndexError):
        kw.verify(bad, A2, B2, 99, nonce, 1 << 6)


# ---------------------------------------------------------------------------
# VRF (HMAC stub)
# ---------------------------------------------------------------------------

def test_vrf_prove_returns_int_and_hex_proof():
    vrf = VRF("sk-1")
    out, proof = vrf.prove("msg")
    assert isinstance(out, int) and out > 0
    assert isinstance(proof, str) and len(proof) == 64
    assert all(c in "0123456789abcdef" for c in proof)


def test_vrf_verify_roundtrip_accepts():
    vrf = VRF("sk-1")
    out, proof = vrf.prove("msg")
    assert VRF.verify("sk-1", "msg", out, proof) is True


def test_vrf_verify_rejects_wrong_key():
    vrf = VRF("sk-1")
    out, proof = vrf.prove("msg")
    assert VRF.verify("sk-2", "msg", out, proof) is False


def test_vrf_verify_rejects_wrong_message():
    vrf = VRF("sk-1")
    out, proof = vrf.prove("msg")
    assert VRF.verify("sk-1", "other", out, proof) is False


def test_vrf_verify_rejects_wrong_output_or_proof():
    vrf = VRF("sk-1")
    out, proof = vrf.prove("msg")
    assert VRF.verify("sk-1", "msg", out + 1, proof) is False
    assert VRF.verify("sk-1", "msg", out, "0" * 64) is False


# ---------------------------------------------------------------------------
# TaskSpec
# ---------------------------------------------------------------------------

def test_taskspec_commits_are_set_and_deterministic():
    s1 = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    s2 = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    assert s1.program_commit == s2.program_commit
    assert s1.program_commit != ""
    assert s1.public_inputs_commit != ""


def test_taskspec_commit_differs_on_harness_or_flops():
    s1 = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    assert TaskSpec("other", (A2, A2), 64, DEADLINE_H).program_commit != s1.program_commit
    assert TaskSpec("mm", (A2, A2), 128, DEADLINE_H).program_commit != s1.program_commit


def test_taskspec_public_inputs_commit_follows_object_identity():
    p1 = (A2, A2)
    p2 = ([list(r) for r in A2], [list(r) for r in A2])  # esit icerik, baska nesne
    s1 = TaskSpec("mm", p1, 64, DEADLINE_H)
    s2 = TaskSpec("mm", p2, 64, DEADLINE_H)
    assert p1 is not p2
    assert s1.public_inputs_commit != s2.public_inputs_commit
    s3 = TaskSpec("mm", p1, 64, DEADLINE_H)  # ayni nesne -> ayni commit
    assert s3.public_inputs_commit == s1.public_inputs_commit


# ---------------------------------------------------------------------------
# Chain — kurulum ve submit_task
# ---------------------------------------------------------------------------

def test_chain_genesis_state():
    ch = Chain()
    assert ch.height() == 0
    assert ch.tip() == S("genesis")
    assert len(ch.blocks) == 1
    assert ch.tasks == {} and ch.miners == {}
    assert ch.burn_address_balance == 0 and ch.slashed_total == 0
    assert ch.D == 1 << 6


def test_chain_defaults_from_constants():
    ch = Chain()
    assert ch.retarget_window == RETARGET_WINDOW == 1000
    assert ch.target_block_time == T_B == 0.1
    assert ul.CLIP_LO == 0.25 and ul.CLIP_HI == 4.0
    assert SEED == 20260919 and W_s == 100 and EPOCH_LOOKBACK == 64
    assert BOND_RATIO == 1.0 and C_FEE == 500 and FRAUD_REWARD == 50


def test_submit_task_fee_escrow_burn_split_tv5():
    ch = Chain()
    spec = TaskSpec("mm-2x2", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("client-1", spec, fee=100, burn_rate=0.3)
    assert t.burned == 30 and t.escrow == 70 and t.bond == 100
    assert ch.burn_address_balance == 30
    assert t.state == "COMMITTED"
    assert t.fee == 100


def test_submit_task_burn_accumulates_in_burn_address():
    ch = Chain()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    ch.submit_task("c1", spec, 100, 0.2)
    ch.submit_task("c2", spec, 100, 0.1)
    assert ch.burn_address_balance == 30
    assert len(ch.tasks) == 2


def test_submit_task_burn_rate_upper_boundary_accepted():
    ch = Chain()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.5)
    assert t.burned == 50 and t.escrow == 50


def test_submit_task_rejects_non_positive_fee():
    ch = Chain()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    with pytest.raises(AssertionError):
        ch.submit_task("c1", spec, 0, 0.2)
    with pytest.raises(AssertionError):
        ch.submit_task("c1", spec, -5, 0.2)


def test_submit_task_rejects_burn_rate_out_of_half_open_interval():
    ch = Chain()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    with pytest.raises(AssertionError):
        ch.submit_task("c1", spec, 100, 0.0)
    with pytest.raises(AssertionError):
        ch.submit_task("c1", spec, 100, 0.5000001)
    with pytest.raises(AssertionError):
        ch.submit_task("c1", spec, 100, -0.1)


def test_submit_task_truncates_burn_to_int():
    ch = Chain()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 99, 0.333)
    assert t.burned == int(99 * 0.333) == 32
    assert t.escrow == 99 - 32 == 67


def test_submit_task_tid_is_deterministic():
    ch = Chain()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t1 = ch.submit_task("c1", spec, 100, 0.2)
    t2 = ch.submit_task("c1", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.2)
    assert t1.tid == t2.tid
    t3 = ch.submit_task("c2", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.2)
    assert t3.tid != t1.tid


# ---------------------------------------------------------------------------
# epoch_seed / assign_tasks
# ---------------------------------------------------------------------------

def test_epoch_seed_refuses_missing_lookback():
    ch = Chain()
    with pytest.raises(AssertionError):
        ch.epoch_seed(ch.height())


def test_epoch_seed_uses_the_lookback_block():
    ch = _chain_with_lookback(70)
    h_exp = 70 - EPOCH_LOOKBACK
    expected = H("seed", ch.blocks[h_exp])
    assert ch.epoch_seed(70) == expected
    assert ch.epoch_seed(70) != H("seed", ch.blocks[h_exp + 1])


def test_assign_tasks_assigns_with_prob_one():
    ch = _chain_with_lookback()
    t = ch.submit_task("c1", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.2)
    got = list(ch.assign_tasks("m1", [t], prob=1.0))
    assert got == [t]
    assert t.state == "ASSIGNED" and t.assignee == "m1"
    assert t.vrf_out != 0 and len(t.vrf_proof) == 64


def test_assign_tasks_skips_non_committed_state():
    ch = _chain_with_lookback()
    t = ch.submit_task("c1", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.2)
    t.state = "SOLVED"
    assert list(ch.assign_tasks("m1", [t], prob=1.0)) == []
    assert t.state == "SOLVED"  # degismedi


def test_assign_tasks_prob_zero_crashes_kok3():
    """KOK-3 (bulgu): w >= prob oldugunda (lotteri kaybeden task) atama
    yapilmaz ama VRF-verify assert'i yine de calisir; vrf_out=0 ve
    vrf_proof='' defaultlari ile kiyaslaninca AssertionError firlatir."""
    ch = _chain_with_lookback()
    t = ch.submit_task("c1", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.2)
    with pytest.raises(AssertionError):
        list(ch.assign_tasks("m1", [t], prob=0.0))
    assert t.state == "COMMITTED" and t.assignee == ""


def test_assigned_task_vrf_proof_verifies():
    ch = _chain_with_lookback()
    t = ch.submit_task("c1", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    seed = ch.epoch_seed(ch.height())
    assert VRF.verify("sk-m1", str(seed) + "|" + t.tid, t.vrf_out, t.vrf_proof)


# ---------------------------------------------------------------------------
# miner_bond / mine_block
# ---------------------------------------------------------------------------

def test_miner_bond_setdefault_creates_and_reuses():
    ch = Chain()
    m1 = ch.miner_bond("m1")
    assert m1 == {"bond": 0, "slashed": 0}
    assert ch.miner_bond("m1") is m1


def test_mine_block_rejects_non_pq_proof_system_tv10():
    ch = Chain()
    with pytest.raises(AssertionError):
        ch.mine_block("m1", [], A2, A2, proof_system_id="legacy-snark-v0")


def test_mine_block_returns_full_receipt_and_grows_chain():
    ch = Chain()
    blk = ch.mine_block("m1", [], A2, B2)
    assert set(blk) >= {"hash", "ctx", "nonce", "cert", "u_proofs", "fee_total",
                        "miner", "phi", "height"}
    assert blk["miner"] == "m1"
    assert blk["nonce"] >= 1
    assert blk["u_proofs"] == [] and blk["fee_total"] == 0
    assert ch.height() == 1 and ch.tip() == blk["hash"]
    assert blk["ctx"] == H("ctx", S("genesis"), "m1", DEFAULT_PS)


def test_mine_block_cert_verifies_off_chain():
    ch = Chain()
    blk = ch.mine_block("m1", [], A2, B2)
    assert ch.kernel.verify(blk["cert"], A2, B2, blk["ctx"], blk["nonce"], ch.D)


def test_mine_block_phi_is_zero_without_tasks():
    ch = Chain()
    blk = ch.mine_block("m1", [], A2, A2)
    assert blk["phi"] == 0.0


def test_mine_block_phi_formula_with_assigned_tasks():
    ch = _chain_with_lookback()
    spec = TaskSpec("mm", (A2, A2), 256, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A2, A2)
    expected = 256 / (256 + G_FLOPS * blk["nonce"])
    assert blk["phi"] == pytest.approx(expected)
    assert 0.0 < blk["phi"] <= 1.0


def test_mine_block_solves_matmul_for_assigned_tasks():
    ch = _chain_with_lookback()
    spec = TaskSpec("mm", (A2, B2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A2, B2)
    expected_C = [[19, 22], [43, 50]]  # A2 x B2
    assert blk["u_proofs"][0]["result"] == expected_C
    assert t.state == "SOLVED" and t.result == expected_C
    assert t.proof_height == ch.height() - 1


def test_mine_block_wrong_result_perturbs_first_entry_mod_q():
    ch = _chain_with_lookback()
    spec = TaskSpec("mm", (A2, B2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A2, B2, wrong_result=True)
    assert blk["u_proofs"][0]["result"][0][0] == (19 + 7) % 97
    assert t.result[0][0] == (19 + 7) % 97


def test_mine_block_anti_aggregation_guard_tv6():
    ch = _chain_with_lookback()
    tasks = [ch.submit_task(f"c{k}", TaskSpec("mm", (A2, A2), 64, DEADLINE_H), 100, 0.1)
             for k in range(6)]  # 6 * 100 = 600 > C_FEE=500
    with pytest.raises(AssertionError, match="anti-aggregation"):
        ch.mine_block("m1", tasks, A2, A2)
    # parcali cozum gecer
    ch.mine_block("m1", tasks[:3], A2, A2)
    ch.mine_block("m1", tasks[3:], A2, A2)
    assert ch.height() >= 2


def test_mine_block_u_proof_structure():
    ch = _chain_with_lookback()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A2, A2)
    p = blk["u_proofs"][0]
    assert set(p) == {"tid", "root", "result", "ps", "height", "flops"}
    assert p["tid"] == t.tid and p["ps"] == DEFAULT_PS
    assert p["flops"] == 64 and p["root"] == S("u", t.tid, p["result"])


def test_mine_block_accepts_the_other_pq_schema():
    ch = Chain()
    blk = ch.mine_block("m1", [], A2, A2, proof_system_id="stark-pq-1")
    assert ch.validate_block(blk, A2, A2) == "ACCEPT"


# ---------------------------------------------------------------------------
# validate_block — her RED sebebi
# ---------------------------------------------------------------------------

def _honest_block(ch):
    return ch.mine_block("m1", [], A2, B2)


def test_validate_block_accepts_honest_empty_block_tv8():
    ch = Chain()
    blk = _honest_block(ch)
    assert ch.validate_block(blk, A2, B2) == "ACCEPT"


def test_validate_block_rejects_bad_g_certificate():
    ch = Chain()
    blk = _honest_block(ch)
    blk["cert"] = {"tile": (0, 0, 123456789), "m": 1}
    assert ch.validate_block(blk, A2, B2) == "REJECT:G-cert"


def test_validate_block_rejects_phi_out_of_range():
    ch = Chain()
    blk = _honest_block(ch)
    blk["phi"] = 1.5
    assert ch.validate_block(blk, A2, B2) == "REJECT:phi-range"
    blk["phi"] = -0.001
    assert ch.validate_block(blk, A2, B2) == "REJECT:phi-range"


def test_validate_block_rejects_non_pq_schema_in_proof():
    ch = _chain_with_lookback()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A2, A2)
    blk["u_proofs"][0]["ps"] = "legacy-snark-v0"
    assert ch.validate_block(blk, A2, A2) == "REJECT:PQ-schema"


def test_validate_block_rejects_unsolved_task_state():
    ch = _chain_with_lookback()
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A2, A2)
    assert ch.validate_block(blk, A2, A2) == "ACCEPT"
    ch.settle(t.tid) if t.state == "SOLVED" else None
    assert t.state == "SETTLED"
    blk2 = dict(blk)
    assert ch.validate_block(blk2, A2, A2) == "REJECT:task-state"


def test_validate_block_rejects_anti_aggregation_fee_total():
    ch = Chain()
    blk = _honest_block(ch)
    blk["fee_total"] = C_FEE + 1
    assert ch.validate_block(blk, A2, B2) == "REJECT:anti-aggregation"
    blk["fee_total"] = C_FEE
    assert ch.validate_block(blk, A2, B2) == "ACCEPT"


def test_validate_block_crashes_on_unknown_task_id_kok6():
    """KOK-6 (bulgu): u_proof bilinmeyen bir tid icin self.tasks[p["tid"]]
    KeyError firlatir; REJECT:unknown-task donmez."""
    ch = Chain()
    blk = _honest_block(ch)
    blk["u_proofs"] = [{"tid": "yok-boyle-gorev", "ps": DEFAULT_PS}]
    with pytest.raises(KeyError):
        ch.validate_block(blk, A2, B2)


# ---------------------------------------------------------------------------
# challenge / settle
# ---------------------------------------------------------------------------

def _assigned_task(ch, fee=100, burn=0.2):
    spec = TaskSpec("mm", (A2, A2), 64, DEADLINE_H)
    t = ch.submit_task("c1", spec, fee, burn)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    return t


def test_challenge_slashes_fraud_tv7():
    ch = _chain_with_lookback()
    t = _assigned_task(ch)
    blk = ch.mine_block("m1", [t], A2, A2, wrong_result=True)
    assert ch.validate_block(blk, A2, A2) == "ACCEPT"  # on-chain gorulmez
    verdict, rew = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "SLASHED" and rew == FRAUD_REWARD == 50
    assert ch.miners["m1"]["slashed"] >= 100
    assert ch.slashed_total >= 100
    assert t.state == "SLASHED"


def test_challenge_refuses_after_fraud_window():
    ch = _chain_with_lookback()
    t = _assigned_task(ch)
    ch.mine_block("m1", [t], A2, A2, wrong_result=True)
    with pytest.raises(AssertionError):
        ch.challenge("v1", t.tid, ch.height() + W_s + 1)


def test_challenge_accepts_exactly_at_window_edge():
    ch = _chain_with_lookback()
    t = _assigned_task(ch)
    ch.mine_block("m1", [t], A2, A2, wrong_result=True)
    # proof_height + W_s tam sinirda hala acik (<= sozlesmesi)
    verdict, _ = ch.challenge("v1", t.tid, t.proof_height + W_s)
    assert verdict == "SLASHED"


def test_challenge_rejects_malicious_challenge_from_registered_miner():
    ch = _chain_with_lookback()
    t = _assigned_task(ch)
    ch.mine_block("m1", [t], A2, A2)  # dogru sonuc
    ch.miner_bond("v1")  # itirazci kayitli
    verdict, rew = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "CHALLENGE_REJECTED" and rew == 0
    assert ch.miners["v1"]["slashed"] == 1
    assert t.state == "SOLVED"


def test_challenge_crashes_on_unregistered_challenger_kok4():
    """KOK-4 (bulgu): kotu niyetli itiraz yolunda self.miners[challenger]
    kayitli degilse KeyError; challengers'in onceden madencilik yapmis
    olmasi beklenir ama bu zorunluluk kodda ifade edilmemis."""
    ch = _chain_with_lookback()
    t = _assigned_task(ch)
    ch.mine_block("m1", [t], A2, A2)
    with pytest.raises(KeyError):
        ch.challenge("v_never_mined", t.tid, ch.height())


def test_settle_pays_from_solved_task_but_escrow_goes_negative_kok2():
    """KOK-2 (bulgu): pay = fee - burned ve escrow -= (burned + pay);
    escrow = fee - burn oldugundan sonuc -(burn) olur (burn iki kez sayilir)."""
    ch = _chain_with_lookback()
    t = _assigned_task(ch, fee=100, burn=0.3)
    ch.mine_block("m1", [t], A2, A2)  # SOLVED
    pay = ch.settle(t.tid)
    assert pay == 70
    assert t.state == "SETTLED"
    assert t.escrow == 70 - (30 + 70) == -30  # negatife dustu


def test_settle_returns_zero_for_unsolved_task():
    ch = _chain_with_lookback()
    t = _assigned_task(ch)
    assert ch.settle(t.tid) == 0  # hala SOLVED degil (madencilik yapilmadi)
    assert t.state == "ASSIGNED"


# ---------------------------------------------------------------------------
# retarget / sim_block / record_time
# ---------------------------------------------------------------------------

def test_retarget_is_noop_before_the_window():
    ch = Chain()
    ch.retarget_window = 4
    for i in range(3):
        ch.record_time(1.0)
    assert ch.retarget() is None


def test_retarget_fires_once_per_window_and_reports_lambda_hat():
    ch = Chain()
    ch.retarget_window = 4
    for i in range(4):
        ch.record_time(1.0)
    D_before = ch.D
    r = ch.retarget()
    assert r is not None
    assert r["T_act"] == pytest.approx(4.0)
    assert r["lam_hat"] == pytest.approx(D_before * 4 / 4.0)
    assert r["lam_smooth"] == r["lam_hat"]  # tek pencere -> medyan kendisi
    assert ch.window_history[-1] == (r["T_act"], D_before, r["lam_hat"])
    ch.record_time(1.0)
    assert ch.retarget() is None  # pencere dolana kadar tekrar yok


def test_retarget_clips_upward_to_4x():
    ch = Chain()
    ch.retarget_window = 4
    for _ in range(4):
        ch.record_time(0.01)  # cok hizli -> lam_hat devasa
    D_old = ch.D
    r = ch.retarget()
    assert r["D"] == D_old * 4
    assert ch.D == D_old * 4


def test_retarget_clips_downward_to_quarter():
    ch = Chain()
    ch.retarget_window = 4
    for _ in range(4):
        ch.record_time(1000.0)  # cok yavas -> lam_hat kucuk
    D_old = ch.D
    r = ch.retarget()
    assert r["D"] == D_old // 4
    assert ch.D >= 1


def test_retarget_never_drops_below_one():
    ch = Chain()
    ch.retarget_window = 4
    for _ in range(4):
        ch.record_time(1e9)
    r = ch.retarget()
    assert ch.D >= 1
    assert r is not None


def test_retarget_median_smooths_the_last_three_windows():
    ch = Chain()
    ch.retarget_window = 2
    for T in (0.5, 0.25, 2.0):  # uc farkli pencere
        for _ in range(2):
            ch.record_time(T)
        assert ch.retarget() is not None
    assert len(ch.window_history) == 3
    for _ in range(2):
        ch.record_time(0.25)
    r = ch.retarget()
    assert r is not None
    # median filtre: lam_smooth son 3 pencerenin sirali ortancasi (len//2)
    last3 = [h[2] for h in ch.window_history[-3:]]
    assert r["lam_smooth"] == sorted(last3)[len(last3) // 2]
    assert last3[-1] == r["lam_hat"]  # guncul pencere gecmise eklendi


def test_sim_block_grows_time_and_chain():
    ch = Chain()
    ch.retarget_window = 8
    r = ch.sim_block(lam=100.0)
    assert r is None  # ilk blokta retarget yok (n=1, 1 % 8 != 0)
    assert len(ch.blocks) == 2
    assert ch.times[-1] > ch.times[-2]
    for _ in range(7):
        ch.sim_block(lam=100.0)
    assert ch.height() == 8  # 8. blokta retarget tetiklendi


def test_record_time_accumulates_monotonically():
    ch = Chain()
    ch.record_time(1.5)
    ch.record_time(2.5)
    assert ch.times == [0.0, 1.5, 4.0]


# ---------------------------------------------------------------------------
# kurtosis (TV-9)
# ---------------------------------------------------------------------------

def test_kurtosis_of_constant_matrix_is_zero():
    assert kurtosis([[1, 1], [1, 1]]) == 0.0


def test_kurtosis_is_positive_for_non_degenerate_matrix():
    import random
    r2 = random.Random(7)
    m = [[r2.randint(-64, 64) for _ in range(8)] for _ in range(8)]
    k = kurtosis(m)
    assert k > 0


def test_kurtosis_uniform_is_lower_than_gaussian():
    # uniform dagilimin kurtosis'i ~1.8; Gauss ~3.0 (Basu 2606.04819)
    import random
    r2 = random.Random(7)
    uniform = [[r2.randint(-64, 64) for _ in range(64)] for _ in range(64)]
    gauss = [[int(r2.gauss(0, 3)) for _ in range(64)] for _ in range(64)]
    ku, kg = kurtosis(uniform), kurtosis(gauss)
    assert 0.5 < ku < 4.0
    assert 1.5 < kg < 6.0
    assert ku < kg


def test_tv9_kurtosis_trap_returns_the_documented_fields():
    res = ul.tv9_kurtosis_trap()
    assert set(res) == {"uniform", "nn", "adversarial",
                        "adversarial_passes_naive_check"}
    # uniform ~1.8 < nn ~3-4; ikisi depositive
    assert 0.5 < res["uniform"] < 4.5
    assert res["uniform"] < res["nn"]
    # Basu 2606.04819: adversarial N(0,18) ~3.0 ile naif 2.0-4.0 kontrolunden GECER
    assert 2.0 <= res["adversarial"] <= 4.0
    assert res["adversarial_passes_naive_check"] is True


# ---------------------------------------------------------------------------
# gonderilen test vektorleri
# ---------------------------------------------------------------------------

def test_tv5_escrow_burn_vector():
    burned, escrow, sybil = ul.tv5()
    assert (burned, escrow) == (30, 70)
    assert sybil == 30000


def test_tv6_anti_aggregation_vector():
    caught, nblk = ul.tv6()
    assert caught is True
    assert nblk >= 2


def test_tv7_fraud_slash_vector():
    verdict, slashed, rew = ul.tv7()
    assert verdict == "SLASHED"
    assert slashed >= 100
    assert rew == FRAUD_REWARD


def test_tv8_zero_demand_liveness_vector():
    ok = ul.tv8()
    assert ok == 1000


def test_tv10_pq_downgrade_vector():
    assert ul.tv10() is True


def test_tv123_stub_replay_rejection_vector():
    assert "PASS" in ul.tv123_stub()


# ---------------------------------------------------------------------------
# constants sanity
# ---------------------------------------------------------------------------

def test_pq_set_and_default():
    assert DEFAULT_PS in PQ_SET
    assert PQ_SET == {"stark-circle-1", "stark-pq-1"}
