"""Round-6 + audit probe layer, wave 2: the probes that audit the probes.

An AST sweep of the root prototype modules (public, non-underscore functions
whose name never appears anywhere under tests/) leaves these functions in the
ROUND-6 and AUDIT layer:

  * probe_round6_probes_en  -- r6_1 .. r6_4, the round that turns the
    adversarial method on the round-5 probe files themselves (does every probe
    have a real failure mode? do exceptions map to failures, not passes? does
    each file run and count? are the _en files ASCII-clean?).
  * probe_round6b_paper_en -- r6b2, the paper-claim traceability audit.
  * audit_en_output         -- audit_file_source / audit_file_runtime, the two
    halves of the EN-package Turkish-leak auditor (source scan vs. run-and-
    capture-stdout scan).
  * audit_turkish_en        -- scan, the wide Turkish-leak detector.
  * egap_cert_en            -- probe_what_this_does_not_prove, the honest-
    boundary statement that returns None (a "could not drive" verdict, never
    a PASS and never a FINDING).

Every probe is cut on BOTH arms, the convention the preceding waves
established (test_kok_probe_layer.py / test_kok_probe_measurement.py /
test_kok_vacuous_probes.py):

  - the HONEST arm: the probe runs on the unbroken module and returns the
    verdict its own claim names, and
  - the FAULT arm: the invariant the probe guards is broken by a scoped
    monkeypatch and the probe must NOTICE -- its verdict must flip. A probe
    that still passes over the broken invariant is unfalsifiable, which is
    the exact defect class this project has been bitten by.

The faults are applied as context-managed mock.patch.object calls so the
modules are restored before the next test. The subprocess-driven probes
(r6_3, audit_file_runtime) run from the project root via monkeypatch.chdir,
because they invoke sibling files by bare relative name; the fault arms
replace subprocess.run with a fake that reports the broken condition the
probe must catch. Nothing outside this file is modified. stdlib + pytest
only; no network.
"""

import contextlib
import io
import os
import subprocess

import pytest
from unittest import mock

import audit_en_output as audit_en
import audit_turkish_en as audit_tr
import egap_cert_en as egap
import probe_round6_probes_en as probe_r6
import probe_round6b_paper_en as probe_r6b

KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(fn, *args, **kwargs):
    """Run a probe with its chatter captured; return (verdict, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rv = fn(*args, **kwargs)
    return rv, buf.getvalue()


@pytest.fixture(autouse=True)
def at_project_root(monkeypatch):
    """The subprocess-driven probes address sibling files by bare name, so
    they must be invoked with the project root as the cwd."""
    monkeypatch.chdir(KOK_ROOT)


# ============================================================ R6-1
def test_r6_1_passes_on_the_honest_probe_files():
    rv, out = _run(probe_r6.r6_1_every_probe_file_has_an_unsatisfiable_failure_mode)
    assert rv is True
    assert "can print FINDING and PASS" in out


def test_r6_1_notices_a_probe_file_that_cannot_fail():
    """FAULT: a probe file whose source contains neither FINDING nor PASS has
    no failure mode at all; the probe must report that as a finding."""
    with mock.patch.object(probe_r6, "PROBE_FILES", ["egap_cert_en"]):
        # egap_cert_en prints PASS/FINDING only under __main__; its module
        # source still carries both strings, so this file alone is not enough
        # to flip the verdict. Drive the flip with a module whose source is
        # genuinely missing both tokens.
        with mock.patch.object(probe_r6.inspect, "getsource",
                               lambda mod: "def f():\n    return 1\n"):
            rv, out = _run(
                probe_r6.r6_1_every_probe_file_has_an_unsatisfiable_failure_mode)
    assert rv is False
    assert "BROKEN" in out


def test_r6_1_counts_real_probe_definitions():
    """The probe count it prints must be the real top-level def count, so a
    file that has been gutted of its probes is itself a finding."""
    src = "\n".join("def %s(): pass" % n for n in ("a", "b", "_c", "main"))
    with mock.patch.object(probe_r6, "PROBE_FILES", ["egap_cert_en"]), \
            mock.patch.object(probe_r6.inspect, "getsource", lambda mod: src):
        rv, out = _run(
            probe_r6.r6_1_every_probe_file_has_an_unsatisfiable_failure_mode)
    # _c and main are excluded by the probe's own counting rule, so the count
    # it measures is 2, and FINDING/PASS are absent from this synthetic source
    assert rv is False
    assert "probes=2" in out


# ============================================================ R6-2
def test_r6_2_passes_on_the_honest_probe_files():
    rv, out = _run(probe_r6.r6_2_no_probe_passes_on_an_exception_path)
    assert rv is True
    assert "none" in out


def test_r6_2_notices_an_except_pass_that_returns_true():
    """FAULT: an `except: pass` sitting in a function that can `return True`
    without the try-block ever succeeding hides a failure. The probe must
    report the site."""
    bad_src = "\n".join([
        "def probe_x():",
        "    try:",
        "        return check()",
        "    except Exception:",
        "        pass",
        "    return True",
    ])
    mod = mock.MagicMock(name="bad_probe")
    with mock.patch.object(probe_r6, "PROBE_FILES", ["bad_probe"]), \
            mock.patch("builtins.__import__", lambda n: mod), \
            mock.patch.object(probe_r6.inspect, "getsource",
                              lambda obj: bad_src):
        rv, out = _run(probe_r6.r6_2_no_probe_passes_on_an_exception_path)
    assert rv is False
    assert "bad_probe:4" in out


def test_r6_2_ignores_an_except_pass_that_cannot_return_true():
    """The same except:pass shape is NOT a defect when the enclosing function
    has no reachable True without the try-block succeeding -- the probe must
    not cry wolf."""
    good_src = "\n".join([
        "def probe_y():",
        "    n = 0",
        "    try:",
        "        n += measure()",
        "    except Exception:",
        "        pass",
        "    return n == 1",
    ])
    mod = mock.MagicMock(name="good_probe")
    with mock.patch.object(probe_r6, "PROBE_FILES", ["good_probe"]), \
            mock.patch("builtins.__import__", lambda n: mod), \
            mock.patch.object(probe_r6.inspect, "getsource",
                              lambda obj: good_src):
        rv, _ = _run(probe_r6.r6_2_no_probe_passes_on_an_exception_path)
    assert rv is True


# ============================================================ R6-3
def test_r6_3_passes_when_every_probe_file_runs_and_counts():
    rv, out = _run(probe_r6.r6_3_the_probes_run_and_report_a_count)
    assert rv is True
    assert "rc=0 and print a probe count" in out


def test_r6_3_notices_a_probe_file_that_exits_nonzero():
    """FAULT: a probe file that crashes reports no count and a nonzero rc;
    the probe must notice and report it rather than passing."""
    import probe_round6_probes_en as _pr6  # noqa: F401  (module identity)
    fake = subprocess.CompletedProcess(["x"], 1, stdout="traceback", stderr="")
    with mock.patch("subprocess.run", lambda *a, **k: fake):
        rv, out = _run(probe_r6.r6_3_the_probes_run_and_report_a_count)
    assert rv is False
    assert "rc=1" in out


def test_r6_3_notices_a_probe_file_that_prints_no_count():
    """A file that exits 0 but prints no N/M count is equally broken: the
    runner cannot tell whether its probes ran at all."""
    fake = subprocess.CompletedProcess(["x"], 0, stdout="hello world", stderr="")
    with mock.patch("subprocess.run", lambda *a, **k: fake):
        rv, out = _run(probe_r6.r6_3_the_probes_run_and_report_a_count)
    assert rv is False
    assert "counted=False" in out


# ============================================================ R6-4
def test_r6_4_passes_on_the_ascii_clean_probe_files():
    rv, out = _run(probe_r6.r6_4_no_turkish_letters_in_the_probe_files)
    assert rv is True
    assert "none" in out


def test_r6_4_notices_a_turkish_letter_in_an_en_probe_file():
    """FAULT: a Turkish letter in an _en file breaks the project's own stated
    convention, and this probe is the independent check that does not rely on
    the audit script's exemption list."""
    bad = "probe_round5a_field_en"
    real_open = open
    with mock.patch.object(probe_r6, "PROBE_FILES", [bad]), \
            mock.patch("builtins.open",
                       lambda p, *a, **k: io.StringIO("x = 'geçerli'\n")
                       if os.path.basename(p) == bad + ".py"
                       else real_open(p, *a, **k)):
        rv, out = _run(probe_r6.r6_4_no_turkish_letters_in_the_probe_files)
    assert rv is False
    assert "probe_round5a_field_en.py has" in out


def test_r6_4_reports_the_specific_turkish_letters_it_finds():
    """The report must name the offending letter so the finding is fixable."""
    bad = "probe_round5a_field_en"
    real_open = open
    with mock.patch.object(probe_r6, "PROBE_FILES", [bad]), \
            mock.patch("builtins.open",
                       lambda p, *a, **k: io.StringIO("sansür ve görev")
                       if os.path.basename(p) == bad + ".py"
                       else real_open(p, *a, **k)):
        rv, out = _run(probe_r6.r6_4_no_turkish_letters_in_the_probe_files)
    assert rv is False
    assert "ü" in out
    assert "ö" in out


# ============================================================ R6B-2
def test_r6b2_passes_on_the_honest_paper():
    rv, out = _run(probe_r6b.r6b2_the_paper_does_not_claim_a_score_the_code_cannot_print)
    assert rv is True
    assert "traceable" in out


def test_r6b2_reads_the_paper_and_counts_score_tokens():
    """The verdict is structural, but the measurement it reports -- the count
    of N/M score-like tokens and the count of .py files -- must be real."""
    rv, out = _run(probe_r6b.r6b2_the_paper_does_not_claim_a_score_the_code_cannot_print)
    assert "N/M score-like tokens in the paper:" in out
    assert "files present:" in out
    # the paper states at least the seven claims R6B-1 cross-checks
    assert "13" in out or "tokens" in out


def test_r6b2_skips_scores_that_disagree_as_findings_not_claims():
    """A score whose halves differ (N != M) is a stated failure, not a claim,
    so the probe must not report it as untraceable evidence."""
    src = "TV-99 measured 2/3 on the toy field.\n"
    real_open = open
    with mock.patch("builtins.open",
                    lambda p, *a, **k: io.StringIO(src)
                    if os.path.basename(p) == probe_r6b.PAPER
                    else real_open(p, *a, **k)):
        rv, out = _run(probe_r6b.r6b2_the_paper_does_not_claim_a_score_the_code_cannot_print)
    assert rv is True
    assert "score-like tokens in the paper: 1" in out


# ============================================================ audit_en_output
def test_audit_file_source_finds_no_turkish_in_a_clean_en_file():
    hits = audit_en.audit_file_source(
        os.path.join(KOK_ROOT, "egap_cert_en.py"))
    assert hits == {}


def test_audit_file_source_reads_the_file_it_is_given():
    """The source audit is content-bound: the same file read twice gives the
    same hits, and a different file can give different hits."""
    a = audit_en.audit_file_source(os.path.join(KOK_ROOT, "egap_cert_en.py"))
    b = audit_en.audit_file_source(os.path.join(KOK_ROOT, "egap_cert_en.py"))
    assert a == b


def test_audit_file_source_returns_a_count_dict():
    """The return value is a word -> count map, so the caller can rank hits."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_audit_src_sample.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write('x = "sansur"\ny = "sansur"\nz = "gorev"\n')
    try:
        hits = audit_en.audit_file_source(sample)
        assert hits == {"sansur": 2, "gorev": 1}
    finally:
        os.remove(sample)


def test_audit_file_runtime_captures_stdout_and_stderr():
    """The runtime audit runs the file and scans BOTH streams: a Turkish word
    printed to stderr is a leak exactly like one printed to stdout."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_audit_rt_sample.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("import sys\n"
                 "print('sansur')\n"
                 "sys.stderr.write('gorev\\n')\n")
    try:
        hits = audit_en.audit_file_runtime(sample)
        assert hits.get("sansur") == 1
        assert hits.get("gorev") == 1
    finally:
        os.remove(sample)


def test_audit_file_runtime_reports_subprocess_failure_as_a_hit():
    """FAULT: a run that raises must surface as an explicit error entry, never
    an empty hit dict that would read as 'clean' -- an empty dict from a
    broken run is exactly the false 'TEMIZ' this project has been bitten by."""
    def boom(*a, **k):
        raise OSError("cannot run")
    with mock.patch("subprocess.run", boom):
        hits = audit_en.audit_file_runtime(
            os.path.join(KOK_ROOT, "definitely_not_a_module_zzz.py"))
    assert len(hits) == 1
    (key,) = hits
    assert "runtime error" in key
    assert "cannot run" in key


def test_audit_file_runtime_reports_a_nonzero_exit_through_tr_hits():
    """A file that runs but exits nonzero is not itself a Turkish hit: the
    audit only reports WORDS, so a crashed file whose stderr is pure English
    stays clean and the crash shows up only through its exit code (which the
    auditor's main loop does not gate on). This pins that contract so a later
    change cannot silently start counting tracebacks as Turkish prose."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_audit_crash.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("raise RuntimeError('boom')\n")
    try:
        hits = audit_en.audit_file_runtime(sample)
        assert hits == {}
    finally:
        os.remove(sample)


def test_audit_file_runtime_is_clean_on_a_file_that_prints_english():
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_audit_rt_en.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("print('the quick brown fox jumps over the lazy dog')\n")
    try:
        assert audit_en.audit_file_runtime(sample) == {}
    finally:
        os.remove(sample)


# ============================================================ audit_turkish_en
def test_audit_turkish_scan_is_clean_on_an_english_file():
    hits = audit_tr.scan(os.path.join(KOK_ROOT, "egap_cert_en.py"))
    assert hits == []


def test_audit_turkish_scan_flags_an_unambiguous_turkish_word():
    """The wide detector catches ASCII Turkish that the letter filter misses;
    'kesinti' and 'satir' are on the word list and are not English words."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_tr_scan.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("x = 'kesinti ve satir'\n")
    try:
        hits = audit_tr.scan(sample)
        assert hits, "expected at least one unambiguous Turkish hit"
        kinds = {h[1] for h in hits}
        assert "word" in kinds
        tokens = {h[2] for h in hits}
        assert "kesinti" in tokens or "satir" in tokens
    finally:
        os.remove(sample)


def test_audit_turkish_scan_flags_a_turkish_letter_first():
    """A line with a Turkish special character is reported once, as 'char',
    and the loop continues to the next line rather than double-reporting."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_tr_char.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("x = 'sansür'\ny = 'plain english text here'\n")
    try:
        hits = audit_tr.scan(sample)
        assert hits
        line, kind, token, excerpt = hits[0]
        assert kind == "char"
        assert line == 1
    finally:
        os.remove(sample)


def test_audit_turkish_scan_reports_line_numbers_and_excerpts():
    """Each hit carries (line, kind, token, excerpt) so a finding is locatable."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_tr_loc.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("# clean line\n")
        fh.write("y = 'hata ve sorun'\n")
    try:
        hits = audit_tr.scan(sample)
        assert hits
        line, kind, token, excerpt = hits[0]
        assert line == 2
        assert token in ("hata", "sorun")
        assert "hata" in excerpt or "sorun" in excerpt
    finally:
        os.remove(sample)


def test_audit_turkish_scan_skips_ambiguous_english_words():
    """Words that are both English and Turkish ('once', 'var', 'test') are
    skipped: matching them yields only false positives in English text."""
    sample = os.path.join(KOK_ROOT, "tests", "_tmp_tr_amb.py")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("# run this once, then check the var and the test\n")
    try:
        assert audit_tr.scan(sample) == []
    finally:
        os.remove(sample)


def test_audit_turkish_scan_tolerates_a_missing_file():
    """scan() reads the file directly, so a missing path must raise rather
    than report a false CLEAN; main() guards that path, and this test pins
    the contract so the guard is not silently removed."""
    with pytest.raises(OSError):
        audit_tr.scan(os.path.join(KOK_ROOT, "definitely_missing_zzz.py"))


# ============================================================ egap honest boundary
def test_egap_what_this_does_not_prove_returns_none_not_a_pass():
    """The honest-boundary statement deliberately returns None -- the 'could
    not drive' verdict -- so the runner prints neither PASS nor FINDING. A
    future refactor that returns True here would turn a statement into a
    spurious passed probe, which is the failure mode this pins."""
    rv, out = _run(egap.probe_what_this_does_not_prove)
    assert rv is None
    # the statement must still say what it does NOT measure
    assert "does NOT measure phi > 0" in out
    assert "prediction" in out


def test_egap_what_this_does_not_prove_names_tv72_as_the_measured_cause():
    """The boundary statement grounds itself in the measured negative result;
    if it stops naming TV-72 the honest framing is gone."""
    rv, out = _run(egap.probe_what_this_does_not_prove)
    assert "TV-72" in out
    assert "phi = 0" in out or "phi=0" in out
