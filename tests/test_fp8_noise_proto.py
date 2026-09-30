"""Tests for fp8_noise_proto.py: the simplified FP8 quantizer and noise models.

Covers the quantization grid (subnormal flush, E4M3 vs E5M2, clamp to emax),
the entropy metric, and both noise models' magnitude/floor behaviour, plus
determinism and boundary inputs.
"""

import math

import pytest

from fp8_noise_proto import (
    DELTA,
    FP8_FORMATS,
    entropy_bits,
    fp8_quantize,
    noise_fp8_aware,
    noise_int_model,
    output_tiles,
    quantize_vec,
)


# ---------------------------------------------------------------------------
# fp8_quantize — exact grid points
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("x", [0.0, 1.0, 2.0, 4.0, 64.0, 128.0])
def test_fp8_quantize_fixes_powers_of_two(x):
    assert fp8_quantize(x) == pytest.approx(x)
    assert fp8_quantize(-x) == pytest.approx(-x)


def test_fp8_quantize_represents_simple_decimals():
    assert fp8_quantize(3.0) == pytest.approx(3.0)     # 1.5 * 2^1, m=4/8
    assert fp8_quantize(5.0) == pytest.approx(5.0)     # 1.25 * 2^2, m=2/8
    assert fp8_quantize(1.5) == pytest.approx(1.5)     # m=4/8


def test_fp8_quantize_rounds_to_the_grid():
    # 3-bit mantissa in E4M3 -> steps of 1/8 of the exponent; 1.3 lands on 1.25
    assert fp8_quantize(1.3) == pytest.approx(1.25)
    assert fp8_quantize(1.2) == pytest.approx(1.25)    # 0.2*8=1.6 -> 2 -> 1.25


# ---------------------------------------------------------------------------
# fp8_quantize — boundary values
# ---------------------------------------------------------------------------


def test_fp8_quantize_zero_is_zero():
    assert fp8_quantize(0.0) == 0.0
    assert fp8_quantize(-0.0) == 0.0


@pytest.mark.parametrize("tiny", [1e-10, 1e-6, 1e-4])
def test_fp8_quantize_flushes_subnormals_to_zero(tiny):
    # E4M3 subnormal_min = 2^-9 ~ 0.00195
    assert tiny < FP8_FORMATS["E4M3"]["subnormal_min"]
    assert fp8_quantize(tiny) == 0.0


def test_fp8_quantize_keeps_just_above_the_subnormal_min():
    edge = FP8_FORMATS["E4M3"]["subnormal_min"]
    assert fp8_quantize(edge) == pytest.approx(edge)
    assert fp8_quantize(edge * 0.999) == 0.0


@pytest.mark.parametrize("fmt,emax", [("E4M3", 448.0), ("E5M2", 57344.0)])
def test_fp8_quantize_clamps_overflow_to_emax(fmt, emax):
    assert fp8_quantize(1e30, fmt) == pytest.approx(emax)
    assert fp8_quantize(-1e30, fmt) == pytest.approx(-emax)


def test_fp8_quantize_e5m2_has_a_lower_subnormal_floor():
    # 5e-5 is below E4M3's floor but above E5M2's -> only the latter keeps it
    assert fp8_quantize(5e-5, "E4M3") == 0.0
    kept = fp8_quantize(5e-5, "E5M2")
    assert kept != 0.0
    assert kept == pytest.approx(5.340576171875e-05)


def test_fp8_quantize_is_odd_in_sign():
    for x in (1.3, -2.7, 0.01, -0.01):
        assert fp8_quantize(-x) == pytest.approx(-fp8_quantize(x))


def test_fp8_quantize_output_stays_on_the_grid():
    for x in (-100.0, -1.7, 0.03, 2.9, 55.0, 400.0):
        q = fp8_quantize(x)
        assert q == 0.0 or abs(q) >= FP8_FORMATS["E4M3"]["subnormal_min"]
        assert abs(q) <= FP8_FORMATS["E4M3"]["emax"]


def test_fp8_quantize_determinism():
    for x in (1.3, -2.7, 1e-8, 1e6):
        assert fp8_quantize(x) == fp8_quantize(x)


def test_fp8_quantize_rejects_unknown_format():
    with pytest.raises(KeyError):
        fp8_quantize(1.0, "E7M0")


# ---------------------------------------------------------------------------
# quantize_vec
# ---------------------------------------------------------------------------


def test_quantize_vec_maps_elementwise():
    vals = [0.0, 64.0, 1e-10, 1e6, -3.0]
    assert quantize_vec(vals) == [fp8_quantize(v) for v in vals]
    assert quantize_vec(vals)[2] == 0.0


def test_quantize_vec_empty():
    assert quantize_vec([]) == []


def test_quantize_vec_respects_format():
    assert quantize_vec([1e6, 1e6], "E5M2") == [57344.0, 57344.0]


# ---------------------------------------------------------------------------
# entropy_bits
# ---------------------------------------------------------------------------


def test_entropy_bits_uniform_is_log2_n():
    assert entropy_bits([1, 2, 3, 4]) == pytest.approx(2.0)
    assert entropy_bits([1, 2]) == pytest.approx(1.0)
    assert entropy_bits(list(range(8))) == pytest.approx(3.0)


def test_entropy_bits_identical_values_is_zero():
    assert entropy_bits([7, 7, 7]) == pytest.approx(0.0)


def test_entropy_bits_empty_is_zero():
    assert entropy_bits([]) == pytest.approx(0.0)


def test_entropy_bits_single_value_is_zero():
    assert entropy_bits([42]) == pytest.approx(0.0)


def test_entropy_bits_is_sub_log2_n_and_non_negative():
    data = [1, 1, 1, 2]
    e = entropy_bits(data)
    assert 0.0 <= e < math.log2(2)
    assert e == pytest.approx(0.8112781244591328)


def test_entropy_bits_determinism_and_stability():
    d = [1, 2, 2, 3, 3, 3]
    assert entropy_bits(d) == entropy_bits(d)
    # Shannon entropy is invariant under relabelling
    assert entropy_bits(d) == pytest.approx(entropy_bits([9, 8, 8, 7, 7, 7]))


# ---------------------------------------------------------------------------
# noise_int_model
# ---------------------------------------------------------------------------


def test_noise_int_model_proportional_to_rms():
    # row [3, 4] has RMS sqrt((9+16)/2) = sqrt(12.5) -> sigma = DELTA * sqrt(12.5)
    rms = math.sqrt((3.0 ** 2 + 4.0 ** 2) / 2)
    assert noise_int_model([3.0, 4.0]) == pytest.approx([DELTA * rms] * 2)
    assert noise_int_model([3.0, 4.0])[0] == pytest.approx(1.7677669529663689)


def test_noise_int_model_default_delta():
    rms = math.sqrt((3.0 ** 2 + 4.0 ** 2) / 2)
    assert noise_int_model([3.0, 4.0])[0] == pytest.approx(DELTA * rms)


def test_noise_int_model_custom_delta():
    rms = math.sqrt((3.0 ** 2 + 4.0 ** 2) / 2)
    assert noise_int_model([3.0, 4.0], delta=0.1) == pytest.approx([0.1 * rms] * 2)


def test_noise_int_model_zero_row_is_zero():
    assert noise_int_model([0.0, 0.0, 0.0]) == pytest.approx([0.0, 0.0, 0.0])


def test_noise_int_model_scales_with_magnitude():
    small = noise_int_model([1.0, 1.0])
    large = noise_int_model([100.0, 100.0])
    assert large[0] == pytest.approx(100.0 * small[0])


def test_noise_int_model_uniform_across_the_row():
    row = [1.0, -5.0, 3.0, 12.0]
    sig = noise_int_model(row)
    assert len(sig) == len(row)
    assert all(s == sig[0] for s in sig)


# ---------------------------------------------------------------------------
# noise_fp8_aware
# ---------------------------------------------------------------------------


def test_noise_fp8_aware_applies_the_absolute_floor():
    # zero row: INT-model noise is 0, so the sigma_min floor must show through
    floor = 1.0 * FP8_FORMATS["E4M3"]["subnormal_min"]
    assert noise_fp8_aware([0.0, 0.0], 1.0) == pytest.approx([floor, floor])


def test_noise_fp8_aware_matches_int_model_when_base_dominates():
    # large row: base = DELTA * RMS beats the floor
    assert noise_fp8_aware([100.0, 100.0], 0.001) == pytest.approx(
        noise_int_model([100.0, 100.0]))


def test_noise_fp8_aware_floor_is_magnitude_independent():
    tiny = noise_fp8_aware([1e-6, 1e-6], 1.0)
    zero = noise_fp8_aware([0.0, 0.0], 1.0)
    assert tiny == pytest.approx(zero)


def test_noise_fp8_aware_floor_scales_with_sigma_min():
    a = noise_fp8_aware([0.0], 0.5)[0]
    b = noise_fp8_aware([0.0], 2.0)[0]
    assert b == pytest.approx(4.0 * a)


def test_noise_fp8_aware_e5m2_uses_its_own_subnormal_min():
    floor = 0.5 * FP8_FORMATS["E5M2"]["subnormal_min"]
    assert noise_fp8_aware([0.0], 0.5, fmt="E5M2") == pytest.approx([floor])


# ---------------------------------------------------------------------------
# output_tiles
# ---------------------------------------------------------------------------


def test_output_tiles_dot_product():
    assert output_tiles([[1, 2], [3, 4]], [1, 1]) == [3, 7]
    assert output_tiles([[2, 0, 1]], [1, 1, 1]) == [3]


def test_output_tiles_empty():
    assert output_tiles([], []) == []


def test_output_tiles_scalar_row():
    assert output_tiles([[5]], [2]) == [10]


def test_output_tiles_negative_and_zero():
    assert output_tiles([[-1, 2], [0, 0]], [3, -4]) == [-11, 0]


def test_output_tiles_determinism():
    A = [[1.5, -2.0], [0.25, 4.0]]
    B = [2.0, -0.5]
    assert output_tiles(A, B) == output_tiles(A, B)
