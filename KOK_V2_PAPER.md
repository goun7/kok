# KÖK Network v2 — PoW L1 + Verifiable-Compute Market: The Best System Possible on Paper

**Date:** 19 September 2026 (KW/Pearl/Demirel update) · **Status:** Design document (supersedes the v1 paper)
**Symbol:** `$KOK` · **Consensus:** GHOSTDAG + KW MatMul PoUW (demand-independent security) · **Fair launch**
**Technical spec:** `KOK_V2_TECHNICAL_SPEC.md` (Annex A task market, Annex B difficulty, Annex C economy)

> **Pitch (old → new):**
> ~~"Miners solve an AI matrix, and validators verify it in microseconds, without spending energy."~~
> **"A fair-launch PoW L1: security comes from the memoryless rejection-sampling hardness of
> Komargodski–Weinstein MatMul PoUW certificates — entirely demand-independent (without falling
> into Pearl's 'useful work = security' fallacy). On top of it, a fee-paid verifiable-compute
> market: clients pay for governance proofs and provable inference, and demand is externalized
> through the real fee held in escrow. The cryptography is hash-based and post-quantum;
> emergency-fork schemes are committed in advance."**
> This is **not a "free AI inference" promise.** The promise is this: **the same security
> mathematics as Bitcoin (attack = PR/2), but a verifiable-compute output — paid for with the same
> electricity and purchasable for real money — is also produced.** Energy is still spent; utility
> is a **bonus**, not the source of security — the three 2026 papers make this unavoidable (§3.2).

---

## 1. Design Philosophy: Three Unbreakable Invariants

Three of v1's five fatal gaps were converted directly into three invariants:

- **I1 — The work must be worst-case hard by definition.** Work = **KW MatMul PoUW certificate**
  (ePrint 2025/685): prescribed hardness is independent of the input choice, with 1+o(1) overhead,
  and resistant to FMM. v1's Freivalds equation is, relative to KW, "trivial O(1) overhead but
  useless" — it is open to a structured-matrix attack. (Security rests on a **conjecture**; §3.1.)
- **I2 — The certificate's statement must be bound to the chain.** `ctx = selected_parent_hash ‖
  miner_pubkey ‖ task_ref ‖ height ‖ proof_system_id ‖ nonce`. This makes precompute, replay, and
  grinding impossible (SNARKChain's "chain integrity + miner identity" requirement, arXiv 2510.09729).
- **I3 — The difficulty must be memoryless.** Once `H(FS_digest ‖ nonce) < target` is added to the
  block validity condition, block intervals become exponentially distributed → **Bitcoin's retarget
  mathematics applies verbatim**, and the DAG block rate is preserved. This is used instead of
  "task size = difficulty" for deterministic work (full formulation: `KOK_V2_TECHNICAL_SPEC.md`,
  Annex B).

The remaining two gaps (economics, law) are addressed in §7 and §9.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6 — ECONOMY: tail emission + %treasury + task-fee market (Pass 2026)    │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 5 — CRYPTO-AGILITY PLANE:                                               │
│   versioned schemas (statement_schema_id, proof_system_id, activation_epoch)   │
│   dual-verification window · formal-verification gate · miner lead-time        │
│   hardness monitoring + pre-committed emergency-fallback schema                │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 4 — CONSENSUS: GHOSTDAG (PHANTOM, ePrint 2018/104)                      │
│   + rejection-sampling difficulty (I3) + incentive-compatible task/tx selection│
│   + per-block STARK aggregation (ZK-ACE: ~160 B/tx)                            │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 3 — PROOF SYSTEM (PQ, transparent setup):                               │
│   S2: Circle STARK / S-two AIR (Lean-verified soundness, arXiv 2606.04311)     │
│   + lookup arguments for non-linear operations (Jolt Atlas, 2602.17452)        │
│   + recursive aggregation: Arc (hash-based, unbounded depth, CRYPTO 2025)      │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 2 — DETERMINISTIC COMPUTE HARNESS (for S2):                             │
│   pinned kernel/reduction-order/seed · Merkle trace commitment                 │
│   fixed-point + published error budget (today) → native FP precompile          │
│   (arXiv 2606.05433), once mature, verifies the REAL compute the GPU did       │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 1 — WORK LAYER (source of the useful output):                           │
│   S1: KW-native — the miner's OWN AI workload (1+o(1), 2-for-1)                │
│   S2: premium SNARK service — governance proofs + provable inference           │
│   Filler: dense-random MatMul = honest pure-PoW mode (liveness)                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Work Function and Task Market (Core)

> **2026-09-19 UPDATE — critical:** This section, based on research through Pass (arXiv 2606.06700),
> **2026-09-19 UPDATE — CRITICAL (2nd revision):** Research through Pass (arXiv 2606.06700) surfaced
> the **Komargodski–Weinstein construction** (IACR ePrint 2025/685): **prescribed hardness** with
> **1+o(1) overhead** for MatMul in a permissionless setting — it cryptographically closes v1's
> "structured-matrix" vulnerability. But three 2026 papers **also constrained PoUW's utility claim**:
> (i) Basu (arXiv 2606.04819) measured that Pearl's **live network at 24 EH/s produces zero useful
> AI computation** — the protocol accepts random matrices "by design"; (ii) Demirel
> (ePrint 2026/1492) proved **demand ≠ work**: a secure and live mechanism **has to be a
> demand-independent leader-election path** (Thm 2); (iii) SoK (ePrint 2025/1814): "utility does not
> contribute to the security budget". **This is why KÖK v2's architecture split into two: a SECURITY
> layer (demand-independent PoW) + a UTILITY layer (a fee-paid verifiable-compute market). There is no
> "useful work is chain security" promise — there cannot be.**

### 3.1 Cryptographic foundation: Komargodski–Weinstein MatMul PoUW
- **Construction:** ePrint 2025/685 (2025-04-15, 3 revisions, latest 2025-12-08). Arbitrary MatMul,
  miner-chosen input, **1+o(1) multiplicative overhead**, prescribed hardness; a claimed resistance
  to FMM algorithms (ω<2.371177, Aug. 2026).
- **What it provides / what it does not:** KW provides **work soundness (W)** — working for h(n) is
  mandatory for a valid certificate, independent of the input choice. **It does not provide demand
  exogeneity (E)** — it does not certify that the matrices are anyone's work (Pearl marketed this as
  "an economic property, not a cryptographic guarantee"; Basu measured its total collapse).
- **⚠ Dependency (honest):** KW's security is a **conjecture** (reducing the hardness to the "batch of
  low-rank random linear equations" problem). This is the protocol's single cryptographic assumption;
  independent review is the gate to Phase 2; an emergency fallback for its collapse is defined in the
  spec (`KOK_V2_TECHNICAL_SPEC.md` §A.9).

### 3.2 The two-layer honest architecture

**LAYER G — SECURITY (demand-independent; satisfies Demirel's Thm 2 at the construction level):**
- Work = **KW certificate + memoryless difficulty** (`H(FS_digest‖nonce) < target`).
- The miner chooses its own MatMul input (freely); thanks to **prescribed hardness**, that choice
  cannot reduce the work → sybil/easy-instance attacks are closed off. **But it is not claimed to be
  "useful"** — so as not to repeat Pearl's error.
- **Filler:** while task demand is insufficient, the protocol has miners produce dense-random
  MatMul = **pure-PoW mode** (Pass's Bitconia). The chain **survives under every condition**; this is
  the exact counterpart of Demirel's "null-demand projection" requirement.
- Attack cost = **PR/2**, whatever the demand may be (Pass). Economy: tail emission + 5% treasury.

**LAYER U — UTILITY (a fee-paid verifiable-compute market; E exogenous by construction):**
- The client commits the task + fee to the chain **first** (escrow, containing an **irrecoverable
  burn component** — Demirel's "irrecoverable tax"). Demand is **external** because of the payment;
  the matrix content is **determined by the client**, not by the miner.
- The task is assigned to a miner **with a VRF** (against grinding/collusion); the miner produces a
  full zkVM/STARK proof **for that task**. Utility: (a) **frontier-AI governance proofs**
  (arXiv 2606.05433 — regulators audit cumulative training compute, and the audit relies on
  self-reporting; verifying the real GPU computation via a native BF16/FP32 precompile, on a ~36-month
  horizon); (b) **provable inference** (a 1.469% hidden surcharge in reasoning is undetectable,
  arXiv 2605.30040).
- **Cornerstone:** the U layer **cannot determine leader election** — only a **bounded, unpriced
  boost** (Demirel Corollary 4) and fee revenue. Security always comes from the G layer.
- **Anti-aggregation (arXiv 2505.21685):** a per-block useful-fee cap `C_fee` + tasks spilling over
  into later blocks (preventing miners from gathering every high-fee task into a single block).

### 3.3 Chain binding and task lifecycle
- **ctx binding:** every solution's statement contains `selected_parent ‖ miner_pubkey ‖ task_ref ‖
  height ‖ proof_system_id ‖ nonce` → **precompute/replay is impossible** (T-A2, spec §A.3).
- **U-layer lifecycle:** submit+fee+burn → escrow → VRF assignment (epoch seed, N-64 blocks earlier)
  → proof → block inclusion → `W_s`-block fraud window → settle (fee + reward); a fraudulent proof →
  bond slash + a reward to the challenger. Full pseudocode: `KOK_V2_TECHNICAL_SPEC.md`, Annex A.
- **Measurement obligation:** Pearl's failure showed that the question "is the miner software doing
  inference?" must be answered **with evidence**. For the U layer, KÖK publishes the on-chain
  **φ (useful-task ratio)** and the fee-burn volume (spec §C.4).

---

## 4. Security Model (Theorem Skeletons)

- **T1 (Statement binding):** Because `ctx` is embedded in the statement, a proof is valid only at a
  specific chain position and for a specific miner key; **replay and precompute are impossible** (the
  chain hash cannot be known in advance). Reduction: otherwise, the determinism of the FS transcript
  would be violated.
- **T2 (Prescribed hardness):** Under KW (ePrint 2025/685), the work cost is `h(n) = Θ(n³)` FLOPs and
  **is independent of the input choice** — there is no structured-matrix/easy-instance shortcut.
  Resistance to FMM (ω<2.371177) is claimed by KW. **Dependency:** this rests on KW's low-rank random
  linear equations conjecture (§3.1); independent review + an emergency fallback are required.
- **T3 (Soundness):** For STARKs the soundness error is `2^-λ`; for the parameters `λ ≥ 128`, a single
  proof suffices (with additional amplification under aggregation). The under-constrained circuit risk
  is addressed by automatic **solution-set cardinality** verification in the **ZEBRA**
  (arXiv 2609.15020, Sept. 2026) style + AIR soundness in **Lean** (the S-two model, arXiv 2606.04311)
  + independent audit. (ZEBRA found 11 zero-days in 5 real zkVMs; this is the real attack surface.)
- **T4 (Economic attacks):** Pass (arXiv 2606.06700): **once equilibrium prices are taken into
  account, the cost of a majority attack remains tied to the block reward** (`PR/2`, in every
  regime); the "pay the attacker" straw man collapses. The design targets the **Fortessia regime**:
  duplex work increases security without changing the useful output. The parameters (`θ`, `α`, `γ`)
  are published through on-chain simulation (spec Annex C).
- **T5 (DAG incentives):** GHOSTDAG's random transaction selection is not a Nash equilibrium
  (arXiv 2109.01102, 2305.16757; ACNS 2025 / 2501.10888). KÖK makes the task/tx selection rule
  **protocol-determined** (not free), adds protocol-controlled commitments and a small-block penalty
  against the pooling tendency, and continuously regression-tests against the ACNS 2025 solver for
  selfish mining.
- **T6 (ASIC / hardware):** Because the work is the **MatMul that GPUs already perform** (KW 1+o(1)),
  there is **no natural market** for special-purpose mining ASICs — miners are consumers of AI
  compute, and their hardware retains its value after an attack (Pass §1.8's GPU-vs-ASIC stock
  analysis). Matmul-ASIC centralization (v1's fatal weakness) is structurally reduced; nevertheless,
  single-address and pool-share metrics are published continuously (spec §C.4 alert).

---

## 5. Difficulty, Block Production, and Verification Cost

- **Block validity:** (i) a valid proof for the assigned task, (ii) `H(FS_digest ‖ nonce) < target`,
  (iii) the GHOSTDAG ordering rules.
- **Memorylessness:** The expected number of attempts is `1/p`, `p = target/2^256` → the intervals
  are exponential; **the retarget algorithm is of the same form as Bitcoin's** (using DAG height
  instead of a 2016-block window).
- **Difficulty unit:** "expected proof-FLOPs" — verifiable, not manipulable.
- **Retarget design (2026-09-20, an honest alternative from Pearl):** KÖK v2 uses a **window + median
  filter** (`Λ̂ = D·W/T_act`, 4× clip, median; RT-1..RT-3 verified). Pearl uses **WTEMA** (weighted
  transposed EMA, per-block, 7-day decay) — an adjustment at every block, with no windowed lag.
  **Both are defensive:** WTEMA reacts faster but fully reflects a single slow block (lowering D);
  window+median is slower but robust against sudden one-off anomalies. The KÖK v2 specification
  **keeps WTEMA as an alternative to B.3** (both are run and compared on testnet; as decision data).
- **Production parameter ranges (taken from Pearl §4.8, as a starting point for the KÖK G layer):**
  rank `r ∈ {32..1024}`; `16r ≤ k ≤ 4r²`; `k ≤ 2¹⁶`; `64 | k`; `h·w ≥ 32`; `k(h+w) ≤ 2²²`;
  `m, n ≤ 2²⁴`. KÖK takes these as **testnet calibration**, not as fixed values (TV-2's
  prescribed-hardness criterion is re-run for every range).
- **Verification asymmetry (with real numbers):** ZK-ACE Circle STARK backend: **14.5 ms prove /
  1.1 ms verify / ~107 KB proof** (2603.07974); for general programs, a zkVM (Prezta, RISC Zero):
  prove in tens of seconds / verify in tens of ms (2607.11466). **Aggregation:** with per-block STARK
  aggregation, the consensus-visible data is **~160 Byte/tx**.
- **Validator cost:** 1.1 ms verify per block; even at the 10 BPS target this is ~11 ms per second —
  sustainable. **Important correction:** there is no "validators spend no energy" brag here; a
  realistic cost table is part of the spec.

---

## 6. Arithmetic and Determinism (where v1 said "Unsolvable")

- **Today:** all provable work is **finite-field / fixed-point** + a **published error budget**. For
  FP workloads, if the error threshold is exceeded, the task is rejected; this is the definition of
  "verification-grade compute" (the premium niche).
- **Tomorrow (a concrete path):** once the zkVM + **native BF16/FP32 precompile** (arXiv 2606.05433,
  **verified**: Peigné–Nguyen–Wang, "Zero knowledge verification for frontier AI training is
  possible", v2 2026-08-22, 44 pages) matures, the proof verifies **the real floating-point
  computation that the GPU performed**. The paper: a pre-committed training spec + inter-node network
  observations + on-the-fly Merkle commitments + zkVM native BF16/FP32 precompiles; three proof types
  (genesis / in-training step / ex-ante attestation); the claim of a **~36-month deployable PoC with
  single-digit-percent training-side overhead**, a 6–10-year cycle against custom silicon; and a
  catalog of 13 open problems. This becomes KÖK's **planned, versioned transition** (it fits the
  machinery in §7 exactly).
- **Determinism:** a pinned harness (kernel versions, reduction order, seed) + a Merkle trace
  commitment; for GPU non-determinism (Hawkeye, MLSys 2026), **third-party reproduction audits** are
  required; lossless reproduction of the same result on CPU is the protocol standard.
- **★ Two paths (2026-09-20, from Pearl as the primary source; full table in spec §A.9b):**
  **Path A = Hawkeye bit-exact replay** (MLSys 2026, in production on the Pearl mainnet;
  *Komargodski is an author of both KW and Hawkeye*) — **the decision for Phase 2**. **Path B = the
  Peigné native-FP zkVM** (~36 months) — Phase 3. **Honest risk:** Path A ties KÖK v2 to GPU
  generations (an sm90 whitelist); whitelist-expansion governance must be defined in Phase 2 (the §11
  ASIC-centralization concern is real, but manageable).
- **★ The structural difference of Pearl's FP scheme:** in Pearl, entrywise quantization is
  non-linear (`Q(A+N) ≠ Q(A)+Q(N)`) → the low-rank shortcut breaks → **the ticket directly hashes the
  output tile, and an (n/r)³ transcript is not needed**. KÖK's INT kernel must remain
  transcript-dependent (in INT, the shortcut is open, and it is the subject of Assumption 6.4); the
  transcript-free design is deferred to FP (Phase 3). **The Jackpot policy (TV-11..TV-14) is built on
  top of Path A.**

---

## 7. Future-Proofing: Crypto-Agility at the Right Layer

Migration is four layers (a summary of DEGERLENDIRME_100.md §7), and only **layer A** is PVI's
responsibility:

| Layer | Policy |
|---|---|
| **A. Proof system / verifier** | PVI + **versioned schema** + **dual-verification window** (old+new for N epochs) + **formal gate** (Lean + ZEBRA-class automatic verification + audit) + **a 6–12-month lead-time for miners**. Rule: *if only the verifier changes, **the work function must remain fixed*** — "seamless" is only true if this holds. |
| **B. Work function** | **Never change it if at all possible.** If it changes, it is a **hard fork** and it resets miner capital (the lessons of BTC SegWit/BCH and the ETH merge/ETC). A change requires at least 12 months of signaling + a phased rollout + optional coexistence with the old chain. |
| **C. Signatures & hash** | **PQ from today:** STARK/hash are already PQ; signatures are **ZK-ACE** (identity-bound ZK authorization, with no signature object on-chain → escaping kilobyte-scale PQC artifacts). Changing the hash = the most disruptive action; only in a pre-committed emergency. |
| **D. Difficulty assumption** | **The real risk that v1 missed.** With KW, prescribed hardness is independent of the input (no structured-matrix shortcut); resistance to FMM (ω<2.371177) is claimed. **The precondition of agility is that the hardness be structural** — KW provides this, plain Freivalds does not. |

**The emergency machine:** a **backup proof system** committed to the chain in advance; if a soundness
error or a break is reported (hardness monitoring + responsible disclosure), `proof_system_id` changes
through threshold activation, and the old verifier is retired. This is communicated as **"not zero
downtime, but planned minimal downtime"** — claiming otherwise would be false (v1's error).

**What can never be migrated without a fork (honest list):** the work function; the emission policy;
the PoW hash; the address/signature format. Migration plans for these are written **in advance**.

### 7.1 ★ Lessons from Pearl's two real hard forks (2026-09-20, primary source)

The Pearl mainnet has hard-forked **twice** (`docs/moe-fork-upgrade-guide.md`,
`docs/salted-seed-fork-upgrade-guide.md`). These are not theory but **the production procedures of a
live chain** — and they provide a **classification table** for layer A of KÖK v2's §7:

| | **MoE fork (V1→V2)** | **Salted-seed fork (V2→V3)** |
|---|---|---|
| What changed | dense → MoE certificate (the utility space widened) | the noise seed derivation was bound to the matrix dimensions with **keyed BLAKE3** (against grinding) |
| **Old miner kept working** | **YES** — "old dense proofs work before and after the fork" | **NO** — "everything must be upgraded: node, ZK proving code, **and miners**" |
| Upgrade mandatory for | node + ZK proving code (only) | node + proving + **miners** |
| Fork height | (TBD in the guide; as inferred from V3, it took place) | **Mainnet 99,000** / Testnet 38,484 |
| Commitment | `double_sha256(cert_version_le32 ‖ public_data)` — **version-prefixed** | same, prefix 3 |
| Template mechanism | `getblocktemplate` → `requiredcertversion`; **"don't hardcode the fork height, read it from the template"** | same |

**★ The classification rule (the pattern taken into layer A of KÖK v2's §7):**

> **If the derivation does not feed mining itself → backward-compatible (soft-ish); if it does →
> mandatory (all layers).**

Pearl distinguished this empirically: because MoE only changed the certificate *format* that the
*verifier* sees, the old proofs were still valid; because salted-seed changed *how the noise is
derived* — which directly affects what the miner computes — the old miner software produced **invalid
shares** after the fork. **KÖK v2 settles this distinction in advance:** for every layer-A change, the
question "does the derivation feed mining?" must be answered in the spec; if the answer is YES, then
the upgrade chain (node→prover→miner) and the **fork height are published in advance** (like Pearl's
Testnet/Testnet2/Mainnet table); if the answer is NO, the old miners keep running in parallel for one
epoch (the dual-verification window).

**Three concrete mechanisms adopted:**
1. A **version-prefixed commitment** `H(cert_version ‖ public_data)` — production evidence for KÖK's
   ctx-binding (T-A2): Pearl had to strengthen the binding *in two consecutive forks*.
2. The **`requiredcertversion` template field** + the "don't hardcode it, read it from the template"
   rule — the live precursor of KÖK's `proof_system_id` mechanism: the node publishes it, and the
   miner/pool reads it.
3. **`check_cert_version_eligible` + the `*_for_cert_version` dispatchers + pinned test vectors** — an
   **implementation recipe for KÖK's Phase 2**: a separate prover cache per proof-system version, a
   `deserialize_compat` that accepts both the old and new formats, and the pre-fork rule "an MoE share
   is invalid" (wasted hashing).

**The main lesson (utility expansion vs. security repair):** with the MoE fork, Pearl **widened its
utility space** (dense → MoE = a new harness = new utility). **KÖK v2 does this without needing a
fork:** because the U layer is task-oriented, a new inference harness (MoE, FP4, training) is added as
a **new task type**, without touching the G layer. **Only a security repair** (seed derivation,
commitment strengthening) requires a fork — and Pearl announced that in advance too, carrying it out
with pinned test vectors.

---

## 8. Economics and Monetary Policy (according to 2026 realities)

> **2026-09-19: the claims of this section are now supported by an executable
> simulation** — `pass_sim.py` (closed-form solver of Pass 2606.06700, Pearl-calibrated;
> output `sim_out.txt`). Below, **measured** values are bold, theoretical expectation in
> parentheses.

- **Calibration (the strongest verification hook):** Pearl's **live** network (320,000 GPUs, 800
  blocks/day, 2,674 PRL/block, $0.76) was reproduced with the model's Tullock full-payment
  condition `eS = PR`: **S = PR/e = 338,707** vs measured 320,000 GPUs — **5.8% deviation**;
  revenue/cost **1.058** vs Basu's measured **1.06**. So the model predicts a real mainnet from
  first principles, not with tuned parameters.
- **Emission:** **tail emission** — a decreasing but **never zero** block reward (Monero/Grin
  tradition). The Kaspa curve that v1 copied is **exhausted** in 2026 (96.5% of the max supply
  mined, ~$40M remaining). The security budget must not fall to zero on an infinite horizon.
  *Measurement (sim §5):* with the halvings the economy descends Duplexia → Fortessia (~14th
  year) and the attack cost settles at the **$0.76 floor** with tail `R_∞ = 2` PRL — it does
  **not** go to zero as in Kaspa.
- **Treasury:** **5–8% of block rewards** to a development fund (escrow + milestone-gated
  vesting). It does **not** contradict fair launch (Kaspa ran this way too); no VCs, no
  premine, no free tokens to the founder. Without this, the R&D in §11 cannot be financed.
- **Task-fee market:** clients pay a task fee (duplex model); miner = task fee + block reward.
  **When demand is zero, difficulty is maintained with (c)-class pure-PoW filler**; this regime
  is written in the spec (Pass's "Bitconia" descent).
  *Measurement (sim §6):* if demand collapses (`K→0`), `Q→0` but **S → PR/e = 338,707** — the
  chain lives on as pure-PoW, security stays Bitcoin-equal (Demirel Thm 2 ✓). **Utility is
  zero, security is not** — the formal admission that the "useful work = security" promise
  does not hold.
- **Targeted regime:** **Fortessia** (security increases, useful output preserved). The
  parameters (`token-inference ratio`, duplex overhead) are published and audited with
  on-chain simulation.
  *Measurement (sim §3):* at the same θ, security increases by a full
  **1/(γ(1−1/α)) = 3.33×**, useful output unchanged (matching theory exactly; α=γ=1.3).
- **Attack cost:** **PR/2** in every regime (Pass Thm). *Measurement:* with heterogeneous cost
  (b=1), even though total S drops 38%, the current attack cost is still **PR/2 = $1,016** —
  stock effects (hardware resale value) are outside the model, an open limitation of Pass.
- **The bitter lesson from Pearl:** Pearl's real PR level implies an endogenous **θ = 1.05 → a
  pure Duplexia** regime; that is, its economy was in the regime where it **should have
  subsidized inference** — yet the measured **φ = 0**: no utility ever materialized. The reason
  is the **E-gap** (Demirel 2026/1492): the protocol could not certify that the matrices were
  anyone's job. **Pearl behaved like Bitconia and was marketed as Duplexia.** KÖK v2 bakes
  this gap into the architecture via the G/U separation (§3.2).
- **Commitment:** the emission curve is published once and **cannot be changed in the future**
  (a change is the strongest broken trust signal; please remove v1's laxness of "to be
  finalized before launch").

### 8.1 ★ The market — what is measured, and what remains a guess (2026-09-21)

This section states a market size from primary evidence, and then says exactly where that
evidence stops.

**The size of AI compute spending (cited, verifiable):** the single cleanest proxy is the revenue
of the dominant GPU supplier — it is a tax-aware count of how much the world pays for the hardware
that AI compute runs on. NVIDIA's revenue, from its own reported figures:

| FY | Revenue (bn $) | Net income (bn $) |
|---|---|---|
| 2023 | 26.9 | 4.3 |
| 2024 | 60.9 | 29.7 |
| 2025 | 130 | 72.8 |
| **2026** | **215** | **120** |

That is **an 8× increase in three years**, and it is still accelerating: Q2 FY2027 revenue was
**$96.2B, +106% year-over-year** (from $46.7B). The build-out is equally visible in commitments:
NVIDIA's memorandum of understanding to invest **$100B in OpenAI** carries an undertaking to build
new AI data centers of **at least 10 GW** of system power; NVIDIA also invested **$2B** in the AI
cloud provider Nebius (2026). *(Source: NVIDIA's reported figures as compiled in the cited
secondary record, 2026-09-21; each figure is re-checkable against NVIDIA's own earnings releases.)*

**What this evidence does NOT establish, and the paper does not claim:**
1. It is **not** the total AI market — it excludes energy, facilities, integration and labour,
   which sit outside the chip supplier's revenue. The true spend is larger; the growth rate is the
   useful signal, not the absolute ceiling.
2. **Nothing here prices a permissionless task.** The subset of this market that would settle as a
   fee-paying task **on a public L1 is unknown** — it is not 1% of the above, nor 0.1%; it has
   never been measured, because no chain has yet offered it as a priced market. **F3a (§10.1)
   exists to measure it**, and §10.2 explains why F3a is deliberately the cheapest decision point.

**Why the discipline matters:** a pre-testnet paper that quotes a TAM forecast would be quoting a
vendor's promotional number, and an academic reader who checks the footnote would find it. The
figures above are reported earnings — they survive the check. **The honest market claim is:
"the spend exists and it is growing at ~100%/yr; the addressable permissionless subset is unknown,
and we intend to measure it rather than to assume it."**

---

## 9. Law and Compliance

- **The phrase "AI-indexed" has been removed.** In its place: **the protocol is a
  verifiable-computation settlement layer**; the token's value depends on network security and
  the task-fee market. Per the Howey analysis, this framing weakens (but does not eliminate)
  the "promise of investment return."
- **TR:** the crypto-asset service provider licensing regime (in force since 2025) applies to
  listing/custody; the status of mining and fair-launch promotion must be clarified by legal
  counsel as a separate heading (**not verified** in this document; it is an open item).
- **EU/AI Act + US compute reporting:** this is the **regulatory tailwind** of the
  governance-proof market in §3.2(a); room is reserved in the risk register for the opposite
  wind (the verification demand remaining unregulated) scenario.
- **Protocol ↔ promotion separation:** the protocol is open source and independent of the
  team; the promotion contains no promise of return. "AI washing" actions (SEC) are the main
  edge.
- **★ 2026-09-20: Pearl's intersection with Polymath Economic (2) — a compliance advantage or
  a risk?**
  Pearl itself lists three applications: **(a) a voting system for AI agents** (async
  coordination, GPU funding, a compute marketplace), **(b) model tracing** (retroactive
  inference proof, ZK), **(c) "a stablecoin for compute"** ("if Bitcoin trades energy outside
  the dollar system, Pearl trades compute"). KÖK v2's escrow+burn task market **could be the
  infrastructure for (a) and (c)** — but this is an area the document **deliberately defers**:
  **(a) voting = an on-protocol application**, not within KÖK v2's scope (the protocol
  provides only the task market + consensus; the application layer belongs to third parties).
  **(c) compute-stablecoin is something KÖK v2 consciously does not claim** — the word
  "stable" is used not as a promise to peg a token to compute, but only in the sense of
  "opening compute to trade with a token." **Legal discipline: KÖK v2 promises no
  application; only infrastructure.**
- **★ Regulation is not mandatory, but compliance is an advantage.** Polymath's "model tracing"
  application and KÖK v2's provable-inference tasks satisfy **the same regulatory demand** (EU
  AI Act article-level documented compute; US compute reporting). That is, KÖK v2's U layer,
  if regulation arrives, **is already compliant infrastructure** (first-mover advantage); if it
  does not, **utility demand is optional** (the G layer stands regardless). **This allows KÖK
  v2 to position regulation not as a risk but as an option** — the worst case is "just an
  honest GHOSTDAG PoW" (§11 item 3).
- **★ 2026-09-21: the MiCA classification, verified against the official text.** The utility-token
  route was checked against Regulation (EU) 2023/1114 (MiCA) as published in the Official Journal
  (EUR-Lex, CELEX:32023R1114, L 150/40, 9.6.2023; in force 30 December 2024). The relevant
  definitions, quoted verbatim from Article 3:
  - **(5)** "‘crypto-asset’ means a digital representation of a value or of a right that is able
    to be **transferred** and stored electronically using distributed ledger technology or
    similar technology;"
  - **(9)** "‘utility token’ means a type of crypto-asset that is **only intended to provide
    access to a good or a service supplied by its issuer**;"
  - **(6)** "‘asset-referenced token’ means a type of crypto-asset that is not an electronic
    money token and that **purports to maintain a stable value** by referencing another value
    or right or a combination thereof…"

  **Honest consequence:** KÖK v2's token is **not** a utility token under (9). It grants access
  to verifiable compute, but it is also **mined for a block reward** — a value and a right under
  (5) that is not "only" access. The honest classification is therefore **"crypto-asset, other
  than an asset-referenced or e-money token"** — MiCA's third category — with the white-paper
  disclosure duties that follow, including the verbatim requirement that the paper state:
  "the crypto-asset may lose its value in part or in full; (b) the crypto-asset may not always
  be transferable; (c) the crypto-asset may not be liquid; (d) where the offer to the public
  concerns a utility token, that utility token may not be exchangeable against the good or
  service…"

  **What this changes in the design:** nothing structural, and that is the point. MiCA imposes
  **disclosure duties on the offer**, not a prohibition on mining-based distribution. The
  fair-launch, no-premine, no-investor structure of KÖK v2 is what keeps the disclosure surface
  small. **What it does not solve (open):** the jurisdiction question — MiCA binds the EU offer,
  not the anonymous issuer.

- **★ 2026-09-21: the US side is no longer an internal analysis — the case law is now cited.**
  The SEC v. Ripple record was retrieved and the sequence is material to this design:

  - **13 July 2023 — Judge Analisa Torres, summary judgment.** The court **distinguished the asset
    from the circumstances of its sale**: Ripple's *institutional* sales were unregistered
    investment contracts, but its **programmatic sales on exchanges were not**, because purchasers
    on an exchange did not reasonably expect profits derived from the efforts of others.
  - **7 August 2024 — final judgment:** civil penalty of **$125,035,150** for the institutional
    sales, plus an injunction.
  - **2025 — the parties asked to dissolve the injunction and cut the penalty to $50M; the court
    refused**, finding no exceptional circumstances. On **7 August 2025 both sides withdrew their
    appeals. The case is closed.**
  - **17 March 2026 — the SEC issued a new interpretation** (with CFTC guidance; published in the
    Federal Register 23 March 2026) identifying **XRP alongside bitcoin, ether, solana and stellar
    as digital commodities**, whose value derives from *functioning crypto systems and supply and
    demand* rather than from expectations of profit from others' managerial efforts. It also said
    explicitly that **a crypto-asset which is not itself a security can still be offered or sold as
    part of an investment contract, depending on the circumstances of the transaction.**

  **What this means for KÖK v2 (the legal reason for the fair-launch):** the 2023 holding and the
  2026 interpretation both support the position that a token distributed by mining and sold on
  exchanges is **not** an investment contract — there is no purchaser relying on an issuer's
  efforts, and the value derives from the functioning system. **But the SEC's own caveat is the
  operative constraint:** the same token *becomes* a security when sold in circumstances that do
  create that expectation — a presale, an investor round, or a treasury allocation marketed on
  expected issuer effort. KÖK v2's **no-premine / no-investor** structure is therefore not a
  stylistic choice; it is the specific design feature that keeps the protocol on the commodity
  side of the line the SEC drew. **Honest limits of this analysis:** it is a reading of US
  precedent applied to a not-yet-existing token, by non-lawyers, and it is not a legal opinion;
  the jurisdiction decision and a formal securities opinion remain pre-launch items (§10.2).

---

## 10. Proof, Audit and Roadmap

| Phase | Content | Criterion (defined success) |
|---|---|---|
| **F1 — Formal spec** | statement schema, task market protocol, GHOSTDAG+rejection-sampling spec, economic model | Walk-through by independent cryptographers; T1–T6 skeletons. **✅ complete on paper: `KOK_V2_TECHNICAL_SPEC.md`** |
| **F1b — Working prototype** | task lifecycle + penalty economics + difficulty retarget | **✅ `u_layer_prototype.py` (TV-5..TV-10), `g_layer_tests.py` (TV-1..TV-4, RT-1..RT-3) — all PASS** |
| **F2 — Soundness verification** | verification of the AIR with Lean + ZEBRA-class cardinality check | Under-constrained bug = 0 (third-party audit) |
| **F3 — Devnet** | `kok-node` (Rust), S-two/Circle STARK verifier, task market, filler tasks | 10 BPS, verify ≤2 ms/block, difficulty approaches the target in 7 days |
| **F4 — Economic simulation** | on-chain simulation of Pass's model (3 regimes) | Controlled transition to pure-PoW mode in the zero-demand scenario. **✅ closed-form solver: `pass_sim.py` — Pearl calibration 5.8%, Fortessia ×3.33, zero-demand S→PR/e, tail $0.76** |
| **F4b — Cryptographic analysis** | independent assessment of the KW conjecture | **✅ `KW_ANALIZ.md`: risk high → low-medium (Assumption 6.4 not needed; the real risk is the E-gap)** |
| **F5 — Testnet + miner** | open testnet, `kok-miner`, ecosystem task channels | 1000+ miners, demand paying for ≥1 of the real (a)/(b) tasks |
| **F6 — Audit + mainnet** | 2 independent security audits + bug bounty | No critical findings; miner ecosystem stable for 6 months |

### 10.1 ★ Testnet roadmap — specifically an "off-protocol testnet" (2026-09-20)

The strategic conclusion of §12.1 says this: **what needs to be fast is not the architecture,
but getting the prototype onto an off-protocol testnet** (against the risk of Pearl expanding
its utility surface). Therefore we split F3 into **two sub-phases**:

| Phase | Content | Criterion | Duration (target) |
|---|---|---|---|
| **F3a — Economy testnet (off-protocol)** | Only the **U layer**: task market + escrow/burn/slash + VRF assignment, **without consensus** — a central sequencer (mock leader) produces blocks, a dummy proof in place of the G layer. Tokens are test tokens. Goal: **to measure real demand and the penalty economy** — this is KÖK's least-measured assumption (φ>0). | ≥1 **real paying** task; a slashing-triggered attack case; escrow refund rate measured | **3–4 months** (in parallel with the cryptographer review) |
| | **★ Working prototype (2026-09-20): `f3a_sequencer_proto.py` — TV-15..TV-19 all PASS: refund-guarantee, task-migration, censorship-freeness, dilemma-free verification, honest lifecycle.** The toy limits are in the file. |
| **F3b — Consensus devnet** | `kok-node` (Rust), GHOSTDAG parent-set selection, KW per-tile G layer, difficulty retarget (window+median), filler tasks (φ=0). **The entire protocol**, with real proofs. | 10 BPS, verify ≤2 ms/block, difficulty approaches the target in 7 days (F3's original criterion) | **4–6 months** after F3a |
| **F5 — Open testnet** | The two are merged; `kok-miner`; ecosystem task channels. | 1000+ miners, demand paying for ≥1 of the real (a)/(b) tasks | **3–4 months** after F3b |

**★ Why F3a first (honest justification):** the success of F3b (cryptography) depends on the
outcome of `KOK_V2_CRYPTO_BRIEF.md` and is **exogenous in timing** — we cannot accelerate it.
F3a carries **zero cryptographic risk** (dummy proof) and measures KÖK's **largest unmeasured
assumption** (φ>0: will anyone pay a fee for real AI inference?). Our answer to Pearl's φ=0
result must be **architecture + real demand measurement**; architecture alone is not enough.
**Moreover, F3a is the only way to test market validity before the G layer is ready** — if
nobody pays, it is learned **before investing in F3b** that KÖK v2 would be "not a revolution,
but an honest GHOSTDAG PoW" (§11 item 3).

**★ Measurement metrics (F3a, published on-chain):** average fee per task; escrow holding
time; number of slashing events; **ratio of real paying users** (what % of total tasks are
real AI workloads); number of verifier's-dilemma triggers (spec §A.5).

**★ HONEST LIMIT (found during the hook test, `pass_sim.py` §9):** F3a's small-network data
(~1200 miners) **cannot recalibrate** `pass_sim.py` — the model rests on Pass Thm 2's
"competitive equilibrium" assumption, and in small networks fixed costs dominate marginal
costs (hypothetical test: **86% deviation**). Pass's own calibration rests on a $30B inference
market and 52,560 blocks/year; F3a is outside this scale. **Therefore F3a's role is clear:**
it measures the U layer's demand (φ>0) — **not the Pass model**. The Pass calibration is
valid **at mainnet scale** (proven with Pearl at 5.8%), and the **expected** zero-φ result
from F3a is consistent with the model's "Bitconia" descent; it does not calibrate it. This
was pinned with a working regression-guard in §9 of `pass_sim.py` (Pearl 5.8% preserved).

**★ Risk (honest):** F3a's central sequencer **limits the test's real value** — a central
sequencer can censor, and this does not measure the U layer's **censorship resistance**.
Therefore a **censorship-resistance criterion** is added to F3a: when the sequencer
deliberately rejects task X, it is shown that the (task owner → alternative sequencer →
refund) path works. This is a **temporary** centrality that will be replaced by GHOSTDAG in
F3b, and it is written explicitly in the document as a "test limitation."

### 10.2 ★ Budget — the honest constraint (2026-09-21)

Every roadmap above names durations but no cost. The constraint is not modesty — it
is **structural**, and it shapes the design:

| Item | Cost | Constraint |
|---|---|---|
| **F1/F1b/F4b (spec, prototypes, analysis)** | ~0 (compute time) | **Already done.** The paper, spec and 7 runnable prototypes are the entire output of this phase. |
| **F3a (economy testnet)** | 1 VPS + ~200 dev-hours | Can be done **by one person** in 3–4 months. This is the cheapest decision point in the entire plan, and it is deliberately first. |
| **Cryptographer review** | $0 — **deferred payment** | The reviewers are external academics; while the project is anonymous **compensation is hard or impossible** (no bank account, no legal entity). Payment is deferred to post-funding, which means **the review timing is not ours to control** — it is the single largest schedule risk. |
| **F3b (consensus devnet)** | 2–3 engineers × 6 months + test GPUs | **Not fundable today.** Requires either funding (breaks anonymity) or a grant program (requires a legal entity). This is the hard gate. |
| **F5/F6 (testnet, audits)** | 2 security audits ≈ market rate; 1000+ miners implies ecosystem traction | **Not fundable today.** Audits before mainnet are non-negotiable; an unaudited mainnet with a bond market would be reckless. |

**What this budget says, plainly:** KÖK v2 can reach **F3a and a review** without money. It
**cannot** reach F3b without either funding or a grant. The design consequence — already present,
now stated as a budget consequence rather than a preference: **F3a exists to fail cheaply.** If
F3a shows nobody pays for tasks, the project stops having spent one person's time; if it shows
real demand, that evidence is the only thing that could justify the F3b raise. **No promise is
made here about reaching mainnet.** The honest statement of intent is: reach the measurement,
publish the result either way.

**Anonymity is a means, not a value:** it exists because the project is pre-testnet with no
users or funds to protect. The moment a legal entity exists (for audits, exchanges, or
compensating reviewers), the cost of anonymity exceeds its benefit and it should be dropped.
This is a decision deferred to the funding event, not a commitment to permanent anonymity.

---

## 11. Known Limits and the Ceiling of the Paper

There is no dishonest 100/100 claim; this document acknowledges the following:

1. **Energy is still spent and "useful work does not increase security."** Three papers from
   2026 compelled this: the SoK (2025/1814) states "utility does not contribute to the
   security budget"; Demirel (2026/1492) proved that leader election must be
   **demand-independent** (Thm 2); Basu (2606.04819) measured that **Pearl's 24 EH/s live
   network produced zero useful computation**. KÖK v2 honestly bakes this into the
   architecture: security is demand-independent (G layer), utility materializes only in the
   **fee-paying** U layer. **"Useful = secure" is not for sale.**
2. **The cryptographic dependency is at a single point:** KW's prescribed-hardness security is
   a **conjecture** (low-rank random linear equations). If it fails, the network falls back to
   pure-PoW (spec §A.9), but the "useful work" claim dies at that moment. **After the
   2026-09-20 PDF verification, the risk is low-medium:** `KW_ANALIZ.md` §6 extracted verbatim
   that KW *himself* says, for Assumption 6.4, "the number of bits needed to write down all
   intermediates – **Θ(n³/r)** – is always a lower bound on the running time" — so the
   assumption is satisfied almost automatically by a standard **output-size lower bound** (the
   same conclusion as my independent §3.1 observation). Additionally, Lemma 6.5 (E,F uniform
   rank-r in the ROM) and the **α = o(1)** overhead were confirmed verbatim. Conjecture A.1
   (the random-rotation alternative) is **still unproven** — Pearl's own Polymath Problem (1)
   asks "Is this secure?"; the main body does not use it. All structural attacks and the
   trapdoor-matrix literature were refuted. **But this is an LLM reading — 2 independent human
   cryptographer reviews are still mandatory** (F2/F6).
3. **U-layer demand risk:** governance-proof and provable-inference demand **depend on
   regulation and market trend**. If they do not materialize, the network becomes "just an
   honest GHOSTDAG PoW" — which is still a better position than Kaspa (emission exhausted)
   and Pearl (utility claim collapsed), but **not a revolution**.
4. **Core sharing with Pearl:** both use the KW construction. KÖK v2's contribution is
   **accepting the E-gap and baking it into the architecture** — which Pearl could not do.
   **2026-09-19 primary-source correction:** Pearl's own §7 benchmark shows that the coupling
   can be without overhead (Pearl-certified Llama 3.3 70B, +12.7% faster than Meta's, 806
   TMADs/s of useful work). So the reason for the live-network-measured φ=0 is **not overhead
   but workflow alignment**: the certified path requires running specific models with a
   plugin, while the permissionless miner's optimum is raw filler; the useful work occurs in
   Pearl's **separate** hosted-inference business. Pearl's shortcoming is not technical but
   **architectural**: leaving the marketplace in whitepaper §1 as a future vision (no
   escrow/bond/burn/anti-aggregation). KÖK v2 builds this — details in §12.
5. **FP verification: two paths, neither yet working in KÖK.** The Pearl path (**Hawkeye
   bit-exact replay**, MLSys 2026, in production) is **proven today** but ties KÖK v2 to GPU
   generations (sm90 whitelist; the governance for extending the whitelist is undefined — this
   sub-item itself is a limit). The native zkVM path (arXiv 2606.05433) has a **~36-month**
   horizon. Until then: fixed-point + error budget + the INT KW kernel (with transcript; the
   transcript-less design in Pearl's FP scheme was deferred to FP, spec §A.9b).
6. **The paper's ceiling is ~85/100.** The remaining 15 points **are proofs**: the criteria of
   F3–F6, the live security budget, real paying task demand, independent audits. **A perfect
   paper is not equal to a running chain** — this is written at the top of the document so
   that the perfectionism is honest.

---

## 12. Differentiation (against the 2026 state of the art)

> **2026-09-19 update:** Pearl is now compared **from the primary source** (INT whitepaper +
> live site + GitHub; see `PEARL_DOCS_ANALIZ.md`). The previous table relied only on Basu's
> measurement; now Pearl's own documents are also available.

| | **KÖK v2** | **Pearl Network (live, primary source)** | HadAgent (2604.18614) | SNARKChain (2510.09729) | Kaspa |
|---|---|---|---|---|---|
| Source of security | **demand-independent PoW** (filler + memoryless) — Demirel Thm 2 ✓ | **"useful work"** (E-gap not accommodated in the architecture) | deterministic inference | SNARK marketplace | purposeless hash |
| Source of utility | **only fee-paying tasks** (escrow + bond + **burn**) | miner's choice → **measured: zero**; utility in the hosted-inference business | inference itself | the market | none |
| Work | KW MatMul PoUW (G) + zkVM proof (U) | **KW INT kernel** (r ∈ {32..1024}, 16r ≤ k ≤ 4r²) | deterministic LLM inference | SNARK proof | hash |
| Overhead | 1+o(1) (G) / high (U) | 1+o(1); **+12.7% throughput on certified models** (its own benchmark) | 1:1 re-execution | high | n/a |
| Consensus | **GHOSTDAG (BlockDAG)**, ~10 BPS target | **Bitcoin fork: UTXO + linear longest-chain, 194 s blocks (NO GHOSTDAG)** | single chain | single chain | **GHOSTDAG** |
| Difficulty | **window + median filter** (RT-1..3 verified) | **WTEMA** (per-block EMA, 7-day decay) | deterministic | "—" | classical |
| Cryptography | **PQ suite mandatory** (TV-10) + Lean/ZEBRA + agility + emergency fallback | Plonky2 ZK (input privacy!); **XMSS reserved but disabled**; P2MR | re-exec | SNARK | hash |
| Economy | **tail emission (R_∞ floor)** + 5% treasury + Pass simulation | S=2.1M; **1/t² polynomial (no halving, R(t)→0 — NO tail)**; 24 EH/s, 1.06× revenue/cost | — | marketplace | **exhausted** (96.5%) |
| Task market | **escrow + bond + burn + C_FEE anti-agg + VRF + W_s=100** | **NONE** — marketplace in §1 as future vision | — | exists | none |
| **Novel** | **baking the E-gap into the architecture: security ≠ utility** | **first KW implementation; its own business model is effectively the G/U separation** (inference platform + chain) | PoI consensus | PoUW + binding | GHOSTDAG |

**Honest statement:** **Pearl Network is the academic-commercial owner of the KÖK v1 idea** (KW
= Komargodski & Weinstein; economics = Pass's advising) — and **it is the sole example of a
live PoUW chain.** But Basu (2606.04819) measured it: **24 EH/s, ~320 thousand GPUs, ~112 MW
→ zero useful AI computation**; verification accepts random matrices (44 pool-approved shares,
NVIDIA/AMD/CPU/Apple Silicon); there is no inference code in the miner software (0/4,803
strings); GPU rental prices +38%, a **~$600K/yr deadweight loss** to research; miners mine
for the "call option" under >200% volatility.

**How Pearl's own documents explain this (2026-09-19, important):** Pearl's §7 benchmark shows
that **Pearl-certified Llama 3.3 70B is FASTER than Meta's original** (17,206 vs 15,270 tok/s,
4×H200, PP=4; MMLU 0.8190 vs 0.8198) and produces **806 TMADs/s** of useful work — the mining
quantization library itself, so **the coupling has no cost**. So the reason for φ=0 on the
live network is **not overhead but workflow alignment**: the certified path requires running
specific models with a plugin; the permissionless miner's economic optimum is raw filler.
**The useful work occurs in Pearl's hosted-inference business (pearlresearch.ai + the 25%+
cheaper Gemma-4-31B-it-Pearl endpoint on Together AI), not in the chain's miners.** Pearl's
mistake: **marketing "useful work = security" and not baking the E-gap into the architecture**
— while its own business model is effectively the G/U separation, not binding it in the chain.
KÖK v2 builds exactly this binding: **Demirel's unrefundable burn with the task market**
(absent from Pearl's whitepaper) + **GHOSTDAG** (absent from Pearl) + **tail emission floor**
(Pearl's 1/t² goes to zero, KÖK's does not) + **mandatory PQ gate** (Pearl leaves XMSS
reserved).

**★★ Pearl's own E-gap admission (September 20, 2026, primary source):** Pearl's open-problem
page "Polymath Project" (*pearlpolymath.com*) admits in Economic Problem (1):

> "A common criticism of (0-overhead) PoUW is that the **marginal cost of mining is ~0 and
> hence also the cost of attacking the network**. However, the last statement is only true if
> one has an **infinite stream of useful work**—i.e., the ability to collect AI workloads for
> which an external consumer is willing to pay. This observation highlights the difference
> between Pearl and Bitcoin—**the key 'scarce' resource in PoUW mining is the ability to
> collect useful data (matrices)**. ... **What should be the value/price of the Pearl coin at
> 0 mining overhead? Is it 0? infinity?**"

**This quote is the primary-source verification of this document's thesis.** Pearl is aware of
the E-gap, and its defense is **economic**: "the scarce resource is collecting useful data."
But in the φ=0 world measured by Basu (nobody sends matrices) this defense **collapses** —
under demand depression the "scarce resource" cheapens and the attack cost falls; Pearl's own
question ("Is it 0?") interrogates this. **KÖK v2's answer is at the protocol level:**
Demirel's unrefundable burn fixes the security budget independently of demand. **The
difference between the two answers is the core of KÖK's "novel" claim: Pearl relies on the
mercy of the market, KÖK on cryptography.** (For all the open problems,
`PEARL_DOCS_ANALIZ.md` §11.2.)

### 12.1 Rival move scenarios (where does KÖK v2 stand if Pearl makes a move?)

Pearl's **own open-problem list** (Polymath) is a roadmap; KÖK v2's position against each must
be written **in advance** — otherwise the "differentiation" claim is specific to today:

| Pearl's move | Probability | Where KÖK v2 still differs | Threat level |
|---|---|---|---|
| **Extends to training** (Polymath 4: cuPOW inference-only; SGD robustness conjecture) | medium-high | **The U layer is task-focused**: a training task is added in KÖK as a new *task type*; the G layer and the fork are untouched. But if Pearl makes this move, **it captures the first-mover advantage** — KÖK's timing depends on Phase 2. | **HIGH timing risk** |
| **Adds a U_layer-like escrow/burn** (marketplace moved from §1 to the protocol) | low-medium | Then Pearl and KÖK v2 **converge on the same architecture**; what remains of KÖK is **GHOSTDAG + tail emission + mandatory PQ gate + WTEMA alternative**. The difference shrinks but is not zeroed. | MEDIUM (half of the differentiation erodes) |
| **Switches to FP4** (Polymath 3: NVFP4 scale optimization) | high (the natural step after FP8) | **Irrelevant for KÖK v2**: the U layer accepts every precision as a task type; the G layer is fixed at INT/FP8. Even if Pearl is on FP4, KÖK's G layer is the same. | LOW |
| **Proves Polymath (1) random-rotation** | low (they themselves question it) | Does not change the KW main body; only the Appendix A alternative. KÖK still uses the §6.5 instantiation. | LOW |
| **Solves ASIC-resistance** (Polymath 6: "1-bit hardware enough?") | medium | **CAUTION — this is open for KÖK too**: KÖK v2's G layer is also MatMul-based; a low-entropy hardware attack **affects both protocols**. **TV-21 measured (2026-09-20):** in the INT toy, the attack passes **0/10** in the 10→400 peak sweep — but we admit that this result is **not proof for FP8**: the toy's RMS-noise model points in the **opposite** direction to FP8's per-tensor scale compression (Pearl wp §5.1.2). In FP8 the noise model must be rewritten quantization-aware (Phase 3, Path A). In production, the **Hawkeye whitelist + jackpot policy** defend together. | SHARED RISK — robust in the INT toy, **OPEN** in FP8 |
| **Makes 0%-overhead whole-model PoI secure** (Polymath 7) | low (no SNARK, backdoor open) | If Pearl achieves this, it reaches the "2-for-1" meaning in full — but **it does not close the E-gap** (security still demand-dependent). KÖK v2's Demirel separation still holds. | LOW |

**★ Strategic conclusion (honest):** half of KÖK v2's differentiation **is architectural (E-gap
+ GHOSTDAG + tail + PQ), half is timing.** Pearl's Polymath list shows that Pearl **is not
approaching closing the E-gap architecturally** (no problem contains
escrow/burn/anti-aggregation); but **it is advancing in application areas (training, FP4).**
So the threat is not "Pearl becomes KÖK," but **"while Pearl expands its utility surface, KÖK
remains on paper"** — which is why the timing of Phase 2 (sharing prototype → testnet) is as
critical as the differentiation itself. **What KÖK v2 needs "to be fast" about is not the
architecture, but getting the PROTOTYPE onto an off-protocol testnet.**

KÖK v2's claim is **not** to have invented the KW core; it is to build the following layers:
**(i) independence of security from demand** (filler + memoryless difficulty → satisfies
Demirel Thm 2 at the construction level), **(ii) defining utility only via fee-paying tasks**
(E exogenous-by-construction: escrow + unrefundable burn), **(iii) GHOSTDAG parallelism**,
**(iv) a formally verified PQ agility plane** (Lean + ZEBRA + emergency fallback), **(v) a
published tail-emission economy with the Pass model.** All antecedents are attributed;
**Pearl's collapse proves that this differentiation is necessary.**

### 12.2 The name, and what it does and does not claim (2026-09-21)

The name is stated once, plainly, and with its etymology **used correctly** — an earlier draft
mixed two homographs and an academic reader would have noticed:

- **"KÖK"** is the Turkish word for **root**, in the sense of *root of a tree* and, by the
  standard mathematical extension, *root node* / *roots of unity* — the senses relevant to a
  consensus layer (the genesis block, the root of the DAG, the primitive root of a finite field).
  It is a common Turkish noun, not a mythological proper noun.
- **What it is not:** it is **not** "Kök Tengri." In Old Turkic, *Kök Tengri* is the
  **Blue/Sky God** — there *kök* is a **color word** (blue/sky), a different homograph from the
  modern *kök* = root/origin. An earlier draft conflated the two; that conflation was a real
  etymological error and it has been removed. The name carries **no religious or geopolitical
  claim**, only the tree/root image that a blockDAG naturally invites.
- **Opsec — stated as a fact, not as a promise:** the project is anonymous because it is
  pre-testnet with **no users, no funds, and no investors to protect**. That is a *present
  condition*, not a guarantee that no analyst could ever link the identity. **No unproveable
  claim is made here** ("nobody can deanonymize us" would be exactly the kind of statement this
  paper refuses to make in §11). Anonymity is a cost/benefit choice: it is dropped the moment a
  legal entity becomes necessary for audits or reviewer compensation (§10.2).
- **Geographic scope:** the name is Turkish; the protocol is not. Nothing in the design is
  jurisdiction-specific, and the paper's jurisdictional analysis (§9) is deliberately framed
  around EU MiCA and US Howey as the two regimes that matter for an offer — not around any
  national claim. A Turkish word for a universal image is a naming choice, not a positioning.

---

## 13. References (September 20, 2026, live)

> **For the verified full list + access notes: `KOK_V2_REFERENCES.md`** (ePrint PDF gives raw
> binary; use ar5iv.org for full text). **Working evidence:** `pass_sim.py` (Pass economics,
> Pearl-calibrated), `u_layer_prototype.py` + `g_layer_tests.py` (protocol prototype),
> `KW_ANALIZ.md` (cryptographic analysis), `KOK_V2_TECHNICAL_SPEC.md` (formal spec).

**Core cryptography:** ePrint 2025/685 = arXiv 2504.09971v4 (Komargodski–Weinstein, MatMul
PoUW) · arXiv 2502.13065 + 2502.13060 (trapdoor matrices, LPN — assessed as a threat,
refuted) · 2404.16349 (ADV+24, ω<2.371339) · Pearl Network (built on KW, under construction) ·
PoUW/economics: 2606.06700 (Pass, full model) · 2606.04819 (Basu, measurement of Pearl) ·
ePrint 2026/1492 (Demirel, PoD≠PoW) · ePrint 2025/1814 (SoK) · 2510.09729 (SNARKChain) ·
2505.21685 (external utilities) · 2405.19027 · 2209.03865 · 2512.13666 (SEDULity) · 2404.09005
(incentive security) · Work/applications: 2604.18614 (HadAgent) · 2606.05433 (frontier-AI ZK) ·
2605.30040 (token inflation) · 2603.19025 (SaTML) · 2602.17452 (Jolt Atlas) · 2506.11458 ·
Proof/PQ: 2606.04311 (S-two Lean) · 2603.07974 (ZK-ACE) · ePrint 2024/1731 (Arc) · 2501.05500 ·
Security/zkVM: 2609.15020 (ZEBRA) · 2605.25493 (ZK-Tracer) · 2607.11466 (Prezta) · 2603.20421
(Hawkeye = Pearl's FP verification path, MLSys 2026) · 2606.16146 (NTT vs SumCheck) ·
**Pearl primary:** pearlresearch.ai/research/int-whitepaper · pearlpolymath.com ·
github.com/pearl-research-labs/pearl · Pass 2606.06700 · Basu 2606.04819 · DAG: 2018/104
(PHANTOM) · 2109.01102 / 2305.16757 / 2501.10888 · Difficulty: 2608.16884 (ω<2.371177) ·
Market: CoinGecko (BTC/KAS/TAO/RNDR/AKT/DNX) · Digiconomist · blockchain.info
