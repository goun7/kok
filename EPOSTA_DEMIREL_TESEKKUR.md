Subject: Re: Independent review of a PoUW security design — thank you

Dear Ömer,

Thank you for the reply and for reading the package. I want to answer
your three points directly.

Payment. You are right, and the revised paper contradicts itself here. A
fixed fee cannot also come after funding, and a review whose payment
depends on its findings is not an independent one. I have no schedule
that satisfies both, and I will not try to renegotiate terms you have
already set as conditions.

Prototypes. You are right that the revised paper cites files that were
not in the ZIP. They have been changing faster than the bibliography
between sends. I am not attaching them. There is no point in asking you
to spend time on work we already know we cannot commission, and the list
below only says which files the citations refer to.

Timing. Rather than leave this half open: it is a no for now, not a
maybe. The design still has to be built, and that goes on regardless.

Thank you for the read. The three questions located the two places where
the paper overstates its position, which are the two above.

Best regards,
Kök Protocol

---

## FILE LIST (2026-09-23)

The files the revised paper cites, and what each one is. The files
themselves are not attached.

All prototypes are Python 3 stdlib only and run clean unless marked.
None requires a testnet, a deployment, or any third-party package.

### A. The two-layer L1

| File | What it is |
|---|---|
| `g_layer_tests_en.py` | **Layer G**, the PoW certificate: KW/cuPOW MatMul kernel, Merkle-bound tile, target grinding, block validation (TV-1..TV-4, TV-11..TV-14) |
| `u_layer_prototype_en.py` | **Layer U**, the verifiable-compute market: escrow, burn, slash, VRF assignment, fraud window, anti-aggregation bound, utility density (TV-5..TV-10, TV-38, TV-39) |

### B. The proofs of useful work

| File | What it is |
|---|---|
| `f0b_air_proto.py` (~1700 lines) | **F0b, the AIR chain** — the soundness-critical file. Three verifier layers: plaintext, quotient, masked; the input binding runs through all three (TV-40..TV-43, TV-66, TV-70) |
| `f0b_prod_field_en.py` | The same AIR over a 256-bit field with a 32-byte leaf digest (TV-76) |
| `F0B_PRODUCTION_DESIGN.md` | The order of work to close the toy field limit, and which of the three attack classes field growth alone does not close |
| `probe_f0b_zk_en.py` | TV-65: the original zero-knowledge claim retracted; TV-66 replaces it |

### C. The ordering

| File | What it is |
|---|---|
| `ghostdag_proto_en.py` | The DAG ordering: mergeset, blue/red coloring, recursive blue_score, selected-parent chain, total order (TV-22..TV-26) |
| `probe_ghostdag_en.py` | TV-56..TV-59; TV-59 measures the mergeset deviation against ePrint 2018/104 |

### D. The economic model

| File | What it is |
|---|---|
| `pass_sim_en.py` | The pass-regime model: Bitconia/Fortessia/Duplexia, cost, price formation, Pearl calibration to 5.8% |
| `probe_pass_sim_en.py` | TV-61..TV-64 |
| `bond_margin_proto_en.py` | TV-31..TV-33: bond margin, fee-capped slash |
| `f0_demand_discovery.py`, `f0_candidate_list.py` | Demand-discovery tooling |
| `adoption_econ.py` | Adoption dynamics: liquidity barrier, cold start, escape threshold (TV-34..TV-37, TV-60) |

### E. Measurement and audit

| File | What it is |
|---|---|
| `probe_edges_en.py` | TV-45..TV-49 |
| `probe_u_layer_en.py` | TV-51..TV-55 |
| `probe_field_scale_en.py` | TV-71: the toy field as a parameter choice, measured at three field sizes |
| `probe_live_demand_en.py` | TV-72: Pearl's live network reproduced to 5.8%, utility density measured at zero |
| `probe_blindspot_en.py` | TV-73: the U-layer driven into corners the tests do not cover |
| `audit_turkish_en.py` | Character-set audit on the English files |

### F. The documents

| File | What it is |
|---|---|
| `KOK_V2_PAPER.md` | The design paper |
| `KOK_V2_TECHNICAL_SPEC.md` | The spec with the full finding table, TV-1..TV-76. If one file is read, this is it |
| `KOK_V2_REFERENCES.md` | Bibliography, citations verified against primary sources |
| `KOK_V2_CRYPTO_BRIEF.md`, `KW_ANALYSIS_EN.md`, `KW_ANALIZ.md` | The KW analysis already sent to you |

That is the full list. If a file is missing here, it is internal working
notes rather than a prototype or a document.
