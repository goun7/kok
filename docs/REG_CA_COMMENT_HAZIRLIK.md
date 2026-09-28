# Reg Crypto Assets — Comment Period Preparation

**NOT A FILED COMMENT.** This is preparation for a decision the project owner has
not made. Nothing here has been submitted anywhere, and nothing will be — the
project's own communication restrictions forbid it. See "Rules for this file" at
the bottom before quoting any of it.

---

## 0. The deadline

| Field | Value |
|---|---|
| Rule | **Regulation Crypto Assets** (proposed) |
| Federal Register citation | **91 FR 54510** |
| Document number | 2026-17183 |
| Docket | Release Nos. **33-11434; 34-106150**; File No. **S7-2026-27** |
| RIN | **3235-AN38** |
| Published | 21 August 2026 |
| **Comments close** | **20 October 2026** — "Comments should be received on or before October 20, 2026" |
| Status as of 28 September 2026 | **Proposed, not adopted. 22 days remain.** |
| Where to comment | `regulations.gov` docket for File No. S7-2026-27 (verify before use) |

**The timer matters because of what a comment can and cannot do.** A comment
filed before 20 October is read by the Commission; a comment filed after is not
part of the rulemaking record. This file is preparation only, and its value
decays to zero on the deadline — the date line above becomes historical on
21 October and must be re-verified from the Federal Register API before any use.

---

## 1. The one question this design cares about: who is the "issuer"?

The proposed rule's safe harbour (Rule 400) and its disclosure mechanics (Form TR)
are written around an **issuer**: a party that made representations, owes
essential managerial efforts, and files a transition report on EDGAR when the
network becomes functional. The entire machinery assumes there is such a party.

**A fair-launch, no-premine, no-entity network has no issuer.** There is no sale,
no representation, no promoter, no one to file Form TR and no one the form could
describe. The network is bootstrapped by mining, and the token's initial
distribution is emission to miners rather than sale to buyers.

**This is a genuine gap in the proposal, not a defect in this design.** The
proposal's own analysis (§II.A.4.b.i) describes the network becoming functional
and value deriving from its **programmatic operation** rather than from the
efforts of an issuer — but the *mechanisms* it provides to mark that transition
all require the issuer to act. A network with no issuer has no agent for the
mechanism.

### Why this is theoretically favourable, not a request for an exception

The question "who files Form TR for a network that had no issuer?" is the natural
consequence of the Commission's own framework, and answering it in the direction
this design sits is *consistent with the proposal's stated logic* rather than
contrary to it. Two readings of a no-issuer network are possible:

- **Reading A (adverse):** no issuer means the safe harbour is simply
  unavailable, and the analysis of "functional network" never applies. This
  leaves such networks in the pre-2026 position, with no on-ramp.
- **Reading B (favourable):** a network that never had an issuer never had a
  covered investment contract to terminate. The §II.A.4.b.i logic — value from
  programmatic operation, not from essential managerial efforts — applies by
  *absence of the premise* rather than by transition. Nothing ceases to exist
  because nothing was created.

**This design advances Reading B, and says plainly that it is an argument, not a
ruling.** The proposal is silent between the two readings, and silence is what a
comment can honestly ask the Commission to resolve. What it must not do is claim
Reading B has been adopted — it has not, the rule is proposed, and a proposed rule
can be withdrawn, narrowed, or rewritten.

### Does PoUW mining count as an "issuer"-like activity? Analysis

This is the sharpest version of the question, and it deserves a direct answer
rather than a rhetorical one.

| Activity in this design | Is it "essential managerial effort"? | Reasoning |
|---|---|---|
| Designing the protocol and publishing the paper | **No, and this is the honest hard case.** | Development is a real effort by identifiable people. But the proposal's own §II.A.4.b.i analysis addresses exactly this: once the network is functional, services to "secure, maintain, improve, or enhance" it are not essential managerial efforts. Development precedes functionality; it is the premise the test operates on, not the thing the test measures. **The honest limit: this argument only holds once the network is functional, and this network is not.** |
| Mining G-layer blocks (the MatMul proof-of-work) | **No — the proposal names this.** | §II.A.4.b.i lists "**validators and/or miners**" among the many parties whose activities affect the network's success, and holds that securing a functional network is not essential managerial effort. This is the closest thing in the proposal to a direct answer about this design's layer G. |
| Running a node, verifying blocks, enforcing consensus | **No** | Same provision: securing and maintaining a functional network. |
| The team operating a task marketplace | **Yes, potentially — and this is the asymmetry the design must respect.** | If the project operates the U-layer marketplace as a business, that is a service performed by an identified party, and the proposal treats ongoing services to a network differently from securing it. **This is why the design separates protocol from application** (paper §9): the protocol is open source; the marketplace, if one is ever run, is a separate entity subject to ordinary business regulation. |
| Making promises about future value | **Yes, categorically.** | Any representation that the token will appreciate, or that efforts will continue, is the core Howey fact pattern. This design makes none, and the absence is a design feature, not a coincidence. |

**The conclusion of this analysis, stated as a claim and as its limit.** The
claim: mining and consensus participation in a functional network are, by the
proposal's own text, not essential managerial efforts, so a fair-launch token
distributed by mining sits closer to the proposal's commodity framing than a
sale-funded token does. The limit: this network is **not functional**, the paper
is a pre-testnet design document, and "functional" is a status only a live chain
can claim. The analysis is a design argument about a future state, and it says so.

---

## 2. Draft comment (English)

**What this draft is.** A comment the project *could* file. It has not been filed.
It is written to be usable as a starting point: the asks are narrow, the
reasoning is the proposal's own, and no claim is made that exceeds the text. If
the owner decides to file, it should be read by counsel first — this is a
design document, not a legal document, and the project has no lawyer.

**Tone chosen deliberately.** The Commission receives comments that demand, and
comments that ask. This draft asks, because the asks are genuinely open questions
in the proposal rather than grievances about it, and because a comment from a
pre-testnet project claiming it already knows the answer would be less credible
than one identifying a gap the Commission's own framework created.

---

> **Re: Regulation Crypto Assets, File No. S7-2026-27, RIN 3235-AN38**
> *(Comment draft — NOT FILED. Prepared 28 September 2026.)*
>
> The Commission's proposal addresses a question this project has spent
> considerable time on: how the Howey analysis treats a crypto asset whose
> network is functional, and where its value comes from. We write not to
> object but to identify a gap the proposal's own framework creates, and to
> ask the Commission to address it.
>
> We design a proof-of-useful-work layer-1. Its distinguishing structural
> choice is that **no party ever offered the asset for sale**. The asset is
> distributed by mining from genesis, with no premine, no investor round, and
> no entity that collected capital against promises of effort. The network's
> security budget comes from mining alone.
>
> The proposal's §II.A.4.b.i analysis holds that once a network is functional,
> services to "secure, maintain, improve, or enhance" it "would not constitute
> essential managerial efforts," and that the asset "should derive its value
> from the programmatic operation of the associated crypto network," with
> "validators and/or miners" named among the parties whose activities affect
> its success. We share that analysis, and our architecture is built to satisfy
> it: our consensus participants perform exactly the securing and maintaining
> the analysis describes, and nothing else.
>
> **The gap.** The mechanisms the proposal provides to mark the point at which
> a network becomes functional — Rule 400's cessation of a covered investment
> contract, and the Form TR filing in Rule 400(b) — are each performed by an
> **issuer**. A network that distributed its asset solely by mining has no
> issuer: no party made a representation, no party owes essential managerial
> efforts, and no party exists to file a transition report. The proposal does
> not address whether such a network is outside the framework entirely, or
> inside it with nothing to terminate.
>
> We ask the Commission to consider two questions, and we offer no answer to
> either:
>
> 1. Where a crypto network has no issuer because its asset was never sold —
>    only mined — does the Commission regard the network as outside the
>    framework the proposal establishes, or as a network in which no covered
>    investment contract ever arose, such that there is nothing to which
>    cessation could apply?
>
> 2. If the latter, would the Commission consider stating, in the adopting
>    release or in guidance, that the absence of a sale is a fact bearing on
>    the Howey analysis in the same direction the proposal already recognises
>    for functional networks — rather than leaving no-issuer networks to infer
>    it?
>
> We raise this because the omission is not hypothetical for our design, and
> because we believe it is resolvable within the proposal's own logic. We do
> **not** ask the Commission to adopt any particular position on our asset, to
> treat this comment as a ruling, or to exempt proof-of-work distribution from
> the analysis the proposal applies to all crypto assets. The distinction we
> draw is structural — the absence of a sale — not technological, and it is
> available to any network with the same structure regardless of its work
> function.
>
> Two limits we state plainly. First, our network is **not yet
> functional**; it is a pre-testnet design with a specification and prototypes.
> The "functional network" analysis we reference is one we aspire to satisfy
> and cannot yet claim to. Second, this comment is submitted by the project's
> designers, not by counsel; the legal question is one we have identified but
> are not competent to answer.

---

**Three things the draft deliberately does not do**, and the reason each matters:

1. **It does not claim the safe harbour applies to this design.** It cannot: Rule
   400 terminates a contract, and this design's thesis is that no contract
   existed. Claiming the harbour would contradict the design's own position.
2. **It does not argue that PoUW is legally special.** The distinction drawn is
   *no sale*, which any mining-distributed asset shares. Making the argument
   technological would narrow it to this project and weaken it.
3. **It does not ask for an exemption.** It asks for a *statement*. An exemption
   for one project is a corrupting ask; a clarification of the framework is a
   legitimate one, and it is the ask the gap actually supports.

---

## 3. The arithmetic of the window

**22 days remain as of 28 September 2026.** What each of them is for:

| Days | What happens | Who does it |
|---|---|---|
| 1–7 (to ~5 Oct) | Read the draft, decide whether to comment **at all**. The decision is whether the project wants its design associated with a public regulatory position while pre-testnet — this is a strategic question, not a drafting one | **Human decision. Not delegable.** |
| 8–14 (to ~12 Oct) | If yes: counsel review. The project has no lawyer (Stage 4 §4.2), so this means *finding* one for a narrow reading of a short comment, which is a different and cheaper engagement than a full securities opinion | Human + counsel |
| 15–20 (to ~19 Oct) | Revise, verify the docket path on regulations.gov is correct and the comment will land in the right file, file | Human |
| 21–22 (20 Oct) | **The deadline.** "Received on or before" means filed, not drafted, by close of business | — |

**The one decision that is genuinely a decision.** Filing puts the design on the
public record as having taken a regulatory position. It costs nothing in money
and it cannot be retracted. The project's current posture — citing the proposal
in the paper as corroboration without participating in the rulemaking — is a
legitimate choice and requires no justification. Filing is also legitimate. The
draft above exists so that whichever is chosen, the work is already done and the
clock is the only constraint.

---

## 4. What the paper already says (do not contradict it)

If a comment is filed, it must not assert anything the paper does not support.
The paper's position, which the comment draft above is consistent with:

- §9.2: the proposal's analysis describes this architecture, arrived at
  **independently** — corroboration, **not** confirmation. The paper does not
  claim the rule was written about this design.
- §9.2, weakening 1: **this chain cannot *use* the safe harbour.** Rule 400
  codifies cessation; this design's thesis is that there was never a contract.
- §9.2, weakening 2: **there is no issuer to file Form TR.** Recorded as an
  unresolved gap in the proposal, not a defect in this design.
- §9.2, weakening 3: **"functional" is a status this design cannot yet claim.**
- §9.3 item 3: the "issuer" clarification is the one live question, and the
  comment period running to 20 October 2026 is what makes it live.
- §9.3: no counsel has been engaged. Every legal reading in the project is a
  reading by non-lawyers.

The draft comment repeats each of these limits in its own words. If any of them
is changed, the comment must change with it — a comment that softened the
"cannot use the safe harbour" admission would be inconsistent with the paper's
recorded position, and a reader who found both would reasonably ask why.

---

## 5. Rules for this file

- **Nothing here is filed, and nothing will be filed without the project owner's
  explicit decision.** The project's standing communication restrictions apply.
- **Not legal advice.** This project has no counsel. The analysis in §1 is
  design analysis by the project's authors; the draft in §2 is a drafting
  exercise. Either becomes something else only after a lawyer reads it.
- **Verify the deadline before use.** The 20 October 2026 close date came from
  the Federal Register's own API (`/api/v1/documents/2026-17183.json`; the HTML
  page gives a bot challenge). After that date passes, every "open" statement in
  this file is historical. Re-verify from the API, not from this file.
- **Do not quote the §II.A.4.b.i language from this file.** The verbatim
  quotations live in `KOK_V2_PAPER.md` §9.2 and in
  `arastirma/federal_register_yorum_analizi.md` with their provenance recorded.
  Quote from there, where the source is attached.
- **The score is not moved by this file.** No code, no test, no measurement and
  no paper claim changed because of it. It is preparation for a human decision,
  and the honest version of preparation is that it proves nothing.
