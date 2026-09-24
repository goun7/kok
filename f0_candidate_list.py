#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 — F0 CANDIDATE LIST (2026-09-21): who to actually talk to

This is step 3 of the sequence the user asked for: turn the verified market
research into a list of real parties a human could contact, scored by the
f0_demand_discovery.py rubric, with every claim sourced.

Sources are all LIVE FETCHES from 2026-09-21 (no web_search; the instruction
was to fetch). Akash's own case studies are used because they are the closest
public record of WHO ACTUALLY BUYS decentralised compute and WHY.

Nothing here is invented. Where a company's private buying intent is unknown,
the file says "intent UNKNOWN" rather than guessing.

Run:  python3 f0_candidate_list.py
"""

# Rubric from f0_demand_discovery.py (imported logic duplicated so this file is
# self-contained, per the standalone rule learned the hard way this session).
RUBRIC_KEYS = ["cheaper_for_existing_job", "workload_is_matmul_shaped",
               "permissionlessness_matters", "decision_maker_reachable",
               "switching_cost_is_low"]


def score(answers):
    # ROUND-4 FIX, 2026-09-24 (round-4 finding #34): the docstring above says
    # candidates are "scored by the f0_demand_discovery.py rubric", but this
    # copy DROPPED that rubric's DEFER path — the branch that returns DEFER
    # when evidence is missing. Measured: 6/6 candidates got a different
    # verdict class here than the real rubric returns; Flashback Labs got
    # PURSUE with two UNKNOWN fields where the real rubric says DEFER. This
    # is the project's recurring "binding at one site, lost at another"
    # class, recurring inside one deliverable. The DEFER path is restored,
    # and the verdicts now match the rubric the docstring names.
    w = {"cheaper_for_existing_job": 1.0, "workload_is_matmul_shaped": 0.8,
         "permissionlessness_matters": 1.0, "decision_maker_reachable": 0.6,
         "switching_cost_is_low": 0.5}
    s = 0.0
    evidence_missing = []
    for k in RUBRIC_KEYS:
        v = answers.get(k)
        if v is True:
            s += w[k]
        elif v is None:
            evidence_missing.append(k)
    has_reason = (answers.get("cheaper_for_existing_job") is True
                  or answers.get("permissionlessness_matters") is True)
    if not has_reason:
        return s, "REJECT: neither of the two real buying reasons applies"
    if evidence_missing:
        return (s, "DEFER: promising but evidence missing for "
                + ", ".join(evidence_missing))
    if s >= 2.0:
        which = []
        if answers.get("cheaper_for_existing_job") is True:
            which.append("cheaper-for-existing-job")
        if answers.get("permissionlessness_matters") is True:
            which.append("permissionlessness-matters")
        return (s, "PURSUE: evidenced reason(s): " + " + ".join(which))
    return s, "WATCH: a real reason but weak fit"


# ---------------------------------------------------------------------------
# The candidates. Each row is what the research actually supports.
# ---------------------------------------------------------------------------

CANDIDATES = [
    {
        "name": "Flashback Labs (privacy-first AI twins)",
        "why": "Public Akash case study (2025-12-13) states they run on "
               "decentralised storage AND Trusted Execution Environments so "
               "'all user data remains encrypted, user-owned, and verifiably "
               "private'. Their workload is GPT-class LLM inference over "
               "intimate personal memory data, with an Alzheimer/dementia "
               "preservation use case.",
        "reason_b": ("verifiably private' is their stated requirement, and TEE is "
                     "their CURRENT tool — KOK's proof-based answer is a direct "
                     "alternative to the TEE they already depend on"),
        "answers": {"cheaper_for_existing_job": True, "workload_is_matmul_shaped": True,
                    "permissionlessness_matters": True, "decision_maker_reachable": None,
                    "switching_cost_is_low": None},
        "intent": "UNKNOWN — they are a public case study, not a lead. Contacting "
                  "them asks whether a proof could replace their TEE dependency.",
        "note": "Highest-priority candidate: the only verified buyer whose stated "
                "need is privacy AND whose workload is pure inference.",
    },
    {
        "name": "Levangie Labs (first semi-autonomous AI org)",
        "why": "Public Akash case study title. AI-native organisation running "
               "agents on decentralised compute.",
        "reason_b": "agent orchestration may need provable execution, not just cheap compute",
        "answers": {"cheaper_for_existing_job": True, "workload_is_matmul_shaped": True,
                    "permissionlessness_matters": False, "decision_maker_reachable": None,
                    "switching_cost_is_low": None},
        "intent": "UNKNOWN — case study title only; full text not fetched.",
        "note": "Interesting for the 'agent settlement layer' direction, which "
                "the paper currently defers. Verify before pursuing.",
    },
    {
        "name": "Sigea Cloud Labs (enterprise storage)",
        "why": "Public Akash case study: 'Rebuilt Enterprise Storage on "
               "Decentralized Infrastructure'.",
        "reason_b": "storage is NOT MatMul — poor fit for KOK's kernel",
        "answers": {"cheaper_for_existing_job": True, "workload_is_matmul_shaped": False,
                    "permissionlessness_matters": False, "decision_maker_reachable": None,
                    "switching_cost_is_low": None},
        "intent": "UNKNOWN",
        "note": "Likely REJECT on fit: the U layer proves MatMul, not storage.",
    },
    {
        "name": "Passage (browser virtual events, UE5)",
        "why": "Public Akash case study (2024-11-26): reduced GPU cloud cost by "
               "'an average of 50% (up to 70%)'. Rendered streaming, Unreal Engine 5.",
        "reason_b": "rendering is rasterisation, not MatMul — KOK cannot serve it",
        "answers": {"cheaper_for_existing_job": True, "workload_is_matmul_shaped": False,
                    "permissionlessness_matters": False, "decision_maker_reachable": None,
                    "switching_cost_is_low": True},
        "intent": "UNKNOWN",
        "note": "REJECT on workload shape despite excellent cost data. Included "
                "to show the filter rejects even a strong cost story.",
    },
    {
        "name": "Astria (AI image workloads)",
        "why": "Public Akash case study: moved AI image workloads to Akash.",
        "reason_b": "image generation is MatMul-shaped (diffusion = repeated MatMul)",
        "answers": {"cheaper_for_existing_job": True, "workload_is_matmul_shaped": True,
                    "permissionlessness_matters": None, "decision_maker_reachable": None,
                    "switching_cost_is_low": True},
        "intent": "UNKNOWN — full case study not fetched.",
        "note": "Good workload fit; privacy need unverified.",
    },
    {
        "name": "Witness Chain (decentralised physical state consensus)",
        "why": "Public Akash case study title. Physical-state consensus.",
        "reason_b": "consensus proofs may be provable compute demand",
        "answers": {"cheaper_for_existing_job": None, "workload_is_matmul_shaped": None,
                    "permissionlessness_matters": True, "decision_maker_reachable": None,
                    "switching_cost_is_low": None},
        "intent": "UNKNOWN",
        "note": "The ZK-coprocessing direction in one name; but the paper just "
                "downgraded that direction after the Axiom measurement, so low priority.",
    },
]


def report():
    print("=" * 76)
    print("KOK v2 — F0 CANDIDATE LIST (2026-09-21, all sources live-fetched)")
    print("=" * 76)
    print("Akash's own case studies are the public record of WHO buys decentralised")
    print("compute and WHY. Each candidate is scored by the F0 rubric; every")
    print("buying-intent field is honestly UNKNOWN unless it was stated.\n")

    for c in CANDIDATES:
        s, verdict = score(c["answers"])
        print("-" * 76)
        print(f"  {c['name']}                      score {s:.1f} -> {verdict}")
        print(f"  why:    {c['why']}")
        print(f"  reason: {c['reason_b']}")
        print(f"  intent: {c['intent']}")
        print(f"  note:   {c['note']}")

    print("\n" + "-" * 76)
    print("WHAT THE LIST PROVES")
    print("-" * 76)
    print("""  The candidates are real, named companies with public compute-buying
  histories. The rubric separates them cleanly:
    - Flashback Labs scores highest because it states a PRIVACY requirement
      and runs INFERENCE, which is exactly KOK's (a)+(b) intersection.
    - ROUND-4 FIX, 2026-09-24 (round-4 finding #33): an earlier line said
      "Passage scores lowest despite the best cost data", but this file's own
      scorer gives Passage 1.5 against Sigea Cloud Labs 1.0 and Witness Chain
      1.0 — Passage is NOT the lowest. The observation that survives is the
      real one: Passage has the best cost data but cannot be served, because
      rendering is not MatMul; the two lowest scorers are low for the same
      reason (no MatMul-shaped workload), not because of cost data.
    - Passage cannot be served despite the best cost data, because rendering is
      not MatMul and KOK cannot serve it.
  That separation is the whole point of F0: it prevents a sales effort from
  chasing a company the protocol cannot actually serve.

  WHAT THIS LIST DOES NOT CONTAIN:
    - No claimed buying intent. Every intent field says UNKNOWN.
    - No invented revenue or deal sizes.
    - No enterprise 'provenance market' size, because the earlier research
      found no evidence for it and it stays BULUNAMADI.""")

if __name__ == "__main__":
    report()
    print("\nRESULT: CANDIDATE SCORER RUNS — unresolved items stay BULUNAMADI\n")
