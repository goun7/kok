"""The F0 demand-side tools: f0_demand_discovery.py and f0_candidate_list.py.

Neither had test coverage. They are the roadmap's first phase made concrete --
the rubric that separates a customer KOK can serve from one it cannot, the
TV-37 crossover that decides whether the utility layer can win on price, and
the append-only log that is the project's evidence record. The tests cut:

  - score_candidate: every verdict branch (REJECT / DEFER / PURSUE / WATCH),
    the weights of the five rubric criteria, and that only True counts as
    evidence while None defers and False neither scores nor defers,
  - price_is_competitive: the crossover arithmetic in both directions, the
    exact-boundary strictness, the custom flops_per_Mtoken parameter, and the
    zero/negative mining-rate guard that reports a missing datum instead of
    dividing by it,
  - log_result / log_status: written against a TEMP log (the real
    f0_demand_log.jsonl is never touched), covering the missing-file start,
    the interview/signed counts, the exclusion of EXAMPLE-ILLUSTRATIVE rows
    from the interview count (round-4 #28), and corrupt-line tolerance,
  - f0_candidate_list.score: parity with the real rubric on every shipped
    candidate, and that each candidate's answers are complete over the
    rubric keys; report() prints every candidate.

Stdlib only; the log tests monkeypatch the module's LOG_FILE to tmp_path.
"""

import json

import f0_candidate_list as cl
import f0_demand_discovery as dd
import pytest

ALL_TRUE = {"cheaper_for_existing_job": True, "workload_is_matmul_shaped": True,
            "permissionlessness_matters": True,
            "decision_maker_reachable": True, "switching_cost_is_low": True}
MAX_SCORE = 1.0 + 0.8 + 1.0 + 0.6 + 0.5


def _verdict_class(v):
    return v.split(":")[0]


# ------------------------------------------------------------ score_candidate

def test_score_candidate_rejects_when_neither_buying_reason_applies():
    score, verdict = dd.score_candidate({})
    assert score == 0.0
    assert verdict.startswith("REJECT")
    # a workload fit with neither load-bearing reason is still a reject
    s2, v2 = dd.score_candidate({"workload_is_matmul_shaped": True,
                                 "decision_maker_reachable": True})
    assert s2 == 1.4
    assert v2.startswith("REJECT")


def test_score_candidate_defers_when_evidence_is_missing():
    score, verdict = dd.score_candidate(
        {"cheaper_for_existing_job": True, "decision_maker_reachable": None})
    assert score == 1.0
    assert verdict.startswith("DEFER")
    assert "decision_maker_reachable" in verdict


def test_score_candidate_pursues_above_two_and_names_the_evidenced_reasons():
    score, verdict = dd.score_candidate(ALL_TRUE)
    assert score == MAX_SCORE
    assert verdict.startswith("PURSUE")
    assert "cheaper-for-existing-job" in verdict
    assert "permissionlessness-matters" in verdict


def test_score_candidate_pursues_on_permissionlessness_alone():
    ans = dict(ALL_TRUE, cheaper_for_existing_job=False)
    score, verdict = dd.score_candidate(ans)
    assert score == MAX_SCORE - 1.0
    assert verdict.startswith("PURSUE")
    assert "cheaper-for-existing-job" not in verdict
    assert "permissionlessness-matters" in verdict


def test_score_candidate_watches_a_real_reason_below_the_threshold():
    # a FULL answer set (no None) with a real reason but score < 2.0 -> WATCH
    score, verdict = dd.score_candidate(
        {"cheaper_for_existing_job": True,
         "workload_is_matmul_shaped": True,
         "permissionlessness_matters": False,
         "decision_maker_reachable": False,
         "switching_cost_is_low": False})
    assert score == 1.8
    assert verdict.startswith("WATCH")
    # one criterion over the line by exactly 0.5
    s2, v2 = dd.score_candidate({"cheaper_for_existing_job": True,
                                 "workload_is_matmul_shaped": True,
                                 "permissionlessness_matters": False,
                                 "decision_maker_reachable": False,
                                 "switching_cost_is_low": True})
    assert s2 == 2.3
    assert v2.startswith("PURSUE")


def test_score_candidate_false_neither_scores_nor_defers():
    # False is a NEGATIVE answer, not missing evidence
    score, verdict = dd.score_candidate(
        {"cheaper_for_existing_job": True,
         "workload_is_matmul_shaped": False,
         "permissionlessness_matters": False,
         "decision_maker_reachable": False,
         "switching_cost_is_low": False})
    assert score == 1.0
    assert "DEFER" not in verdict
    assert verdict.startswith("WATCH")


def test_score_candidate_weights_sum_to_the_rubric():
    assert MAX_SCORE == pytest.approx(3.9)
    assert set(dd.RUBRIC) == set(ALL_TRUE)
    assert dd.RUBRIC["cheaper_for_existing_job"]["weight"] == 1.0
    assert dd.RUBRIC["permissionlessness_matters"]["weight"] == 1.0
    assert dd.RUBRIC["workload_is_matmul_shaped"]["weight"] == 0.8
    assert dd.RUBRIC["decision_maker_reachable"]["weight"] == 0.6
    assert dd.RUBRIC["switching_cost_is_low"]["weight"] == 0.5


# ---------------------------------------------------------- price_is_competitive

def test_price_is_competitive_below_the_crossover_can_underbid():
    r = dd.price_is_competitive(current_price_per_Mtoken=4.00,
                                token_price_usd=0.10,
                                reward_per_s_KOK=50.0 * 10.0,
                                flops_per_s=1e17)
    assert r["customer_pays_per_Mtoken"] == 4.00
    assert r["kmin_crossover_token_price_usd"] == pytest.approx(8.0)
    assert r["kok_can_underbid_on_price"] is True
    assert "price-competitive" in r["note"]


def test_price_is_competitive_above_the_crossover_cannot():
    r = dd.price_is_competitive(current_price_per_Mtoken=4.00,
                                token_price_usd=10.0,
                                reward_per_s_KOK=500.0,
                                flops_per_s=1e17)
    assert r["kok_can_underbid_on_price"] is False
    assert r["kmin_crossover_token_price_usd"] == pytest.approx(8.0)
    assert "permissionlessness" in r["note"]


def test_price_is_competitive_is_strict_at_the_boundary():
    r = dd.price_is_competitive(current_price_per_Mtoken=4.00,
                                token_price_usd=8.0,
                                reward_per_s_KOK=500.0,
                                flops_per_s=1e17)
    assert r["kmin_crossover_token_price_usd"] == pytest.approx(8.0)
    assert r["kok_can_underbid_on_price"] is False


def test_price_is_competitive_honours_a_custom_flops_per_mtoken():
    # the round-4 #32 fix: the scenario constant is a parameter. A 10x
    # smaller cost-per-Mtoken lifts the crossover 10x (market_usd_per_FLOP
    # rises, so the token price the mining opportunity cost must beat rises)
    r = dd.price_is_competitive(current_price_per_Mtoken=4.00,
                                token_price_usd=0.10,
                                reward_per_s_KOK=500.0,
                                flops_per_s=1e17,
                                flops_per_Mtoken=1e13)
    assert r["kmin_crossover_token_price_usd"] == pytest.approx(80.0)
    assert r["kok_can_underbid_on_price"] is True


def test_price_is_competitive_reports_a_missing_rate_instead_of_dividing():
    for bad in (0, -1e17):
        r = dd.price_is_competitive(current_price_per_Mtoken=4.00,
                                    token_price_usd=0.10,
                                    reward_per_s_KOK=500.0,
                                    flops_per_s=bad)
        assert r["kmin_crossover_token_price_usd"] is None
        assert r["kok_can_underbid_on_price"] is None
        assert "CANNOT BE MADE" in r["note"]


# ------------------------------------------------------------ the honest log

@pytest.fixture
def log_file(tmp_path, monkeypatch):
    path = tmp_path / "test_demand_log.jsonl"
    monkeypatch.setattr(dd, "LOG_FILE", str(path))
    return path


def test_log_status_reports_not_started_when_the_log_is_absent(tmp_path,
                                                              monkeypatch):
    monkeypatch.setattr(dd, "LOG_FILE", str(tmp_path / "absent.jsonl"))
    st = dd.log_status()
    assert st == {"interviews": 0, "signed": 0, "status": "NOT STARTED"}


def test_log_result_appends_one_entry_per_call(log_file):
    e = dd.log_result("Acme", 2.3, "PURSUE: ...", {"a": 1}, False, "note")
    assert e["candidate"] == "Acme"
    assert e["score"] == 2.3
    assert e["letter_of_intent_signed"] is False
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["candidate"] == "Acme"


def test_log_status_counts_interviews_and_signatures(log_file):
    dd.log_result("Acme", 2.3, "PURSUE", {}, False, "n1")
    dd.log_result("Beta", 1.0, "WATCH", {}, True, "n2")
    st = dd.log_status()
    assert st["interviews"] == 2
    assert st["signed"] == 1
    assert st["status"] == "F0 COMPLETE"


def test_log_status_reports_in_progress_without_a_signature(log_file):
    dd.log_result("Acme", 2.3, "PURSUE", {}, False, "n1")
    st = dd.log_status()
    assert st["interviews"] == 1
    assert st["signed"] == 0
    assert st["status"].startswith("F0 IN PROGRESS")


def test_log_status_excludes_the_worked_example_from_the_interview_count(
        log_file):
    # the round-4 #28 fix: EXAMPLE-ILLUSTRATIVE rows are the file's own seed,
    # not outreach, so they are counted separately and never as an interview
    dd.log_result("EXAMPLE-ILLUSTRATIVE (not a real lead)", 3.9, "PURSUE", {},
                  False, "seeded by the tool itself")
    dd.log_result("Acme", 2.3, "PURSUE", {}, False, "n1")
    st = dd.log_status()
    assert st["interviews"] == 1
    assert st["worked_examples_in_log"] == 1
    assert st["signed"] == 0


def test_log_status_tolerates_a_corrupt_line_and_reports_it(log_file):
    log_file.write_text(
        json.dumps({"candidate": "Acme",
                    "letter_of_intent_signed": False}) + "\n"
        "this line is not json\n")
    st = dd.log_status()
    assert st["interviews"] == 1
    assert st["corrupt_lines_skipped"] == 1
    assert "corrupt_lines_skipped" in st


def test_log_status_skips_blank_lines_and_an_empty_log_is_not_started(log_file):
    log_file.write_text("\n\n")
    st = dd.log_status()
    assert st["interviews"] == 0
    assert st["signed"] == 0
    assert st["status"].startswith("F0 NOT STARTED")


# --------------------------------------------------------- f0_candidate_list

@pytest.mark.parametrize("cand", cl.CANDIDATES)
def test_every_candidate_answers_every_rubric_key(cand):
    assert set(cand["answers"]) == set(cl.RUBRIC_KEYS)
    s, verdict = cl.score(cand["answers"])
    assert isinstance(s, float)
    assert s >= 0.0
    assert _verdict_class(verdict) in ("REJECT", "DEFER", "PURSUE", "WATCH")


@pytest.mark.parametrize("cand", cl.CANDIDATES)
def test_the_local_scorer_agrees_with_the_real_rubric(cand):
    # the round-4 #34 fix: this copy had dropped the rubric's DEFER path, so
    # 6/6 candidates got a different verdict class. Parity must hold now.
    local = cl.score(cand["answers"])
    real = dd.score_candidate(cand["answers"])
    assert local[0] == pytest.approx(real[0])
    assert _verdict_class(local[1]) == _verdict_class(real[1])


def test_flashback_labs_defers_on_two_missing_evidence_fields():
    fb = next(c for c in cl.CANDIDATES if "Flashback" in c["name"])
    s, verdict = cl.score(fb["answers"])
    assert s == pytest.approx(2.8)
    assert _verdict_class(verdict) == "DEFER"
    assert "decision_maker_reachable" in verdict
    assert "switching_cost_is_low" in verdict


def test_score_rejects_when_neither_reason_applies():
    s, verdict = cl.score({"workload_is_matmul_shaped": True})
    assert s == 0.8
    assert _verdict_class(verdict) == "REJECT"


def test_score_defers_and_pursues_like_the_rubric():
    # a partial answer set defers on the unanswered keys (absent == None)
    assert _verdict_class(
        cl.score({"cheaper_for_existing_job": True})[1]) == "DEFER"
    defer = cl.score({"cheaper_for_existing_job": True,
                      "decision_maker_reachable": None})
    assert _verdict_class(defer[1]) == "DEFER"
    assert _verdict_class(cl.score(dict(ALL_TRUE))[1]) == "PURSUE"


def test_report_prints_every_candidate(capsys):
    assert cl.report() is None
    out = capsys.readouterr().out
    for cand in cl.CANDIDATES:
        assert cand["name"] in out
    # one scored block per candidate
    assert out.count("score ") >= len(cl.CANDIDATES)
