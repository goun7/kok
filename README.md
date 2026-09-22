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
| `f0b_air_proto.py` | **F0b, the AIR chain (TV-40 to TV-43, TV-66)**: constraints, Merkle commitment with sampled verification, low-degree testing, zero-knowledge masking, and the TV-66 fix that restores hiding with verifier-unknowable masks (`SzZkTileAIR`) |
| `probe_edges_en.py` | **Adversarial edge probes (TV-45..TV-49)**: corners the spec is quiet about. Not requirements — they exist because the three real f3a bugs found this pass were all caught by provoking the machine, not by reading it |
| `probe_u_layer_en.py` | **u_layer adversarial probes (TV-51..TV-55)**: same method on the L1 prototype. TV-51 found a bookkeeping bug — the escrow field went negative at settlement while the money flow was correct |
| `probe_ghostdag_en.py` | **GHOSTDAG adversarial probes (TV-56..TV-59)**: TV-59 measures a real deviation — the greedy mergeset makes the ordering sequence work a block does not reference (572 entries outside past(B) on 51 blocks). Documented, not hidden |
| `probe_pass_sim_en.py` | **Pass economic model probes (TV-61..TV-64)**: TV-62/TV-63 found that `_theta_from_PR` bracketed 1e-12..1e9 and never checked the (theta_low, theta_high) interval its docstring names — low-price parameter sets returned a Fortessia-regime theta as if it were Duplexia. Fixed; `solve()` was never wrong |
| `probe_f0b_zk_en.py` | **F0b zero-knowledge probe (TV-65)**: TV-43's "zero-knowledge" claim is **retracted** — the mask derives from a seed the *verifier* supplies, so it recovers every plaintext it was sent. Provenance, not privacy. **Fixed by TV-66 in `f0b_air_proto.py` (`SzZkTileAIR`): Merkle-bound pad openings, commitment before the challenge, the view carries no pad — hiding demonstrated at toy scale after one round of adversarial review caught a self-confirming test in the first attempt** |

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
