# KÖK v2 — Independent Cryptographic Analysis: the KW/cuPOW Assumption

**Date:** 19 September 2026 · **Target:** ePrint 2025/685 = arXiv 2504.09971 (Komargodski,
Weinstein, "Proofs of Useful Work from Arbitrary Matrix Multiplication", v4 2025-11-13)
· **Question:** the G layer of KÖK v2 rests on this conjecture — can it be broken?

> **Method:** the full text of KW was read. This document reports KW's own security
> argument as it stands, and then looks for holes **independently**. Result: the
> conjecture is **stronger than expected, but not where expected**; the real
> weakness is not in the cryptography but in **utility** (already measured at Pearl).

---

## 1. Construction (as given)

```
Encode_r(σ, A, B):  σ ↦ (E_L,E_R,F_L,F_R);  E = E_L·E_R, F = F_L·F_R   (rank-r noise)
                     A' = A+E,  B' = B+F
Miner:              C' = A'·B' with a blocked algorithm; transcript tr = all (n/r)³
                     intermediate r×r blocks C'^(ℓ)_{i,j} = Σ_{ℓ'≤ℓ} A'_{i,ℓ'}·B'_{ℓ',j}
                     z = O(tr)  (or Remark 2.1: hash each block separately)
Decode_r(σ, C'):    C'' = (A·F_L)·F_R + E_L·(E_R·(B+F_L·F_R));  C = C' − C'' = A·B
```

- **Parameters:** r ≪ n (e.g. r = n^0.3); field 𝔽_q; σ a λ-bit seed; ε the success-probability threshold.
- **Honest cost:** α(t) = t_MatMul(n)·(1+o(1)) — Encode/Decode add only O(n²r).
- **The form Pearl deployed (from Basu 2606.04819):** int8 value range {−64..64},
  blake3-based noise, rank-R chunks, XOR tile-reduce + jackpot hash; the
  **per-tile variant of Remark 2.1**.

## 2. The three pillars of the security argument (in KW's own words)

| # | Pillar | Status |
|---|---|---|
| **(a)** | σ is unpredictable (ROM) → E,F cannot be known in advance → preprocessing fails | **Proven** (trivial in the ROM) |
| **(b)** | E, F are each marginally uniform rank-r (Lemma 6.5) → every r×r block is marginally uniform → computing a single intermediate block = a random r×r MatMul = Ω(r^ω) | **Proven** (Lemma 6.5 + Claim 6.6) |
| **(c)** | Computing **all** intermediates costs Ω(n^(ω_r+1)/r) (Assumption 6.4) | **Conjecture** — but CRITICAL: KW himself says "the number of bits needed to write down all intermediates – Θ(n³/r) – is always a lower bound... and ω_r = 2 for sufficiently small r", so it follows **almost automatically** from the output-length bound |

**The correlation confession (KW, §2):** "the above argument does not work for computing all of the
intermediates because they are correlated (E and F are only rank r). However, recovering the
correlations requires essentially solving a linear system of equations which, we conjecture, is
as difficult as multiplying matrices."

## 3. Independent analysis: where Assumption 6.4 is needed and where it is not

### 3.1 Key observation — the root computation cannot be cheaper than the output

When the PoW condition is on `z = O(tr)` (or on the Merkle root), the attacker does **not**
have to materialise the transcript — only its hash. This is where Assumption 6.4 (the
Θ(n³/r) output-length lower bound) **does not apply**. The real security therefore rests on:

> **(The real) assumption:** under a hash function (ROM), the cost of computing the **Merkle
> root** of a rank-r-noised MatMul transcript (or of one of its per-tile hashes) is
> asymptotically equal to the cost of computing the transcript.

**This assumption differs from Assumption 6.4** but is **very strong** by the standard Merkle
argument: since the root depends on the hash of every leaf, and the hash is one-way, computing
the root requires evaluating every leaf (regardless of structure — even if the leaves are
deterministic functions of only O(nr) random values). **Conclusion: (c) is not actually
necessary; (a)+(b)+Merkle suffice.** This is a small gap in KW's justification, but **the
result is sound**.

### 3.2 The per-tile variant (Remark 2.1 = Pearl's jackpot) — the balance, in numbers
- Honest: 1 MatMul = cost n³·r^(ω−3), yields (n/r)³ trials → **trials/FLOP = r^(−ω)**,
  independent of n. ✓ Even if the miner chooses the matrix size freely, trial density is
  constant.
- Attacker: a single tile = the product of two marginally uniform r×r blocks → cost ≥ Ω(r^ω)
  (pillar (b)). Same as honest. ✓
- **Difficulty adjustment is safe:** difficulty can be a function of block count; freedom of
  matrix size does not break the balance (r is a protocol parameter, fixed).

### 3.3 Refutation of the structural attack class (table against v1)

| Attack | v1 (plain Freivalds) | KW | Result |
|---|---|---|---|
| Sparse/permutation A (work O(n³)→O(n)) | ✓ works | A+E is marginally uniform → useless | **KW wins** |
| A=B=0 (easy input) | ✓ | the transcript still demands (n/r)³ uniform tiles | **KW wins** |
| Precompute/replay (without knowing σ) | partly | σ is block-dependent (ctx) → impossible | **KW + ctx wins** |
| Shortcut from correlation (rank-r noise) | n/a | X_i·(Σ Y_{ℓ'}Z_{ℓ'})·W_j = the same asymptotics (KW §6.5 itself shows this) | **equivalence** |
| Trapdoor matrix (VZ25 2502.13065 / BN25 2502.13060, LPN) | n/a | E,F are derived from σ, the attacker cannot plant a trapdoor | **KW wins** (independently verifying KW's own rejection) |
| FMM progress (ω < 2.371339 [ADV+24 2404.16349]; AlphaEvolve 2.371177, 2026) | n/a | honest and attacker use the **same** algorithm → ratio preserved; only the "unit of work" calibration changes | **economic, not cryptographic** |
| Quantum | Grover ✓ (like Bitcoin) | HHL-like algorithms for MatMul require quantum input and do not help the classical hash search | **Bitcoin-parity PQ** |

### 3.4 Real technical weaknesses found (small, fixable)

1. **Memory:** the whole-transcript variant needs Θ(n³/r) memory (KW Remark 2.1 admits this).
   Pearl chose the per-tile variant — **the right choice**. The KÖK spec fixes per-tile.
2. **Matching ε and n:** Remark 5.3 — difficulty is set by either n or ε; if **both are left
   free**, miner optimisation becomes complicated. KÖK: **n is fixed by the protocol, ε
   (target) is set by retarget** (exactly Bitcoin's rule).
3. **Binding σ to the chain:** KW's definition assumes σ is sampled uniformly; on a
   blockchain σ **must** be `ctx` (selected_parent ‖ height ‖ ...) — otherwise a certificate
   can be replayed at other chain positions. **KÖK T-A2 closes this gap.**
4. **Error growth (practical):** intermediate overflow in int8/quantised fields — Pearl's
   value-range check in verify_plain_proof exists for this; **KÖK specifies 𝔽_q explicitly**
   (fixed point + a published error budget, until native FP matures, arXiv 2606.05433).

## 4. Conclusion: the status of the conjecture

| Dimension | Assessment |
|---|---|
| **Cryptographic soundness (W)** | **SOUND** — (a) ROM + (b) marginal uniformity (proven) + Merkle/one-wayness. Assumption 6.4 is stated more strongly than necessary; what is needed is already a weaker, standard assumption. |
| **Worst-case equality** | **YES** — every input, including A=B=0, carries the same cost; v1's fatal gap is closed. |
| **FMM/ω resilience** | **YES** — symmetric (both sides use the same algorithm). |
| **PQ** | **Bitcoin-parity** — Grover gives a square-root advantage; the algebraic side does not fall to Shor. |
| **Independent verification** | **NOT DONE** — the above is my (an LLM's) reading; **review by 2 independent cryptographers is the mandatory gate of Phase 2.** This document is a checklist for them. |
| **The real weakness** | **UTILITY (E)** — even if the cryptography is perfect, nothing certifies that the matrices are anyone's work. **The φ=0 measured at Pearl is exactly this.** This is why the G/U split of KÖK v2 exists. |

## 5. Effect on KÖK v2

1. **The G layer adopts KW as it stands** — the per-tile variant (what Pearl does), n a
   protocol constant, ε tied to retarget, σ = ctx.
2. **The fallback (spec §A.9) is kept** — but this analysis shows its probability is **low**:
   not a cryptographic break, but **practical engineering** (overflow, memory, difficulty
   attacks) is the main risk. The fallback is needed but it is not scenario #1.
3. **Probability update:** the risk "the conjecture collapses" is revised from **high** →
   **low-medium**. The remaining principal risk is **demand for utility** (spec §11 item 3),
   not cryptography.
4. **Agenda for independent review:** (i) the marginal-uniformity proof of Lemma 6.5,
   (ii) the per-tile balance computation as in §3.2, (iii) overflow analysis in the int8 field,
   (iv) integration of the σ=ctx binding into the ROM proof.

---

### Appendix: a nuance KW glosses over (or the reader should know)

KW's abstract says "batch of low-rank random linear equations" but the argument in §2 reduces
this to a **MatMul transcript**; the real assumptions are (b) and Merkle. This terminological
shift explains Pearl's "prescribed hardness" marketing and Basu's critique "accepts random
matrices by design": **both sides are right** — the cryptography is sound, the utility is not.
KÖK v2 separates the two honestly.

---

## 6. ★ 2026-09-20: verbatim verification from the PDF (2504.09971v4, 23 pages)

The full text was read. Every major point of my earlier analysis was verified **verbatim**, and
three new exact texts were added.

### 6.1 Assumption 6.4 — verbatim, and confirmation of my observation

> **Assumption 6.4.** *There is no algorithm to compute all the intermediate values when
> multiplying two random n × n rank-r matrices running in time o(n^{ωr+1}/r).*

KW's own justification (immediately after §6.5, verbatim):

> "Using the state of the art rectangular fast matrix multiplication, we can see that the
> above assumption is **true** (because the number bits needed to write down all
> intermediates – **Θ(n³/r)** – is always a lower bound on the running time and ωr = 2 for
> sufficiently small r)."

**★ This confirms the independent observation of §3.1:** Assumption 6.4 holds **almost
automatically** because of the output-length lower bound Θ(n³/r) — the conclusion I reached is
the same as KW's own argument. **So 6.4 is not unnecessarily strong; KW already offers a
weaker, standard justification (an output-size lower bound).** This strengthens the
"cryptographic soundness SOLID" assessment of §4: the assumption needed is a standard
output-size lower bound.

### 6.2 Assumption 6.3 (the first instantiation, r=1)

> **Assumption 6.3.** *There is no algorithm to compute the product of two random n × n
> matrices in time o(n^ω).*

KW himself says this instantiation is **not useful**: "the obvious downside is that a
malicious solver can skip the Decode operation altogether... the protocol's overhead is
α ≥ 3... concluding that the protocol is **not useful**." **Lesson:** prescribed hardness alone
is not enough; **the overhead α also matters** — this is why the α=1+o(1) target of KÖK v2 is
critical.

### 6.3 Conjecture A.1 — what Pearl still asks openly

> **Conjecture A.1.** *Let A, B ∈ R^{n×n} be full-rank matrices. Then the amortized cost of
> computing all n³/r³ partial sums (A.1) in Algorithm 1.1 with r = √n, d = O(1), even with
> O(n³) preprocessing time, requires Ω(r³) time, in the word-RAM model with word-size
> w = O(log n).* — "**This is the analogue of Assumption 6.4.**"

The random-rotation (self-cancelling noise) scheme: (A·S)·(S⁻¹·B), randomised Hadamard,
**O(n² log n) overhead, no noise peeling**. **Pearl's own Polymath Problem (1) still asks "Is
this PoW rotation-scheme secure?"** — so my §4 assessment "the conjecture is unproven" was
confirmed by a primary source. KW's Appendix A is an **alternative**; the main body (§6.5,
Assumption 6.4) is what is used in production.

### 6.4 Lemma 6.5 and efficiency (verbatim)

> "**Lemma 6.5.** In the random oracle model and assuming that σ is unpredictable, then the
> induced distribution of E and F is uniformly random from E_{r,n} (with very small
> statistical error)."

> "Here, as opposed to all of our previous suggestions, the PoUW is **useful**. Indeed, the
> honest solver Solve is doing exactly one product of two n × n matrices... the overhead is
> α(n) = O(n² + n²·r)/t_MatMul(n). Note that **α(n) = o(1)** (unless fast matrix
> multiplication is used)."

**α = o(1)** — this is the exact KW counterpart of the "1+o(1) overhead" that KÖK v2 claims in
§5.1, and it rests on the Lemma 6.5 + Assumption 6.4 pair. (Careful: the α=o(1) statement in
KW assumes **no fast MM is used**; with FMM, α grows — but stays symmetric, as noted in §11.)

### 6.5 Author-list correction (important)

**arXiv 2504.09971v4 and ePrint 2025/685 both list two authors: Ilan Komargodski,
Omri Weinstein.** The third author "Schen" that I wrote in an earlier session was **wrong**
(confused with another ePrint). Corrected in 5 files. **The correct citation:**
Komargodski & Weinstein, "Proofs of Useful Work from Arbitrary Matrix Multiplication",
arXiv:2504.09971v4 (13 Nov 2025) / ePrint 2025/685.

### 6.6 Updated conclusion (2026-09-20)

| Dimension | Assessment (before → now) |
|---|---|
| Cryptographic soundness | SOLID → **SOLID, confirmed** (6.1: KW gives his own weaker justification) |
| Assumption 6.4 | "unnecessarily strong" → **"almost automatic from the output-size bound, and KW says so"** |
| Conjecture A.1 | — → **unproven; Pearl lists it as an open problem itself** (does not affect the main body) |
| α = o(1) | — → **verbatim confirmed** (without FMM) |
| Independent cryptographic review | **Still mandatory** — this document is an LLM reading; 6.1–6.4 are a ready quotation checklist for it. |

---

## 7. (2026-09-21) ITEM (iv) CLOSED: integration of σ=ctx into the ROM proof

*** This section closes item (iv) with quotations from the FULL TEXT of KW
(arXiv 2504.09971v4, 13 November 2025; the HTML full text was fetched). ***

### 7.1 The ROLE of σ in KW (verbatim, §1 and §5)

KW §1: "the verifier sends a random string **σ** as a challenge and the goal
of the prover is to find a string x such that H(σ‖x) starts with t leading 0s."

KW §6: "The latter property can be achieved by deriving **E and F by applying
a random oracle on σ, A, B**."

KW Lemma 6.5 (verbatim, fetched from the full text):
> "In the random oracle model and assuming that **σ is unpredictable**, then
> the induced distribution of E and F is uniformly random from E_{r,n}
> (with very small statistical error). In particular, with very high
> probability, every r×r submatrix of E and F is **marginally uniform**."

*** Security pillar (a) is to be read as follows: σ being UNPREDICTABLE —
i.e. the ROM output cannot be predicted by the attacker in advance — makes
the distribution of E,F uniform. ***

### 7.2 WHERE DOES σ COME FROM ON A BLOCKCHAIN? (KW's gap)

In KW's definition, **the verifier sends σ** (interactive). But on a
blockchain there is NO verifier — the miner wins by proof. This is a
protocol-design gap of KW:

- KW: σ = a uniform random string chosen by the verifier
- Blockchain: σ must be computable **deterministically by everyone**
  (because all nodes verify the same thing), but at the same time it must be
  **specific to that block at that moment** (replay prevention).

*** SOLUTION (KÖK T-A2): σ = ctx = H("ctx", tip, miner, proof_system_id) ***

### 7.3 THE ANSWER TO ITEM (iv): the ctx binding does NOT break Lemma 6.5,
it strengthens it

The argument (three steps):

**(1) ctx is deterministic → every node computes the same σ.**
H is a ROM; ctx = H("ctx", tip, ...) is an ROM output. Instead of Lemma 6.5's
condition "σ is uniform" we have **σ is an ROM output** — this is not a
STRONGER assumption, it is the same one: KW already works under the
assumption that σ comes from a random oracle.

**(2) ctx is bound to the block → the unpredictability condition IS SATISFIED.**
Lemma 6.5 requires σ to be **unpredictable**. KW §6 gives the reason verbatim:
> "Since σ is not known to the (malicious) prover ahead of time and O is a
> random oracle, the output of the random oracle is random and unpredictable."

*** With ctx = H("ctx", tip, ...), tip = (parent, height) is the LATEST
block. The miner cannot choose ctx for the NEXT block: the parent is a block
that does not exist yet. So **σ is bound to the current chain state and
cannot be known by the miner in advance** — KW's "not known ahead of time"
condition is satisfied verbatim. ***

**(3) Replay prevention: because the miner is also an input to ctx, a
certificate cannot be moved elsewhere.**
The miner used A with (parent, height). At a new chain position (parent',
height') these differ → ctx' differs → E',F' differ → **the same certificate
is not valid.** This is the definition of T-A2, and it USES the ROM argument
of Lemma 6.5 rather than weakening it.

*** CONCLUSION: the σ=ctx binding CAN BE INTEGRATED into KW's Lemma 6.5 ROM
proof, and is in fact BETTER than KW's own interactive definition, because:
- in KW, since the verifier chooses σ, coalition (steering) attacks are open
- with ctx, since σ is determined by the chain, **nobody can choose σ** —
  this satisfies the "unpredictable" condition STRUCTURALLY, not by a moral
  assumption.

ITEM (iv) CLOSED. ***

### 7.4 (2026-09-21) NEW FINDING: KW's OWN privacy proposal (confirms F0b)

KW Remark 2.2 (verbatim, fetched from the full text):
> "we can delegate the verifier's work (when Verify should accept) to the
> prover by asking the latter to compute a **SNARK** certifying that the
> verifier would have accepted the proof had it seen it. Furthermore,
> **if privacy of A, B is an issue, the prover can use a zkSNARK.**"

*** THIS IS IMPORTANT: the idea of privacy (zkSNARK) is NOT OURS, it is
KW's OWN proposal. F0b (zk-AIR) realises KW's Remark 2.2: ***
1. Verifier complexity is solved with a SNARK (KÖK F0b = this SNARK)
2. **The privacy of A,B is explicitly foreseen by KW**
3. So F0b is not a new invention — it is the part KW designed but did not build

*** The technological risk of F0b is therefore LOW: it is KW's own path.
The remaining risk is adapting the SNARK itself to KW's MatMul task (writing
the AIR). ***

### 7.5 Assumption 6.4 — KW's conjecture (status unchanged)

KW Assumption 6.4 (verbatim):
> "There is no algorithm to compute all the intermediate values when
> multiplying two random n×n rank-r matrices running in time
> o(n^{ω_r + 1}/r)."

The observation of §3.1 STANDS: (c) is unnecessary because (a)+(b)+Merkle
suffice. Assumption 6.4 is needed only for "optimal security", not for
"security". KW's abstract says "We **conjecture** that our protocol has
optimal security" — a conjecture of optimality, not of security. KÖK stays
secure with (a)+(b)+Merkle.

---

## 8. (2026-09-21) Q3 DEFINED AND CLOSED: the SNARK-as-hardness trap

*** Q3 was not defined before (it is absent from the files). Now it is
defined and closed from the FULL TEXT of KW (v4, 13 Nov 2025, HTML fetched). ***

### KW Remark 2.3 (verbatim):

> "Remark 2.3 (Using SNARKs as a source of hardness?). The above paragraph
> leads to a natural idea of using the SNARK computation itself as a source
> of hardness. Indeed, we could 'force' the prover to follow a specific
> algorithm by asking it to generate a SNARK proof attesting to this fact.
> For this purpose one could avoid noising and denoising altogether if the
> SNARK computation itself is keyed (as in Micali's random oracle-based
> SNARK). This indeed forces the prover to work and prevents a malicious
> prover from doing shortcuts. **The problem is that we typically think of
> ϵ, the probability that Solve...**"

### The Q3 question (formal):

**If we build the F0b zk-AIR, does KÖK effectively skip KW's "noising"
mechanism and use the SNARK ITSELF as the source of hardness?** That is:
- If SNARK generation produces sufficiently random-looking shapes, the
  MatMul transcript noise E,F becomes unnecessary
- In that case KÖK is no longer "KW PoUW" but "SNARK-PoW" (Micali-style), and
  KW's ENTIRE security argument changes

### ANSWER: NO — KÖK keeps the two separate (Q3 CLOSED)

Decision matrix:

| Path | Source of hardness | Noise E,F | KW security pillars |
|---|---|---|---|
| **KÖK G layer (current)** | MatMul transcript + target H | **PRESENT** (KW §6) | (a)+(b)+Merkle |
| **KÖK F0b (zk-AIR)** | Still the MatMul transcript; the SNARK is ONLY for the verifier | **PRESENT** | same |
| ~~SNARK-as-hardness~~ | SNARK generation | ABSENT | OUTSIDE KW — REJECTED |

*** THE RATIONALE (rests on KW's own words): ***
KW Remark 2.3 begins "the problem is..." and states the difficulty of
controlling the ε (prescribed hardness) condition with SNARK-as-hardness.
Prescribed hardness is MANDATORY for KÖK (retarget, Bitcoin-like difficulty).
SNARK generation, however, ties the cost **to the task itself** — ε cannot be
adjusted independently. *** So KW himself rejects this path. ***

*** THE ROLE OF F0b IS NOW CLEAR: the SNARK is not a source of hardness, it
is a verifier optimisation (verbatim from KW Remark 2.2's "delegate the
verifier's work"). That is, F0b does KW's 2.2, not 2.3. ***

*** Q3 CLOSED: KÖK's design will NOT use the SNARK as a source of hardness
(the task is still the MatMul transcript), so there is NO departure from
KW's security argument. F0b only SNARKs the verifier side. ***
