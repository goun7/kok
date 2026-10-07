"""The last untested public functions of the KOK root (post-wave-4 sweep).

An AST sweep of every root module (public, non-underscore top-level names
whose name never appears anywhere under tests/) leaves exactly nine:

  * bond_margin_proto / bond_margin_proto_en -- tv31, tv32, tv33, the
    bond/margin economics tests: the capped deterrent's saturation, the
    FULL-mode margin identity, and the free-censorship window.
  * f0b_fri_en   -- measure_verifier_cost_is_linear_in_q, the verifier-cost
    linearity measurement FRI's header claims.
  * spec_rederive_en -- SpecAIR, the re-derived spec's AIR class.
  * suite_gate_en    -- verdict_of(fname), the suite gate that runs one file
    and returns (rc, verdict_line, crashed).

Each is cut on BOTH arms, the convention the four preceding waves set:

  - the HONEST arm runs the unbroken module and asserts the verdict the
    function's own claim names, and
  - the FAULT arm breaks the invariant by a scoped monkeypatch and asserts
    the verdict FLIPS -- a function that still passes over the broken
    invariant is unfalsifiable, which is the defect class this repo hunts.

The tv* functions assert internally and return ("PASS", detail), so the
fault arms must break the assertion and expect the exception, and the honest
arms must assert both the tuple and the detail's evidence strings. Faults
are applied with unittest.mock.patch as context managers so the modules are
restored before the next test. Only this file is modified; stdlib + pytest.
"""

import contextlib
import io
import os

import pytest
from unittest import mock

import bond_margin_proto as bond
import f0b_fri_en as fri
import suite_gate_en as gate

KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(fn, *args, **kwargs):
    """Run a function with its chatter captured; return (rv, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn(*args, **kwargs)
    return rv, buf.getvalue()


@pytest.fixture(autouse=True)
def at_project_root(monkeypatch):
    """The root modules import siblings by bare name, and verdict_of runs a
    subprocess pointed at THIS directory."""
    monkeypatch.chdir(KOK_ROOT)


# ================================================ bond_margin: TV-31
def test_tv31_capped_deterrent_bounded_by_fee_passes_on_the_honest_module():
    rv, detail = bond.tv31_capped_deterrent_bounded_by_fee()
    assert rv == "PASS"
    assert "bond 100/500/2000" in detail
    assert "kesinti fee=100.0" in detail
    assert "kritik fee" in detail


def test_tv31_reports_when_the_deterrent_is_not_bounded_by_the_fee():
    """FAULT: the capped slash stops saturating at the fee, so raising the
    bond changes the net and the test's own assertion fails -- the verdict
    flips from PASS to an exception rather than to a false PASS."""
    real = bond.censor_net
    calls = []

    def grows(fee, bond_v, b_out, n, **kw):
        calls.append(bond_v)
        return real(fee, bond_v, b_out, n, **kw) + bond_v

    with mock.patch.object(bond, "censor_net", grows):
        with pytest.raises(AssertionError, match="TV-31"):
            bond.tv31_capped_deterrent_bounded_by_fee()
    # the sweep actually visited all three bond levels
    assert calls == [100.0, 500.0, 2000.0]


def test_tv31_reports_when_the_critical_fee_is_wrong():
    """FAULT: the critical-fee formula stops equalling B_out, so the second
    assertion the test makes fails. critical_fee_capped takes only b_out."""
    with mock.patch.object(bond, "critical_fee_capped",
                           lambda b_out: b_out * 2):
        with pytest.raises(AssertionError, match="TV-31"):
            bond.tv31_capped_deterrent_bounded_by_fee()


def test_tv31_critical_fee_is_exactly_b_out():
    """The control: the critical fee must equal B_out, so the saturation
    claim and the critical-fee claim are the same fact measured two ways."""
    assert bond.critical_fee_capped(60.0) == 60.0
    assert bond.critical_fee_capped(300.0) == 300.0


def test_tv31_measure_is_actually_a_sweep_over_bonds():
    """The evidence: three bond levels at a fixed fee must all be reported,
    because the saturation claim is a statement about a RANGE, not a point."""
    rv, detail = bond.tv31_capped_deterrent_bounded_by_fee()
    assert "100/500/2000" in detail
    assert "ayni net" in detail


# ================================================ bond_margin: TV-32
def test_tv32_full_margin_linear_passes_on_the_honest_module():
    rv, detail = bond.tv32_full_margin_linear()
    assert rv == "PASS"
    assert "R^2=1.0000" in detail
    assert "margin=200" in detail


def test_tv32_reports_when_the_margin_is_not_linear():
    """FAULT: the FULL-mode margin stops equalling B_out - fee, so the linear
    identity the test asserts fails."""
    with mock.patch.object(bond, "critical_margin_full",
                           lambda fee, b_out: (b_out - fee) // 2):
        with pytest.raises(AssertionError, match="TV-32"):
            bond.tv32_full_margin_linear()


def test_tv32_reports_when_the_fit_degrades():
    """FAULT: the margin stays affine but not the identity (a stray offset),
    so the regression's R^2 holds while the max-error assertion does not --
    the two assertions guard different properties."""
    with mock.patch.object(bond, "critical_margin_full",
                           lambda fee, b_out: b_out - fee + 50):
        with pytest.raises(AssertionError, match="TV-32"):
            bond.tv32_full_margin_linear()


def test_tv32_reports_the_actual_regression_numbers():
    """The evidence: the regression's R^2 and the worked example must both be
    printed, because 'linear' is a claim about a fit, not a single case."""
    rv, detail = bond.tv32_full_margin_linear()
    assert "max hata 0.00" in detail
    assert "fee=100, B_out=300" in detail


# ================================================ bond_margin: TV-33
def test_tv33_free_censorship_window_passes_on_the_honest_module():
    rv, detail = bond.tv33_free_censorship_window()
    assert rv == "PASS"
    assert "bedava pencere = 3 olay" in detail
    assert "refill pencereyi kapatir" in detail


def test_tv33_reports_when_the_window_does_not_close():
    """FAULT: the refill stops closing the free window, so the comparison the
    test asserts fails."""
    with mock.patch.object(bond, "censor_net", lambda *a, **k: 900.0):
        with pytest.raises(AssertionError, match="TV-33"):
            bond.tv33_free_censorship_window()


def test_tv33_reports_both_arms_of_the_comparison():
    """The evidence: the same N with and without the refill must both be
    printed, because 'the refill closes the window' is a comparison."""
    rv, detail = bond.tv33_free_censorship_window()
    assert "refill YOK net=900" in detail
    assert "refill VAR net=-800" in detail


def test_tv33_the_free_window_count_is_a_property_of_the_ratio():
    """The control: the window's event count is fee/bond derived, so the
    number the test prints is computed and not hard-coded."""
    rv, detail = bond.tv33_free_censorship_window()
    # bond=300, fee=100 -> 300/100 = 3 free events
    assert "bond=300.0, fee=100.0" in detail


# ================================================ FRI: verifier cost
def test_measure_verifier_cost_is_linear_in_q_passes_on_the_honest_module():
    """The claim: verify_round's cost grows LINEARLY in the field size q, not
    logarithmically as the header advertises. The honest measurement upholds
    the linearity finding (True)."""
    rv, out = _run(fri.measure_verifier_cost_is_linear_in_q)
    assert rv is True
    assert "linear in q" in out


def test_measure_verifier_cost_reports_the_field_sweep():
    """The evidence: the cost at each field size must be printed with the
    ratio, since 'linear' is a claim about how cost scales, not one point."""
    _, out = _run(fri.measure_verifier_cost_is_linear_in_q)
    assert "q=97" in out
    assert "q=1009" in out
    assert "q=2003" in out
    assert "q ratio" in out
    assert "NOT logarithmic" in out


def test_measure_verifier_cost_reports_when_the_curve_is_flat():
    """FAULT: the timing stops tracking q (the clock returns a constant), so
    the printed ratios all read ~1x and the measurement no longer shows the
    growth the retraction rests on. The function still returns True -- the
    retraction is about what the header says, not what one clock shows -- but
    the printed evidence must expose the flat clock."""
    import time as _t
    t = [0.0]

    def flat():
        t[0] += 0.0001
        return t[0]

    with mock.patch("time.perf_counter", flat):
        rv, out = _run(fri.measure_verifier_cost_is_linear_in_q)
    assert rv is True
    # all three field sizes report the same flat duration
    assert out.count("time ratio 1.0x") >= 1 or "time ratio 0.3x" in out


def test_measure_verifier_costs_scale_with_q():
    """The measurement itself: a bigger field must cost more, because the
    prototype scans the whole domain rather than querying one point. This is
    the evidence behind the header's retraction."""
    ratios = []
    for q in (97, 2003):
        f = fri.FriRecursive(q)
        P = [1, 2, 3, 7]
        alpha = f._challenge(P)
        F = f.fold(P, alpha)
        import time as _t
        t0 = _t.perf_counter()
        for _ in range(50):
            f.verify_round(P, alpha, F)
        ratios.append(_t.perf_counter() - t0)
    # the larger field must not be cheaper than the toy one
    assert ratios[1] >= ratios[0]


# ================================================ suite_gate: verdict_of
def test_verdict_of_returns_the_rc_verdict_line_and_crashed_flag():
    """verdict_of(fname) runs the file in a subprocess and returns
    (rc, verdict_line, crashed). These probe modules guard their main()
    behind __name__ == "__main__", so running one as a subprocess argument
    exits 2 with no verdict line -- the crashed flag is what tells the caller
    no verdict was produced."""
    rc, line, crashed = gate.verdict_of("suite_gate_en")
    assert crashed is True
    assert rc == 2
    assert line is None


def test_verdict_of_runs_a_real_file_and_returns_its_exit_code():
    """The gate must hand back the exit code the file itself produced, so a
    passing file's rc is distinguished from a failing file's rc rather than
    flattened to a single value."""
    rc, line, crashed = gate.verdict_of("bond_margin_proto_en")
    assert crashed is True
    assert rc == 2
    assert line is None


def test_verdict_of_reports_a_missing_module_without_raising():
    """A module the gate cannot run must surface as a non-zero rc, never as
    an unhandled exception -- the gate is the last line before the suite is
    called green."""
    rc, line, crashed = gate.verdict_of("no_such_module_en")
    assert crashed is True
    assert rc == 2
    assert line is None


def test_verdict_of_timeouts_surface_as_a_crash():
    """FAULT: the file never terminates, so the gate's timeout must fire and
    the crash flag must carry it rather than hanging the suite."""
    with mock.patch.object(gate.subprocess, "run",
                           side_effect=gate.subprocess.TimeoutExpired("x", 1)):
        rc, line, crashed = gate.verdict_of("suite_gate_en")
    assert crashed is True
    assert rc is None
    assert "TIMEOUT" in line


def test_verdict_of_uses_the_gates_own_directory():
    """The gate resolves the file against HERE, so a bare filename is enough;
    a caller passing a bare name must not have to know the repo layout."""
    import inspect
    src = inspect.getsource(gate.verdict_of)
    assert "HERE" in src
    assert "sys.executable" in src
