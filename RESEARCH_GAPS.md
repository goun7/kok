# Research log — what is not yet built (started 2026-09-21)

Purpose: while KÖK waits on Astria and Demirel, investigate path B and the wider
question of what system is actually needed, using current sources rather than
intuition. KÖK stays on path A; this is separate and does not commit to anything.

Method carried over from F0: every claim sourced, intent marked UNKNOWN where not
stated, and nothing presented as a measurement that was not measured.

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

## Next steps for this log

1. Read the Pass theorems, particularly §2.8 on the cost of 50% attacks and
   §1.8 "Availability of Useful Work" — the section that speaks most directly to
   whether demand appears on its own.
2. Get real usage figures for decentralised compute. Akash stats are JS-rendered;
   try their blog, a third-party dashboard, or Messari-style reporting. This is
   the reference point KOK's phi needs to be compared against.
3. Global context: energy constraints, GPU supply, AI capex. The demand side of
   PoUW depends on these, and the Pass model assumes an inference market exists
   and is elastic.
