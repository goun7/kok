#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 — F0 DEMAND-DISCOVERY SCRIPT (a working tool, not a prototype)

This is the roadmap's new first phase, made concrete. TV-35/36/37 established
that the project lives or dies on ONE customer with ONE job. This file is the
instrument that goes looking for that customer -- and, just as importantly, it
is the thing that records a negative result honestly.

It does not simulate demand. It STRUCTURES the search for it.

What it does:
  1. Scores a candidate customer against the two reasons anyone actually buys
     (cheaper for an existing job / only place the job can run).
  2. Computes, for that customer's real workload, whether KOK's cross-subsidy
     can underbid their current provider -- using the crossover from TV-37.
  3. Writes the interview result to a log that cannot be retroactively
     "improved": either a signed letter of intent exists or it does not.

Run:  python3 f0_demand_discovery.py
"""

import json
import os
from datetime import date

LOG_FILE = "f0_demand_log.jsonl"

# ============================================================================
# The scoring rubric -- the two reasons, turned into questions
# ============================================================================

RUBRIC = {
    "cheaper_for_existing_job": {
        "question": "Do they already PAY for this exact workload today?",
        "weight": 1.0,
        "evidence": "a quoted invoice, a cloud bill, or a signed contract",
    },
    "workload_is_matmul_shaped": {
        "question": "Is the workload MatMul-shaped (inference, simulation, linear algebra)?",
        "weight": 0.8,
        "evidence": "the customer states the kernel, or the job description implies it",
    },
    "permissionlessness_matters": {
        "question": "Is there a reason this job CANNOT run on the incumbent cloud?",
        "weight": 1.0,
        "evidence": "a ToS conflict, a jurisdictional bar, a provenance requirement",
    },
    "decision_maker_reachable": {
        "question": "Can we reach the person who pays the compute bill (not a middleman)?",
        "weight": 0.6,
        "evidence": "a named contact and a confirmed conversation",
    },
    "switching_cost_is_low": {
        "question": "Is the workload portable (containerised, no data residency lock-in)?",
        "weight": 0.5,
        "evidence": "they describe the job as a batch or an API call",
    },
}


def score_candidate(answers: dict) -> tuple:
    """answers: {criterion_key: True/False/None}. Returns (score, verdict)."""
    score = 0.0
    evidence_missing = []
    for key, spec in RUBRIC.items():
        a = answers.get(key)
        if a is True:
            score += spec["weight"]
        elif a is None:
            evidence_missing.append(key)
    # the two load-bearing criteria: without at least one, there is no deal
    has_reason = (answers.get("cheaper_for_existing_job") is True
                  or answers.get("permissionlessness_matters") is True)
    if not has_reason:
        return score, "REJECT: neither of the two real buying reasons applies"
    if evidence_missing:
        return score, "DEFER: promising but evidence missing for " + ", ".join(evidence_missing)
    if score >= 2.0:
        # ROUND-4 FIX, 2026-09-24 (round-4 finding #27): the text asserted
        # "both reasons evidenced", but has_reason requires only ONE of the
        # two load-bearing criteria — the file's own worked example sets
        # permissionlessness_matters=False and still printed "both reasons
        # evidenced". The verdict now names which reasons are evidenced.
        which = []
        if answers.get("cheaper_for_existing_job") is True:
            which.append("cheaper-for-existing-job")
        if answers.get("permissionlessness_matters") is True:
            which.append("permissionlessness-matters")
        return (score,
                "PURSUE: a real candidate, evidenced reason(s): "
                + " + ".join(which))
    return score, "WATCH: a real reason but weak fit -- keep the door open"


# ============================================================================
# The price test -- can KOK actually underbid this customer's provider?
# ============================================================================

def price_is_competitive(current_price_per_Mtoken: float, token_price_usd: float,
                         reward_per_s_KOK: float, flops_per_s: float,
                         flops_per_Mtoken: float = 1e14) -> dict:
    """Given what the customer PAYS today, can the cross-subsidy beat it?

    This is TV-37's crossover applied to one real customer. If the token is
    above the crossover, mining pays better than selling and KOK cannot win on
    price -- the pitch must be reason (b), permissionlessness, or nothing.

    ROUND-4 finding #32 (fixed 2026-09-24): the FLOPs-per-Mtoken was a bare
    1e14 literal with a comment saying '~2*N*T for a 50B model'. A scenario
    constant that drives the whole crossover should be a PARAMETER with the
    scenario named, so a caller with a different model size passes its own
    number instead of editing the source. The default keeps the 50B scenario.
    """
    market_usd_per_FLOP = current_price_per_Mtoken / flops_per_Mtoken
    # ROUND-4 finding #29 (fixed 2026-09-24): flops_per_s == 0 crashed here
    # with ZeroDivisionError. A caller comparing hardware that reports no
    # measured FLOPs is a real input (a device whose rate is not yet
    # measured), and crashing makes it look like a defect in the pricing
    # claim rather than in the caller's datum. The crossover is undefined
    # without a rate, so the honest result states that rather than dividing.
    if flops_per_s <= 0:
        return {
            "customer_pays_per_Mtoken": current_price_per_Mtoken,
            "kmin_crossover_token_price_usd": None,
            "token_price_today_usd": token_price_usd,
            "kok_can_underbid_on_price": None,
            "note": ("the mining rate is %r FLOPs/s, so the crossover is "
                     "undefined and the price comparison CANNOT BE MADE; "
                     "this is a missing datum, not a verdict"
                     % flops_per_s),
        }
    moc_KOK_per_FLOP = reward_per_s_KOK / flops_per_s           # mining opportunity cost
    crossover_usd = market_usd_per_FLOP / moc_KOK_per_FLOP
    return {
        "customer_pays_per_Mtoken": current_price_per_Mtoken,
        "kmin_crossover_token_price_usd": crossover_usd,
        "token_price_today_usd": token_price_usd,
        "kok_can_underbid_on_price": token_price_usd < crossover_usd,
        "note": ("mining pays less than the customer's price, so the utility "
                 "layer is price-competitive" if token_price_usd < crossover_usd else
                 "mining pays better than this customer's price, so KOK cannot "
                 "win on price -- the pitch must be permissionlessness"),
    }


# ============================================================================
# The honest log -- an append-only record of the search
# ============================================================================

def log_result(candidate: str, score: float, verdict: str, price: dict,
               letter_of_intent: bool, note: str):
    """Append one interview result. The log is the evidence; it is not edited."""
    entry = {
        "date": str(date.today()),
        "candidate": candidate,
        "score": score,
        "verdict": verdict,
        "letter_of_intent_signed": letter_of_intent,
        "price_analysis": price,
        "note": note,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def log_status():
    """The honest summary: how many candidates, how many signed.

    ROUND-4 FIX, 2026-09-24 (round-4 finding #28): every run of this file
    appends an EXAMPLE-ILLUSTRATIVE row to the log, and log_status counted
    those rows as interviews — so the "honest log" measured how many times
    the file was RUN, not how many candidates were contacted. The worked
    example is now counted separately and never as an interview, so the
    interview count is the count of real outreach rows only.
    """
    if not os.path.exists(LOG_FILE):
        return {"interviews": 0, "signed": 0, "status": "NOT STARTED"}
    rows = []
    for l in open(LOG_FILE, encoding="utf-8"):
        l = l.strip()
        if not l:
            continue
        try:
            rows.append(json.loads(l))
        except json.JSONDecodeError:
            # ROUND-4 (round-4 finding #30): a corrupt line used to crash the
            # whole status read. The log is the project's evidence record; it
            # must tolerate a malformed line and report it rather than abort.
            rows.append({"_corrupt": l[:80]})
    real = [r for r in rows
            if "EXAMPLE-ILLUSTRATIVE" not in str(r.get("candidate", ""))
            and not r.get("_corrupt")]
    corrupt = sum(1 for r in rows if r.get("_corrupt"))
    signed = sum(1 for r in real if r.get("letter_of_intent_signed"))
    out = {
        "interviews": len(real),
        "worked_examples_in_log": len(rows) - len(real) - corrupt,
        "signed": signed,
        "status": ("F0 COMPLETE" if signed >= 1 else
                   "F0 NOT STARTED -- no real outreach recorded yet"
                   if not real else
                   "F0 IN PROGRESS -- no signed letter of intent yet"),
    }
    if corrupt:
        out["corrupt_lines_skipped"] = corrupt
    return out


# ============================================================================
# A worked example -- the shape of a real candidate, not a claim about one
# ============================================================================

if __name__ == "__main__":
    print("=" * 76)
    print("KOK v2 — F0 DEMAND DISCOVERY (the roadmap's first phase, as a tool)")
    print("=" * 76)
    print("TV-37 said the project needs one customer with one job. This tool")
    print("finds that customer and records the search honestly.\n")

    # --- a WORKED EXAMPLE scored against the rubric (labelled as an example) ---
    example_answers = {
        "cheaper_for_existing_job": True,
        "workload_is_matmul_shaped": True,
        "permissionlessness_matters": False,
        "decision_maker_reachable": True,
        "switching_cost_is_low": True,
    }
    score, verdict = score_candidate(example_answers)
    print(f"  Worked example (illustrative, not a real lead):")
    print(f"    score {score:.1f}/3.9  ->  {verdict}")

    # --- the price test for that example, at the spec's own parameters ---
    R0 = 50.0
    BPS = 10.0
    flops = 1e17
    price = price_is_competitive(
        current_price_per_Mtoken=4.00,          # SCENARIO: the customer's real bill
        token_price_usd=0.10,                   # SCENARIO
        reward_per_s_KOK=R0 * BPS,
        flops_per_s=flops,
    )
    print(f"\n  Price test (crossover from TV-37, applied to one customer):")
    for k, v in price.items():
        print(f"    {k}: {v}")

    # --- record it in the log so the example is not mistaken for a lead ---
    log_result("EXAMPLE-ILLUSTRATIVE (not a real lead)", score, verdict, price,
               letter_of_intent=False,
               note="seeded by the tool itself to demonstrate the format; delete before use")
    st = log_status()
    print(f"\n  Log status: {st}")

    print("\n" + "-" * 76)
    print("HOW TO USE THIS (the part that is not code):")
    print("-" * 76)
    print("""  1. Find 10 parties who already pay for MatMul-shaped compute. Not
     investors, not 'partners', not people who like the idea -- people with
     a compute bill. Ask what they pay, per token or per GPU-hour.
  2. Score each with score_candidate(). The rubric is deliberately blunt:
     if neither 'cheaper for an existing job' nor 'cannot run elsewhere'
     is true, there is no deal and the tool says REJECT.
  3. Run price_is_competitive() with THEIR real numbers. If the token is
     above the crossover, price cannot win and the pitch must be (b).
  4. Log every result, including the failures. The F0 criterion is not
     'we feel good about it'; it is one signed letter of intent. The log
     is the only honest record of whether that exists.
  5. If 10 interviews produce zero letters of intent, that is the kill
     signal from section 11b -- not a reason to try harder on the
     cryptography, which cannot fix a market that is not there.""")

    print("\n" + "-" * 76)
    print("ZERO-BUDGET MODE (2026-09-21) — the constraint that rewrites the plan")
    print("-" * 76)
    print("""  The project has no money for the expensive parts. That is not a problem
  for F0, because the two halves of demand discovery cost opposite amounts:

    contact + conversations      $0     <- we can do this today
    delivery after a YES         $50k+  <- audit, mainnet, infrastructure

  The danger is therefore not spending money on outreach. It is getting a YES
  and then over-promising delivery we cannot fund. One email that promises a
  working zk-AIR mainnet to a company handling medical data, backed by no
  audit and no capital, destroys the project's credibility in one step. That
  is the mirror image of Pearl's failure: marketed a capability, could not
  deliver the work.

  THE ZERO-BUDGET PATH (every step free until a grant pays for the rest):

    1. Contact: ask 'we are building this, would you use it?' — never 'we
       will serve you'. The question measures demand; it does not sell.
    2. Letter of intent: free to sign. Its purpose is not a deal; it is
       EVIDENCE for the next step.
    3. Grant applications: Akash grants, the Aethir $100M ecosystem fund,
       Ethereum Foundation grants. Applying is free. A signed LOI is exactly
       what these programmes fund, and the grant — not our capital — pays for
       the audit and the testnet.
    4. Intermediaries do the selling, not the protocol. Akash does not sell to
       its own case-study customers; providers with GPUs and sales teams do.
       KOK publishes the market, providers serve it. A permissionless chain
       cannot have a sales function without ceasing to be permissionless.

  THE HARD QUESTION TO KEEP ASKING: if a buyer says yes, can we hand them
  unaudited cryptographic code and let it touch medical records? Today the
  answer is no, because F0b is a toy AIR. So no promise may be made until
  F0b exists AND is audited — and the audit is what the LOI buys.

  WHAT STAYS TRUE IF ALL OF IT FAILS: a filled log with zero letters is the
  correct negative result and the kill criterion of section 11b applies —
  fall back to the specified pure-PoW mode rather than marketing a capability
  that cannot be delivered.""")
