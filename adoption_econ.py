#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOK v2 — ADOPTION ECONOMICS PROTOTYPE
=====================================
TV-35  The cross-subsidy claim: is the compute really "free"?
TV-36  The two-sided cold start: can the network escape the empty-block equilibrium?
TV-37  The honest verdict: when does KOK beat a plain GHOSTDAG PoW?

This file tests the project's central selling point with arithmetic, not adjectives.
It is deliberately separate from the protocol prototypes: it models the MARKET,
not the chain. Every number it uses is either (a) a spec parameter, (b) a verified
market figure whose source is named below, or (c) a clearly-labelled SCENARIO
assumption that the reader is invited to change.

------------------------------------------------------------------------------
THE CLAIM UNDER TEST (the one the whole project rests on)
------------------------------------------------------------------------------
"Because miners must already buy hardware and electricity to chase block rewards,
the useful work they could sell is available at near-zero marginal cost, so KOK can
underprice dedicated AI compute."

This sounds compelling. It is the standard PoUW pitch. It is also, as written,
FALSE — and TV-35 shows exactly why, and what the true version of the claim is.

The error: a miner's hardware is paid for by the block reward, but the block reward
pays for a specific thing — a winning lottery ticket. The miner buys hashpower to
buy tickets. If the miner sells the compute instead of mining with it, it stops
buying tickets. The compute is therefore NOT free; its cost is the forgone block
reward. The honest version of the claim is about TAX incidence, not free lunch:
the security budget is a cost the protocol must pay anyway, so any useful work it
can parasitically attach itself to is *subsidised by security spending* — useful
work is cheap, not free, and it is cheap exactly to the extent that it can ride
on compute the miner was going to do anyway.

TV-35 measures the size of that subsidy and finds the honest number.
------------------------------------------------------------------------------

VERIFIED SOURCES USED (as of 2026-09-21; see KOK_V2_REFERENCES.md):
  [Basu]  arXiv 2606.04819 — the live Pearl network: 24 EH/s, ~320,000 GPU-equivalents,
          ~112 MW, and (the number that matters here) ZERO useful computation sold.
          This is the measured counter-example to the naive claim: a large PoUW
          network ran for years and sold nothing.
  [KW]    arXiv 2504.09971v4 — the honest cost of the PoUW kernel is
          alpha(n) = o(1) overhead over plain MatMul (Lemma 6.5 discussion), i.e. the
          useful and the security work are nearly the SAME work. This is the one
          structural fact that makes the subsidy argument work at all.
  [Pass]  arXiv 2606.06700 — the regime taxonomy; used for TV-37.

Everything else below is a labelled assumption. Run:  python3 adoption_econ.py
"""

import math

# ============================================================================
# SECTION 1 — VERIFIED ANCHORS (do not edit without a source)
# ============================================================================

ANCHORS = {
    # [Basu] the one live PoUW network, measured
    "pearl_hashrate_EH_s":      24.0,
    "pearl_gpu_equivalents":    320_000.0,
    "pearl_MW":                 112.0,
    "pearl_useful_compute_sold": 0.0,          # <-- the finding that matters
    # [KW] overhead of the useful construction over plain MatMul
    "kw_alpha_overhead":        1.30,          # gamma=alpha=1.3 in spec C.2 (Pass's KW instantiation)
    # VERIFIED 2026-09-21, official pages (ARASTIRMA_SONUCLARI.md):
    "deepseek_v4pro_peak_usd_per_Mtoken_in": 1.32,   # api-docs.deepseek.com
    "deepseek_v4pro_offpeak_usd_per_Mtoken": 0.66,   # half of peak
    "h100_spot_usd_per_gpu_hr": 2.15,      # ROUND-6: SUPERSEDED quote —
    # KOK_V2_PAPER.md:949 now records Nebius preemptible at $0.79/GPU-hr;
    # this line is kept as the earlier quote, not a current price.
    "h100_ondemand_usd_per_gpu_hr": 3.85,           # Nebius
    # the one network that publishes real compute revenue
    "aethir_2025_revenue_usd":  127_800_000.0,      # their own blog
    "aethir_arr_q3_2025_usd":   166_000_000.0,
}

# ============================================================================
# SECTION 2 — SPEC PARAMETERS (from KOK_V2_TECHNICAL_SPEC.md section C.2)
# ============================================================================

SPEC = {
    "R0_first_reward_KOK":      50.0,
    "Rinf_tail_reward_KOK":     2.0,
    "target_block_time_s":      0.1,           # 10 BPS
    "treasury_share":           0.05,
    "network_FLOPs_per_s":      1e17,          # mid scenario, spec C.2 (10^16..10^18)
}


# ============================================================================
# TV-35  THE CROSS-SUBSIDY NUMBER — what the compute actually costs
# ============================================================================
#
# Setup. A miner owns G GPUs. Each GPU can do F GPU-FLOPs/s. Two ways to use it:
#   (A) mine: run the KW kernel. Expected revenue = block_reward_per_second
#       * (my_share_of_hashrate) = R_ps * G*F / NetFLOPs.
#   (B) sell: run a customer's MatMul. Revenue = price_per_FLOP * G*F * utilisation.
#
# The naive claim says (B) is free because the hardware is sunk. But if the miner
# does (B) it forgoes (A). So the true marginal cost of selling one second of GPU
# time is exactly the mining revenue that second would have earned. That is the
# number below: the MINING OPPORTUNITY COST of compute.
#
# Then the honest subsidy statement: if the protocol's kernel is the SAME work
# (KW's alpha ~1.3), then a miner who mines is *also* doing useful MatMul-shaped
# work, and the protocol can sell that work without the miner forgoing anything.
# The subsidy exists only where the two overlap. TV-35 quantifies the overlap.

def tv35_cross_subsidy(price_per_Mtoken: float, utilisation: float = 1.0):
    """Return the honest economics of the cross-subsidy claim.

    price_per_Mtoken: the market price for 1 million tokens of LLM inference (USD).
                      A caller-supplied SCENARIO value; the research file supplies
                      verified ones. This function is agnostic.
    utilisation:      fraction of GPU time the sold job actually occupies.
    """
    # --- the security budget: what the chain pays per second, in KOK and USD ---
    R0 = SPEC["R0_first_reward_KOK"]
    T_b = SPEC["target_block_time_s"]
    BPS = 1.0 / T_b
    reward_per_s_KOK = R0 * BPS                      # 50 KOK * 10/s = 500 KOK/s at launch
    tail_per_s_KOK = SPEC["Rinf_tail_reward_KOK"] * BPS

    # --- the network's compute ---
    NetF = SPEC["network_FLOPs_per_s"]

    # --- mining opportunity cost, per FLOP, in KOK ---
    # If the whole network splits the reward, one FLOP of mining earns:
    moc_per_FLOP_KOK = reward_per_s_KOK / NetF       # launch
    moc_tail_KOK = tail_per_s_KOK / NetF             # tail (the permanent regime)

    # --- what the customer's compute is worth, converted to the same unit ---
    # A modern GPU does ~1e15 GPU-FLOPs/s; 1M tokens of inference needs a fixed
    # amount of FLOPs (roughly 2 * params * tokens; for a mid model ~1e14 FLOPs
    # per 1M tokens). So price_per_Mtoken / FLOPs_per_Mtoken = $/FLOP.
    FLOPs_per_Mtoken = 1e14                          # SCENARIO: 2*N*T for a ~50B model
    usd_per_FLOP = price_per_Mtoken / FLOPs_per_Mtoken

    return {
        "reward_per_s_KOK": reward_per_s_KOK,
        "tail_per_s_KOK": tail_per_s_KOK,
        # the two per-FLOP costs, each in its OWN unit: the mining opportunity
        # cost in KOK/FLOP and the market compute price in USD/FLOP. They are NOT
        # on a comparable footing until one is converted with the KOK token price
        # -- that conversion is exactly what TV-37's crossover does. If the mining
        # opportunity cost, once converted to $, EXCEEDS the market compute price,
        # the compute is NOT free and the subsidy argument does not make KOK
        # competitive on price alone.
        "mining_opp_cost_per_FLOP_KOK_launch": moc_per_FLOP_KOK,
        "mining_opp_cost_per_FLOP_KOK_tail": moc_tail_KOK,
        "market_price_per_FLOP_usd": usd_per_FLOP,
        # ROUND-5 FIX, 2026-09-24 (round-5 finding F12): `utilisation` was
        # documented as "fraction of GPU time the sold job actually occupies"
        # and the model's own setup states revenue = price*G*F*utilisation,
        # but it was only ECHOED here and entered no arithmetic -- measured:
        # utilisation in {1.0, 0.5, 0.01, 0.0, 100, -1} left every computed
        # field identical. The sold revenue per FLOP now scales by it, so a
        # job occupying half the GPU time earns half as much per FLOP of
        # network capacity, which is what the setup formula says.
        "utilisation": utilisation,
        "sold_revenue_per_FLOP_usd": usd_per_FLOP * utilisation,
    }


# ============================================================================
# TV-36  THE TWO-SIDED COLD START — can the network escape the empty block?
# ============================================================================
#
# The equilibrium that kills every PoUW chain: miners mine empty blocks because
# the subsidy pays them to; nobody submits tasks because no miner is serving; the
# chain runs forever at phi=0 and is, functionally, a plain PoW chain with worse
# marketing. [Basu] measured exactly this state in the wild: 24 EH/s, zero useful
# compute sold.
#
# The model: two populations whose growth depends on each other.
#   miners M(t)     grow if mining is profitable AND (optionally) if selling is
#   demand D(t)     grows if the network's compute is cheap and available
# A demand network effect: each new buyer makes the next buyer more likely
# (liquidity of compute). Each new miner makes compute cheaper.
#
# The question is not "does demand exist" but "does the basin of attraction of
# the EMPTY equilibrium shrink once a real task arrives". TV-36 finds the
# critical seed of demand -- the smallest D(0) that escapes the dead state.

def tv36_cold_start(seed_demand: float, cross_subsidy_ratio: float,
                    miner_take: float = 0.5, steps: int = 400):
    """Simulate the two-sided market and report whether it escapes the dead state.

    ROUND-5 FIX, 2026-09-24 (round-5 finding F21): this function accepted
    anything for its inputs -- measured: negative seed_demand returned
    final_demand 0.0 (silently clamped), a ratio of -1.0 silently produced
    a NEGATIVE price advantage (arrivals NEGATIVE, churn positive, so D
    decayed faster than the ratio-0 case and looked like a stronger dead
    state), and non-numeric or NaN inputs propagated NaN through every
    threshold and produced a plausible-looking number. Inputs are now
    validated, so a nonsense parameter is an error rather than a result.

    seed_demand:          initial fraction of the network's compute that is
                          actually SOLD (D(0)). The parameter we sweep.
    cross_subsidy_ratio:  market compute price / mining opportunity cost. >1
                          means selling beats mining (miners will serve); <1
                          means mining pays better (miners ignore tasks).
                          CORRECTED (2026-09-23): this ratio is NOT produced by
                          TV-35. TV-35 returns the mining opportunity cost in
                          KOK/FLOP and the market price in USD/FLOP and computes no
                          dimensionless ratio; turning those two into this number
                          requires the KOK token price, which TV-37 uses only for
                          its crossover analysis. The ratio is a SCENARIO input:
                          the only caller (tv37_verdict, section [6]) passes the
                          hardcoded values 0.5, 1.0 and 2.0.
    miner_take:           fraction of a task fee that reaches the miner.
    """
    # The model that makes the dead state REAL: demand has a liquidity barrier.
    # A buyer comes only if enough other buyers are already there that the
    # market is liquid (a job can be served immediately). Below the barrier the
    # arrival rate is NEGATIVE -- buyers churn out because the market is dead,
    # exactly as [Basu] measured. Above it, network effects take over.
    D = seed_demand             # the thing we are solving for
    D_alt = 0.60                # SCENARIO: the incumbent cloud captures the rest
    LIQ_BARRIER = 0.02          # SCENARIO: the critical-mass threshold (2% of market)
    CHURN_DEAD = 0.04           # buyers leave a market that cannot serve them

    # ROUND-5 FIX, 2026-09-24 (round-5 finding F21): validate the inputs. A
    # negative ratio silently produced a negative price advantage (arrivals
    # NEGATIVE, D decaying FASTER than the ratio-0 case and masquerading as a
    # stronger dead state); NaN propagated through every threshold into a
    # plausible-looking number. These are now errors.
    if not (0.0 <= seed_demand <= 1.0):
        raise ValueError("seed_demand must lie in [0,1], got %r" % (seed_demand,))
    if not math.isfinite(cross_subsidy_ratio):
        raise ValueError("cross_subsidy_ratio must be finite, got %r"
                         % (cross_subsidy_ratio,))
    if cross_subsidy_ratio < 0.0:
        raise ValueError("a negative cross_subsidy_ratio inverts the price "
                         "advantage and is meaningless here, got %r"
                         % (cross_subsidy_ratio,))
    if not (0.0 <= miner_take <= 1.0):
        raise ValueError("miner_take must lie in [0,1], got %r" % (miner_take,))

    # the price advantage KOK offers a buyer, from TV-35
    price_adv = min(cross_subsidy_ratio, 2.0)        # capped: no infinite advantage

    for t in range(steps):
        if D < LIQ_BARRIER:
            # below critical mass: no network effect, buyers churn, miners do not
            # bother to serve a market with no buyers. This is the Pearl state.
            # The price advantage decides whether ANY seed can escape: arrivals
            # must be able to outrun churn somewhere below the barrier. If the
            # subsidy is weak the dead state is ABSORBING -- no seed escapes,
            # which is the honest reading of a PoUW chain whose compute earns
            # less than the market pays.
            # Measured by binary search over tv36_cold_start: the escape
            # threshold sits at a cross-subsidy ratio of about 0.79, not at 1.0.
            # Escape begins BEFORE parity, which is the one piece of good news
            # the model offers; below 0.79 no seed below the barrier escapes.
            # CORRECTION 2026-09-23 (round-3 finding [28]): "below 0.79 no
            # seed escapes" is an OVERSTATEMENT — this file's own section [6]
            # refutes it. ROUND-5, 2026-09-24 (round-5 finding F19): "5 of 9"
            # matched no count this file performs; the measured count is 184
            # of 199 sub-barrier seeds (0.0001..0.0199 at ratio 0.5) escape.
            # ROUND-6, 2026-09-24 (SESTER audit): this count is now PRINTED by
            # the TV-60b sweep below rather than existing only in prose, so a
            # future refactor that changes the dynamics moves the printed
            # number with it instead of leaving a stale claim behind.
            # The dynamics have a REPELLING fixed point at D*, not an absorbing
            # state: seeds below D* decay and seeds above it grow, and 0.79 is
            # where the growth is fast enough to cross the 0.15 visibility line
            # within the test's 400 steps. Restated below rather than left
            # overclaiming.
            # Arrivals come from the price advantage alone (a buyer who finds a
            # genuinely cheaper supplier switches regardless of liquidity), plus a
            # small term from the market that already exists. Churn is the cost of
            # an illiquid market. The two cross at a critical price_adv, below
            # which the dead state is absorbing for every seed.
            arrive = 0.05 * price_adv * D * (1.0 + 8.0 * D / LIQ_BARRIER)
            churn = CHURN_DEAD * (1.0 + (LIQ_BARRIER - D)) * D
        else:
            # above critical mass: network effects, liquidity, miner reputation
            arrive = 0.04 * price_adv * (0.5 + D)
            churn = 0.02 * (1.0 - miner_take) * D
        D = D + arrive - churn
        D = max(0.0, min(1.0 - D_alt, D))           # never exceeds the addressable share

        escaped = D > 0.15          # 15% of the addressable market served = alive
    # ROUND-5, 2026-09-24 (round-5 finding F20): this loop used to grow a
    # normalised miner count M = M*(1+0.001*(1+ratio)), but M never entered
    # the D dynamics and `final_miners` was never read downstream, so the
    # miner side was INERT -- measured: removing the two M lines leaves D
    # bit-identical for all 36 (ratio, seed) combinations. The dead state is
    # reported as DEMAND-only, and miner growth is out of scope here; if a
    # future version needs miner feedback it must be wired into D or reported.
    return {"final_demand": D, "escaped_dead_state": escaped}


def tv36_find_critical_seed(cross_subsidy_ratio: float):
    """The smallest seed of real demand that escapes the empty-block equilibrium.

    Honest semantics: a seed right at the liquidity barrier is not a real escape,
    it is being placed past the obstacle by fiat. The seed we report must clear
    the barrier from BELOW -- i.e. the market must be able to grow through the
    barrier on its own dynamics once seeded. If no seed below the barrier can do
    that, the dead state is absorbing and we report None (never escapes)."""
    for seed in [x / 5000.0 for x in range(1, 100)]:   # 0.0002 .. 0.0198, all BELOW
        r = tv36_cold_start(seed, cross_subsidy_ratio)
        if r["escaped_dead_state"]:
            return seed, r
    return None, None


# ============================================================================
# TV-37  THE HONEST VERDICT — the question the user actually asked
# ============================================================================
#
# "Why would anyone use this?" answered as a comparison against the honest
# alternative: a plain GHOSTDAG PoW coin with the same parameters and no utility
# layer at all (Kaspa-shaped). If KOK's answer is only "it is Kaspa plus a
# hope", then the utility layer has no strategic value and the project is, as the
# user said, dead on arrival. TV-37 computes the crossover: how much real demand
# does KOK need before it is worth more than its own fallback?

def tv37_verdict(verified_compute_price_per_Mtoken=None, token_price_usd=0.10):
    """Print the honest strategic verdict with the numbers behind it.

    token_price_usd: the KOK price in USD. A SCENARIO input, clearly labelled:
    without it the two sides of the comparison are in different units and the
    question 'is selling better than mining' cannot be answered. The honest
    treatment is to report the CROSS-OVER PRICE -- the token price at which
    mining opportunity cost equals the market compute price -- because that is
    the number that does not depend on guessing the market.
    """
    print("=" * 76)
    print("TV-37  WHY WOULD ANYONE USE THIS? (the honest answer, with arithmetic)")
    print("=" * 76)

    if verified_compute_price_per_Mtoken is None:
        # VERIFIED 2026-09-21 from official pricing pages (ARASTIRMA_SONUCLARI.md):
        # DeepSeek V4-Pro-0813, api-docs.deepseek.com, peak input $1.32/Mtoken.
        # Chosen as the anchor because it is the cheapest serious frontier model,
        # i.e. the hardest price KOK would have to beat. Together AI lists the
        # identical model at the identical $1.32, which cross-checks it.
        # ROUND-5 FIX, 2026-09-24 (round-5 finding F14): this was a LITERAL
        # 1.32 while ANCHORS held the same value under a "verified" key that
        # no arithmetic read -- measured: overwriting the anchor with 99.0
        # moved no output, only the literal did. The default now reads the
        # anchor, so the verified figure and the figure used are the same
        # variable and cannot drift apart.
        verified_compute_price_per_Mtoken = ANCHORS["deepseek_v4pro_peak_usd_per_Mtoken_in"]

    r35 = tv35_cross_subsidy(verified_compute_price_per_Mtoken)

    print(f"\n  [1] What the chain pays for security, per second:")
    print(f"      at launch:  {r35['reward_per_s_KOK']:>10,.0f} KOK/s   (R0 * 10 BPS)")
    print(f"      at the tail: {r35['tail_per_s_KOK']:>9,.0f} KOK/s   (the permanent regime)")

    print(f"\n  [2] The mining opportunity cost of compute (the number that kills")
    print(f"      the 'free lunch' version of the claim):")
    print(f"      one FLOP of mining is worth, at launch,")
    print(f"      {r35['mining_opp_cost_per_FLOP_KOK_launch']:.3e} KOK. A miner that sells")
    print(f"      that FLOP instead of mining with it forgoes exactly this.")

    print(f"\n  [3] What the same FLOP is worth on the AI market:")
    print(f"      ${r35['market_price_per_FLOP_usd']:.3e} / FLOP at the VERIFIED")
    print(f"      ${verified_compute_price_per_Mtoken:.2f}/Mtoken (DeepSeek V4-Pro peak).")

    # ROUND-5, 2026-09-24 (round-5 finding F13): ANCHORS holds verified figures
    # for GPU rental and Aethir revenue (h100_spot/ondemand per GPU-hour,
    # aethir_2025_revenue, aethir_arr_q3_2025, deepseek_offpeak) that this
    # verdict's ARITHMETIC never reads -- measured: overwriting each with 99.0
    # moved no computed field. They are kept as the file's citation record, and
    # reported here as UNUSED-ARITHMETIC anchors rather than being presented as
    # inputs the conclusion depends on.
    unused = ["deepseek_v4pro_offpeak_usd_per_Mtoken",
              "h100_spot_usd_per_gpu_hr",
              "h100_ondemand_usd_per_gpu_hr",
              "aethir_2025_revenue_usd",
              "aethir_arr_q3_2025_usd"]
    print(f"      ROUND-5 anchor audit: {len(unused)} verified figures are")
    print(f"      citation-only (GPU rental, Aethir revenue, off-peak price) and")
    print(f"      enter no arithmetic in this file; only the peak price does.")

    # THE CROSS-OVER PRICE: the token price at which mining one FLOP is worth
    # exactly what selling that FLOP is worth on the AI market. Above it, mining
    # pays better than any compute sale, and the utility layer cannot compete on
    # price -- it must win on reason (b), permissionlessness. Below it, selling
    # beats mining and the subsidy argument is real. This is the number that does
    # NOT depend on guessing the token price.
    moc_launch = r35["mining_opp_cost_per_FLOP_KOK_launch"]
    xover_launch = r35["market_price_per_FLOP_usd"] / moc_launch
    xover_tail = r35["market_price_per_FLOP_usd"] / r35["mining_opp_cost_per_FLOP_KOK_tail"]
    print(f"\n  [3b] THE CROSS-OVER TOKEN PRICE (the scenario-free number):")
    print(f"      mining == selling when KOK = ${xover_launch:.6f} (at launch rewards)")
    print(f"      mining == selling when KOK = ${xover_tail:.6f} (at the 2-KOK tail)")
    # honest reading: BELOW the crossover, selling is the better use of the FLOP,
    # so the cross-subsidy is REAL and price competition can drive adoption.
    # ABOVE it, mining pays better and the utility layer cannot win on price.
    below = token_price_usd < xover_launch
    print(f"      Reading: at ${token_price_usd:.2f} KOK is {'BELOW' if below else 'ABOVE'} the")
    print(f"      crossover, so selling compute pays {'BETTER' if below else 'WORSE'} than mining")
    print(f"      and the cross-subsidy argument is {'REAL' if below else 'NOT REAL'} at this price.")
    print(f"      The crossover, not the guess, is the strategic number: it says the")
    print(f"      utility layer is price-competitive exactly while the token is cheap.")

    print(f"\n  [4] THE HONEST RESTATEMENT OF THE CLAIM:")
    print(f"      The compute is NOT free. It is SUBSIDISED, and only to the extent")
    print(f"      that KW's kernel is the same work as the sold work (alpha ~")
    print(f"      {ANCHORS['kw_alpha_overhead']}). Where they overlap, security spending")
    print(f"      pays for the compute and the fee is nearly pure margin.")
    print(f"      Where they do not overlap, the utility layer competes with mining")
    print(f"      for the same FLOPs and must pay the market rate or better.")

    print(f"\n  [5] THE COUNTER-EXAMPLE WE MUST EXPLAIN ([Basu]):")
    print(f"      Pearl ran {ANCHORS['pearl_hashrate_EH_s']:.0f} EH/s on")
    print(f"      {ANCHORS['pearl_gpu_equivalents']:,.0f} GPU-equivalents")
    print(f"      ({ANCHORS['pearl_MW']:.0f} MW) and sold")
    print(f"      {ANCHORS['pearl_useful_compute_sold']:.0f} useful compute.")
    print(f"      This is the measured shape of the dead equilibrium. Whatever KOK")
    print(f"      does differently has to be a causal answer to THIS number, not a")
    print(f"      slogan about wasted energy.")

    # *** THE INVERTED INCENTIVE: the crossover RISES with the token price. ***
    # At launch (rewards high) the crossover is $2.64; at the tail it is $66.00.
    # (The values above are printed by the code below; an earlier comment here
    # stated $10 and $250, which were the numbers under a different parameter
    # set and no longer matched what the run produces. If the two ever disagree
    # again, the printed values are the authoritative ones.)
    # Read carefully, this is the project's most uncomfortable fact:
    #   - when the token is CHEAP, selling beats mining -> the utility layer is
    #     price-competitive, but the chain is small and nobody has heard of it;
    #   - when the token is EXPENSIVE, mining pays far better than any compute
    #     sale -> miners ignore the utility layer and the chain drifts toward
    #     the empty-block equilibrium, i.e. toward being just an ordinary PoW.
    # The utility layer is most competitive exactly when the network is least
    # established. Adoption must be won EARLY, or the window closes as the
    # token succeeds. This inverts the usual "grow first, monetise later" plan.
    print(f"\n  [5b] THE SPECULATION PARADOX (the uncomfortable fact, corrected):")
    print(f"      the crossover is ${xover_launch:.2f} at launch but ${xover_tail:.2f} at the tail.")
    print(f"      Reading the crossover correctly: it is the token price at which mining")
    print(f"      and selling pay the same. A HIGH crossover means mining pays little per")
    print(f"      FLOP, so selling is attractive. Two forces push it in OPPOSITE ways:")
    print(f"        - the network GROWS  -> the fixed reward is split over more FLOPs ->")
    print(f"          mining pays less per FLOP  -> crossover RISES  -> selling IMPROVES")
    print(f"        - the token APPRECIATES -> mining pays more in dollar terms ->")
    print(f"          crossover is CROSSED  -> selling WORSENS")
    print(f"      *** So speculation is the project's ENEMY, not its friend: a token price")
    print(f"      spike makes the utility layer uncompetitive overnight, even if the")
    print(f"      network is healthy. *** Adoption must be won while the token is cheap;")
    print(f"      the design tension is that every incentive programme that raises the")
    print(f"      price also narrows the window. This is why F0 precedes F3a, and why the")
    print(f"      emission tail (2 KOK) is deliberately small.")

    # the critical-seed analysis at three subsidy positions
    print(f"\n  [6] CAN WE ESCAPE THE DEAD STATE? (critical seed of real demand)")
    for ratio, label in [(0.5, "selling pays HALF of mining (subsidy weak)"),
                         (1.0, "selling pays exactly mining (break-even)"),
                         (2.0, "selling pays DOUBLE mining (subsidy strong)")]:
        seed, res = tv36_find_critical_seed(ratio)
        if seed is None:
            print(f"      {label:46s} -> NEVER ESCAPES")
        else:
            # ROUND-5, 2026-09-24 (round-5 finding F15): the printed share is
            # the model's CEILING (D is clamped to 1-D_alt = 0.40), not an
            # outcome the dynamics chose -- measured: ratios 0.5/0.6/0.8/1.0/
            # 2.0/5.0 all end at exactly 0.400000. The label says so, so a
            # reader does not mistake the clamp for a forecast.
            print(f"      {label:46s} -> escapes at seed D0 >= {seed:.4f}"
                  f"  (saturates at the model's "
                  f"{res['final_demand']*100:.0f}% ceiling)")
    print(f"\n      Reading: the seed is the fraction of the network's compute that")
    print(f"      must be REAL, paying demand from day one. A chain that launches")
    print(f"      with seed = 0 is Pearl. The seed is not something the protocol can")
    print(f"      emit; it is something someone must bring. THAT is the go-to-market.")

    print(f"\n  [7] THE VERDICT (the user's question, answered plainly):")
    print(f"      People will use KOK for exactly one of these reasons, and no other:")
    print(f"        (a) it is provably cheaper than the alternative for a job they")
    print(f"            already pay for; or")
    print(f"        (b) it is the only place a job can run permissionlessly.")
    print(f"      Everything else -- green narratives, 'wasted energy' arguments,")
    print(f"      AI-for-all rhetoric -- is decoration that [Basu] already falsified.")
    print(f"      If neither (a) nor (b) is true on day one, the chain converges to")
    print(f"      the empty-block equilibrium and stays there, because that is the")
    print(f"      stable state of a two-sided market with a zero seed.")
    print(f"\n      Therefore the roadmap's first milestone is not a testnet.")
    print(f"      It is A CUSTOMER WITH A JOB. Everything else is downstream of that.")
    return r35


# ============================================================================
# main
# ============================================================================

if __name__ == "__main__":
    print("=" * 76)
    print("KOK v2 — ADOPTION ECONOMICS (TV-35 / TV-36 / TV-37 / TV-60)")
    print("=" * 76)
    print("Testing the project's central claim with arithmetic, not adjectives.\n")

    r35 = tv37_verdict()

    print("\n" + "-" * 76)
    print("TV-60: THE ESCAPE THRESHOLD, for one seed under this file's constants")
    print("-" * 76)
    lo, hi = 0.5, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if tv36_cold_start(0.0002, mid)["escaped_dead_state"]:
            hi = mid
        else:
            lo = mid
    absorbing_below = lo
    # 0.79 is the value the paper quotes; allow a small band so a legitimate
    # parameter refinement moves the guard, not the prose.
    ok = 0.75 <= absorbing_below <= 0.83
    print("      escape begins at a cross-subsidy ratio of about %.4f" % hi)
    # CORRECTION 2026-09-23 (round-3 finding [28]): the line below said
    # "absorbing for every seed below the barrier". That is false — the
    # dynamics have a REPELLING fixed point at D*~0.00158, so seeds ABOVE D*
    # escape even below the 0.79 ratio. Restated to what the probe actually
    # shows: below this ratio a seed planted at 0.0002 (the test seed, which
    # sits below D*) does not escape within the 400-step horizon.
    print("      below %.2f a seed planted at 0.0002 does not escape within the"
          % absorbing_below)
    print("      400-step horizon (D* is ratio-dependent; it is ~0.00158 at")
    print("      ratio 0.5 and no interior repellor exists above ratio 0.82)")
    # ROUND-5, 2026-09-24 (round-5 findings F16/F17): the threshold is labelled
    # "MEASURED" but it is a property of (this file's constants, the single
    # seed 0.0002, and the 400-step horizon), not of any data. Measured
    # sensitivity: CHURN_DEAD 0.04->0.02 moves it to 0.5000 and ->0.08 moves
    # it to 1.0000; LIQ_BARRIER 0.02->0.01 gives 0.7114 and ->0.05 gives
    # 0.8935; the arrival coefficient 0.05->0.10 gives 0.5000; the arrival
    # exponent 8->4 gives 0.8533; the horizon alone moves it 1.0000 (100
    # steps) -> 0.8907 (200) -> 0.7930 (400) -> 0.7587 (1000) -> 0.7554
    # (20000). And over ALL sub-barrier seeds the dead state is absorbing
    # only for ratio <= ~0.08-0.10, not 0.79 -- the 0.79 figure is the
    # threshold for seed 0.0002 specifically. The guard below is therefore the
    # code checking the paper's number against the code's own output under ONE
    # fixed configuration; that is stated here so it is not read as a
    # calibrated measurement.
    # ROUND-6, 2026-09-24 (internal audit, provenance note): the seed set this
    # file sweeps is 0.0001..0.0199 (199 seeds) here and 0.0002..0.0198
    # (99 seeds) in the 184/199 measurement — two different sets, both
    # correctly measured under their own definition. The count is now given
    # with its range wherever it appears so the two are never conflated.
    print("      ROUND-5 honesty note: 0.79 is the threshold for the seed")
    print("      0.0002 under THIS file's constants and horizon, not a")
    print("      calibrated measurement — sweeping the constants moves it")
    print("      (CHURN_DEAD 0.04->0.02 gives 0.50; horizon 400->20000 gives")
    print("      0.7554), and the all-seed absorbing threshold is ~0.08-0.10.")
    print("      paper quotes ~0.79; guard band 0.75..0.83  %s"
          % ("ACCEPT" if ok else "RED"))
    assert ok, ("TV-60: the escape threshold has moved outside the quoted band; "
                "the paper says ~0.79 — check both before assuming either is right")

    # ROUND-6, 2026-09-24 (SESTER internal audit): the 184/199 count was
    # quoted in the prose above and in the paper/spec as a "measured count"
    # while this file never printed it — the "measurement that measures
    # nothing" pattern this project has closed everywhere else. The sweep
    # now runs here and prints its own result, so the number is produced by
    # the code that claims it. Both seed sets are swept and labelled, which
    # also closes the 99-vs-199 provenance confusion in one place.
    print("\n" + "-" * 76)
    print("TV-60b: THE ALL-SEED SWEEP (the count the prose quotes, now printed)")
    print("-" * 76)
    for label, seeds in (("199 seeds 0.0001..0.0199", [i / 10000 for i in range(1, 200)]),
                         ("99 seeds  0.0002..0.0198", [i / 10000 for i in range(2, 200, 2)])):
        esc = sum(1 for s in seeds
                  if tv36_cold_start(s, 0.5)["escaped_dead_state"])
        print("      ratio 0.50, %-26s escaping: %3d/%d"
              % (label, esc, len(seeds)))
    # the all-seed absorbing threshold: the highest ratio where NO seed escapes
    thr = 0.0
    for ratio_x10 in range(1, 200):
        ratio = ratio_x10 / 100.0
        any_esc = any(tv36_cold_start(s, ratio)["escaped_dead_state"]
                      for s in [i / 10000 for i in range(1, 200)])
        if any_esc:
            thr = ratio
            break
    print("      all-seed absorbing threshold (199 seeds): %.4f" % thr)
    print("      (the prose says ~0.08-0.10; this is the number behind it)")

    print("\n" + "-" * 76)
    print("TV-35/36/37 COMPLETE")
    print("-" * 76)
    print("Honest limits of this model: it is a market model, not a forecast. The")
    print("scenario inputs are labelled. Where the research file supplies a verified")
    print("price, substitute it into tv37_verdict(...). The conclusions that do NOT")
    print("depend on the scenario are (4) the restatement of the claim, (5) the")
    print("Pearl counter-example, and (7) the verdict: those hold at any price.")
    print()
    print("ROUND-4, 2026-09-23 (round-3 finding [33]), stated in the file itself:")
    print("the miner side does NOT feed back into D. miner_take and LIQ_BARRIER")
    print("are PARAMETERS of the arrival and churn terms, not quantities derived")
    print("from the miners' observed behaviour within the run, so the model has no")
    print("miners-respond-to-demand channel. A model with that channel is")
    print("qualitatively different, not a correction of this one: miner entry would")
    print("raise security spending, which raises the price advantage, which raises")
    print("D. That loop is deliberately absent here, because closing it requires a")
    print("supply-side calibration this project does not have. Stated rather than")
    print("hidden, so no conclusion drawn from this file is read as including it.")
    print("\nRESULT: STATED — the supply-side calibration this project does not have is named here rather than assumed\n")
