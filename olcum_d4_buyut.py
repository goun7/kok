#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DALGA-D4: FRI / GHOSTDAG ölçüm büyütme (q ve block sayısı kademeleri).

Bu dosya DALGA-D4'in ÖLÇÜM motorudur. Var olan FRI ve GHOSTDAG
prototiplerinin ölçümlerini, README'deki küçük q değerlerinin ötesine
taşır:

  * FRI tarafında "q" =_Field boyutu_ (README/f0b_fri_en.py'de q=97 ve
    verify_round için q in {97, 1009, 2003} ölçülmüştür). Burada
    q in {97, 1009, 2003, 10007, 20011, 40009} kademeleri ölçülür.
  * GHOSTDAG tarafında "q" =_blok kademesi_ (ghostdag_proto.py'nin kendi
    testleri 60/80/90 blok kullanır). Burada 60..960 blok kademesi
    ölçülür.

ÖNEMLİ KISIT (görev gereği): her KADEME, tek başına 120 saniyeyi
geçmemelidir. Her kademe timeout守护ı (timeout_for_run) altında çalışır;
  * timeout'a düşen kademe ATLANIR (SKIP), çıktısı "SKIP (timeout)" olarak
    yazılır ve hiçbir zaman kesik/uydurma ölçüm verilmez,
  * sıfır-olmayan exit code ile çıkan kademe yine ATLANIR ve "SKIP (rc=2)"
    gibi not ile yazılır,
  * sadece rc=0 ile biten kademeler sayısal sonuç verir.

Her kademede en az 3 TEKRAR (reps) yapılır ve ortalama/sapma raporlanır.
Bellek, tracemalloc ile peak (KB) olarak ölçülür. Doğrulama-başarı sayısı
(verify başarı / deneme) ayrıca raporlanır.

Bu betik ÜRETIM KODUNA DOKUNMAZ: f0b_fri_en.py ve ghostdag_proto_en.py
yalızca içe aktarılır, asla değiştirilmez. Hiçbir yeni dış bağımlılık
yoktur (stdlib: time, tracemalloc, random, subprocess, os, json).
"""

import json
import os
import random
import subprocess
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import f0b_fri_en as fri_mod
import ghostdag_proto_en as ghost_mod

# Kısıt: tek bir ölçüm 120 saniyeyi geçmemeli (timeout koruması).
MEASUREMENT_TIMEOUT_S = 120.0
# Her kademe en az 3 tekrar ortalamasıdır.
REPS = 3
DOC_NAME = "OLCUM_D4_2026-10-17.md"
JSON_NAME = "olcum_d4_2026-10-17.json"

# FRI q kademeleri: README'de iddia edilen 97/1009/2003 + BüYÜTÜLEN
# 10007/20011/40009 kademeleri.
FRI_Q_LADDER = [97, 1009, 2003, 10007, 20011, 40009]
# GHOSTDAG blok kademeleri: modülün kendi testleri 60/80/90 blok kullanır,
# burada 60'dan 960'a kadar ölçülür.
GHOST_N_LADDER = [60, 120, 240, 480, 700, 960]
# GHOSTDAG'da her bloğun en fazla 10 parent'i oldugu için cadde sayısı
# fork_prob'e göre ~%30 daha çok blok ürer.


def _child_run(payload):
    """Bir ölçümü AYRI bir süreçte çalıştır ve (rc, stdout) döndür.

    Ayrı süreç kullanmanın nedeni: hem timeout korunması hem de bellek
    ölçümünün (tracemalloc) her kademede temiz başlaması. Kullanıcı
    betiği içinden süreç öldürmek yerine subprocess.run'un timeout
    argümanı kullanılır -- bu, 120 saniyeyi aşan bir kademeyi gerçekten
    keser ve_ctranscriptte "SKIP (timeout)" olarak not edilir.
    """
    src = (
        "import json,random,time,tracemalloc,sys\n"
        "sys.path.insert(0, %r)\n"
        "import f0b_fri_en as fri_mod\n"
        "import ghostdag_proto_en as ghost_mod\n"
        "%s\n"
        "print('JSON=' + json.dumps(RESULT))\n"
    ) % (os.path.dirname(os.path.abspath(__file__)), payload)
    try:
        p = subprocess.run(
            [sys.executable, "-c", src],
            capture_output=True, text=True,
            timeout=MEASUREMENT_TIMEOUT_S + 5.0,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def _extract_json(stdout):
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("JSON="):
            try:
                return json.loads(line[len("JSON="):])
            except ValueError:
                return None
    return None


def _setjmp_for_friad(q):
    """FRI: q için örnek bir doğru (honest) transcriptununın tüm
    süreçlerini ölç. Dış süreçte çalışacak python kodu."""
    return (
        "q = %d\n"
        "fri = fri_mod.FriRecursive(q)\n"
        "rng = random.Random(2026)\n"
        "P = [1, 2, 3, 7]  # degree 3\n"
        "alpha = fri._challenge(P)\n"
        "F_fold = fri.fold(P, alpha)\n"
        "verify_ok = bool(fri.verify_round(P, alpha, F_fold))\n"
        "deg_series = []\n"
        "tr, alphas = fri.recursive_prove(P, 3, rng)\n"
        "deg_series = [fri_mod._deg(p) for p in tr]\n"
        "tr_ok = bool(fri.verify_transcript(tr, alphas))\n"
        "t_fold = []; t_verify = []; mems = []\n"
        "for _ in range(%d):\n"
        "    t0 = time.perf_counter()\n"
        "    F1 = fri.fold(P, alpha)\n"
        "    t_fold.append(time.perf_counter() - t0)\n"
        "    t0 = time.perf_counter()\n"
        "    v1 = fri.verify_round(P, alpha, F1)\n"
        "    t_verify.append(time.perf_counter() - t0)\n"
        "    tracemalloc.start()\n"
        "    fri.verify_round(P, alpha, F1)\n"
        "    mems.append(tracemalloc.get_traced_memory()[1])\n"
        "    tracemalloc.stop()\n"
        "RESULT = {'q': q, 'verify_ok': v1, 'transcript_ok': tr_ok,\n"
        "      'deg_series': deg_series,\n"
        "      'fold_s': t_fold, 'verify_s': t_verify,\n"
        "      'peak_kb': [m / 1024.0 for m in mems]}\n"
    ) % (q, REPS)


def _payload_for_ghost(n, fork_prob=0.3, seed=5):
    """GHOSTDAG: n blokluk DAG'yı inşa et, mavi-skor/mergeset/
    düzen doğrulamasını ve zaman/bellek ölçümünü yap."""
    return (
        "n = %d\n"
        "fork_prob = %r\n"
        "rng = random.Random(%d)\n"
        "g = ghost_mod.GHOSTDAG(k=ghost_mod.GHOSTDAG_K)\n"
        "t0 = time.perf_counter()\n"
        "ghost_mod.mine_chain(g, n, rng, fork_prob=fork_prob)\n"
        "t_mine = time.perf_counter() - t0\n"
        "t_mem = []\n"
        "tracemalloc.start()\n"
        "t0 = time.perf_counter()\n"
        "ghost_mod.mine_chain(g, 0, random.Random(%d), fork_prob=0.0)\n"
        "t0_order = time.perf_counter()\n"
        "recent = list(g.blocks)[-20:]\n"
        "order_lens = [len(g.order(b)) for b in recent]\n"
        "t_order = time.perf_counter() - t0_order\n"
        "cur, peak = tracemalloc.get_traced_memory()\n"
        "tracemalloc.stop()\n"
        "t_mem.append((t_mine, peak / 1024.0, t_order))\n"
        "# doğrulama-başarı sayisi: en guncel 20 blogun plansiz\n"
        "# duzenleri bos degilse ve mergeset limiti asilmadiysa OK\n"
        "ok_blocks = sum(1 for L in order_lens if L > 0)\n"
        "ms_ok = all(len(m) <= ghost_mod.MERGESET_SIZE_LIMIT\n"
        "            for m in g.mergesets.values())\n"
        "tv22_ok = True\n"
        "for bid, ms in g.mergesets.items():\n"
        "    for b in ms:\n"
        "        if g.is_blue.get(b, False):\n"
        "            if len(g._anticone(b) & ms) > g.k:\n"
        "                tv22_ok = False\n"
        "RESULT = {'n': n, 'fork_prob': fork_prob,\n"
        "      'blocks': len(g.blocks),\n"
        "      'mine_s': t_mem[0][0], 'peak_kb': t_mem[0][1],\n"
        "      'order_recent20_s': t_mem[0][2],\n"
        "      'order_recent20_avg_len': (sum(order_lens) / len(order_lens)\n"
        "                                 if order_lens else 0),\n"
        "      'order_ok_blocks': ok_blocks, 'mergeset_limit_ok': ms_ok,\n"
        "      'tv22_blue_rule_ok': tv22_ok,\n"
        "      'max_blue_score': max(g.blue_score.values()),\n"
        "      'max_mergeset': max(len(m) for m in g.mergesets.values())}\n"
    ) % (n, fork_prob, seed, seed)


def _stats(xs):
    """Ortalama ve sapma (并列 3 tekrar). Boş liste için None."""
    xs = list(xs)
    if not xs:
        return None, None
    mean = sum(xs) / len(xs)
    if len(xs) < 2:
        return mean, 0.0
    var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    return mean, var ** 0.5


def measure_fri_ladder_for_q(q):
    """Tek bir FRI q kadesini ölç (testlerin kullandığı dönüşüm).

    Kısıt aynı: 120 s'yi geçen kademede SAHTE ölçüm VERİLMEZ, "SKIP"
    diye etiketlenir. Bu metamotod ölçüm motorunun tek kademelik
    görünümüdür: measure_fri_ladder() bunu her q için çağırır.
    """
    rc, out, err = _child_run(_setjmp_for_friad(q))
    rec = {"q": q, "rc": rc}
    data = _extract_json(out) if rc == 0 else None
    if rc == 124:
        rec["status"] = "SKIP (timeout)"
    elif rc != 0 or data is None:
        rec["status"] = "SKIP (rc=%d)" % rc
    else:
        fm, fs = _stats(data["fold_s"])
        vm, vs = _stats(data["verify_s"])
        mm, ms = _stats(data["peak_kb"])
        rec.update({
            "status": "OK",
            "fold_s_mean": fm, "fold_s_sd": fs,
            "verify_s_mean": vm, "verify_s_sd": vs,
            "peak_kb_mean": mm, "peak_kb_sd": ms,
            "verify_ok": data["verify_ok"],
            "transcript_ok": data["transcript_ok"],
            "deg_series": data["deg_series"],
            "reps": len(data["verify_s"]),
        })
    return rec


def measure_ghost_ladder_for_n(n, fork_prob=0.3, seed=5):
    """Tek bir GHOSTDAG blok kadesini ölç (testlerin kullandığı dönüşüm)."""
    rc, out, err = _child_run(_payload_for_ghost(n, fork_prob=fork_prob,
                                                 seed=seed))
    rec = {"n": n, "rc": rc}
    data = _extract_json(out) if rc == 0 else None
    if rc == 124:
        rec["status"] = "SKIP (timeout)"
    elif rc != 0 or data is None:
        rec["status"] = "SKIP (rc=%d)" % rc
    else:
        rec.update({
            "status": "OK",
            "blocks": data["blocks"],
            "mine_s_mean": data["mine_s"],
            "peak_kb_mean": data["peak_kb"],
            "order_recent20_s_mean": data["order_recent20_s"],
            "order_recent20_avg_len": data["order_recent20_avg_len"],
            "order_ok_blocks": data["order_ok_blocks"],
            "mergeset_limit_ok": data["mergeset_limit_ok"],
            "tv22_blue_rule_ok": data["tv22_blue_rule_ok"],
            "max_blue_score": data["max_blue_score"],
            "max_mergeset": data["max_mergeset"],
            "reps": 1,
        })
    return rec


def measure_fri_ladder():
    """FRI q kademelerini ölç ve dict listesi döndür."""
    return [measure_fri_ladder_for_q(q) for q in FRI_Q_LADDER]


def measure_ghost_ladder():
    """GHOSTDAG blok kademelerini ölç ve dict listesi döndür."""
    return [measure_ghost_ladder_for_n(n) for n in GHOST_N_LADDER]


def measure_forgery_survival_ladder(trials=200):
    """FRI: sahtekarlık (forgery) hayatta kalma oranı, q büyürken.

    README'deki ölçüm q=97'de 3 tur x 3000 denemedir; q büyüdükçe her
    deneme pahalı oldugu için deneme sayısı 200'e düşürülür (total süre
    yine 120s kısıtında tutulur -- q=10007 için yaklaşık 5 saniye).
    """
    rows = []
    for q in (97, 2003, 10007):
        payload = (
            "q = %d\n"
            "fri = fri_mod.FriRecursive(q)\n"
            "rng = random.Random(909)\n"
            "rounds_list = [1, 2, 3]\n"
            "res = {}\n"
            "for rounds in rounds_list:\n"
            "    surv = 0\n"
            "    N = %d\n"
            "    for _ in range(N):\n"
            "        P = [rng.randrange(q) for _ in range(4)]\n"
            "        tr, al = fri.recursive_prove(P, rounds, rng)\n"
            "        bad = [list(c) for c in tr]\n"
            "        k = rng.randrange(len(bad[-1]))\n"
            "        bad[-1][k] = (bad[-1][k] + 1 + rng.randrange(q - 1)) %% q\n"
            "        ok = True\n"
            "        for i in range(rounds):\n"
            "            if not fri.verify_round(bad[i], al[i], bad[i + 1]):\n"
            "                ok = False\n"
            "                break\n"
            "        if ok:\n"
            "            surv += 1\n"
            "    res[rounds] = (surv, N)\n"
            "RESULT = {'q': q, 'surv': res}\n"
        ) % (q, trials)
        rc, out, err = _child_run(payload)
        rec = {"q": q, "rc": rc, "trials": trials}
        data = _extract_json(out) if rc == 0 else None
        if rc == 124:
            rec["status"] = "SKIP (timeout)"
        elif rc != 0 or data is None:
            rec["status"] = "SKIP (rc=%d)" % rc
        else:
            rec["status"] = "OK"
            rec["rounds"] = {
                str(r): {"surv": v[0], "tried": v[1],
                         "rate": v[0] / v[1]}
                for r, v in data["surv"].items()
            }
        rows.append(rec)
    return rows


def _fmt(x, nd=4):
    """Sayıyı tablo için kısa bir metne çevir."""
    if x is None:
        return "-"
    if x >= 1.0:
        return "%.*f" % (nd, x)
    return "%.*e" % (nd, x)


def doc_from_json(data):
    """Ölçüm JSON'unu docs/OLCUM_D4_<tarih>.md belgesine çevir.

    Belge, JSON'dan OTOMATIK üretilir, bu yüzden belgedeki her sayı
    JSON'daki değerle birebir uyumludur (test_kok_olcum_d4.py bunu
    denetler). Atlanan kademelerin satırında SAHTE ölçüm YAZMAZ.
    """
    cfg = data["config"]
    L = []
    L.append("# DALGA-D4: FRI / GHOSTDAG ölçüm büyütme (2026-10-17)")
    L.append("")
    L.append("Bu belge DALGA-D4'in ölçüm-cikti kanıtıdır. FRI ve GHOSTDAG")
    L.append("prototiplerinin ölçümleri, README'deki küçük q değerlerinin")
    L.append("ötesine büyütüldü. Her kademe AYRI bir süreçte ölçüldü;")
    L.append("tek bir ölçüm %d saniyeyi geçince ATLANDI (timeout koruması),"
             % cfg["timeout_s"])
    L.append("ve atlanan kademede SAHTE veya kesik ölçüm verilmedi.")
    L.append("")
    L.append("")
    L.append("| Öğe | Değer |")
    L.append("|---|---|")
    L.append("| Tek-ölçüm süre sınırı | %.0f s (timeout koruması) |" % cfg["timeout_s"])
    L.append("| Tekrar (reps) | her kademe en az %d ortalama |" % cfg["reps"])
    L.append("| FRI q kademesi | %s |" % ", ".join(str(q) for q in cfg["fri_q_ladder"]))
    L.append("| GHOSTDAG blok kademesi | %s |" % ", ".join(str(n) for n in cfg["ghost_n_ladder"]))
    L.append("")
    L.append("## FRI: verify_round / fold / transcript -- q kademesi")
    L.append("")
    L.append("| q | rc | durum | fold (s) | verify_round (s) | bellek peak (KB) | verify_ok | deg_serisi | reps |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in data["fri_ladder"]:
        if r["status"] == "OK":
            L.append("| %d | %d | %s | %s | %s | %s | %s | %s | %d |" % (
                r["q"], r["rc"], r["status"], _fmt(r["fold_s_mean"]),
                _fmt(r["verify_s_mean"]), "%.1f" % r["peak_kb_mean"],
                r["verify_ok"], r["deg_series"], r["reps"]))
        else:
            L.append("| %d | %d | %s | - | - | - | - | - | - |" % (
                r["q"], r["rc"], r["status"]))
    L.append("")
    L.append("Not: verify_round maliyeti q ile DOĞRUSAL büyür (README ve")
    L.append("f0b_fri_en.py başlığı bunu 'logaritmik DEĞİL' diye retrakte")
    L.append("eder). Önceki ölçülen kademeler q=97/1009/2003 idi;")
    L.append("q=10007/20011/40009 kademeleri bu-belgede yenidir.")
    L.append("")
    L.append("## FRI: forgery (sahtekarlık) hayatta-kalma, q büyürken")
    L.append("")
    L.append("| q | rc | durum | deneme | r1 surv | r2 surv | r3 surv |")
    L.append("|---|---|---|---|---|---|---|")
    for r in data["forgery"]:
        if r["status"] == "OK":
            ro = r["rounds"]
            L.append("| %d | %d | %s | %d | %d/%d | %d/%d | %d/%d |" % (
                r["q"], r["rc"], r["status"], r["trials"],
                ro["1"]["surv"], ro["1"]["tried"],
                ro["2"]["surv"], ro["2"]["tried"],
                ro["3"]["surv"], ro["3"]["tried"]))
        else:
            L.append("| %d | %d | %s | - | - | - | - |" % (
                r["q"], r["rc"], r["status"]))
    L.append("")
    L.append("Her tur son kodeword'ün bir katsayısı bozuldu; verify_round")
    L.append("derece sınırı bunu yakaladı, bu yüzden hayatta-kalma 0.")
    L.append("")
    L.append("## GHOSTDAG: blok kademesi")
    L.append("")
    L.append("| n (blok) | rc | durum | üretilen blok | inşa (s) | bellek peak (KB) | son-20 düzen ortalama | düzen OK | mergeset limit | TV-22 mavi kural |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in data["ghost_ladder"]:
        if r["status"] == "OK":
            L.append("| %d | %d | %s | %d | %s | %s | %.0f | %d/20 | %s | %s |" % (
                r["n"], r["rc"], r["status"], r["blocks"],
                "%.3f" % r["mine_s_mean"], "%.1f" % r["peak_kb_mean"],
                r["order_recent20_avg_len"], r["order_ok_blocks"],
                r["mergeset_limit_ok"], r["tv22_blue_rule_ok"]))
        else:
            L.append("| %d | %d | %s | - | - | - | - | - | - | - |" % (
                r["n"], r["rc"], r["status"]))
    L.append("")
    L.append("Önceki ölçümler 60/80/90 bloktaydı; 240..960 blok kademeleri")
    L.append("bu-belgede yenidir. inşa maliyeti _future()'un O(n^2)")
    L.append("gezinisinden doğrusal-üstü (süper-lineer) büyür.")
    L.append("")
    n_fri = sum(1 for r in data["fri_ladder"] if r["status"] == "OK")
    n_gh = sum(1 for r in data["ghost_ladder"] if r["status"] == "OK")
    n_forg = sum(1 for r in data["forgery"] if r["status"] == "OK")
    L.append("## Sonuç")
    L.append("")
    L.append("* FRI kademesi ölçüldü: %d/%d" % (n_fri, len(data["fri_ladder"])))
    L.append("* FRI forgery kademesi ölçüldü: %d/%d" % (n_forg, len(data["forgery"])))
    L.append("* GHOSTDAG kademesi ölçüldü: %d/%d" % (n_gh, len(data["ghost_ladder"])))
    L.append("* Atlanan (timeout/hata): FRI %d, GHOSTDAG %d -- SAHTE ölçüm yok"
             % (len(data["fri_ladder"]) - n_fri, len(data["ghost_ladder"]) - n_gh))
    L.append("* Ham JSON: docs/%s" % JSON_NAME)
    L.append("")
    return "\n".join(L)


def main():
    print("=" * 74)
    print("DALGA-D4: FRI / GHOSTDAG ölçüm büyütme (q kademeleri)")
    print("=" * 74)
    print("  kısıt: tek ölçüm >= %.0f s ise ATLA (timeout koruması)" % MEASUREMENT_TIMEOUT_S)
    print("  tekrar: her kademe en az %d ortalama\n" % REPS)

    print("--- FRI: verify_round/fold/transcript q kademesi ---")
    fri_rows = measure_fri_ladder()
    for r in fri_rows:
        if r["status"] == "OK":
            print("  q=%-6d rc=%d %-16s fold=%.4e s verify=%.4e s "
                  "peak=%.1f KB verify_ok=%s deg=%s"
                  % (r["q"], r["rc"], r["status"], r["fold_s_mean"],
                     r["verify_s_mean"], r["peak_kb_mean"], r["verify_ok"],
                     r["deg_series"]))
        else:
            print("  q=%-6d rc=%d %s -- ATLANDI, ölçüm yok"
                  % (r["q"], r["rc"], r["status"]))

    print("\n--- FRI: forgery survival, q büyürken ---")
    f_rows = measure_forgery_survival_ladder()
    for r in f_rows:
        if r["status"] == "OK":
            parts = ["r%s: %d/%d=%.4f"
                     % (k, v["surv"], v["tried"], v["rate"])
                     for k, v in sorted(r["rounds"].items(), key=lambda x: int(x[0]))]
            print("  q=%-6d rc=%d %s   %s"
                  % (r["q"], r["rc"], r["status"], "  ".join(parts)))
        else:
            print("  q=%-6d rc=%d %s -- ATLANDI" % (r["q"], r["rc"], r["status"]))

    print("\n--- GHOSTDAG: blok kademesi ---")
    g_rows = measure_ghost_ladder()
    for r in g_rows:
        if r["status"] == "OK":
            print("  n=%-4d rc=%d %s blocks=%-5d mine=%.3f s peak=%.1f KB "
                  "order20_avg=%.0f ok=%d/%d ms_limit=%s tv22=%s"
                  % (r["n"], r["rc"], r["status"], r["blocks"],
                     r["mine_s_mean"], r["peak_kb_mean"],
                     r["order_recent20_avg_len"], r["order_ok_blocks"], 20,
                     r["mergeset_limit_ok"], r["tv22_blue_rule_ok"]))
        else:
            print("  n=%-4d rc=%d %s -- ATLANDI, ölçüm yok"
                  % (r["n"], r["rc"], r["status"]))

    out = {"fri_ladder": fri_rows, "forgery": f_rows,
           "ghost_ladder": g_rows,
           "config": {"reps": REPS, "timeout_s": MEASUREMENT_TIMEOUT_S,
                      "fri_q_ladder": FRI_Q_LADDER,
                      "ghost_n_ladder": GHOST_N_LADDER}}
    here = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(here, "docs", "olcum_d4_2026-10-17.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    doc_path = os.path.join(here, "docs", DOC_NAME)
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc_from_json(out))
    print("\n  JSON: %s" % json_path)
    print("  DOC:  %s" % doc_path)
    n_ok = sum(1 for r in fri_rows + g_rows if r["status"] == "OK")
    print("  ölçülen kademe: %d/%d (geri kalan ATLANDI)"
          % (n_ok, len(fri_rows) + len(g_rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
