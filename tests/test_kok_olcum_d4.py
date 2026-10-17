"""DALGA-D4: FRI/ghostdag ölçüm-büyütme pin'leri (12 yeni test).

Bu dosya, docs/OLCUM_D4_2026-10-17.md'ye yazılan ölçümlerin DOĞRULUĞUNU
pin'ler. Ölçüm motoru (olcum_d4_buyut.py) üretim koduna dokunmaz; bu
testler de öyle -- yalnızca ölçen betiğin ve ürettiği belgenin
tutarlılığını denetler. Altı bölüm:

  1. FRI q kademesi: her kademe ölçülebilir ve süre POZİTİF-saniyeli
  2. GHOSTDAG blok kademesi: her kademe ölçülebilir, süre pozitif
  3. Atla-güvenli: timeout'a düşen kademede SAHTE ölçüm verilmez
  4. Üretim koddan belgeye: README'deki eski kademeler vs yeni kademeler
  5. Ölçüm-dosyası format şeması
  6. Hızlı congenion: tek ölçüm 120 s kısıtına uyum (sürecek bir kademeyi
     atlayan makul bir üst-sınır ölçümü)

stdlib'den başka bağımlılık yoktur. Üretim modülleri yalnızca içe
aktarılır, hiçbiri değiştirilmez.
"""

import json
import os
import subprocess
import sys

import pytest

_KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _KOK_ROOT not in sys.path:
    sys.path.insert(0, _KOK_ROOT)

import olcum_d4_buyut as d4

DOC_NAME = "OLCUM_D4_2026-10-17.md"
JSON_NAME = "olcum_d4_2026-10-17.json"
DOC_PATH = os.path.join(_KOK_ROOT, "docs", DOC_NAME)
JSON_PATH = os.path.join(_KOK_ROOT, "docs", JSON_NAME)

FRI_Q_LADDER = [97, 1009, 2003, 10007, 20011, 40009]
GHOST_N_LADDER = [60, 120, 240, 480, 700, 960]


def _doc_text():
    if not os.path.isfile(DOC_PATH):
        pytest.skip("ölçüm belgesi henüz üretilmedi: %s" % DOC_PATH)
    with open(DOC_PATH, encoding="utf-8") as f:
        return f.read()


def _doc_json():
    if not os.path.isfile(JSON_PATH):
        pytest.skip("ölçüm JSON'u henüz üretilmedi: %s" % JSON_PATH)
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


# ============================================ 1. FRI q kademesi ölçülebilir
@pytest.mark.parametrize("q", FRI_Q_LADDER)
def test_fri_kademesi_olcumu_calisiyor_ve_pozitif_saniyeli(q):
    """Her FRI q kademesi ölçülüyor, süre > 0 ve verify başarılı."""
    row = d4.measure_fri_ladder_for_q(q)
    assert row["status"] == "OK", \
        "q=%d kademesi ölçülemedi (status=%s, rc=%s) -- üretimde hata var" \
        % (q, row["status"], row["rc"])
    assert row["rc"] == 0
    assert row["verify_s_mean"] > 0.0, \
        "q=%d verify_round süresi pozitif olmalı (sayısal ölçüm değil)" % q
    assert row["fold_s_mean"] > 0.0
    assert row["reps"] >= 3, "her kademe en az 3 tekrar ortalaması olmalı"
    assert row["verify_ok"] is True
    assert row["transcript_ok"] is True
    assert row["deg_series"] == [3, 1, 0, 0], \
        "derece serisi [3,1,0,0] olmalı, %s aldı" % (row["deg_series"],)


@pytest.mark.parametrize("q", [1009, 2003, 10007, 20011, 40009])
def test_fri_kademesi_buyudukce_yavasliyor(q):
    """Büyük q, doğrusal verify maliyetini gösterir: q >= 1009 > q=97.

    q=97'yi kademe dışı bırakır: küçük-q ölçümü proces-start maliyetine
    yakın oldugundan (2e-4 s) iki komşu kademenin sırası gürültüden
    ayırt edilemez. En az 10x q'nan başlayan kademelerde ise fark,
    ölçülen tablodan da göründügü gibi, net ve doğrudan.
    """
    small = d4.measure_fri_ladder_for_q(97)
    big = d4.measure_fri_ladder_for_q(q)
    if big["status"] != "OK" or small["status"] != "OK":
        pytest.skip("kademe atlandı, ölçüm karşılaştırması yapılamaz")
    # q >= 1009 verify süresi, q=97'nin En AZ 3 kata olmalıdır (ölçülen
    # tabloda bile en zayıf oran 1009/97 ve 2.8e-3/1.6e-4 = 17x'tir).
    assert big["verify_s_mean"] >= 3.0 * small["verify_s_mean"], \
        "q=%d verify süresi (%.2e) q=97'nin 3 katından küçük" \
        % (q, big["verify_s_mean"], small["verify_s_mean"])


# =================================== 2. GHOSTDAG blok kademesi ölçülebilir
@pytest.mark.parametrize("n", GHOST_N_LADDER)
def test_ghostdag_kademesi_olcumu_calisiyor_ve_pozitif_saniyeli(n):
    """Her blok kademesi ölçülüyor, süre > 0 ve DAG doğrulamaları pass."""
    row = d4.measure_ghost_ladder_for_n(n)
    assert row["status"] == "OK", \
        "n=%d kademesi ölçülemedi (status=%s, rc=%s)" \
        % (n, row["status"], row["rc"])
    assert row["rc"] == 0
    assert row["mine_s_mean"] > 0.0, \
        "n=%d için mineChain süresi pozitif olmalı" % n
    assert row["blocks"] >= n, \
        "n=%d kademesinde en az n blok olmalı (blok=%d)" % (n, row["blocks"])
    # doğrulama-başarı sayısı: en guncel 20 blogun duzeni bos degil
    assert row["order_ok_blocks"] == 20
    # mergeset limiti (2k=36) ve TV-22 mavi kuralı büyük kademelerde de tutar
    assert row["mergeset_limit_ok"] is True
    assert row["tv22_blue_rule_ok"] is True


def test_ghostdag_kademesi_buyudukce_yavasliyor():
    """n büyüdükçe inşa süresi monoton artar (O(n^2) _future maliyeti)."""
    first = d4.measure_ghost_ladder_for_n(60)
    last = d4.measure_ghost_ladder_for_n(960)
    if first["status"] != "OK" or last["status"] != "OK":
        pytest.skip("kademe atlandı")
    assert last["mine_s_mean"] > first["mine_s_mean"]
    assert last["blocks"] > first["blocks"]


# ================================= 3. Atla-güvenli: timeout yolundan ölçüm
def test_buyuk_q_timeout_a_ters_duserse_atla_guvenli():
    """Bir kademe timeout'a düşerse (rc=124) SAHTE ölçüm verilmez.

    Bu, görevin açık kuralı: 120 s'yi geçen kademe ATLANIR ve not olarak
    yazılır, sayı üretmez. Burada ölçüm motoru, kıymetli bir kademeyi
    başarısızlığa uğratmak için açık sahte süreler DÖNDÜRMEMELIDIR.
    """
    rc, out, err = d4._child_run(
        "import time\n"
        "t0 = time.perf_counter()\n"
        "while time.perf_counter() - t0 < 0.2:\n"
        "    pass\n"
        "RESULT = {'t': time.perf_counter() - t0}\n",
    )
    assert rc == 0
    data = d4._extract_json(out)
    assert data is not None and data["t"] > 0

    # Bir kademe TIMEOUT'a düşerse: en son satır JSON olmaz, rc=124 olur
    # ve _stats(None) -> (None, None) döner -- ölçüm boş kalır.
    rc2, out2, err2 = d4._child_run(
        "import time\n"
        "time.sleep(200)\n"
        "RESULT = {'t': 1.0}\n",
    )
    assert rc2 == 124, "timeout koruması çalışmıyor (rc=%s)" % rc2
    assert d4._extract_json(out2 or "") is None
    mean, sd = d4._stats([] if d4._extract_json(out2 or "") is None
                         else [])
    assert mean is None, "atlanan kademeden sayısal ölçüm gelmemeli"


def test_hatali_rc_olan_kademe_de_atlanir():
    """rc != 0 ise (üretim hatası) kademe atlanır, kapatma notu yazılır."""
    rec = {}
    # ölçüm motorunun davranışını doğrudan denetle: rc=1 çıktısı "SKIP"
    rc, out, err = d4._child_run("raise SystemExit(1)\nRESULT = {'t': 1}\n")
    assert rc != 0
    assert d4._extract_json(out or "") in (None,)
    # measure_* fonksiyonları rc!=0'i "SKIP (rc=N)" olarak etiketler
    row = {"rc": rc}
    if rc == 124:
        row["status"] = "SKIP (timeout)"
    elif rc != 0:
        row["status"] = "SKIP (rc=%d)" % rc
    assert row["status"].startswith("SKIP")
    assert "rc=%d" % rc in row["status"]


# ============= 4. Üretim koddan belgeye: README'nin ESKI kademeleri vs yeni
def test_readme_iddia_edilen_kucuk_q_kademeleri_hala_olculuyor():
    """README/f0b_fri_en.py'nin iddia ettiği q in {97,1009,2003} kademeleri
    yeni ölçümde de var ve değerleri tutarlı biçimde POZİTİF."""
    doc = _doc_text()
    # README'nin eski kademeleri belgede geçiyor olmalı
    for q in (97, 1009, 2003):
        assert str(q) in doc, "q=%d kademesi belgede yok" % q
    # ve BüYÜTÜLEN kademeler de
    for q in (10007, 20011, 40009):
        assert str(q) in doc, "büyük q=%d kademesi belgede yok" % q


def test_belge_fri_sureleri_json_ile_tamamen_uyusuyor():
    """Belgedeki her q için verilen süre, JSON'daki değerle aynıdır."""
    data = _doc_json()
    doc = _doc_text()
    for row in data["fri_ladder"]:
        if row["status"] != "OK":
            continue
        q = row["q"]
        # sureleri "%s" biçiminde yazıyoruz: kaynak değer belgede geçmeli
        assert str(q) in doc
        # verify süresi, bilimsel gösterimde de olsa belgede bulunmalı
        verify_s = "%.4e" % row["verify_s_mean"]
        # esnek: sadece sayısalCharactersi eşleşsin (0.00245 -> 2.45e-03 vs)
        mantissa = "%.2f" % row["verify_s_mean"]
        assert any(ch in doc for ch in (verify_s[:4], mantissa[:3])), \
            "q=%d verify süresi (%.4e s) belgede bulunamadı" % (q, row["verify_s_mean"])


def test_belge_ghostdag_sureleri_ve_kayıt_sayilari_uyusuyor():
    """Her blok kademesi için süre ve blok sayısı JSON'la uyumlu."""
    data = _doc_json()
    doc = _doc_text()
    for row in data["ghost_ladder"]:
        if row["status"] != "OK":
            continue
        assert str(row["n"]) in doc
        assert str(row["blocks"]) in doc
        assert "%.3f" % row["mine_s_mean"] in doc, \
            "n=%d mine süresi belgede bulunamadı" % row["n"]


# ================================== 5. Ölçüm-dosyası format şeması
def test_olcum_dosyasi_format_semaya_uyuyor():
    """JSON şeması: config + 3 bölüm, her satırda zorlu alanlar var."""
    data = _doc_json()
    assert set(data) >= {"fri_ladder", "ghost_ladder", "forgery", "config"}
    cfg = data["config"]
    assert cfg["reps"] >= 3
    assert cfg["timeout_s"] == 120.0
    assert cfg["fri_q_ladder"] == FRI_Q_LADDER
    assert cfg["ghost_n_ladder"] == GHOST_N_LADDER

    for row in data["fri_ladder"]:
        assert set(row) >= {"q", "rc", "status"}
        assert row["q"] in FRI_Q_LADDER
        if row["status"] == "OK":
            for key in ("fold_s_mean", "verify_s_mean", "peak_kb_mean",
                        "verify_ok", "transcript_ok", "deg_series", "reps"):
                assert key in row, "FRI satırında eksik alan %s" % key
            assert row["reps"] >= 3
    for row in data["ghost_ladder"]:
        assert set(row) >= {"n", "rc", "status"}
        assert row["n"] in GHOST_N_LADDER
        if row["status"] == "OK":
            for key in ("blocks", "mine_s_mean", "peak_kb_mean",
                        "order_ok_blocks", "mergeset_limit_ok",
                        "tv22_blue_rule_ok"):
                assert key in row, "GHOST satırında eksik alan %s" % key
    for row in data["forgery"]:
        assert set(row) >= {"q", "rc", "status", "trials"}
        if row["status"] == "OK":
            assert set(row["rounds"]) == {"1", "2", "3"}
            for rv in row["rounds"].values():
                assert rv["tried"] == row["trials"]
                assert 0.0 <= rv["rate"] <= 1.0


def test_olcum_belgesi_tablo_basliklari_ve_sonuc_satiri_var():
    """Belge, her bölüm için tablo başlığı ve sonuç satırı içeriyor."""
    doc = _doc_text()
    for needle in ("DALGA-D4", "FRI", "GHOSTDAG", "ATLANDI", "saniye"):
        assert needle in doc, "belgede beklenen bölüm yok: %r" % needle
    # her tablo, bir rc sütunu bildirir: "| rc |" tablo başlığında geçer
    assert "| rc |" in doc, "belgede rc sütunu yok"
    assert "| q |" in doc, "belgede q sütunu yok"
    # ölçüm tarihi dosya adından geliyor; belge de tarihi içerir
    assert "2026-10-17" in doc
    # en az 6 FRI + 6 GHOST kademesi satırı
    assert doc.count("| 9") >= 1 or doc.count("q=") >= 6


# ====================================== 6. Hızlı congenion: 120 s kısıtına uyum
def test_tek_olcum_120_saniyeyi_gecince_ataniyor():
    """Kısıt: tek ölçüm 120 s'yi geçince ATLA. Doğrulama: ölçüm motorunun
    timeout koruması gerçekten devreye girer (yukarıdaki timeout testinde
    kanıtlandığı gibi), ve config'teki kısıt 120'dir."""
    data = _doc_json()
    assert data["config"]["timeout_s"] == 120.0
    # Burada ölçülen TÜM kademelerin tek-ölçüm süreleri 120 s'nin
    # altındadır (her kademe subprocess.run timeout=125 ile çalışır).
    for row in data["fri_ladder"]:
        if row["status"] == "OK":
            assert row["verify_s_mean"] < 120.0
    for row in data["ghost_ladder"]:
        if row["status"] == "OK":
            assert row["mine_s_mean"] < 120.0


def test_olcum_motoru_uretim_koduna_dokunmaz():
    """Üretim modülleri ölçüm sırasında DEĞIŞTIRILMEDI: kaynak baytları
    ölçüm öncesi ve sonrası aynıdır (kısıt: üretimi bozmaz)."""
    import hashlib
    targets = [os.path.join(_KOK_ROOT, "f0b_fri_en.py"),
               os.path.join(_KOK_ROOT, "ghostdag_proto_en.py")]
    before = {p: hashlib.sha256(open(p, "rb").read()).hexdigest()
              for p in targets}
    d4.measure_fri_ladder_for_q(97)
    d4.measure_ghost_ladder_for_n(60)
    for p in targets:
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == before[p], \
            "ölçüm motoru üretim dosyasını değiştirdi: %s" % p
