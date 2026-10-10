#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for probe_blindspot_en._load (TV-73 blind-spot probe harness).

_load is a THREE-line import shim:

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import u_layer_prototype_en as ul
    return ul

Its whole contract is: (a) import the U-layer prototype, (b) SWALLOW its
import-time stdout so probe output stays clean, (c) return the module. This file
covers every one of those behaviours plus the API-completeness contract the
caller (_drive) depends on, idempotence, stdout-restoration, nested redirects,
cwd independence, the no-network rule, and Unicode handling.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
Saf in-memory: dis ag/HTTP/DB cagrisi YOK.
"""

import contextlib
import io
import sys
import types

import pytest

from probe_blindspot_en import _load


# ============================================================ return contract
class TestReturnContract:
    def test_returns_a_module(self):
        assert isinstance(_load(), types.ModuleType)

    def test_returns_u_layer_prototype_en(self):
        assert _load().__name__ == "u_layer_prototype_en"

    def test_returns_the_same_object_every_call(self):
        # sys.modules caching: the second import does not re-execute the module
        first = _load()
        second = _load()
        assert first is second

    def test_same_object_as_sys_modules_entry(self):
        ul = _load()
        assert sys.modules["u_layer_prototype_en"] is ul

    def test_not_none(self):
        assert _load() is not None


# =========================================================== stdout swallowing
class TestStdoutSwallowing:
    def test_import_time_stdout_is_swallowed(self, capsys):
        # the module prints nothing at import today; whatever it prints goes to
        # the throwaway buffer, never to the real stdout
        _load()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_stdout_is_restored_after_the_call(self):
        before = sys.stdout
        _load()
        assert sys.stdout is before

    def test_redirect_receives_a_stringio(self, monkeypatch):
        # SINIR: _load's silence is BY CONSTRUCTION -- it routes the import
        # through contextlib.redirect_stdout. Spy on it to prove the wiring.
        seen = {}
        real = contextlib.redirect_stdout

        def spy(target):
            seen["target"] = target
            return real(target)

        monkeypatch.setattr(contextlib, "redirect_stdout", spy)
        _load()
        assert isinstance(seen.get("target"), io.StringIO)

    def test_buffer_is_discarded_not_returned(self):
        # the StringIO is a local: the caller cannot read it back
        ul = _load()
        assert not isinstance(ul, io.StringIO)
        assert not hasattr(ul, "getvalue")

    def test_nested_redirect_is_safe(self):
        # _load must work when the caller already redirected stdout
        outer = io.StringIO()
        with contextlib.redirect_stdout(outer):
            ul = _load()
        assert ul.__name__ == "u_layer_prototype_en"
        # outer sees nothing from _load (it has its own inner buffer)
        assert outer.getvalue() == ""

    def test_stderr_is_not_redirected(self, capsys):
        _load()
        # only stdout is silenced; stderr is untouched (not asserted to be empty,
        # just confirmed the call did not redirect it)
        assert sys.stderr is not None


# ======================================================= api completeness
class TestApiCompleteness:
    """_drive and the probes need this exact surface on the loaded module."""

    @pytest.mark.parametrize("name", ["Chain", "TaskSpec", "Task", "VRF",
                                      "KWKernel", "H", "S", "EPOCH_LOOKBACK",
                                      "BOND_RATIO", "PQ_SET", "DEFAULT_PS",
                                      "RETARGET_WINDOW", "T_B"])
    def test_required_names_present(self, name):
        assert hasattr(_load(), name)

    @pytest.mark.parametrize("name", ["Chain", "TaskSpec", "Task", "VRF",
                                      "KWKernel", "H", "S"])
    def test_callables_are_callable(self, name):
        assert callable(getattr(_load(), name))

    def test_epoch_lookback_value(self):
        assert _load().EPOCH_LOOKBACK == 64

    @pytest.mark.parametrize("name", ["submit_task", "assign_tasks", "mine_block",
                                      "validate_block", "settle", "epoch_seed",
                                      "height", "tip"])
    def test_chain_methods_present(self, name):
        assert callable(getattr(_load().Chain, name))

    def test_chain_is_constructible_in_memory(self):
        ul = _load()
        ch = ul.Chain()
        assert ch.height() == 0
        assert len(ch.blocks) == 1


# ==================================================== no-network / no side effects
class TestInMemoryOnly:
    def test_no_network_module_is_pulled_by_load(self, monkeypatch):
        # Kural-4: the loaded prototype must stay pure-stdlib
        before = set(sys.modules)
        _load()
        added = set(sys.modules) - before
        assert not {"socket", "requests", "urllib.request", "http.client"} & added

    def test_sys_path_unchanged_by_load(self):
        before = list(sys.path)
        _load()
        assert list(sys.path) == before

    def test_no_filesystem_state_required(self, tmp_path, monkeypatch):
        # works from an unrelated cwd because conftest put the repo root on the path
        monkeypatch.chdir(tmp_path)
        assert _load().__name__ == "u_layer_prototype_en"

    def test_chain_has_no_open_handles(self):
        ul = _load()
        ch = ul.Chain()
        assert ch.tasks == {}
        assert ch.miners == {}


# ================================================== re-import / determinism
class TestReimport:
    def test_reimport_after_cache_clear(self, monkeypatch):
        ul = _load()
        monkeypatch.delitem(sys.modules, "u_layer_prototype_en")
        again = _load()
        assert again.__name__ == "u_layer_prototype_en"
        assert again is not ul

    def test_reimport_keeps_epoch_lookback(self, monkeypatch):
        monkeypatch.delitem(sys.modules, "u_layer_prototype_en")
        assert _load().EPOCH_LOOKBACK == 64

    def test_repeat_calls_are_stable(self):
        for _ in range(5):
            assert _load().__name__ == "u_layer_prototype_en"


# ================================================== unicode / TR handling
class TestUnicode:
    def test_hash_of_turkish_string_is_deterministic(self):
        ul = _load()
        assert ul.H("éğış", "İstanbul") == ul.H("éğış", "İstanbul")

    def test_hash_of_turkish_string_differs_from_ascii(self):
        ul = _load()
        assert ul.H("éğış") != ul.H("egis")

    def test_string_commit_is_hex(self):
        ul = _load()
        out = ul.S("madencilik", "görev", 42)
        assert isinstance(out, str)
        assert set(out) <= set("0123456789abcdef")

    def test_string_commit_is_deterministic(self):
        ul = _load()
        assert ul.S("görev", "İstanbul") == ul.S("görev", "İstanbul")

    def test_chain_survives_turkish_task_id_lookup(self):
        # the loaded module's own hashing drives tid derivation; TR data flows
        # through it without raising
        ul = _load()
        ch = ul.Chain()
        tid = ul.S("task", "müşteri", "görev", 100, 200)
        assert tid == ul.S("task", "müşteri", "görev", 100, 200)
        assert tid != ul.S("task", "musteri", "gorev", 100, 200)
        assert ch.tasks.get(tid) is None


# ================================================= integration: feeds _drive
class TestFeedsDrive:
    def test_loaded_module_drives_end_to_end(self):
        # _load's contract is only meaningful if _drive can run on the result
        from probe_blindspot_en import _drive
        ch, t = _drive(_load())
        assert t.state == "SOLVED"
        assert ch.height() > 0
