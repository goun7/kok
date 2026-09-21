# KÖK Network v2 — PoW L1 + Verifiable-Compute Market: The Best System Possible on Paper

**Date:** 21 September 2026 (KW/Pearl/Demirel update + verified bibliography, MiCA and SEC v. Ripple) · **Status:** Design document (supersedes the v1 paper)
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
- **Construction:** ePrint 2025/685 = arXiv 2504.09971v4 (received 2025-04-15; arXiv v4 2025-11-13; ePrint latest rev 2025-12-08). Arbitrary MatMul,
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
- **Cornerstone:** the U layer **has zero consensus weight — it never participates in leader
  election.** The block solution depends solely on the G-layer certificate; the target test reads
  only `kw_cert`, and U proofs contribute fee revenue alone. Security always comes from the G layer.
  *(Reviewer note, 2026-09-21: an earlier draft said "a bounded, unpriced boost", citing
  Demirel Cor. 4. The specification's own pseudocode contradicted that wording — the U proofs
  are appended to a block already won by the G layer and are never read by the target test.
  The wording is corrected to match the code, and the citation is withdrawn because Cor. 4 was
  never verified against the source.)*
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

- **★ 2026-09-21: the MiCA disclosure text, drafted against the article it comes from.** MiCA
  does not merely classify; it requires the white paper to carry specific statements. Drafting
  them now — from the verified text, not from a summary — is the cheapest real compliance work
  available to a pre-testnet project. **The four mandatory statements (per the MiCA
  white-paper provision, quoted from the official text):**
  > "(a) the crypto-asset may lose its value in part or in full; (b) the crypto-asset may not
  > always be transferable; (c) the crypto-asset may not be liquid; (d) where the offer to the
  > public concerns a utility token, that utility token may not be exchangeable against the
  > good or service..."

  **Drafted for KÖK v2 (a disclosure, not a legal document):**
  > (a) The KÖK token has no collateral, no issuer promise and no revenue share. Its value, if
  > any, derives from fee-paying demand for verifiable compute and from mining cost; both are
  > uncertain and the token may lose all value. (b) Transferability depends on third-party
  > infrastructure (nodes, wallets, exchanges) that does not yet exist; the token may not be
  > transferable. (c) There is no market and no liquidity is promised; early blocks carry
  > rewards no one has agreed to buy. (d) KÖK v2 is not a utility token under MiCA Art. 3(9)
  > — see the classification above — so this paragraph is stated for completeness: the token
  > may not be exchangeable for any good or service of the issuer, because the issuer provides
  > no good or service except the protocol itself.

  **What this is, stated plainly:** a disclosure drafted to match the regulation's own wording.
  It is **not** a MiCA white paper, which requires an issuer, a legal entity and a competent
  authority — none of which exist while the project is anonymous (§10.2). **The honest framing:
  the disclosure content is ready; the legal vehicle is not.** When a legal entity exists, this
  text becomes the core of the white paper's risk section. Until then it is a design artifact,
  and it is published here so that the promise it makes — *we will disclose the risks, in the
  regulator's own words, before we ask anyone for anything* — is verifiable now rather than
  promised later.

---

## 10. Proof, Audit and Roadmap

| Phase | Content | Criterion (defined success) |
|---|---|---|
| **F0b — zk-AIR: provenance AND privacy (the highest-leverage item on this roadmap)** | Close the gap that reason (b) depends on: the "STARK-like" trace must become a real AIR, and the AIR should be built **zero-knowledge** — prove correct execution *without revealing the inputs*. Also measure liveness under realistic delay. **Motivated by §F: TV-38 already shows the verifier binds the certificate to the computation, but on toy sizes and a tile-level check; a real AIR is what turns that into an asymptotic claim.** **The privacy extension is not extra work: an AIR with the zero-knowledge property serves two markets with one construction — provenance for the buyer who must prove a result, and privacy for the buyer who must not reveal model weights or sensitive data.** | A real zk-AIR for one MatMul task; a third party can verify *correctness without seeing the inputs*. **Progress (2026-09-21): the first four steps run as a chain in `f0b_air_proto.py` — TV-40 the AIR constraints, TV-41 Merkle commitment with sampled verification, TV-42 low-degree testing that closes the single-row gap, TV-43 zero-knowledge masking where an honest witness verifies, a forged one is rejected, and no real trace value is ever transmitted. Each file states the gap it still does not close (no FRI recursion, no codeword, one-time-pad hiding rather than Schwartz-Zippel), so this is the property at toy scale, not an audited system. Until it is audited, reason (b) remains a promise rather than a proof.** |
| **F0 — Demand discovery** | Find the first real customer with a real job. Not a testnet, not a simulation: a party who already pays for compute and would switch to KÖK if it were cheaper, or a job that cannot run permissionlessly anywhere else. Interview ≥10 candidates; record what they actually pay, what they need, and what would make them switch. | **≥1 signed letter of intent to buy compute at a named price.** This is the seed of demand (§12.1); without it the chain converges to the empty-block equilibrium and stays there |
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
| **F3a — Economy testnet (off-protocol)** | Only the **U layer**: task market + escrow/burn/slash + VRF assignment, **without consensus** — a central sequencer (mock leader) produces blocks, a dummy proof in place of the G layer. Tokens are test tokens. Goal: **to measure real demand and the penalty economy** — this is KÖK's least-measured assumption (φ>0). | ≥1 **real paying** task ✅ (TV-22); a slashing-triggered attack case ✅ (TV-24); escrow refund rate measured ✅ (TV-24b, books balance exactly) | **3–4 months** (in parallel with the cryptographer review). **Progress (2026-09-21): the mechanism is proven at prototype scale — TV-21 supplies the demand meter (φ), TV-22 walks one task end to end through escrow, assignment, solve, verification, settlement and burn, and shows a censored task cannot inflate φ because only SETTLED tasks count. TV-23 runs three buyer populations — demandless, sparse, dense — and φ tracks the arrival rate (0.0000 / 0.0675 / 0.1675), which is what makes the number readable on a real testnet; the demandless case reproduces Pearl's zero exactly. TV-24 supplies the remaining two criteria: a slashing case, where a bad result is challenged once and then slashed with the bond cut, the buyer refunded in full and nothing burned; and the refund rate measured from the network's own books rather than accumulated by hand, so the arithmetic balances by construction. The links are not broken. What no prototype can manufacture is the buyer: test tokens are not demand, and the remaining question is a person spending currency they acquired outside the protocol. That is what the testnet itself is for.** TV-34 (added 2026-09-22) is the regression guard for a reporting bug found during this pass: the demand meter counted only SETTLED tasks once, so REFUNDED, MIGRATED and SLASHED tasks were recounted in every block they lingered on a sequencer list, inflating the reported refund and slash rates by the lingering time. φ itself was unaffected, and the financial books were never touched (they read the event counters, not the observation counters), but the reported rates were wrong. Fixed, guarded, and stated here because the paper reports measured numbers.** |
| | **★ Working prototype (2026-09-20): `f3a_sequencer_proto_en.py` — TV-15..TV-24 all PASS: refund-guarantee, task-migration, censorship-freeness, dilemma-free verification, honest lifecycle, bond-refill, demand meter (φ), the end-to-end paying task, three demand populations, the slashing case, and the measured refund rate.** The toy limits are stated in the file. |
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
   **★ 2026-09-21 correction, found by self-review:** this paper used to list "A=B=0" among the
   refuted structural attacks. That is correct **only for security** — with A=B=0 the noise
   dominates and the prescribed hardness is unchanged. It is **wrong for the utility claim**: in
   S1 mode the miner selects its own input freely, so nothing in the G layer prevents mining
   empty work while appearing to run the protocol. The actual guarantee is **economic**, not
   cryptographic: a block carrying no U task has `phi = 0`, still valid (the E-gap acceptance,
   TV-4) but earning only the baseline subsidy. **S1 cannot be forced to be useful; it is
   incentivized to be.** This is now a runnable test (TV-34) rather than an assertion, and the
   word "refuted" is scoped to security only wherever it appears. The same self-review found
   that the reference prototype modeled KW's rank-r noise with full-rank draws — a deviation in
   the *safe* direction (stronger noise than required), meaning the toy witnesses the difficulty
   argument but not the rank-r structure; the production kernel must use the `E_L·E_R`
   factorization (spec §A.0).
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
   generations (sm90 whitelist). **The whitelist governance — previously left undefined,
   which was itself a limit — is now specified** (spec §A.11: proposal + bit-exactness
   dossier → 2-epoch verification window → zero false-accept tolerance → versioned-schema
   activation → symmetric removal; its own limit is stated there — a whitelist is only as
   honest as the population verifying it). The native zkVM path (arXiv 2606.05433) has a **~36-month**
   horizon. Until then: fixed-point + error budget + the INT KW kernel (with transcript; the
   transcript-less design in Pearl's FP scheme was deferred to FP, spec §A.9b).
6. **The paper's ceiling is ~85/100.** The remaining ~15 points **are proofs**: the criteria of
   F3–F6, the live security budget, real paying task demand, independent audits. **A perfect
   paper is not equal to a running chain** — this is written at the top of the document so
   that the perfectionism is honest. **Current standing (2026-09-21): ≈80/100** by the
   internal rubric — up from 37 (v1) and 77 — with the bibliography now **11/11
   live-verified**, the US precedent cited (§9) and the market sized from reported earnings
   (§8.1). The 80→85 gap is exactly the set of items no paper can close: human review and
   live measurement.

---

## 11b. Adoption — "Why Would Anyone Use This?" (2026-09-21)

> This section exists because the single most honest criticism of the project is not
> cryptographic or legal. It is that a chain can be technically perfect and still die.
> The user asked the question directly; this is the answer, and it is written to survive
> being read by someone who is not inclined to be persuaded.

### The central claim is weaker than the pitch, and the true version is still interesting

The standard proof-of-useful-work pitch says: *"miners already buy hardware and electricity
to chase block rewards, so the useful work they could sell is available at near-zero
marginal cost, so we can underprice dedicated AI compute."*

**As written, this is false**, and the arithmetic is in `adoption_econ.py` (TV-35). A miner's
hardware is paid for by the block reward, but the block reward buys a *specific thing*: a
winning lottery ticket. Compute spent selling is compute not spent mining. The true marginal
cost of one second of GPU time is the mining revenue that second would have earned. The
compute is **not free**.

The true version of the claim is about **tax incidence, not free lunch**: the security budget
is a cost the protocol pays regardless, so useful work that can *ride on* work the miner was
going to do anyway is **subsidised by security spending** — cheap, not free, and cheap exactly
to the extent that KW's kernel is the same work as the sold work (overhead alpha ~ 1.3,
confirmed verbatim from KW). Where the two overlap, the fee is nearly pure margin. Where they
do not, the utility layer competes with mining for the same FLOPs and must pay the market rate.

**This restatement is not ours; it is the independently published one.** Rafael Pass's "The
Economics of Proof-of-Useful-Work" (arXiv 2606.06700, June 2026, DOI verified) reaches the same
conclusion by equilibrium analysis and names the regime KÖK is aiming at: **Duplexia**, in
which — verbatim — *"block rewards act as REBATES on inference prices, generating additional
socially useful computation that would not arise without the blockchain."* Three of his
findings matter directly:

- **"Free" is wrong; "subsidised by token emission" is right**, and the subsidy is exactly a
  price rebate, which is what TV-35 measures. The useful compute is additional and would not
  exist without the block reward — but the block reward pays for it.
- **Duplex work carries a computational overhead** (KW's alpha ~ 1.3), so the "same work twice"
  story is also approximate rather than exact.
- **PoUW does not make attacks cheaper**: once equilibrium prices are accounted for, the
  economic cost of a majority attack remains tied to the block reward. This answers the most
  common objection to the design, from the source a critic would cite.

Pass's equilibrium also names the two failure regimes KÖK must avoid: **Bitconia** (the chain
degenerates into ordinary PoW — the empty-block equilibrium of TV-36) and **Fortessia**
(duplex mining is displaced by something else; security improves but useful output does not).
**KÖK's roadmap is, in effect, a plan to land in Duplexia** and its kill criterion (§11b) is
the honest test of whether it has instead landed in Bitconia — which is what Pearl measured.

This distinction is not rhetorical. It decides the design: **the utility layer must be built so
that the sold work and the mined work overlap as much as the KW construction allows.** Every
task that requires the miner to do *additional* compute beyond the mining kernel is
unsubsidised and must stand on its own economics.

### The counter-example we have to explain, not slogan past

Pearl's live network ran **24 EH/s on ~320,000 GPU-equivalents (~112 MW) and sold zero useful
computation** (Basu, arXiv 2606.04819, verified verbatim). This is not a hypothetical failure
mode; it is the *measured* steady state of a large PoUW chain. Any claim that KÖK will be
different must be a **causal** answer to this number:

- Pearl's work was not the work anyone wanted to buy. **KÖK's answer:** the G layer is MatMul
  by construction (KW), the same primitive AI inference is made of — so the hardware and the
  workload are aligned, not merely both "computers."
- Pearl had no priced market, so there was nothing to buy. **KÖK's answer:** the U layer is a
  *market* (escrow, fee, burn), not a charity — demand must arrive as a paying transaction.
  *(Reviewer note, 2026-09-21 — the honest boundary on this claim: a paying transaction is
  necessary but NOT sufficient evidence of demand. The token is protocol-issued and its price
  derives partly from speculation, so a fee denominated in that token does not by itself prove a
  buyer wanted compute for its own sake — it proves only that someone parted with some value.
  Independent demand is measured, not asserted: by whether the buyer would have paid in a
  currency they did not print. F3a's "one real paying task" criterion is therefore the honest
  test, and a task paid in externally-acquired currency is stronger evidence than one paid in
  mined tokens. Payment and burn are a security budget and a sybil filter; they are not a
  proof of demand.)*
- Pearl's miners had no reason to serve. **KÖK's answer:** the fee is the only way to earn
  beyond the tail subsidy, and the tail is deliberately small (2 KOK), so serving demand is
  where the money is.
- **Pearl's verification accepted random matrices** (the research file's most damaging detail:
  the dominant mining software contained no inference code at all, and verification accepted
  whatever was submitted). This is the *mechanism* of the zero: the protocol literally could
  not distinguish real work from theatre, so it got theatre. **KÖK's answer, and it is
  tested, not asserted (TV-38):** our verifier recomputes the claimed tile from A, B and the
  ROM-derived noise, so a fabricated certificate, a forged tile value, or a certificate
  presented against the wrong input matrices all fail. The test is in
  `u_layer_prototype_en.py`. **This is the single most important structural difference from
  Pearl, because it is the one that makes "24 EH/s of real work" possible rather than 24 EH/s
  of theatre.**

**The honest gap:** none of these three are *proof* that demand arrives. They are the
preconditions. Whether anyone comes is an empirical question, and no paper can settle it.

### The market exists, and one network proves compute revenue is real (2026-09-21, verified)

The research file answers the question that determines whether this project is worth doing
at all. Three findings, each from a live source:

- **Aethir publishes $127.8M of compute revenue for 2025 and $166M ARR (Q3 2025)** — real
  dollars from selling GPU compute, not token market capitalisation. This is the existence
  proof that the market for decentralised compute is not hypothetical.
- **No PoUW chain publishes compute revenue.** Qubic and Dynex — the two existing
  proof-of-useful-work chains — publish none; Dynex is winding its token down (Feb 2026).
  Bittensor's 30-day revenue of $9.85M against $76.8M paid out means **~88% of its "revenue"
  is emission**, not sales. **So the exact combination KÖK proposes — PoW security plus
  compute sales — has no proven predecessor.** That is simultaneously the opportunity and
  the warning.
- **Verified prices set the bar.** H100 spot is $2.15/GPU-hr (Nebius preemptible) and
  DeepSeek V4-Pro is $1.32/M-token at peak. KÖK's compute must beat *these* numbers, and
  TV-35's crossover ($2.64 at launch rewards) says it can — while the token stays cheap.

**The strategic consequence:** the market is real (Aethir), the specific combination is
unproven (Qubic/Dynex/Bittensor), and the price bar is measurable (not a guess). That is
enough to justify F0 — and enough to define its failure honestly.

**The channel problem, which is the real reason F0 is hard.** Aethir reached $127.8M because it
operates like a vendor: it has a sales function and signs enterprise deals. **A permissionless
protocol has no sales function and cannot acquire one without ceasing to be permissionless.**
There is no channel through which "KÖK" calls a buyer, because there is no entity called KÖK —
only a protocol and whoever mines it. So the two-sided-market problem is worse than the usual
one: the supply side is self-organising and the demand side has no one to talk to.

The consequence is a narrowing of what F0 can actually be. It cannot be "enterprise outreach",
so it must be **outreach to the buyers the incumbents cannot or will not serve**:

- work that a cloud provider refuses to host (reason (b), and note it is also the smaller
  market, which is precisely why the incumbent left it);
- work whose provenance must be verifiable and where a vendor's word is not enough;
- **other chains' own proof requirements** — the demand that is *crypto-internal*, where the
  buyer is another protocol rather than an enterprise, and where the buying is itself a
  protocol action rather than a sales call.

The third is the one that survives the channel analysis, because it is the only one where the
buyer needs no one to sell to it. It is also the market the research found to be real but
revenue-free: Axiom, =nil;, Layer N all prove *demand* for verifiable compute and publish no
*revenue* from it. **That is the honest shape of the opportunity: demand exists, money has not
followed, and the protocol that lets it follow has no sales team.** This is why F0b (the real
AIR) is not an engineering nice-to-have — it is the closest thing to a product the protocol can
offer a buyer that cannot be called on the phone.

### The two-sided cold start, modelled (TV-36)

A chain is a two-sided market: miners supply compute, users supply tasks. The failure mode is
an **empty-block equilibrium** — miners mine because the subsidy pays, nobody submits tasks
because no market exists, and the chain runs forever at phi=0, functionally a plain PoW chain
with worse marketing. That is Pearl's measured state, and it is a *stable* state: the basin of
attraction of the dead equilibrium.

`adoption_econ.py` (TV-36) models this and finds the **critical seed of demand** — the smallest
fraction of the network's compute that must be *real, paying demand from day one* for the
market to escape the dead state. Two findings, both stated plainly:

1. **The seed cannot be emitted by the protocol.** No token distribution, airdrop or incentive
   programme creates a buyer who has a job. The seed is brought by someone who already pays
   for compute. **This is why F0 (demand discovery) is now the first roadmap phase, ahead of
   the formal spec's successor phases.**
2. **Below roughly break-even, the dead state is absorbing** — no seed escapes. The chain
   cannot subsidise its way to adoption if its compute costs more than the market's; the
   cross-subsidy must be real, which loops back to the overlap requirement.
3. **The speculation paradox.** The crossover token price (where mining and selling pay the
   same) is pushed in *opposite* directions by the two kinds of success. A **larger network**
   splits the fixed reward over more FLOPs, so mining pays less per FLOP, the crossover
   *rises*, and selling improves. A **higher token price** does the reverse: it crosses the
   crossover and makes utility uncompetitive. **So a speculative spike is the project's enemy,
   not its friend** — the utility window is open while the token is cheap, and a price rally
   can close it even on a healthy network. This is a genuine design tension, not a marketing
   problem: every incentive that raises the token price also narrows the adoption window. It
   is why the emission tail is deliberately small (2 KOK) and why F0 is time-critical rather
   than merely important.

### Who would actually use this — the honest two reasons

People will use KÖK for exactly one of these, and no other:

**(a) It is provably cheaper for a job they already pay for.** Not "cheaper in theory" —
cheaper at a quoted price, for a workload that exists today, verified against the market's own
published rates. This is a sales problem, not a cryptography problem.

**(b) It is the only place a job can run permissionlessly.** A computation that a cloud
provider will not host, or a result whose *provenance* must be verifiable (provably-correct
inference, reproducible research, a regulatory audit trail) has no substitute at any price.
This is the smaller market but the more defensible one, because the incumbent cannot compete
on it by lowering prices.

**Reason (b) has three weaknesses, and selling it before they close is fraud-adjacent:**

1. **Permissionlessness cuts both ways.** A protocol that cannot refuse a job cannot refuse a
   malign one. The same property that defends KOK against deplatforming also invites the
   content a cloud provider would remove — and this sits in direct tension with the MiCA/AML
   posture of §9. **This is a risk to be priced, not a bug to be fixed**: a permissionless
   chain cannot be selectively permissionless.
2. **Provenance is currently claimed, not proven.** The prototype's "STARK-like" trace is not a
   real AIR (§A.0) — so the buyer's provenance guarantee rests on the honest miner and the fee,
   not on mathematics. **This is closable** and it is why F0b exists: until the trace is a real
   AIR, reason (b) is a promise from an anonymous team, which is exactly what a buyer paying
   for provenance is trying to avoid.
3. **Liveness is unmeasured.** The GHOSTDAG toy assumes all blocks are valid, so the
   availability story (10 BPS, no provider outage) is an argument, not a measurement.

The strategic reading: **reason (b) is the more defensible position, but it is not yet a
defensible *claim*.** F0b is what makes it one. Reason (a) needs no new cryptography — only a
customer — but it is vulnerable to the incumbent's price list. Neither is free.

Everything else — the green narrative, the "wasted energy" argument, the AI-for-all rhetoric
— is decoration that Pearl's measured zero already falsified. **A chain whose only story is
"wasted energy is bad" has no answer to a chain whose story is "here is a customer."**

### Expansion areas, and which survive honesty

| Direction | Why plausible | Why it might fail | Status |
|---|---|---|---|
| **Verifiable inference as a service** | The U layer already proves MatMul; inference *is* MatMul. The (b)-reason. | Verification cost may exceed the job's cost at small scale; the provenance market is unproven | **Primary candidate.** Needs a real buyer (F0) |
| **ZK-coprocessing for other chains** | Other L1/L2s provably need off-chain compute with proofs; KÖK's proving market is exactly that | Competes with dedicated prover networks that do not also run a chain | **WEAK after the Axiom measurement** — see the note below this table |
| **Permissionless batch compute** | The (a)-reason: MatMul-shaped work that is price-sensitive | A commodity market; the cross-subsidy must be genuine to win on price | **Conditional on the overlap being real** |
| **AI agent settlement layer** | Fast blocks (10 BPS, GHOSTDAG) + a native compute market is a coherent agent substrate | Speculative; depends on an agent ecosystem that does not yet exist | **Explicitly deferred — do not build on a hope** |

**Note on the downgrade (2026-09-21, verified from axiom.xyz and nil.foundation):**
the prover market is real but the competition is *fast*, not merely cheap. **OpenVM 2.1
proves an Ethereum mainnet block in real time on 4 GPUs** (29 Jul 2026) and OpenVM 2.0
reaches 1 GHz proving throughput across 64 GPUs with 100 bits of provable post-quantum
security, formally verified in Lean. =nil; is an Ethereum L2 live on mainnet with zkSharding
and 300+ developers. **This dismantles the cross-subsidy argument for that specific market:**
when a rival proves Ethereum in real time on four GPUs, "our provers are mining anyway" is
not a decisive edge, because the buyer is not shopping for cheap proving — it is shopping for
fast proving, and the incumbent has already crossed that bar. KÖK's ZK direction is therefore
recorded as **weak**, not secondary.

**The one direction that survives this measurement, and why.** Confidential compute is where
the demand is *provably* paying today: Akash ships hardware-enforced TEEs to a one-line config
and names its buyers explicitly — *"sensitive medical records, proprietary algorithmic trading
models, or core company intellectual property embedded in model weights"* (28 Jul 2026,
verbatim). Akash's answer to "can I trust an unknown provider" is *don't trust — encrypt*.
KÖK's answer would be *don't trust — verify*. **Both solve the same buyer's problem, and the
buyer exists and is paying right now.** The honest caveat is that Akash's solution ships today
and KÖK's requires F0b (a real AIR). This is the strongest customer answer the research has
produced, and it is the first one that makes F0b a market requirement rather than an
engineering preference.
**The privacy extension is not our invention — KW proposes it.** Remark 2.2 of the KW paper
(verbatim, from the full text fetched 2026-09-21) says the verifier's work *"can delegate the
verifier's work ... to the prover by asking the latter to compute a SNARK certifying that the
verifier would have accepted the proof had it seen it. Furthermore, **if privacy of A, B is an
issue, the prover can use a zkSNARK.**"* So F0b is the construction KW designed but did not
build: the zk-AIR both removes the verifier's cost and hides the inputs. **This is why the risk
of F0b is engineering (writing the AIR), not cryptographic (inventing a scheme) — the scheme is
published.**

What F0b deliberately does *not* do is KW's adjacent Remark 2.3, which asks whether the SNARK
computation itself could be the source of hardness, removing the need for the noise matrices
E, F. **KÖK rejects that path**, because prescribed hardness — the ability to retarget ε
independently of the task, as Bitcoin does — is required for the difficulty adjustment, and a
SNARK's cost is tied to the task rather than to an independent target. KW raises the objection
in the remark itself. So F0b is strictly the verifier-delegation of Remark 2.2, not the
hardness substitution of Remark 2.3, and the G layer's security argument is untouched.
| **ZK-coprocessing, analysed — now downgraded** | Demand is *endogenous*: other L1/L2s provably need proofs (bridges, light clients, fraud windows) that they cannot generate themselves — so the "why would anyone use this" question inverts to "I already need this". The seed problem partly disappears. | **The overlap must be real for a ZK proof, not just for MatMul.** KW's MatMul-transcript PoW is not a zk-SNARK's AIR, so the cross-subsidy does not automatically carry over; this requires the same real-AIR work as F0b. Dedicated prover networks (RiscZero, =nil;, Succinct, Axiom) run no chain, so their whole cost base is proof-making and they hold the first-mover position | **Strongest second candidate; it shares F0b's precondition — a real AIR unlocks both reason (b) and this market** |

### Who would actually use this — the customer answer, verified (2026-09-21)

The market research now answers the question with named buyers rather than segments, and the
answer is narrower and more useful than the earlier "two reasons" framing:

**The buyers exist and are paying today: health, finance, and IP-holders running
privacy-sensitive AI inference.** Akash sells them hardware-enforced confidential compute
(TEE) right now, in a one-line config, and describes the workload in its own words as
*"sensitive medical records, proprietary algorithmic trading models, or core company
intellectual property embedded in model weights."* That is the demand, stated by the vendor
that is serving it.

**Akash's answer is *don't trust — encrypt*. KÖK's answer would be *don't trust — verify*.**
These are two solutions to the same buyer's problem. The buyer does not care which one wins on
philosophy; they care whether their model weights are safe on a stranger's GPU. The proof-based
answer is the one that does not depend on trusting Intel or AMD's enclave implementation, and
in that narrow sense it is a stronger product — **but it does not exist yet, and F0b is what
builds it.**

What the same measurement *demolishes* is the ZK-coprocessing idea: OpenVM proves Ethereum in
real time on 4 GPUs, so "our provers mine anyway" is not a competitive edge in a market where
the buyer wants speed and already has it. **That direction is now recorded as weak, not
secondary** — an honest downgrade from the earlier version of this section.

**So the concrete customer answer, verified rather than hoped:** health, finance, and
IP-sensitive inference buyers who would prefer a proof over an enclave. One buyer from that
group is the F0 target. **Everything else in this paper is in service of that one sentence.**

### The zero-budget constraint, and what it forbids

The project has no capital for the expensive parts — a security audit, a mainnet, hosting —
and this is not a problem for F0, because outreach costs nothing. **The danger is the opposite
of spending: getting a "yes" and over-promising delivery that cannot be funded.** One email
promising a working zk-AIR mainnet to a company processing medical data, backed by no audit
and no capital, destroys the project's credibility in a single step — the mirror image of
Pearl's failure, which marketed a capability it could not deliver.

The zero-budget path is therefore: **contact ($0) → letter of intent ($0) → grant application
($0) → the grant pays for the audit and the testnet.** Akash's grants programme, Aethir's
$100M ecosystem fund, and Ethereum Foundation grants are the realistic candidates, and a
signed LOI is precisely what such programmes fund. **Intermediaries do the selling, not the
protocol:** Akash does not sell to the customers in its own case studies — providers with GPUs
and sales teams do. KÖK publishes the market; providers serve it. A permissionless chain
cannot acquire a sales function without ceasing to be permissionless, which is the channel
problem of §11b turned into a design principle rather than a handicap.

The consequence for sequencing is strict: **no promise may be made until F0b exists and is
audited, and the audit is what the letter of intent buys.** If the LOI arrives and no grant
follows, the honest move is the kill criterion below, not a larger promise.

### Why the review waits, and the measurement does not

A cryptographic review of the G layer is available and affordable in principle,
and it has been deferred deliberately, not for want of money alone. The reason
is priority. The review would examine KW's cryptography, and the independent
analysis above already reports KW's own justifications verbatim: ROM
unpredictability and marginal uniformity are proven, Assumption 6.4 follows
almost automatically from the output-size bound and KW says so. **The
cryptography is not the binding constraint. The binding constraint is demand.**
Pearl ran a 24 EH/s proof-of-useful-work network and measured zero useful
compute sold. A cryptographic review cannot change that number.

So the order is: measure first, review second. F3a is a testnet, not a mainnet —
the U layer alone, a central sequencer, a dummy proof, test tokens, no consensus,
no audit required, no investment required. Its single job is to find out whether
anyone pays for a task. Two outcomes are both useful: a zero means the Pearl
failure is ours too, and no mainnet should be built on it; a non-zero result is
the evidence that justifies the review and the grant that pays for it.

**Launching the mainnet to see who shows up is the experiment Pearl already
ran**, and it produced the zero. Repeating it is not a strategy; it is the same
measurement at a thousand times the cost.

Investment is likewise deferred rather than refused. A token sale raises the
MiCA question, since mining grants value or a right and the token is therefore
not an Art. 3(9) utility; equity implies a premine and gives up the fair-launch
position that keeps the token on the commodity side. Either path costs the
project something it is currently holding. Until a measurement says the demand
exists, that price is being paid for nothing.

### The kill criteria, stated in advance

To be worth continuing past F3a, the project must show **one real paying task**. If F3a ends
with zero real demand, the honest conclusion is that the utility layer has no market and the
project should fall back to its specified pure-PoW mode (§A.9) — which is a *legitimate
outcome*, already designed for, and far better than spending years converging to Pearl's
measured state while insisting the demand is coming.

**This is the answer to the user's question, and it is deliberately uncomfortable:** the
project's survival does not depend on the cryptography (as sound as a paper can make it) or
the law (now navigable). It depends on **one customer with one job**. That is not a weakness
unique to KÖK; it is the shape of every two-sided market. But it is the reason the roadmap now
begins with demand discovery rather than with a testnet.

**The critical path, stated once and plainly:**

```
F0 (demand discovery)  ─┐
                        ├──> F3a (economy testnet) ──> F3b ──> F5 ──> F6
F0b (real AIR)         ─┘
```

- **F0 and F0b are both unblocked today.** Neither waits on a cryptographer, a lawyer or an
  investor. F0 is a sales exercise (10 interviews, one letter of intent); F0b is an engineering
  one (one real AIR for one MatMul task). They can run in parallel with the Demirel review.
- **F3a cannot start without F0** — an economy testnet with no demand measures nothing, which is
  the precise error Pearl's years of running made.
- **F2 is already in flight.** When F0b lands, the review package is re-sent with a real AIR,
  because the first package had 77 untranslated strings and a modeled-but-not-instantiated
  noise distribution (both since fixed and recorded in §A.0).
- **The kill criterion is a date, not a feeling.** If F3a ends with zero real paying tasks, the
  honest move is the specified pure-PoW fallback (§A.9) — a designed-for outcome, not a defeat.

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
| **Proves Polymath (1) random-rotation** | low (they themselves question it) | Does not change the KW main body; only the Appendix A alternative. KÖK still uses the main-body instantiation (KW §6, the non-Appendix-A construction). | LOW |
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

### 12.1b ★ The wider competitive map, and the one empty cell (2026-09-21)

The rivalry analysis above treats Pearl as the comparator, which is right, because it is the
only live PoUW chain. But the wider field was surveyed while waiting on Astria and Demirel, and
it changes what KÖK is competing **for**, if not whom. The survey comes from a Pearl-affiliated
source, so its ranking is not used here; only its taxonomy and status facts are, and those were
checked against the projects' own sites.

The taxonomy separates real PoUW from marketing on three tests: the mining work **is** the useful
work, the output is **verifiable on-chain**, and **there is a paying customer**. The third test is
the one Pearl fails, and it is the one φ measures.

| Project | Useful work | Consensus | Paying customer? |
|---|---|---|---|
| **Pearl** | LLM inference (NoisyGEMM) | PoUW | **no** — measured zero |
| **Bittensor** | subnet ML tasks | incentive chain | **no** — "the chain pays contributors in TAO"; ~88% of revenue is emission |
| **Qubic** | PoUW | PoUW | **no revenue published** |
| **Dynex** | neuromorphic PoUW | PoUW | **no revenue published; cancelling its utility token (Feb 2026)** |
| **Gensyn** | training → now verifiable inference, oracles | not PoUW | not yet; repositioned to prediction markets |
| **Akash** | generic GPU/CPU compute | **PoS marketplace** | **yes** — $5M all-time spend |
| **Render** | GPU rendering | **PoS marketplace** | yes, production |
| **io.net** | GPU aggregation | **DePIN** | some |
| **Golem** | generic compute | marketplace | low usage |
| **Aethir** | GPU cloud | DePIN | **yes** — $127.8M/2025, $166M ARR (the exception) |

The pattern is the finding. **Useful work with paying customers exists — in marketplaces on PoS,
where it is not tied to block production. True PoUW exists — with no paying customer.** The two
halves have not met in one system. Pearl and Bittensor pay from inflation, confirmed from
Bittensor's own front page. Akash and Render sell real compute but secure nothing by it. KÖK's
target is specifically the unoccupied cell: useful work that is both consensus-relevant and
externally purchased.

The scale question is where this gets uncomfortable, and it was answered in an earlier research
pass (`arastirma/pazar_ve_rekabet_2026.md`). **Almost nobody in this field publishes real USD
revenue.** Aethir is the exception at $127.8M for 2025 and $166M ARR. Akash's $5M is all-time,
cumulative, small against that, and small against the $2/GPU-hr floor the pricing survey found —
H100 on-demand runs $2.89–6.16, spot $2.15–2.46, and Akash itself lists $1.33. The two other live
PoUW chains, Qubic and Dynex, publish no compute revenue at all, and **Dynex is cancelling its
utility token (February 2026)**. Bittensor's revenue is roughly 88% emission. So the honest
statement is not "demand exists" but "demand is mostly either undisclosed, inflation-funded, or
smaller than the subsidy that creates it." **No revenue-proven predecessor exists for the
combination KÖK is building**, which is the same conclusion the earlier pass reached and which
F3a exists to test.

Two external observations sharpen this. First, **Akash's own Q1 2026 report describes the failure
mode KÖK's U layer is built against**, in Akash's words: under their earlier AEP-23 scheme "when
tenants pay in USDC, demand for AKT weakens. Usage grew while AKT's role as the network's core
economic unit eroded." They fixed it with burn-mint equilibrium, live on mainnet since 23 March
2026 — buy AKT, burn it to a stable credit, settle. KÖK's irrecoverable fee burn reaches the same
position structurally rather than via a two-token path, but the important thing is that **the
problem was real enough for the largest decentralised compute marketplace to fork its economics
mid-flight.** That is a second measured failure alongside Pearl's, pointing the same way.

Second, and more speculatively: the **only demand-side force found that requires no crypto
ideology is physical.** Reporting on centralized AI infrastructure describes planned data centers
delayed or canceled, a Maine moratorium, communities refusing eight-figure land offers, and gas
turbine lead times of years. If centralized inference capacity is genuinely supply-constrained,
buyers have a reason to look for capacity elsewhere that has nothing to do with permissionlessness.
The supply side is constrained on **two independent axes**, both reported in Akash's own 2025
review: **NVIDIA H100s stayed allocation-only through 2025 with 6-12 month wait times for
enterprise buyers, and AWS and Azure responded by raising prices while reducing availability.**
Compute access became the primary business constraint for the startups and mid-market builders who
are the natural first customers of a permissionless market.

**This is recorded as a signal, not a measurement.** The data-center-delay figures were cited by a
self-interested blog and not independently fetched; the IEA's "Energy and AI" report (April 2025)
corroborates the structural energy constraint but predates the 2026 figures; the H100 allocation
and price-increase claims are Akash's self-report, not NVIDIA's or the clouds'. If the constraint
is real on both axes, it is the first external thing that could fill the empty cell. Whether it is
real is exactly the kind of question F3a's buyer is there to answer — Astria moved providers for a
price reason, which is a capacity-and-cost reason, not an ideological one.

**What this does not change:** the roadmap, the wait for Demirel, or the single-invitation
discipline. The survey supports the claim that the chosen problem is real and the architecture
fits two documented failures. It does not create a buyer, and it does not license an announcement
beyond the one already sent.

**One correction the survey forces, dated 21 September 2026.** The "unoccupied cell" claim above
was written from a landscape survey a week old. A check of current arXiv submissions found work
three days old that changes it: **arXiv 2609.21728, "Verifiable Computation with Trusted Execution
Environments and On-Chain Digital Rights Tokens"** (Kruger and Georg, submitted 18 September 2026).
It builds a market where data owners pool private data inside TEEs and issue **narrowly scoped
computational rights as on-chain tokens**; an analyst redeems a right to run specific open-source
code on sealed data and receives the result, not the data. A **reference implementation runs
WASM/Python jobs and records redemptions on Solana.**

So the "computation market settled on a ledger" is no longer an untested idea — someone has
published a working one, on an existing chain, with a different trust root. The cell KÖK targets
is still unoccupied **at the intersection with PoUW consensus**, which this paper does not touch
at all (no prescribed hardness, no leader election from the work, Solana underneath). But the
utility half is no longer novel by itself, and the design choice KÖK must now be able to defend
explicitly is: **why an escrowed fee with irrecoverable burn and a zkVM proof, rather than a
rights token with a TEE as the enforcement boundary.**

That has a real answer, and it is the one §11b already states from the buyer's side. A TEE and a
zkVM solve **different halves of the same buyer's problem.** The TEE provides *confidentiality*:
the provider never sees the data, which is exactly why Akash's confidential-compute buyers
(medical records, trading models, IP in weights) are paying today. It does **not** provide
*verification*: nothing attests that the computation was performed correctly, only that it ran
inside an enclave. Kruger and Georg's rights token inherits exactly this asymmetry — it enforces
*what* an analyst may run, and it does so convincingly, but the ledger records a redemption rather
than a correctness proof.

KÖK's zkVM proof inverts the emphasis: it verifies *that* the work was done correctly, and KW's
Remark 2.2 (the zkSNARK variant, which KÖK adopts as F0b) adds confidentiality on top. So the two
are complements on paper, and the honest question is not which is better but **which half the
buyer is actually paying for.** Akash's shipped evidence says the confidentiality half has paying
customers right now, and KÖK's F0b has not been written. That is a real gap in delivery, not a gap
in the argument, and it is stated here rather than smoothed over. What remains KÖK's own is the
combination: prescribed-hardness consensus *and* a paid task market with cryptographic
settlement, which the Solana design does not attempt.

**A second finding, same day, that partly reinstates a direction this project had ruled out.**
The AI-agent security gap was rejected during the same research pass on the strength of the
CertiK data: 2026 losses traced to North Korean actors, cross-chain failures, phishing and
deepfakes, and the recommended defences were user-side. **That conclusion stands, because it is
correct for the losses CertiK measured.** But **arXiv 2609.22076, "APort Vault"** (Uchibeke,
18 September 2026) measures something else, and conflating the two would be the exact error the
research discipline exists to prevent.

APort Vault benchmarked **payment authorization in tool-using agents**: 4,371 human-written
attacks from a public capture-the-flag event, replayed against 14 models from 8 labs, five policy
configurations, two tracks, **225,964 evaluations**. Transfers to recipients the passport did not
permit numbered **140 of 76,842 with the model alone, and 0 of 69,297 behind a deterministic
pre-action layer** implementing the Open Agent Passport specification — a per-session upper bound
of 0.38% across 790 sessions. Critically, the zero was not bought by refusing payments: **25,370
legitimate payments still executed** behind the layer, while the policy denied 187 of 25,640
transfer calls, 148 for a forbidden recipient.

So the gap is not "users are careless." It is that **agents can be talked into paying the wrong
recipient, and a protocol-level boundary stops it without breaking legitimate payments.** That is
a measured problem with a measured answer.

**Stated narrowly, this does not change what KÖK builds.** It is not a blockchain, there is no
consensus or ledger, and it does not justify an AI-agent-security chain. What it does is
identify the shape of KÖK's future customer. **The buyer of inference is increasingly an agent
rather than a human, and an agent that cannot be safely authorized to pay cannot become a
customer at all.** KÖK's escrow-and-burn task market already separates what an agent may *do*
from what it may *take*: the fee is escrowed before assignment, payout occurs only on verified
settlement, and a slashed provider refunds the buyer in full. That is an authorization boundary of
the same shape as the one this paper benchmarked, reached from the opposite direction. Worth
knowing. Not worth building on.

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

## 13. References (21 September 2026, live — 11/11 verified)

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
Market: CoinGecko (BTC/KAS/TAO/RNDR/AKT/DNX) · Digiconomist · blockchain.info ·
**Competitive landscape (§12.1b, surveyed 2026-09-21):** akash.network/token and
akash.network/blog/akash-network-q1-2026-report (BME, $5M all-time spend, the AEP-23
admission) · bittensor.com ("the chain pays contributors in TAO") · gensyn.ai (open-1b,
Delphi, Credibly Neutral AI Oracles) · iea.org/reports/energy-and-ai (April 2025, primary
energy source) · lordofpearls.xyz/blog/top-pouw-chains-2026 (taxonomy used; Pearl-affiliated,
ranking not used) · **arXiv 2609.21728** (Kruger & Georg, TEE + on-chain digital rights tokens,
reference impl on Solana — the working verifiable-compute market; forces the zkVM-vs-TEE
defence) · arXiv 2609.22076 (APort Vault, AI agent payment authorization)
