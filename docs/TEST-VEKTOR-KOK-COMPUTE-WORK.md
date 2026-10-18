# Public test vector — kok compute-work receipt (MatMul PoUW)

> **Date:** 2026-10-18 · **Contact:** repo owner (GitHub `goun7`)
> **Purpose:** a stranger-checkable artifact for the x402 `proof-of-done`
> discussion ([x402-foundation/x402#3379](https://github.com/x402-foundation/x402/issues/3379)).
> It follows the labeling discipline that thread established:
> every field is `observed`, `derived`, or `simulated`, and a field without a
> label is worthless here.

**What this artifact is, in one sentence:** a receipt that a compute provider
actually performed the small MatMul job it claims — the job is *bound into the
proof* rather than asserted next to it, and the whole thing is verifiable with
a ~400-line Python file that imports nothing from this repo.

**What it is not:** there is no payment, no settlement, no buyer and no seller
in this vector. The x402 leg is **simulated**. This is the work half only —
deliberately the same shape as the Tamga pairing fixture's separation of work
evidence from content evidence.

---

## 1. Files

| File | What it is |
|---|---|
| `receipt/kok_receipt_verify_en.py` | the independent verifier (~400 lines, stdlib + `nacl.bindings`). Imports **nothing** from this repo. |
| `receipt/right-run-kok-g-layer-matmul.json` | the mined receipt (the vector itself) |
| `receipt/anchor-ledger.jsonl` | the corresponding `compute-anchor` record in a Tamga-style ledger |
| `receipt/kok_receipt_verify_test_en.py` | 12 tests: 1 honest cross-language, 8 tamper negatives, 3 contract |

Run the verifier (no build, no network):

```bash
python3 receipt/kok_receipt_verify_en.py receipt/right-run-kok-g-layer-matmul.json
# KABUL  receipt/right-run-kok-g-layer-matmul.json  (did did:key:z6MkmmxFDtxYfmwaCJ..., receipt fb30f1f2fb8cbbba, tile (0, 0, 68))
```

The rest of this repo is a Rust implementation (`cargo run --bin kok -- create`
mines a receipt); this directory is the language-independent half.

---

## 2. The vector

`receipt/right-run-kok-g-layer-matmul.json`, mined on 2026-10-18 with
`ctx=20261018, target=2^2, q=97, n=8, r=2`:

| Field | Value | Source |
|---|---|---|
| `receipt_hash` | `fb30f1f2fb8cbbba4248d45daf18b723406d18e3024f2ab49cedb78162afff40` | derived — `sha256(work_canonical(receipt))`, 271-byte pipe-delimited envelope |
| `miner_did` | `did:key:z6MkmmxFDtxYfmwaCJYDj8gRTMb1M1oribYwBDA64n6toikw` | observed |
| `signature` | `2b0b93676e06cbfe7180bbb0e969c72b32bad01f23979eff8a69fdf2027a18d78cfe76a152b4f95b782d3200126bd1ecadf1c2f6ec3e22cc76fed25154a63e05` | observed — Ed25519 over `SIG_DOMAIN ‖ sha256(envelope)` |
| `task_program` | `kok/g-layer-matmul-toy` | observed |
| `program_commit` | `4c3d100124cf3b941bd3a5c038bb47b0cf7b456da63853b0e27b080c417f271e` | derived — `sha256("kok.program.v1‖name‖q‖n‖r")` |
| `input_commit` | `231b7e29c13c42620cea25541be2f78f75e5648a27e05d1f766613fd84be1022` | derived — `sha256("kok.input.v1‖flatA‖flatB")` over the two carried matrices |
| `cert_i`, `cert_j`, `cert_value` | `0`, `0`, `68` | derived — the certified tile of the product |
| `nonce` | `1` | observed |
| `ctx` | `20261018` | observed — the binding context (would carry the x402 `paymentId` in a real settlement; **simulated** here) |
| `target` | `4` | observed — difficulty `2^2` |
| `q`, `n`, `r` | `97`, `8`, `2` | observed — the job parameters |
| `matrix_a`, `matrix_b` | 8×8 mod-97 matrices, in the file | observed |
| `proof_version`, `layer` | `1`, `G` | observed |
| `task_fee`, `task_burn_rate_per_mille` | `0`, `0` | observed — the fee is **not** part of the hash envelope |

**The check a stranger can recompute** (this is the whole point, and it is the
difference between a receipt and a claim):

```
h_num("tile", (ctx, nonce, i, j, acc)) % target == 0
```

where `h_num(prefix, nums) = int.from_bytes(sha256(prefix|"|"|nums-joined)[:8], "big")`
and `acc[i][j] = Σ_l A′[i·r][l·r] · B′[l·r][j·r] mod q`, with `A′ = A + E` and the
noise pair `(E, F)` a pure function of `(ctx, n, q)` via
`h_num("E"/"F", (ctx, i, j)) % q`. The noise is **derived, not carried**: a
verifier recomputes it from the same context, so the provider cannot shop for
an easy matrix pair after seeing the job. On this vector:
`h_num("tile", (20261018, 1, 0, 0, 68)) % 4 == 0` — passes.

---

## 3. What is honestly proved, and what is not

**Proved (recomputable by a stranger, no trust in the provider):**

1. Some party knew the Ed25519 private key behind `miner_did` when the
   receipt was signed (`crypto_sign_open` over the domain-separated digest).
2. The signed envelope is exactly the 19 fields listed above —
   `receipt_hash` is the digest of that envelope, so any later edit breaks it.
3. The claimed output tile **is** the product of the claimed inputs under the
   claimed job parameters, with the noise derived from the claimed context —
   all recomputable from the file itself.
4. The certified tile satisfies the difficulty relation, i.e. the provider did
   real hashing work *on this job*, not on a hashcash-style detour unrelated
   to it. **The work and the job are the same object.**

**Not proved, and deliberately not claimed:**

- **That any payment happened.** There is no settlement in this vector and no
  x402 binding beyond the `ctx` field. The `ctx`-carries-`paymentId` step is a
  proposal in §4, not something this file demonstrates.
- **That the work was the work the buyer wanted.** A provider can mine a
  receipt for a real MatMul job and deliver something else. This receipt binds
  *a* job, not *the transaction*. That seam is the same one the thread named:
  `receipt.stdout_sha256` (derived) and `claim.delivered` (asserted) answer
  different questions and neither holds the other.
- **Correctness of the task program itself.** `program_commit` pins the name
  and parameters, not the semantics. A wrong algorithm with the right
  commitments still verifies green.
- **That the work was useful.** A mod-97 MatMul is a toy. This is a shape
  demonstration, not a production claim, and the difficulty target here is
  `2^2` so the receipt mines in milliseconds.
- **Freshness or non-replay.** `receipt_prev` is all-zeros in this vector.
  The receipt scheme has a chaining field, but a single receipt does not
  demonstrate it and nothing here prevents the same receipt being shown to
  two different verifiers.
- **Anything about hardware, runtime, or how long the job took.** No timing
  fields are carried, precisely because timing is asserted, and the thread's
  own `wall_ms` lesson (asserted, not derived, ~172× swing on identical work)
  is the reason.

---

## 4. Why we are posting this to #3379

The thread's own convergence is: durable-evidence attests to *what* was
delivered, proof-of-done attests to *whether the work ran*, capacity-attest to
*whether the buyer agreed*. Every proposal in the thread so far binds the
"work" to a **settlement**; the missing edge is the same one your own
already-shipped pieces have — no artifact in the thread binds the *bytes of
the job itself* into the proof.

The kok receipt is a different point in the space, and we want to state where
it sits rather than overclaim convergence:

- **The work is not pinned by a hash of the code** (the thread's
  `agent.wasm`-pinning shape, which we respect). It is pinned by the *inputs,
  parameters and the output relation* of the job. The difference is real:
  code-pinning says "the same program ran the same way"; job-binding says
  "the product of these inputs under these parameters is this tile". Neither
  implies the other.
- **The cost is paid before the claim exists, not after.** The thread's D-014
  discussion named the two failure classes: optional checks get bypassed at
  zero cost, and credibility comparisons force a ranking. A job-bound receipt
  cannot be produced without performing the job's own arithmetic — so it is
  not *declinable* the way an optional check is. It is strictly weaker than a
  fix for delivery quality (a provider can still deliver the wrong thing), but
  it does not sit in either of the two failure classes the thread identified.
  That is an observation for the record, not a proposal to close D-014.
- **The noise structure is what makes it non-transferable.** `(E, F)` derives
  from `(ctx, n, q)`, and in a real settlement `ctx` would carry the x402
  `paymentId`. Then a receipt mined for payment A cannot be replayed against
  payment B, because the noise — and therefore the accumulator, and therefore
  the difficulty relation — changes with the context. **We have not
  demonstrated that binding here**; `ctx` is a plain integer in this vector and
  the x402 leg is simulated. Stating it as designed rather than measured.

---

## 5. Composition shape (proposal, not shipped)

If the `extensions[<key>]` shape lands, the natural seat for this is:

```json
{ "scheme": "kok-compute-work-v1",
  "receiptHash": "<64-hex, sha256 of the kok work envelope>",
  "job": {"alg": "matmul-mod-q", "q": 97, "n": 8, "r": 2},
  "verify": "python3 kok_receipt_verify_en.py <receipt.json>" }
```

Two notes in the thread's own vocabulary:

- `receiptHash` is the digest of the **work envelope**, which is a different
  object from the Tamga ledger's record hash. In the anchor ledger
  (`receipt/anchor-ledger.jsonl`) the two sit side by side: the ledger's own
  `h` (`32c96843…`) is computed over the *ledger* record, while
  `receipt_hash` (`fb30f1f2…`) is the kok envelope's digest. Two digests, two
  preimages, one artifact — we label rather than equate them, per the thread's
  keccak/sha-256 lesson.
- `job.alg` exists because the thread's algorithm-tagging rule applies to job
  descriptors too: `"alg": "matmul-mod-q"` rather than a bare parameter set.

---

## 6. Honest size/overhead note

The reference mine on this vector took **3.5 ms** (`target=2^2`, `q=97`,
`n=8`, `r=2`, single tile certified, one run, quiet host). This is a toy
configuration chosen so a stranger can re-run the whole thing in under a
second; it says nothing about a production-sized job, and we are not making an
overhead claim for one. The verifier itself is ~400 lines and runs offline.
*Small verifiers as a distribution strategy* is a rule this thread already
stated; this artifact follows it.

Two limits of this toy scale that a reader should not have to derive for
himself, both surfaced by an independent replay (§7) and re-measured by us
locally:

- **Declared input is four times the participating input.** With `n=8, r=2`
  the accumulator reads only `A′[i·r][l·r]` and `B′[l·r][j·r]`, so it touches
  **32 of the 128 declared cells**. Zeroing the other 96 leaves all sixteen
  tiles byte-identical and the certificate value at 68. The 96 unused cells
  are still bound by `input_commit` (the commitment changes when they do),
  but they are bound **by commitment, not by computation** — different
  guarantees. At toy scale that is harmless; at a size where someone pays for
  the work, the declared/participating ratio belongs in the vector itself,
  because a buyer reading `matrix_a` as an 8×8 input is reading more than the
  arithmetic used.
- **Verifying costs what producing costs.** `check_certificate` recomputes
  the whole accumulator to test one tile — 64 multiplications against the
  prover's 64 — and one of sixteen tiles is ever tested against the target.
  That is the price of the design choice this artifact exists to demonstrate
  (the hashing work and the job are the same object): the receipt buys
  attribution and binding, **not a cheaper verifier**. It should not be read
  as a succinctness claim. Separately, `target=2^2` is the easiest nontrivial
  difficulty, and the vector's `nonce=1` is the luckiest possible first draw
  (measured per-(nonce,tile) clear rate 0.256 over 3200 trials against a
  theoretical 0.25), so the 3.5 ms figure above sits at the easy end of the
  range rather than being typical of a harder target.

---

## 7. Independent replay (2026-10-18T16:50Z)

**Replayed by `holistis`** ([comment on
#3379](https://github.com/x402-foundation/x402/issues/3379#issuecomment-6252521348)),
who read the scheme out of `kok_receipt_verify_en.py` and **rewrote it in
Node** with Node's own Ed25519 and hand-rolled base58, so none of our code
executed. Eleven checks, all eleven agree with the vector;
`receipt_hash` reproduces as `fb30f1f2…` over exactly 271 bytes; the tile
recomputes to 68 from the strided noisy factors rather than from the declared
value; the did:key decodes under the `0xed01` tag; the signature verifies
over the domain string plus `sha256(envelope)`. Six mutants — cert value,
`matrix_a[0][0]`, `ctx`, `nonce`, `task_fee`, `program_commit` — all six
caught, failing on the stages that check them.

The same replay named the two unlabeled limits now carried in §6, which we
**re-measured locally before accepting** (see above): the 32-of-128
participating-input ratio, and the verifier-cost-equals-producer-cost
property. Neither refutes anything the vector claimed; both are now stated
in the document itself.

---

*Disclosure: artifact produced by the project owner; receipt mined with the
repo's own Rust binary and verified with the independent Python verifier
shipped alongside it. Independently replayed by a third party on 2026-10-18
(§7); the standing invitation is to break it, and if any limit above turns
out to be softer than stated, that is the useful finding.*
