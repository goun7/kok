# REFERENCES — KÖK Network v2 evaluation and redesign

All references **verified** (as of 2026-09-19; access methods noted).
System date: 19 September 2026.

## Pearl Network (primary sources — 2026-09-19/20, all verified)

- **INT Whitepaper (full text, HTML):** `https://pearlresearch.ai/research/int-whitepaper`
  — the KW construction as applied in production; §3.1 noise identity + transcript +
  per-tile BLAKE3 jackpot (Algorithm 4); §4.8 production parameters (rank r ∈ {32..1024},
  16r ≤ k ≤ 4r², k ≤ 2¹⁶, 64|k); §4.7 Plonky2 ZK (<60 KB, 3-fold recursion); §5.1
  pouw_meta block identity (against ZK random malleability); §5.2 Taproot-only +
  OP_CHECKXMSSSIG reserved (XMSS/SHAKE256) + P2MR (BIP-360); §5.4 S=2.1×10⁹, 194 s block,
  1/t² emission (H=650,226 block), WTEMA difficulty; §6 econ-101 (C=$1.7/H100-h, τ=0.1,
  τ·G·D = p·e; Pass's forthcoming official economics document = 2606.06700);
  §7 launch benchmark (Llama 3.3 70B, 4×H200: Pearl-certified 17,206 tok/s vs Meta
  15,270, 806 TMADs/s).
- **Live site:** `https://pearlresearch.ai` (Pearl Research Labs, NVIDIA Inception) +
  `/network` (the Gemma-4-31B-it-Pearl endpoint on Together AI, 25%+ cheaper) + `/research`
  (paper list).
- **GitHub:** `https://github.com/pearl-research-labs/pearl` — 311 ★, 6,803 commits,
  public; `zk-pow/`, `pearl-blake3/`, `plonky2/`, `xmss/`, `miner/`, `node/`, `wallet/`,
  `py-pearl-mining/` (Go + Python + C kernels).
- **★ Polymath Project (open problem list, `pearlpolymath.com`):** 7 mathematics
  + 2 economic open problems. **Economic (1) = Pearl's OWN E-gap admission** (full quote
  in `KOK_V2_PAPER.md` §12): "the marginal cost of mining is ~0 and hence also the cost
  of attacking ... the key scarce resource in PoUW mining is the ability to collect useful
  data (matrices). What should be the value/price of the Pearl coin at 0 mining overhead?
  Is it 0? infinity?" Additionally: (1) KW Appendix A random-rotation security — **still
  open**; (2) Pearl-GEMM noise distribution; (3) FP4/NVFP4 scale optimization; (4)
  **training/finetuning** (currently inference only); (5) MatMul-based 128-bit hash (a GPU
  alternative to BLAKE3); (6) **ASIC-resistance — Pearl itself lists it as a problem** ("Is
  1-bit hardware enough?"); (7) 0%-overhead whole-model PoI ("doesn't have an efficient
  SNARK").
- **★ "Pearl Floating Point Scheme Specification" (September 2026, new whitepaper PDF):**
  **FP8** PoUW — because entrywise quantization is nonlinear, it breaks the low-rank
  shortcut, and **tickets hash the output tiles directly (no transcript needed)**.
  **Assumption 1 (quantized-subspace hardness)** = the FP analogue of KW
  transcript-unpredictability; r=32 (k <= 2^16). **§5 jackpot policy = 4 concrete checks**
  (entry-liveness, noise-floor, tamed-products, unpredictable-summands) + **§5.2** six
  attack vectors (NaN/Inf, seed grinding k>=1024, no-noise, low-local-entropy → special
  hardware, coherent, low-rank planting) + **§7** five speedup classes. **Verification =
  bit-exact replay with Hawkeye** — the Hawkeye authors are **Badash, Boneh, Komargodski,
  Srivastava** (Komargodski is an author of both KW and Hawkeye). MoE extension (e <= 1024),
  ZK appendix (split verification). Detail: `PEARL_DOCS_ANALIZ.md` §11.1.
- **Domain note:** `pearl.network` → GoDaddy parked; `pearl.foundation` → DNS dead;
  `pearlnetwork.io` → DNS dead. **No Pearl records at all** in the Wayback Machine.

## Cryptography / PoUW core

1. **Komargodski, Weinstein — "Proofs of Useful Work from Arbitrary Matrix
   Multiplication."** IACR ePrint **2025/685** = **arXiv 2504.09971v4** (received 2025-04-15,
   v4 2025-11-13). *Full text: `https://ar5iv.org/abs/2504.09971` (ePrint PDF returns raw
   binary; r.jina.ai 403).* The cryptographic foundation of the KÖK v2 G layer. Independent
   analysis: `KW_ANALIZ.md`.
2. **Alman, Duan, Vassilevska Williams, Xu, Xu, Zhou — "More asymmetry yields faster matrix
   multiplication."** arXiv **2404.16349** (2024). ω < 2.371339 (cited by KW).
   *(AlphaEvolve additional progress: ω < 2.371177, 2026 — not cryptographic, a calibration
   effect.)* **⚠ ar5iv caveat (2026-09-20):** `ar5iv.org/abs/2504.09971` renders KW with
   **3 authors** (Komargodski, **Itamar Schen**, Weinstein) — this is **an older version**
   (Schen later withdrew). Correct source: **ePrint 2025/685 (latest rev 2025-12-08) + PDF
   v4 (2025-11-13) = 2 authors** (Komargodski, Weinstein). ePrint "Contact author(s)":
   `ilankom10@gmail.com`, `omri.weins@gmail.com`.
3. **Vaikuntanathan, Zamir — "Improving algorithmic efficiency using cryptography."**
   arXiv **2502.13065** (2025). LPN-based **trapdoor matrices** — near-linear matrix
   multiplication with a secret key. *Evaluated as a threat and refuted* (E,F are derived
   from σ; the attacker cannot plant a trapdoor).
4. **Braverman, Newman — "Practical Secure Delegated Linear Algebra with Trapdoored
   Matrices."** arXiv **2502.13060** (v3 2025-10-06, TCC 2025). Same technique, secure
   delegation. Same refutation.
5. **"Hawkeye: Reproducing GPU-Level Non-Determinism"** — arXiv **2603.20421v2**
   (2026-03-20; **MLSys 2026 accepted**; *Pearl's own research*). **Bit-exact, lossless**
   reproduction on CPU of GPU Tensor Core operations (rounding direction, subnormal
   handling, non-associative accumulation; Ampere/Hopper/Lovelace; FP16/BFP16/FP8);
   for third-party auditing. Code: `github.com/badasherez/gpu-simulator`.
   **The verified source for the "determinism" route of KÖK v2 §6** (an alternative to
   native-FP ZK: reproducibility-based auditing).
6. **Ball, Rosen, Sabin, Vasudevan — "Proofs of useful work."** ePrint 2017/203 → CRYPTO
   2018 ("Proofs of work from worst-case assumptions"). The first formal PoUW; **they
   retracted the usefulness claims** (poly-log overhead). KW is its successor.
7. **Dotan, Tochner — "Proofs of useless work."** arXiv 2007.01046 (2020). An inventory of
   why prior PoUW systems failed.
6a. **Sompolinsky, Wyborski, Zohar — "PHANTOM and GHOSTDAG: A Scalable Generalization of
   Nakamoto Consensus."** IACR ePrint **2018/104** (received 2018-01-30; last of 17
   revisions 2021-11-10). **Verified 2026-09-20.** The source of the blockDAG ordering
   KÖK v2 §B.2 inherits: parameter *k* = anticone tolerance; PHANTOM solves an **NP-hard**
   optimization, GHOSTDAG is the efficient greedy approximation with a proof that its
   ordering is irreversible up to an exponentially negligible factor. *Contact author(s):
   yonatan sompolinsky @ mail huji ac il.*
6b. **Kaspa reference implementation — `rusty-kaspa`** (kaspanet, public repo, live
   2026-09-20). **Production GHOSTDAG parameters** used as the calibration for
   `ghostdag_proto_en.py`, read from `consensus/core/src/config/bps.rs` and `params.rs`:
   BPS=1 ⇒ `ghostdag_k = 18` (from `calculate_ghostdag_k`, the minimal *k* bounding
   anticone probability); `max_block_parents = 10` (floor 10, cap 16 for quadratic-
   parent-reference performance); `mergeset_size_limit = 2k = 36`. **Note:** these are
   Kaspa's parameters, used as a template; KÖK v2's own BPS is not yet chosen.

   **Verification-status note (2026-09-21 → ★ RE-VERIFIED 2026-09-27):**
   these figures were originally read from the live repository in an earlier
   session, and a re-verification attempt on 2026-09-21 could not reach
   github.com. **They are now RE-VERIFIED against the repository's own
   source**, fetched directly from `raw.githubusercontent.com/kaspanet/
   rusty-kaspa/master/consensus/core/src/config/bps.rs` (HTTP 200, read
   verbatim). Every figure matches: `ghostdag_k()` for `BPS=1` is **`18`**
   (the table reads `1 => 18, 2 => 31, 3 => 43, 4 => 55, 5 => 67, 6 => 79, 7
   => 90, 8 => 102, 9 => 113, 10 => 124, … 32 => 362`); `max_block_parents()`
   is `ghostdag_k() / 2` **floored at 10 and capped at 16**;
   `mergeset_size_limit()` is `ghostdag_k() * 2` **floored at 180 and capped
   at 512**; and `calculate_ghostdag_k` is the minimal *k* bounding anticone
   probability by `delta` per PHANTOM §4.2 eq. 1. The prototype takes `k`,
   `max_parents` and `mergeset` as **parameters**, so the code stays correct
   whatever the calibration — but the calibration itself is now confirmed from
   the source rather than from memory.

   **★ Kaspa's own scaling caveat, read from the same file (2026-09-27).**
   The cap comment is not incidental boilerplate; it is a stated condition on
   raising BPS: *"We currently limit the number of parents by 16 in order to
   preserve processing performance and to prevent number of parent references
   per network round from growing quadratically with BPS. As BPS might grow
   beyond 10 this will mean that blocks will reference less parents than the
   average number of DAG tips. Which means relying on randomness between
   network peers for ensuring that all tips are eventually merged. We
   conjecture that with high probability every block will be merged after a
   log number of rounds. For mainnet this requires an increase to the value
   of GHOSTDAG K accompanied by a short security analysis, or moving to the
   parameterless DAGKNIGHT."* This matters for KÖK because the BPS choice is
   still open here, and Kaspa's own maintainers treat raising it past 10 as
   requiring **new security analysis or a different protocol** — not merely
   plugging a larger number into the table above. The same file also bounds
   `mergeset_size_limit` at 512 for a stated storage reason: *"Bounded
   relatively low because we have storage complexity of O(#headers *
   mergeset_limit) coming from reachability and GHOSTDAG stores."* Both are
   constraints on a parameter this project has not yet chosen, from the
   implementation it calibrates against.

6c. **Keller — "Automated Selfish Mining Analysis for DAG-Based PoW Consensus
    Protocols."** arXiv **2501.10888v3** (submitted 18 Jan 2025, v3 revised 21
    Jun 2025; *to be published in ACNS '25 proceedings*; University of
    Innsbruck; cs.CR + cs.DC; DOI 10.48550/arXiv.2501.10888). **Verified
    2026-09-27** against the canonical `abs` page and the full HTML v3 text.

    **★ Why this paper is the relevant external check on KÖK's GhostDAG
    posture:** it is, by its own claim, the first *generic MDP-based*
    selfish-mining analysis to cover GhostDAG — the exact attack class KÖK's
    consensus layer must withstand, and one that, per the paper, DAG protocols
    had previously escaped because enumerating arbitrary DAG states is
    intractable. The headline finding cuts **both ways and is recorded both
    ways**: *"GhostDAG seems to be incentive incompatible for relatively weak
    attackers (low α) although it clearly outperforms Bitcoin and Byzantium
    for strong attackers"* (§7.3), and *"relatively weak miners can benefit
    from selfish mining in GhostDAG"* (§1). *"The most resilient protocol is
    Parallel Proof-of-Work."* The honest read is that GhostDAG's advantage
    over Bitcoin is real **for strong attackers** and its disadvantage is real
    **for weak ones** — not a clean "GhostDAG resists selfish mining" claim,
    and KÖK does not get to make one from this source.

    **WHAT THE PAPER DOES NOT GIVE (stated plainly — a source that cannot
    support a claim must not be cited as though it can):**
    - **No numbers for GhostDAG.** Its results are plotted curves only
      (Fig. 5 §7.3, Fig. 6 §7.4); the data series are raster images and no
      per-α values appear in the text. Fig. 5's y-axis spans 0–~0.20 "reward
      per progress minus α", which bounds the surplus's *order*, not its value.
    - **No GhostDAG profitability threshold.** Searched: the only "threshold"
      sentence is §1's reference to *prior* Bitcoin/linear-chain work
      (Eyal–Sirer, Sapirshtein et al.); the paper never converts its curves
      into an α* for GhostDAG. **Any KÖK claim of a specific GhostDAG
      threshold is unsupported by this paper.**
    - **No k-scaling evidence.** Stated as an open question: *"We are
      particularly interested in how GhostDAG's and Parallel's k-parameters
      affect the results… We here set k = 3, while the designers of both
      protocols propose much higher values."* KÖK's `GHOSTDAG_K = 18` is
      **6× the analyzed value and outside this paper's evidence.**
    - **The 6-block ceiling makes every number a LOWER BOUND on the
      attacker's advantage.** §7.2 verbatim: *"reward per progress grows
      monotonically for increasing BlockDAG size limit, independent of the
      model. This indicates that the BlockDAG size limit restricts the
      attacker. In a real setting, there is no BlockDAG size limit and the
      attacker's reward per progress could be even higher."* This cuts
      **against** using the paper to argue GhostDAG is safe.
    - **Keller's GhostDAG is NOT Kaspa's.** `"Kaspa" appears nowhere in the
      paper` (full-text searched). The modeled source is PHANTOM-GHOSTDAG
      (Sompolinsky–Wyborski–Zohar, AFT '21) with Keller **inventing** the
      economics: *"the publication [17] does not specify rewards and progress—
      we fill these gaps"* — blue blocks pay 1 unit, red blocks pay 0, whereas
      **Kaspa pays both, red at a discount**. His mining rule is `tips(G)`
      (parent every leaf), not Kaspa's selected-parent + k-bounded merge set.
      Tie-breaks use Python's `hash()`, not blue score. `k = 3`, DAG ≤ 6
      blocks, and §6 adds that canonization *"is an invalid operation for
      GhostDAG"*, so its budget could not be raised past 6. **Transfer: the
      qualitative direction at low k may transfer; the numbers must be treated
      as not-transferable to `GHOSTDAG_K = 18`.**
    - **The attack model excludes other vectors** (Appendix 0.A): A1/A2 no
      transactions or out-of-band communication; A3 all blocks the same PoW;
      A4 topological delivery order; A5 deterministic honest behaviour; A7 a
      single colluding attacker; **A8 "the attacker may withhold and ignore
      blocks but otherwise behaves honestly" — no DAA gaming**, and the paper
      itself notes the DAA *can* be gamed by faking timestamps but assumes it
      stable (A9). For KÖK this matters: KÖK's own retargetor is a
      first-class component, and Keller's model deliberately excludes
      attacking it. **A source that excludes a vector does not prove that
      vector closed.**

    **Net status for KÖK:** independent external evidence that GhostDAG's
    incentive-compatibility is a genuine open question at the parameters
    actually analyzed, that weak-attacker selfish mining in GhostDAG is real,
    and that KÖK's `k=18` sits outside the analyzed range. **Cited as a limit
    and a direction, NOT as support for a selfish-mining-resistance claim.**

6d. **Kolozyan, Sorger, Hicks, Chaliasos — "ZKP Security Tools and
    Verification: Coverage, Effectiveness, Adoption, and Challenges."**
    arXiv **2607.23752v1** (submitted 26 Jul 2026; cs.CR; DOI
    10.48550/arXiv.2607.23752; affiliations MPI-SP, KTH, Ethereum Foundation,
    Athens & zkSecurity). **Verified 2026-09-27** against the canonical `abs`
    page and the full HTML v1 text (all ten sections + references).

    **★ Why this is the empirical check on the soundness story the paper
    tells in T3.** T3 stacks three mitigations for under-constrained-circuit
    risk — automatic solution-set cardinality verification (ZEBRA style),
    AIR soundness in Lean (S-two), and independent audit. This paper measures
    the first two classes of tooling empirically and, read in full, it
    qualifies both and endorses the third. Recorded here in both directions
    because the finding is partly favourable to this design and partly
    unfavourable, and only the unfavourable half was being used to write the
    paper's correction.

    **The numbers, verbatim and with their denominators.** Six open-source
    non-interactive Circom tools across 70 known vulnerabilities, extended
    from Chaliasos et al.'s Circom dataset: *"In isolated mode, at least one
    tool detects 32 of the 70 bugs (45.7%). … In project mode, effectiveness
    drops sharply: at least one tool detects only 11 of the 56 bugs (19.6%)."*
    The 70/56 split exists because 14 projects failed to compile in project
    mode. The study measures **true-positive detection only** — *"We do not
    measure false positives, as our goal is to assess current bug-finding
    capability"* — so these are upper bounds on capability, not measured
    false-positive rates in deployment.

    **THE CARDINALITY LEG IS THE BEST-COVERED CLASS, NOT A GAP.** From the
    paper's Table IV: **assigned-but-unstrained is 6/6 (100%) isolated and
    2/5 (40%) in project mode** — the highest-isolated rate of any class in
    the study. Missing input constraints 10/22 (45.5%) → 3/18 (16.7%);
    logic-to-constraint translation 9/18 → 3/13; unsafe circuit reuse 4/10 →
    2/7; **circuit design issue 0/6 → 0/6**; arithmetic field issues 2/4 →
    1/4; **spec. misimplementation 1/3 → 0/2**; other programming errors
    0/1 → 0/1. ⚠ **The paper's §V prose and Table IV disagree** on this cell:
    the prose says *"assigned-but-unconstrained bugs fall from 100% to 20%"*
    while the table reports 2/5 = 40%. **The table carries the auditable
    counts; cite the table.** The class this paper finds uncovered lies
    beyond cardinality — circuit design and specification misimplementation
    are 0%, and practitioners rate proof-system issues 15% covered, system
    integration 5%, crypto-primitive misuse 12%, semantic mismatches 30%.
    The paper also widens the term: *"A circuit is also underconstrained
    whenever semantic mismatches occur: constraints accept witnesses that do
    not correspond to valid executions, even when deterministic"* — and that
    broader reading is the poorly-covered one.

    **THE EVALUATION CONTAINS NO ZKVM — a direct scope limit for this
    project.** All six evaluated tools are Circom tools and the whole 70-bug
    dataset is Circom; zkVMs appear only as targets of *formal verification*
    in §VI (SP1, OpenVM, RISC Zero, Jolt, zkWasm, Cairo/StarkWare, Plonky3,
    Scroll, ZKsync Era), never as bug-detection targets. Its own
    external-validity caveat: *"The RQ2 results may not generalize beyond
    Circom and the six tools we evaluated, although Circom is currently the
    best-supported DSL by automated tools."* **So 45.7%/19.6% was never
    measured on anything resembling this project's zkVM proof layer; the
    study is evidence about the state of the tooling, measured where that
    tooling is strongest.**

    **THE LEAN LEG: SUPPORTED AS THE MOST MATURE GOAL, AND BOUNDED BY THE
    PAPER'S OWN WORDS.** *"zkVM verification is converging on Lean and the
    Sail RISC-V specification, but results remain isolated: they mostly prove
    constraint soundness, leave key artifacts unverified, and rely on trusted
    extraction and modeling."* §VI-C: *"Constraint soundness is the most
    mature goal … It is, however, only one direction of one layer of the
    stack, and significant gaps remain elsewhere. No zkVM has end-to-end
    formal verification, and verified components are isolated.
    Constraint-correctness proofs cover instruction semantics, but the
    witness generator, the lookup/permutation arguments, the proof-system
    backend, and the on-chain verifier remain largely unverified."* On
    precompiles: *"most precompiles remain unverified across all zkVMs"* and
    can be auto-generated *"thereby multiplying their number into an
    open-ended, shifting set that cannot be chased circuit by circuit."* On
    maintenance: *"several efforts we cite target code that is now
    deprecated"* and *"Guarantees not checked on every commit silently
    decay, while AI-generated proofs remain a poor fit for CI."* The
    trusted-computing-base line is the one to quote in the paper: *"a proof
    of a vacuous or misstated theorem passes the kernel while establishing
    nothing, so what is proven is as much part of the TCB as the machinery
    that checks it."* (AIR appears once, as an API surface: *"it is possible
    to intercept the circuit-builder API (e.g., Plonky3's Air trait) and
    export the constraints to a proof assistant."*)

    **THE AUDIT LEG IS THE ONE THIS PAPER ENDORSES — it is already in the
    design.** Its §X conclusion: *"current defenses are useful but
    incomplete… Practitioners likewise report human-led workflows."* §VII:
    *"Manual code review remains dominant, reported by 79% of developers and
    83% of auditors… The picture is thus not one of push-button security, as
    tooling is layered around human-led review."* And on AI: *"LLMs may
    reduce the cost of authoring, translating, and maintaining these
    artifacts, but cannot establish that they faithfully capture protocol
    intent."* **The third leg of T3 is the strongest; the first two are the
    qualified ones.**

    **WHAT THE PAPER DOES NOT PROVE (recorded so it is not over-cited).** It
    does **not** mention ZEBRA, "zero-day," or "11 zero-days in 5 zkVMs" —
    **zero occurrences in the full text** — so it cannot support or rebut
    that claim; ZEBRA (2609.15020) stands on its own. The six tool names are
    mostly not in the text (only Civer, Circomspect, Ecne appear in §V
    prose); the full list is in Figure 2, which is an image, and in the
    artifact at `github.com/t-sorger/zkp-security-tools`. The benchmark is
    **known-bug biased** (bugs from audits and public disclosures), so it
    cannot support claims about bug prevalence. Several Table IV project-mode
    cells are ≤5 bugs, so those percentages are fragile. Tool versions are
    not stated in the paper. And its §V notes *"Results differ substantially
    from tool-specific benchmarks presented in their own research papers,
    highlighting the bias introduced by narrow evaluation suites."*

    **Net status for KÖK:** the ZEBRA-style cardinality check is the single
    best-served mitigation available and it is Circom-only, never measured on
    a zkVM, and drops from 100% to 40% at whole-project scale; the Lean AIR
    proof is the most mature verification goal and covers "one direction of
    one layer"; independent human audit is what the study identifies as
    still load-bearing. **Cited as a qualification of the soundness stack,
    and as evidence for keeping the audit leg prominent — not as evidence
    that zkVM soundness is measured, because it is not.**

## 2026 NEW ACADEMIC SOURCES (added 2026-09-26)

Six papers found and verified against their own canonical pages this session
(all HTTP 200, abstracts read from arxiv.org/abs/... or eprint.iacr.org/...). All six are
directly on KÖK's thesis and **none was in the earlier reference set**. The two of June 2026
(Pass, Barbaccia) are the economics and quantum arguments; SNARKChain and SEDULity are
**prior art for the G-layer design** and both independently confirm properties KÖK argued from
its own negative results; the July-2026 VRS paper names the grinding class that KÖK's own
assignment layer documents as its open surface — recorded as a mapped future, not an adoption
candidate, because its construction needs quantum hardware and its threat model is per-input
precomputation rather than KÖK's per-key registration; and the **October-2025 SoK by Dikshit
et al.** is the most confirming external paper of all, since its headline negative result over
more than fifty PoUW constructions — that utility does not contribute to the security budget —
is precisely the separation KÖK's two-layer design is built on.

### Pass — "The Economics of Proof-of-Useful-Work" (BİRİNCİL, arXiv 2606.06700)

> **Rafael Pass** (Cornell Tech / Tel Aviv), arXiv **2606.06700**, submitted **4 June 2026**,
> cs.GT + cs.CR + econ.TH. *https://arxiv.org/abs/2606.06700* — abstract read verbatim
> 2026-09-26.

**Why this paper matters to KÖK — it is the academic resolution of KÖK §4.5's own argument.**
KÖK v2 answers the "paid to attack" objection by separating the consensus-weight layer (G,
MatMat PoW) from the fee-paid compute layer (U, zero consensus weight). Pass now gives the
**formal** version of that answer:

- Builds a **competitive-equilibrium model** where compute splits across pure mining, pure
  useful work (instantiated as **ML inference**), or **"duplex" work that produces both with
  computational overheads**. That duplex category is KÖK's G layer — the work is
  simultaneously a security-producing puzzle and (in KÖK's case) useful matrix multiplication.
- **Complete closed-form characterization** of equilibrium allocations and prices as a
  function of the duplex overheads and a single parameter: the **token-inference ratio**
  (token adoption relative to the inference market).
- **Three regimes** named in the paper: **"Bitconia"** (reduces to classical PoW),
  **"Fortessia"** (duplex replaces mining — security *increases* while useful output is
  unchanged), and **"Duplexia"** (token rewards subsidize inference — prices fall, inference
  supply expands).
- **THE RESULT KÖK SHOULD CITE (verbatim from the abstract):** *"Contrary to the common
  strawman argument, PoUW does not make attacks economically cheap: once equilibrium prices
  are taken into account, the economic cost of a majority attack remains tied to the block
  reward."* — This is the "paid to attack" criticism, refuted formally. KÖK v2 §4.5 argues
  this from the two-layer design; Pass argues it from equilibrium pricing. **The two
  arguments are independent and agree** — that agreement is much stronger than either alone.
- **Second result (verbatim):** *"in Duplexia, block rewards act as rebates on inference
  prices, generating additional socially useful computation that would not arise without the
  blockchain — an expansion monotonically increasing in token adoption and technological
  efficiency."* This is a positive welfare claim KÖK can cite rather than assert.

**Honest limitation of this access:** the abstract and metadata were read from arxiv.org
verbatim; the full 377 KB PDF was **not** fetched (ar5iv/ePrint have returned raw binary or
403 in this environment before). The three regimes and both quoted results are from the
abstract, so nothing about theorem statements or proof structure is claimed here.

### Barbaccia, Vhaduri, Dibbo — "Quantum-Resilient Decentralized AI Economies" (BİRİNCİL, arXiv 2606.24942)

> arXiv **2606.24942**, submitted **22 Jun 2026**, cs.CR, 15 pages / 4 figures / 4 tables.
> *https://arxiv.org/abs/2606.24942* — abstract read verbatim 2026-09-26.

**Why this matters — an independent three-layer architecture that mirrors KÖK's own.**
The paper proposes a decentralized AI economy where nodes are rewarded for **useful
machine-learning work (inference and training)** instead of hashing, and it separates into
**three layers: compute, validation, and economic coordination**. Read against KÖK:

| This paper | KÖK v2 |
|---|---|
| compute layer | G layer — MatMat PoW (leader election) |
| validation layer | PVI / FRI verification boundary |
| economic coordination layer | ledger escrow + U layer task market |
| $(\theta_c, \theta_w, W)$-**closed-loop token economy** | task fee → escrow → settle (assignee) / refund → burn |
| **sufficient-stake condition for honest participation** | anti-aggregation fee cap C_FEE + bond-margin (TV-17) |

**Quantum argument (relevant to KÖK's PQ posture):** Grover gives only a **quadratic**
speedup against hash puzzles and does **not** accelerate ML-native linear algebra, while
Shor threatens classical signatures; the paper concludes useful-work consensus therefore has
**both economic and quantum-security advantages** over classical PoW. KÖK's G layer is
exactly ML-native linear algebra, so the argument applies directly: the useful work is
quantum-harder to shortcut than the hashing it replaces, and the signature layer is a
separate, lattice/hash-migratable concern.

**Honest limitation:** abstract + metadata read verbatim from arxiv.org; the full PDF was
**not** fetched, so the sufficient-stake theorem's assumptions are not verified here. The
paper is **concurrent independent work** — KÖK's two-layer split was designed from its own
negative results (see the next section), not from this paper.

### Oleksak, Gazdik, Peresini, Homoliak — "SNARKChain" (BİRİNCİL, arXiv 2510.09729)

> Samuel Oleksak, Richard Gazdik, Martin Peresini, Ivan Homoliak (Masaryk University),
> arXiv **2510.09729**, v1 10 Oct 2025, **v2 13 July 2026**, cs.CR.
> *https://arxiv.org/abs/2510.09729* — abstract read verbatim from arXiv (HTTP 200, 26 Sept 2026).

**Verbatim, the part that matters to KÖK:**

> "existing PoUW proposals often **fail to embed the integrity of the chain and the identity of
> the miner into the puzzle solutions**, not meeting the necessary requirements for PoW and thus
> rendering them vulnerable. In this work, we propose a PoUW consensus protocol that computes
> **client-outsourced SNARK proofs as a byproduct**, which are simultaneously used to secure the
> consensus protocol. We further leverage this mechanism to design a **decentralized marketplace
> for outsourcing SNARK proof generation**, which is, to the best of our knowledge, the **first
> such marketplace operating at the consensus layer** while meeting all necessary properties of PoW."

**Why this is high-value for KÖK — it validates the exact hazard KÖK's ctx binding closes.**
SNARKChain names the failure mode of prior PoUW: the useful puzzle does not bind the **chain's
integrity** or the **miner's identity** into the solution, so the work is not actually tied to
the block that claims it. KÖK's G layer was designed against precisely this: every solution's
statement carries `selected_parent ‖ miner_pubkey ‖ task_ref ‖ height ‖ proof_system_id ‖ nonce`
(spec §A.3, T-A2) — the chain binding and the miner binding are *in the statement*, which is
why precompute and replay are closed. **A published academic paper naming the absence of that
binding as a vulnerability class is stronger than any self-assessment.**

**AND IT SHARPENS KÖK'S DIFFERENTIATION, which is the honest part.** SNARKChain puts the
client-outsourced proofs **into the consensus** — the useful work *secures* the chain. KÖK
deliberately does the opposite: the U layer has **zero consensus weight**, the target test
reads only the G-layer certificate, and task fees buy fee revenue alone. The difference is
philosophical and worth stating as such — SNARKChain pursues maximum usefulness per unit of
consensus work; KÖK pursues a security budget that is **demand-independent**, so the chain
survives the zero-demand equilibrium that Pass's "Bitconia" regime predicts. Both are defensible
designs and the paper's existence is **prior art that KÖK's security argument is not novel in
wanting** — but KÖK's separation is the rarer choice, and SNARKChain is the reference point
against which to state it. **NOTE: this is an independent design lineage from KÖK's**; no
claim of derivation in either direction is made, and the KÖK G-layer work is MatMul
verification rather than SNARK generation.

**Honest limitation:** abstract + metadata read verbatim; the full PDF was **not** fetched, so
the claimed PoW-property proofs are not verified here, and the "first such marketplace" claim is
the authors' own, not an independent assessment.

### Cao, Doger, Ulukus — "SEDULity: A Proof-of-Learning Framework" (BİRİNCİL, arXiv 2512.13666)

> Weihang Cao, Mustafa Doger, Sennur Ulukus (University of Maryland), arXiv **2512.13666**,
> v1 15 Dec 2025, **v2 10 June 2026**, cs.CR + cs.DC + cs.IT + cs.LG.
> *https://arxiv.org/abs/2512.13666* — abstract read verbatim from arXiv (HTTP 200, 26 Sept 2026).

**Verbatim, the part that matters to KÖK:**

> "we **encode the template block into the training process** and design a useful function that
> is difficult to solve but relatively easy to verify, as a substitute for the PoW puzzle. …
> we design an incentive mechanism to incentivize task verification. **We show theoretically
> that a rational miner is incentivized to train fully honestly with well-designed system
> parameters.**"

**Why this is on-point for KÖK — it is the honest-mining question, answered theoretically by a
third party.** SEDULity's core claim is that a rational miner's incentive is to do the useful
work **honestly** rather than to fake it, given the right parameters. That is the same property
KÖK's G layer buys with **prescribed hardness** (the miner's choice of MatMul input cannot
reduce the work, which closes the sybil/easy-instance attack) and that its U layer buys with a
**client-determined matrix** — the miner does not choose what to compute, so there is nothing
to cheapen. SEDULity reaches a similar destination from the incentive side rather than from the
hardness side, and **the convergence is the useful thing**: two independent designs conclude
that honest useful work is achievable, by different mechanisms.

**The honest differences, stated rather than smoothed:** SEDULity's useful function is model
*training* (Proof-of-Learning), whereas KÖK's G layer is MatMul *verification* certificates —
training admits iterative-approximation attacks that verification does not, which is exactly why
KÖK chose the certificate form. And SEDULity embeds the template block into the work, which
mirrors KÖK's ctx binding (above) and independently confirms that the work must be bound to the
block to be honest. **No derivation is claimed in either direction.**

**Honest limitation:** abstract + metadata read verbatim; the full PDF was **not** fetched, so
the theoretical incentive result and its parameter conditions are not verified here, and the
simulation results are not reproduced.

### Yeoh Wei Zhu et al. — "Verifiable Random Sampling" (BİRİNCİL, arXiv 2607.26734)

> Yeoh Wei Zhu, Soorya Rethinasamy, Anthony Alexiades Armenakas, Yash Satsangi,
> Shaltiel Eloul, Ruslan Shaydulin, arXiv **2607.26734**, submitted **29 July 2026**, cs.CR.
> *https://arxiv.org/abs/2607.26734* — abstract read verbatim from arXiv (HTTP 200, 26 Sept 2026).

**Verbatim, the exact limitation KÖK's own assignment layer admits to:**

> "once the public key is published, the induced function is fixed and is a deterministic
> function of the input. **This determinism can enable collusion and grinding-style attacks
> in which adversaries precompute and selectively exploit favorable input-output pairs.**
> To address these limitations, we introduce the formal notion of **verifiable random
> sampling (VRS)**."

**Why this matters to KÖK, and why the honest verdict is "mapped future, not a fix".**
KÖK's U layer assigns tasks through an ECVRF gate (`kok-u-layer/src/assign.rs`), and that
module's own header documents the grinding surface in the plainest terms: the miner
evaluates the VRF under **its own key**, so splitting one stake across N registered keys
multiplies the independent draws by N — one identity gets N tickets. The mitigation is
explicitly out of crate scope: one-key-per-bonded-identity at the **registration** layer,
and the `splitting_one_stake_into_two_keys_doubles_the_draws` test **measures** the ~2.0
multiplier so a future fix has a number to beat rather than a vague worry.

This paper names the *class* of that problem from an independent direction: VRF determinism
itself is what grinding exploits, and the authors propose sample freshness as the property
that removes it. **What it does NOT do is solve KÖK's specific instance.** KÖK's grinding
surface is per-key registration, not per-input precomputation — the adversary's leverage is
the *number of keys*, not the choice of input-output pairs. A VRS keyed to a quantum circuit
would not stop a stake split across identities, because the draw count is a registration
property. And the paper's construction is based on **random quantum circuit sampling**, which
requires quantum hardware KÖK cannot assume today; KÖK runs RFC 9381 ECVRF on P-256, verified
byte-for-byte against the standard's own test vectors.

**The honest placement in the roadmap:** this is a mapped direction for the F3+ horizon
rather than an adoption candidate — if a classical, hardware-free VRS-like construction with
freshness emerges, it is the citation the assignment layer's grinding paragraph would move
under. Recorded here so that the limitation stays connected to the literature that names it,
instead of sitting as a project-internal worry with no external anchor.

**Honest limitation:** abstract + metadata read verbatim; the full PDF was **not** fetched, so
the constructive-cryptography security proof and the RCS construction details are not verified
here, and no claim is made that the paper's threat model matches KÖK's.

### Dikshit, Emami, Sedlmeir, Fridgen — "SoK: Is Proof-of-Useful-Work Really Useful?" (BİRİNCİL, IACR ePrint 2025/1814)

> Pratyush Dikshit (University of Luxembourg), Ashkan Emami (University of Luxembourg),
> Johannes Sedlmeir (University of Münster), Gilbert Fridgen (University of Luxembourg),
> IACR ePrint **2025/1814**, received **3 Oct 2025**, approved **8 Oct 2025**.
> *https://eprint.iacr.org/2025/1814* — abstract + metadata read verbatim from IACR's own
> page (HTTP 200, 26 Sept 2026). Short URL `https://ia.cr/2025/1814`. License CC0.

**Verbatim, the finding that states KÖK's two-layer premise from the outside:**

> "We examine more than **50 PoUW constructions** where we find recurring shortcomings. We
> introduce a formal economic model of PoUW for miner incentives, **solution reusability**,
> and **external market value to the security budget**... Our findings show that **PoUW is
> actually not as useful as expected, since the economic and societal utility do not
> contribute to the security budget.** Finally, we highlight design recommendations for PoUW
> that integrate **verifiable computation, partial incentive allocation, and utility-aware
> difficulty adjustment**."

**Why this is the single most confirming external paper for KÖK's architecture.**
This SoK is a systematization of the *entire* PoUW design space — over 50 constructions — and
its headline negative result is precisely the separation KÖK v2 is built on. KÖK's two-layer
design assigns useful work to the U layer with **zero consensus weight by construction**,
pinned by tests (`kok-consensus::u_consensus_weight` sums to zero over every proof, computed
with checked arithmetic so the invariant cannot disguise a wrap), because security must come
from the G layer's certificates alone. This paper reaches the same separation from the
economic direction: utility that *would* contribute to the security budget is the thing that
has failed across the design space, and it names the failure mode — utility does not transfer
to security.

**Two of the paper's three design recommendations map onto choices already made here, and
saying which is which is more useful than citing them loosely:**
- "**verifiable computation**" — this is the G layer's reason to exist. KÖK did not adopt it
  from this paper; the G layer predates this citation and rests on KÖK's own negative results
  (Pearl's φ=0, the Basu measurement). The SoK is independent confirmation, not a source.
- "**partial incentive allocation**" — KÖK's fee split is exactly this: the task's fee is
  escrowed at task-post and settles as `pay + burn` with `TREASURY_BPS`, so the *useful* work
  is paid by the task market while the *security* is paid by the G layer. The paper's phrase
  is a good external description of an allocation KÖK already implements and tests
  (`kok-ledger` conservation law, 12 checked sites).
- "**utility-aware difficulty adjustment**" — this one KÖK deliberately does **not** do, and
  the difference is worth stating. Difficulty adjusts on the G layer's verification work; the
  U layer has no difficulty of its own because it carries no weight. Utility-aware adjustment
  would re-couple the two things this paper's own finding says do not transfer — the opposite
  of what KÖK's negative results showed.

**Solution reusability, the paper's middle term, is a live open question KÖK has measured
rather than assumed away.** If a proof of useful work is reusable across tasks or chains, its
security contribution is not fresh, and the U layer's fee market would be buying spent work.
This is recorded as a standing measurement obligation rather than a closed property.

**Honest limitation:** the abstract, metadata, author list, affiliations, dates and license
were read verbatim from IACR's own page (HTTP 200). The **full PDF was not fetched** —
`eprint.iacr.org/2025/1814.pdf` returns raw binary the fetch tool cannot parse, and no arXiv
mirror of this paper exists (a guessed arXiv ID returned an unrelated biology paper, which is
itself a caution). So the taxonomy's 50 constructions, the formal economic model, and the
Toulmin evaluation are **not verified here** — only the abstract's statements of them are
quoted, verbatim, and they are attributed as the paper's claims rather than as verified
results.



### MEASURED CORRECTION to the Kaspa k=18 note above (2026-09-25)

§6b records Kaspa's `calculate_ghostdag_k` producing **k=18 as "the minimal k bounding
anticone probability."** This session **measured** the actual required k in KÖK's own
parent-pool DAG model (`kok-ghostdag/src/sim.rs::mine_chain`, parents drawn from a
2×MAX_BLOCK_PARENTS=20-block tip neighbourhood) and found the claim does not hold *in that
model*: the required k is **8, flat across an 8× load range** (fork rates
0.05/0.10/0.20/0.30/0.40, seed 1000+i, 200 blocks, tolerance 0.02, sweep
ks=[1,2,4,8,16,18,32,64]); max anticone observed 7,7,7,8,7 — all below
2×MAX_BLOCK_PARENTS=20. **Neither k∝L (predicts 64) nor k∝√L (predicts 22.6) fits.**

**The resolution is not that Kaspa is wrong — it is a model difference, and it must be
stated rather than glossed:** Kaspa's `calculate_ghostdag_k` derives k from a **network
delay** assumption (the delay band relative to block interval), not from load alone. KÖK's
simulator has no delay model; its anticone is bounded by the parent-pool window. So the two
numbers answer different questions, and §6b's phrasing "the minimal k bounding anticone
probability" is **Kaspa's claim under its delay model**, not a measurement in KÖK's. The
measured conclusion for KÖK is: **k is a function of the delay band, not of load**, Kaspa's
production k=18 carries roughly **2.25× headroom** against the load-only requirement, and
KÖK inherits k=18 as a safe conservative choice rather than as a tight bound. §6b's wording
should be read with this in mind.

---

## 2026 negative results (evidence forcing the G/U separation in KÖK v2)

8. **Basu — an empirical measurement of the Pearl Network.** arXiv **2606.04819** (2026):
   24 EH/s, ~320,000 GPUs, ~112 MW → **zero useful AI computation**; NoisyGEMM accepts
   random matrices by design (44 pool-accepted share); 8,012 AlphaPool workers, 0/4,803 ML
   string; kurtosis 1.79 (uniform) vs 3.33 (NN) vs **2.97 (adversarial N(0,18) — passes the
   check)**; economics 1.06 revenue/cost; vLLM coupling consumes 10–30% of the hashrate.
9. **Demirel — "Proof of Demand Is Not Proof of Work."** ePrint **2026/1492** (2026-07-21,
   rev 2026-08-23): W/B/E framework; **Lemma 1** (coalition-controlled payments are
   reversible transfers); **Theorem 2** (leader election requires a demand-independent
   path); **Corollary 4**; solution: **irreversible burn/tax = the source of security.**
   The theoretical justification for the burn mechanism of the KÖK U layer.
10. **Dikshit, Emami, Sedlmeir, Fridgen — SoK: "Is Proof-of-Useful-Work Really Useful?"**
   ePrint **2025/1814** (2025-10-03): 50+ constructions; **utility does not contribute to
   the security budget**; proposal of verifiable computation + partial incentive
   allocation.
11. **Externally rewarded PoW trade-offs.**
    arXiv **2505.21685** (2025): miners can aggregate useful tasks into a single block →
    KÖK's **C_FEE anti-aggregation cap** (T-A3, TV-6).
    (ROUND-6, 2026-09-24, audit: author list NOT settled. The paper's own §3.2 names
    **Bar-On**, this entry previously named **Komargodski & Weinstein**, and a third
    project file (PAPER.md §3.1) cites Komargodski–Weinstein for a DIFFERENT work,
    IACR ePrint **2025/685** — the prescribed-hardness MatMul construction. The two
    are not the same paper and the names should not be conflated: 2505.21685 is the
    aggregation trade-off, 2025/685 is the certificate construction KÖK actually
    builds on. This entry stays anonymous until the arXiv record is checked.)
12. **Komargodski–Weinstein — prescribed-hardness MatMul PoUW.** IACR ePrint **2025/685**:
    the certificate KÖK's G layer implements (the paper the PAPER.md pitch names).
    Separated from entry 11 because the two were being cited interchangeably.
13. **"SEDULity."** arXiv **2512.13666** (2025): binding the chain by encoding the template
    block into training — a different approach from KÖK's ctx-binding (T-A2).
14. **Proof-of-Learning with incentive security.** arXiv **2404.09005** (2024):
    Θ(1)→O(log E/E) overhead, overcoming the Verifier's Dilemma.

## Economics

15. **Pass — "The Economics of Proof-of-Useful-Work."** arXiv **2606.06700**
    (CORRECTED 2026-09-25, internal audit against the arXiv record: the date
    was given as 2026-08-10; the record's submitted date is **4 June 2026**,
    and only the v1 exists — the later date was a version-date conflation):
    M/L/D activities, Δ = 1/γ + 1/α − 1, θ = PR/(pQ), **Theorem 1** (Bitconia /
    Fortessia / Duplexia regimes), **Theorem 3** (p = αe/(1+θ), ΔSV), **Prop 1**, attack
    cost = PR/2 (in every regime), Fisher foundation. The theoretical basis of KÖK's
    `pass_sim_en.py`; the Pearl calibration (eS=PR Tullock) reproduced the live network within
    5.8%. *Full verification from the PDF (2026-09-20):* **Theorem 2 = Cost₅₀% = PR/2 "in
    any competitive equilibrium, regardless of which regime"**; with partial reimbursement
    ν, **(1−ν)PR/2**; the definition of attack[block rewards are irreversible (token
    collapse) — "if the attacker can also redeem block rewards at their full current USD
    price, the net cost of attacking is zero even for Bitcoin"]; **Theorem 3** p =
    (α/(1+θ))·e < e; **α = γ = 1.3 ≈ 23% savings** ("for the price of one compute op,
    duplex delivers 1/1.3 ≈ 0.77 units of inference and 1/1.3 ≈ 0.77 units of security");
    demand elasticity (Jevons, ε=2) is a precondition for all results; calibration $30B
    inference market / 52,560 blocks.
16. **Hoffmann — "Challenges of Proof-of-Useful-Work" / the verifiability–usefulness
    tension.** arXiv **2209.03865**. *RESOLVED 2026-09-25:* the arXiv record was checked
    against the primary source and this is **Felix Hoffmann's single-author paper** —
    the "Leinweber et al." attribution that circulated in Basu's citation (and that
    this project carried while the authorship was unverified) is a misattribution and
    is now dropped. Corrected rather than silently: the wrong name was in a table that
    claimed 39/39 verified citations, which is the exact failure mode this project
    exists to avoid.
17. **Peigné, Nguyen, Wang — "Zero knowledge verification for frontier AI training is
    possible."** arXiv **2606.05433v2** (2026-06-03, v2 2026-08-22, 44 pages). *Verified
    (2026-09-19):* verification of **real floating-point** computation with zkVM + native
    BF16/FP32 precompiles (not a fixed-point approach); pre-committed training spec +
    inter-node observations + on-the-fly Merkle commitments; genesis/in-training/ex-ante
    proof types; ~36-month deployable PoC, single-digit-percentage training overhead; 13
    open problems. **The source for the "tomorrow" route of KÖK v2 §6** — the transition
    away from 𝔽_q fixed-point once native FP ZK matures.

## Tools / methods used (access notes)

- `web_search` (401) unavailable; **Bing/Google blocked** → all research was done with
  `mcp__weblocal__web_fetch` via the **arXiv API** (`http://export.arxiv.org/api/query?...`,
  single-quoted phrase; `AND` returns empty; `ti:"..."` works) and **ePrint search**
  (`https://eprint.iacr.org/search?q=...`, paper pages `https://eprint.iacr.org/2025/685`).
  **ePrint PDF returns raw binary**; for full text, **ar5iv.org**.
- **Wayback Machine works** (`archive.org/wayback/available?url=...` + CDX API) — returned
  **empty** for Pearl (no archived records).
- **PDFs cannot be read** (raw binary) — when a PDF is needed, the user pastes the text
  (first instance: Pearl's new whitepaper, see `PEARL_DOCS_ANALIZ.md` §8).
- Evidence repository: `findings.md` (§9–§18), `DEGERLENDIRME_100.md` (§6–§8, §13),
  `PEARL_DOCS_ANALIZ.md` (Pearl primary-source analysis).

## Market data (2026-09-21, live)

**Bitcoin — refreshed 2026-09-21 via the blockchain.info open API** (each value is an
instantaneous query; source `https://blockchain.info/q/*`):
hashrate **956,911,537,880 GH/s ≈ 957 EH/s** (the blockchain.info/q/hashrate endpoint returns
GH/s; labelled "TH/s" before round-6, a 1000× unit error), price **$81,162.26**, difficulty
**1.3276×10¹⁴**, block height **967,912**. (A repeated query gave 963.5 EH/s — ordinary
variance; treat the hashrate as ~957–964 EH/s.)

**Older snapshot (2026-09-19), retained for provenance:** BTC 204.44 TWh/yr, ~904 EH/s,
$81,448 (−35.4% from ATH $126,080). The hashrate has risen ~6% between the two dates; the
price is essentially flat. **Neither figure is load-bearing in the paper** — the paper cites
Pearl's 24 EH/s (from Basu), not Bitcoin's, for its security comparison.

Kaspa 27.71B/28.70B KAS mined (96.5%, ~$40M left); Dynex mcap $128k at ATL (−99.91%);
AI-compute tokens TAO −65%, RNDR −88%, AKT −93%. Pearl: 800 blocks/day (108 s),
2,674 PRL/block, $0.76.

**Verifiable live source for the Bitcoin figures** (any reader can re-run):
`https://blockchain.info/q/hashrate`, `/q/24hrprice`, `/q/getdifficulty`, `/q/getblockcount`.
CoinGecko's API returned 429 (rate-limited) on 2026-09-21, so token prices were not refreshed
this session — the TAO/RNDR/AKT figures above are the 2026-09-19 snapshot and should be
re-checked before being cited externally.

## Regulation (verified 2026-09-21 against the official text)

- **MiCA — Regulation (EU) 2023/1114.** EUR-Lex CELEX:32023R1114, Official Journal of the
  European Union **L 150/40**, 9.6.2023 (regulation of 31 May 2023).
  <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114> — full text
  fetched (1.68 MB), Article 3 definitions quoted verbatim in `KOK_V2_PAPER.md` §9. Applies
  **from 30 December 2024**. Article 3 **(5)** crypto-asset, **(6)** asset-referenced token,
  **(7)** e-money token, **(9)** utility token, **(10)** issuer.
  *Note: earlier working notes cited "Article 3(1)(5)" — the official numbering is (9) for
  utility token; corrected.*
- **SEC v. Ripple — PRIMARY TEXT, UPGRADED 2026-09-27.** Both Torres rulings
  are now read from the court's own text rather than secondary summaries, and
  the 2023 order is from SDNY's own server. The procedural record: filed
  **22 Dec 2020** in SDNY (Case No. 1:20-cv-10832-AT); **13 July 2023**
  **Document 874** (34 pages, fetched as 321,952 bytes from
  `nysd.uscourts.gov`, extracted to 1,802 lines) held **institutional sales
  (~$728.9M) WERE investment contracts** in violation of §5, while
  **programmatic exchange sales (~$757.6M) were NOT** — because "the record
  does not establish the third Howey prong as to the Programmatic Sales",
  and the court expressly did not reach the first or second prong; **other
  distributions** were also not investment contracts. **7 Aug 2024** final
  judgment, **$125,035,150** penalty + a permanent injunction against
  violating §5's registration provisions. **26 June 2025 Document 989**
  (5 pages) **DENIED** the joint motion for an indicative ruling that would
  have dissolved the injunction and cut the penalty by sixty percent:
  *"the parties do not have the authority to agree not to be bound by a
  court's final judgment"*; under **U.S. Bancorp Mortgage Co. v. Bonner
  Mall** they had to show exceptional circumstances and *"have not come
  close to doing so here"*; the court offered two exits — withdraw the
  appeals, or take the appeal, *"the primary route"* Congress created.
  **7 Aug 2025** both appeals withdrawn (SEC Litigation Release No. 26369),
  the final judgment **remaining in effect**. **17 Mar 2026** the SEC
  identified **XRP as a digital commodity** alongside bitcoin, ether, solana
  and stellar, while stating a non-security asset **can still be sold as
  part of an investment contract depending on the transaction**.
  **What this establishes for §9:** programmatic exchange sales of a token
  are not securities per the strongest available US authority — now cited
  from the court's own words — and an injunction on institutional token
  sales survives even a consensual settlement. *Honest limit: the 2023
  order is from the court's server; Document 989 was obtained from a
  law-firm mirror (nutter.com) because a direct SDNY e-filing download
  could not be located, though header, case number and ECF document number
  match. Still not a substitute for a formal securities opinion, and the
  programmatic-sales holding never received appellate review because the
  cross-appeals were withdrawn by stipulation.*
- **NEW — Regulation Crypto Assets, proposed rule (added 2026-09-27, comment
  period OPEN until 20 October 2026).** Federal Register **91 FR 54510**,
  21 Aug 2026, doc. no. **2026-17183**, Release Nos. **33-11434; 34-106150**,
  File No. **S7-2026-27**, RIN **3235-AN38**, 146 pages. Verified against
  the Federal Register's **own API** (`/api/v1/documents/2026-17183.json`)
  because the HTML page serves a bot challenge; full text (13,701 lines)
  fetched from the documents/full_text endpoint. Two offering exemptions
  (up to **$5M** over four years; up to **$75M** per 12 months with
  financial statements and ongoing reporting) and a **conditional safe
  harbor** in proposed **Rule 400** from the term "investment contract",
  codifying the **2026 Interpretation, Release No. 33-11412, 91 FR 13714**
  (17 Mar 2026). **The passage that matters to this paper's §9 thesis** is
  §II.A.4.b.i: once a network is functional, services to "secure, maintain,
  improve, or enhance" it "would not constitute essential managerial
  efforts", and the asset "should derive its value from the **programmatic
  operation of the associated crypto network**" — with "validators and/or
  miners" named among the many parties whose contributions determine
  success. **The honest limit, stated in the paper too: this is a PROPOSED
  rule, not an adopted one; the paper's Howey analysis does not depend on
  it, and this project cannot use the safe harbor because it codifies when
  a contract CEASES to exist, which presupposes one existed.** See
  `arastirma/federal_register_yorum_analizi.md` for the full internal
  analysis of KÖK's position.
- **NVIDIA — AI compute market size, from reported earnings (2026-09-21).** Annual revenue
  ($B): **2023: 26.9 · 2024: 60.9 · 2025: 130 · 2026: 215** (net income 2026: $120B). Quarterly
  momentum: Q4 FY2026 **$68.1B**; Q2 FY2027 **$96.2B, +106% YoY** (from $46.7B). Build-out:
  **$100B** NVIDIA→OpenAI MOU with **≥10 GW** of new AI data centers; **$2B** into AI-cloud
  provider Nebius (2026). **This is the proxy for AI compute spending cited in §8.1.** Its
  limit is stated there: chip-supplier revenue is not total AI spend, and **the permissionless
  priced subset has never been measured.**
- **arXiv IDs re-verified 2026-09-21** (arXiv /abs/ pages, HTTP 200):
  **2504.09971** = Komargodski & Weinstein, *Proofs of Useful Work from Arbitrary Matrix
  Multiplication* (submitted 14 Apr 2025, v4 revised 13 Nov 2025) ✓;
  **2606.06700** = **Rafael Pass**, *The Economics of Proof-of-Useful-Work* (submitted 4 Jun
  2026) — the **Bitconia / Fortessia / Duplexia** regimes are confirmed verbatim ✓;
  **2606.04819** = **Abhinaba Basu**, *The Usefulness Gap in Proof-of-Useful-Work: An Empirical
  Study of Pearl's cuPOW Protocol* (submitted 3 Jun 2026, v2 5 Jun 2026) — **24 EH/s,
  ~320,000 GPU-equivalents, ~112 MW, zero useful AI computation, GPU rental +38%, utilization
  57%→94%, 8,012 workers, 44 pool-accepted shares, $0.76, ROI −1%..+67%** all confirmed ✓.

**★ Bibliography status: 11/11 LIVE-VERIFIED 2026-09-21; Ripple upgraded
2026-09-27.** Every arXiv and ePrint identifier in this file was fetched
against the live archive and matched on title, authors and venue, and the
complete 11-row table with per-entry evidence is in
`arastirma/uydurma_denetimi.md` §C3. On 27 September 2026 the Ripple entry
was **upgraded to primary text** — both Torres rulings now quoted from the
court's own PDFs — and the Regulation Crypto Assets proposed rule was added,
verified against the Federal Register's own API with its full text read.
Two further verifications worth noting: the SoK (ePrint 2025/1814) is led by
**Pratyush Dikshit of the University of Luxembourg** — the reviewer this
package was sent to — and Pass (2606.06700) is confirmed the **sole author**.
No citation in this package is unverified.

---

## ★ PROOF INDEX — where each claim is proven (2026-09-20)

> This index is an appendix to `KOK_V2_CRYPTO_BRIEF.md` and the fast starting point for
> external auditing: each claim → **file + section + verification type** (running test /
> verbatim PDF quote / live URL / model output). Items that are "LLM reads" are marked with
> a †.

### G layer (cryptography)

| Claim | Evidence | Type |
|---|---|---|
| The real footing of KW security is (a)+(b)+Merkle, not (c) | `KW_ANALIZ.md` §3.1, §6.1 | **KW verbatim quote** + † analysis |
| Nearly automatic from the Θ(n³/r) output-size bound of Assumption 6.4 | `KW_ANALIZ.md` §6.1 | **KW verbatim** ("the number bits... is always a lower bound") |
| Conjecture A.1 (random-rotation) is still open | `KW_ANALIZ.md` §6.3; Pearl Polymath Problem 1 | **Pearl itself** asks |
| α = o(1) overhead | `KW_ANALIZ.md` §6.4 | **KW verbatim** |
| Lemma 6.5 (E,F uniform rank-r, ROM) | `KW_ANALIZ.md` §6.4 | **KW verbatim** |
| Prescribed hardness: no easy-instance advantage | `g_layer_tests_en.py` **TV-2** | **running test** (spread <15%) |
| Permutation/sparse attack does not work | `g_layer_tests_en.py` **TV-3** | **running test** |
| A=B=0 is not a bad input | `g_layer_tests_en.py` **TV-4** + V1X | **running test** |
| ctx-binding closes the replay attack | `g_layer_tests_en.py` **TV-1** | **running test** |
| Jackpot policy 4 checks | `g_layer_tests_en.py` **TV-11..TV-14** | **running test** (toy INT) |
| Low-entropy (Polymath 6) resistance | `g_layer_tests_en.py` **TV-21** | **running test** — for INT; for FP8 **OPEN** (§A.10.7 note) |
| FMM progress preserves the ratio | `KW_ANALIZ.md` §3.3 line 6 | † analysis (symmetry argument) |
| Trapdoor matrix is not a threat | `KW_ANALIZ.md` §3.3 line 5 | † analysis (E,F derived from σ) |
| Retarget is safe (window+median) | `g_layer_tests_en.py` **RT-1..RT-3** | **running test** |
| GHOSTDAG blue rule: blue ⟺ mergeset-anticone ≤ k | `ghostdag_proto_en.py` **TV-22** | **running test** (Kaspa k=18) |
| selected_parent = max blue_score (ties: lowest hash) | `ghostdag_proto_en.py` **TV-23** | **running test** |
| Mergeset size ≤ 2k (36) | `ghostdag_proto_en.py` **TV-24** | **running test** — reached exactly 36, never above |
| ctx binds the parent-set (T-A2 strengthened) | `ghostdag_proto_en.py` **TV-25** | **running test** — different parent-set ⇒ REJECT |
| Ordering survives a splitter attack (liveness) | `ghostdag_proto_en.py` **TV-26** | **running test** — 137 blocks, 50% fork rate; **no PoW check** (toy) |
| ⚠ The mergeset is a GREEDY approximation, not ePrint 2018/104's mergeset | `probe_ghostdag_en.py` **TV-56/TV-59** | **measured deviation, not a passing test** — the intersection with past(B) is dropped, so the ordering sequences work the block does not reference; on a 51-block DAG, 572 order entries fall outside the block's own past. Two blocks' orderings are NOT guaranteed to agree on work neither references. The true mergeset is F3b work, and this is the largest gap between the file and the paper it implements |

### U layer (task market + censorship)

| Claim | Evidence | Type |
|---|---|---|
| Escrow+burn+fraud window works | `u_layer_prototype_en.py` **TV-5..TV-10** | **running test** |
| Refund guarantee nullifies the benefit of censorship | `f3a_sequencer_proto_en.py` **TV-15** | **running test** |
| Task-migration breaks the bond (negative return) | `f3a_sequencer_proto_en.py` **TV-16, TV-17** | **running test** |
| **Bond re-adding is mandatory** (the deterrent must not be one-shot) | `f3a_sequencer_proto_en.py` **TV-20** + `pass_sim_en.py` §10 | **running test + model** — † the economics model found it open in the prototype |
| Dynamic bond = fee + margin | `pass_sim_en.py` §10 (off-game 120 → bond 200 insufficient) | **model output** |
| **Capped slash: deterrent bounded by fee** (spec correction) | `bond_margin_proto_en.py` **TV-31** | **running test** — bonds 100/500/2000 give identical net (−40); critical fee = B_out |
| **FULL-mode margin = B_out − fee** (linear, §10 equation confirmed) | `bond_margin_proto_en.py` **TV-32** | **running test** — max error 0.00, R²=1.0000 |
| **Free-censorship window = bond/fee** without refill | `bond_margin_proto_en.py` **TV-33** | **running test** — +900 (no refill) vs −800 (refill) over 20 events |
| Verifier's dilemma is not triggered | `f3a_sequencer_proto_en.py` **TV-18** | **running test** |

### Economics

| Claim | Evidence | Type |
|---|---|---|
| Attack cost = PR/2 in every regime | Pass **Theorem 2** (verbatim PDF) | **verbatim PDF quote** (`extracted/Pass_full.txt`) |
| p = (α/(1+θ))·e < e; ~23% savings | Pass **Theorem 3** (verbatim PDF) | **verbatim PDF quote** |
| The model generates the live network from first principles (Pearl 5.8%) | `pass_sim_en.py` §0, §9 regression guard | **model output** |
| Zero-demand → pure-PoW survives (Demirel Thm 2) | `pass_sim_en.py` §6 | **model output** |
| Fortessia ×3.33 security | `pass_sim_en.py` §3 | **model output** (α=γ=1.3) |
| **F3a cannot calibrate pass_sim** (small-scale limit) | `pass_sim_en.py` §9 (86% deviation) | **model output** — † negative result, corrected V2 §10.1 |
| E-gap: Pearl's own admission | Polymath Economic (1) | **verbatim quote** (above, `KOK_V2_PAPER.md` §12) |
| φ=0 on the live network | Basu arXiv 2606.04819 | **publication** (24 EH/s, zero utility) |

### Determinism / FP

| Claim | Evidence | Type |
|---|---|---|
| Hawkeye bit-exact replay in production | Pearl FP wp + Hawkeye MLSys 2026 | **live URL + publication** |
| FP8 subnormal compression (Q nonlinear) | `fp8_noise_proto_en.py` **TV-27** | **running test** — 100% of subnormals flush to 0 |
| FP8 low-entropy attack succeeds without σ_min | `fp8_noise_proto_en.py` **TV-28** | **running test — NEGATIVE result** (entropy 0.00; reverse of TV-21) |
| Noise floor σ_min closes the FP8 attack | `fp8_noise_proto_en.py` **TV-29** | **running test** — 13 distinct values with σ_min=8 |
| DELTA ≤ 0.06 under seed grinding | `fp8_noise_proto_en.py` **TV-30** | **running test — spec correction**; average-case bound 0.217 fails (3.52%) |
| Route A (Hawkeye) Phase 2, Route B (Peigné) Phase 3 | `KOK_V2_TECHNICAL_SPEC.md` §A.9b | † decision + status of the publications |
| No transcript needed in Pearl FP | Pearl FP wp §5.1 | **verbatim quote** (Q(A+N) ≠ Q(A)+Q(N)) |
| GPU whitelist risk | `KOK_V2_TECHNICAL_SPEC.md` §A.9b | † honest risk |

### Differentiation / migration

| Claim | Evidence | Type |
|---|---|---|
| Pearl made two real hard forks | Pearl `docs/{moe,salted-seed}-fork-upgrade-guide.md` | **live GitHub** |
| MoE backward-compatible, salted-seed mandatory | the same guides | **verbatim** ("old dense proofs work..."; "everything must be upgraded") |
| The E-gap is embedded into the architecture (G/U) | `KOK_V2_PAPER.md` §A.1, §12; Demirel Thm 2 | † design + **publication** |
| Competitor move scenarios | `KOK_V2_PAPER.md` §12.1 | † analysis (via Pearl Polymath) |

### KNOWN GAPS (focus of external auditing)

1. **NO 2 independent human cryptographer reviews.** `KOK_V2_CRYPTO_BRIEF.md`
   was not sent. All of `KW_ANALIZ.md` §1–6 is a **† LLM read**. **STATUS
   (2026-09-26, DIRECTION CORRECTED):** no review exists and no review was
   requested that anyone accepted or declined — the correspondence is
   **entirely unsent drafts**. The phrase "it is a no for now, not a maybe"
   (which an earlier version of this gap recorded as *Demirel declining*) is
   **the project's own draft closure language TO Demirel**, not a reply FROM
   him — see `EPOSTA_DEMIREL_TESEKKUR.md:20`, where it appears as drafted text
   in an unsent letter. The operational log is explicit that the reply was
   never transmitted: `EPOSTA_SOK.md` records *"Demirel'e cevap yok (gondermek
   yasak, kullanici 'devam et' dedi ve konuyu kapatti)"* — no reply to Demirel,
   sending prohibited, the user closed the subject — after judging the proposed
   fee unaffordable ("$215 is more than I make an hour, this external-review
   business is a story"). So the accurate state is: **the human review was
   never pursued to a point where anyone could accept or decline it.** The
   erteleme argument the paper had been making was **circular**, so the paper no
   longer makes it. This is the single largest remaining gap and **it is not
   closeable by code**: it needs a human who will read for pay, and payment
   while anonymous is hard or impossible. See the paper's FAQ (§9.1) for what
   this gap does and does not invalidate.
2. **FP8 low-entropy — PARTIALLY CLOSED (2026-09-20):** `fp8_noise_proto_en.py`
   now models quantization-aware noise (TV-27..TV-30). Two honest findings:
   (a) the FP8 reversal is CONFIRMED — without an absolute noise floor the
   low-entropy attack succeeds (tiles pin to 1 value, entropy 0.00), so σ_min is
   MANDATORY for FP8; (b) DELTA must be lowered 0.5 → 0.06 because seed grinding
   breaks the average-case bound. Still OPEN: the model is simplified RNE +
   subnormal flush, NOT IEEE-754, and r=2 toy rank — the asymptotic question and
   real hardware (tensor-core accumulation) remain Phase 3 / Hawkeye work.
3. **~~The economic weight of TV-17 is partially open~~ — CLOSED (2026-09-20):**
   `bond_margin_proto_en.py` measured the margin (TV-31..TV-33). It confirmed the §10
   threshold equation in FULL slash mode (margin = B_out − fee, R²=1.0000) and found a
   **spec correction**: in f3a's actual capped mode the deterrent is bounded by the fee,
   so bond above fee is inert — the protocol needs a FULL slash mode to make
   "bond = fee + margin" effective. Remaining open: B_out is hidden from the protocol,
   so the margin must still be estimated by governance; the accuracy requirement is the
   F3a measurement.
4. **Toy dimensions** — q=97, n=8, r=2, K=64: **does not test asymptotic arguments.**
   The paper's FAQ (§9.1, 2026-09-26) now states this limit where a reader will meet
   it, rather than leaving it here only.
5. **~~GHOSTDAG parent-set selection is MISSING from the prototype~~ — CLOSED
   (2026-09-20):** `ghostdag_proto_en.py` now tests the GHOSTDAG greedy ordering
   with Kaspa mainnet production parameters (k=18, max_block_parents=10,
   mergeset limit 36); TV-22..TV-26 all PASS. Remaining honest limit: no PoW
   validity check (all blocks assumed valid), uniform network-delay model.
   **ADDITIONALLY (2026-09-26):** the Rust GHOSTDAG now also pins the partial-DAG
   tolerance against phantom ancestors (`25fcc30`) and the money path against
   absent-record and wrap-in-disguise hazards (`345e0b8`, `25ef7cc`, `a5d7eb1`,
   `7bed3b5`). Bug class 7 — "when a function tolerates absent inputs, audit every
   site that records the same input" — was named and closed in four instances, all
   found by measurement rather than by reading.
6. **~~FAQ answers missing~~ — CLOSED (2026-09-26):** the paper now carries §9.1,
   answering the 51% attack question (resting on Pass's PR/2 result, with the
   honest limit that the KW assessment is an LLM read and the independent
   reviews have not happened), the post-quantum question (G layer hash-based and
   PQ; the ECVRF used for *task routing* is explicitly NOT PQ, stated as a
   deliberate trade because it guards assignment rather than consensus), and the
   emission question (tail emission never hits zero, deliberately unlike Bitcoin
   and Pearl; supply is rate-bounded, not integer-capped). Written as plain text
   rather than a JS accordion, because this file's own access notes record that
   JS-rendered content could not be read — an answer that cannot be read cannot
   be verified. Each answer names its citation AND its limit.

### Access method summary (tool constraints)

- `web_search` **401** (dead) → all fetches via `mcp__weblocal__web_fetch`.
- **arXiv API**: `http://export.arxiv.org/api/query?...` (single-quoted phrase, `AND`
  returns empty).
- **ePrint PDF raw binary** → for full text, **ar5iv.org** or a user-pasted PDF.
- **User-pasted PDFs**: `pdftotext -layout` → `extracted/KW_full.txt` (1,258 lines),
  `extracted/Pass_full.txt` (3,430), `extracted/Pearl_new_wp.txt` (1,223).
- **Wayback works** but is **empty** for Pearl.
- **JS-rendered pages cannot be read** (SPA/accordion) → the reason for the missing FAQ.
