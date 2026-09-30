"""Tests for bond_margin_proto.py: censor_net, critical_fee_capped, critical_margin_full.

Covers both slash modes ("capped" = f3a behaviour, "full" = spec A.5.5 intent),
refill on/off, boundary values (0, fee >= B_out), and determinism.
"""

import pytest

from bond_margin_proto import (
    censor_net,
    critical_fee_capped,
    critical_margin_full,
)


# ---------------------------------------------------------------------------
# censor_net — capped mode
# ---------------------------------------------------------------------------


def test_censor_net_capped_single_event_slashes_the_fee():
    # slash = min(bond, fee) = 100 -> net = 60 - 100 = -40
    net = censor_net(100.0, 100.0, 60.0, 1, refill=True, slash_mode="capped")
    assert net == pytest.approx(-40.0)


def test_censor_net_capped_bond_above_fee_is_ineffective():
    # TV-31: in capped mode the deterrent is bounded by the FEE, so raising the
    # bond changes nothing
    n100 = censor_net(100.0, 100.0, 60.0, 1, slash_mode="capped")
    n500 = censor_net(100.0, 500.0, 60.0, 1, slash_mode="capped")
    n2000 = censor_net(100.0, 2000.0, 60.0, 1, slash_mode="capped")
    assert n100 == pytest.approx(n500)
    assert n500 == pytest.approx(n2000)


def test_censor_net_capped_bond_below_fee_slashes_only_the_bond():
    # bond smaller than fee: the whole bond is lost per event
    net = censor_net(100.0, 25.0, 60.0, 1, slash_mode="capped")
    assert net == pytest.approx(60.0 - 25.0)


def test_censor_net_capped_is_profitable_when_fee_below_b_out():
    net = censor_net(10.0, 30.0, 60.0, 5, refill=True, slash_mode="capped")
    assert net == pytest.approx(5 * 60.0 - 5 * 10.0)
    assert net > 0


# ---------------------------------------------------------------------------
# censor_net — full mode
# ---------------------------------------------------------------------------


def test_censor_net_full_slashes_the_whole_bond():
    # full: slash = min(cur, bond) = 300 -> net = 60 - 300 = -240
    net = censor_net(100.0, 300.0, 60.0, 1, refill=True, slash_mode="full")
    assert net == pytest.approx(-240.0)


def test_censor_net_full_mode_is_stronger_deterrent_than_capped():
    full = censor_net(100.0, 300.0, 60.0, 1, slash_mode="full")
    capped = censor_net(100.0, 300.0, 60.0, 1, slash_mode="capped")
    assert full < capped


def test_censor_net_unknown_slash_mode_falls_back_to_full_branch():
    # the else branch is taken for anything != "capped" (documented behaviour)
    net = censor_net(100.0, 300.0, 60.0, 1, slash_mode="nonsense")
    assert net == pytest.approx(-240.0)


# ---------------------------------------------------------------------------
# censor_net — refill on/off (TV-33)
# ---------------------------------------------------------------------------


def test_censor_net_no_refill_depletes_the_bond_once():
    # bond=300, fee=100: 3 blocked events, then censorship is FREE
    net = censor_net(100.0, 300.0, 60.0, 20, refill=False, slash_mode="capped")
    assert net == pytest.approx(20 * 60.0 - 300.0)
    assert net > 0


def test_censor_net_refill_makes_every_event_pay():
    net = censor_net(100.0, 300.0, 60.0, 20, refill=True, slash_mode="capped")
    assert net == pytest.approx(20 * 60.0 - 20 * 100.0)
    assert net < 0


def test_censor_net_no_refill_total_slash_capped_at_bond():
    # however many events, the one-time bond is the ceiling on the slash
    small = censor_net(100.0, 300.0, 60.0, 5, refill=False)
    large = censor_net(100.0, 300.0, 60.0, 500, refill=False)
    assert small == pytest.approx(5 * 60.0 - 300.0)
    assert large == pytest.approx(500 * 60.0 - 300.0)


def test_censor_net_no_refill_window_is_bond_over_fee():
    fee, bond, b_out = 100.0, 300.0, 60.0
    window = int(bond / fee)
    # just inside the window the censor is still deterred; past it, it profits
    inside = censor_net(fee, bond, b_out, window, refill=False)
    assert inside == pytest.approx(window * b_out - bond)
    assert inside < 0


# ---------------------------------------------------------------------------
# censor_net — boundary values
# ---------------------------------------------------------------------------


def test_censor_net_zero_events_yields_zero():
    assert censor_net(100.0, 300.0, 60.0, 0) == pytest.approx(0.0)


def test_censor_net_zero_b_out_is_all_cost():
    assert censor_net(100.0, 300.0, 0.0, 4, refill=True) == pytest.approx(-400.0)


def test_censor_net_negative_b_out_is_negative():
    # no validation on b_out (it is hidden from the protocol); sign propagates
    assert censor_net(100.0, 300.0, -60.0, 2, refill=True) == pytest.approx(-320.0)


def test_censor_net_zero_fee_and_bond_is_free_censorship():
    assert censor_net(0.0, 0.0, 60.0, 10, refill=True) == pytest.approx(600.0)


def test_censor_net_determinism():
    args = (100.0, 300.0, 60.0, 20)
    assert censor_net(*args, refill=False) == censor_net(*args, refill=False)
    assert censor_net(*args, refill=True, slash_mode="full") == censor_net(
        *args, refill=True, slash_mode="full")


def test_censor_net_scales_linearly_in_events():
    base = censor_net(100.0, 300.0, 60.0, 1, refill=True)
    assert censor_net(100.0, 300.0, 60.0, 10, refill=True) == pytest.approx(10 * base)


# ---------------------------------------------------------------------------
# critical_fee_capped
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("b_out", [1.0, 30.0, 60.0, 123.456, 500.0])
def test_critical_fee_capped_equals_b_out(b_out):
    # the smallest fee that makes a single capped event unprofitable is B_out
    cf = critical_fee_capped(b_out)
    assert cf == pytest.approx(b_out, abs=1e-6)


def test_critical_fee_capped_zero_b_out():
    assert critical_fee_capped(0.0) == pytest.approx(0.0, abs=1e-12)


def test_critical_fee_capped_is_indeed_critical():
    b_out = 60.0
    cf = critical_fee_capped(b_out)
    assert censor_net(cf * 0.99, cf * 3, b_out, 1) > 0
    assert censor_net(cf * 1.01, cf * 3, b_out, 1) < 0


# ---------------------------------------------------------------------------
# critical_margin_full
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("b_out", [120.0, 150.0, 200.0, 300.0, 500.0])
def test_critical_margin_full_is_b_out_minus_fee(b_out):
    fee = 100.0
    m = critical_margin_full(fee, b_out)
    assert m == pytest.approx(b_out - fee, abs=1e-6)


def test_critical_margin_full_zero_when_fee_meets_b_out():
    # no margin is needed when the fee alone already deters
    assert critical_margin_full(100.0, 100.0) == pytest.approx(0.0, abs=1e-9)


def test_critical_margin_full_zero_when_fee_exceeds_b_out():
    # fee above B_out: censoring is unprofitable even with zero margin
    assert critical_margin_full(200.0, 60.0) == pytest.approx(0.0, abs=1e-9)


def test_critical_margin_full_is_indeed_critical():
    fee, b_out = 100.0, 300.0
    m = critical_margin_full(fee, b_out)
    assert censor_net(fee, fee + m * 0.9, b_out, 1, slash_mode="full") > 0
    assert censor_net(fee, fee + m * 1.1, b_out, 1, slash_mode="full") < 0
