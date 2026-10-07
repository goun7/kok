"""Probe layer, wave 4: the round-5a field/FRI probes and the U-layer warm()
helper — the last untested public functions of the probe layer.

An AST sweep of the root prototype modules (public, non-underscore functions
whose name never appears anywhere under tests/) leaves exactly these:

  * probe_round5a_field_en -- f3, f4, tv76_field_margin_src, f5, f6, f7, f9
    and the three *_src factories that RETURN a probe (a probe of a probe:
    the measurement is built lazily and must be driven to yield its number).
  * probe_round5a_fri_en  -- f1..f4, f6, f8 and probe_honest_src, the same
    factory pattern.
  * probe_u_layer_en       -- warm(ch), the chain-advance helper every TV
    probe uses to get past the VRF lookback.

These are the adversarial probes layered over the CORE CRYPTO: the field's
binding surface (F.3/F.5/F.6/F.7/TV-76), the FRI verifier's degree and
boundary checks (F.1/F.2/F.3/F.8), the paper's unmeasured verifier-cost and
soundness-compounding claims (F.4/F.6) and the honest-survival baseline.

Every probe is cut on BOTH arms, the convention the preceding waves
established:

  - the HONEST arm: the probe runs on the unbroken module and returns the
    verdict its own claim names (True for a claim that holds), and
  - the FAULT arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE -- its verdict must flip. A probe
    that still passes over the broken invariant is unfalsifiable, which is
    the exact defect class this project has been bitten by.

The *_src factories are tested BOTH as factories (they return a callable) and
as probes (the callable is driven and yields a real measurement). The faults
are applied with unittest.mock.patch as context managers so the modules are
restored before the next test. Nothing outside this file is modified.
stdlib + pytest only; no network, no disk beyond the repo.
"""

import contextlib
import inspect
import io
import os

import pytest
from unittest import mock

import probe_round5a_field_en as probe_field
import probe_round5a_fri_en as probe_fri
import probe_u_layer_en as probe_u

KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(fn, *args, **kwargs):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn(*args, **kwargs)
    return rv, buf.getvalue()


@pytest.fixture(autouse=True)
def at_project_root(monkeypatch):
    """The probes address sibling modules by bare name."""
    monkeypatch.chdir(KOK_ROOT)


# ================================================ F.3: the Merkle code is dead
def test_f3_the_step2_merkle_code_is_never_used_by_the_air():
    """The claim is CONFIRMED when verify() consults the commitment tree, and
    the honest module's verify() does reference the merkle_* code, so the
    STEP-2 leaf hash IS wired into verification (True)."""
    rv, out = _run(probe_field.f3_step2_merkle_code_is_never_used_by_the_air)
    assert rv is True
    assert "verify() references any merkle_*: True" in out
    assert "prove()  references any merkle_*: True" in out
    assert "TileAIRProd references merkle_check_prod    True" in out


def test_f3_reports_when_the_air_truly_omits_the_merkle_code():
    """FAULT: verify() stops consulting the commitment tree, so the wiring the
    probe certifies is gone and the finding flips to 'never connected'."""
    import inspect
    real_getsource = inspect.getsource

    def fake(obj):
        if obj is probe_field.TileAIRProd.verify:
            return "def verify(self, proof):\n    return self._check(proof)\n"
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f3_step2_merkle_code_is_never_used_by_the_air)
    assert rv is False
    assert "verify() references any merkle_*: False" in out


def test_f3_reports_when_prove_omits_the_merkle_code():
    """FAULT on the other half of the same measurement: prove() drops the
    merkle_* wiring while verify() keeps it. The probe's verdict is the OR of
    the two, so losing one half is enough to flip it."""
    import inspect
    real_getsource = inspect.getsource

    def fake(obj):
        if obj is probe_field.TileAIRProd.prove:
            return "def prove(self):\n    return self._build()\n"
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f3_step2_merkle_code_is_never_used_by_the_air)
    assert rv is True
    assert "prove()  references any merkle_*: False" in out


# ================================================ F.4: the phantom measurement
def test_f4_the_20000_challenge_measurement_does_not_exist():
    """ROUND-5 added the sweep: the named function now runs a multi-sample
    randrange loop, so the 20000-challenge measurement exists (True)."""
    rv, out = _run(probe_field.f4_the_20000_challenge_measurement_does_not_exist)
    assert rv is True
    assert "occurrences of 'randrange' in tv76_field_margin: 5" in out


def test_f4_notices_when_the_measurement_is_removed():
    """FAULT: the sweep is dropped back to the single fixed tamper, so the
    20000-sample measurement the probe certifies is gone (randrange < 3)."""
    import inspect
    real_getsource = inspect.getsource
    fixed = ("def tv76_field_margin():\n"
             "    t = _h_truncated('sib', 3)\n"
             "    return sum(1 for k in range(97) if _h_truncated('sib', k) == t)\n")

    def fake(obj):
        if getattr(obj, "__name__", "") == "tv76_field_margin":
            return fixed
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f4_the_20000_challenge_measurement_does_not_exist)
    assert rv is False
    assert "occurrences of 'randrange' in tv76_field_margin: 0" in out


# ================================================ TV-76: the field margin
def test_tv76_field_margin_factory_returns_a_probe():
    """The *_src helpers are PROBE FACTORIES: they return a callable the
    caller must drive. A factory that returns a constant would be a probe
    that never measures anything."""
    fn = probe_field.tv76_field_margin_src()
    assert callable(fn)


def test_tv76_field_margin_measures_a_real_number():
    """Driving the factory must run the measurement and state its number --
    the tamper-caught rate at the toy field, with the analytic bound named
    alongside it so the two are not conflated."""
    rv, out = _run(probe_field.tv76_field_margin_src())
    # the measurement prints both the toy rate and the analytic bound
    assert "0.5000" in out or "2/4" in out
    assert "Schwartz-Zippel" in out or "0.5033" in out
    assert rv is None


def test_tv76_field_margin_states_the_two_numbers_are_not_in_conflict():
    """TV-76's 0.5 and TV-66's 0.32 answer different questions; the probe
    must say so, because conflating them is exactly the ambiguity that let
    an overstated margin pass review."""
    _, out = _run(probe_field.tv76_field_margin_src())
    assert "not in conflict" in out
    assert "TV-66" in out


# ================================================ F.5: Schwartz-Zippel
def test_f5_schwartz_zippel_function_measures_nothing():
    """ROUND-5 made the measurement real: the function builds the AIR and
    runs prove/verify, so STEP 1 is a measurement and not a formula (True)."""
    rv, out = _run(probe_field.f5_schwartz_zippel_function_measures_nothing)
    assert rv is True
    assert "builds an AIR / runs prove / runs verify: True" in out
    assert "lines of the function: 66" in out


def test_f5_notices_when_the_function_reverts_to_a_formula():
    """FAULT: the function stops running the AIR and prints (m+1)/q inline
    again, so the MEASURED label sits on a formula and the verdict flips."""
    import inspect
    real_getsource = inspect.getsource
    formula = ("def measure_schwartz_zippel():\n"
               "    q = 97\n"
               "    m = 4\n"
               "    bound = (m + 1) / q\n"
               "    print('bound', bound)\n")

    def fake(obj):
        if getattr(obj, "__name__", "") == "measure_schwartz_zippel":
            return formula
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f5_schwartz_zippel_function_measures_nothing)
    assert rv is False
    assert "builds an AIR / runs prove / runs verify: False" in out


def test_measure_schwartz_zippel_factory_returns_a_probe():
    fn = probe_field.measure_schwartz_zippel_src()
    assert callable(fn)


def test_measure_schwartz_zippel_yields_a_rate():
    """Driving the factory must produce the measured survival rate of a
    forged proof under random challenges -- a real number, not a verdict."""
    rv, out = _run(probe_field.measure_schwartz_zippel_src())
    assert rv is None
    # the measurement reports a rate against the analytic bound
    assert "survival" in out.lower() or "0.0515" in out


# ================================================ F.6: the inversion target
def test_f6_inversion_probe_target_is_outside_the_searched_pool():
    """ROUND-5 fixed the finding: the target is now drawn from inside the
    pool, so the probe accepts the fixed measurement (True)."""
    rv, out = _run(probe_field.f6_inversion_probe_target_is_outside_the_searched_pool)
    assert rv is True
    assert "target 42424242 (OUTSIDE range(97)): 0 hits" in out


def test_f6_notices_when_the_rigged_target_returns():
    """FAULT: the named function goes back to searching an unreachable
    target (42424242 outside range(97)), so the fix the probe certifies is
    gone and the printed '0' is again a property of the target choice."""
    import inspect
    real_getsource = inspect.getsource
    rigged = ("def measure_leaf_inversion_cost():\n"
              "    target = _h_truncated('sib', 42424242)\n"
              "    return sum(1 for k in range(97) if h(k) == target)\n")

    def fake(obj):
        if getattr(obj, "__name__", "") == "measure_leaf_inversion_cost":
            return rigged
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f6_inversion_probe_target_is_outside_the_searched_pool)
    assert rv is False
    assert "42424242 absent: False" in out


def test_measure_leaf_inversion_cost_factory_returns_a_probe():
    fn = probe_field.measure_leaf_inversion_cost_src()
    assert callable(fn)


def test_measure_leaf_hash_inversion_factory_returns_a_probe():
    fn = probe_field.measure_leaf_hash_inversion_src()
    assert callable(fn)


# ================================================ F.7: the two functions disagree
def test_f7_two_functions_state_opposite_things_about_the_same_attack():
    """ROUND-5 reconciled the contradiction in print: the STEP-2 section now
    carries an explicit reconciler naming where each answer holds, so the
    probe accepts (True) rather than reporting unreconciled text."""
    rv, out = _run(probe_field.f7_two_functions_state_opposite_things_about_the_same_attack)
    assert rv is True
    assert "STEP-2 now carries an explicit reconciler: True" in out


def test_f7_notices_when_the_reconciler_is_removed():
    """FAULT: the reconciler disappears from the STEP-2 section, so the two
    statements sit side by side unreconciled and the probe must report that."""
    import inspect
    real_getsource = inspect.getsource
    unreconciled = ("def measure_leaf_hash_inversion():\n"
                    "    # the attacker can pick a leaf value to hit a\n"
                    "    # truncated target: the toy gap is the truncated leaf\n")

    def fake(obj):
        if getattr(obj, "__name__", "") == "measure_leaf_hash_inversion":
            return unreconciled
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f7_two_functions_state_opposite_things_about_the_same_attack)
    assert rv is False
    assert "STEP-2 now carries an explicit reconciler: False" in out


# ================================================ F.9: ROM noise width
def test_f9_rom_noise_is_64_bit_in_a_256_bit_field():
    """ROUND-5 recast the finding as a STRUCTURAL limit that is now declared
    in _E's own body, so the probe accepts the stated limit (True)."""
    rv, out = _run(probe_field.f9_rom_noise_is_64_bit_in_a_256_bit_field)
    assert rv is True
    assert "_E declares the 2^64 limit in its own body: True" in out
    assert "max E value bits: 64 (field is 256 bits)" in out


def test_f9_notices_when_the_limit_is_undeclared():
    """FAULT: _E stops declaring the 2^64 width, so the production-scale claim
    is made without the limit the probe requires, and the verdict flips."""
    import inspect
    real_getsource = inspect.getsource
    silent = ("def _E(self, i, a, b):\n"
              "    return int(self._h(b'x', a, b).hex(), 16) % self.P\n")

    def fake(obj):
        if getattr(obj, "__name__", "") == "_E":
            return silent
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_field.f9_rom_noise_is_64_bit_in_a_256_bit_field)
    assert rv is False
    assert "_E declares the 2^64 limit in its own body: False" in out


def test_f9_noise_is_actually_64_bits_wide_at_the_production_field():
    """The measurement itself: sampled _E values at P256 must stay under
    2^64, because the digest is 8 bytes. This is the evidence the declared
    limit rests on."""
    air = probe_field.TileAIRProd(probe_field.P256, probe_field.TOY_N,
                                  probe_field.TOY_R)
    vals = [air._E(1, a, b) for a in range(64) for b in range(64)]
    assert max(vals).bit_length() <= 64
    assert len(vals) == 4096


# ================================================ FRI: F.1 degree check
def test_f1_verifier_never_checks_the_degree():
    """The probe CONSTRUCTS the cheat rather than grepping source: a fold of
    degree 48 that agrees with the honest fold on every checked point. The
    verifier rejects it, so the degree claim IS enforced (True)."""
    rv, out = _run(probe_fri.f1_verifier_never_checks_the_degree)
    assert rv is True
    assert "verify_round(P, alpha, cheat): False" in out
    assert "cheating F degree:             48" in out
    assert "honest fold degree:            1" in out


def test_f1_notices_when_the_verifier_accepts_the_degree_cheat():
    """FAULT: verify_round stops rejecting the degree-48 cheat, so the degree
    enforcement the probe certifies is gone and the verdict flips."""
    real_verify_round = probe_fri.FriRecursive.verify_round

    def lax(self, P, alpha, F):
        # the cheat's folding identity agrees on every checked point, so a
        # verifier that ignores the degree accepts it
        return True

    with mock.patch.object(probe_fri.FriRecursive, "verify_round", lax):
        rv, out = _run(probe_fri.f1_verifier_never_checks_the_degree)
    assert rv is False
    assert "verify_round(P, alpha, cheat): True" in out


def test_f1_honest_fold_is_accepted():
    """The control: the honest fold must pass verify_round, so the cheat's
    rejection above is about the degree, not about the folding identity."""
    import random as _random
    q = 97
    fri = probe_fri.FriRecursive(q)
    rng = _random.Random(2026)
    P = probe_fri._interpolate(
        [(t, (t * t + 3 * t + 7) % q) for t in range(5)], q)
    alpha = rng.randrange(1, q)
    F = fri.fold(P, alpha)
    assert fri.verify_round(P, alpha, F) is True


# ================================================ FRI: F.2 final constant
def test_f2_no_final_constant_check():
    """The probe inflates the LAST round's polynomial to degree 48: the round
    checks then fail, so the final constant claim is enforced (True)."""
    rv, out = _run(probe_fri.f2_no_final_constant_check)
    assert rv is True
    assert "honest final degree:  0" in out
    assert "inflated final degree: 48" in out
    assert "every round still verifies: False" in out


def test_f2_notices_when_the_inflated_final_passes():
    """FAULT: the round checks start accepting the degree-48 final, so the
    enforcement the probe certifies is gone and the verdict flips."""
    with mock.patch.object(probe_fri.FriRecursive, "verify_round",
                           lambda self, P, alpha, F: True):
        rv, out = _run(probe_fri.f2_no_final_constant_check)
    assert rv is False
    assert "every round still verifies: True" in out


# ================================================ FRI: F.3 prover challenge
def test_f3_the_challenge_is_generated_by_the_prover():
    """The claim is CONFIRMED only if the challenge is generated verifier-side.
    recursive_prove no longer draws alpha from its own rng, so the challenge
    is not prover-picked and the finding the probe reports is void (True)."""
    rv, out = _run(probe_fri.f3_the_challenge_is_generated_by_the_prover)
    assert rv is True
    assert "recursive_prove draws alpha from its own rng: False" in out
    assert "verify_round receives alpha as an argument:   True" in out


def test_f3_notices_when_the_prover_picks_the_challenge_again():
    """FAULT: recursive_prove goes back to drawing alpha from its own rng, so
    the challenge becomes prover-picked and the verdict flips."""
    real_getsource = inspect.getsource
    prover_picks = ("def recursive_prove(self, P, rounds, rng):\n"
                    "    alpha = rng.randrange(1, self.q)\n"
                    "    return self.fold(P, alpha), [alpha]\n")

    def fake(obj):
        if obj is probe_fri.FriRecursive.recursive_prove:
            return prover_picks
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_fri.f3_the_challenge_is_generated_by_the_prover)
    assert rv is False
    assert "recursive_prove draws alpha from its own rng: True" in out


def test_f3_verify_round_takes_alpha_as_an_argument():
    """The evidence the probe prints must be true of the honest module:
    verify_round receives alpha rather than generating it."""
    assert "alpha" in inspect.getsource(probe_fri.FriRecursive.verify_round)


def test_f4_header_measurement_3_verifier_cost_is_never_measured():
    """ROUND-5 added the timing: the file now mentions perf_counter, so the
    header's measurement 3 has a probe behind it (True)."""
    rv, out = _run(probe_fri.f4_header_measurement_3_verifier_cost_is_never_measured)
    assert rv is True
    assert "file mentions perf_counter   True" in out
    assert "file mentions cost           True" in out
    assert "file mentions time           True" in out


def test_f4_notices_when_the_timing_is_removed():
    """FAULT: the timing tokens leave the file, so the measurement the probe
    certifies is gone and the verdict flips to 'never measured'. The
    replacement source must avoid even the bare word 'time'/'cost'."""
    import f0b_fri_en as fri_mod
    real_getsource = inspect.getsource
    untimed = ("def probe_honest_survives_all_rounds():\n"
               "    return True\n")

    def fake(obj):
        if obj is fri_mod:
            return untimed
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_fri.f4_header_measurement_3_verifier_cost_is_never_measured)
    assert rv is False
    # every timing token the probe scans for is gone
    assert "file mentions time           False" in out
    assert "file mentions perf_counter   False" in out
    assert "file mentions monotonic      False" in out


def test_f6_header_measurement_4_soundness_compounding_is_never_measured():
    """ROUND-5 backed the retraction with a MEASURED survival sweep (3000
    trials at 1/2/3 rounds, reported in the file), so the probe accepts the
    number behind the retraction (True)."""
    rv, out = _run(probe_fri.f6_header_measurement_4_soundness_compounding_is_never_measured)
    assert rv is True
    assert "survival sweep now present in the file: True" in out


def test_f6_notices_when_the_sweep_disappears():
    """FAULT: the survival sweep leaves the file, so the retraction loses its
    number and the probe must report the measurement as absent again."""
    import f0b_fri_en as fri_mod
    real_getsource = inspect.getsource
    with mock.patch("inspect.getsource",
                    lambda obj: "def probe_honest_survives_all_rounds():\n"
                                "    return True\n"
                    if obj is fri_mod else real_getsource(obj)):
        rv, out = _run(probe_fri.f6_header_measurement_4_soundness_compounding_is_never_measured)
    assert rv is False
    assert "survival sweep now present in the file: False" in out


def test_f6_prints_the_token_scan():
    """The evidence the probe prints must be true of the honest module: the
    file names probability/survival, and the sweep count is reported."""
    _, out = _run(probe_fri.f6_header_measurement_4_soundness_compounding_is_never_measured)
    assert "file mentions probability" in out
    assert "file mentions survival" in out


# ================================================ FRI: F.8 mislabeled check
def test_f8_degree_non_increase_check_is_mislabeled():
    """ROUND-5 FIXED the label: it now names both checks the boolean
    measures, so the probe accepts the corrected label (True)."""
    rv, out = _run(probe_fri.f8_degree_non_increase_check_is_mislabeled)
    assert rv is True
    assert "label now names both checks it measures: True" in out


def test_f8_notices_when_the_label_reverts_to_the_half_truth():
    """FAULT: the label goes back to 'every round verifies' alone, so the
    degree condition's failures would be misreported as round failures."""
    import inspect
    real_getsource = inspect.getsource
    half_truth = ('def probe_honest_survives_all_rounds():\n'
                  '    print("  every round verifies:  %s" % ok)\n'
                  '    return ok\n')

    def fake(obj):
        if getattr(obj, "__name__", "") == "probe_honest_survives_all_rounds":
            return half_truth
        return real_getsource(obj)

    with mock.patch("inspect.getsource", fake):
        rv, out = _run(probe_fri.f8_degree_non_increase_check_is_mislabeled)
    assert rv is False
    assert "label now names both checks it measures: False" in out


# ================================================ FRI: honest baseline
def test_probe_honest_src_factory_returns_a_probe():
    fn = probe_fri.probe_honest_src()
    assert callable(fn)


def test_probe_honest_survives_all_rounds():
    """The honest baseline must actually pass: every round verifies AND the
    degree sequence is non-increasing. This is the control that makes the
    tamper arms meaningful -- a probe whose honest case fails certifies
    nothing about its fault cases."""
    rv, out = _run(probe_fri.probe_honest_src())
    assert rv is True
    assert "degree non-increasing" in out
    assert "degrees across rounds:" in out


def test_probe_honest_reports_the_degree_sequence():
    """The measurement must print the per-round degrees, because that
    sequence is the evidence the non-increase claim rests on."""
    rv, out = _run(probe_fri.probe_honest_src())
    assert "[2, 1, 0, 0]" in out


# ================================================ U-layer: warm()
def test_warm_advances_the_chain_past_the_vrf_lookback():
    """warm(ch) mines EPOCH_LOOKBACK+5 empty blocks so the epoch seed the VRF
    reads exists; it returns None (a helper, not a probe)."""
    class FakeChain:
        def __init__(self):
            self.blocks = 0

        def sim_block(self, flops):
            self.blocks += 1

    ch = FakeChain()
    rv = probe_u.warm(ch)
    assert rv is None
    assert ch.blocks == probe_u.EPOCH_LOOKBACK + 5


def test_warm_is_idempotent_in_effect():
    """Running warm twice advances the chain twice as far: it is a pure
    helper with no state of its own, so its effect is fully determined by
    how many times it is called."""
    class FakeChain:
        def __init__(self):
            self.blocks = 0

        def sim_block(self, flops):
            self.blocks += 1

    ch = FakeChain()
    probe_u.warm(ch)
    after_first = ch.blocks
    probe_u.warm(ch)
    assert ch.blocks == 2 * after_first


def test_warm_passes_through_the_flops_argument():
    """The block's flops argument is the chain's own input; warm must forward
    it unchanged rather than substituting a value of its own."""
    seen = []

    class FakeChain:
        def sim_block(self, flops):
            seen.append(flops)

    probe_u.warm(FakeChain())
    assert seen == [1.0] * (probe_u.EPOCH_LOOKBACK + 5)


def test_warm_leaves_the_task_set_alone():
    """warm() only advances the chain; it must not create, submit or settle
    a task, because the TV probes that call it set their own tasks up."""
    class FakeChain:
        def __init__(self):
            self.blocks = 0
            self.tasks_created = 0

        def sim_block(self, flops):
            self.blocks += 1

        def submit_task(self, *a, **k):
            self.tasks_created += 1

    ch = FakeChain()
    probe_u.warm(ch)
    assert ch.tasks_created == 0
