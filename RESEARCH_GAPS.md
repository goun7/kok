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

Three candidate directions have now been tested:

- **AI agent security gap** — rejected. Losses trace to social engineering and
  cross-chain failures, not a missing protocol primitive.
- **Decentralized compute demand** — confirmed real but small. Akash at $5M
  all-time spend, with physical constraints now limiting centralized supply.
- **PoUW with paying customers** — empty. Nobody in the true-PoUW bucket has one,
  and the marketplaces that do are PoS.

The synthesis so far: KOK's design is aligned with the two failures that have
actually been measured (optional usefulness gets skipped; decoupling token from
usage erodes the token), and it targets the one empty cell in the table — true
PoUW with a paying customer. Whether that cell can be filled is still exactly what
phi measures.

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

Uchi Uchibeke, submitted 21 Sep 2026. Benchmarking AI agent payment authorization
with an "Open Agent Passport." Not yet read in detail. It is listed here because it
sits at the intersection the earlier AI-agent research flagged, and because
*payment authorization for agents* is closer to a real primitive than the
phishing-and-deepfake material that caused that direction to be rejected.

**Status: abstracts read. Neither paper's full text has been examined.**

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

## Synthesis — what the ten sources say together

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

**Nobody occupies the empty cell.** True PoUW systems (Pearl, Bittensor) have no
paying customer; the chain pays miners or contributors. Systems with paying
customers (Akash, Render, io.net) are marketplaces on PoS, where useful work is
not tied to consensus. Gensyn was the strongest training-verification candidate and
has repositioned toward verifiable inference, oracles, and prediction markets. The
specific gap is **PoUW consensus where useful output is bought by an external
party**, and it is unoccupied on every side.

**One external force could create the missing demand.** Physical constraints on
centralised AI are the only demand signal found that requires no ideology: planned
data centers delayed or canceled, a state moratorium, community refusals of
eight-figure land offers, and multi-year lead times on turbines. If buyers cannot
get centralised capacity, permissionless supply becomes an alternative rather than
a belief. This is the strongest argument found for why the empty cell might be
fillable now rather than in some abstract future — and its primary source remains
unverified, which is recorded.

**What this changes for KOK, and what it does not.** It strengthens the case that
the problem KOK chose is real and that the design fits the measured failures. It
does not create demand. The F3a testnet still measures phi with a real buyer, the
Astria invitation is still the only one sent, and the decision to wait for Demirel
stands. The research supports the path; it does not shorten it.
