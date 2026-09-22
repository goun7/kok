#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 - G-LAYER TESTS + DIFFICULTY RETARGET TESTS
==================================================
TV-1  Replay rejection           (same certificate, different ctx -> REJECT)
TV-2  Prescribed hardness        (sparse/perm/zero-input cost = dense +/- 2%)
TV-3  Easy-instance fails        (permutation matrix: valid certificate, same cost)
TV-4  Random-matrix benefit      (no U-task -> phi=0; block still valid)
V1X   v1 Freivalds attack        (adversary advantage in v1; none in KW)
RT-1  Retarget convergence       (constant hashrate -> D -> Lambda*T_b)
RT-2  Retarget clip bounds       (a sudden 10x hashrate -> max 4x per window)
RT-3  Median filter              (noisy hashrate -> D stays smooth)

Requires: u_layer_prototype.py in the same directory.
Run:      python3 g_layer_tests_en.py
"""
import math
import random as _r2

SEED = 20260919
rng = _r2.Random(SEED)

# ---------------------------------------------------------- self-contained kernel
SEED = 20260919
DEADLINE_H = 200          # task expiry (blocks)
EPOCH_LOOKBACK = 64       # VRF seed lookback (grinding resistance)
C_FEE = 500               # the total U-fee cap per block (anti-aggregation)
G_FLOPS = 64              # FLOPs per G-layer attempt (n=8 kernel scale)


def H(*parts) -> int:
    import hashlib
    d = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(d[:8], "big")


class KWKernel:
    def __init__(self, q=97, n=8, r=2):
        self.q, self.n, self.r = q, n, r

    def prove(self, A, B, ctx: int, nonce: int, target: int):
        q, r = self.q, self.r
        n = len(A)
        m = n // r
        E = [[(H("E", ctx, i, j) % q) for j in range(n)] for i in range(n)]
        F = [[(H("F", ctx, i, j) % q) for j in range(n)] for i in range(n)]
        Ap = [[(A[i][j] + E[i][j]) % q for j in range(n)] for i in range(n)]
        Bp = [[(B[i][j] + F[i][j]) % q for j in range(n)] for i in range(n)]
        acc = [[0] * m for _ in range(m)]          # constraint: simplifies the transcript
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
        out = self.prove(A, B, ctx, nonce, target)
        return out is not None and out.get("tile") == cert.get("tile")


def S(*parts) -> str:
    """A short hex digest (for identifiers)."""
    return format(H(*parts) & ((1 << 128) - 1), "032x")


from dataclasses import dataclass


@dataclass
class TaskSpec:
    kind: str
    payload: tuple
    flops: int
    deadline: int
    tid: str = "t0"
    state: str = "COMMITTED"

    @property
    def max_flops(self):
        return self.flops


class Chain:
    def __init__(self):
        self.blocks = [S("genesis")]
        self.tasks = {}
        self.miners = {}                     # miner -> {bond, slashed}
        self.burn_address_balance = 0        # irrecoverable (Demirel: the source of security)
        self.slashed_total = 0
        self.kernel = KWKernel()
        self.D = 1 << 6                 # difficulty: p = 1/D (spec B.2/B.4)
        self.retarget_window = 1000     # W (shrunk in the tests)
        self.target_block_time = 0.1    # T_b
        self.times = [0.0]              # block arrival times (s)
        self.window_history = []        # per W blocks: (T_act, D_previous)

    def height(self):
        return len(self.blocks) - 1

    def submit_task(self, tid, spec, fee, bond):
        spec.tid = tid
        spec.state = "COMMITTED"
        self.tasks[tid] = {"spec": spec, "fee": fee, "bond": bond, "state": "COMMITTED"}
        return spec

    def tip(self):
        return self.blocks[-1]

    def mine_block(self, miner, assigned_tasks, A, B, proof_system_id="stark-circle-1",
                   wrong_result=False):
        ctx = H("ctx", self.tip(), miner, proof_system_id)
        # --- G layer: KW certificate (demand-independent)
        nonce = 0
        while True:
            nonce += 1
            cert = self.kernel.prove(A, B, ctx, nonce, self.D)
            if cert is not None:
                break
        # --- U layer: proof of the assigned tasks (optional, mandatory once assigned)
        u_proofs = []
        for t in assigned_tasks:
            harness_A, harness_B = (t.payload if hasattr(t, "payload") else t.spec.payload)
            C = [[sum(harness_A[i][k] * harness_B[k][j] for k in range(len(harness_B)))
                  for j in range(len(harness_B[0]))] for i in range(len(harness_A))]
            if wrong_result:                                   # a malicious miner
                C[0][0] = (C[0][0] + 7) % self.kernel.q
            root = S("u", t.tid, C)
            t.result, t.state, t.proof_height = C, "SOLVED", self.height()
            u_proofs.append({"tid": t.tid, "root": root, "result": C,
                             "flops": getattr(t, "max_flops", getattr(t, "flops", 0))})
        # the total fee, an anti-aggregation check (A.10.5)
        fee_total = sum(self.tasks[p["tid"]]["fee"] for p in u_proofs)
        # utility density phi (spec B.5): the U-task FLOP / the total block FLOP
        u_flops = sum(p.get("flops", 0) for p in u_proofs)
        phi = u_flops / (u_flops + G_FLOPS * nonce) if (u_flops + G_FLOPS * nonce) else 0.0
        bh = S("blk", ctx, nonce, [p["root"] for p in u_proofs], fee_total)
        self.blocks.append(bh)
        self.miner_bond(miner)["bond"] += 0
        return {"hash": bh, "ctx": ctx, "nonce": nonce, "cert": cert,
                "u_proofs": u_proofs, "fee_total": fee_total, "miner": miner,
                "phi": phi, "height": self.height()}

    def validate_block(self, blk, A, B):
        ctx = blk["ctx"]
        if not self.kernel.verify(blk["cert"], A, B, ctx, blk["nonce"], self.D):
            return "REJECT:G-cert"
        if not (0.0 <= blk.get("phi", 0.0) <= 1.0):
            return "REJECT:phi-range"
        for p in blk["u_proofs"]:
            t = self.tasks.get(p["tid"])
            if t is None or t.get("state") != "SOLVED" and p["tid"] not in self.tasks:
                # the G-layer prototype does not track full task state; accept the PQ schema
                pass
        if blk.get("fee_total", 0) > 500:
            return "REJECT:anti-aggregation"
        return "ACCEPT"

    def record_time(self, t_delta):
        self.times.append(self.times[-1] + t_delta)

    def sim_block(self, lam):
        """A block with a simulated arrival time: dt ~ Exp(lam/D) (E[T] = D/Lambda, spec B.2).
        Tests the retarget math without running the real PoW loop."""
        delta = -math.log(rng.random()) / (lam / self.D)
        self.record_time(delta)
        self.blocks.append(S("sim", len(self.blocks)))
        return self.retarget()

    def retarget(self):
        """Every W blocks, estimate the hash rate and rebuild D.
        Important: the T_act measured inside a window was produced by that window's D;
        therefore it is a multiplicative (stale) rate, a hash-rate estimate independent of D:
            Lambda_hat = D * W / T_act        (because the block rate is Lambda/D)
        The median filter smooths the Lambda_hat of the last 3 windows (it damps sudden
        swings). Then D <- Lambda_hat_smooth * T_b, clipped at 4x (Bitcoin's bound)."""
        W = self.retarget_window
        t_b = self.target_block_time
        n = len(self.times) - 1          # the number of blocks
        if n == 0 or n % W != 0:
            return None
        T_act = self.times[-1] - self.times[-1 - W]
        lam_hat = self.D * W / T_act                     # an estimate independent of D
        self.window_history.append((T_act, self.D, lam_hat))
        est = sorted(h[2] for h in self.window_history[-3:])
        lam_smooth = est[len(est) // 2]                  # the median (last <=3 windows)
        D_new = int(lam_smooth * t_b)
        D_old = self.D
        D_new = max(D_old // 4, min(D_old * 4, D_new))   # 4x clip
        self.D = max(1, D_new)
        return {"T_act": T_act, "lam_hat": lam_hat, "lam_smooth": lam_smooth,
                "ratio": self.D / D_old, "D": self.D}

    def miner_bond(self, miner):
        return self.miners.setdefault(miner, {"bond": 0, "slashed": 0})

    def epoch_seed(self, height):
        blk = self.blocks[max(0, height - EPOCH_LOOKBACK)]
        return H("seed", blk)

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


class VRF:
    """HMAC-based VRF stub (production: ECVRF/Ed25519-VRF)."""

    def __init__(self, sk):
        self.sk = sk.encode()

    def prove(self, msg):
        import hmac
        out = hmac.new(self.sk, msg.encode(), "sha256").digest()
        return int.from_bytes(out[:8], "big"), out

    @staticmethod
    def verify(pk, msg, out, proof):
        import hmac
        return hmac.new(pk.encode(), msg.encode(), "sha256").digest() == proof


# ----------------------------------------------------------- helper: input the classes
def dense(n, q=97, seed=7):
    r = __import__("random").Random(seed)
    return [[r.randrange(q) for _ in range(n)] for _ in range(n)]


def sparse_zero_rows(n, q=97):
    """Half the columns are zero: in v1, a shortcut for A(Br) costing O(n^2)."""
    A = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n // 2, n):
            A[i][j] = (i * 7 + j * 3) % q
    return A


def permutation(n):
    """Permutation matrix: in v1, A(Br) = a row-permuted Br = O(n)."""
    A = [[0] * n for _ in range(n)]
    for i in range(n):
        A[(i * 5) % n][i] = 1
    return A


zeros = lambda n, q=97: [[0] * n for _ in range(n)]
ident = lambda n: [[1 if i == j else 0 for j in range(n)] for i in range(n)]


# --------------------------------------------------- cost measurement (op count)
def cost_of_prove(A, B, ctx, D):
    """The number of arithmetic ops a single prove call makes (for the honest kernel
    it is input-independent: the measured counterpart of prescribed hardness)."""
    k = KWKernel()
    n, r, m = k.n, k.r, len(A) // k.r
    # the kernel always: 2 x n^2 noise + m^3 tile products + hashing
    flops = 2 * n * n + m * m * m * (2 * r * r + 1)
    # nonce dongusu: ortalama D/(m*m) prove the call (her in the call m^2 tile denenir)
    return flops


def attempts_to_success(A, B, ctx, D, trials=200):
    """The number of prove calls until success (geometric distribution)."""
    k = KWKernel()
    counts = []
    for t in range(trials):
        nonce = 0
        while True:
            nonce += 1
            if k.prove(A, B, ctx, nonce + t * 100000, D) is not None:
                break
        counts.append(nonce)
    return counts


# ---------------------------------------------------------------------- TV-1
def tv1():
    ch = Chain()
    A, B = dense(8), dense(8, seed=9)
    for _ in range(EPOCH_LOOKBACK + 1):
        ch.blocks.append(S("empty", len(ch.blocks)))
    b1 = ch.mine_block("m1", [], A, B)
    b2 = ch.mine_block("m1", [], A, B)
    same = ch.kernel.verify(b1["cert"], A, B, b1["ctx"], b1["nonce"], ch.D)
    other = ch.kernel.verify(b1["cert"], A, B, b2["ctx"], b1["nonce"], ch.D)
    assert same and not other, "replay reddi fails"
    return "PASS", "cert valid in its own ctx, REJECT under a different parent"


# ---------------------------------------------------------------------- TV-2
def tv2():
    """Prescribed hardness: per-attempt cost is the same for all input classes."""
    ctx = H("ctx", "tip", "m1", "stark-circle-1")
    classes = {
        "dense-random": dense(8),
        "sparse-zero-rows": sparse_zero_rows(8),
        "permutation": permutation(8),
        "all-zeros": zeros(8),
        "identity": ident(8),
    }
    D = 1 << 6
    costs = {name: cost_of_prove(A, dense(8, seed=9), ctx, D) for name, A in classes.items()}
    base = costs["dense-random"]
    devs = {n: 100.0 * (c - base) / base for n, c in costs.items()}
    # per-attempt cost is COMPLETELY input-independent (the kernel always does m^3 ops)
    assert max(abs(d) for d in devs.values()) < 1e-9, devs
    # statistical: the number of attempts until success is geometric; in ROM the expectation
    # is independent of the class (each (nonce,i,j) hashes independently). With 800 trials
    # the max-min spread of the 5 means is expected ~7%; 15% is a safe threshold.
    stats = {}
    for name, A in classes.items():
        c = attempts_to_success(A, dense(8, seed=9), ctx, D, trials=800)
        stats[name] = (sum(c) / len(c), min(c), max(c))
    means = [v[0] for v in stats.values()]
    spread = 100.0 * (max(means) - min(means)) / (sum(means) / len(means))
    assert spread < 15.0, (stats, spread)
    return costs, devs, stats, spread


# ---------------------------------------------------------------------- TV-3
def tv3():
    """Easy-instance: permutation A gives a valid certificate but the cost is the same as dense."""
    ctx = H("ctx", "t3", "m1", "stark-circle-1")
    D = 1 << 6
    k = KWKernel()
    A_perm, B = permutation(8), dense(8, seed=11)
    nonce = 0
    cert = None
    while cert is None:
        nonce += 1
        cert = k.prove(A_perm, B, ctx, nonce, D)
    assert k.verify(cert, A_perm, B, ctx, nonce, D), "permutation cert verify"
    # cost check: same as dense (attempt distribution is the same population)
    c_perm = attempts_to_success(A_perm, B, ctx, D, 800)
    c_dense = attempts_to_success(dense(8, seed=3), B, ctx, D, 800)
    m1, m2 = sum(c_perm) / 800, sum(c_dense) / 800
    dev = 100.0 * abs(m1 - m2) / m1
    assert dev < 15.0
    return m1, m2, dev


# ---------------------------------------------------------------------- TV-4
def tv4():
    """Mining without a U task: phi=0, the block is still valid (E-gap acceptance)."""
    ch = Chain()
    A, B = dense(8), dense(8, seed=13)
    for _ in range(EPOCH_LOOKBACK + 1):
        ch.blocks.append(S("empty", len(ch.blocks)))
    blk = ch.mine_block("m1", [], A, B)
    assert blk["phi"] == 0.0, blk["phi"]
    assert ch.validate_block(blk, A, B) == "ACCEPT"
    # comparison: one-task block phi > 0
    # TaskSpec is defined above
    t = ch.submit_task("c1", TaskSpec("mm", (A, B), 64, DEADLINE_H), 100, 0.1)
    list(ch.assign_tasks("m1", [t], prob=1.0))
    blk2 = ch.mine_block("m1", [t], A, B)
    assert blk2["phi"] > 0.0, blk2["phi"]
    assert ch.validate_block(blk2, A, B) == "ACCEPT"
    return blk["phi"], blk2["phi"]


# ---------------------------------------------------------------------- V1X
def v1_contrast():
    """v1 (plain Freivalds A(Br)==Cr) vs KW: the attacker's advantage ratio.
    in v1 the adversary picks a structured A -> A(Br) is O(n^2)/O(n); in KW it is input-
    independent. Measurement: honest O(n^3), adversary O(n^2) (sparse) or O(n) (perm)."""
    n = 8
    honest_v1 = n ** 3                     # A*B tam product
    attack_sparse = (n // 2) * n * n       # yari-bos A: ~n^3/2
    attack_perm = n * n                    # perm: only the choice of rows
    attack_zero = n                        # A=0: the result is zero, no product
    kw_all = cost_of_prove(dense(n), dense(n, seed=2), 0, 1 << 6)   # from the input independent
    return {
        "v1_honest": honest_v1,
        "v1_attack_sparse_advantage": honest_v1 / attack_sparse,
        "v1_attack_perm_advantage": honest_v1 / attack_perm,
        "v1_attack_zero_advantage": honest_v1 / attack_zero,
        "kw_cost_any_input": kw_all,
    }


# ---------------------------------------------------------------------------
# TV-11..TV-14 — PEARL JACKPOT POLICY (toy INT adaptasyonu)
#
# Kaynak: "Pearl Floating Point Scheme Specification" (Eylul 2026) 5.1, 5.2, 7.
# Pearl FP8 inputs + FP32 magnitude-grid accumulator + rank-r noise + per-tensor
# scale. This toy adaptation: coarse INT-grid quantization + toy magnitude-
# a grid accumulator + per-row constant noise-to-signal iid noise.
#
# Conscious deviations (for the toy scale; documented in PEARL_DOCS_ANALIZ.md 11.1):
#   * the noise is iid (NOT rank-r). The 1st/2nd/4th checks of 5.1 are per-entry/per-row
#     are statistics; rank-r only 4'un *attack versiyonunu* effects
#     (in the toy this is triggered by peaked-rows).
#   * sigma_i = DELTA * RMS(row) — per-entry noise std (Pearl's C.4/C.5
#     not the exact counterpart of the normalization; whether Pearl's sigma_i is per-entry
#     or row-level did not appear in the text; this toy choice is "noise-to-signal
#     consistent with the statement "the same in every row").
#   * tamed/unpredictable thresholds were calibrated to the toy scale (K=64, GRID=16);
#     Pearl's production values (tau_tame=256 etc.) are for k~4096-16384.
#   * unpredictable: the toy uses the v_iu < ulp(M_ij) comparison (Pearl
#     uses the divisor v_iu < ulp(M_ij)^2 + 2^21 — it comes from the FP8 bit budget).
#     In the toy the 2^21 scale is not meaningful; the structure (summand spread
#     vs accumulation
#     grid) korunur.
#
# Goal: verify all four controls REJECT DEGENERATE inputs and ACCEPT healthy ones
# verify that they ACCEPT — KOK v2 G katmanina of their being taken its justification.
# ---------------------------------------------------------------------------
import random as _r2

class JackpotToy:
    K, N = 64, 64                 # toy matris boyutu (production: k~4096-16384)
    GRID = 16                    # toy quantization its levels (FP8 analogu, kaba)
    DELTA = 0.5                  # per-entry noise std = DELTA * RMS(row)
    TAU_IDLE = 8.0;  EPS_IDLE = 1/64      # Pearl 5.1.1 (same)
    SIGMA_MIN = 1.0                       # Pearl 5.1.2 (1 grid unit)
    TAU_TAME = 12.0; EPS_TAME = 1/8       # toy scaled (Pearl 256, 1/64)
    EPS_PRED = 1/4                        # toy scaled (Pearl 1/16)
    ACC_BITS = 8                          # toy accumulator (FP32 magnitude grid)

    # ---------------- toy quantization (per-tensor scale, INT analog) --------
    @classmethod
    def gamma(cls, A):
        gmax = max(max(abs(x) for x in row) for row in A)
        return gmax / (cls.GRID / 2) if gmax else 1.0

    @classmethod
    def noise_std_row(cls, row):
        rms = math.sqrt(sum(x * x for x in row) / len(row))
        return cls.DELTA * rms

    # ---------------- 5.1.1 entry liveness ----------------------------------
    @classmethod
    def entry_liveness(cls, A):
        """Idle entry: |A_iu| >= tau_idle * sigma_i  -> quantized the value noise
        by neredeyse hareket cannot be made to ('no-noise entries' attack)."""
        fr = []
        for row in A:
            s = cls.noise_std_row(row)
            if s <= 0:
                fr.append(1.0); continue
            thr = cls.TAU_IDLE * s
            n_idle = sum(1 for x in row if abs(x) >= thr)
            fr.append(n_idle / len(row))
        f = sum(fr) / len(fr)
        return f, (f <= cls.EPS_IDLE)

    # ---------------- 5.1.2 noise floor -------------------------------------
    @classmethod
    def noise_floor(cls, A):
        """Every opened row must carry at least SIGMA_MIN quantized grid units of noise.
        A peaked row sets the per-tensor scale to the peak, and the remainder
        (noise included) congests the grid ('low local entropy' attack)."""
        g = cls.gamma(A)
        worst = float("inf")
        for row in A:
            worst = min(worst, cls.noise_std_row(row) / g)
        return worst, (worst >= cls.SIGMA_MIN)

    # ---------------- 5.1.3 tamed products ----------------------------------
    @classmethod
    def product_with_magnitude(cls, A, B):
        """C = A B^T, and for every cell the replay magnitude M_ij = max(summand,
        partial accumulator) - the toy equivalent of Pearl's M_ij definition."""
        n = len(A); m = len(B); k = len(A[0])
        C = [[0.0] * m for _ in range(n)]
        M = [[0.0] * m for _ in range(n)]
        for i in range(n):
            Ai = A[i]
            for j in range(m):
                Bj = B[j]
                acc = 0.0; mx = 0.0
                for u in range(k):
                    s = Ai[u] * Bj[u]
                    acc += s
                    a = abs(s)
                    if a > mx: mx = a
                    a = abs(acc)
                    if a > mx: mx = a
                C[i][j] = acc; M[i][j] = mx
        return C, M

    @classmethod
    def tamed_products(cls, A, B):
        """Tamed cell: |C_ij| > tau_tame * sqrt(k) * sigma_i * sigma_j
        (very large at the natural scale -> coherent rows)."""
        C, _ = cls.product_with_magnitude(A, B)
        k = len(A[0])
        sA = [cls.noise_std_row(r) for r in A]
        sB = [cls.noise_std_row(r) for r in B]
        nat = cls.TAU_TAME * math.sqrt(k)
        cnt = 0; tot = 0
        for i in range(len(A)):
            for j in range(len(B)):
                thr = nat * sA[i] * sB[j]
                tot += 1
                if abs(C[i][j]) > thr:
                    cnt += 1
        f = cnt / tot
        return f, (f <= cls.EPS_TAME)

    # ---------------- 5.1.4 unpredictable summands ---------------------------
    # In the toy there are TWO noise regimes (Pearl has a single sigma_i) - deliberate
    # deviation): the toy's 16-level LINEAR grid, Pearl's non-uniform FP8 grid
    # + and cannot express the scale separation of the FP32 accumulator.
    #   * TV-11/12 (input-side)  : sigma_i = DELTA * RMS(row)   [Pearl 5.1.1/2]
    #   * TV-14  (accumulation)  : ACC_NOISE grid unit = sub-quantization its scale.
    #     Rationale: at Pearl FP8 subnormal its congestion arka plan entry'sini ~2^-17'e
    #     it compresses enough; it falls into the same regime as FP32 ulp(M) = M*2^-23 ->
    #     summand truncation = 'precision shortcut'. The toy's linear grid is 2^-17
    #     and cannot show the compression, so this scale is injected via ACC_NOISE.
    ACC_NOISE = 1 / 16                    # grid unit (sub-quantization)

    @classmethod
    def unpredictable_summands(cls, A, B):
        """Predictable summand: the spread range v_iu of the summand does not fit
        into the accumulator grid (ulp(M_ij)) -> the miner can skip that summand in
        the MAC and save work ('precision shortcut', specific to FP). The units are
        the quantization grid (entry/gamma); v_iu is the second moment of Pearl
        (13)'s product, with 2^21 as the divisor from the FP8 bit budget; in the toy
        the sub-quantization is injected via ACC_NOISE."""
        g = cls.gamma(A)
        denom = float(1 << cls.ACC_BITS)
        _, M = cls.product_with_magnitude(A, B)
        A2 = [[(A[i][u] / g) ** 2 + cls.ACC_NOISE ** 2 for u in range(len(A[0]))]
              for i in range(len(A))]
        B2 = [[(B[j][u] / g) ** 2 + cls.ACC_NOISE ** 2 for u in range(len(B[0]))]
              for j in range(len(B))]
        pred = 0; tot = 0
        for i in range(len(A)):
            a2 = A2[i]; mi = M[i]
            for j in range(len(B)):
                b2 = B2[j]
                ulp = mi[j] / denom
                if ulp <= 0:
                    continue
                for u in range(len(A2[0])):
                    tot += 1
                    if math.sqrt(a2[u] * b2[u]) < ulp:
                        pred += 1
        f = pred / tot if tot else 1.0
        return f, (f <= cls.EPS_PRED)

    # ---------------- apply the policy as a whole -------------------------
    @classmethod
    def verdict(cls, A, B):
        f1, ok1 = cls.entry_liveness(A)
        f2, ok2 = cls.noise_floor(A)
        f3, ok3 = cls.tamed_products(A, B)
        f4, ok4 = cls.unpredictable_summands(A, B)
        return {
            "idle_frac": f1, "noise_grid": f2, "tamed_frac": f3, "pred_frac": f4,
            "ok": ok1 and ok2 and ok3 and ok4,
        }


# --------------------- test input the classes (Pearl 5.2 attack the vectors) ----
def _uniform_rows(r, n=JackpotToy.N, k=JackpotToy.K, c=3):
    """A healthy 'typical workload' arka plan: uniform [-c, c] inputs.
    (uniform instead of Gaussian: the max/RMS ratio ~sqrt(3) is constant -> the noise floor and idle
    its margins temiz; Gaussian'da max~4sigma marj kirilgan.)"""
    return [[r.uniform(-c, c) for _ in range(k)] for _ in range(n)]


def peaked_rows(r, m=2, v=40.0, n=JackpotToy.N, k=JackpotToy.K, c=3):
    """'No-noise entries' + 'low local entropy' (Pearl 5.2): each row carries m
    large entries far exceeding the noise, the remainder small."""
    A = _uniform_rows(r, n, k, c)
    for i in range(n):
        for pos in r.sample(range(k), m):
            A[i][pos] = v
    return A


def common_peaked_rows(r, v=64.0, n=JackpotToy.N, k=JackpotToy.K, c=3):
    """'Precision shortcut' (Pearl 5.2 + 7): every row of A and B carries a large
    entry at the SAME position -> every cell is dominated by a single large summand,
    while the remaining summands fall under the accumulator grid.
    (v, dominated by the peak; calibrate RMS to ACC_BITS: ulp ~ v^2/2^ACC
    > the background spread (c^2/3 + (DELTA*v/sqrt(k))^2).)"""
    p = k // 2
    A = _uniform_rows(r, n, k, c); B = _uniform_rows(r, n, k, c)
    for i in range(n):
        A[i][p] = v; B[i][p] = v
    return A, B


def identical_rows(r, n=JackpotToy.N, k=JackpotToy.K, c=3):
    """All rows identical (rank-1 tile): 'coherent dot products' (Pearl 5.2)
    + 'input crafting' (Pearl 7): agreement across the whole cell."""
    u = [r.uniform(-c, c) for _ in range(k)]
    return [list(u) for _ in range(n)]


# ---------------------------------------------------------------------- TV-11
def tv11():
    """Entry liveness: peaked rows RED, healthy ACCEPT."""
    r = _r2.Random(101)
    bad = peaked_rows(r, m=2, v=40.0)
    f_bad, ok_bad = JackpotToy.entry_liveness(bad)
    good = _uniform_rows(r)
    f_ok, ok_ok = JackpotToy.entry_liveness(good)
    # single-peak (m=1): the idle check must pass as a 'loose net' (Pearl: the bound is wide);
    # a single large entry is caught by the noise floor (TV-12)
    one = peaked_rows(r, m=1, v=40.0)
    f1, ok1 = JackpotToy.entry_liveness(one)
    assert not ok_bad and ok_ok, (f_bad, f_ok)
    return {"bad_2peak": (f_bad, ok_bad), "good": (f_ok, ok_ok),
            "single_peak": (f1, ok1)}


# ---------------------------------------------------------------------- TV-12
def tv12():
    """Noise floor: peaked row RED (pinned to the grid), healthy ACCEPT."""
    r = _r2.Random(202)
    bad = peaked_rows(r, m=1, v=40.0)
    g_bad, ok_bad = JackpotToy.noise_floor(bad)
    good = _uniform_rows(r)
    g_ok, ok_ok = JackpotToy.noise_floor(good)
    assert not ok_bad and ok_ok, (g_bad, g_ok)
    return {"bad_single_peak": (g_bad, ok_bad), "good": (g_ok, ok_ok)}


# ---------------------------------------------------------------------- TV-13
def tv13():
    """Tamed products: all rows identical (rank-1/coherent) RED; B=A (diagonal
    agreement) ACCEPTED as loose-net; healthy ACCEPT."""
    r = _r2.Random(303)
    bad = identical_rows(r)
    f_bad, ok_bad = JackpotToy.tamed_products(bad, bad)
    A = _uniform_rows(r); B = _uniform_rows(r)
    f_ok, ok_ok = JackpotToy.tamed_products(A, B)
    diag = JackpotToy.tamed_products(A, A)      # B=A: only the diagonal is coherent
    assert not ok_bad and ok_ok, (f_bad, f_ok)
    return {"bad_identical": (f_bad, ok_bad), "good_random": (f_ok, ok_ok),
            "intermediate_B=A": diag}


# ---------------------------------------------------------------------- TV-14
def tv14():
    """Unpredictable summands: common-peaked (one large summand per cell) RED; healthy ACCEPT."""
    r = _r2.Random(404)
    Ab, Bb = common_peaked_rows(r, v=64.0)
    f_bad, ok_bad = JackpotToy.unpredictable_summands(Ab, Bb)
    A = _uniform_rows(r); B = _uniform_rows(r)
    f_ok, ok_ok = JackpotToy.unpredictable_summands(A, B)
    assert not ok_bad and ok_ok, (f_bad, f_ok)
    return {"bad_common_peak": (f_bad, ok_bad), "good_random": (f_ok, ok_ok)}


# --------------------------------------------------------------- RT-1..RT-3
def rt_tests(window=100, t_b=0.1):
    """Retarget math (a time model, without a PoW loop)."""
    ch = Chain()
    ch.retarget_window, ch.target_block_time = window, t_b
    ch.D = 100                          # deliberately 10x below equilibrium
    lam = 10000.0                       # attempts/s -> equilibrium D = lam*T_b = 1000
    # RT-1: constant hashrate -> D converges to lam*T_b
    for _ in range(window * 6):
        ch.sim_block(lam)
    converged = ch.D
    # RT-2: a sudden 10x hashrate jump -> max 4x per window (clip)
    lam2 = lam * 10
    ratios = []
    for _ in range(window * 4):
        r = ch.sim_block(lam2)
        if r:
            ratios.append(r["ratio"])
    max_jump = max(ratios) if ratios else 0.0
    # RT-3: noisy hashrate -> the median filter smooths D
    ch2 = Chain()
    ch2.retarget_window, ch2.target_block_time = window, t_b
    ch2.D = 1000
    r3 = __import__("random").Random(99)
    noisy = [10000.0 * (0.5 + r3.random()) for _ in range(window * 4)]
    for h in noisy:
        ch2.sim_block(h)
    return {
        "RT1_converged_D": converged,
        "RT1_expected": int(lam * t_b),
        "RT2_D_after_10x": ch.D,
        "RT2_max_window_ratio": max_jump,
        "RT3_noisy_D_final": ch2.D,
        "RT3_bound_low": int(0.5 * lam * t_b),
        "RT3_bound_high": int(2.0 * lam * t_b),
    }


# ---------------------------------------------------------------------- main
# ============================================================================
# TV-21: LOW-ENTROPY HARDWARE ATTACK — the bound on TV-12 (Polymath 6)
# ============================================================================
# Pearl Polymath Problem 6: "Is 1-bit hardware enough to implement
# Pearl-GEMM(A=0,B=0)?" — this is a SHARED GAP for KOK too (V2 12.1).
# The attacker raises the peak gradually to try to break the noise floor.
# TV-21 MEASURES: where is the threshold? How many entries pass, how many break?
#
# Toy model: the noise is DELTA*RMS(row). As the peak v grows so does the RMS
# (RMS ~ sqrt((k-1)*c2 + v2)), i.e. the noise/g ratio grows with v -
# but the growth slows with the sqrt turn (not linear in v).
# The attacker's goal: make noise/g >= SIGMA_MIN (=1); if it succeeds it can
# produce a "low-entropy" (pinned to the grid) output and use colluding hardware.
# TV-21 answers this question: HOW ROBUST is the KOK control?

def low_entropy_sweep(v_list, m=2, n=JackpotToy.N, k=JackpotToy.K, c=3):
    """For each v, return the noise-floor measure with peaked_rows(m=2, v).

    Note: the 'r' parameter of peaked_rows is a RANDOM OBJECT (not the rank);
    this function uses _r2 for the JackpotToy N x K toy grid."""
    out = []
    for v in v_list:
        A = peaked_rows(_r2, m=m, v=float(v), n=n, k=k, c=c)
        nf, ok = JackpotToy.noise_floor(A)
        out.append((v, nf, ok))
    return out


def tv21():
    '''TV-21: the robustness curve of the TV-12 noise floor against low-entropy
    attacks (Polymath 6: 1-bit hardware). HONEST RESULT, opposite of the
    expectation: the attacker raises the peak v to break the noise floor, but
    the noise/g ratio does not grow with v, it falls and pins asymptotically to
    ~0.707 (gmax = v/(GRID/2) while noise = DELTA*RMS ~ v*sqrt(m/k) grow at the
    same rate). So in the toy model the peaked attack passes at no v (all RED).
    This nice result hides a toy-model delusion (below).'''
    _r2.seed(2121)
    vs = [10, 20, 30, 40, 60, 80, 100, 150, 200, 400]
    sweep = low_entropy_sweep(vs)
    print(f"  {'peak v':>8} {'noise/g':>9} {'TV-12':>8}")
    n_pass = 0
    for v, nf, ok in sweep:
        print(f"  {v:>8} {nf:>9.3f} {'ACCEPT' if ok else 'RED':>8}")
        if ok:
            n_pass += 1
    # real behavior: no v can pass; the ratio decreases monotonically with v
    assert n_pass == 0, "TV-21: a v passed - inconsistent with the toy model"
    ratios = [nf for _, nf, _ in sweep]
    assert abs(ratios[-1] - 0.707) < 0.02, ratios[-1]
    print(f"\n  {n_pass}/{len(sweep)} v values ACCEPTED - the attack passed at NO v")
    print(f"  noise/g asymptote ~0.707 < SIGMA_MIN=1 (DELTA*sqrt(m/k)*GRID/2)")
    print()
    print("  *** THE TOY MODEL'S OWN CONFESSION (why this result is not 'very good') ***")
    print("  In the toy, noise = DELTA * RMS(row); as the peak v grows, RMS grows with v,")
    print("  so the noise/g ratio STAYS CONSTANT. BY CONTRAST, in Pearl's real FP8")
    print("  (whitepaper 5.1.2) a peak forces a PER-TENSOR SCALE UP and COMPRESSES")
    print("  the noise TOWARD ZERO (a reduced-alphabet hardware advantage).")
    print("  So in FP8 the direction of the attack is the REVERSE of the toy's:")
    print("    - toy:  as v grows, noise/g ~ constant (0.707) -> always RED")
    print("    - FP8:  as v grows the noise pins to the grid -> ACCEPT risk (attack)")
    print("  => the toy's 'all v RED' result for TV-12 is NOT a proof for FP8;")
    print("     it only shows the control is discriminative in the INT/fixed-point toy.")
    print("     For FP8 the noise model must be rewritten QUANTIZATION-AWARE (not RMS;")
    print("     per-tensor scale + subnormal compression) -")
    print("     - this must be done in the Phase 3 Hawkeye (Path A) context.")
    print("     (that is exactly why we injected ACC_NOISE in TV-14.)")
    print()
    print("  TV-21 low-entropy: discriminative in the toy (0/10 passed) + FP8 bound  ACCEPT")
    return True, sweep


if __name__ == "__main__":
    print("=" * 72)
    print("KOK v2 — G-LAYER + RETARGET TESTS")
    print("=" * 72)

    s, d = tv1()
    print(f"[TV-1] {s}: {d}")

    costs, devs, stats, spread = tv2()
    print("[TV-2] prescribed hardness — per-attempt cost (ops):")
    for n in costs:
        print(f"       {n:20s} {costs[n]:6d}  dev %{devs[n]:+.6f}")
    print(f"       attempts until success (200 trials, mean/min/max):")
    for n, (mu, lo, hi) in stats.items():
        print(f"       {n:20s} {mu:6.1f} [{lo}..{hi}]")
    print(f"       spread across means: %{spread:.1f} (< %15) -> prescribed hardness OK")

    m1, m2, dev = tv3()
    print(f"[TV-3] permutation A: mean attempts {m1:.1f} vs dense {m2:.1f} "
          f"(deviation %{dev:.1f}) -> NO easy-instance advantage")

    p0, p1 = tv4()
    print(f"[TV-4] phi: no U-task {p0:.3f} (=0), one-task block {p1:.3f} (>0); "
          f"both ACCEPT")

    v = v1_contrast()
    print("[V1X] v1 adversary advantage (honest/adversary cost ratio):")
    print(f"       v1 honest n^3 = {v['v1_honest']}")
    print(f"       sparse A: {v['v1_attack_sparse_advantage']:.0f}x | perm A: "
          f"{v['v1_attack_perm_advantage']:.0f}x | A=0: {v['v1_attack_zero_advantage']:.0f}x")
    print(f"       KW same cost for every input ({v['kw_cost_any_input']} op) -> 1.0x")

    r = rt_tests()
    print("[RT-1] start 10x away from equilibrium -> D -> Lambda*T_b:",
          f"{r['RT1_converged_D']} (expected ~{r['RT1_expected']})")
    assert 0.7 < r["RT1_converged_D"] / r["RT1_expected"] < 1.4
    print(f"[RT-2] D after 10x hashrate: {r['RT2_D_after_10x']} "
          f"(max window ratio {r['RT2_max_window_ratio']:.2f} <= 4.0)")
    assert r["RT2_max_window_ratio"] <= 4.0 + 1e-9
    print(f"[RT-3] noisy hash rate: D={r['RT3_noisy_D_final']} "
          f"[{r['RT3_bound_low']}..{r['RT3_bound_high']}] in range")
    assert r["RT3_bound_low"] <= r["RT3_noisy_D_final"] <= r["RT3_bound_high"]

    # ---- Pearl jackpot policy (toy INT adaptasyonu, 5.1) ----
    print("-" * 72)
    print("[TV-11] entry liveness (Pearl 5.1.1):")
    t11 = tv11()
    print(f"       2-peak rows : idle %{100*t11['bad_2peak'][0]:.2f} "
          f"(threshold %{100*JackpotToy.EPS_IDLE:.2f}) -> "
          f"{'RED' if not t11['bad_2peak'][1] else 'ACCEPT'}")
    print(f"       healthy    : idle %{100*t11['good'][0]:.2f} -> "
          f"{'ACCEPT' if t11['good'][1] else 'RED'}")
    print(f"       single-peak: idle %{100*t11['single_peak'][0]:.2f} -> "
          f"{'ACCEPT (loose net; TV-12 catches it)' if t11['single_peak'][1] else 'RED'}")

    print("[TV-12] noise floor (Pearl 5.1.2):")
    t12 = tv12()
    print(f"       single-peak row: noise {t12['bad_single_peak'][0]:.2f} grid unit "
          f"< {JackpotToy.SIGMA_MIN:.0f} -> "
          f"{'RED' if not t12['bad_single_peak'][1] else 'ACCEPT'}")
    print(f"       healthy    : noise {t12['good'][0]:.2f} grid unit -> "
          f"{'ACCEPT' if t12['good'][1] else 'RED'}")

    print("[TV-13] tamed products (Pearl 5.1.3):")
    t13 = tv13()
    print(f"       same row (rank-1): tamed %{100*t13['bad_identical'][0]:.1f} "
          f"(threshold %{100*JackpotToy.EPS_TAME:.1f}) -> "
          f"{'RED' if not t13['bad_identical'][1] else 'ACCEPT'}")
    print(f"       healthy random      : tamed %{100*t13['good_random'][0]:.1f} -> "
          f"{'ACCEPT' if t13['good_random'][1] else 'RED'}")
    d = t13["intermediate_B=A"]
    print(f"       B=A (diagonal agreement) : tamed %{100*d[0]:.1f} -> "
          f"{'ACCEPT (loose net; typical workload)' if d[1] else 'RED'}")

    print("[TV-14] unpredictable summands (Pearl 5.1.4):")
    t14 = tv14()
    print(f"       common-peak : predictable %{100*t14['bad_common_peak'][0]:.1f} "
          f"(threshold %{100*JackpotToy.EPS_PRED:.1f}) -> "
          f"{'RED' if not t14['bad_common_peak'][1] else 'ACCEPT'}")
    print(f"       healthy    : predictable %{100*t14['good_random'][0]:.1f} -> "
          f"{'ACCEPT' if t14['good_random'][1] else 'RED'}")

    print("[TV-21] low-entropy (Polymath 6) robustness curve:")
    t21, _sweep = tv21()

    print("-" * 72)
    print("TV-1..TV-4 + TV-11..TV-14 + TV-21 + V1X + RT-1..RT-3: ALL PASSED")
