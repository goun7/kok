# Research log — what is not yet built (started 2026-09-21)

Purpose: while KÖK waits on Astria and Demirel, investigate path B and the wider
question of what system is actually needed, using current sources rather than
intuition. KÖK stays on path A; this is separate and does not commit to anything.

Method carried over from F0: every claim sourced, intent marked UNKNOWN where not
stated, and nothing presented as a measurement that was not measured.

**Pre-existing work — read this first.** An earlier session already ran the core
market research and it is in `arastirma/pazar_ve_rekabet_2026.md` (397 lines,
Turkish report, all prices live-fetched 2026-09-21). Its five headline findings:

1. **GPU pricing floor.** H100 on-demand $2.89-6.16/GPU-hr, spot/preemptible
   $2.15-2.46; Akash $1.33, io.net $2.20. KOK must sell below ~$2/GPU-hr to
   compete, which is hard without block-reward subsidy.
2. **"Free compute" is the wrong frame.** Pass's model shows useful compute is an
   inference rebate paid for by token emission, not a free byproduct.
3. **PoUW produced no useful work empirically.** Pearl: 24 EH/s, 320K GPUs,
   112 MW, zero useful computation; budget GPU rental +38%, utilisation 57→94%,
   research workloads displaced.
4. **Almost nobody publishes real USD revenue.** Aethir is the exception
   ($127.8M/2025, $166M ARR). The two other live PoUW chains (Qubic, Dynex) publish
   no compute revenue, and Dynex is cancelling its utility token (Feb 2026).
   Bittensor's revenue is ~88% emission. No revenue-proven predecessor exists for
   the "PoW security + compute sale" combination.
5. **Verifiable-compute demand is crypto-internal.** Axiom proves Ethereum blocks
   (EthProofs) and Lighter EVM; =nil; became an L2; N1 became a financial L1. None
   publish revenue, and no evidence was found of enterprise "prove this
   computation" demand. KOK's U layer may find its realistic customers in other
   chains, not enterprises.

Sources for those: arXiv 2606.06700 (Pass), 2606.04819 (Basu), 2209.03865
(Hoffmann), 2510.09729 (SNARKChain), 2405.19027, 2512.13666, 2102.08107 (Ciaian et
al., mining cost/reward/security interdependence), plus live pricing pages.

**This log therefore does not repeat that work.** What follows is the layer the
earlier session did not cover: the 2026 competitive landscape as a taxonomy, the
marketplaces' own admissions about token-usage decoupling, and the physical
constraints on centralized supply. Where the two overlap, the earlier file is
authoritative and this one points to it.

## Source 1 — Rafael Pass, "The Economics of Proof-of-Work" (arXiv 2606.06700)

- Submitted 4 Jun 2026, revised 24 Aug 2026.
- **The author was consulting for Pearl Research Labs when he wrote it.** This is
  not independent criticism of Pearl; it is Pearl's own theoretical foundation.
  That matters for how it should be read.

### What it models

Competitive equilibrium for a PoUW chain. Compute splits three ways: pure mining,
pure useful work (instantiated as machine-learning inference), or "duplex" work
that produces both at some computational overhead.

One parameter pins the whole equilibrium: the **token/inference ratio (T/I)**,
token adoption relative to the size of the inference market.

### The three regimes

- **Bitconia** — the useful work is not adopted and the economy collapses back to
  classical PoW. Security exists, usefulness does not.
- **Fortessia** — duplex replaces pure mining. Security rises while useful output
  is unchanged.
- **Duplexia** — token rewards subsidise inference, prices fall, and inference
  supply expands. Block rewards act as rebates on inference prices, producing
  computation that would not exist without the chain.

### The result that matters most to us

The common strawman says PoUW makes attacks cheap, because an attacker is "paid
to attack." The paper shows the opposite: once equilibrium prices are accounted
for, the economic cost of a majority attack stays tied to the block reward.

### Why it matters for KOK, and where it does not

The paper is a *defence* of PoUW economics, and it is the strongest available one.
It also gives us a vocabulary: KOK's question "does anyone pay" is precisely the
question of whether the chain lands in Bitconia or escapes it, and the paper says
the answer hinges on the T/I ratio rather than on the cryptography.

But note the limit. The model assumes an inference market exists and that demand
is elastic enough to absorb subsidised supply. Pearl's measured result — zero
useful compute sold at 24 EH/s — is evidence that arriving in Duplexia is not
automatic. The paper explains *why* subsidised inference would expand; it does
not establish that buyers appear. KOK's phi measurement is still the test.

**Status: read abstract and structure in full. Theorems not yet read in detail.**

## Source 2 — AI agent infrastructure (security gaps) — EVALUATED, DOWNGRADED

The headline suggested a missing AI-agent security primitive. Reading the sources
changed the picture:

- The CertiK report attributes 2026 losses mostly to **North Korean actors and
  cross-chain failures**: a $293M Kelp DAO breach via LayerZero cross-chain
  messaging, and a $280M Drift Protocol hack.
- The AI component is **phishing, deepfakes, and social engineering** aimed at
  users, plus autonomous tools scanning contracts for bugs. Zerion lost about
  $100K to a social engineering campaign against its hot wallets.
- The recommended defence is user-side: verify URLs, use cold wallets.

**Conclusion: this is not a protocol gap.** The missing piece is human vigilance
and custody hygiene, not a chain-level primitive. Building an L1 feature here
would be solving a people problem with consensus. **Rejected as a direction.**

The Autheo page on agentic payments was also read and discarded: it is a
competitor's marketing surface for a node sale, not an independent analysis.

## Source 3 — Akash's burn-mint engine

Fetched from akash.network/token (2026-09-21):

> "Under AEP-76, deployments mint stable internal credits by burning AKT. The
> system automatically executes these token burns to settle provider payments,
> linking token scarcity directly to infrastructure demand."

This is notable for KOK. Akash ties demand to token burn directly: a deployment
burns AKT to pay providers, so usage is mechanically linked to scarcity. The
structure is close to KOK's U layer, where a settled task burns part of the fee
irrecoverably. The design is proven in production at Akash's scale, which is
supportive for KOK's mechanism, but Akash's scale is the relevant unknown and
this page states no usage figures.

**Status: design confirmed, demand magnitude UNKNOWN. Akash's stats page is
JS-rendered and returned no numbers.**

## Source 4 — Basu's Pearl measurement, read in full detail

arXiv 2606.04819v2 (5 Jun 2026). The numbers now have their full context:

- **24 EH/s, ~320,000 GPU-equivalents, ~112 MW, zero useful computation.**
- vast.ai budget GPU rental prices rose **38%** in two weeks after the mining
  software went public, with utilisation surging from **57% to 94%**.
- 8,012 workers analysed (about 21% of hashrate): all have inference-capable
  hardware, yet the dominant mining software contains **no inference code paths**
  and generates matrices from random seeds.
- Random matrices pass verification **by design**. Basu's open-source miner got
  44 pool-accepted shares on NVIDIA, AMD, CPU, and Apple Silicon, and earned
  1.2477 PRL on mainnet.
- Kurtosis distinguishes uniform-random matrices (1.79) from quantised NN weights
  (3.33), but adversarial Gaussian sampling reaches 2.97 at **zero extra cost**,
  so the check is trivially defeated.
- Mining economics are marginal: +67% ROI on RTX 3060 Ti, -1% on RTX 3090, -99%
  on an MI300X. The absence of inference overhead, estimated at a **10-30%
  hashrate reduction**, gives miners a direct economic reason to skip useful work.

### The sentence that defines the problem

> "Pearl's protocol verifies computational **correctness** (the GEMM was performed
> accurately) but not computational **utility** (the matrices served an AI purpose)."

This is the verifiability-usefulness tension, and it is exactly what KOK's
architecture separates: the G layer guarantees prescribed-hardness MatMul (the
correctness side), while utility lives only in the U layer, where it must be
**paid for**. Pearl's failure is that usefulness was an economic property nobody
paid for, so miners took the free option and skipped it.

Basu's own analysis confirms the mechanism: skipping inference costs nothing and
saves 10-30% of hashrate. Any design that leaves usefulness optional will get the
same result, at any scale.

## Source 5 — Akash Q1 2026 report, with the key figures

Fetched from akash.network/blog/akash-network-q1-2026-report (2026-09-21):

- **$5 million all-time compute spend**, crossed in Q1 2026. This is cumulative,
  not quarterly, and it is the honest reference point for what a decentralised
  compute marketplace actually sells.
- **AkashML reached 1.7 billion tokens/day** on OpenRouter.
- **BME (burn-mint equilibrium) went live on mainnet 23 March 2026** via
  Proposal 318.
- Homenode Beta opened for consumer GPUs (RTX 4090, 5090, RTX 6000 Ada), framed
  as resilience against physical data-centre attacks.

### The admission that matters most

The report describes the problem BME was built to solve, and it is the same
problem KOK's U layer addresses:

> "when tenants pay in USDC, demand for AKT weakens. **Usage grew while AKT's role
> as the network's core economic unit eroded.**"

Akash ran the experiment KOK is designing around: stablecoin payments drove
adoption but decoupled usage from the token. BME is their fix, and it works by
buying AKT on the open market and burning it into ACT for settlement. KOK's
irrecoverable burn does the same job structurally, but at the protocol level
rather than through a two-token settlement path.

## The comparison that gives phi its scale

| | Pearl | Akash | KOK (target) |
|---|---|---|---|
| Compute sold | **zero** at 24 EH/s | $5M all-time | phi > 0 |
| Token tied to usage | no, mining only | yes, via BME burn | yes, fee burn |
| Usefulness optional? | **yes, and it was skipped** | n/a, it is a marketplace | **no, it must be paid for** |

This is the honest scale. Akash, the leading decentralised compute marketplace,
has sold $5M of compute cumulatively. That is a real number, small against cloud,
and it is what "demand exists" looks like in this market. Pearl's zero is what
"supply without demand" looks like.

For KOK the lesson is twofold. Utility must be **paid for**, because optional
utility is skipped (Pearl, proven at scale). And the token must be tied to usage,
because decoupling them erodes the economic unit even while usage grows (Akash,
stated in their own report). KOK's U layer does both by construction.

## Source 6 — The 2026 PoUW competitive landscape

Fetched from lordofpearls.xyz (10 May 2026). **The bias is stated before use: the
site is Pearl-affiliated and openly advocates PEARL as "the one to watch." It is
useful for the taxonomy and the mainnet-status table, not for conclusions about
who wins.**

The taxonomy is the valuable part. Three properties separate real PoUW from
marketing:

1. The mining work **is** the useful work — block production is the act of doing
   the computation.
2. The output is **verifiable on-chain** — a miner cannot fake it.
3. **There is a paying customer** — someone outside the chain wants the output
   enough to pay for it. Otherwise the work is "slightly more expensive busywork."

The third test is the one Pearl's own measurement says it fails, and it is the one
KOK's phi measures directly.

### Status table (as the site reports it)

| Project | Useful work | Mainnet | Real users |
|---|---|---|---|
| PEARL | LLM inference (NoisyGEMM) | Apr 2026 | live gateway |
| Bittensor | subnet ML tasks | 2023 | mostly internal |
| Render | GPU rendering | 2020 | production, but PoS |
| Gensyn | ML training | expected 2026 | not yet |
| Akash | generic compute | live | production, marketplace not PoUW |
| io.net | GPU aggregation | live | some, DePIN not PoUW |
| Golem | generic compute | since 2018 | low usage |

Two things follow. First, **nobody in the true-PoUW bucket has a paying customer
yet** — Bittensor's reward flow is described as mostly internal economics. Second,
the projects with real customers (Render, Akash, io.net) are **marketplaces on
PoS**, not PoUW consensus. The industry has split: useful work exists, and true
PoUW exists, but not in the same system.

### The Gensyn point worth tracking

One claim in the post is not advocacy: ML training is roughly 1000x the compute
spend of inference, and the hard part is verifying remote training without redoing
it. Gensyn has been building that for years, and if their verification works it
changes the category. KOK's G layer is on the inference side (MatMul prescribed
hardness), so this does not compete directly, but a training-verification
breakthrough would shift where the demand sits.

## Source 7 — The physical constraint on centralized AI

Fetched from akash.network/blog/ais-infrastructure-problem-is-bigger-than-the-grid
(16 Apr 2026). The global-context piece, and the strongest demand-side signal found:

- **Nearly half of US data centers planned for 2026 are delayed or canceled**,
  per Bloomberg, due to land resistance, community opposition, regulatory bans,
  and energy constraints.
- **Maine has a moratorium** on new data center development.
- In Missouri, residents voted out half a city council that had backed a data
  center project.
- Farmers declined $15M and $26M offers for land, choosing conservation over sale.
  A volunteer fire department declined a $250K Google donation tied to a project.
- **Gas turbine wait times extend to seven years** (IEEE Spectrum), which makes
  interim grid solutions incompatible with AI's pace.

The structural claim: centralized AI cannot scale at the speed it needs, because
land, permitting, and energy move on multi-year timescales while AI demand moves
in months. The proposed answer is to move compute to where energy already exists
rather than building energy where compute is.

### Why this is a real demand signal, unlike the others

The AI-agent gap was a people problem. This is a physical constraint, and physical
constraints do not resolve themselves. If centralized inference capacity is
genuinely supply-constrained, buyers have a reason to look elsewhere that has
nothing to do with crypto ideology — they simply cannot get capacity. That is the
first external force found that could pull demand into a permissionless market
without anyone having to be persuaded.

**Caveat, and it is a real one:** this is an Akash blog post arguing for Akash's
own thesis. The Bloomberg and IEEE figures are cited but were **not independently
fetched**, and "nearly half delayed" is exactly the kind of claim that needs a
primary source before it is relied on.

## Where the research stands

Four candidate directions have now been tested:

- **AI agent security gap** — rejected for the losses CertiK measured, then partly
  reinstated by APort Vault, which measures a protocol-level boundary rather than
  user carelessness. Not a chain, but relevant to who the buyer is.
- **Decentralized compute demand** — confirmed real but small. Akash at $5M
  all-time spend against Aethir's $127.8M for 2025, with physical constraints now
  limiting centralized supply on two independent axes.
- **PoUW with paying customers** — empty. Nobody in the true-PoUW bucket has one,
  and the marketplaces that do are PoS.
- **Computation market settled on a ledger** — **no longer empty.** arXiv 2609.21728
  ships a reference implementation on Solana. The unoccupied cell is the PoUW half,
  not the market half.

The synthesis so far: KOK's design is aligned with the two failures that have
actually been measured (optional usefulness gets skipped; decoupling token from
usage erodes the token), and it targets a narrower gap than this log first claimed.
Whether that gap can be filled is still exactly what phi measures.

## Source 8 — Gensyn has moved, and the training thesis needs updating

Fetched from gensyn.ai (2026-09-21). The competitive picture shifted and the
earlier note needs correcting.

Gensyn is no longer purely a verifiable-training play. Recent items:

- **"Introducing open-1b: the first model you don't have to trust"** (15 Sep 2026)
  — a model with verifiable provenance.
- **"Gensyn Launches Delphi: Decentralised Information Markets"** (7 May 2026)
  — a pivot toward prediction markets and agentic trading.
- **"Credibly Neutral AI Oracles"** (8 Jul 2026) — research on dispute mechanisms
  for AI report layers.
- **"REE: Reproducible Execution Environment"** (17 Mar 2026).
- **IR3DE-AXL: Collective Inference Network** (8 Sep 2026).

The training-verification thesis from the PoUW landscape post appears to have
broadened into verifiable AI more generally, with prediction markets as the
application. So the "1000x training market" is not unclaimed; the strongest team
working on it has repositioned around verifiable inference and oracles, which
overlaps the same demand KOK's U layer targets from the other side.

What this does not change: Gensyn is still not a PoUW chain, and their proof work
is verification of training and inference rather than prescribed-hardness
consensus. But it does mean the "empty cell" observation needs a sharpening. The
gap is specifically **PoUW consensus with a paying customer**, and Gensyn is
working on the verification half of that from a non-consensus direction. If they
succeed at cheap verifiable inference, the buyer-side problem KOK is trying to
solve becomes easier for everyone, including KOK.

**Status: homepage fetched. Protocol specifics not yet read.**

## Source 11 — Akash 2025 in review: the scale of the reference marketplace

Fetched from akash.network/blog/akash-2025-year-in-review (9 Jan 2026). This fills in
the scale that the Q1 report's $5M figure lacked context for:

- **Deployments grew 466% to over 3.1 million created** in 2025.
- **Daily fees hit all-time highs above $13,000.**
- **AkashML launched managed inference at 70-85% lower cost than AWS.**
- The network held a **consistent 60% utilization rate for accelerated compute**.
- Grayscale named AKT a "Top 20 Asset with High Potential" for three consecutive
  quarters.
- H100s remained allocation-only through 2025, with 6-12 month wait times for
  enterprise buyers; AWS and Azure raised prices while reducing availability.

The last point is the demand-side fact that matters most for KOK. **Compute access
became the primary business constraint** for startups and mid-market AI builders,
and the incumbent cloud responded to scarcity by raising prices. That is the
economic condition under which a buyer moves providers for a price reason — which
is exactly the case F0 recorded for Astria, and exactly the buyer profile the F3a
invitation targeted.

The 70-85% cost claim is Akash's own marketing figure, so it is treated as a claim,
not a measurement. The $13K/day in fees is also self-reported. But the direction is
corroborated by the 466% deployment growth and the 60% utilization rate: the
marketplace was absorbing real demand, not just reporting a number.

## Source 12 — H100 allocation and the supply constraint, corroborated

The same Akash report independently corroborates the GPU-supply side of the
physical-constraint story (Source 7): NVIDIA H100s stayed allocation-only through
2025 with 6-12 month wait times, and AWS and Azure responded by raising prices and
cutting availability. Combined with the data-center construction delays, the
picture is a supply side constrained on **two independent axes** — hardware
allocation and physical infrastructure — while demand accelerated.

This is the strongest structural argument found for why the empty cell might be
fillable now rather than in the abstract future. It is still not a measurement of
what KOK would sell, and it is still not an excuse to announce anything.

**Status: supply constraint corroborated from a second Akash source. Still not
independently verified against NVIDIA or cloud-provider primary data.**

## Source 13 — Fresh arXiv work in KOK's exact area (18 Sep 2026)

A check of the current cs.CR listing turned up two papers from the last week that
sit directly on KOK's design surface. Both are newer than anything else in this
log.

### arXiv 2609.21728 — Verifiable Computation with TEEs and On-Chain Digital Rights Tokens

Kruger and Georg, submitted 18 Sep 2026 (cs.CR, cs.DC).

The architecture: data owners combine private data into pools inside Trusted
Execution Environments and manage them by issuing **narrowly scoped computational
rights encoded as Digital Rights Tokens (DRTs)**. Each DRT binds specific
open-source code to a pool and is **issued and redeemed on a distributed ledger**.
An analyst gets the right to run that code on the sealed data inside the TEE and
receives the *result*, not the data. A reference implementation runs WASM/Python
jobs over sealed datasets and records redemptions **on Solana**.

This is close enough to KOK's U layer to be worth stating precisely how it
differs, rather than noting it vaguely:

- **KOK's U layer sells verifiable compute with a zkVM proof.** This paper sells
  *permission to execute* on sealed data, with the TEE as the enforcement
  boundary and no SNARK in the path.
- **Their primitive is a rights token, not an escrowed fee.** KOK's task market
  escrows a fee and burns part of it irrecoverably; here the ledger records
  issuance and redemption of a scoped right.
- **What is verifiable in their title is authorisation and provenance, not output
  correctness — confirmed in their own words (full text fetched 2026-09-22).**
  Their §2.4 separates trust into "a platform layer (the TEE and its remote
  attestation) and an authorisation layer (the on-chain rules governing which code
  may run on which pool)." The platform layer is an assumption they state openly:
  "(T1) Hardware: the TEE faithfully executes the loaded image... We accept the
  published adversary model for the underlying TEE family and treat physical
  attacks and microarchitectural side channels as out of scope." Their §2.3
  enforcement is over code identity — the enclave "refuses to run if the hash does
  not match" — and what the ledger records is provenance: "a tamper-evident audit
  trail of who computed what, on which dataset, and under which approved code."
  If the enclave is compromised, that trail is still impeccable and the result is
  still wrong. This is a declared scope, not a defect; it is why the two systems
  are complements rather than substitutes.
- **They have a running reference implementation on Solana.** KOK has F3a, which
  is off-protocol and deliberately not a chain. This is a real deployment
  advantage for them, on a chain that already exists.
- **Their trust assumption is a TEE.** KOK's is a cryptographic proof plus a fraud
  window. The paper's own abstract says it illustrates "the feasibility and
  limitations" of the approach, so the limitations are acknowledged rather than
  hidden.

**What this means for KOK, stated honestly.** It does not compete on consensus —
there is no PoW, no prescribed-hardness layer, the ledger is Solana. It competes
on the *utility* side: someone else has now built and published a working
verifiable-compute-on-a-ledger market, three days ago, with a different trust
root. The "market for computation settled on a chain" is no longer an untested
idea, and the design choice KOK must be able to defend is why a zkVM proof plus
escrow-and-burn beats a TEE plus rights token. That is a real question with a real
answer (TEE attestation is hardware-trusted, KOK's proof is not), but it is now a
question rather than an assumption.

### arXiv 2609.22076 — APort Vault: AI Agent Payment Authorization

Uchi Uchibeke, submitted 18 Sep 2026. This one caused the earlier rejected direction
to be re-examined, and the re-examination found something real.

The benchmark: 4,371 human-written attacks against a live payment agent, collected
during a public capture-the-flag event, replayed across **14 models from 8 labs**,
five policy configurations, two replay tracks, with and without a deterministic
pre-action check implementing the **Open Agent Passport (OAP)** specification.
**225,964 evaluations completed.** The paper reports five distinct events per
evaluation, because "collapsing them is how an agent benchmark produces a number
that does not survive review."

The headline result: at Levels 2 to 4, transfers to recipients the passport did not
permit numbered **140 of 76,842 with the model alone, and 0 of 69,297 behind the
layer**. On matched model/prompt/track triples, 105 against 0. The zero spans 790
source sessions, giving a per-session upper bound of 0.38%. At Level 4, request
rates run 71.2% to 84.3% across the fourteen models, and 809 of 1,293 prompts (62.6%)
elicited a request from all fourteen, each ending in a successful payment to the
level's allowlisted recipient.

**The crucial detail is what the zero did not cost:** it was not obtained by
refusing payments. **25,370 payments executed behind the layer**, while the policy
denied only 187 of the 25,640 transfer calls it evaluated, 148 of them for a
forbidden recipient. The boundary stops unauthorized transfers while letting
legitimate ones through.

**Three bounds on the reading, from the full text (fetched 2026-09-22), stated
because a reinstated direction has to carry its own limits.** The authors scope
their result in §1.3: "It is scoped to payments, to one tool schema, in a simulated
bank. It is not evidence about data exfiltration, code execution, or delegation
between agents." They raise the strongest counter-argument to their own headline in
§6.1: **five of the fourteen models reached zero unpermitted transfers with no layer
at all**, so the layer's value is not that it is the only thing that works but that
it works **independently of which model is chosen** — the property a deployer needs
and cannot get from a model ranking. And the zero is not a zero-width interval: the
session-clustered upper bound is 0.38%, quoted conservatively over the exact
per-evaluation bound of 0.0043%.

What this does and does not establish for KÖK's thesis: it does not establish demand
for a compute market. It establishes that a **deterministic pre-action check at a
tool boundary is a measurable security primitive**, which is the same structural
position KÖK's fraud window occupies for task settlement. The parallel is
architectural, not commercial.

### Why this reopens the direction the log rejected

The AI-agent security gap was rejected on the grounds that CertiK's losses traced to
phishing, deepfakes, and social engineering, a people problem rather than a protocol
gap. **That reasoning still holds for the losses CertiK measured.** But this paper is
evidence of a different thing: a **deterministic protocol-level boundary that makes
agent payment authorization provably contained**, benchmarked against 4,371 real
attacks, with the usability cost measured and near zero.

The distinction is stated carefully: the missing primitive is not "users must be
more careful." It is **a pre-action authorization layer that agents cannot talk
their way past**, with an open specification and a public dataset. That is a
protocol-shaped gap, and someone just benchmarked it.

**What this does not do:** it is not a blockchain. There is no consensus, no ledger,
no token. It is a boundary layer for agents that already have payment access. So it
does not compete with KOK, and it does not by itself justify building a chain. What
it does establish is that **agent payment authorization is a real, measured problem
with a measured solution shape** — directly relevant to the U layer's buyer side,
since the buyers F3a targets are increasingly agents rather than humans, and an agent
that cannot be authorized to pay safely cannot be a customer at all.

**Status: abstract read in full. The OAP specification itself has not been fetched.**

## Source 9 — IEA "Energy and AI" (primary source on the energy constraint)

Fetched from iea.org/reports/energy-and-ai. Published **10 April 2025**, CC BY 4.0.
This is the primary source behind the energy-constraint narrative, and it is a
year older than the Akash post, so it predates the 2026 datacenter-delay reports.

The report's own framing: "There is no AI without energy — specifically electricity
for data centres." It provides global and regional modelling of AI electricity
consumption over the next decade and analyses energy security, emissions, and
affordability.

**Status: located and confirmed as primary. Numbers not yet extracted, and the
April 2025 date means it does not cover the 2026 delays.** It corroborates that
the constraint is structural and internationally recognised, but it cannot
substitute for the Bloomberg 2026 figure, which remains unfetched.

## Source 10 — Bittensor's payment direction, confirmed from its own site

Fetched from bittensor.com (2026-09-21). One line settles open question 2 in the
negative direction:

> "Bittensor is an open network where independent subnets produce digital
> commodities and **the chain pays contributors in TAO**."

The payer is the chain, not an external buyer. This is exactly the "internal
economics" characterisation from the landscape survey, now confirmed from
Bittensor's own front page rather than a biased third party. In Pass's terms,
Bittensor has token rewards but no external inference market paying for output,
which is the T/I ratio pinned by adoption alone rather than by external demand.

**Caveat:** the site is a landing page, not a financial statement, and it does not
rule out external buyers entirely. But the network's stated mechanism is
inflation-funded subsidies to subnet contributors, which is a different thing from
a buyer paying for compute.

## Synthesis — what the thirteen sources say together

The picture that emerges is narrower and more useful than "what is not built."

**Two measured failures define the design space.** Pearl proved that optional
usefulness is skipped at 24 EH/s scale — 320,000 GPUs producing zero AI output
because skipping inference saved 10-30% of hashrate and cost nothing. Akash proved
the mirror failure: when they let tenants pay in USDC, usage grew while the token's
economic role eroded, and they had to retrofit burn-mint to reconnect them. KOK's
U layer is built directly against both, which is no longer a design hypothesis but
an alignment with two documented outcomes.

**The Pass model gives the failure a name and a condition.** The regime is
Bitconia when the token/inference ratio is low, and Duplexia when it is high
enough for block rewards to act as inference rebates. Pass was consulting for
Pearl when he wrote this, so it is Pearl's own theory, and it does not assert that
buyers appear — it says what happens *if* the ratio is high enough. The ratio is
external demand, and external demand is what phi measures. KOK's measurement is
therefore not a side experiment; it is the variable the theory is parameterised on.

**The empty cell is narrower than it first looked, and this log corrected itself.**
The first pass at the landscape claimed nobody had built a computation market
settled on a ledger. That was wrong by three days: **arXiv 2609.21728** (Kruger and
Georg, 18 Sep 2026) has a working reference implementation on Solana, using TEEs
and on-chain digital rights tokens. What remains unoccupied is specifically **PoUW
consensus where useful output is bought by an external party** — the PoUW half,
not the market half. Bittensor pays from inflation, confirmed from its own front
page; the other live PoUW chains publish no revenue and one of them, Dynex, is
cancelling its utility token. The correction is kept in the log rather than edited
away.

**The demand side has one structural signal and one new customer shape.** The
structural signal is physical: centralised AI capacity constrained on two
independent axes — hardware allocation, with H100s allocation-only and 6-12 month
waits, and physical infrastructure, with planned data centers delayed, a state
moratorium, and multi-year turbine lead times. If buyers cannot get centralised
capacity, permissionless supply becomes an alternative rather than a belief. This
is the only ideology-free demand force found, and its primary sources remain
unverified, which is recorded.

The new customer shape is that **the buyer is increasingly an agent.** APort Vault
establishes that agent payment authorization is a real, measured problem — 140 of
76,842 unauthorized transfers without a boundary, 0 of 69,297 with one, while
25,370 legitimate payments still executed. This is not a chain and does not compete
with KOK, but it says the U layer's eventual customer will need safe authorization
to pay at all. KOK's escrow-then-settle structure is already that shape.

**What this changes for KOK, and what it does not.** It strengthens the case that
the problem KOK chose is real and that the design fits the measured failures. It
also removes one claim that was too strong: the market half is no longer novel, and
the design must be defended on the zkVM-versus-TEE question. It does not create
demand. The F3a testnet still measures phi with a real buyer, the Astria invitation
is still the only one sent, and the decision to wait for Demirel stands. The
research supports the path; it does not shorten it.

**What remains genuinely open, and is not papered over:**

1. The "nearly half of data centers delayed" figure is still unfetched at its
   primary source, and the attempt to fetch it (2026-09-22) downgrades it further
   than "unfetched". The Akash blog post was retrieved and read in full: it says
   "According to Bloomberg, nearly half of U.S. data centers planned for 2026 are
   now expected to be delayed or canceled" and gives **no link, no date and no
   author** for that Bloomberg reference. So the figure cannot be traced even from
   the document that cites it. Three routes to the primary source were attempted:
   DuckDuckGo returns a bot challenge, Bing returns irrelevant localised results
   regardless of the query, and Bloomberg itself sits behind a paywall. The
   figure is therefore **not verifiable with the tools available**, and it stays
   quarantined as an unverified secondary claim. The same applies to the IEEE
   Spectrum seven-year gas-turbine wait, the Maine moratorium and the land
   refusals: all are stated in the same self-interested blog without primary
   links. **The structural argument does not depend on this number** — land,
   permitting and energy move on multi-year timescales regardless of whether
   "nearly half" is the right fraction — but the specific figure should not be
   repeated as a measurement.
2. Pass's model assumes an elastic inference market, and the paper states the
   assumption as an assumption, not a measurement. Verbatim from 2606.06700
   (§2, "A simple monetary model"): "We assume throughout that inference demand
   is sufficiently elastic so that total spending pD(p) increases when effective
   inference prices fall (elasticity greater than one), and ignore parameters
   that occur with measure 0." The working parameters are an isoelastic curve
   D(p) = K p^(-ε) with (K, ε) = (571,000, 2), chosen because "ε = 2 corresponds
   to an elastic market in which lower prices unlock new use cases, consistent
   with the Jevons effect," with a sensitivity sweep in §5.3.

   What this means for KOK, stated plainly: the entire Duplexia result — that
   inference output expands when the effective price falls — is conditional on
   ε > 1. The paper is honest about this; it is a modelling assumption, not a
   claim about the world. KOK inherits the condition without testing it. In a
   supply-constrained world (GPU capacity actually saturated, which is the state
   the launch market has been in since 2023) ε can be well below 1 over the
   relevant range, because buyers competing for scarce capacity bid prices up
   without expanding supply. If ε < 1 the mechanism runs the other way:
   subsidising inference raises total spending per unit without expanding
   output, and the Fortessia/Duplexia boundary moves. This remains untested, and
   testing it is a demand-discovery measurement (F0), not a simulation: ask the
   buyers what they would do at a lower price, and whether they are currently
   capacity-constrained or price-constrained.
3. ~~The TEE-versus-zkVM comparison has not been written from KOK's side.~~
   **Written (2026-09-22) and now sourced verbatim.** The full HTML text of
   2609.21728 was fetched and read, and the argument's central claim is confirmed
   in the authors' own words: their §2.4 threat model separates a platform layer
   (TEE + attestation) from an authorisation layer, and the platform layer rests on
   the stated assumption that "the TEE faithfully executes the loaded image," with
   "physical attacks and microarchitectural side channels... out of scope." What
   their ledger records is provenance — "a tamper-evident audit trail of who
   computed what, on which dataset, and under which approved code." So a TEE and a
   zkVM solve different halves of the same buyer's problem: the TEE gives
   confidentiality, the zkVM gives verification of correctness, and KW's Remark 2.2
   adds confidentiality on top of the proof. What remains open is not the argument
   but the delivery: Akash ships the confidentiality half today and KOK's F0b has
   not been written — a statement this file now has to correct, because the code
   was written and the property is absent from it. Probe TV-65 (2026-09-22) shows
   why: F0b's TV-43 masking step derives its mask from a seed the *verifier*
   supplies, so the verifier recomputes the mask and recovers every plaintext it
   was sent. The prototype establishes provenance (soundness without transmitting
   secrets) but not confidentiality, at any scale. The gap to Akash is therefore
   not "KOK has not written the code" but "KOK wrote the code and it does not
   hide."
4. Whether agents can be real buyers of inference at all — not merely authorized to
   pay, but carrying demand a human did not initiate — is an open empirical
   question that no source here answers.

## Verification record (2026-09-22)

The numbers the paper quotes from Basu were checked against the primary source
(arXiv 2606.04819, 16 pages, full PDF read). All four agree exactly:

- kurtosis uniform 1.79 / NN weights 3.33 / adversarial Gaussian 2.97 (§4.5)
- revenue/cost ratio ≈ 1.06, with the cost derivation stated as
  "320K GPUs × $0.20/hr × 24h = $1.54M" (§4.6.2)

The last item is the load-bearing one. `pass_sim_en.py` calibrates the Pearl
network from those same three inputs and prints `cost_day = 1,536,000` with a
5.8% deviation from the measured hashrate. The prototype's input arithmetic is
therefore not an interpretation of Basu — it is Basu's own estimate, reproduced
from the paper's stated quantities. The 5.8% deviation is measured against the
320,000-GPU count, not against a figure the prototype invented.

The corroboration runs the other way too. Basu reads the 1.06 ratio as
"near equilibrium at current prices," which is the same economic state Pass's
model calls the zero-profit condition the solver enforces as a residual of
zero. Two independent papers, written for different purposes, describe the same
network as sitting at the same point. That is the strongest single piece of
external evidence the calibration has, and it is now recorded as such rather
than asserted.
