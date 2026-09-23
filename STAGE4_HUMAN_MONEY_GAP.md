# Stage 4 — the human and money gap (recorded, not performed)

**What this file is.** Stages 1–3 of the build were code and measurement, and
they are done. Stage 4 is the part that cannot be closed by writing more code:
it requires a person whose name is at stake, or a buyer whose money is at
stake. This file records what remains, what it costs, and why it is not
circular — so that the gap is stated rather than optimistically framed.

This file is itself the Stage 4 deliverable: an honest record. It does not
attempt to close what it lists.

---

## 4.1 External cryptographic review — CLOSED AS UNAFFORDABLE, not as unnecessary

**Status:** declined, priced, and recorded. Not deferred.

Demirel replied on 2026-09-23 and declined at **$215/hour**, with two
conditions: payment on an agreed schedule **independent of future funding**,
and **independent of the findings**.

Both conditions are correct on their own terms. They are also incompatible with
this project's position:

- A fee that cannot wait for funding cannot be paid before funding exists.
- A review whose payment depends on its findings is not the *independent* review
  the paper was asking for — the whole point of the request was a signature that
  could not be bought.

**The circularity, now stated rather than made.** An earlier version of this
project's plan deferred external review "until after funding." That is
circular: the funding is being sought partly on the strength of the security
claims, and the security claims are the thing the review would certify. This
file records the circle instead of walking it. The revised paper no longer
makes the deferral argument (§12.3, corrected 2026-09-23).

**What the gap costs the claims.** Everything in Stages 1–3 is self-reviewed:
found by adversarial probing against our own code, by the same author class.
That is real evidence about the *algebra's clarity* and about the *prototype's
behaviour*, and it is not nothing — 60+ bugs were found and fixed this way. It
is not evidence that a second party staked its name on the result. TV-74's
caveat is the honest version of this: an independent reimplementation by the
same author class is spec-clarity evidence about the algebra, not security
evidence, and the cross-check is algebraic, not byte-level.

**Why this is recorded as a finding and not a task.** The user's decision is
recorded verbatim in `EPOSTA_SOK.md`: the fee is more than the project's time
is worth at the margin, and payment independent of future funding makes the
engagement circular with the paper's own deferral plan. This is a real
outside-world block — "was not done," not "cannot be done."

---

## 4.2 Legal review — NOT PERFORMED

**Status:** not started, not priced, not misrepresented.

The paper's legal section (§11) cites four primary sources, all four verified
against the primary docket or release rather than a secondary summary:

| Claim | Source | Verified |
|---|---|---|
| SEC v. NVIDIA, expert-reports dispute | SDNY 1:20-cv-10832, docket 19857399, docs 874/973/989 | docket text |
| Appeal of that ruling | 2d Cir. 24-2648, 24-2705, docket 69230851 | docket text |
| Climate-disclosure rule rescission | 91 FR 13714 | Federal Register |
| The two 2025 releases | SEC Releases 33-11412, 34-105020 | release text |

**What is missing and cannot be substituted.** Verification that a citation is
real is not the same as legal advice. Whether the protocol's own structure — a
fee-burning useful-work market, an escrowed task layer — attracts any particular
regulatory treatment is a question for counsel, and no amount of docket
reading answers it. This is recorded as **not performed**. The paper does not
claim otherwise.

---

## 4.3 A live network of paying buyers — NOT STARTED (F3a/F3b)

**Status:** forbidden by the current constraints, and unstarted.

The paper's φ=0 measurement (TV-72) is a *live* measurement of a real network's
behaviour, reproduced from Pearl's published parameters to within 5.8%. Its
cause was the E-gap: nothing certified the matrices were anyone's job. Stage 2
built the missing binding and measured it in the prototype (TV-77, 4/4).

**What Stage 2 does not claim.** It does not claim φ > 0, because no prototype
can. φ is a property of a live network of paying buyers. The correct statement
is that the mechanism whose absence caused the measured φ=0 now exists and is
measured in the prototype; the economic consequence remains a prediction.

**Why this is not started here.** A real task market against paying buyers is
F3a; a real F3a testnet is F3b. Both are out of scope by explicit constraint.
This file does not attempt them and does not claim progress toward them.

---

## 4.4 The honest summary of what Stage 4 changed

Nothing was built. Three things were corrected in the prose so that the prose
no longer contradicts the recorded position:

1. The paper no longer implies external review is merely deferred. The price,
   the conditions, and the incompatibility are stated (§12.3).
2. The paper no longer describes the greedy mergeset as an open F3b deviation.
   It was measured at 572, closed to 0 in Stage 1.1, and the probe that guarded
   it was inverted so the number cannot quietly return.
3. This file exists so that "not done" is a recorded fact with a cost attached,
   rather than an omission. The score's remaining external-world gap is
   quantified in `DEGERLENDIRME_100.md` and is deliberately not reduced by any
   of the Stage 1–3 work, because none of that work was performed by a party
   whose name or money was at stake.

---

## What is deliberately NOT in this file

- No request for funding, and no investor-facing language.
- No claim that Stages 1–3 substitute for 4.1, 4.2, or 4.3.
- No new features, protocols, or constructions.
- No claim that the gap is smaller than it is. The score is held, not raised.
