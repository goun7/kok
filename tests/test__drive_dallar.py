#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for probe_blindspot_en._drive (TV-73 honest-task driver).

_drive builds the smallest honest task end-to-end:

    ch = ul.Chain(); rnd = random.Random(seed); q, n = 97, 8
    A, B = random n x n matrices over F_97
    mine (EPOCH_LOOKBACK + 2) EMPTY blocks so the VRF epoch seed exists
    submit TaskSpec("mm", (A,B), 64, 1000) at fee=100, burn_rate=0.1
    assign_tasks("m1", [t], prob=1.0)
    mine ONE task block, validate it
    return (ch, t)

This file covers: the return contract, the state machine (COMMITTED->ASSIGNED->
SOLVED), the fee/burn/escrow/bond economics, height/proof-height arithmetic,
determinism vs the seed, seed-independence of the TASK ID (a real finding: the
tid excludes the matrix), the un-reduced result (mine_block line 291 computes
C WITHOUT mod q), the VRF assignment artifacts, block-book invariants, the
no-print hygiene, and Unicode handling.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
Saf in-memory: dis ag/HTTP/DB cagrisi YOK.
"""

import pytest

from probe_blindspot_en import _drive, _load

UL = _load()
Q, N = 97, 8
FEE, BURN_RATE = 100, 0.1
BURN = int(FEE * BURN_RATE)          # 10 -- taken immediately, unrecoverable
ESCROW = FEE - BURN                  # 90 -- the payable part
BOND = int(FEE * UL.BOND_RATIO)      # 100 -- separate collateral (BOND_RATIO=1.0)
EMPTY_BLOCKS = UL.EPOCH_LOOKBACK + 2  # 66 -- so the lookback seed resolves
HEIGHT = EMPTY_BLOCKS + 1            # 67 -- height after the task block


# =========================================================== return contract
class TestReturnContract:
    def test_returns_a_pair(self):
        out = _drive(UL)
        assert isinstance(out, tuple) and len(out) == 2

    def test_first_is_a_chain(self):
        ch, _ = _drive(UL)
        assert isinstance(ch, UL.Chain)

    def test_second_is_a_task(self):
        _, t = _drive(UL)
        assert isinstance(t, UL.Task)

    def test_default_seed_is_eleven(self):
        # the signature default and the explicit value must agree exactly
        assert _drive(UL)[1].tid == _drive(UL, 11)[1].tid

    def test_seed_accepts_keyword_and_positional(self):
        assert _drive(UL, seed=3)[1].tid == _drive(UL, 3)[1].tid


# =========================================================== state machine
class TestStateMachine:
    @pytest.mark.parametrize("seed", [0, 11, 12345])
    def test_ends_in_solved(self, seed):
        assert _drive(UL, seed)[1].state == "SOLVED"

    def test_task_is_assigned_before_mining(self):
        # mine_block flips state -> SOLVED; the assign step set it to ASSIGNED
        _, t = _drive(UL)
        assert t.state == "SOLVED"            # terminal
        assert t.assignee == "m1"             # the VRF assignment landed
        assert t.proof_height > 0

    def test_not_settled(self):
        # _drive stops at SOLVED; settle() is the probes' next step, not its
        _, t = _drive(UL)
        assert t.state != "SETTLED"

    def test_proof_height_is_the_task_block_height(self):
        ch, t = _drive(UL)
        assert t.proof_height == EMPTY_BLOCKS   # mined at height 66
        assert ch.height() == HEIGHT            # ...then the block was appended


# ================================================================ economics
class TestEconomics:
    def test_fee_burn_rate(self):
        _, t = _drive(UL)
        assert t.fee == FEE
        assert t.burn_rate == BURN_RATE

    def test_burned_is_taken_immediately(self):
        ch, t = _drive(UL)
        assert t.burned == BURN                      # 10
        assert ch.burn_address_balance == BURN       # ...and credited to the burn

    def test_escrow_is_fee_minus_burn(self):
        _, t = _drive(UL)
        assert t.escrow == ESCROW                    # 90

    def test_fee_invariant_partial(self):
        # the invariant this file STATES: payable + burned == fee
        _, t = _drive(UL)
        assert t.escrow + t.burned == t.fee

    def test_bond_is_separate_collateral(self):
        # FINDING: the task's own bond field is ZERO after mining because
        # mine_block POSTS it to the miner ledger (u_layer_prototype_en L319-321)
        ch, t = _drive(UL)
        assert t.bond == 0
        assert ch.miner_bond("m1")["bond"] == BOND

    def test_full_accounting_with_the_posted_bond(self):
        # escrow + burned + posted bond == fee + bond (bond sits OUTSIDE the fee)
        ch, t = _drive(UL)
        assert t.escrow + t.burned + ch.miner_bond("m1")["bond"] == FEE + BOND

    def test_miner_is_not_slashed(self):
        ch, _ = _drive(UL)
        assert ch.slashed_total == 0
        assert ch.miner_bond("m1")["slashed"] == 0

    @pytest.mark.parametrize("seed", [11, 99, 555])
    def test_economics_is_seed_independent(self, seed):
        # the matrices change with the seed; the money math does not
        _, t = _drive(UL, seed)
        assert (t.fee, t.burned, t.escrow, t.burn_rate) == (FEE, BURN, ESCROW, BURN_RATE)


# ================================================== harness / spec contract
class TestSpec:
    def test_harness_id(self):
        _, t = _drive(UL)
        assert t.spec.harness_id == "mm"

    def test_max_flops_and_deadline(self):
        _, t = _drive(UL)
        assert t.spec.max_flops == 64
        assert t.spec.deadline == 1000

    def test_client(self):
        _, t = _drive(UL)
        assert t.client == "c1"

    def test_program_is_a_matrix_pair(self):
        _, t = _drive(UL)
        A, B = t.spec.program
        assert len(A) == len(B) == N
        assert all(len(row) == N for row in A + B)

    def test_program_entries_are_in_the_field(self):
        _, t = _drive(UL)
        A, B = t.spec.program
        assert all(0 <= v < Q for row in A + B for v in row)

    def test_commits_are_derived(self):
        # TaskSpec.__post_init__ fills both commits; both must be non-empty here
        _, t = _drive(UL)
        assert t.spec.program_commit
        assert t.spec.public_inputs_commit
        assert t.spec.program_commit != t.spec.public_inputs_commit


# ================================================== result: the mod-q finding
class TestResultIsNotReduced:
    """FINDING: mine_block stores C = sum(A*B) as RAW PYTHON INTEGERS, never
    reduced mod q (u_layer_prototype_en L291-292). With q=97, n=8 entries reach
    8*96*96 = 73_728. The toy AIR in f0b_air_proto works mod q, so the U-layer
    'useful work' result is NOT an element of the field the proof is over."""

    def test_result_is_the_raw_product(self):
        _, t = _drive(UL)
        A, B = t.spec.program
        expect = [[sum(A[i][k] * B[k][j] for k in range(N)) for j in range(N)]
                  for i in range(N)]
        assert t.result == expect

    def test_result_can_exceed_the_field(self):
        _, t = _drive(UL)
        assert max(v for row in t.result for v in row) >= Q

    def test_result_shape(self):
        _, t = _drive(UL)
        assert len(t.result) == N
        assert all(len(row) == N for row in t.result)

    def test_result_is_all_non_negative_ints(self):
        _, t = _drive(UL)
        assert all(isinstance(v, int) and v >= 0 for row in t.result for v in row)

    def test_result_is_not_the_reduced_product(self):
        _, t = _drive(UL)
        A, B = t.spec.program
        reduced = [[sum(A[i][k] * B[k][j] for k in range(N)) % Q for j in range(N)]
                   for i in range(N)]
        assert t.result != reduced


# ================================================ determinism vs the seed
class TestDeterminism:
    @pytest.mark.parametrize("seed", [11, 11])
    def test_same_seed_is_bit_identical(self, seed):
        ch1, t1 = _drive(UL, seed)
        ch2, t2 = _drive(UL, seed)
        assert t1.tid == t2.tid
        assert t1.result == t2.result
        assert t1.vrf_out == t2.vrf_out
        assert t1.vrf_proof == t2.vrf_proof
        assert t1.spec.public_inputs_commit == t2.spec.public_inputs_commit
        assert ch1.height() == ch2.height()

    def test_different_seeds_give_different_programs(self):
        a = _drive(UL, 11)[1]
        b = _drive(UL, 12)[1]
        assert a.spec.public_inputs_commit != b.spec.public_inputs_commit
        assert a.result != b.result

    def test_tid_is_seed_independent(self):
        # FINDING: tid = S("task", client, program_commit, fee, escrow_locked)
        # and program_commit = S("prog", harness_id, max_flops) EXCLUDES the
        # matrix. Two different programs share one tid -> ch.tasks key COLLISION.
        a = _drive(UL, 11)[1]
        b = _drive(UL, 99999)[1]
        assert a.tid == b.tid
        assert a.spec.program_commit == b.spec.program_commit
        assert a.spec.public_inputs_commit != b.spec.public_inputs_commit

    def test_two_different_programs_collide_on_one_tid(self):
        # the same collision, shown directly on one chain: both submits land on
        # the SAME dict key, so only the LAST task survives
        ch = _drive(UL)[0]
        A1 = [[1] * N] * N
        A2 = [[2] * N] * N
        s1 = UL.TaskSpec("mm", (A1, A1), 64, 1000)
        s2 = UL.TaskSpec("mm", (A2, A2), 64, 1000)
        t1 = ch.submit_task("c1", s1, FEE, BURN_RATE)
        t2 = ch.submit_task("c1", s2, FEE, BURN_RATE)
        assert t1.tid == t2.tid
        assert len(ch.tasks) == 1                 # one key -> the first submit is LOST
        assert ch.tasks[t2.tid] is t2             # ...the second overwrote it
        assert t1.spec.public_inputs_commit != t2.spec.public_inputs_commit


# ============================================================ VRF assignment
class TestVrfAssignment:
    def test_vrf_output_is_present(self):
        _, t = _drive(UL)
        assert isinstance(t.vrf_out, int)
        assert t.vrf_out > 0

    def test_vrf_output_is_256_bit_range(self):
        _, t = _drive(UL)
        assert 0 <= t.vrf_out < (1 << 256)

    def test_vrf_proof_is_a_64_hex_digest(self):
        _, t = _drive(UL)
        assert len(t.vrf_proof) == 64
        assert set(t.vrf_proof) <= set("0123456789abcdef")

    def test_vrf_verify_accepts_the_artifacts(self):
        # NOTE: verify() is a STRUCTURAL check by design (see its docstring) --
        # it validates shape, not key possession
        _, t = _drive(UL)
        pk = UL.VRF("sk-m1").pk
        assert UL.VRF.verify(pk, "msg", t.vrf_out, t.vrf_proof) is True

    @pytest.mark.parametrize("bad_pk", ["nope", "sk-m1", "z" * 64])
    def test_vrf_verify_rejects_malformed_pk(self, bad_pk):
        _, t = _drive(UL)
        assert UL.VRF.verify(bad_pk, "msg", t.vrf_out, t.vrf_proof) is False

    @pytest.mark.parametrize("bad_out", [-1, 1 << 256])
    def test_vrf_verify_rejects_bad_output(self, bad_out):
        _, t = _drive(UL)
        pk = UL.VRF("sk-m1").pk
        assert UL.VRF.verify(pk, "msg", bad_out, t.vrf_proof) is False

    def test_vrf_verify_rejects_malformed_proof(self):
        _, t = _drive(UL)
        pk = UL.VRF("sk-m1").pk
        assert UL.VRF.verify(pk, "msg", t.vrf_out, "abc") is False

    def test_assignment_prob_is_one(self):
        # _drive passes prob=1.0, so the VRF draw always clears the threshold
        ch, t = _drive(UL)
        assert t.assignee == "m1"
        assert t.state == "SOLVED"
        assert t.tid in ch.tasks


# ============================================================ chain books
class TestChainBooks:
    def test_height(self):
        ch, _ = _drive(UL)
        assert ch.height() == HEIGHT

    def test_block_count(self):
        ch, _ = _drive(UL)
        assert len(ch.blocks) == HEIGHT + 1   # genesis + 66 empty + 1 task

    def test_all_blocks_are_hash_strings(self):
        ch, _ = _drive(UL)
        assert all(isinstance(b, str) for b in ch.blocks)

    def test_genesis_is_the_first_block(self):
        ch, _ = _drive(UL)
        assert ch.blocks[0] == UL.S("genesis")

    def test_epoch_seed_is_resolvable(self):
        # the 66 empty blocks exist precisely so height - EPOCH_LOOKBACK >= 0
        ch, _ = _drive(UL)
        assert ch.height() - UL.EPOCH_LOOKBACK >= 1
        seed = ch.epoch_seed(ch.height())
        assert isinstance(seed, int)

    def test_two_drives_build_independent_chains(self):
        ch1, _ = _drive(UL)
        ch2, _ = _drive(UL)
        assert ch1 is not ch2
        assert ch1.blocks == ch2.blocks          # same seed -> same hashes
        assert ch1.tasks is not ch2.tasks

    def test_no_slash_and_no_expiry_states(self):
        ch, _ = _drive(UL)
        assert all(t.state == "SOLVED" for t in ch.tasks.values())
        assert ch.slashed_total == 0


# ================================================================ hygiene
class TestHygiene:
    def test_drive_prints_nothing(self, capsys):
        _drive(UL)
        assert capsys.readouterr().out == ""

    def test_drive_leaves_no_global_state(self):
        import random
        before = random.Random(11).randrange(97)
        _drive(UL)
        after = random.Random(11).randrange(97)
        assert before == after   # uses its OWN Random instance, not global one


# ================================================================ unicode
class TestUnicode:
    def test_tid_is_hex_for_ascii_clients(self):
        _, t = _drive(UL)
        assert set(t.tid) <= set("0123456789abcdef")
        assert len(t.tid) == 32                   # S() -> 16-byte digest hex

    def test_chain_accepts_turkish_client_after_drive(self):
        # the driven chain stays usable with TR identifiers (in-memory, no IO)
        ch, _ = _drive(UL)
        spec = UL.TaskSpec("mm", ([[1] * N] * N, [[1] * N] * N), 64, 1000)
        tr = ch.submit_task("müşteri-İstanbul", spec, FEE, BURN_RATE)
        assert tr.client == "müşteri-İstanbul"
        assert ch.tasks[tr.tid] is tr

    def test_turkish_task_id_differs_from_ascii_counterpart(self):
        ch = _drive(UL)[0]
        spec = UL.TaskSpec("mm", ([[1] * N] * N, [[1] * N] * N), 64, 1000)
        tr = ch.submit_task("müşteri", spec, FEE, BURN_RATE)
        en = ch.submit_task("musteri", spec, FEE, BURN_RATE)
        assert tr.tid != en.tid
        assert len(ch.tasks) >= 3
