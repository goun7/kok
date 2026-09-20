# KÖK v2 — Phase 2 Cryptographer Review Brief

**Date:** 20 September 2026 · **Owner:** the KÖK v2 protocol (paper: `KOK_V2_PAPER.md`,
spec: `KOK_V2_TECHNICAL_SPEC.md`) · **Target:** 2 independent human cryptographers

> **Purpose of this brief:** to package the security argument of KÖK v2's Layer G for
> independent cryptographers to audit. Each question is presented with **verbatim
> quotations from the source** and **the preliminary result we (an LLM) reached**. What
> we ask of you is to **verify or refute** the preliminary result. "I agree" is not
> sufficient; you must state **why**.

---

## 0. Background (30 seconds)

KÖK v2 is a two-layer L1:

- **Layer G (security):** a KW/cuPOW MatMul PoUW with memoryless difficulty. **Security is
  independent of demand** — it satisfies Theorem 2 of Demirel (ePrint 2026/1492) at the
  construction level: liveness is preserved with a φ=0 filler (TV-4/TV-8).
- **Layer U (utility):** a fee-paid verifiable-compute market (escrow + bond +
  irrecoverable burn). **It never elects leaders.** The E-gap is architecturally
  separated (see `KOK_V2_PAPER.md`; confirmed by Pearl's own open-problems page, which
  confesses it).

This brief audits **only the cryptography of Layer G**. The game theory of Layer U
(spec §A.4–A.6) and its economics (`pass_sim_en.py`) require a separate review; that
brief lives in Appendix C of `KOK_V2_TECHNICAL_SPEC.md`.

**Why we are approaching you:** our analysis of the KW construction is **an LLM's
reading**. The mandatory gate for Phase 2 is the approval of **two independent human
cryptographers**. The questions below are the key to that gate.

---

## 1. The core under review: the KW construction and its three security legs

**Source:** Komargodski & Weinstein, "Proofs of Useful Work from Arbitrary Matrix
Multiplication", arXiv:2504.09971v4 (13 Nov 2025) = ePrint 2025/685.

```
Encode_r(σ, A, B):  σ ↦ (E_L,E_R,F_L,F_R);  E = E_L·E_R, F = F_L·F_R   (rank-r noise)
                    A' = A+E,  B' = B+F
Miner:              C' = A'·B';  transcript tr = all (n/r)³ intermediate r×r blocks
                    z = O(tr)     (or Remark 2.1: hash each block separately)
Decode_r(σ, C'):    C'' = (A·F_L)·F_R + E_L·(E_R·(B+F_L·F_R));  C = C' − C'' = A·B
```

Parameters: r ≪ n (we propose r = n^0.3; Pearl uses fixed r ∈ {32..1024} in production);
field 𝔽_q; σ a λ-bit seed; ε the success threshold. Honest overhead α = 1+o(1) (KW §6.5,
verbatim: "α(n) = O(n² + n²·r)/t_MatMul(n)... α(n) = o(1)").

| # | Leg | Status (preliminary result) |
|---|---|---|
| **(a)** | σ unpredictable (ROM) → E,F unknowable in advance → preprocessing useless | **Proven** (trivial in the ROM) |
| **(b)** | E,F individually uniform rank-r (Lemma 6.5) → each r×r block marginally uniform → a single block = a random r×r MatMul = Ω(r^ω) | **Proven** (Lemma 6.5 + Claim 6.6) |
| **(c)** | Computing all intermediates costs Ω(n^(ω_r+1)/r) (Assumption 6.4) | **Conjecture** — but KW themselves argue it is nearly automatic from the output-length bound (§6.1) |

**Correlation caveat (KW §2, verbatim):** "the above argument does not work for computing all
of the intermediates because they are correlated (E and F are only rank r). However,
recovering the correlations requires essentially solving a linear system of equations which,
we conjecture, is as difficult as multiplying matrices."

---

## 2. QUESTION-1: Is Assumption 6.4 actually unnecessary? (the most critical question)

**Verbatim (KW §6.5):**

> **Assumption 6.4.** *There is no algorithm to compute all the intermediate values when
> multiplying two random n × n rank-r matrices running in time o(n^{ωr+1}/r).*

**KW's own justification (verbatim):**

> "Using the state of the art rectangular fast matrix multiplication, we can see that the
> above assumption is **true** (because the number bits needed to write down all
> intermediates – **Θ(n³/r)** – is always a lower bound on the running time and ωr = 2 for
> sufficiently small r)."

**Our preliminary result:** Assumption 6.4 holds almost automatically because of the
**output-length lower bound** Θ(n³/r) — which is exactly KW's argument. So (c) is stated
**unnecessarily strongly**; the real security rests on (a)+(b)+Merkle and survives even
under a weaker, standard assumption.

**However, we specifically want you to audit this nuance:** when the PoW condition is
`z = O(tr)` or, more precisely, a **Merkle root**, the attacker need not **materialise** the
transcript — only its hash. That is where the output-length bound **does not apply**. The
true security assumption is therefore:

> **(Real) Assumption:** under a hash function (ROM), the cost of computing the **Merkle
> root** of a rank-r-noised MatMul transcript (or of any one per-tile hash) is
> asymptotically equal to the cost of computing the transcript.

**Questions:**
- **(1a)** Is this "real assumption" **provable** from a standard Merkle/one-wayness
  argument, or is it an additional assumption? Since the root depends on the hashes of all
  leaves, and a hash is one-way, computing the root requires evaluating every leaf
  (regardless of structure — even if the leaves are deterministic functions of only O(nr)
  random values). **Do you see a hole in this argument?**
- **(1b)** KW's Θ(n³/r) output-length argument relies on ω_r = 2 (rectangular FMM). If
  ω_r < 2 (i.e. progress on rectangular multiplication), does Assumption 6.4 **collapse**?
  Even if it does, do (a)+(b)+Merkle survive? (Our preliminary result: yes; but ω_r < 2
  also means the honest miner speeds up — a difficulty adjustment suffices to preserve the
  ratio, see the FMM row in the attack table.)
- **(1c)** Is the linear-system reduction in the "correlated intermediates" caveat (KW §2)
  really as hard as MatMul? Is this what KW's **abstract** calls a "batch of low-rank
  random linear equations", and does the terminological slippage (transcript vs. linear
  equations) **weaken** the security argument, or is it purely presentational?

---

## 3. QUESTION-2: Marginal uniformity of Lemma 6.5 — are ROM+σ sufficient?

**Verbatim:**

> **Lemma 6.5.** *In the random oracle model and assuming that σ is unpredictable, then the
> induced distribution of E and F is uniformly random from E_{r,n} (with very small
> statistical error). In particular, with very high probability [each row...]*

**Questions:**
- **(2a)** Does the proof of Lemma 6.5 break when σ is bound to the **blockchain context**
  (KÖK uses `ctx` = `selected_parent_hash ‖ miner_pubkey ‖ task_ref ‖ height ‖
  proof_system_id ‖ nonce`)? σ is no longer uniform, it is **derived from ctx**. Our
  preliminary result: no — the lemma's hypothesis is "σ is unpredictable", a ctx-bound σ is
  still unpredictable (not fair, but unpredictable) and H's output in the ROM stays uniform.
  **But this integration is ours, not KW's — please verify.**
- **(2b)** "Very small statistical error" — how does this error bind the probability that
  **all** (n/r)³ blocks are weak simultaneously? Is a union bound over (n/r)³ tiles small
  enough, or does a problem arise in matching ε to n (see QUESTION-4)?

---

## 4. QUESTION-3: Per-tile balance — is the difficulty secure? (Remark 2.1 = Pearl's jackpot)

KÖK v2 uses the **per-tile variant** (Pearl's production choice; KW Remark 2.1). Our
balance computation:

- **Honest:** one MatMul (cost n³) yields (n/r)³ tile attempts → **attempts per FLOP =
  r^(−ω)**, independent of n.
- **Attacker:** a single tile is the product of two marginally uniform r×r blocks → cost
  ≥ Ω(r^ω) (leg (b)). Same as honest.
- **Conclusion:** difficulty can be a function of block count (or DAG height); **freedom
  in matrix size does not break the balance** (r is a protocol parameter, fixed).

**Questions:**
- **(3a)** Is this balance computation correct? In particular, verify that the attacker
  cannot reduce FLOPs per tile by choosing **many small matrices** (small n), because
  attempts/FLOP = r^(−ω) and **r is fixed**. But what if the attacker chooses **large n**?
  The tile count grows as (n/r)³, but each tile's cost is **unchanged** (an r×r block). Can
  the overhead (the O(n²r) of Encode/Decode) be amortised so that attempts/FLOP
  **increases**? (Our preliminary result: only to a limited extent — O(n²r)/n³ = r/n → 0;
  so attempts/FLOP can only rise, the attacker **does not gain**, and the same advantage is
  available to an honest miner. **We want this verified.**)
- **(3b)** Is Pearl's jackpot policy (TV-11..TV-14, the `JackpotToy` class in
  `g_layer_tests.py`) the correct counterpart of this balance in an **FP/quantised**
  setting? In particular: does the **unpredictable-summands** control (which in FP catches
  the attack of discarding a summand that rounds a certain way) have any meaning in an
  **integer** setting? Our preliminary result: in INT there is no precision shortcut (no
  rounding), so TV-14 pertains only to FP (Phase 3) and is unnecessary for the INT Layer G.
  **Do you agree?**

---

## 5. QUESTION-4: Matching ε and n (Remark 5.3) — the rule for adjusting difficulty

KW Remark 5.3: difficulty is adjusted through **either n or ε**; if both are left free,
miner optimisation becomes complicated. KÖK v2's rule: **n is a protocol constant, and ε
(the target) is adjusted by retargeting** (exactly Bitcoin's rule; spec Appendix B).

**Questions:**
- **(4a)** Does this rule still hold in the per-tile variant (QUESTION-3)? In per-tile,
  the tile count depends on n, but each tile's cost depends on **r**. So is adjusting
  difficulty via ε secure, **as long as r is fixed**? (Preliminary result: yes; r is a
  protocol parameter and cannot change without a fork — §7, Layer A.)
- **(4b)** Memory: the full-transcript variant requires Θ(n³/r) memory (KW Remark 2.1
  concedes this). The per-tile choice reduces this to O(nr). **Is that right?** And is
  O(nr) still a **meaningful hardware threshold** for a miner (against ASICs)?

---

## 6. QUESTION-5: Structural attack classes — is an attack missing?

Refute or confirm the table below. If you find a **missing row** (an attack that is not in
the table), that would be the most valuable output of this brief.

| Attack | v1 (plain Freivalds) | KW + KÖK ctx | Result |
|---|---|---|---|
| Sparse/permutation A (work O(n³)→O(n)) | ✓ works | A+E marginally uniform → useless | KW wins |
| A=B=0 (easy input) | ✓ | transcript still demands (n/r)³ uniform tiles | KW wins |
| Precompute/replay (without knowing σ) | partially | σ = ctx (selected_parent ‖ ...) → impossible | KW + ctx wins (TV-1) |
| Shortcut from correlation (rank-r noise) | n/a | X_i·(Σ Y_{ℓ'}Z_{ℓ'})·W_j = same asymptotics (KW §6.5 itself shows this) | **equivalence** |
| Trapdoor matrix (VZ25 2502.13065 / BN25 2502.13060, LPN) | n/a | E,F are derived from σ; the attacker **cannot plant** a trapdoor | KW wins (we independently verify KW's own dismissal) |
| FMM progress (ω < 2.371339; AlphaEvolve 2.371177, 2026) | n/a | honest and attacker use the **same** algorithm → ratio preserved | **economic, not cryptographic** |
| Quantum | Grover ✓ (like Bitcoin) | HHL-like algorithms for MatMul require quantum access and find no classical hash | **Bitcoin-parity PQ** |
| **Low-entropy hardware (Pearl's open problem: "is 1-bit hardware enough?")** | n/a | Layer G is MatMul-based; a low-alphabet special circuit affects **both Pearl and KÖK** | **SHARED OPEN GAP** — toy evidence from the noise-floor test; in production, a whitelist plus jackpot policy |

**Questions:**
- **(5a)** The "equivalence" row above (the correlation shortcut) — is it genuinely
  **equivalent**, or is there a constant-factor advantage for the attacker? (Pearl's
  jackpot thresholds ε_idle/ε_tame/ε_pred exist to bound those constant advantages; we have
  a toy adaptation but **no production calibration**.)
- **(5b)** Hunt for a **missing attack**, especially in these three directions:
  (i) **Algebraic:** a shortcut arising from the rank-r structure of E,F (E = E_L·E_R) and
  the prefix-sum structure Y = Σ_{ℓ'≤ℓ} A'_{i,ℓ'}·B'_{ℓ',j};
  (ii) **Hash:** a shortcut from the **structure** (low rank) of MatMul outputs causing
  BLAKE3 (or whichever RO is used) to behave non-randomly on them;
  (iii) **Social/strategic:** a miner using **multiple identities** (sybil) to influence
  voting or task assignment (VRF assignment, spec §A.10.3) — **this is outside Layer G**,
  but could it weaken G?

---

## 7. QUESTION-6: Conjecture A.1 (random rotation) — does it affect KÖK?

**Verbatim (KW Appendix A):**

> **Conjecture A.1.** *Let A, B ∈ R^{n×n} be full-rank matrices. Then the amortized cost of
> computing all n³/r³ partial sums (A.1) in Algorithm 1.1 with r = √n, d = O(1), even with
> O(n³) preprocessing time, requires Ω(r³) time, in the word-RAM model with word-size
> w = O(log n).* — "**This is the analogue of Assumption 6.4.**"

**Context:** the random-rotation (self-cancelling noise) scheme (A·S)·(S⁻¹·B), randomised
Hadamard, **O(n² log n) overhead, no noise peeling**. **Pearl's own open-problems page
still asks whether this rotation PoW scheme is secure.**

**Questions:**
- **(6a)** KÖK v2 does **not** use this scheme (we use the §6.5 instantiation). But if
  Conjecture A.1 were proven, would that have **any consequence for KÖK's Assumption
  6.4**? (Preliminary result: no — two different schemes; A.1 is presented as an *analogue*
  of 6.4 but is independent of it.)
- **(6b)** If A.1 **fails** (as Pearl fears), is KÖK's Layer G (transcript variant)
  affected? (Preliminary result: no — A.1 binds only the rotation scheme.)

---

## 8. Format of the review output we expect

For each QUESTION:
1. **Verdict:** CONFIRMED / REFUTED / PARTIALLY / UNDETERMINED (evidence insufficient).
2. **Rationale:** with a mathematical argument or a citation.
3. **If refuted:** give a concrete attack or counterexample — we can run it on the
   prototypes (`u_layer_prototype.py`, `g_layer_tests.py`) and update the specification.
4. **If undetermined:** state what additional evidence or experiment is needed.

**Important:** "I agree" is **not sufficient.** Stating the reason for a verdict is
mandatory — because the score of KÖK v2 (technical 82/100 in our internal rubric) depends
on the **outcome** of this review, and if we want to say "a cryptographer confirmed this",
we must know **what** was confirmed.

---

## 9. Executable evidence (available to you)

- `u_layer_prototype.py` — TV-5..TV-10 (escrow/burn, VRF, fraud, slashing, PQ gate);
  stdlib only, 2.5 s. Uses `KWKernel(q=97, n=8, r=2)` — **toy size**, but the interface is
  identical to the production spec (§A.10).
- `g_layer_tests.py` — TV-1..TV-4 (replay rejection, prescribed hardness, easy instance,
  φ), TV-11..TV-14 (toy adaptation of the jackpot policy), RT-1..RT-3 (retarget); 12.8 s.
- `pass_sim_en.py` — closed-form solver for Pass (arXiv 2606.06700), calibrated on Pearl
  (reproduces the live network's size to within 5.8%).
- `extracted/KW_full.txt`, `extracted/Pass_full.txt`, `extracted/Pearl_new_wp.txt` — full
  texts of the source papers.

**Toy-size caveat (honest):** q=97, n=8, r=2 — this does **not** test **asymptotic**
arguments, only **interface and economic** behaviour. Asymptotic security is the part of
this brief that is **your** expertise; the prototype instead evidences **economic and
protocol** behaviour.

---

## 10. Timeline and compensation

- This Phase 2 review is **mandatory before testnet**.
- Depending on the outcome: CONFIRMED → the testnet roadmap begins; REFUTED → the fallback
  (spec §A.9, pure-PoW mode) engages and Layer G is redesigned.
- Compensation: from the treasury described in `KOK_V2_PAPER.md` (5–8% of block rewards),
  either in a PRL-like token or as a fixed fee. **Accepting this brief is not a promise of
  payment.**

---

## Appendix: a nuance KW glosses over (and the reader should know)

KW's abstract says "batch of low-rank random linear equations", but the §2 argument reduces
this to the **MatMul transcript**; the real assumption is (b) plus Merkle. This
terminological slippage explains both Pearl's "prescribed hardness" marketing and the
criticism that the system "accepts random matrices by design": **both sides are right** —
the cryptography is sound, the utility is not. KÖK v2 separates the two honestly.
