"""Tests for adoption_econ.py: TV-35 cross-subsidy, TV-36 cold start, TV-37 verdict.

Covers normal inputs, boundary values (0, negative, NaN, large), determinism,
and the documented ValueError guards in tv36_cold_start.
"""

import math

import pytest

from adoption_econ import (
    ANCHORS,
    SPEC,
    tv35_cross_subsidy,
    tv36_cold_start,
    tv36_find_critical_seed,
    tv37_verdict,
)

# ---------------------------------------------------------------------------
# tv35_cross_subsidy
# ---------------------------------------------------------------------------


def test_tv35_returns_all_expected_keys():
    r = tv35_cross_subsidy(1.32)
    assert set(r) == {
        "reward_per_s_KOK",
        "tail_per_s_KOK",
        "mining_opp_cost_per_FLOP_KOK_launch",
        "mining_opp_cost_per_FLOP_KOK_tail",
        "market_price_per_FLOP_usd",
        "utilisation",
        "sold_revenue_per_FLOP_usd",
    }


def test_tv35_security_budget_matches_spec():
    # R0 * (1 / target_block_time) = 50 * 10 = 500 KOK/s at launch
    r = tv35_cross_subsidy(1.32)
    assert r["reward_per_s_KOK"] == pytest.approx(
        SPEC["R0_first_reward_KOK"] / SPEC["target_block_time_s"])
    assert r["tail_per_s_KOK"] == pytest.approx(
        SPEC["Rinf_tail_reward_KOK"] / SPEC["target_block_time_s"])
    assert r["reward_per_s_KOK"] == pytest.approx(500.0)
    assert r["tail_per_s_KOK"] == pytest.approx(20.0)


def test_tv35_mining_opportunity_cost_per_flop():
    r = tv35_cross_subsidy(1.32)
    # reward_per_s / network_FLOPs_per_s = 500 / 1e17
    assert r["mining_opp_cost_per_FLOP_KOK_launch"] == pytest.approx(5e-15)
    assert r["mining_opp_cost_per_FLOP_KOK_tail"] == pytest.approx(2e-16)


def test_tv35_market_price_per_flop_scales_linearly():
    assert tv35_cross_subsidy(1.32)["market_price_per_FLOP_usd"] == pytest.approx(1.32e-14)
    assert tv35_cross_subsidy(0.0)["market_price_per_FLOP_usd"] == pytest.approx(0.0)
    # doubling the token price doubles the USD/FLOP
    assert (tv35_cross_subsidy(2.64)["market_price_per_FLOP_usd"]
            == pytest.approx(2 * 1.32e-14))


def test_tv35_default_utilisation_is_one():
    assert tv35_cross_subsidy(1.32)["utilisation"] == pytest.approx(1.0)
    assert tv35_cross_subsidy(1.32)["sold_revenue_per_FLOP_usd"] == pytest.approx(1.32e-14)


@pytest.mark.parametrize("util", [0.0, 0.01, 0.5, 1.0])
def test_tv35_utilisation_scales_sold_revenue(util):
    # ROUND-5 fix: utilisation must actually enter the sold-revenue arithmetic.
    r = tv35_cross_subsidy(1.32, util)
    assert r["utilisation"] == pytest.approx(util)
    assert r["sold_revenue_per_FLOP_usd"] == pytest.approx(1.32e-14 * util)


def test_tv35_utilisation_does_not_touch_security_numbers():
    # utilisation is a demand-side knob; the security budget is independent of it
    base = tv35_cross_subsidy(1.32, 1.0)
    for util in (0.0, 0.5, 2.0, 100.0):
        r = tv35_cross_subsidy(1.32, util)
        assert r["reward_per_s_KOK"] == base["reward_per_s_KOK"]
        assert r["tail_per_s_KOK"] == base["tail_per_s_KOK"]
        assert r["mining_opp_cost_per_FLOP_KOK_launch"] == base["mining_opp_cost_per_FLOP_KOK_launch"]
        assert r["mining_opp_cost_per_FLOP_KOK_tail"] == base["mining_opp_cost_per_FLOP_KOK_tail"]


def test_tv35_determinism():
    assert tv35_cross_subsidy(1.32, 0.7) == tv35_cross_subsidy(1.32, 0.7)


# ---------------------------------------------------------------------------
# tv36_cold_start — boundary / error cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [-0.1, -1.0, 1.5, 2.0])
def test_tv36_rejects_seed_demand_out_of_range(seed):
    with pytest.raises(ValueError, match="seed_demand"):
        tv36_cold_start(seed, 1.0)


@pytest.mark.parametrize("ratio", [-0.01, -1.0, float("nan"), float("inf")])
def test_tv36_rejects_invalid_cross_subsidy_ratio(ratio):
    with pytest.raises(ValueError, match="cross_subsidy_ratio"):
        tv36_cold_start(0.01, ratio)


@pytest.mark.parametrize("take", [-0.1, 1.5, 2.0])
def test_tv36_rejects_miner_take_out_of_range(take):
    with pytest.raises(ValueError, match="miner_take"):
        tv36_cold_start(0.01, 1.0, miner_take=take)


def test_tv36_accepts_exact_boundaries():
    # [0, 1] endpoints are valid and must not raise
    assert tv36_cold_start(0.0, 0.0)["escaped_dead_state"] is False
    assert isinstance(tv36_cold_start(1.0, 0.0)["final_demand"], float)


def test_tv36_zero_seed_is_the_absorbing_dead_state():
    # Pearl state: no seed, no subsidy strength -> stays dead forever
    for ratio in (0.0, 0.5, 1.0, 2.0):
        r = tv36_cold_start(0.0, ratio)
        assert r["final_demand"] == pytest.approx(0.0)
        assert r["escaped_dead_state"] is False


def test_tv36_no_subsidy_never_escapes_from_below_barrier():
    # ratio 0 -> no price advantage -> arrivals are zero below the barrier
    for seed in (0.0002, 0.005, 0.019):
        assert tv36_cold_start(seed, 0.0)["escaped_dead_state"] is False


def test_tv36_strong_subsidy_escapes_and_saturates_at_ceiling():
    # the model clamps D to 1 - D_alt = 0.40 (the incumbent holds the rest)
    r = tv36_cold_start(0.01, 2.0)
    assert r["escaped_dead_state"] is True
    assert r["final_demand"] == pytest.approx(0.40)


def test_tv36_demand_never_exceeds_addressable_share():
    for ratio in (0.5, 1.0, 2.0, 10.0, 1000.0):
        r = tv36_cold_start(0.01, ratio)
        assert 0.0 <= r["final_demand"] <= 0.40 + 1e-12


def test_tv36_determinism():
    assert tv36_cold_start(0.01, 1.0) == tv36_cold_start(0.01, 1.0)
    assert tv36_cold_start(0.01, 1.0, miner_take=0.25) == tv36_cold_start(0.01, 1.0, miner_take=0.25)


def test_tv36_miner_take_changes_above_barrier_dynamics():
    # above the barrier churn = 0.02 * (1 - miner_take) * D, so a higher
    # miner_take slows churn; the two runs must not be identical
    low = tv36_cold_start(0.05, 2.0, miner_take=0.1, steps=5)
    high = tv36_cold_start(0.05, 2.0, miner_take=0.9, steps=5)
    assert low != high


def test_tv36_horizon_affects_result():
    # a short horizon can miss an escape that a long one catches
    short = tv36_cold_start(0.01, 2.0, steps=1)
    long_ = tv36_cold_start(0.01, 2.0, steps=400)
    assert short["escaped_dead_state"] is False
    assert long_["escaped_dead_state"] is True


# ---------------------------------------------------------------------------
# tv36_find_critical_seed
# ---------------------------------------------------------------------------


def test_find_critical_seed_none_when_subsidy_is_zero():
    seed, res = tv36_find_critical_seed(0.0)
    assert seed is None
    assert res is None


def test_find_critical_seed_finds_an_escape_above_barrier():
    for ratio in (0.5, 1.0, 2.0):
        seed, res = tv36_find_critical_seed(ratio)
        assert seed is not None
        assert 0.0 < seed < 0.02           # always found BELOW the barrier
        assert res["escaped_dead_state"] is True


def test_find_critical_seed_stronger_subsidy_needs_a_smaller_seed():
    s_weak = tv36_find_critical_seed(0.5)[0]
    s_strong = tv36_find_critical_seed(2.0)[0]
    assert s_strong <= s_weak


# ---------------------------------------------------------------------------
# tv37_verdict
# ---------------------------------------------------------------------------


def test_tv37_verdict_returns_tv35_dict(capsys):
    r = tv37_verdict(token_price_usd=0.10)
    out = capsys.readouterr().out
    assert "TV-37" in out
    assert "CROSS-OVER" in out
    # the return value is the tv35 result, so the reported figures are testable
    assert set(r) == set(tv35_cross_subsidy(1.32))
    assert r["market_price_per_FLOP_usd"] == pytest.approx(1.32e-14)


def test_tv37_verdict_default_price_reads_the_verified_anchor():
    # ROUND-5 fix F14: the default must come from ANCHORS, not a literal
    assert ANCHORS["deepseek_v4pro_peak_usd_per_Mtoken_in"] == pytest.approx(1.32)
    r = tv37_verdict()
    assert r["market_price_per_FLOP_usd"] == pytest.approx(
        ANCHORS["deepseek_v4pro_peak_usd_per_Mtoken_in"] / 1e14)


def test_tv37_verdict_custom_price_is_used(capsys):
    r = tv37_verdict(verified_compute_price_per_Mtoken=2.64)
    assert r["market_price_per_FLOP_usd"] == pytest.approx(2.64e-14)
    assert "$2.64/Mtoken" in capsys.readouterr().out


def test_tv37_crossover_is_scenario_free_arithmetic(capsys):
    tv37_verdict(verified_compute_price_per_Mtoken=1.32, token_price_usd=0.001)
    out = capsys.readouterr().out
    # crossover at launch = market_usd_per_FLOP / moc_launch = 1.32e-14 / 5e-15
    assert "$2.640000" in out
    assert "BELOW the" in out
