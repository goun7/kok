Subject: Independent cryptographic review of a KW-based PoUW design — invitation

Dear Dr. Demirel,

I am writing to invite you to review the cryptographic layer of a
proof-of-useful-work design we have been developing, and to ask whether
you would be willing to take it on.

A word on why we are asking you in particular. Our architecture is a
two-layer L1: a KW/cuPOW matrix-multiplication proof secures the chain,
and a separate fee-paid verifiable-compute market carries the utility.
The split is not decorative. It was designed against Theorem 2 of your
"Proof of Demand Is Not Proof of Work" (ePrint 2026/1492), which
requires a leader-election path that does not depend on demand. We would
rather have the person who proved that requirement tell us whether we
actually satisfy it than discover later that we only believed we did. We
also understand you have audited Pearl cuPOW, so you would arrive
already familiar with the production system our design departs from.

What we are asking for is a written review of six questions. Each is set
out with the relevant verbatim quotes from Komargodski and Weinstein and
with our own preliminary answers, so that your effort goes into checking
rather than into reconstructing our reasoning. The questions, the
quotes, the prototypes, and an index locating every claim are collected
in the attached brief. In short: is Assumption 6.4 genuinely needed?
Does our context-binding of sigma preserve Lemma 6.5? Is the per-tile
difficulty balance sound? And is there an attack class we have missed?

One thing we want to disclose rather than leave you to find. Our
economic simulation is built on the model of Pass ("The Economics of
Proof-of-Useful-Work", arXiv 2606.06700), which was written while its
author was consulting for Pearl Research Labs. We do not think this
invalidates the model. We have run it, and it recovers the size of the
live Pearl network to within 5.8 percent from first principles. But it
is a reason to have the model itself reviewed independently, and if you
take this on we would ask that its assumptions be part of what you
examine.

On terms. The review is published whatever its conclusion. If you find
that our core assumption does not hold, we fall back to a pure-PoW mode
that is already specified, and that finding goes on the record.
Compensation is available from the protocol treasury at 5 to 8 percent
of block rewards, milestone-vested; a fixed fee is also fine. Please
treat this as an enquiry and not as a commitment on either side.

I have attached the full package to this message. If you would rather
talk through it first, a call is easy to arrange. Thank you for your
time.

Attachments (all included with this message):
- KOK_V2_CRYPTO_BRIEF.md - the six questions, verbatim quotes, our preliminary results
- KOK_V2_TECHNICAL_SPEC.md - formal specification (Appendix A is the task-market protocol)
- KOK_V2_PAPER.md - the design paper (architecture, economics, competitive analysis)
- KOK_V2_REFERENCES.md - bibliography plus a proof index mapping every claim to its evidence
- g_layer_tests_en.py - Layer G tests: replay rejection, prescribed hardness,
  easy-instance resistance, jackpot policy, retarget (TV-1..TV-21)
- u_layer_prototype_en.py - Layer U tests: escrow, burn, VRF, fraud, slashing (TV-5..TV-10)
- f3a_sequencer_proto_en.py - censorship-resistance tests: refund, migration,
  bond refill (TV-15..TV-20)
- pass_sim_en.py - closed-form solver for the Pass (2026) economic model,
  calibrated on the live Pearl network (reproduces its size within 5.8%)

Best regards,
The KÖK v2 protocol design team
kokprotocol@proton.me
