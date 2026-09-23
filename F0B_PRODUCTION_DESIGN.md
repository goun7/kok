# F0b Production Design — from toy field to security margin

**Status: a design document, not an implementation.** Written 2026-09-23 after
TV-71 measured that the toy field is a parameter choice, not a structural
property of the construction. This is what would have to change, and what each
change costs, so the gap is visible as engineering rather than as a caveat.

The running prototype is `f0b_air_proto.py`. Its honest limits are documented
in place and are all real:

| Limit in the toy | Why it is a limit | What production needs |
|---|---|---|
| q = 97 | pad space q^(m-1) = 912,673, walkable in ~0.1s | a 256-bit prime |
| SHA-256 truncated to 8 bytes | preimage space 2^64 regardless of q | full 32-byte digest, or a 256-bit-secure hash |
| Merkle leaves are raw field elements | leaf domain is {0..q-1}, so inversion costs q trials | leaves must be codeword symbols, not elements |
| no FRI | degree claim is spot-checked, not recursively reduced | a FRI composition |
| auth paths built per-opening | fine at toy scale | batched, with a domain-separated padding rule |

## 1. What TV-71 actually measured

The decisive experiment: the same `SzZkTileAIR` construction, with only `q`
changed, still produces a proof that verifies at every challenge point at
q = 65521 and q = 2147483647. The construction is parameterized on `q` and
scales.

What does NOT scale with `q` is the leaf hash. The three attacks scale
differently, and the honest recommendation has to cover all three:

| Attack | Cost at toy | Scales with q? | Closed by |
|---|---|---|---|
| Brute force over pad space | q^(m-1) = 912,673 | YES — q^(m-1) | field growth |
| Uniqueness of consistent pads | exactly 1 vector | YES — same count | field growth |
| Auth-path sibling inversion | ~107 hash trials | NO — 2^64 fixed | one-way leaf hash |

This is why the toy text says "size claim, not a security margin": the first
two are closed by growing the field, the third is not. A recommendation of
"grow the field" alone would leave the third open and would be the same class
of error as the original hiding claim — one correct-sounding fix that misses
the real surface.

## 2. The parameters that matter

**Field.** A 256-bit prime. The toy uses 97 because the trace values must be
printable and the brute force must be runnable; both are test conveniences.
The soundness of the AIR's transition check is Schwartz-Zippel over the
challenge point: a random z hits the degree-m+1 constraint polynomial with
probability (m+1)/q, which at q = 2^256 is negligible. At q = 97 the measured
forgery survival rate was 0.3200 against the analytic (m-3)/(m-1) = 0.3333 —
a toy number, not a margin.

**Leaf hash.** The commitment must be over codeword symbols under a hash that
is one-way at the field's security level. In the toy the leaf is the field
element itself and the hash is truncated, which is why auth-path inversion
cost ~107 trials and did not close when q grew. This is the one item where
"make the field bigger" is actively misleading.

**Commitment scheme.** Merkle with a domain-separated padding rule for odd
tails (the toy duplicates the last node, marked "D" in the auth path —
correct round-trip, fine for a prototype, not a production rule).

**FRI.** The prototype has `prove_poly`/`verify_low_degree`, which is the
quotient identity Q = C/Z at fresh off-domain points. That is one round of
what FRI does recursively; production needs the recursive composition over
successively smaller domains.

## 3. What this does NOT change

- The AIR itself: the trace recurrence `trace[t+1] = trace[t] + a[t]*b[t] mod q`
  is correct at any field size, and the round-two fixes (input binding at all
  three verifier layers, position-domain-separated Merkle checks) are
  field-independent.
- The hiding structure: commit before the challenge, open one leaf with an
  auth path, keep the pad out of the transmitted view. TV-71 shows this
  survives the field change.
- The honest ceiling: even with all of the above, this is a prototype of one
  MatMul tile, not an audited system. Two independent human cryptographic
  reviews are still absent, and no parameter choice substitutes for them.

## 4. The order to do it in

1. Field (mechanical — TV-71 already shows the construction accepts it).
2. Leaf hash over codewords (closes the one attack field growth misses).
3. FRI recursion (replaces spot-checking with a recursive degree claim).
4. Then, and only then, does the claim become "sound at a stated security
   level" rather than "sound at a size nobody would deploy".

Steps 1-2 are parameter and encoding work. Step 3 is real protocol work.
Nothing here is blocked on the two pending replies, and none of it is F3b:
this is the prototype's own roadmap item F0b, and it does not require a
testnet, a deployment, or a published announcement.
