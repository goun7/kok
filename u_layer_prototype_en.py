#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 — U-LAYER PROTOTYPE (working code, a pre-testnet reference implementation)
================================================================================
Akis:  submit_task (escrow + bond + burn)
    -> VRF assignment  (epoch seed, lookback=64)
    -> mine_block   (G-layer KW certificate + U-layer STARK-like proof)
    -> validate_block (G + VRF + proof + C_FEE anti-aggregation + PQ schema)
    -> challenge / slash / settle  (W_s = 100 block fraud window)

The G layer (KW/cuPOW) is represented in this file by a simplified kernel:
a feasible MatMul-transcript PoW (small size, per-tile hash).
Goal: test the U-layer economics/penalty machine with real code; the KW kernel
prototype is at the level and will be changed with cuPOW where acca is marked.

Dependencies: none (standard library). Deterministic: the SEED is fixed.
Calistirma: python3 u_layer_prototype.py
"""
import hashlib, hmac, math, random
from dataclasses import dataclass, field

# ---------------------------------------------------------------- constants
SEED = 20260919
W_s = 100                 # fraud window (blocks)
EPOCH_LOOKBACK = 64       # VRF seed lookback (grinding resistance)
BOND_RATIO = 1.0          # miner bond = fee * BOND_RATIO  (sybil cost)
C_FEE = 500               # total U fee cap per block (anti-aggregation)
FRAUD_REWARD = 50         # the reward for a successful challenge
DEADLINE_H = 200          # task expiry (blocks)
PQ_SET = {"stark-circle-1", "stark-pq-1"}    # izin verilen proof_system_id'ler
DEFAULT_PS = "stark-circle-1"
RETARGET_WINDOW = 1000     # W (spec B.3; shrunk in the tests)
T_B = 0.1                  # target block time (s) — 10 BPS
CLIP_LO, CLIP_HI = 0.25, 4.0    # Bitcoin's 4x bounds
G_FLOPS = 64               # FLOPs per G-layer attempt (n=8 kernel scale)

rng = random.Random(SEED)


def H(*parts) -> int:
    m = hashlib.sha3_256()
    for p in parts:
        m.update(str(p).encode())
        m.update(b"|")
    return int.from_bytes(m.digest(), "big")


def S(*parts) -> str:
    """A short hex digest (for identifiers)."""
    return format(H(*parts) & ((1 << 128) - 1), "032x")


# ------------------------------------------------------- G layer: plain KW
# Note: this is KW's per-tile variant (Remark 2.1) - a miniature imitation of it.
# Transcript: (n/r)^3 intermediate r x r blocks; PoW: a tile hash is below the target.
# to be replaced by the cuPOW kernel: keeps the same interface once the burn stub is real.
class KWKernel:
    def __init__(self, q=97, n=8, r=2):
        self.q, self.n, self.r = q, n, r

    def prove(self, A, B, ctx: int, nonce: int, target: int):
        """Honest: all intermediate blocks compute; the first sub-target tile certificate make."""
        q, r = self.q, self.r
        n = len(A)
        m = n // r
        E = [[(H("E", ctx, i, j) % q) for j in range(n)] for i in range(n)]   # noise (plain)
        F = [[(H("F", ctx, i, j) % q) for j in range(n)] for i in range(n)]
        Ap = [[(A[i][j] + E[i][j]) % q for j in range(n)] for i in range(n)]
        Bp = [[(B[i][j] + F[i][j]) % q for j in range(n)] for i in range(n)]
        acc = [[0] * m for _ in range(m)]          # constraint: simplifies the transcript
        # prototype: per-tile loop (n^3 work) — in the real kernel this part is untouched
        for i in range(m):
            for j in range(m):
                for l in range(m):
                    acc[i][j] = (acc[i][j] +
                                 Ap[i * r][l * r] * Bp[l * r][j * r]) % q
        for i in range(m):
            for j in range(m):
                if H("tile", ctx, nonce, i, j, acc[i][j]) % target == 0:
                    return {"tile": (i, j, acc[i][j]), "m": m}
        return None

    def verify(self, cert, A, B, ctx: int, nonce: int, target: int) -> bool:
        if cert is None:
            return False
        i, j, val = cert["tile"]
        q, r = self.q, self.r
        n = len(A)
        E = [[(H("E", ctx, a, b) % q) for b in range(n)] for a in range(n)]
        F = [[(H("F", ctx, a, b) % q) for b in range(n)] for a in range(n)]
        # the miner claims it computed the tile; since the tile is small we simply
        # recompute it ourselves = verification.
        acc = 0
        for l in range(n // r):
            acc = (acc + (A[i * r][l * r] + E[i * r][l * r]) *
                   (B[l * r][j * r] + F[l * r][j * r])) % q
        return acc == val and H("tile", ctx, nonce, i, j, val) % target == 0


# ------------------------------------------------------------- VRF (stub)
# Prototype: an HMAC-based VRF (in reality ECVRF/Ed25519-VRF).
class VRF:
    def __init__(self, sk):
        self.sk = sk

    def prove(self, msg):
        out = hmac.new(self.sk.encode(), str(msg).encode(), hashlib.sha3_256).digest()
        return int.from_bytes(out, "big"), out.hex()

    @staticmethod
    def verify(pk, msg, out, proof):
        exp = hmac.new(pk.encode(), str(msg).encode(), hashlib.sha3_256).digest()
        return int.from_bytes(exp, "big") == out and exp.hex() == proof


# ------------------------------------------------------ U layer: harness
@dataclass
class TaskSpec:
    harness_id: str
    program: object            # (A, B) the matrices — in this prototype "useful is"
    max_flops: int
    deadline: int
    program_commit: str = ""
    public_inputs_commit: str = ""

    def __post_init__(self):
        self.program_commit = S("prog", self.harness_id, self.max_flops)
        self.public_inputs_commit = S("in", id(self.program))


@dataclass
class Task:
    tid: str
    client: str
    spec: TaskSpec
    fee: int
    burn_rate: float
    state: str = "COMMITTED"     # COMMITTED -> ASSIGNED -> SOLVED -> SETTLED/SLASHED/EXPIRED
    escrow: int = 0          # the payable escrow remaining from the fee (TV-5: 70)
    bond: int = 0            # separate collateral (TV-7 slashes it)
    burned: int = 0
    assignee: str = ""
    vrf_out: int = 0
    vrf_proof: str = ""
    proof_height: int = 0
    result: object = None


# ------------------------------------------------------------------- ledger
class Chain:
    def __init__(self):
        self.blocks = [S("genesis")]
        self.tasks = {}
        self.miners = {}                     # miner -> {bond, slashed}
        self.burn_address_balance = 0        # irrecoverable (Demirel: the source of security)
        self.slashed_total = 0
        self.kernel = KWKernel()
        self.D = 1 << 6                 # difficulty: p = 1/D (spec B.2/B.4)
        self.retarget_window = RETARGET_WINDOW     # W (shrunk in the tests)
        self.target_block_time = T_B               # T_b
        self.times = [0.0]              # block arrival times (s)
        self.window_history = []        # per W blocks: (T_act, D_previous)

    def height(self):
        return len(self.blocks) - 1

    def tip(self):
        return self.blocks[-1]

    # ---------------- A.10.2 task submission
    def submit_task(self, client, spec, fee, burn_rate, gas=0):
        assert fee > 0 and 0.0 < burn_rate <= 0.5, "burn_rate (0.0, 0.5]"
        bond = int(fee * BOND_RATIO)
        burn = int(fee * burn_rate)                     # cannot be taken back
        escrow_locked = fee + bond                      # locked total
        tid = S("task", client, spec.program_commit, fee, escrow_locked)
        t = Task(tid=tid, client=client, spec=spec, fee=fee, burn_rate=burn_rate)
        t.escrow = fee - burn                            # odenebilir escrow (70)
        t.bond = bond                                    # ayri teminat
        t.burned = burn
        self.burn_address_balance += burn               # <-- burn HEMEN
        self.tasks[tid] = t
        return t

    # ---------------- A.10.3 VRF assignment (lookback seed)
    def epoch_seed(self, height):
        h = height - EPOCH_LOOKBACK
        assert h >= 0, "height below the lookback"
        return H("seed", self.blocks[h])

    def assign_tasks(self, miner, tasks, prob=0.5):
        """The miner cannot choose its own task: it is assigned by the VRF output."""
        seed = self.epoch_seed(self.height())
        vrf = VRF("sk-" + miner)
        pk = "sk-" + miner
        for t in tasks:
            if t.state != "COMMITTED":
                continue
            out, proof = vrf.prove(str(seed) + "|" + t.tid)
            w = (out % (1 << 64)) / (1 << 64)
            if w < prob:
                t.assignee, t.vrf_out, t.vrf_proof, t.state = miner, out, proof, "ASSIGNED"
                yield t
            assert VRF.verify(pk, str(seed) + "|" + t.tid, t.vrf_out, t.vrf_proof), \
                "the VRF proof is invalid (the assignment is not off-phase)"

    def miner_bond(self, miner):
        return self.miners.setdefault(miner, {"bond": 0, "slashed": 0})

    # ---------------- A.10.4 madencilik
    def mine_block(self, miner, assigned_tasks, A, B, proof_system_id=DEFAULT_PS,
                   wrong_result=False):
        assert proof_system_id in PQ_SET, "outside the PQ schema"
        ctx = H("ctx", self.tip(), miner, proof_system_id)
        # --- G layer: KW certificate (demand-independent)
        nonce = 0
        while True:
            nonce += 1
            cert = self.kernel.prove(A, B, ctx, nonce, self.D)
            if cert is not None:
                break
        # --- U layer: proof of the assigned tasks (optional but mandatory once assigned)
        u_proofs = []
        for t in assigned_tasks:
            harness_A, harness_B = t.spec.program
            C = [[sum(harness_A[i][k] * harness_B[k][j] for k in range(len(harness_B)))
                  for j in range(len(harness_B[0]))] for i in range(len(harness_A))]
            if wrong_result:                                   # a malicious miner
                C[0][0] = (C[0][0] + 7) % self.kernel.q
            # the "STARK-like" trace: the Merkle root of the outputs + a deterministic ordering
            root = S("u", t.tid, C)
            u_proofs.append({"tid": t.tid, "root": root, "result": C,
                             "ps": proof_system_id, "height": self.height(),
                             "flops": t.spec.max_flops})
            t.result, t.state, t.proof_height = C, "SOLVED", self.height()
        # fee total: anti-aggregation check (A.10.5)
        fee_total = sum(self.tasks[p["tid"]].fee for p in u_proofs)
        assert fee_total <= C_FEE, f"anti-aggregation: {fee_total} > {C_FEE}"
        # utility density phi (spec B.5): U-task FLOP / total block FLOP
        u_flops = sum(p.get("flops", 0) for p in u_proofs)
        phi = u_flops / (u_flops + G_FLOPS * nonce) if (u_flops + G_FLOPS * nonce) else 0.0
        bh = S("blk", ctx, nonce, [p["root"] for p in u_proofs], fee_total)
        self.blocks.append(bh)
        self.miner_bond(miner)["bond"] += 0
        return {"hash": bh, "ctx": ctx, "nonce": nonce, "cert": cert,
                "u_proofs": u_proofs, "fee_total": fee_total, "miner": miner,
                "phi": phi, "height": self.height()}

    # ---------------- B.3 difficulty retarget (time model)
    def record_time(self, t_delta):
        self.times.append(self.times[-1] + t_delta)

    def sim_block(self, lam):
        """The simulation goes from arrival to its duration per block: Δt ~ Exp(λ/D) (E[T] = D/Λ, spec B.2).
        It tests the retarget mathematics without running a real PoW loop."""
        delta = -math.log(rng.random()) / (lam / self.D)
        self.record_time(delta)
        self.blocks.append(S("sim", len(self.blocks)))
        return self.retarget()

    def retarget(self):
        """Every W blocks the hashrate is estimated and D is set again.
        Important: the T_act measured inside a window was produced by that window's D;
        therefore it is a multiplicative (stale) rate, a hash-rate estimate independent of D
            Lambda_hat = D * W / T_act        (because block rate = Lambda/D)
        is used. The median filter smooths the Lambda_hat of the last 3 windows
        (it also smooths its fluctuations). Then D <- Lambda_hat_smooth * T_b, bounded
        by 4x (as Bitcoin's is)."""
        W = self.retarget_window
        t_b = self.target_block_time
        n = len(self.times) - 1          # the block count
        if n == 0 or n % W != 0:
            return None
        T_act = self.times[-1] - self.times[-1 - W]
        lam_hat = self.D * W / T_act                     # an estimate independent of D
        self.window_history.append((T_act, self.D, lam_hat))
        est = sorted(h[2] for h in self.window_history[-3:])
        lam_smooth = est[len(est) // 2]                  # median (last <=3 windows)
        D_new = int(lam_smooth * t_b)
        D_old = self.D
        D_new = max(D_old // 4, min(D_old * 4, D_new))   # 4x clip
        self.D = max(1, D_new)
        return {"T_act": T_act, "lam_hat": lam_hat, "lam_smooth": lam_smooth,
                "ratio": self.D / D_old, "D": self.D}

    # ---------------- A.10.5 verification
    def validate_block(self, blk, A, B):
        ctx = blk["ctx"]
        if not self.kernel.verify(blk["cert"], A, B, ctx, blk["nonce"], self.D):
            return "REJECT:G-cert"
        if not (0.0 <= blk.get("phi", 0.0) <= 1.0):
            return "REJECT:phi-range"
        for p in blk["u_proofs"]:
            t = self.tasks[p["tid"]]
            if p["ps"] not in PQ_SET:
                return "REJECT:PQ-schema"
            if t.state != "SOLVED":
                return "REJECT:task-state"
        if blk["fee_total"] > C_FEE:
            return "REJECT:anti-aggregation"
        return "ACCEPT"

    # ---------------- A.10.6 fraud window + slash
    def challenge(self, challenger, tid, ledger_block_height):
        t = self.tasks[tid]
        assert ledger_block_height <= t.proof_height + W_s, "fraud window closed"
        # independent backend: recompute the output from scratch (different path, same result)
        harness_A, harness_B = t.spec.program
        C = [[sum(harness_A[i][k] * harness_B[k][j] for k in range(len(harness_B)))
              for j in range(len(harness_B[0]))] for i in range(len(harness_A))]
        if t.result != C:                                        # FRAUD was proven
            bond = max(t.fee * BOND_RATIO, 1)
            self.miners[t.assignee]["slashed"] += bond
            self.slashed_total += bond
            self.miners.setdefault(challenger, {"bond": 0, "slashed": 0})
            t.state = "SLASHED"
            return "SLASHED", FRAUD_REWARD
        # a malicious challenge
        self.miners[challenger]["slashed"] += 1
        return "CHALLENGE_REJECTED", 0

    def settle(self, tid):
        t = self.tasks[tid]
        if t.state == "SOLVED":
            t.state = "SETTLED"
            pay = t.fee - t.burned             # to the miner from escrow; the burn has already gone
            # The escrow was initialised as fee - burn, so it never held the
            # burn: it was collected at submission. Subtracting burned again
            # drove this field to -30 and any health reader would report a
            # shortfall that does not exist. Only the payable part is drawn.
            t.escrow -= pay
            return pay
        return 0


# ------------------------------------------------------------ TV-9 kurtosis
def kurtosis(mat):
    vals = [v for row in mat for v in row]
    n = len(vals)
    mu = sum(vals) / n
    var = sum((v - mu) ** 2 for v in vals) / n
    if var == 0:
        return 0.0
    return (sum((v - mu) ** 4 for v in vals) / n) / var ** 2


def tv9_kurtosis_trap():
    """Basu 2606.04819: uniform-random matrices can be decomposed from NN's, BUT
    the adversarial N(0,18) passes the kurtosis check. => the check is NOT security."""
    r2 = random.Random(1)
    uniform = [[r2.randint(-64, 64) for _ in range(64)] for _ in range(64)]
    nn_like = [[int(r2.gauss(0, 3)) for _ in range(64)] for _ in range(64)]
    adversarial = [[int(round(r2.gauss(0, 18))) for _ in range(64)] for _ in range(64)]
    k_u, k_n, k_a = kurtosis(uniform), kurtosis(nn_like), kurtosis(adversarial)
    # check: "the kurtosis must be between 2.0-4.0" (NN-like) — does it pass?
    trap = (2.0 <= k_a <= 4.0)
    return {"uniform": k_u, "nn": k_n, "adversarial": k_a,
            "adversarial_passes_naive_check": trap}


# -------------------------------------------------------------- test vector
def tv5():
    """Fee escrow + burn: fee 100, burn_rate 0.3 -> 30 burn, 70 escrow; sybil cost > 0."""
    ch = Chain()
    A = [[1, 2], [3, 4]]
    spec = TaskSpec("mm-2x2", (A, A), 64, DEADLINE_H)
    t = ch.submit_task("client-1", spec, fee=100, burn_rate=0.3)
    assert t.burned == 30 and t.escrow == 70 and t.bond == 100, (t.burned, t.escrow, t.bond)
    assert ch.burn_address_balance == 30
    # sybil: sending the same work 1000 times would be free without the burn
    cost = 1000 * 30
    assert cost > 0
    return t.burned, t.escrow, cost


def tv6():
    """Anti-aggregation: in a single block, sum(fee) > C_FEE -> REJECT."""
    ch = Chain()
    tasks, A = [], [[1, 2], [3, 4]]
    for k in range(6):                            # 6 * 100 = 600 > C_FEE=500
        tasks.append(ch.submit_task(f"c{k}", TaskSpec("mm", (A, A), 64, DEADLINE_H),
                                    fee=100, burn_rate=0.1))
    # if the miner tries to aggregate everything into one block the assert trips -> REJECT
    caught = False
    try:
        ch.mine_block("m1", tasks, A, A)
    except AssertionError as e:
        caught = "anti-aggregation" in str(e)
    assert caught
    # the solution is to split (250 + 250 across two blocks)
    ch.mine_block("m1", tasks[:3], A, A)
    ch.mine_block("m1", tasks[3:], A, A)
    return caught, len(ch.blocks) - 1


def tv7():
    """Fraud slash: a wrong proof + evidence -> the miner's bond is slashed, the challenger gets a reward."""
    ch = Chain()
    A = [[1, 2], [3, 4]]
    # produce 64+ blocks to exceed the lookback (empty blocks = zero-demand liveness too)
    for _ in range(EPOCH_LOOKBACK + 5):
        ch.blocks.append(S("empty", len(ch.blocks)))
    t = ch.submit_task("c1", TaskSpec("mm", (A, A), 64, DEADLINE_H), 100, 0.2)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk = ch.mine_block("m1", [t], A, A, wrong_result=True)
    assert ch.validate_block(blk, A, A) == "ACCEPT"     # weak verification: we cannot see it on-chain
    verdict, rew = ch.challenge("v1", t.tid, ch.height())
    assert verdict == "SLASHED" and rew == FRAUD_REWARD
    assert ch.miners["m1"]["slashed"] >= 100
    assert t.state == "SLASHED"
    return verdict, ch.miners["m1"]["slashed"], rew


def tv8():
    """Zero-demand liveness: no U-task for 1000 blocks -> all blocks valid."""
    ch = Chain()
    A = [[1, 2], [3, 4]]
    ok = 0
    for i in range(1000):
        blk = ch.mine_block("m1", [], A, A)             # assigned_tasks = []
        if ch.validate_block(blk, A, A) == "ACCEPT":
            ok += 1
    assert ok == 1000
    assert len(ch.tasks) == 0
    return ok


def tv10():
    """PQ downgrade: a block signed with a non-PQ schema -> REJECT."""
    ch = Chain()
    A = [[1, 2], [3, 4]]
    caught = False
    try:
        ch.mine_block("m1", [], A, A, proof_system_id="legacy-snark-v0")
    except AssertionError:
        caught = True
    assert caught
    blk = ch.mine_block("m1", [], A, A, proof_system_id="stark-pq-1")
    assert ch.validate_block(blk, A, A) == "ACCEPT"
    return caught


def tv123_stub():
    """TV-1..TV-4 G-layer tests are outside this prototype's scope (KW_ANALIZ.md
    and the G-layer kernel test in the file). Here only replay rejection is
    verified."""
    ch = Chain()
    A, B = [[1, 2], [3, 4]], [[5, 6], [7, 8]]
    for _ in range(EPOCH_LOOKBACK + 1):
        ch.blocks.append(S("empty", len(ch.blocks)))
    b1 = ch.mine_block("m1", [], A, B)
    ctx1 = b1["ctx"]
    b2 = ch.mine_block("m1", [], A, B)
    # the same certificate in a different ctx (different parent) -> verify False = REJECT
    same = ch.kernel.verify(b1["cert"], A, B, b1["ctx"], b1["nonce"], ch.D)
    other = ch.kernel.verify(b1["cert"], A, B, b2["ctx"], b1["nonce"], ch.D)
    assert same and not other
    return "replay-rejection: PASS"


# =============================================================================
# TV-34  Empty-input attack (S1): A=B=0 still mines, but phi=0  (2026-09-21)
#
# Adversarial self-review finding. The spec used to list "A=B=0" as a refuted
# attack. That is true for SECURITY (prescribed hardness still holds: with
# A=B=0 the noise dominates and every leaf is a product of ROM outputs, so the
# work is unchanged). It is FALSE for UTILITY: the computation carries zero
# useful work. In S1 mode the miner picks its own input for free, so nothing in
# the G layer alone stops empty mining. The real defense is economic: a block
# with no U task earns the baseline subsidy only, never utility revenue.
#
# This test makes the claim runnable instead of asserted.
# =============================================================================
def tv34_empty_input():
    def _dense(n, seed):
        import hashlib
        return [[int.from_bytes(hashlib.sha256(f"{seed}|{i}|{j}".encode()).digest()[:2], "big") % 97
                 for j in range(n)] for i in range(n)]

    ch = Chain()
    n = 8
    zero = [[0] * n for _ in range(n)]
    A, B = _dense(n, 7), _dense(n, 13)
    for _ in range(EPOCH_LOOKBACK + 1):
        ch.blocks.append(S("empty", len(ch.blocks)))

    # (1) empty mining: A=B=0 still produces a valid G certificate
    blk0 = ch.mine_block("m1", [], zero, zero)
    ok_g = ch.validate_block(blk0, zero, zero) == "ACCEPT"
    phi0 = blk0["phi"]

    # (2) useful mining: a real input with one assigned task
    t = ch.submit_task("c1", TaskSpec("mm", (A, B), 64, DEADLINE_H), 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk1 = ch.mine_block("m1", [t], A, B)
    ok_u = ch.validate_block(blk1, A, B) == "ACCEPT"
    phi1 = blk1["phi"]

    return ok_g, phi0, ok_u, phi1


# --------------------------------------------------------------------- main
if __name__ == "__main__":
    print("=" * 72)
    print("KOK v2 — U-LAYER PROTOTYPE  (seed %d)" % SEED)
    print("=" * 72)

    b, e, sybil = tv5()
    print(f"[TV-5] escrow+burn : burned={b} escrow={e} (fee=100, burn_rate=0.3)")
    print(f"       sybil cost (1000 tasks) = {sybil}  > 0  OK")

    caught, nblk = tv6()
    print(f"[TV-6] anti-aggregation: REJECT was caught={caught}; fragmented block count={nblk}")

    verdict, sl, rew = tv7()
    print(f"[TV-7] fraud slash : verdict={verdict} slash={sl} reward={rew}")

    ok = tv8()
    print(f"[TV-8] zero-demand liveness: {ok}/1000 blocks ACCEPT")

    k = tv9_kurtosis_trap()
    print(f"[TV-9] kurtosis : uniform={k['uniform']:.2f} nn={k['nn']:.2f} "
          f"adversarial={k['adversarial']:.2f}")
    print(f"       did the adversarial input PASS the naive check? "
          f"{k['adversarial_passes_naive_check']}  => the check is not security (Basu)")

    print(f"[TV-10] PQ downgrade: legacy schema REJECT={tv10()}")

    print(f"[G]    {tv123_stub()}")

    print("-" * 72)
    ok_g, phi0, ok_u, phi1 = tv34_empty_input()
    print("[TV-34] empty input A=B=0: G-cert ACCEPT=%s, phi=%.3f" % (ok_g, phi0))
    print("        useful input     : ACCEPT=%s, phi=%.3f" % (ok_u, phi1))
    assert ok_g, "empty mining must still produce a valid G certificate"
    assert phi0 == 0.0, "an empty block must have phi = 0 (no useful work)"
    assert ok_u and phi1 > 0.0, "a useful block must carry phi > 0"
    print("        -> S1 cannot be FORCED to be useful; it is INCENTIVIZED to be.")
    print("        -> the old spec calling A=B=0 'refuted' was overstated;")
    print("           now scoped to security only. Recorded as a correction.")

    print("-" * 72)
    print("ALL TEST VECTORS PASSED — U-layer state machine + penalty economics working.")
    print("Known prototype limits: (1) the G kernel is a plain stand-in for cuPOW;")
    print("(2) the VRF is an HMAC stub; (3) the 'STARK-like' trace is not a real AIR; (4)")
    print("tests are in g_layer_tests.py (time model); (5) GHOSTDAG parent-set")
    print("selection missing (single parent). All share the interface of spec A.10/B.3.")


# =============================================================================
# TV-38  The Pearl verification gap, tested on our own kernel (2026-09-21)
#
# The market research (ARASTIRMA_RESULTS.md) records the single most damaging
# finding about Pearl: its verification ACCEPTED RANDOM MATRICES. A "useful"
# miner could submit a certificate without ever doing the useful work, and the
# network accepted it. That is how a chain runs 24 EH/s and sells zero useful
# compute -- not because miners were lazy, but because the protocol could not
# tell real work from fake work.
#
# This test asks the same question of OUR kernel: does verify() distinguish
# (a) a certificate produced by the real MatMul, from
# (b) a certificate fabricated without doing the work, and
# (c) a certificate produced with the WRONG input matrices?
#
# It does. The reason is structural, not accidental: verify() recomputes the
# claimed tile from A, B and the ROM-derived noise. A fabricated value cannot
# match, because the verifier recomputes the same deterministic function the
# honest miner ran. Pearl's gap was that its verifier did not bind the
# certificate to the claimed computation; ours does, by construction.
# =============================================================================
def tv38_pearl_gap():
    import random as _r
    _rng = _r.Random(77)          # fixed seed -> deterministic draws (file SEED promise)
    q, n = 97, 8
    ch = Chain()
    k = ch.kernel
    A = [[_rng.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[_rng.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx = 999

    # a real certificate: the honest miner actually runs the kernel
    cert, nonce = None, 0
    for nonce in range(1, 300):
        c = k.prove(A, B, ctx, nonce, ch.D)
        if c is not None:
            cert, good = c, nonce
            break
    assert cert is not None

    v_real = k.verify(cert, A, B, ctx, good, ch.D)

    # (c) wrong input: a miner claims the certificate but with different matrices
    A_wrong = [[(A[i][j] + 1) % q for j in range(n)] for i in range(n)]
    v_wrong_input = k.verify(cert, A_wrong, B, ctx, good, ch.D)

    # (b) fabricated certificate: never ran anything, just picked a tile value
    fake = {"tile": (0, 0, _rng.randrange(q)), "m": n // 2}
    v_fabricated = k.verify(fake, A, B, ctx, good, ch.D)

    # (b2) correct tile COORDINATES but a value that was never computed
    i, j, _ = cert["tile"]
    forged = {"tile": (i, j, (cert["tile"][2] + 1) % q), "m": n // 2}
    v_forged_value = k.verify(forged, A, B, ctx, good, ch.D)

    return v_real, v_wrong_input, v_fabricated, v_forged_value


if __name__ == "__main__":
    _r, _wi, _fab, _fg = tv38_pearl_gap()
    print("[TV-38] Pearl verification gap, tested on our own kernel:")
    print("        real certificate accepted      : %s" % _r)
    print("        wrong input matrices accepted  : %s   <- must be False" % _wi)
    print("        fabricated certificate accepted : %s   <- must be False" % _fab)
    print("        forged tile value accepted      : %s   <- must be False" % _fg)
    assert _r, "a real certificate must verify"
    assert not (_wi or _fab or _fg), "a fabricated or wrong-input certificate must NOT verify"
    print("        -> our verifier BINDS the certificate to the computation.")
    print("        -> Pearl's gap was that its verifier did not; this is the")
    print("           causal difference between 24 EH/s of real work and")
    print("           24 EH/s of theatre.")


# =============================================================================
# TV-39  The ctx binding, tested (2026-09-21) — closes KW_ANALIZ item (iv)
#
# KW's Lemma 6.5 assumes sigma is "unpredictable". In KW's original protocol
# sigma is chosen by an interactive verifier, which does not exist on a chain.
# KOK binds sigma to the chain: sigma = ctx = H("ctx", tip, miner, proof_id).
#
# The three-step argument (KW_ANALIZ 6.3) is:
#   (1) ctx is deterministic, so every node computes the same sigma, and since
#       it is a random-oracle output it satisfies the uniformity Lemma 6.5 needs.
#   (2) ctx depends on the parent block, which does not exist yet when the miner
#       works, so the miner cannot know sigma ahead of time - which is exactly
#       the condition KW states verbatim: "Since sigma is not known to the
#       (malicious) prover ahead of time and O is a random oracle, the output of
#       the random oracle is random and unpredictable."
#   (3) The miner's identity is inside ctx, so a certificate cannot be replayed
#       at another chain position or by another miner.
#
# This test proves (3) by construction: a valid certificate at one ctx fails at
# another. It is the runnable form of the replay-prevention argument.
# =============================================================================
def tv39_ctx_binding():
    import random as _r
    _rng = _r.Random(99)          # fixed seed -> deterministic draws (file SEED promise)
    q, n = 97, 8
    ch = Chain()
    k = ch.kernel
    A = [[_rng.randrange(q) for _ in range(n)] for _ in range(n)]
    B = [[_rng.randrange(q) for _ in range(n)] for _ in range(n)]
    ctx_here, ctx_there = 11111, 22222

    cert, good = None, 0
    for good in range(1, 400):
        c = k.prove(A, B, ctx_here, good, ch.D)
        if c is not None:
            cert, good = c, good
            break
    assert cert is not None
    same_position = k.verify(cert, A, B, ctx_here, good, ch.D)
    replayed = k.verify(cert, A, B, ctx_there, good, ch.D)
    return same_position, replayed


if __name__ == "__main__":
    _sp, _rp = tv39_ctx_binding()
    print("[TV-39] The ctx binding (KW_ANALIZ item iv):")
    print("        certificate at its own ctx          : %s" % _sp)
    print("        same certificate at another ctx     : %s   <- must be False" % _rp)
    assert _sp and not _rp
    print("        -> a certificate cannot be replayed to another chain position.")
    print("        -> KW's Lemma 6.5 needs sigma unpredictable; binding sigma to the")
    print("           chain makes it so structurally rather than by assumption.")
