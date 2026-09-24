# Round-5a adversarial review — f0b_fri_en.py, f0b_prod_field_en.py

Method: as in rounds 2-4, every claim a file makes about itself (in prose,
signatures, docstrings and printed labels) was turned into a probe that
MEASURES it. Round-4's recurring bug class was "code that claims a binding or
a measurement and does not perform it". Round-5a found the same class in both
files, plus one outright regression against the toy these files were ported
from.

Probes: `probe_round5a_field_en.py` (9 probes), `probe_round5a_fri_en.py`
(8 probes). Both run rc=0. Both files under review still run rc=0 with their
own probes passing.

Convention: a probe returns PASS when the file's claim is confirmed by its own
measurement, FINDING when the measurement contradicts the claim.

## f0b_prod_field_en.py — 9 findings

### 1. FILE: f0b_prod_field_en.py | LINE: 176-192 | CLASS: BUG + UNSUPPORTED-CLAIM
FINDING: `verify()` advertises an input binding it does not perform. Its
docstring reads "Both are bound to the input commitments by Merkle paths over
the flattened matrices", and its signature accepts `A_commit, B_commit, ctx` —
but the executable body never reads any of them.

EVIDENCE (probe F-1, measured):
```
honest acc bit length:        254
forged acc (attacker-chosen): 4
forged acc == honest acc:     False
fabricated proof, real commitments:     True
fabricated proof, other commitments:    True
fabricated proof, NULL commitments:     True
fabricated proof, different ctx:        True
verdict depends on commitments/ctx:     False
```
The fabricated proof uses `a=[1,1,1,1]`, `b=[1,1,1,1]`, `acc=4` — never
derived from A, B or ctx — and verifies under every commitment value, claiming
an accumulator never computed from the committed inputs.
AST-level confirmation of the executable body (def line and docstring
stripped):
```
body references A_commit   False
body references B_commit   False
body references ctx        False
body references merkle     False
body references _h256      False
body references _E         False
body references _F         False
```

### 2. FILE: f0b_prod_field_en.py | LINE: 176-192 (vs f0b_air_proto.py:218-229) | CLASS: BUG (regression)
FINDING: The toy this file was ported from enforces, per transition, that
`a[t] == a_res[t] + E[..]` (ROM-noise consistency) and that `a_res[t]` is
Merkle-committed under `A_commit` at the right index. The production port
dropped both checks.

EVIDENCE (probe F-2, side-by-side, identical forgery):
```
toy verify on the identical forgery: False (toy has the binding)
prod verify on the identical forgery: True
```
This is round-4's finding [9] (`cost_of_prove` never read its inputs) in a
new file: the signature claims the binding, the body does not perform it, and
every caller passes `None` for both commitments (line 263, 270, 275).

### 3. FILE: f0b_prod_field_en.py | LINE: 80-132, 161-192 | CLASS: DEAD-CODE + UNSUPPORTED-CLAIM
FINDING: The STEP-2 leaf hash — the thing the header says closes "the one
attack field growth misses" — is never wired into the AIR.

EVIDENCE (probe F-3):
```
TileAIRProd references merkle_root_prod     False
TileAIRProd references merkle_path_prod     False
TileAIRProd references merkle_check_prod    False
prove()  references any merkle_*: False
verify() references any merkle_*: False
```
`merkle_root_prod`/`merkle_path_prod`/`merkle_check_prod` are reached only
from `measure_position_binding_in_production_hash`. No proof is bound by the
32-byte-digest tree.

### 4. FILE: f0b_prod_field_en.py | LINE: 216 | CLASS: UNSUPPORTED-CLAIM
FINDING: Prints "MEASURED at toy, 20000 random challenges: see
tv76_field_margin()". The function it names runs ONE fixed interior tamper and
prints a ratio; no 20000-sample measurement exists anywhere in the file.

EVIDENCE (probe F-4):
```
occurrences of 'randrange' in tv76_field_margin: 2   (both generate A, B)
occurrences of 'challenge' in tv76_field_margin: 1   (prose only)
number of tampered traces it builds: 1 (a fixed interior point)
```

### 5. FILE: f0b_prod_field_en.py | LINE: 197-216 | CLASS: UNSUPPORTED-CLAIM
FINDING: `measure_schwartz_zippel`'s docstring says "MEASURED: forgery
survival of the transition check vs field size ... We measure it directly at
the toy field and compare with the analytic bound". The function runs no AIR,
no prove, no verify; every number it prints is `(m+1)/q` computed inline.

EVIDENCE (probe F-5):
```
builds an AIR / runs prove / runs verify: False
lines of the function: 20
every number it prints is (m+1)/q computed inline: True
```

### 6. FILE: f0b_prod_field_en.py | LINE: 295-330 | CLASS: TAUTOLOGY (rigged measurement)
FINDING: `measure_leaf_inversion_cost` prints "0 hits" as the measured
inversion cost, but its target is `_h_truncated("sib", 42424242)` while the
search loop runs `k in range(97)`. The target is outside the searched set, so
the 0 is fixed by construction and cannot come out any other way.

EVIDENCE (probe F-6):
```
target 42424242 (OUTSIDE range(97)): 0 hits over 97 trials
pool values with a preimage inside the pool: 97 of 97
target from inside the pool would give: 1 hit (guaranteed)
```

### 7. FILE: f0b_prod_field_en.py | LINE: 20-27, 219-244 vs 305-330 | CLASS: UNSUPPORTED-CLAIM (contradiction)
FINDING: Two sections of the same file state opposite conclusions about the
same attack. The header and `measure_leaf_hash_inversion` present the
truncated leaf as the open attack that field growth cannot close
("~q trials if the attacker can pick the leaf value to hit a truncated
target"); `measure_leaf_inversion_cost` concludes that attack "was never the
open one" and that round-3's 107-trial figure "was for a DIFFERENT
construction ... and does not transfer". Nothing reconciles them.

EVIDENCE (probe F-7):
```
STEP-2 section says attacker can pick the leaf to hit a target: True
STEP-2 section says the toy gap is the truncated leaf:            True
inversion-cost section says that attack was never open:           True
inversion-cost section says the 107 figure does not transfer:     True
```

### 8. FILE: f0b_prod_field_en.py | LINE: 167-173 | CLASS: TAUTOLOGY
FINDING: `prove()`'s guard assertions cannot fail. `trace` is initialised to
`[0]`, so `trace[0] == 0` is an identity; `acc = trace[m]` two lines above, so
`trace[m] == acc` is an identity. They document the code to itself.

EVIDENCE (probe F-8):
```
prove() calls over random + degenerate inputs: 212
cases where either asserted predicate is false:  0
```
Degenerate inputs included all-zero, all-(P256-1) and single-row matrices.

### 9. FILE: f0b_prod_field_en.py | LINE: 155-159 | CLASS: UNSUPPORTED-CLAIM (minor)
FINDING: The "production" field is 256-bit but the ROM noise is 64-bit:
`_E`/`_F` reduce an 8-byte truncation mod P256, so the noise reaches only
2^64 of 2^256 field positions.

EVIDENCE (probe F-9):
```
sampled E values: 4096
max E value bits: 64 (field is 256 bits)
fraction of the field the noise can reach: 2^64 / 2^256 = 1e-192
```

## f0b_fri_en.py — 8 findings

### 10. FILE: f0b_fri_en.py | LINE: 44-46, 177-198 | CLASS: BUG + UNSUPPORTED-CLAIM
FINDING: The header states "The degree claim is what is under test". The
verifier never tests any degree. `verify_round` checks only the folding
identity, so a fold with an inflated degree passes. Over F_97 the 48
quadratic residues are exactly the roots of `u^48 - 1`, so
`F = fold(P) + k*(u^48 - 1)` agrees with the honest fold at every checked
point while having degree 48.

EVIDENCE (probe F-1):
```
honest fold degree:            1
cheating F degree:             48
verify_round(P, alpha, cheat): True
```
This is not covered by the file's "no Merkle commitment" honest-limit note
(lines 47-51), which disclaims the soundness bound, not the degree check.

### 11. FILE: f0b_fri_en.py | LINE: 19-25, 122-137 | CLASS: BUG (missing check)
FINDING: FRI's terminal claim — the residual is a constant, here it is — is
never made or checked. Nothing asserts `deg(final) == 0`.

EVIDENCE (probe F-2):
```
honest final degree:  0
inflated final degree: 48
every round still verifies: True
```

### 12. FILE: f0b_fri_en.py | LINE: 20, 124-129, 171 | CLASS: UNSUPPORTED-CLAIM
FINDING: The docstring says "the verifier sends a challenge alpha", but
`recursive_prove` draws alpha from the PROVER's rng and `verify_round` accepts
alpha as an argument from the prover's transcript. There is no verifier-side
challenge generation, so the soundness argument (a random challenge hits a
bad polynomial with probability degree/q) has no random challenge to appeal
to; a cheating prover can search alphas freely.

EVIDENCE (probe F-3):
```
recursive_prove draws alpha from its own rng: True
verify_round receives alpha as an argument:   True
any verifier-side challenge source in the file: False
```

### 13. FILE: f0b_fri_en.py | LINE: 31-32 | CLASS: UNSUPPORTED-CLAIM
FINDING: Header measurement 3 — "The verifier cost is logarithmic (the number
of rounds), measured against the linear cost of the existing single-round
check" — has no probe. No timing, no cost comparison, no linear baseline.

EVIDENCE (probe F-4):
```
file mentions time           False
file mentions perf_counter   False
file mentions monotonic      False
file mentions cost           True   (prose only)
file mentions seconds        False
probes in the file: 3 (honest, tampered, degree-halving)
```

### 14. FILE: f0b_fri_en.py | LINE: 23-25, 185-198 | CLASS: UNSUPPORTED-CLAIM (contradicted by the code)
FINDING: "The verifier's cost becomes logarithmic in the degree rather than
linear" describes the round count, not this code's cost. `verify_round` scans
the entire domain once per round, so the verifier is linear in q.

EVIDENCE (probe F-5):
```
domain points verify_round evaluates per round: 48   ((q-1)/2)
measured verify_round cost: 7.562e-05 s/round at fixed degree 1
```

### 15. FILE: f0b_fri_en.py | LINE: 33-36 | CLASS: UNSUPPORTED-CLAIM
FINDING: Header measurement 4 — "the soundness error compounds ... a forgery
is caught with probability approaching 1 as rounds increase" — is never
measured. No probe measures any forgery-survival rate, let alone as a function
of round count.

EVIDENCE (probe F-6):
```
file mentions probability    True  (prose)
file mentions compounds      True  (prose)
file mentions approaching    True  (prose)
file mentions survival       False
```
`probe_tampered_fails` tampers ONE constant of ONE fold and returns a boolean.

### 16. FILE: f0b_fri_en.py | LINE: 30-31, 223-236 | CLASS: UNSUPPORTED-CLAIM (partially contradicted)
FINDING: The header says "a tampered quotient fails at SOME round, and the
file reports which". The tamper probe covers one coefficient of one round and
returns a boolean; no probe reports a round number.

EVIDENCE (probe F-7):
```
final fold is constant (degree 0), so the probe's tamper changes
the ONLY coefficient there is: True
coefficient positions tampered across all rounds: 4   (2 + 1 + 1)
caught by verify_round:                        4
rounds at which a tamper is reported: none
```

### 17. FILE: f0b_fri_en.py | LINE: 213-219 | CLASS: minor UNSUPPORTED-CLAIM (label ≠ measurement)
FINDING: `probe_honest_survives_all_rounds` prints "every round verifies" for
`ok`, but `ok` also ANDs in a separate degree-non-increase condition
(`_deg(tr[r]) >= _deg(tr[r+1])`, line 217). A degree failure would be reported
to the reader as a round-verification failure with no way to tell them apart.

EVIDENCE (probe F-8):
```
probe 1 ANDs in a separate degree condition: True
probe 1 prints it as 'every round verifies': True
```

## Passing regression checks

- `f0b_fri_en.py` own probes still pass 3/3, rc=0:
  honest survives all rounds (degrees [2,1,0,0], every round verifies True);
  tampered final fold verifies False; rounds halve the degree ([3,1,0,0]).
- `f0b_prod_field_en.py` own checks still pass, rc=0: honest verify at
  q=2^256 True (acc 252 bits); tampered trace entry False; wrong claimed
  accumulator False; position binding True / replayed path False;
  inversion search 0 hits; single-point tamper breaks 2 of 4 transitions.
- The toy `f0b_air_proto.py` still rejects the round-5a forgery at its
  noise-consistency check — its input binding is intact (finding 2 is a
  regression in the PORT, not in the toy).
- Both round-5a probe files run rc=0 (17 probes, 0 confirm the files' claims).

## The pattern, stated as round-4 stated it

Every finding is again "a claim the code makes about itself that the code does
not check": a verify() that takes commitments it never reads; a header that
lists four measurements and ships three; a "MEASURED" label on arithmetic; a
"0 hits" measurement whose target cannot be hit; asserts that cannot fail; a
degree claim "under test" that nothing tests; a verifier-sent challenge the
prover generates. The one new shape is finding 2 — the port is weaker than the
original it claims to carry forward.
