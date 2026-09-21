# F3a measurement invitation — quiet, buyer-side (draft, 2026-09-21)

NOT an announcement. A targeted invitation to the scarce side of the market.

## The strategy in one line

Pearl's 24 EH/s arrived for free and measured zero buyers. Supply is abundant;
demand is the scarcity. So this reaches **buyers**, not miners, and it
**invites them to a measurement** rather than claiming a capability.

## What we may say, and what we may not

| Say | Do not say |
|---|---|
| We are running an economics testnet to measure whether anyone pays for useful compute | We solved useful proof-of-work |
| The mechanism is proven at prototype scale (11 test vectors, all passing) | Useful compute will be sold |
| The meter is honest: only settled tasks count | We know φ > 0 |
| A censored task cannot inflate the count | We have demand |

The distinction is the whole point. "We built useful PoW" is the sentence Pearl
said and then measured zero against. "We are measuring whether useful compute
gets bought, and you can be the one who decides it" is a different sentence,
and it happens to be true.

## Who gets it, and why them

From the F0 candidate list (all sources live-fetched 2026-09-21):

**Astria** — AI image workloads on Akash. Image generation is MatMul-shaped
(diffusion is repeated MatMul), and their case study shows they already buy
decentralised compute for a cost reason. Best pure workload fit. The invitation
below is written for them.

**Flashback Labs is deliberately NOT contacted with this.** A separate TEE email
was already sent to them from a personal account, and that conversation is open.
Sending a second, parallel pitch about a testnet would look like working through
a checklist rather than talking to them. If that conversation moves, the testnet
comes up inside it.

Sigea (storage) and Passage (UE5 rendering) are also **not** contacted: the U
layer proves MatMul, not storage or rasterisation. The filter rejects them even
though their cost stories are strong. That discipline is what keeps the
measurement honest.

So the list is one party for now. If Astria does not reply, the list is empty, and
that is information too.

## The invitation itself

Two versions exist. The first is addressed to Alon Burg by name and is the one
to use if a personal address is ever obtained. The second is written for a shared
inbox, because that is what is actually reachable.

### Version A - to a personal address (preferred, not currently available)

Subject: A testnet that measures whether anyone pays for useful compute

---

Alon,

I read your Akash case study and one detail stuck: you kept high-spend API
customers by being able to give them better prices for volume.

I am building a useful-proof-of-work protocol and I am about to run the economics
testnet for it. I need a couple of compute buyers to take part. Since Astria
moved providers for a price reason, it is the kind of buyer the measurement
actually needs.

What I am unsure about is not the cryptography, which is being reviewed. It is
whether anyone will pay for compute through a permissionless market. Pearl ran a
24 EH/s useful-proof-of-work network and measured zero useful compute sold. I
would rather find out whether that number is mine before building a mainnet, not
after.

The testnet measures one number: of the tasks submitted, how many are paid for
and settled. Settled tasks count. Censored or refunded ones do not. I publish the
number, whatever it is.

Your side is fine-tuning, inference and upscaling on H100s and H200s, all MatMul,
so it fits the mechanism directly. For you the compute is free during the test.
What I get out of it is a task somebody actually wanted, run through the
mechanism, so the number means something.

If you have a job you would otherwise put on a cloud GPU, that is the task.

Tokens are test tokens. There is no sale and nothing to buy. The code and the
test vectors are public.

---

### Version B - to the support inbox (the reachable address)

This version is deliberately shorter and does not address Alon by name, because a
shared inbox should not look like it was routed around the front door. It is
written so that whoever reads it can decide whether it is worth forwarding.

Subject: A testnet that measures whether anyone pays for useful compute

---

Hi,

I run a useful-proof-of-work protocol and I am about to start its economics
testnet. I am looking for a small number of compute buyers to take part, and
Astria came up as a candidate because of the Akash case study, where pricing was
the reason for the move.

The short version: I do not know whether anyone will pay for compute through a
permissionless market. Pearl ran a 24 EH/s useful-proof-of-work network and
measured zero useful compute sold, and I would rather find out whether that number
is mine before building a mainnet. The testnet measures one thing, how many
submitted tasks are actually paid for and settled, and the number gets published
whatever it is.

Fine-tuning, inference and upscaling are all MatMul, so the workload fits. For a
buyer the compute is free during the test; what I need in return is a task
somebody actually wanted, so the measurement means something.

If this should reach the person who decides on infrastructure, that would be Alon
or a co-founder.

Tokens are test tokens. There is no sale and nothing to buy. The code and the
test vectors are public.

---

## What changed in the rewrite, and why

The earlier draft read as AI-written and has been rewritten in a first-person
voice. "The honest version of what it is" is the hedge an AI uses to sound
candid; "we are looking for a small number of compute buyers" is formulaic
politeness; the parallel "What a buyer gets / What we get" is balanced
construction, an AI signature. All replaced.

The case study supplied two things worth using. Alon Burg is the co-founder who
said "pricing is great, infrastructure is great", and the mail opens on the
detail that is actually his: that Akash pricing let Astria keep high-spend API
customers who demand better prices for volume. A buyer who switched providers for
a price reason is exactly who a demand measurement needs.

The workload line is specific rather than generic: fine-tuning, inference and
upscaling on H100s and H200s, not "image generation". That is the actual pipeline
the case study describes.

## What is verified and what is not

- `astria.ai` is the company in the Akash case study. Confirmed by fetching the
  case study, which names Astria, generative image for fashion e-commerce and AI
  headshots, H100s and H200s, and the switch from Lambda Labs, AWS and RunPod.
- Alon Burg is a co-founder and the source of the quote. Confirmed in the case
  study text.
- Alon Burg's personal email address is **not found**. LinkedIn shows the profile
  but hides the address. No guess is made.
- `support@astria.ai` is a real address: the domain's mail exchangers are
  Google's, so mail to it is delivered to a real inbox rather than bouncing.

## What not to read into silence

A non-reply from a support inbox is not the measurement. It is more likely to
mean the mail never reached a decision-maker than that a buyer declined. If
Version B gets no response in about two weeks, that is evidence about the channel,
not about demand. Do not record it as Pearl's zero.

---

## Three rules for this, written down so we hold to them

1. **No launch language.** This is an invitation to an experiment, not a product
   launch, a mainnet, or a token event. MiCA already forbids the sale; we have no
   reason to imply one exists.

2. **No claim ahead of the measurement.** Every sentence must survive being read
   after the number is published. If φ comes back zero, nothing we wrote becomes
   false.

3. **The number is published either way.** A zero is a result, and it is the one
   Pearl should have published. If we are not willing to publish a zero, we are
   not running a measurement, we are running a marketing campaign.

## Why this is safe before the cryptographer replies

A quiet invitation to named parties is not a public claim about the protocol's
soundness. Nothing in it asserts the G layer is correct, only that the economics
are being measured. When the review lands, the review and the measurement are
two different findings about two different layers, and neither has to wait for
the other.

## The failure mode this is built to avoid

Announcing loudly, attracting miners (the abundant side), shipping a mainnet,
and then measuring zero — Pearl's path, at our cost. Every choice above exists
to not walk it: buyer-side, quiet, measurement-framed, zero-publishable.



Alon,

I read your Akash case study and one detail stuck: you kept high-spend API customers by being able to give them better prices for volume.

I am building a useful-proof-of-work protocol and I am about to run the economics testnet for it. I need a couple of compute buyers to take part. Since Astria moved providers for a price reason, it is the kind of buyer the measurement actually needs.

What I am unsure about is not the cryptography, which is being reviewed. It is whether anyone will pay for compute through a permissionless market. Pearl ran a 24 EH/s useful-proof-of-work network and measured zero useful compute sold. I would rather find out whether that number is mine before building a mainnet, not after.

The testnet measures one number: of the tasks submitted, how many are paid for and settled. Settled tasks count. Censored or refunded ones do not. I publish the number, whatever it is.

Your side is fine-tuning, inference and upscaling on H100s and H200s, all MatMul, so it fits the mechanism directly. For you the compute is free during the test. What I get out of it is a task somebody actually wanted, run through the mechanism, so the number means something.

If you have a job you would otherwise put on a cloud GPU, that is the task.

Tokens are test tokens. There is no sale and nothing to buy. The code and the test vectors are public.
