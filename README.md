# KÖK Network v2

> ## STATUS — 2026-10-18: the L1 phase ended; evolution to Option C
>
> **The L1 path is closed.** The kill criterion (`KOK_V2_PAPER.md:1913` —
> "if F3a finds zero real demand, the project must stop") fired before F3a
> ever started: F0 demand discovery closed with **0 interviews**, Demirel has
> not answered in 4 weeks, and arXiv's 21-Jan-2026 endorsement policy shut
> that door. **388 commits, zero external artefacts.**
>
> **What replaces it:** a receipt that a compute provider actually performed
> the MatMul job it claims — independently verifiable, anchored into Tamga's
> hash chain and x402's proof-of-done extension. **No mining, no token, no
> L1.** Decision and the 43-URL research:
> `docs/KOK_EVOLUSYON_ARASTIRMA_2026-10-18.md`. L1 documents:
> `docs/historical_l1/` (not deleted — a readable court record).
>
> **The L1 pitch below is historical.** It still explains why the design was
> correct; it is no longer the thing being built.

**Proof-of-Useful-Work L1 with a modular two-layer consensus design.**

KÖK v2 separates the two jobs that prior PoUW designs conflated:

- **Layer G (security)** — a Komargodski–Weinstein / cuPOW matrix-multiplication
  proof-of-work with memoryless difficulty. Leader election is demand-independent
  by construction, which is what Demirel's "Proof of Demand Is Not Proof of Work"
  (ePrint 2026/1492, Theorem 2) requires. The utility never touches the
  security budget.
- **Layer U (utility)** — a fee-paid verifiable-compute market with escrow,
  bond, and an irrecoverable burn. It carries the useful work but **never elects
  leaders**.

The E-gap (utility ≠ security) is architected exogenously rather than assumed away.

---

## In 30 seconds

A proof-of-useful-work chain whose mining work is matrix multiplication, split into
two layers that cannot influence each other: **layer G elects and orders blocks** on a
MatMul proof-of-work whose hardness is structural (the noise matrices come from a
public context, so a miner cannot shop for a friendly instance); **layer U carries
fee-paid verifiable-compute tasks** assigned by a VRF over an epoch seed fixed 64
blocks back — and contributes **exactly zero consensus weight**, so no one can buy
security by buying demand for the useful work. No premine, no sale, no issuer: the
asset is emitted to miners from genesis. It is **pre-testnet** — a paper, a spec and
runnable prototypes, not a chain.

**What "modular consensus" means here, and what it does not.** It is *not* the
blockchain-literature meaning of separating consensus / execution / data-availability.
KÖK separates **security from utility**: leader election depends on nothing the fee
market can influence. That distinction is deliberate. The literature's meaning is not
absent — it is verified and cited: Xu et al., *Exploring Blockchain Technology through
a Modular Lens: A Survey* (arXiv 2304.08283) and Al-Bassam, *LazyLedger*
(arXiv 1905.09274, the Celestia line) decompose a chain into network / consensus /
ledger and data-availability / execution modules respectively. Neither axis is KÖK's:
the KÖK axis is a *weight* separation (`u_task_consensus_weight = 0`), positioned in
the PoUW literature as **"Anti-Pearl"** — Basu measured Pearl's live cuPOW network at
24 EH/s / ~320,000 GPU-equivalents / ~112 MW producing **zero useful AI computation**
with verification accepting random matrices *by design* (arXiv 2606.04819). Full
positioning in
[`docs/arastirma/moduler_konsensus_ve_veri_2026.md`](docs/arastirma/moduler_konsensus_ve_veri_2026.md) §0 ([D11]/[D12]).

### Commands that actually run

```bash
cargo test --workspace --all-targets      # 397 passed, 0 failed (verified 2026-10-18)
python3 -m pytest tests/ -q               # 1.568 passed, 0 failed (verified 2026-10-18, 223.27 s)

# Mine a G-layer proof, then verify it off-chain with no secrets and no network:
cargo run -q --bin kok -- create --ctx 20261020 --target 2 --out kanit.json
cargo run -q --bin kok -- verify kanit.json
```

The Rust suite now includes the **verified protocol result**: the AI-utility
score **cannot** change the mining reward distribution or scale
(`u_task_consensus_weight == 0` at every fee and proof count), measured by
`crates/kok-consensus/tests/madencilik_odul_testleri.rs`. See
`docs/arastirma/pouw_ai_madenciligi_2026.md` §7.

`verify` re-derives the MatMul tile, the program/input commitments, the Ed25519
`did:key` signature and the sha256 receipt from the document's own contents — the same
code a third party would call, which is the point: the useful work is independently
verifiable off-chain.

---

## Status

**This is a pre-testnet design.** No users, no funds, no investors. The repo
contains the paper, the formal spec, and **runnable prototypes** — not a chain.

> **⏰ Regulatory window closing 20 October 2026.** The SEC's proposed
> *Regulation Crypto Assets* (91 FR 54510, File No. S7-2026-27) has a comment
> period open until then, and it contains the one open question this design
> cares about: **who is the "issuer" for a fair-launch network that never had
> one** (Rule 400 / Form TR all assume one). Preparation — analysis and a draft
> comment, **not filed** — is in
> [`docs/REG_CA_COMMENT_HAZIRLIK.md`](docs/REG_CA_COMMENT_HAZIRLIK.md), and the
> reviewable **draft comment itself is in
> [`docs/REG_CA_YANIT_TASLAK.md`](docs/REG_CA_YANIT_TASLAK.md)** (with the code
> evidence behind each architectural claim it makes). Whether to comment **at all**
> is a human decision; nothing is submitted without the owner's explicit approval.

| Artifact | Contents |
|---|---|
| `KOK_V2_PAPER.md` | Design paper: architecture, economics, competitive analysis |
| `KOK_V2_TECHNICAL_SPEC.md` | Formal specification (Appendix A = task-market protocol) |
| `KOK_V2_CRYPTO_BRIEF.md` | The six questions for external cryptographic review |
| `KOK_V2_REFERENCES.md` | Bibliography + a proof index mapping every claim to evidence |
| `g_layer_tests_en.py` | Layer G: replay rejection, prescribed hardness, low-entropy, retarget (TV-1..TV-21) |
| `u_layer_prototype_en.py` | Layer U: escrow, burn, VRF, fraud, slashing (TV-5..TV-10) |
| `f3a_sequencer_proto_en.py` | Censorship-resistance: refund, migration, bond refill (TV-15..TV-20); demand meter and paying task (TV-21..TV-25); regression guards (TV-44, TV-50). **Round-4 (TV-80/TV-81): the slash deterrent was ONE-SHOT on the verification-failure path** — `settle_task` slashed the bond but never refilled it while `migrate_task` did, so a repeat-offender sequencer was punished once (5 events, 50 slashed, bond 100 to 0) and events 2-5 were free. Now refilled; TV-81 measures [100, 200, 300, 400, 500] with the bond held at 100. Also fixed: submit()'s boolean conflated ASSIGNED with REJECTED (now three-valued); TaskSpec accepted burn_rate > 1 and negative fees producing NEGATIVE escrow that corrupted the fee invariant; a duplicate tid silently overwrote a live task and its escrow vanished from the books; w_r=0 or negative fired refunds immediately; the 0.10 viability threshold was an unnamed magic number (now VIABILITY_THRESHOLD with its derivation stated) |
| `ghostdag_proto_en.py` | GHOSTDAG ordering with Kaspa mainnet parameters (TV-22..TV-26) |
| `fp8_noise_proto_en.py` | Quantization-aware FP8 noise model (TV-27..TV-30) |
| `bond_margin_proto_en.py` | Censorship-economics measurement (TV-31..TV-33). **Round-4 (TV-80): TV-31/32/33 re-derive exactly** (critical fee 60.0, margin 200.0, free window 3). Fixed: the slash_mode dispatch was a silent catch-all where a one-character typo flipped the economics to FULL (now explicit ValueError); the critical margin could not represent a negative answer when B_out < fee (now it can); dead imports removed |
| `pass_sim_en.py` | Closed-form solver for the Pass (2026) economic model |
| `adoption_econ.py` | **The adoption question**: cross-subsidy arithmetic (TV-35), two-sided cold-start model (TV-36), the honest verdict (TV-37), and the measured escape threshold (TV-60, ~0.79 — guarded, so the paper and the model cannot drift apart) |
| `f0_demand_discovery.py` | **F0 as an instrument**: candidate scoring rubric, price test against the measured crossover, append-only interview log. **Round-4 (TV-80): the log counted its own worked examples as interviews** — every run appended an EXAMPLE-ILLUSTRATIVE row and log_status() counted those rows, so the honest log measured how many times the file was RUN (10 rows, all self-seeded, reported as interviews: 10). It now reports interviews: 0, worked_examples_in_log: 11 — the honest status is NOT STARTED, and the kill criterion's 10-interview threshold is the GOAL rather than a count the tool inflated. Also fixed: the PURSUE verdict claimed both reasons evidenced when the rubric requires only one; a zero denominator crashed the price test; one corrupt line aborted the whole status read |
| `f0_candidate_list.py` | Six named buyers from Akash's own case studies, scored by the F0 rubric. **Round-4 (TV-80): the local score() copy DROPPED the rubric's DEFER path**, so 6/6 candidates got a different verdict class than the rubric the file's docstring named — Flashback Labs got PURSUE with two UNKNOWN fields where the real rubric says DEFER. DEFER is restored and all six now return it. Also corrected: the summary said Passage scores lowest, but the file's own scorer gives Passage 1.5 against Sigea and Witness Chain at 1.0 |
| `f0b_air_proto.py` | **F0b, the AIR chain (TV-40 to TV-43, TV-66, TV-70)**: constraints with Merkle input binding, commitment with sampled verification, low-degree testing via the quotient Q=C/Z (degree m-2, not the assumed 1), zero-knowledge masking, and the TV-66 construction whose openings are Merkle-bound to commitments made **before** the challenge (`SzZkTileAIR`); TV-70 threads the input binding through the FRI and ZK layers too, so a fabricated tile for a chosen accumulator no longer verifies there |
| `f0b_prod_field_en.py` | **F0b production-field prototype (TV-76)**: steps 1-2 of `F0B_PRODUCTION_DESIGN.md` actually built — the same AIR over a verified 256-bit prime (honest proof verifies, a tampered trace entry and a wrong accumulator reject), and the leaf hash as a full-width 32-byte SHA-256 digest over codeword symbols with the position bound into it. **The negative result is the point:** sibling-hash inversion is a preimage problem, so field growth alone would NOT have closed it; the digest width does, and "field AND one-way leaf hash" was the correct diagnosis rather than "field alone". Deliberately builds no FRI — that is step 3, now built as `f0b_fri_en.py` |
| `f0b_fri_en.py` | **F0b FRI recursive composition (TV-78, Stage 3)**: step 3 of the production design — the recursion that the existing single-round quotient check was one round of. **A real bug was caught by the measurement, not by reading:** the first fold was in x-space, where the even part keeps its own degree (x^2+3x+7 folds to x^2+7+3*alpha, still degree 2), so the recursion reported non-increasing degrees while the verifier found 17 mismatches. The composition that halves the degree is in u = x^2 space, and both fold and verifier were moved there. Measured 3/3, degrees 3->1->0. Honest limits printed in the file: still q=97, no Reed-Solomon extension, no Merkle commitment across rounds | **ROUND-5A (2026-09-24): the FRI challenge was drawn from the PROVER's own RNG** — `alpha = rng.randrange(1, q)` from a seed the prover holds, so the only source of soundness in FRI was chosen by the party being challenged; a cheating prover could search alphas until a bad fold passed, and the degree-bound check was then verifying a property the prover had selected for. Now Fiat-Shamir: alpha is a SHA-256 digest over the polynomial the prover must commit BEFORE the challenge exists, and the verifier recomputes the same alpha from the same committed polynomial. The round also MEASURED and RETRACTED the 'logarithmic verifier cost' claim — verify_round scans range(1,q), measured 0.00009s at q=97 rising to 0.00299s at q=2003 (33x time for 20.6x q, i.e. linear, not logarithmic), and forgery survival 0/3000 at 1/2/3 rounds. Probes 8/8 |
| `egap_cert_en.py` | **E-gap certification (TV-77, Stage 2)**: the binding whose absence caused TV-72's measured phi=0. Round-3 finding [21] showed the G layer accepted caller-supplied matrices, so a cert over [5,6;7,8] validated while the task's program was [2,3;4,5] — the mined matrix and the commissioned one could differ and no check noticed. Now the certificate names (task_id, program_commit, ctx, tile) and the verifier derives what it must be bound to from the TASK. Measured 4/4: foreign matrices reject, own matrices pass, cross-task replay rejects, commitment is content-bound. **States what it does not prove:** phi > 0 cannot be measured by a prototype, that is F0/F3a; TV-72's negative result is answered by this binding, not overturned | **ROUND-5B CRITICAL (2026-09-24, TV-82): the binding bound the commitment STRING, not the COMPUTATION.** verify checked that the cert's commitment field matched the task's and that the PoW target was met, but never that the tile VALUE came from the committed matrices — measured before the fix: commissioned [[2,3],[4,5]] (tile 26) served by mining over [[2,3],[4,6]] (tile 30) was ACCEPTED, because the value was unbound. The verifier now takes the committed program and re-derives the tile value from a single reference computation both sites share, so attributed work must equal commissioned work. probe_round5b_egap_en.py 5/5 |
| `STAGE4_HUMAN_MONEY_GAP.md` | **Stage 4, recorded not performed**: the part that cannot be closed by writing code — external cryptographic review (priced at $215/hr, declined 2026-09-23, the deferral argument now recognised as circular), legal review (citations verified but advice not obtained), a live network of paying buyers (F3a/F3b, not started). Records the gaps with costs attached so "not done" is a fact rather than an omission. Deliberately builds nothing |
| `probe_edges_en.py` | **Adversarial edge probes (TV-45..TV-49)**: corners the spec is quiet about. Not requirements — they exist because the three real f3a bugs found this pass were all caught by provoking the machine, not by reading it |
| `spec_rederive_en.py` | **TV-79: spec-only re-derivation after F.5** — tests whether pinning the thirteen ambiguities actually worked, by re-deriving the AIR from the spec ALONE and cross-checking against the reference. Measured 4/4: honest proofs agree in both directions, a fabricated tile for a chosen accumulator is rejected, the index binding holds, and A1's hash matches the reference byte-level. **The test itself found two more spec defects (A14, A15):** the input commitments are roots over the FLATTENED n*n matrices not the m residuals (this file's first derivation got that wrong and the roots did not match), and the Merkle root is truncated to 8 bytes as an int, not the full digest — capping the commitment space at 2^64 regardless of q, the toy counterpart of TV-76's production-scale point |
| `probe_g_layer_size_en.py` | **Round-4 g_layer probe (TV-80)**: `KWKernel.prove` derived the matrix size from its INPUT but `verify` used the kernel's CONSTANT self.n — so on any other size, verify recomputed the tile over the wrong coordinates. MEASURED before the fix: a 6x6 proof raised `IndexError: list index out of range` in verify; the 8x8 default worked only because it matched the constant, which is why round-3 missed it. Now drives 6x6, 8x8 and 10x10 and asserts the honest certificate verifies at each, plus a forged tile value rejects |
| `probe_u_layer_en.py` | **u_layer adversarial probes (TV-51..TV-57)**: same method on the L1 prototype. TV-51 found a bookkeeping bug — the escrow field went negative at settlement while the money flow was correct. TV-56 (Stage 1.4) measures that the VRF public key is now a digest of the secret rather than the secret itself, and states the verifier-side limit honestly: a hash-based toy cannot check the HMAC without sk, so ECVRF is the real fix. TV-57 (round-4) drives the phi lie directly: the honest block's real phi is 0.1103, and a block declaring phi=0.99 now returns REJECT:phi-mismatch, because the verifier re-derives phi from the proofs' flops and the nonce instead of range-checking the miner's claim |
| `probe_ghostdag_en.py` | **GHOSTDAG adversarial probes (TV-56..TV-59)**: TV-59 measured a real deviation — the greedy mergeset made the ordering sequence work a block does not reference (572 entries outside past(B) on 51 blocks). **CLOSED in Stage 1.1** by intersecting the mergeset with past(B); the probe was inverted so a nonzero count now fails loudly, and the deviation cannot quietly return |
| `probe_pass_sim_en.py` | **Pass economic model probes (TV-61..TV-64)**: TV-62/TV-63 found that `_theta_from_PR` bracketed 1e-12..1e9 and never checked the (theta_low, theta_high) interval its docstring names — low-price parameter sets returned a Fortessia-regime theta as if it were Duplexia. Fixed; `solve()` was never wrong |
| `probe_f0b_zk_en.py` | **F0b zero-knowledge probe (TV-65)**: TV-43's "zero-knowledge" claim is **retracted** — the mask derives from a seed the *verifier* supplies, so it recovers every plaintext it was sent. Provenance, not privacy. **Fixed by TV-66 in `f0b_air_proto.py` (`SzZkTileAIR`): Merkle-bound pad openings, commitment before the challenge, the view carries no pad — NOT a hiding proof at this scale, and not claimed as one: the pad is no longer *transmitted*, so the leak costs a search rather than a subtraction, and at q=97 that search walks 912,673 pads in ~0.1s, the transcript pins the pad uniquely, and the toy leaf hash is invertible. Two adversarial review rounds caught (i) the pad shipped inside the verifier's own dict, (ii) an attack replayed against a construction that no longer existed, and (iii) that the brute-force "recovery" only worked because the test handed it the answer** |

All prototypes are **stdlib-only Python 3**: `python3 <file>`. No dependencies.

## Honest limits

Every prototype says this in its own header; we say it here too:

- The G-layer kernel simplifies cuPOW; the VRF is an HMAC stub; the "STARK-like"
  trace is not a real AIR; the field is a toy q=97.
- GHOSTDAG: **no PoW/validity check** (all blocks assumed valid), uniform delay
  model, k=18 is the Kaspa BPS=1 template not our own.
- FP8: simplified RNE + subnormal flush, **not IEEE-754**; r=2 toy rank.
- Toy dimensions (q=97, n=8, r=2, K=64) **do not test asymptotic arguments**.
- Negative results are recorded, not hidden: TV-28 confirms the FP8 low-entropy
  reversal (the attack succeeds without a noise floor), TV-30 corrects DELTA
  0.5 → 0.06, TV-31 shows the f3a slash is fee-capped.
- **Round-5 (2026-09-24) adversarial review of six never-probed files found two
  bugs that survived every earlier round because the check that would have
  caught each was an identity** (spec TV-84/TV-85): the endogenous theta solver
  solved the wrong equation — Pearl's theta is 1.657, not the 1.05 the paper
  quoted, and the equilibrium reproduced its input PR to one part in two —
  while the file's residual checker compares the solver to the equation it
  itself solved; and FRI's `verify_round` accepted any degree-(q-1)/2
  polynomial, 9/9, because it checked a fold relation every such polynomial
  satisfies. Both are fixed with probes that can fail, and both files now carry
  falsifiable input-consistency checks. Pearl's regime claim is untouched
  (1.657 is still pure Duplexia); the number was wrong.
- Round-5 also removed claims the code does not measure: FRI's "logarithmic
  verifier cost" (the implemented check is Θ(q·deg) — real FRI achieves log cost
  by evaluating at one query point per round, which this prototype does not)
  and "probability approaching 1" (no repeated-forgery sampling exists); and it
  corrected the EN-package audit's ~50 false positives, which were ordinary
  English words ending in a Turkish two-letter suffix (margin, caller, produce,
  tolerance, encode, governance, ...). Turkish prose is still detected when
  injected.

**A perfect paper is not equal to a running chain.** The paper ceiling is ~85/100;
the remaining ~15 points are empirical and cannot be won on paper.

## Cryptographic foundation

The Layer G assumption is **Komargodski & Weinstein, "Proofs of Useful Work from
Arbitrary Matrix Multiplication"** (ePrint 2025/685 = arXiv 2504.09971v4).
Conjecture A.1 (random rotation) is **still open** — this is Pearl's own
Polymath Problem 1, and it is the single largest open assumption we inherit.

**Bibliography status:** every arXiv and ePrint identifier in this project was
fetched against the live archive and matched on title, authors and venue
(**11/11, 2026-09-21**). The per-entry table is in `KOK_V2_REFERENCES.md`.

## Name

**KÖK** is Turkish for *root* — the root of a tree, and by extension the root
node of a DAG and the roots of unity in a finite field, the senses a consensus
layer actually uses. It is **not** *Kök Tengri* (the Old Turkic Sky God, where
*kök* is a **color** word, a different homograph); an early draft conflated the
two and that error was removed. The name carries no religious or national claim.

## External review

The design is under independent review by academic cryptographers. The review is
published whatever its conclusion. If the core assumption does not hold, we fall
back to a pure-PoW mode that is already specified, and that finding goes on the
record.

## License

Code: MIT (see `LICENSE`). Prose: CC-BY-4.0.

## Contact

`kokprotocol@proton.me` — anonymous by design; we are pre-testnet and have nothing
to sell.
| `tv72_egap_mechanism_en.py` | **TV-82: the E-gap mechanism demonstrated, not stated (Stage 2 follow-through, 2026-09-24)** — a two-arm comparison on a mock G layer that measures *why* Pearl's phi was zero. Arm A is the pre-binding acceptance rule (verify the PoW target only): a certificate over matrices the miner prefers is accepted 5/5, detectability 0 by construction. Arm B is the post-binding rule (the verifier derives the required program commitment from the task): the substitution is rejected 4/4 and the commissioned pair accepted. This makes TV-72's negative result causal rather than anecdotal, and states in the file itself what it does NOT prove: a binding that lets the protocol notice cheating is not evidence buyers will arrive (the demand side is F0, deliberately not started); the matrices are toy 2x2; and it is a mock of the acceptance rule, not the shipped KWKernel.verify |
| `probe_round5a_field_en.py` | Round-5a probes on f0b_prod_field_en (9/9): verify's input binding, the toy catching the same forgery, the 20000-challenge sweep, the inversion target drawn from the pool |
| `probe_round5a_fri_en.py` | Round-5a probes on f0b_fri_en (8/8): degree bound, final-constant check, the prover-generated challenge (now Fiat-Shamir), the linear verifier cost, forgery survival |
| `probe_round5b_egap_en.py` | Round-5b probes on the E-gap mechanism (5/5) — FOUND that the binding did not bind the computation, only the commitment string |
| `probe_round5b_rederive_en.py` | Round-5b probes on spec_rederive (3/3): the cross-check compares to the reference rather than to itself, the AIR-only limit is stated, pinned values are compared not listed |
| `probe_round5b_glayer_en.py` | Round-5b probes on g_layer_tests (4/4): the size fix reproduces the old IndexError, cost independence over 12 random contents, forgery at 4..12 and under a foreign ctx, low-entropy has no per-v hook (could-not-drive) |
| `probe_round5b_edges_en.py` | Round-5b probes verifying the 'clean set' labels (3/3): probe_edges' probes are falsifiable, the slashed-payout corner is driven and decided, probe_blindspot's self-assessment is accurate |
