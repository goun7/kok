#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for f0b_prod_field_en._h256 (TV-76 production leaf hash).

Covers EVERY branch of the four-way isinstance dispatch of _h256:

    int   -> p.to_bytes(32, "big")          (branch 1)
    str   -> p.encode()                     (branch 2)
    bytes -> p                              (branch 3)
    else  -> repr(p).encode()               (branch 4 / fall-through)

plus the zero-argument call (empty SHA-256), ordering sensitivity, the
bool-is-an-int Python quirk, the bytearray-is-NOT-bytes quirk, the two
 OverflowError boundaries of to_bytes (negative ints and ints >= 2**256),
determinism, the 32-byte length contract, avalanche, and Unicode (Turkish)
input handling.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
Saf in-memory: dis ag/HTTP/DB cagrisi YOK.
"""

import hashlib

import pytest

from f0b_prod_field_en import _h256, _h_truncated, P256


# ------------------------------------------------------------------ helpers
def _sha(*parts):
    """Independent re-implementation of _h256, used as a cross-check oracle."""
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, int):
            h.update(p.to_bytes(32, "big"))
        elif isinstance(p, str):
            h.update(p.encode())
        elif isinstance(p, bytes):
            h.update(p)
        else:
            h.update(repr(p).encode())
    return h.digest()


# ================================================================ branch 1: int
class TestIntBranch:
    """Branch: isinstance(p, int) -> h.update(p.to_bytes(32, 'big'))."""

    @pytest.mark.parametrize("v", [0, 256, P256])
    def test_int_matches_big_endian_32_bytes(self, v):
        assert _h256(v) == hashlib.sha256(v.to_bytes(32, "big")).digest()

    def test_int_zero_is_32_zero_bytes(self):
        # real vector: sha256(b"\x00" * 32)
        assert _h256(0) == hashlib.sha256(b"\x00" * 32).digest()

    def test_int_one_real_vector(self):
        assert (_h256(1).hex() ==
                "ec4916dd28fc4c10d78e287ca5d9cc51ee1ae73cbfde08c6b37324cbfaac8bc5")

    def test_int_256_real_vector(self):
        # 256 needs 2 bytes; to_bytes(32, 'big') left-pads with zeros
        assert _h256(256) == hashlib.sha256((256).to_bytes(32, "big")).digest()

    def test_p256_fits_exactly(self):
        # the secp256k1-style field prime is the largest intended input
        assert _h256(P256) == hashlib.sha256(P256.to_bytes(32, "big")).digest()
        assert P256.to_bytes(32, "big") == P256.to_bytes(32, "big")

    @pytest.mark.parametrize("v", [-1, -P256])
    def test_negative_int_raises_overflow(self, v):
        # SINIR: to_bytes(32, 'big') is unsigned; negative field elements crash.
        with pytest.raises(OverflowError):
            _h256(v)

    @pytest.mark.parametrize("v", [2**256, 1 << 512])
    def test_int_too_big_raises_overflow(self, v):
        # SINIR: 32 bytes cannot hold >= 2**256; no truncation, hard failure.
        with pytest.raises(OverflowError):
            _h256(v)

    def test_boundary_exclusive(self):
        # 2**256 - 1 is the last accepted int; 2**256 is the first rejected
        assert isinstance(_h256(2**256 - 1), bytes)
        with pytest.raises(OverflowError):
            _h256(2**256)


# ================================================================ branch 2: str
class TestStrBranch:
    """Branch: isinstance(p, str) -> h.update(p.encode())."""

    @pytest.mark.parametrize("s,raw", [("a", b"a"), ("", b""), ("0|1", b"0|1")])
    def test_str_matches_utf8_encoding(self, s, raw):
        assert _h256(s) == hashlib.sha256(raw).digest()

    def test_str_a_real_vector(self):
        assert (_h256("a").hex() ==
                "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb")

    @pytest.mark.parametrize("s", ["éğış", "İstanbul"])
    def test_unicode_str_encodes_utf8(self, s):
        # TR/unicode: encode() is UTF-8 by default; multi-byte sequence is hashed
        assert _h256(s) == hashlib.sha256(s.encode("utf-8")).digest()
        assert len(s.encode("utf-8")) >= len(s)

    def test_unicode_str_differs_from_ascii_lookalike(self):
        # 'İ' (U+0130, 2 UTF-8 bytes) is NOT ASCII 'I'
        assert _h256("İ") != _h256("I")
        assert _h256("İ").hex() != _h256("I").hex()

    def test_empty_str_equals_no_args(self):
        # sha256(b"") == sha256 of nothing
        assert _h256("") == _h256()


# ============================================================== branch 3: bytes
class TestBytesBranch:
    """Branch: isinstance(p, bytes) -> h.update(p)."""

    @pytest.mark.parametrize("b", [b"", b"x", bytes(range(256))])
    def test_bytes_passed_through_verbatim(self, b):
        assert _h256(b) == hashlib.sha256(b).digest()

    def test_bytes_x_real_vector(self):
        assert (_h256(b"x").hex() ==
                "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881")

    def test_bytes_not_double_encoded(self):
        # bytes go in raw, not via encode()/repr(): a digest is valid bytes input
        d = _h256(1)
        assert _h256(d) == hashlib.sha256(d).digest()
        assert _h256(d) != _h256(repr(d))

    def test_bytearray_is_NOT_bytes_branch(self):
        # QUIRK: isinstance(bytearray, bytes) is False -> repr() branch
        ba = bytearray(b"x")
        assert _h256(ba) != _h256(b"x")
        assert _h256(ba) == _h256(repr(ba))
        assert _h256(ba) == hashlib.sha256(repr(bytearray(b"x")).encode()).digest()


# ============================================================== branch 4: else
class TestElseBranch:
    """Fall-through branch: h.update(repr(p).encode())."""

    @pytest.mark.parametrize("p", [1.5, None, [1, 2]])
    def test_else_uses_repr(self, p):
        assert _h256(p) == hashlib.sha256(repr(p).encode()).digest()

    def test_float_repr_branch_real_vector_prefix(self):
        # float is not int/str/bytes -> repr('1.5')
        assert _h256(1.5).hex().startswith("9f29a130438b81170b92a426")

    def test_none_repr_branch(self):
        assert _h256(None) == hashlib.sha256(b"None").digest()

    def test_int_one_and_float_one_differ(self):
        # int 1 -> 32-byte big-endian; float 1.0 -> b'1.0'. NOT interchangeable.
        assert _h256(1) != _h256(1.0)
        assert _h256(1.0) == _h256("1.0")

    def test_list_order_matters(self):
        assert _h256([1, 2]) != _h256([2, 1])
        assert _h256([1, 2]) == _h256(repr([1, 2]))


# ==================================================== bool quirk & dispatch order
class TestDispatchOrderAndBool:
    """bool is a subclass of int, so True/False hit the INT branch first."""

    @pytest.mark.parametrize("b,i", [(True, 1), (False, 0)])
    def test_bool_is_int_branch(self, b, i):
        assert _h256(b) == _h256(i)
        assert _h256(b) == hashlib.sha256(i.to_bytes(32, "big")).digest()

    def test_true_real_vector(self):
        assert _h256(True).hex().startswith("ec4916dd28fc4c10")

    def test_false_real_vector(self):
        assert _h256(False).hex().startswith("66687aadf862bd77")

    def test_int_checked_before_repr(self):
        # an int is never routed to repr(): 1 != '1'
        assert _h256(1) != _h256("1")


# ============================================================ multi-part & order
class TestMultipartAndOrdering:
    def test_mixed_parts_real_vector(self):
        assert (_h256(1, "a", b"x").hex() ==
                "31078b4c0f1f3fcf29f08c789ea74968ccb9271bae7d98315142a9ce0772f16c")

    def test_order_sensitive(self):
        assert _h256(1, "a") != _h256("a", 1)
        assert _h256(1, "a", b"x") != _h256(b"x", "a", 1)

    def test_matches_independent_implementation(self):
        assert _h256(1, "a", b"x", None, 1.5) == _sha(1, "a", b"x", None, 1.5)

    def test_prefix_property(self):
        # appending more parts strictly changes the digest (no absorption bug)
        assert _h256(1) != _h256(1, 2)
        assert _h256(1, 2) != _h256(1, 2, 3)

    def test_duplicate_parts(self):
        assert _h256(7, 7) != _h256(7)
        assert _h256(7, 7) == hashlib.sha256((7).to_bytes(32, "big") * 2).digest()


# =============================================================== invariants
class TestInvariants:
    @pytest.mark.parametrize("p", [0, "éğış", P256])
    def test_always_returns_32_bytes(self, p):
        out = _h256(p)
        assert isinstance(out, bytes)
        assert len(out) == 32

    @pytest.mark.parametrize("p", [0, 1.5, "éğış"])
    def test_deterministic(self, p):
        assert _h256(p) == _h256(p) == _h256(p)

    @pytest.mark.parametrize("a,b", [(0, 1), ("a", "b"), (None, True)])
    def test_distinct_inputs_distinct_outputs(self, a, b):
        assert _h256(a) != _h256(b)

    def test_avalanche_single_bit(self):
        # flipping one bit of a bytes input changes the whole digest
        d0 = _h256(b"\x00")
        d1 = _h256(b"\x01")
        assert d0 != d1
        assert sum(bin(x ^ y).count("1") for x, y in zip(d0, d1)) > 32

    def test_no_args_is_empty_sha256(self):
        assert (_h256().hex() ==
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_digest_is_hex_serializable(self):
        assert len(_h256("madencilik").hex()) == 64
        assert set(_h256("madencilik").hex()) <= set("0123456789abcdef")


# ================================================ _h_truncated consumes _h256
class TestTruncatedConsumer:
    """The toy _h_truncated must be the first 8 bytes of the production hash."""

    @pytest.mark.parametrize("p", [42, "éğış"])
    def test_truncation_is_first_eight_bytes(self, p):
        assert _h_truncated(p) == int.from_bytes(_h256(p)[:8], "big")

    @pytest.mark.parametrize("p", [0, "a"])
    def test_truncated_is_64_bit(self, p):
        assert 0 <= _h_truncated(p) < 2**64

    def test_truncated_collides_only_by_design(self):
        # the production hash distinguishes inputs the 64-bit truncation also
        # distinguishes here (no truncation collision among small inputs)
        assert _h_truncated(1) != _h_truncated(2)
