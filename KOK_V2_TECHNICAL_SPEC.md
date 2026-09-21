# KÖK Network v2 — TECHNICAL SPEC: Task Marketplace, Difficulty Mathematics, Economic Simulation

**Date:** 19 September 2026 · **Parent document:** `KOK_V2_PAPER.md` · **Status:** Formal spec (Appendix A/B/C)

> This document formally specifies three critical subsystems of the v2 design to a "perfection on
> paper" standard. The core cryptographic dependency: **Komargodski–Weinstein MatMul PoUW
> construction (IACR ePrint 2025/685)**; the economic dependency: **Pass PoUW equilibrium model
> (arXiv 2606.06700)**. The parts of both sources that have not yet been independently verified are
> explicitly marked as **"conjecture/dependency"** (§A.9, §C.7).

---

# APPENDIX A — TASK-MARKETPLACE PROTOCOL (Official Spec)

## A.0 Cryptographic basis of the work function

**Choice:** Komargodski–Weinstein "Proofs of Useful Work from Arbitrary Matrix
Multiplication" (ePrint 2025/685 = **arXiv 2504.09971v4**, 2025-04-15, v4 2025-11-13).
**Independent analysis: `KW_ANALIZ.md` (2026-09-19).**

**Why:** KW provides a PoW certificate for MatMul in the **permissionless setting where the miner
chooses its own input**: **1+o(1) multiplicative overhead** (relative to naive MatMul), **prescribed
hardness**, and a claim of resistance to "fast matrix multiplication algorithms" (FMM; ω<2.371339
[ADV+24 arXiv 2404.16349]; AlphaEvolve ω<2.371177, 2026). The plain Freivalds equation
`A(Br)==Cr` used by KÖK v1 is exactly the construction KW explicitly calls **"O(1)-factor overhead
trivial but useless for each task"**: it has verification asymmetry but **no prescribed hardness**
→ a cheating miner gains an asymmetric advantage over an honest miner by selecting an easy input
(structured matrix). KW closes this gap.

**Formal goal (spec language):** The work function `W(A,B; ctx)` = the KW certificate; its
properties:
- **(P1) Prescribed hardness:** the expected cost of producing a valid certificate is `h(n)` FLOPs
  (for n×n MatMul, `h(n) = Θ(n^3)` naive; as long as FMM algorithms are not applied in practice),
  **independent** of input choice.
- **(P2) Near-zero overhead:** honest production cost is `1+o(1)`×.
- **(P3) Verifiability:** the certificate is `O(polylog)` in size, with `O(n²)` or cheaper
  verification.
- **(P4) Chain-binding:** the certificate's statement includes `ctx` (§A.4).

> **⚠ DEPENDENCY (honest):** KW's security is a **conjecture** — a reduction to the hardness of the
> "batch of low-rank random linear equations" problem. This is the protocol's sole cryptographic
> assumption (together with a random oracle) and **requires independent cryptographic review**
> (Phase 2 criterion). The spec defines a fallback in §A.9 so that the network does not collapse
> even if this conjecture fails.
>
> **2026-09-19 independent analysis (summary, full: `KW_ANALIZ.md`):** this conjecture turned out to
> be strong enough to be replaceable by **a weaker and more standard assumption** — Assumption 6.4
> is automatic because of the Θ(n³/r) output-length lower bound and is **not necessary**; the real
> security is (a) unpredictability of σ in the ROM + (b) the proven marginal uniformity (Lemma 6.5)
> + Merkle one-wayness. All structural attacks and the trapdoor-matrix literature were refuted.
> **Risk: high → low-medium.** The remaining principal risk is the demand for utility (E-gap), not
> cryptography. Nevertheless, **2 independent cryptographic reviews are the mandatory gate of Phase
> 2** — the analysis above is an LLM's reading, not a proof.

> **★ 2026-09-21 adversarial self-review — a deviation in the prototype, in the safe direction.**
> KW generates the noise as a product of two rank-r factors (`E = E_L·E_R`), so Lemma 6.5's
> conclusion is that E is uniform over the rank-r manifold `E_{r,n}`. **The reference prototype
> does not do this: it draws every entry independently (`E[i][j] = H("E", ctx, i, j) mod q`), which
> is uniform over the full n×n space — full rank n, not rank r.** Two consequences, both stated:
>
> 1. **The prototype does not literally instantiate KW.** Its noise is *stronger* than required
>    (more randomness than rank-r), so any hardness the toy exhibits is a *conservative* witness,
>    not an over-optimistic one. But a reviewer is entitled to object that the marginal-uniformity
>    property is being modeled rather than instantiated, and the honest answer is: yes, for toy
>    dimensions only. **The production kernel must use the `E_L·E_R` factorization.**
> 2. **This is why the prototype's `r` parameter is unused in the noise draw** — it only sizes the
>    tile grid. That is a modeling choice, not a bug, but it means **TV tests witness the
>    difficulty argument, not the rank-r structure of KW.** Recorded here so no claim is read as
>    stronger than the code supports.
>
> **Also fixed this round (a real defect):** `g_layer_tests_en.py` had been importing its `Chain`,
> `KWKernel` and `H` from the *Turkish* module, so it could not run standalone and the audit could
> not see the Turkish leaking across the import boundary. It is now fully self-contained, and in
> the process the inlined `prove()` was found to have dropped the target check — it never returned
> `None`, so the prescribed-hardness measurement TV-2 was a **no-op that always read 1.0**. Restored:
> the measured attempts are now geometric (4.4/4.4/4.5), as the test intended.

## A.1 Two layers — SECURITY and UTILITY (2026-09-19 revision)

> **After the 2026 negative results:** Basu (2606.04819) measured that Pearl's live 24 EH/s network
> produced **zero** useful computation; Demirel (2026/1492) proved that leader election must be
> **demand-independent** (Thm 2); the SoK (2025/1814) stated that "utility does not contribute to
> the security budget." **The S1/S2 naming of this spec was converted to G/U layers:** S1 is no
> longer "useful" — it is the **G layer (security)**; utility exists **only in the U layer**,
> externalized by fees. **There is no such thing as "useful work is security."**

| | **G layer — SECURITY (every miner, every block)** | **U layer — UTILITY (fee-paid task marketplace)** |
|---|---|---|
| **Who determines it** | The miner chooses its own MatMul input (free) | **The client** commits the task + fee to the chain |
| **Certificate** | KW/cuPOW-style MatMul certificate (1+o(1)) | Full zkVM/STARK proof (Circle STARK + Jolt Atlas) |
| **Utility claim** | **NONE** — prescribed hardness is provided, not utility | **YES** — demand is external, via the real fee in escrow (E ✓) |
| **Source of difficulty** | KW prescribed hardness + `H(FS‖nonce) < target` | Circuit size (structural lower bound) |
| **Role in leader election** | **THE BASE** (sole source of the block solution) | **NONE — zero consensus weight.** The target test reads only `kw_cert`; U proofs carry fee revenue, never leader selection |
| **Under zero demand** | Filler dense-random MatMul → liveness is preserved (Demirel Thm 2 ✓) | U is closed; the network continues to live as pure-PoW |

**The essence of the design:** KW solves **W (work soundness)** but does not solve **E (demand
exogeneity)** — the cause of Pearl's collapse was treating E as an "economic property" and marketing
it as such. KÖK v2 solves E **only in the U layer** and **only with fee payment**; it never ties
security to U.

## A.2 Data structures (format for moving to live)

```
Task (S2)      = { task_id: Hash, client: PubKey, commitment: MerkleRoot,
                   fee: Amount, bond: Amount, harness_id: Version, expire: Height,
                   max_overhead: FLOPs }

Assignment     = { task_id, miner: PubKey, epoch_seed: VRFOutput, height: Height,
                   vrf_proof: VRFPubKey-Proof }        // for S2; ABSENT in S1

Statement(ctx) = { selected_parent: BlockHash,        // from GHOSTDAG ordering
                   parent_set_hash: Hash,             // TV-25: full parent set is bound
                   miner: PubKey, task_ref: Hash,
                   height: Height, proof_system_id: SchemaId,
                   nonce: u64 }

Solution       = { ctx, kw_certificate: Bytes,        // S1
                   || snark_proof: Bytes,             // S2
                   digest_target_check: H(certificate||nonce) < target }

Block          = { header: {parent_set, ctx_root, tx_root, task_root,
                           digest: H(fs_transcript), nonce, proof_system_id},
                  body: { txs, task_set, solutions[], agg_stark} }
```

## A.3 Chain binding and grinding resistance

- **ctx dependency:** since `selected_parent` is GHOSTDAG's **selected parent** and every miner's
  solution is bound to a different chain position, a certificate **cannot be reused for another
  block** (precompute/replay impossible: the chain hash cannot be known in advance).
- **Nonce freshness:** every nonce changes the FS transcript → every attempt **requires a fresh
  certificate** (the repetition of work is the source of difficulty).
- **VRF assignment (S2 only):** task assignment is determined by VRF from the `epoch_seed`; the
  epoch seed is derived from chain history (N-64 blocks back) → the miner **cannot influence** the
  assignment (grinding is expensive), and **collusion** between the task owner and the miner is only
  possible with a bond slash.
- **External-utility attack (arXiv 2505.21685):** externally incentivized miners tend to aggregate
  useful tasks into a single block → **per-block useful-fee cap** `C_fee` and **anti-aggregation
  rule**: the total fee of S2 tasks in one block cannot exceed `C_fee`; the excess shifts to
  subsequent blocks (compatible with DAG ordering).

## A.4 Bonding and slashing matrix

| Crime | Proof | Penalty |
|---|---|---|
| Invalid certificate | Any verifier rejects it (deterministic) | The block is already rejected; the miner cannot receive the block reward (natural penalty) |
| Invalid S2 solution | Fraud-proof window (W_s = 100 blocks) | `slash_task = bond_task` (the task bond) + fee refund |
| Equivocation (same task, two solutions) | Two signed solutions | `slash_eq = 2 × task_fee` |
| Data unavailability | Refusal of an opening request | `slash_da = task_bond` |
| Collusion (task owner = miner, easy task) | **None** — KW prescribed hardness renders this attack meaningless | — |
| Secret miner-pool agreement (Pass §1.8 aggregation risk) | On-chain indicators (single-address share > 20%) | **Not automatic** — observation + community signaling (§C.5 alarm) |

## A.5 Verification incentive security (Verifier's Dilemma)

**Problem (arXiv 2404.09005):** if verification is cheaper than computation, rational nodes may skip
it. **KÖK solution:**
1. **Mandatory verification:** for block acceptance every full node verifies the certificate — it is
   not optional (deterministic; a skipping node stays on a fork).
2. **No re-execution:** since S1/S2 verification is asymptotically cheap, the "chargeable cost" ≈ 0
   → no dilemma arises. (This is the reason to avoid HadAgent-style re-execution.)
3. **Fraud-proof window for S2:** challenge within W_s blocks; the challenging verifier earns
   `reward_fraud` (an insufficient challenge → its own bond is slashed) — **verifier
   incentive-security**.
4. **Controlled difficulty:** parameter design so that the rational miner is the honest miner
   (SEDULity method, arXiv 2512.13666): rational miner = honest miner; the formal condition is
   §A.6.
5. **★ Censorship resistance (2026-09-20, V2 §10.1 F3a criterion):** testnet F3a's centralized
   sequencer is **a temporary test centralization** (to be replaced by GHOSTDAG in F3b).
   Therefore the spec defines **two mechanisms** against sequencer censorship:
   (i) **Refund-guarantee:** the sequencer either includes the task within W_r blocks or publishes a
   rejection-step; if it rejects or times out, the escrow is **automatically refunded** (with no
   bond, to the task owner) — the **cost of censorship is zero, and its benefit is also zero**.
   (ii) **Task-migration:** the task owner can resubmit the rejected task (with the same
   `task_ref`) to an **alternative sequencer**; the first sequencer's bond is slashed (censorship
   yields **negative returns**).
   **In production (after F3b):** the centralized sequencer is removed, and censorship resistance is
   provided by GHOSTDAG's parent-set diversity + miner competition — but **the refund-guarantee and
   task-migration are retained** (these are on-chain mechanisms, independent of consensus).

   **★ Working prototype (2026-09-20):** `f3a_sequencer_proto.py` — TV-15..TV-20, all PASS. It
   proves that the two mechanisms are validated **at prototype level**; **toy limits** (listed in
   the file header): single sequencer object, W_r=3, symbolic fee/bond, dummy proof (crypto in F3b),
   no GHOSTDAG, censorship modeled with an `evil` flag.

   **★★ CRITICAL: The economics model found a BUG in the prototype and changed the spec.**
   `pass_sim.py` §10 (censorship-resistance economics) produced two mandatory policy results:

   1. **Bond refill is MANDATORY** (added to the prototype, tested with TV-20).
      My first modeling assumed the bond was fixed — **wrong**: the bond is **depleted** at the
      first censorship event and subsequent events would be **FREE**, i.e. the deterrent would be
      **one-shot**. A `refill()` method was added: after every censorship event the bond is
      **automatically topped up to the fee level** (a governance mechanism).
      **TV-20 evidence:** over 3 censorship events — with refill, 3×100=300 slashed;
      without refill, **100 slashed (depleted at the first event, 2 events FREE)**.
   2. **Dynamic bond: `bond = fee + margin`** — the margin is an estimated off-game benefit
      (governance; measured in F3a). Table: if the off-game benefit is 40, bond=50 suffices
      (net +100); **if it is 120, even bond=200 is insufficient** (net −200). **A fixed bond
      cannot be set without measuring the margin.**
   3. **Sub-bond trap (from TV-17):** if `bond₀=50 < fee=100`, refill **raises** the bond
      **to the fee level** (50→100). So a sequencer starting with a low bond is pulled up to the
      fee level at the first event — this happens **mechanically, not as a policy**.

   **Previous toy note corrected:** I had written "the economic weight of the bond slash must be
   computed in F4" — **it was computed** (pass_sim §10) and produced the three policy results
   above. **This once again proves the value of the rule "translate proof claims into executable
   code": the economics model found a real gap in the prototype, and the spec was updated with it.**

**★★ UPDATE (2026-09-20): the margin has now been MEASURED —
`bond_margin_proto_en.py`, TV-31..TV-33. One spec correction, recorded honestly:**

- **TV-31 — the f3a slash is capped at fee.** In f3a's actual mode
  `slash = min(bond, fee)`, raising the bond above the fee is **inert**: bonds
  100/500/2000 (fee=100, B_out=60) all yield the **same net −40**. The deterrent
  is bounded by the **fee**, and the critical fee equals B_out. So the
  "bond = fee + margin" policy in item 2 above only takes effect if the protocol
  can slash **more than the fee** in one event. **Proposal:** add a FULL slash
  mode (`slash = bond` per event, with refill) to A.5.5 for severe censorship.
- **TV-32 — in FULL mode the margin is exactly linear:** margin = B_out − fee
  (max error 0.00, R²=1.0000). The §10 threshold equation is confirmed once the
  cap is removed.
- **TV-33 — the free-censorship window:** without refill, only bond/fee events
  are deterred (bond=300, fee=100 → 3 events); thereafter censorship is free
  (net +900 over 20 events). Refill closes the window (net −800).

## A.6 Formal properties (theorem skeletons)

- **T-A1 (Prescribed hardness ⇒ honest-Nash):** If (P1) holds and the block reward > 0, honest
  mining is an ε-Nash equilibrium: cheating strategies (choosing an easy input) **cannot reduce the
  work**, because prescribed hardness is independent of the input. (Depends on the KW conjecture;
  §A.9.)
- **T-A2 (No-replay):** thanks to the selected_parent component of ctx, any solution at depth N-1 is
  invalid for the Nth block (except a hash collision, 2^-256).
- **T-A3 (Fee liveness):** under the `C_fee` and anti-aggregation rules, a task density of g/7 in
  the DAG does not congest any block with peak fees; proof: per-block cap ≤ C_fee and tasks are
  processed in order.
- **T-A4 (Verifier incentive-security):** under the W_s window and the fraud reward, honest
  challenging is dominant (a reduction to the scheme of arXiv 2404.09005).

## A.7 Data availability

- In S1 the matrices **belong to the miner** — only the **certificate** (polylog size) goes to the
  network; the DA of the matrices is the miner's responsibility (they are already present in its own
  AI workflow).
- In S2 the task is given as a **commitment** (Merkle root), with **sublinear opening** in the
  solution; for large models, erasure-coded DAS + load distribution (proportional to the validator
  set size).

## A.8 Lifecycle (for S2)

```
submit → bond → (epoch seed commit) → VRF assignment → proof (S2) / cert (S1)
   → block inclusion → W_s-block fraud window → settle (fee + reward)
   → fraud proof: slash + reward to the challenger
```

## A.9 Fallback and cryptographic resilience

> **2026-09-19 update (after independent analysis — see `KW_ANALIZ.md`):** KW's security argument
> turned out to be **more robust** than presented. Assumption 6.4 (nearly automatic due to the
> Θ(n³/r) output-length lower bound) **is not necessary**: real security rests on (a) the
> unpredictability of σ in the ROM + (b) the **marginal uniformity** proof of Lemma 6.5 + Merkle
> one-wayness — all of these standard. Moreover, all structural attacks (sparse/permutation input,
> precompute, correlation shortcut) were refuted, and the **trapdoor-matrix** literature
> (VZ25 arXiv 2502.13065, BN25 arXiv 2502.13060) poses no threat (E,F are derived from σ; the
> attacker cannot plant a trapdoor). **Risk was revised from "high" to "low-medium."** The
> remaining principal risk is **the demand for utility (E-gap)**, not cryptography. Nevertheless the
> fallback is retained: it is no longer the #1 probable scenario, but it is not zero either.

> **★ 2026-09-21 correction — "A=B=0" was listed as refuted, but that is only true for *security*.**
> Choosing A=B=0 makes `A' = E` and `B' = F`, so every leaf becomes a direct product of ROM
> outputs. This **does not break the PoW** (the prescribed hardness still holds; KW's utility is
> defined by the honest algorithm, not by the attacker's input), so the old text was right about
> security. But the old text was **wrong to imply the utility claim survives**: with A=B=0 the
> computation carries **zero useful work**, and in **S1 mode the miner chooses its own input for
> free** (§A.1), so nothing in the G layer alone stops a miner from mining empty work while
> appearing to run the protocol.
>
> **The actual defense is the U layer, and it is architectural, not cryptographic:** a miner earns
> nothing from S1 work that nobody paid for, because the block's economic value comes from the
> fee-paying tasks it includes, and a block carrying no U task has `phi = 0` — still a valid block
> (the E-gap acceptance, TV-4) but earning only the baseline subsidy, not utility revenue. So the
> honest statement is: **S1 cannot be *forced* to be useful; it is *incentivized* to be.** This is
> precisely why the E-gap is an economic argument (§11) and not a theorem. **Recorded as a
> correction** — the word "refuted" for A=B=0 was overstated and is now scoped to security only.

- **Conjecture collapse:** if the KW hardness is broken, a **backup work function**
  (protocol-generated dense random MatMul + hash binding = pure-PoW mode) is activated by an
  on-chain signal. This is the full use of layer A of the §7 migration: **the work changes, the
  chain keeps living, but it is honestly called a "hard fork"** (unlike v1).
- **Open boundary:** the utility of S1 depends on miners **actually having an AI workload**.
  Otherwise kw certificates produce meaningless (but still secure) work → Pass's **Bitconia**
  decline (§C.4 scenario 5).
  → **2026-09-19 correction:** this open boundary does not hold; the utility of S1 is **not
  claimed** (Pearl's measured zero-utility result). S1 = G layer = security. The open boundary was
  replaced by the G/U distinction in §A.1.

## A.9b Arithmetic determinism — two ways of FP verification (2026-09-20, Pearl as primary source)

The KÖK v2 G layer today uses an **integer (INT) KW kernel** (q=97 toy field; for production, a
large modulus + transcript hashing). But if the U layer wants real AI workloads (BF16/FP8/FP4),
**verification of floating-point multiplication** is unavoidable. Pearl's new FP whitepaper
(September 2026) solved this problem, and **two concrete paths** emerged:

| | **Path A: Bit-exact replay (Pearl/Hawkeye)** | **Path B: Native-FP zkVM (Peigné et al.)** |
|---|---|---|
| Source | Hawkeye arXiv 2603.20421v2 (**MLSys 2026**) | arXiv 2606.05433v2 (44 pp.) |
| Idea | Re-produce the GPU Tensor Core operation on CPU **exactly, losslessly** (rounding direction, subnormal handling, accumulation order pinned); the verifier recomputes the selected tile | A **native BF16/FP32 precompile** into the zkVM; FP arithmetic is inside the circuit |
| Proof status | **in production** (Pearl mainnet, sm90 whitelist); Hawkeye = Badash, Boneh, **Komargodski**, Srivastava | ~**36-month** PoC horizon; 13 open problems |
| Source of determinism | whitelist GPU + pinned accumulation order (Tensor Core microarchitecture) | the circuit definition |
| Cost | verifier = recomputation of one tile (O(mnk/r²)) | zkVM proof generation (high, but Peigné claims single-digit % overhead) |
| Privacy | none (plaintext verifier; Pearl covers this separately with a Plonky2 ZK appendix) | yes (native) |
| Hardware lock-in | **yes** — sm90 (H100/H200) whitelist; a new GPU = a new Hawkeye table | none (the circuit is portable) |
| Role in KÖK v2 | **the proposed path for the Phase 2 G layer** (works today, proven) | **Phase 3+** (in parallel with the crypto-agility plane; §7 layer C) |

**Decision:** the KÖK v2 G layer **adopts Path A** (Hawkeye-style bit-exact replay + GPU whitelist),
because (i) it is proven in production today, (ii) Komargodski is also the author of KW — the two
lines are intentionally merged, (iii) Pearl's jackpot policy (TV-11..TV-14) is built on top of Path
A. **Path B is kept as "the path of the future" on the §7 crypto-agility plane** (it overcomes the
whitelist lock-in; it brings native privacy). **Honest risk:** Path A ties KÖK v2 to specific GPU
generations — this makes the ASIC-centralization concern of §11 **manageable but real**; extending
the whitelist requires a governance process. That process is **defined now** (it was previously
deferred to Phase 2 without a design — an unacceptable open item):

**§A.11 GPU whitelist governance (defined, not deferred)**

The whitelist is a list of `(GPU model, driver, accumulation order)` triples for which the G kernel
is bit-exact. Adding an entry is a **protocol change**, not an operator choice, because it changes
the set of hardware that can mine.

1. **Proposal.** Anyone submits a candidate triple plus a **bit-exactness dossier**: a reference
   device, a pinned driver, and the full set of test vectors (§A.10.7) reproduced on that device.
2. **Verification period — 2 epochs.** Any node may run the dossier on independent hardware of the
   same model. A disagreement is a contested proposal. This is the only part of the process that is
   empirical: bit-exactness cannot be argued, only reproduced.
3. **No false-accept tolerance.** A proposal that fails on **any** reporting device of the same
   model is rejected. The burden is on the proposer, because a false accept lets one hardware
   class produce proofs that the rest of the network cannot verify — the exact failure Path A exists
   to prevent.
4. **Activation via the versioned-schema path** (§A.9): the new triple enters with a schema version;
   blocks citing it before activation are invalid. No flag day.
5. **Removal is symmetric.** A whitelisted triple that stops being bit-exact (driver change,
   microcode) is removed by the same path, with the same 2-epoch window. Mining on a removed
   triple produces unverifiable blocks and is slashed as an invalid proof.

**What this does NOT solve (honest):** the process is only as honest as the hardware population
reporting. A GPU model with few independent operators is verified by few parties. This is the
centralization risk Path A inherits, and the reason Path B (zkVM) remains the long-term answer —
a circuit verifies on any hardware, a whitelist does not.

**Structural difference of Pearl's FP scheme from KW (affects KÖK):** in Pearl, entrywise
quantization is nonlinear — `Q(A+N) ≠ Q(A)+Q(N)` — which breaks the low-rank shortcut; **thus the
tickets hash the output tiles directly, and no (n/r)³ transcript is needed.** KÖK v2's INT kernel
must remain tied to the transcript (in INT the low-rank shortcut is open; this is exactly the
subject of kw Assumption 6.4); the transition to FP (Phase 3) permits a transcript-less design only
via Path A/B.

## A.10 Full protocol pseudocode (U-layer task lifecycle)

> **2026-09-19: the reference implementation of this section works** — `u_layer_prototype.py`
> (standard library, deterministic SEED). TV-5..TV-10 + G replay rejection **all PASS**;
> TV-9 reproduced Basu's live Pearl kurtosis measurements (1.79 / 3.33 / 2.97) one-to-one at
> prototype level (1.81 / 3.58 / 3.04) and proved that adversarial input **passes** the naive
> control. The pseudocode below and the prototype share the same interface; the points where the G
> kernel and the VRF prototype stub are to be replaced with the real ones are marked in the code.

### A.10.1 State machines

```
Task:      DRAFT → COMMITTED → ASSIGNED → SOLVED → CHALLENGED? → SETTLED
                ↘ CANCELLED      ↘ EXPIRED     ↘ SLASHED
Miner:     IDLE → ASSIGNED → PROVING → SUBMITTED → PAID  (or SLASHED)
Verifier:  LISTENING → CHALLENGING → FRAUD_PROVEN | REJECTED
```

### A.10.2 Task submission (client)

```python
def submit_task(client, task_spec, fee, burn_rate, gas):
    # task_spec: {harness_id, program_commit: MerkleRoot, max_flops,
    #             public_inputs_commit, deadline: Height}
    assert fee > 0 and burn_rate in (0.0, 0.5]      # burn = Demirel's irrecoverable tax
    bond = fee * BOND_RATIO                          # sybil is expensive (against Lemma 1)
    burn = fee * burn_rate                           # irrecoverable from escrow: the source of security
    escrow = lock(client, fee + bond, until=deadline + W_s)
    burn_immediately(burn)                           # the protocol's burn address (cannot be spent)
    tid = H("task" ‖ client ‖ task_spec ‖ fee ‖ escrow)
    emit(TaskCommitted{tid, task_spec, fee, escrow_id, expire=deadline})
    return tid
```

### A.10.3 VRF assignment (from the epoch seed — against grinding)

```python
EPOCH_LOOKBACK = 64      # seed from block N-64: a miner cannot influence it today

def epoch_seed(height):
    blk = chain[height - EPOCH_LOOKBACK]
    return H("seed" ‖ blk.hash)

def assign_tasks(height, tasks):
    seed = epoch_seed(height)
    for t in tasks:                                  # independent assignment per task
        vrf_out, vrf_proof = vrf.prove(miner_vrf_key, seed ‖ t.tid)
        w = as_int(vrf_out) / 2**256                  # [0,1)
        if w < t.assignment_probability(height):      # stake/compute-weighted gate
            assigned[miner].append((t, vrf_out, vrf_proof))
    # The miner cannot CHOOSE its assigned task; it only accepts it or FORFEITS (bond slash)
```

### A.10.4 Miner: proof production + block solution

```python
def mine_block(miner, assigned_tasks, ctx):
    # G layer (every block, demand-independent):
    A, B = miner.choose_matrices()                    # serbest; prescribed hardness ne olursa olsun
    while True:
        nonce = rng()
        cert = kw.prove(A, B, ctx ‖ nonce)            # 1+o(1) overhead, ctx-bound (T-A2)
        digest = fs_transcript(cert).digest()
        if int(H(digest ‖ nonce), 16) < target:
            break                                     # block mined

    # U layer (inside the same block, optional; carries fees, NEVER any leader-election weight):
    proofs = []
    for t in assigned_tasks:
        harness = load_harness(t.spec.harness_id)
        witness = harness.trace(t.program, t.inputs)  # deterministic kernel + pinned order
        proofs.append(stark.prove(harness.air, witness, ctx ‖ t.tid))
    return Block{header, kw_cert=cert, u_proofs=proofs, nonce}
```

### A.10.5 Verification (node)

```python
def validate_block(blk):
    ctx = ctx_of(blk)                                 # selected_parent‖miner‖...‖proof_system_id
    if not kw.verify(blk.kw_cert, ctx ‖ blk.nonce):   return REJECT     # G layer
    if int(H(fs_digest(blk.kw_cert) ‖ blk.nonce),16) >= target: return REJECT
    fee_total = 0
    for (t, proof) in zip(blk.tasks, blk.u_proofs):
        if not vrf.verify(t.assignee, epoch_seed ‖ t.tid, proof.vrf):  return REJECT
        if not stark.verify(proof, t.program_commit):  return REJECT     # Lean-verified AIR
        fee_total += t.fee
    if fee_total > C_FEE:                              return REJECT     # anti-aggregation (T-A3)
    return ACCEPT
```

### A.10.6 Fraud window and slash (Verifier's Dilemma solution)

```python
def challenge(challenger, tid, proof):
    assert height <= proof.height + W_s               # W_s = 100 blok
    ok = recheck_with_independent_backend(proof)      # different proving backend
    if not ok:
        slash(proof.miner, proof.miner.bond)
        reward(challenger, FRAUD_REWARD)              # the challenger wins
    else:
        slash(challenger, challenger.bond)            # a malicious challenge
    settle(tid, winner)
```

### A.10.7 Test vectors (deterministic, for testnet)

| # | Scenario | Input | Expected | Criterion |
|---|---|---|---|---|
| TV-1 | Replay rejection | The same `kw_cert` with two different `selected_parent`s | **REJECT** the second | T-A2 |
| TV-2 | Prescribed hardness | Sparse A (an all-zero row) + random B | Certificate cost = ±2% of the dense input | KW W |
| TV-3 | Easy-instance failure | Permutation matrix A | Valid certificate, but the cost of `H(digest‖nonce)` does not change | KW W |
| TV-4 | Random-matrix utility | Mining without a U task | Block valid; marked as **φ=0** | E-gap acceptance |
| TV-5 | Fee escrow + burn | Task submit, fee 100, burn_rate 0.3 | 30 burned, 70 in escrow; sybil cost > 0 | Demirel Lemma 1 |
| TV-6 | Anti-aggregation | `Σfee > C_FEE` in a single block | **REJECT**, tasks shift to subsequent blocks | T-A3, 2505.21685 |
| TV-7 | Fraud slash | Faulty proof + evidence | The miner's bond is slashed, the challenger receives a reward | §A.10.6 |
| TV-8 | Zero-demand liveness | No U task over 1000 blocks | **All blocks valid**, the chain keeps living | Demirel Thm 2 |
| TV-9 | Kurtosis trap | Uniform-random matrices + kurtosis control | **Control invalid**: adversary with N(0,18) passes (Basu) | E-gap: distribution ≠ provenance |
| — | *prototype measurement* | Run TV-9 with `u_layer_prototype.py` | uniform **1.81** / nn **3.58** / adversarial **3.04**; adversarial **PASSES** the [2,4] threshold | Basu live: 1.79 / 3.33 / 2.97 |
| TV-10 | PQ downgrade | Block signed with an old non-PQ schema | **REJECT**; only `proof_system_id ∈ PQ_set` | §5 crypto-agility |
| TV-11 | **Entry liveness** (Pearl 5.1.1) | Rows whose peaks are τ_idle=8× larger than the noise | idle ratio > ε_idle=1/64 → **RED**; healthy ≈0 | No-noise-entries attack |
| TV-12 | **Noise floor** (Pearl 5.1.2) | Single-peaked row (the peak is adjusted to the per-tensor scale) | noise < σ_min=1 grid unit → **RED** | Low-local-entropy → special hardware |
| TV-13 | **Tamed products** (Pearl 5.1.3) | Identical rows (rank-1 tile) | tamed ratio > ε_tame → **RED**; typical workload passes | Coherent dot products |
| TV-14 | **Unpredictable summands** (Pearl 5.1.4) | Common-peak A,B (each cell a single summand) | predictable ratio > ε_pred → **RED** | FP precision shortcut |
| TV-15 | **Refund-guarantee** (§A.5.5-i, F3a) | Bad sequencer does not publish a rejection-step; W_r blocks pass | CENSORED → automatically **REFUNDED** (escrow=70, refund) | Benefit of censorship = 0 |
| TV-16 | **Task-migration** (§A.5.5-ii, F3a) | The rejected task goes to an alternative sequencer | bond 100 → 0 (**min(bond, fee)** slashed) + settles in B | Censorship **negative return** |
| TV-17 | **Censorship-freeness** (F3a) | All 5 tasks censored; 2 migrate, 3 time out | held escrow **0**; refund 210; bond 50 → 0 | The sequencer can **never** hold the escrow |
| TV-18 | **Dilemma-free verification** (§A.5.2, F3a) | Faulty verify → CHALLENGED; then correct verify | dilemma trigger 1 (monitored), SETTLED + burn 30 | Verification is mandatory, cannot be skipped |
| TV-19 | **Honest lifecycle** (F3a) | submit → assign → solve → settle | burn=30, refund=0, slash=0 | Basic flow |
| TV-20 | **Bond refill** (§A.5.5, the gap found in pass_sim §10 and added to the prototype) | 3 censorship events; refill YES vs NO | refill: **3×100=300** slashed; refill-NO: **100 slashed, 2 events FREE** (bond depleted at the first event) | The deterrent must **not** be one-shot |
| TV-21 | **Low-entropy resistance** (Polymath 6; the limit of TV-12) | Peaked attack, sweep v = 10→400 | **0/10 v passes** — noise/g asymptote ~0.707 < 1; in the toy **always RED** | ★ Not a proof in FP8 — the reverse direction (below) |
| TV-22 | **GHOSTDAG blue rule** (ePrint 2018/104; Kaspa mainnet k=18) | 60–90-block DAG, 25–50% fork rate; mergeset-anticone of every blue block | **all ≤ k=18** (77 blue) | Blue selection rule applied correctly |
| TV-23 | **selected_parent = max blue_score** | 74 blocks; each selected_parent compared against its own parents | **every** selected = highest blue_score (ties: lowest hash) | Selection rule deterministic and correct |
| TV-24 | **Mergeset size limit** (2k = 36) | 80 blocks, 40% fork; mergeset sizes | **max = 36**, never above the limit | Production limit honored |
| TV-25 | **ctx binds the parent set** (T-A2 strengthened) | Same (miner, task, height) block, different parent set | **different ctx** ⇒ second one REJECT | Replay protection closes at parent-set granularity |
| TV-26 | **Splitter attack (liveness)** | 3 miners, 50% fork = DAG-splitting attempt; 137 blocks | recent-block mean order length = **64** (47% of the DAG); no block has an empty order | Total ordering preserved under attack |
| TV-27 | **FP8 subnormal compression** (Pearl FP8 wp) | E4M3 grid; entries below 2⁻⁹ | **100%** flush to 0 | FP8 quantization is nonlinear, as Pearl §5.1.2 states |
| TV-28 | **FP8 low-entropy attack — NEGATIVE** | small-magnitude near-identical rows, no noise floor | output tiles pin to **1 value** (entropy 0.00) | Attack SUCCEEDS in FP8 — the reverse of TV-21; σ_min is MANDATORY |
| TV-29 | **Noise floor closes the attack** | same attack, σ_min = 8 quantized units | tiles spread to **13 distinct values** | The FP8-aware noise model closes the TV-28 attack |
| TV-30 | **Entry liveness grinding — SPEC CORRECTION** | 500-seed worst case, τ_idle=8, ε_idle=1/64 | DELTA=0.5 → **6.64%**; analytic 0.217 → **3.52%** (both exceed); DELTA=0.06 → **1.37%** (passes) | DELTA must be ≤ 0.06; average-case bounds insufficient |
| TV-31 | **Capped slash bound — SPEC CORRECTION** | f3a mode slash=min(bond,fee); bond ∈ {100,500,2000}, fee=100, B_out=60 | all three bonds give the **same net (−40)** — the slash saturates at fee; critical **fee = B_out = 60** | Raising bond above fee is inert; "bond = fee + margin" needs the FULL slash mode |
| TV-32 | **FULL-mode margin is linear** | slash=bond; fee=100, B_out ∈ {120,150,200,300,500} | margin = B_out − fee with **max error 0.00, R²=1.0000** (B_out=300 → margin=200) | The §10 threshold equation holds exactly in FULL slash mode |
| TV-33 | **Free-censorship window** | bond=300, fee=100, N=20; refill on/off | no refill: net **+900** (profitable) after a 3-event window; with refill: net **−800** | Refill is mandatory; without it only bond/fee events are deterred |

**TV-21 (low-entropy, Polymath 6) — honest boundary:** the attacker swept the peak v from 10→400;
**no v passed** (noise/g asymptotic ~0.707 < SIGMA_MIN=1). Beneath this "nice" result lies **a
toy-model fallacy**: in the toy the noise is `DELTA·RMS(row)`, and as the peak grows the RMS grows
at the same rate → the ratio stays constant. **In Pearl's FP8 reality (wp §5.1.2) the peak forces a
per-tensor scale-up and squeezes the noise toward zero** (a reduced-alphabet hardware advantage).
So in FP8 the direction of the attack is the **reverse** of the toy's: while the toy always yields
RED, in FP8 there is a risk of ACCEPT. **Conclusion:** the toy result of TV-12 is valid for
INT/fixed-point; for FP8 the noise model must be **rewritten as quantization-aware** (per-tensor
scale + subnormal compression) — this must be done in Phase 3 in the context of Path A (Hawkeye).
(This is exactly why we injected `ACC_NOISE` in TV-14.)

**★★ UPDATE (2026-09-20): the FP8 toy noise model has been WRITTEN —
`fp8_noise_proto_en.py`, TV-27..TV-30. Two negative results, recorded honestly:**

1. **The reversal is CONFIRMED (TV-28).** Without an absolute noise floor, the
   low-entropy attack SUCCEEDS in FP8: output tiles pin to **1 value (entropy
   0.00 bits)** when the attacker uses small-magnitude near-identical rows.
   The INT toy (TV-21) always yielded RED; in FP8 the direction reverses, exactly
   as predicted above. **Conclusion: the noise floor σ_min is MANDATORY for FP8**
   — not an optimization, a hard requirement. With σ_min = 8 quantized units
   (TV-29) the tiles spread to 13 distinct values and the attack closes.

2. **DELTA must be lowered from 0.5 to 0.06 (TV-30) — spec correction.**
   Pearl SS5.1 entry liveness (τ_idle=8, ε_idle=1/64) requires the dwarfed-entry
   fraction to stay below 1.56% **under seed grinding**. Measured worst case over
   500 seeds: DELTA=0.5 → **6.64%** (exceeds). The analytic average-case bound
   DELTA ≤ √3·τ·ε = 0.217 → **3.52%**, *still exceeds* — because grinding selects
   the fluctuation tail of RMS. The real grinding-resistant bound is **DELTA ≤ 0.06**
   (1.37%, passes). **Methodological note:** average-case analysis is INSUFFICIENT
   for grinding-resistant parameters; only worst-case-over-seeds bounds are valid.

**Remaining honest limits of `fp8_noise_proto_en.py`** (listed in the file header):
simplified FP8 (RNE + subnormal flush), **not IEEE-754** — real hardware differs
with RNE/RZ and tensor-core accumulation, which is why Hawkeye bit-exact replay
is mandatory; r=2 toy rank (Pearl: r=32 for k ≤ 2¹⁶), not an asymptotic proof;
Q(A+N) modeled as a single add-then-quantize rather than per-MAC.

**Source note for TV-11..TV-14:** a toy INT adaptation of the Pearl "Floating Point Scheme
Specification" (September 2026) §5.1 — the `JackpotToy` class inside `g_layer_tests.py`; K=64,
GRID=16, DELTA=0.5, ACC_BITS=8. Measured results (2026-09-20, all PASS):

| Test | DEGENERATE input (RED) | Healthy input (ACCEPT) |
|---|---|---|
| TV-11 | 2-peak rows: idle **3.12%** > 1.56% | uniform: **0.00%** |
| TV-12 | single-peak: noise **0.52** grid unit < 1 | uniform: **2.05** grid units |
| TV-13 | rank-1 tile: tamed **100.0%** > 12.5% | random: **0.5%**; B=A: 1.7% (loose net) |
| TV-14 | common-peak: predictable **98.4%** > 25% | random: **0.7%** |

**The advantage of TV-11..TV-14 over TV-9:** TV-9 (kurtosis) was **bypassed by the adversary** on
Pearl's live network (N(0,18) → 2.97, past the [2,4] threshold). Pearl's four production controls
instead look at **structural** properties (the size of the noise budget, the room left in the grid,
coherence, truncation) — not at distribution parameters. **The KÖK v2 G layer adopts these four
controls; the kurtosis control remains only a warning (TV-9).**

**Known limits of the toy adaptation (honest):** (1) the noise is iid, not rank-r — since the
1st/2nd/4th controls of §5.1 are per-entry/per-row statistics, the structure is preserved, but this
is not the exact counterpart of Pearl's production rank-r analysis; (2) the tamed/unpredictable
thresholds were calibrated to the toy scale (K=64); Pearl's production values (τ_tame=256) are for
k~4096-16384; (3) the toy's 16-level linear grid cannot express FP8's non-uniform grid + the scale
separation of the FP32 accumulator — this is why TV-14 accumulation-side noise is injected at the
sub-quantization scale (ACC_NOISE=1/16 grid unit) (in Pearl this scale comes from FP8 subnormal
compression); (4) whether σ_i is per-entry or row-level was not clear from the Pearl text; the toy
chose per-entry (RMS-based). **These limits prove the discriminative power of the four controls; not
the production calibration.**

**TV-9 is particularly critical:** it ensures that Pearl's measured failure (uniform matrices with
kurtosis 1.79 are distinguishable from NN weights with 3.33, but adversarial Gaussian with 2.97
passes the control) is tested **as a warning, not as a control**. **Lesson: a distribution control
is not a proof of utility; only a fee-paid task is a proof of utility.**

---

# APPENDIX B — DIFFICULTY AND BLOCK-PRODUCTION MATHEMATICS

## B.1 Model

Every **attempt** `a`: production of a KW certificate for a MatMul instance (cost `h(n)` FLOPs).
The attempt is **successful** iff

```
H( cert_digest ‖ nonce ) < target,   target = 2^256 / D        (D = difficulty)
```

`cert_digest` is the digest of the FS transcript (together with the nonce). Under a random oracle,
the success probability of every attempt is `p = 1/D`.

## B.2 Block arrival process

- Miner `i` has attempt rate `ρ_i = c_i / h(n)` (c_i = FLOP/s capacity). Total `Λ = Σ ρ_i`.
- Success process: **Poisson**, rate `λ = Λ/D`. Block intervals `Exp(λ)`, mean `E[T] = D/Λ`.
- **Result:** inter-arrival is exponential and memoryless → **all of Bitcoin's difficulty/extraction
  mathematics applies verbatim** (variance, ARA effects, selfish-mining resistance analyses
  transfer).
- GHOSTDAG: block target `T_b = 1/λ_b` (e.g. 100 ms = 10 BPS); every block arrives with its own ctx
  and parent set; the GHOSTDAG rule orders them.

**★ Working prototype (2026-09-20):** `ghostdag_proto_en.py` — TV-22..TV-26, all
PASS. It validates the GHOSTDAG greedy mergeset + selected_parent + blue_score
core with **Kaspa mainnet's real production parameters**: `k=18` (BPS=1),
`max_block_parents=10` (floor 10 / cap 16), `mergeset limit=2k=36` (from
rusty-kaspa `config/bps.rs`). The KÖK v2 addition: **ctx now includes the
parent-set hash** (TV-25), which strengthens T-A2 replay protection down to
parent-set granularity.

**Toy limits** (listed in the file header): **there is NO PoW/validity check** —
every block is assumed to carry valid PoW. Because GHOSTDAG's security argument
(anticone probability bounded by k) rests on PoW, this prototype validates only
the **DAG logic**. Network delay is a uniform model; `_future()` is O(n²)
(tracked incrementally in production); k=18 is the Kaspa BPS=1 template, KÖK
v2's own BPS is not yet chosen.

## B.3 Retarget algorithm (formal)

Let `T_act` be the elapsed time over a window of `W` blocks; the target block time is `T_b`:

```
Lambda_hat = D · W / T_act                       // hash-rate estimate, independent of D
Lambda_smooth = median( Lambda_hat of the last <=3 windows )   // median filter
D <- clip( Lambda_smooth · T_b ,  D/4,  4·D )    // Bitcoin'in 4x sinirlari
```

> **2026-09-19 correction (important):** in the previous version the ratio was written as
> `T_act/(W·T_b)` — **it was inverted** (D is difficulty, §B.2/§B.4: `p = 1/D`, `E[T] = D/Λ`; the
> inverse of Bitcoin's "target" value; if blocks are slow, D must decrease). Moreover, the
> combination of the simple ratio formula + the median filter would produce a **stale-ratio bias**
> (each window's ratio belonged to an old D). The correct formula extracts a **hashrate estimate
> independent of D** from each window: `Λ̂ = D·W/T_act` (because the block rate is `Λ/D`, i.e.
> `T_act/W = D/Λ`). This estimate is independent of D, therefore a median can be taken across
> windows. The prototype `u_layer_prototype.py` + `g_layer_tests.py` (RT-1..RT-3) confirms this:
> from 10× away from equilibrium it converges to `Λ·T_b` in 2 windows; under a 10× sudden hashrate
> jump the per-window change is ≤4×.

- Instead of the window `W = 2016` (Bitcoin), for the DAG **W = 1000 blocks** (~100 s @10 BPS) →
  faster adaptation; but the **4× limit** for noise is retained (it prevents excessive
  oscillation).
- Additional protection: **median filter** (the median of `Λ̂` over the last 3 windows) — prevents
  the retarget from locking onto a single window during sudden hashrate swings. Side effect: the
  response to a genuine hashrate jump is delayed by 2 windows (a security feature, not a bug).

## B.4 Difficulty unit and miner predictability

- Difficulty `D`, in terms of **"expected proof-FLOPs"**: `D = E[FLOP] / h(n)`? No — directly: the
  expected number of attempts `E[k] = D`; the expected work `W_b = D·h(n)` FLOPs/block.
- Miner share: `ρ_i/Λ` (proportional, as in Bitcoin).
- **Worked example:** `T_b = 100 ms`, `h(n) = 2·10^12 FLOPs` (e.g. a 1K×1K MatMul ~2 TFLOPs),
  network `C = 10^17 FLOP/s` (≈ 100× H100): `Λ = C/h = 5·10^4 attempts/s`; `D = Λ·T_b = 5000`;
  `p = 2·10^-4`. The expected work per block `W_b = D·h = 10^16 FLOPs` = 100 H100-seconds. ✓
- **Consistency:** `W_b = C·T_b` — i.e. per block the network spends its total capacity over `T_b`
  time (the nature of the universe; energy = `C·T_b·e'`).

## B.5 Work-supply coupling (liveness equation)

- **S1 density** `φ ∈ [0,1]`: the fraction of the network's attempts that corresponds to real AI
  workloads.
- `φ = 1` (every attempt is real work): full 2-for-1; `φ = 0`: pure-PoW filler (protocol-generated
  dense random MatMul). Liveness is **always** preserved (filler is unlimited); **utility** depends
  on `φ`.
- **Task-gap equation:** `λ_tasks ≥ λ_b·(1−φ)` — if S2 task demand cannot keep up with the block
  rate, filler kicks in. This is the technical condition of scenario 5 in §C.4.

## B.6 Limits and infinitude conditions

- **Block time floor:** `T_b ≥ t_cert + t_prop + t_verify`; the KW certificate production time per
  attempt is `h(n)/c_i` → if `T_b` is too small, not even a single attempt can be completed
  (practical lower bound ~50–100 ms).
- **Size of the certificates:** polylog; the total proof bandwidth at 10 BPS in the DAG must be
  computed (ZK-ACE's per-block STARK aggregation: ~160 B/tx).
- **Soundness protection:** soundness 2^-128 → the verification threshold `λ ≥ 128`; the KW/STARK
  parameters accordingly.

---

# APPENDIX C — ON-CHAIN ECONOMIC SIMULATION SPEC BASED ON THE PASS MODEL

## C.1 Implementation of the model (Pass 2606.06700)

**State variables (each epoch `t`):** activity `M_t, L_t, D_t`; prices `p_t, P_t`; token emit
`R_t`; compute-op cost `e` (constant); duplex overhead `α, γ`.

**Equation set:**
```
S = M + D/γ                                    (security)
Q = L + D/α                                    (inference supply)
π_M = P·R/S − e ≤ 0,     π_M = 0 iff M > 0
π_L = p − e ≤ 0,         π_L = 0 iff L > 0
π_D = P·R/(γS) + p/α − e ≤ 0,  π_D = 0 iff D > 0
Q = 𝒟(p)                                      (market clearing)
θ = P·R / (p·Q)                                (T/I ratio, assumed constant)
```

**Demand:** isoelastic `𝒟(p) = K·p^(−ε)`, `ε > 1` (default `ε = 2`).

**Numerical solver:** mixed-complementarity problem (MCP) — for each (Δ, θ) grid point, the
zero-profit conditions are solved over the combinations of activity patterns `{M,L,D}`; verified
against the regime classification of Theorem 1:
`Δ = 1/γ + 1/α − 1`; `θ_low = α−1`; `θ_high = 1/(γ−1)`.

## C.2 Parameter table (default values)

| Symbol | Meaning | Default | Source/justification |
|---|---|---|---|
| `e` | compute-op cost | $1 | Pass (all-in GPU-blocktime) |
| `α, γ` | duplex overhead | 1.3 | Pass's KW instantiation (≈23% loss) |
| `R_0` | first block reward | 50 KOK | fair launch |
| `ρ_em` | emission decay rate | 0.5/4y (descent to the tail) | §C.6 |
| `R_∞` | **tail emission** (never becomes 0) | 2 KOK | base of the security budget |
| `τ` | treasury share | 5% | consistent with fair launch |
| `ε` | demand elasticity | 2 | the Jevons assumption |
| `θ` | T/I ratio (scenario axis) | 0.1 → 10 | comes from the monetary primitives |
| `ν, λ, V` | stock-flow + velocity | 1, 0.1, 10/epoch | `θ = λθ_raw/(νV)` |
| `C` | network FLOP/s | 10^16 → 10^18 | technical input of the simulation |

## C.3 Simulation scenarios (each ≥1000 epochs)

1. **Launch (low θ, θ<θ_low):** target regime **Fortessia** (security ↑, utility constant).
   Acceptance: `S > S^Bitconia` and `p = e`.
2. **Adoption growth (θ rises):** the Fortessia → Duplexia transition; `p = αe/(1+θ) < e`.
   Acceptance: the price decline is within ±5% of the theoretical curve.
3. **Technology improvement (α,γ → 1.05):** Δ ↑; how does the social value `ΔSV` change?
   (Theorem 3: deadweight loss and duplex overhead decrease.)
4. **Demand shock (K decreases 10×):** the inference market shrinks; θ effectively ↑.
5. **Zero useful demand (φ→0):** **the Bitconia decline.** Acceptance: the network stays alive in
   pure-PoW mode (filler tasks), and the security budget stays at the `R_∞·P` base.
6. **Attack cost over time:** `cost_attack(t) = P·R/2` (Pass: in all regimes). Acceptance: it never
   falls below the Bitcoin-equivalent in any epoch (Pass Corollary).
7. **Pooling/aggregation risk (Pass §1.8):** a single address's block share > 20% → **alarm**.
8. **Stock effect:** the GPU value-loss rate `1 − ρ^ε/α` (ρ=p/e) — post-attack deterrence.

## C.4 On-chain indicator dashboard (published every epoch)

`S, W (waste = M + D(1−1/α)), S−W = DΔ, p, P, R, θ, Δ, φ` (S1 density),
`cost_attack = P·R/2`, `ΔSV` (Theorem 3/Prop 1), regime label
(Bitconia/Fortessia/Duplexia).

**Alarm thresholds:** `cost_attack < $X_min`; `θ > θ_high` (excessive subsidization);
`φ < 0.2` (loss of utility); single-address share > 20%.

## C.5 Monetary policy (emission curve, exact formula)

```
R(t) = max( R_∞, R_0 · 2^(−⌊t/T_half⌋) )         T_half = 4 years
hazineden: h(t) = τ · R(t), τ = 0.05              (escrow + milestone vesting)
total supply: ∫R dt = finite cap + infinite tail   (tail: R_∞ unbounded, decreasing total)
```

**Design rule (honest):** Kaspa's curve running out in 2026 (96.5% of the max supply already
emitted) zeroes the network's security budget; `R_∞` prevents this. **The curve is published once
and cannot be changed** (a change = the greatest breach of trust).

## C.6 Simulation acceptance criteria (Phase 4 gate)

1. Across the entire (Δ, θ) grid, the solution matches the closed form of Theorem 1 (numerical
   error < 1%).
2. In scenario 5 the network stays alive and `cost_attack ≥ Bitcoin-equivalent` is preserved.
3. In scenario 6 the attack cost never falls below the threshold even while being non-monotonic in
   any epoch (proof of the tail-emission effect).
4. Scenario 7 alarm: as `φ` drops (loss of utility), does `θ` rise? — an analysis report.
5. **Social value:** does Duplexia surpass Bitcoin at the same θ (θ < 1/(ε−1) → for ε=2, θ<1)?
   Proven theory + an overlapping simulation is required.

## C.7 Known limits of the model (honest)

- **Single-period approximation:** no dynamic speculative behavior (Pass himself left this out).
- **Constancy-of-θ assumption:** that the monetary primitives are stable is treated-as-empirical
  (Pass's own exploitation); sudden changes can disrupt the transition process → tested with
  scenarios 2/4.
- **No demand-pull friction (Pass §1.8):** in the real world, duplex miners must find customers →
  **aggregation risk**; monitored with scenario 7 in the simulation, but not modeled.
- **Constant e:** for heterogeneous costs, the upward-sloping supply extension of Pass §7 is needed
  (to be added in Phase 4).
- **★ Scale-validity limit (2026-09-20, found from the `pass_sim.py` §9 hook):** the model is valid
  **only at mainnet scale**. F3a's small network (~1200 miners) **cannot recalibrate** the model —
  a hypothetical test gave an **86% deviation**. Root cause: Pass Thm 2 says "in any competitive
  equilibrium" while assuming a competitive equilibrium; in small networks the fixed costs
  (infrastructure/opex) dominate the marginal, and the equilibrium breaks. Pass's own calibration
  is over a $30B inference market / 52,560 block-years. **Practical consequence:** F3a data
  measures U-layer demand (φ>0), it does **not** calibrate the Pass model; the calibration of the
  model stays at Pearl scale (protected with a regression-guard). This required correcting the
  related claim of V2 §10.1 — **corrected**.

## C.8 Working simulation — results (`pass_sim.py`, 2026-09-19)

The code was run and verified (`python3 pass_sim.py`, output `sim_out.txt`). **Key findings:**

1. **Pearl calibration (validation):** the model's Tullock full-payment condition `eS = PR`
   produced Pearl's measured network from first principles: `S = PR/e = 338,707` GPU-op/block vs
   **measured 320,000 GPUs (5.8% deviation)**; revenue/cost ratio **1.058** vs Basu's measured
   **1.06**. → the model can explain a live PoUW chain.
2. **Theorem 1 regime map:** at all θ values the zero-profit residuals are `< 1e-9`, the passive
   violations `0`, the market-clearing error `< 1e-12`; θ<0.3 → Fortessia, θ>0.3 → Duplexia;
   θ>3.33 → mixed.
3. **Pearl's regime diagnosis:** Pearl's real PR level falls into **endogenous θ = 1.05 → pure
   Duplexia**. That is, Pearl's economy **was already in the regime that subsidizes inference** —
   yet the measured φ = 0: no utility ever materialized. The reason is the **E-gap** (Demirel): the
   protocol could not certify that the matrices were anyone's work. **Pearl behaved like Bitconia
   and was marketed like Duplexia.**
4. **Fortessia:** at the same θ, security increases by exactly `1/(γ(1−1/α)) = 3.33×`, with utility
   unchanged (an exact overlap with the theory).
5. **Tail emission:** as the halvings lower R, the economy descends from Duplexia to Fortessia
   around the 14th year, and the attack cost settles at a **$0.76 floor** with `R_∞ = 2` PRL — it
   does **not** go to zero like Kaspa.
6. **Zero demand (K→0):** Q→0 but **S→PR/e**; the chain lives as pure-PoW (Demirel Thm 2 ✓). This
   is the formal admission that the promise of **"useful work = security" does not exist**: security
   is demand-independent, and utility exists only in the U layer's fee-market.
7. **Heterogeneous cost (b=0→1):** S decreases by 38% but the current attack cost is still PR/2;
   stock effects are outside the model (the limit stated by Pass).

**Status of the acceptance criteria §C.6:** (1) ✓ overlap with Theorem 1, (2) ✓ liveness under zero
demand + Bitcoin-equivalent security, (3) ✓ the tail-emission floor, (4) partially — the pooling
scenario 7 was not modeled (only the φ indicator), (5) ✓ the θ<1/(ε−1) threshold was verified
theoretically (ε=2 → θ<1).

---

# PERFECTION CHECKLIST (paper verification)

**Cryptography (every item must be open to independent review):**
- [ ] The prescribed-hardness theorem of the KW construction was reviewed by **independent
      cryptographers** (the status of the conjecture clarified: low-rank random linear equations).
      *2026-09-19: a first-pass independent analysis was done (`KW_ANALIZ.md`) — the risk dropped to
      *low-medium, but this is an LLM's reading, NOT a human cryptographer's review; the box remains
      open.*
- [ ] The ctx-binding formal lemma was written (T-A2) and proven in the random-oracle model.
- [ ] For S2, the **sound verification of the STARK AIR in Lean** (the S-two model, arXiv
      2606.04311) + **ZEBRA-class automatic cardinality checking** (arXiv 2609.15020) — the target
      is 0 under-constrained bugs.
- [ ] Soundness parameters λ ≥ 128; field size ≥ 256-bit; soundness recomputed after aggregation.
- [ ] PQ: STARK/hash + signatures via **ZK-ACE** (arXiv 2603.07974); no non-PQ primitive remains.
- [ ] Crypto-agility: versioned schemas + a dual-verification window + an emergency fallback (§A.9)
      **documented, with test scenarios**.

**Protocol:**
- [ ] The task-marketplace spec (§A.1–A.8) was completed with pseudocode + test vectors.
- [ ] The anti-aggregation rule and the `C_fee` limit are compatible with the DAG ordering (the
      T-A3 proof).
- [ ] The difficulty retarget algorithm (§B.3) passed the oscillation test in simulation (the 4×
      limits + the median filter).
- [ ] The lifecycle (§A.8) contains a slash proof for every crime class.

**Economy:**
- [ ] The Pass model simulation (§C.3) passed the acceptance criteria of **all** 8 scenarios (§C.6).
- [ ] The emission curve (§C.5) was published as unchangeable; the tail emission was proven.
- [ ] The indicator dashboard (§C.4) is readable on-chain and the alarm thresholds are defined.

**Legal/transparency:**
- [ ] The Howey analysis + the TR licensing regime review were completed (open point: findings §12).
- [ ] A **differentiation table** was published against Pearl Network (built on ePrint 2025/685):
      KÖK v2's contribution = GHOSTDAG + the crypto-agility plane + tail emission + a premium SNARK
      service layer; the **KW core is shared** (cited, not plagiarized).

**"Perfection on paper" criterion:** with every box above checked = **85/100** at the spec level
(the remaining 15 = testnet + independent audit + real demand; it cannot be won on paper).

---

## F. The Pearl verification gap — why our kernel does not have it (2026-09-21, TV-38)

Sources: `arastirma/pazar_ve_rekabet_2026.md`, `u_layer_prototype_en.py` TV-38.

### F.1 What happened at Pearl (measured, not assumed)

Pearl ran 24 EH/s on ~320,000 GPU-equivalents (~112 MW) and sold **zero** useful
computation. The *mechanism*: the dominant mining software contained **no inference
code**, and verification **accepted random matrices**. The protocol could not tell
real work from theatre, so it got theatre. **This is a protocol design error, not a
miner-honesty problem.**

### F.2 Does our kernel have the same flaw? (tested: no)

| Attack | Result of `verify()` |
|---|---|
| Fabricated certificate (no MatMul computed) | **REJECT** |
| Forged tile value (correct coordinates, uncomputed value) | **REJECT** |
| Wrong input matrices (real cert, A or B changed) | **REJECT** |
| Honest certificate | ACCEPT |

### F.3 The mechanism — structural, not accidental

`verify()` recomputes the claimed tile from A, B and the ROM-derived noise:

```
acc = sum_l  (A[i*r][l*r] + E[i*r][l*r]) * (B[l*r][j*r] + F[l*r][j*r])  mod q
return  acc == val  AND  H("tile", ctx, nonce, i, j, val) % target == 0
```

- **A and B are inputs to verify()**, so changing either breaks the equality.
- **E, F come from the ROM seeded by ctx**, so the miner cannot choose the noise.
- **The target hash is over the tile value**, so only the *correct* value counts.

**Pearl's verifier did not bind the certificate to the computation; ours does.**

### F.4 Remaining gaps (recorded, not closed)

1. A tile is small (m = n/r): verify() recomputes one tile, not the whole MatMul.
   **The "skip tiles" concern was analysed and dismissed**: H is one-way, so a miner
   cannot predict which value hits the target and must compute a tile to see its
   chance; skipping the rest only lowers its own odds. The true design point is the
   opposite: each nonce grants m² chances, which multiplies expected work and is
   already measured by TV-2 (geometric hardness 4.4/4.4/4.5).
2. q = 97, n = 8, r = 2 are toy sizes; asymptotic security cannot be claimed.
3. H is SHA-256-ish HMAC in the prototype; production needs a STARK-friendly hash.

**Strategic weight: F.2-F.3 are the most defensible technical difference from Pearl,
now a running test rather than a claim. F.4 is why F0b (a real AIR) is prioritised.**
