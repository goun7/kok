# KÖK Network v2

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

## Status

**This is a pre-testnet design.** No users, no funds, no investors. The repo
contains the paper, the formal spec, and **runnable prototypes** — not a chain.

| Artifact | Contents |
|---|---|
| `KOK_V2_PAPER.md` | Design paper: architecture, economics, competitive analysis |
| `KOK_V2_TECHNICAL_SPEC.md` | Formal specification (Appendix A = task-market protocol) |
| `KOK_V2_CRYPTO_BRIEF.md` | The six questions for external cryptographic review |
| `KOK_V2_REFERENCES.md` | Bibliography + a proof index mapping every claim to evidence |
| `g_layer_tests_en.py` | Layer G: replay rejection, prescribed hardness, low-entropy, retarget (TV-1..TV-21) |
| `u_layer_prototype_en.py` | Layer U: escrow, burn, VRF, fraud, slashing (TV-5..TV-10) |
| `f3a_sequencer_proto_en.py` | Censorship-resistance: refund, migration, bond refill (TV-15..TV-20); demand meter and paying task (TV-21..TV-25); regression guards (TV-44, TV-50) |
| `ghostdag_proto_en.py` | GHOSTDAG ordering with Kaspa mainnet parameters (TV-22..TV-26) |
| `fp8_noise_proto_en.py` | Quantization-aware FP8 noise model (TV-27..TV-30) |
| `bond_margin_proto_en.py` | Censorship-economics measurement (TV-31..TV-33) |
| `pass_sim_en.py` | Closed-form solver for the Pass (2026) economic model |
| `adoption_econ.py` | **The adoption question**: cross-subsidy arithmetic (TV-35), two-sided cold-start model (TV-36), the honest verdict (TV-37), and the measured escape threshold (TV-60, ~0.79 — guarded, so the paper and the model cannot drift apart) |
| `f0_demand_discovery.py` | **F0 as an instrument**: candidate scoring rubric, price test against the measured crossover, append-only interview log |
| `f0_candidate_list.py` | Six named buyers from Akash's own case studies, scored by the F0 rubric |
| `f0b_air_proto.py` | **F0b, the AIR chain (TV-40 to TV-43, TV-66, TV-70)**: constraints with Merkle input binding, commitment with sampled verification, low-degree testing via the quotient Q=C/Z (degree m-2, not the assumed 1), zero-knowledge masking, and the TV-66 construction whose openings are Merkle-bound to commitments made **before** the challenge (`SzZkTileAIR`); TV-70 threads the input binding through the FRI and ZK layers too, so a fabricated tile for a chosen accumulator no longer verifies there |
| `f0b_prod_field_en.py` | **F0b production-field prototype (TV-76)**: steps 1-2 of `F0B_PRODUCTION_DESIGN.md` actually built — the same AIR over a verified 256-bit prime (honest proof verifies, a tampered trace entry and a wrong accumulator reject), and the leaf hash as a full-width 32-byte SHA-256 digest over codeword symbols with the position bound into it. **The negative result is the point:** sibling-hash inversion is a preimage problem, so field growth alone would NOT have closed it; the digest width does, and "field AND one-way leaf hash" was the correct diagnosis rather than "field alone". Deliberately builds no FRI — that is step 3, now built as `f0b_fri_en.py` |
| `f0b_fri_en.py` | **F0b FRI recursive composition (TV-78, Stage 3)**: step 3 of the production design — the recursion that the existing single-round quotient check was one round of. **A real bug was caught by the measurement, not by reading:** the first fold was in x-space, where the even part keeps its own degree (x^2+3x+7 folds to x^2+7+3*alpha, still degree 2), so the recursion reported non-increasing degrees while the verifier found 17 mismatches. The composition that halves the degree is in u = x^2 space, and both fold and verifier were moved there. Measured 3/3, degrees 3->1->0. Honest limits printed in the file: still q=97, no Reed-Solomon extension, no Merkle commitment across rounds |
| `egap_cert_en.py` | **E-gap certification (TV-77, Stage 2)**: the binding whose absence caused TV-72's measured phi=0. Round-3 finding [21] showed the G layer accepted caller-supplied matrices, so a cert over [5,6;7,8] validated while the task's program was [2,3;4,5] — the mined matrix and the commissioned one could differ and no check noticed. Now the certificate names (task_id, program_commit, ctx, tile) and the verifier derives what it must be bound to from the TASK. Measured 4/4: foreign matrices reject, own matrices pass, cross-task replay rejects, commitment is content-bound. **States what it does not prove:** phi > 0 cannot be measured by a prototype, that is F0/F3a; TV-72's negative result is answered by this binding, not overturned |
| `STAGE4_HUMAN_MONEY_GAP.md` | **Stage 4, recorded not performed**: the part that cannot be closed by writing code — external cryptographic review (priced at $215/hr, declined 2026-09-23, the deferral argument now recognised as circular), legal review (citations verified but advice not obtained), a live network of paying buyers (F3a/F3b, not started). Records the gaps with costs attached so "not done" is a fact rather than an omission. Deliberately builds nothing |
| `probe_edges_en.py` | **Adversarial edge probes (TV-45..TV-49)**: corners the spec is quiet about. Not requirements — they exist because the three real f3a bugs found this pass were all caught by provoking the machine, not by reading it |
| `probe_u_layer_en.py` | **u_layer adversarial probes (TV-51..TV-56)**: same method on the L1 prototype. TV-51 found a bookkeeping bug — the escrow field went negative at settlement while the money flow was correct. TV-56 (Stage 1.4) measures that the VRF public key is now a digest of the secret rather than the secret itself, and states the verifier-side limit honestly: a hash-based toy cannot check the HMAC without sk, so ECVRF is the real fix |
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
