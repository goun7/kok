#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for probe_live_demand_en.py — TV-72 canli phi=0 olcumu.

probe_live_demand_en.py tek bir genel fonksiyon icerir (main) ve bu dosya
ONUN tum dallarini keser:

    main():
      dal 1: import pass_sim_en (stdout yutularak) → PEARL alinir
      dal 2: PEARL yok (getattr None) → "dict not found" → False
      dal 3: rev_day veya cost_day ANAHTARI YOK → "NOT AVAILABLE" → False
      dal 3b (BULGU): anahtar var ama degeri None → satir 58-60 None-guard'indan
             once TypeError verir (bu dosya gercek davranisi belgeler;
             production koduna dokunulmadi)
      dal 4: cost_day <= 0 (ROUND-4/6 guard: cost=0 eskiden 1.6e15 gibi
             cop bir oran uretiyordu) → False
      dal 5: her iki deger gecerli → oran basılır, True doner
      alt dal: denominator cizgisi cost>0'a gore degisir
      alt dal: ROUND-6 FAIL mesaji yalniz veri eksikken basilir
    (__main__): sys.exit(0 if ok else 1)

TEST YONTEMI (Kural-4: saf in-memory): main() iceride `import pass_sim_en`
yapar. Python once sys.modules'e bakar, bu yuzden gercek diski okumadan
once sahte bir pass_sim_en modulu sys.modules'e enjekte edilir
(monkeypatch.setitem ile, otomatik geri-alinir). Hicbir ag/RPC/zincir/
subprocess/dosya-yazimi cagrisi yapilmaz.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
"""

from __future__ import annotations

import contextlib
import io
import sys
import types

import pytest

import probe_live_demand_en as probe


# ------------------------------------------------------------- yardimcilar
def _main_sessiz(monkeypatch=None, fake_pearl=...):
    """main()'i kosturur, stdout'u yutar ve (donus_degeri, cikti_metni) verir.

    fake_pearl:
      ... (varsayilan)  → gercek pass_sim_en modulu kullanilir
      None              → PEARL attribute'u OLMAYAN sahte modul
      {...}             → PEARL'i bu dict olan sahte modul
    """
    buf = io.StringIO()
    if fake_pearl is ...:
        with contextlib.redirect_stdout(buf):
            rc = probe.main()
    else:
        fake = types.ModuleType("pass_sim_en")
        if fake_pearl is not None:
            fake.PEARL = fake_pearl
        monkeypatch.setitem(sys.modules, "pass_sim_en", fake)
        with contextlib.redirect_stdout(buf):
            rc = probe.main()
    return rc, buf.getvalue()


# ================================================================ dal 5: basari
class TestMainBasarili:
    """main() dal 5: gercek PEARL ile rev/cost ikisi de gecerli → True."""

    def test_true_donar(self):
        rc, _ = _main_sessiz()
        assert rc is True

    def test_banner_tv72(self, ):
        _, out = _main_sessiz()
        assert out.startswith("=" * 76)
        assert "TV-72" in out

    def test_pearl_olcum_satirlari(self):
        _, out = _main_sessiz()
        # Basu (arXiv 2606.04819) ile baglanan uc olcum satiri
        assert "GPUs" in out and "320,000" in out
        assert "revenue/day" in out
        assert "cost/day" in out

    def test_oran_basu_1_06_ile_karsilastirilir(self):
        _, out = _main_sessiz()
        # 1625792/1536000 = 1.058... → "%.3f" ile "1.058"
        assert "revenue/cost ratio" in out
        assert "1.058" in out
        assert "Basu measured 1.06" in out

    def test_oran_gercek_degerle_uyusur(self):
        import pass_sim_en as ps
        _, out = _main_sessiz()
        beklenen = ps.PEARL["rev_day"] / ps.PEARL["cost_day"]
        assert f"{beklenen:.3f}" in out

    def test_import_ciktisi_yutulur(self):
        # pass_sim_en import sirasinda kendi raporunu basar ("0. PEARL
        # CALIBRATION..."); main() onu yutmalidir ki TV-72 raporu kirlenmesin
        _, out = _main_sessiz()
        assert "0. PEARL CALIBRATION" not in out
        assert out.startswith("=" * 76)   # ilk satir TV-72 banner'i olmalidir

    def test_phi_tanimi_ve_e_gap_gerekcesi(self):
        _, out = _main_sessiz()
        assert "phi = paid-useful revenue / total compute spend" in out
        assert "Demirel 2026/1492" in out
        assert "E-gap" in out

    def test_durust_sinir_metni(self):
        # probe'un bilinen siniri: phi>0 hala bir TAHMIN, F0 bir adimdir
        _, out = _main_sessiz()
        assert "WHAT WOULD ACTUALLY CLOSE THE ITEM" in out
        assert "F0 (demand discovery" in out
        assert "not confirmed" in out

    def test_measured_negative_ifadesi(self):
        _, out = _main_sessiz()
        assert "MEASURED NEGATIVE" in out

    def test_denominator_bagli_govdesi(self):
        # cost_day > 0 oldugu icin denominator satiri "IS bound" verir
        _, out = _main_sessiz()
        assert "the denominator IS bound here" in out

    def test_round6_fail_basilmaz(self):
        # basarili yolda ROUND-6 FAIL mesaji ASLA basilamaz
        _, out = _main_sessiz()
        assert "ROUND-6: FAIL" not in out


# ================================================================ dal 2: PEARL yok
class TestMainPearlYok:
    """main() dal 2: pass_sim_en'de PEARL yok → False."""

    def test_false_donar(self, monkeypatch):
        rc, _ = _main_sessiz(monkeypatch, fake_pearl=None)
        assert rc is False

    def test_dict_not_found_mesaji(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch, fake_pearl=None)
        assert "PEARL calibration dict not found in pass_sim_en; aborting." in out

    def test_kisa_cikis(self, monkeypatch):
        # erken donus: WHAT THIS CHANGES bolumune ulasmamali
        _, out = _main_sessiz(monkeypatch, fake_pearl=None)
        assert "WHAT WOULD ACTUALLY CLOSE THE ITEM" not in out

    def test_sys_modules_otomatik_geri_alinir(self, monkeypatch):
        # enjeksiyon test sonucusu bozar: onceki deger neyse teardown ile
        # tam olarak o degere donmeli. monkeypatch teardown'i test govdesinden
        # SONRA calistigi icin burada elle try/finally ile olcuyoruz.
        onceki = sys.modules.get("pass_sim_en")
        fake = types.ModuleType("pass_sim_en")
        sys.modules["pass_sim_en"] = fake
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                probe.main()
        finally:
            del sys.modules["pass_sim_en"]
        # fake kaldirildi; gercek modul hala yukluyse o ayni obje olmali
        assert sys.modules.get("pass_sim_en") in (None, onceki)


# ================================================================ dal 3: deger eksik
class TestMainDegerEksik:
    """main() dal 3: rev_day veya cost_day eksik → NOT AVAILABLE → False."""

    @pytest.mark.parametrize("pearl", [
        dict(gpus=100, cost_day=500.0),               # rev_day yok
        dict(gpus=100, rev_day=500.0),                # cost_day yok
        dict(gpus=100),                               # ikisi de yok
    ])
    def test_false_donar(self, monkeypatch, pearl):
        rc, _ = _main_sessiz(monkeypatch, fake_pearl=pearl)
        assert rc is False

    def test_explicit_none_crashes_before_guard(self, monkeypatch):
        # BULGU (dal-kesen testin actigi gercek gap): rev_day/cost_day
        # anahtari var ama degeri None ise satir 58-60'taki formatlama
        # None-guard'indan ONCE calistigi icin TypeError verir. "NOT
        # AVAILABLE" yolu yalnizca anahtar YOKSA yurunur; None deger
        # modulu durdurur. Kural-1: production koduna dokunulmadi —
        # gercek davranis belgelendi (diz.
        from pytest import raises as _r
        with _r(TypeError):
            _main_sessiz(monkeypatch,
                         fake_pearl=dict(gpus=10, rev_day=None, cost_day=500.0))

    def test_explicit_none_cost_crashes_before_guard(self, monkeypatch):
        from pytest import raises as _r
        with _r(TypeError):
            _main_sessiz(monkeypatch,
                         fake_pearl=dict(gpus=10, rev_day=500.0, cost_day=None))

    def test_not_available_mesaji(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch, fake_pearl=dict(gpus=10, cost_day=5.0))
        assert "NOT AVAILABLE" in out
        assert "cannot compare without both fields" in out

    def test_denominator_bagli_degil(self, monkeypatch):
        # cost_day eksik → denominator satiri "NOT available" verir
        _, out = _main_sessiz(monkeypatch, fake_pearl=dict(gpus=10, rev_day=5.0))
        assert "the denominator is NOT available in this configuration" in out

    def test_round6_fail_mesaji(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch, fake_pearl=dict(gpus=10, rev_day=5.0))
        assert "ROUND-6: FAIL" in out

    def test_phi_tanimi_yine_de_basilir(self, monkeypatch):
        # rubric argumani verisiz de yapilir
        _, out = _main_sessiz(monkeypatch, fake_pearl=dict(gpus=10, cost_day=5.0))
        assert "phi = paid-useful revenue / total compute spend" in out


# ================================================================ dal 4: cost <= 0
class TestMainCostGecersiz:
    """main() dal 4: cost_day <= 0 → cop orani onlemek icin False.

    ROUND-4 FIX: eskiden max(1e-9, cost_day) cost_day=0'da 1.6e15 gibi
    bir cop oran uretiyordu ve "Basu measured 1.06" yaninda bir sayi olarak
    basilmasina izin veriyordu. Simdi NOT AVAILABLE / FAIL verir.
    """

    @pytest.mark.parametrize("cost", [0.0, -1.0, -1536000.0, -1e-12])
    def test_false_donar(self, monkeypatch, cost):
        rc, _ = _main_sessiz(monkeypatch,
                             fake_pearl=dict(gpus=100, rev_day=500.0, cost_day=cost))
        assert rc is False

    def test_sifir_cost_cop_uretmez(self, monkeypatch):
        # 1.6e15 gibi bir sayi YERINE NOT AVAILABLE basilir; ratio satiri
        # kendisi bir sayi degil "NOT AVAILABLE" icermeli
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=100, rev_day=500.0, cost_day=0.0))
        ratio_satiri = [s for s in out.splitlines() if "revenue/cost ratio" in s]
        assert ratio_satiri, "ratio satiri basilmali"
        assert "NOT AVAILABLE" in ratio_satiri[0]
        assert "500.0, cost_day=0.0" in ratio_satiri[0]
        # bilimsel-gosterim cop (eski 1.6e15 yuzu) ratio satirinda olmamali
        assert "e+" not in ratio_satiri[0].replace("e+15", "")
        assert "1.6e+15" not in out

    def test_sifir_cost_round6_fail(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=100, rev_day=500.0, cost_day=0.0))
        assert "ROUND-6: FAIL" in out

    def test_negatif_cost_da_reddedilir(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=100, rev_day=500.0, cost_day=-10.0))
        assert "the denominator is NOT available in this configuration" in out

    def test_sifir_cost_payda_ifadesi(self, monkeypatch):
        # guard'i tetikleyen tam kosul: cost > 0 degil
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=1, rev_day=1.0, cost_day=0.0))
        assert "rev_day=1.0, cost_day=0.0" in out


# ================================================================ basari: fake ile
class TestMainFakeBasarili:
    """Basari dali gercek PEARL disinda degerlerle de calisir (enjeksiyon testi)."""

    def test_fake_gecerli_veri_true_donar(self, monkeypatch):
        rc, out = _main_sessiz(monkeypatch,
                               fake_pearl=dict(gpus=100, rev_day=500.0, cost_day=400.0))
        assert rc is True
        assert "revenue/cost ratio" in out

    def test_fake_oran_dogru_hesaplanir(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=10, rev_day=500.0, cost_day=400.0))
        # 500/400 = 1.250
        assert "1.250" in out

    def test_fake_gpus_satirini_formatlar(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=1234567, rev_day=10.0, cost_day=5.0))
        assert "1,234,567" in out

    def test_fake_basari_round6_fail_yok(self, monkeypatch):
        _, out = _main_sessiz(monkeypatch,
                              fake_pearl=dict(gpus=1, rev_day=10.0, cost_day=5.0))
        assert "ROUND-6: FAIL" not in out
        assert "the denominator IS bound here" in out


# ================================================================ __main__ giris
class TestMainGirisNoktasi:
    """Modul __main__ olarak kosturulunca sys.exit(0 if ok else 1) atar.

    runpy ayni surecte (subprocess YOK) calistirir — Kural-4'e uygun.
    """

    def test_basari_systemexit_sifir(self):
        import runpy
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(SystemExit) as ei:
                runpy.run_module("probe_live_demand_en", run_name="__main__")
        assert ei.value.code == 0

    def test_basarisiz_systemexit_bir(self, monkeypatch):
        import runpy
        fake = types.ModuleType("pass_sim_en")     # PEARL yok → main() False
        monkeypatch.setitem(sys.modules, "pass_sim_en", fake)
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(SystemExit) as ei:
                runpy.run_module("probe_live_demand_en", run_name="__main__")
        assert ei.value.code == 1

    def test_giris_result_satiri_basarili(self):
        import runpy
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with pytest.raises(SystemExit):
                runpy.run_module("probe_live_demand_en", run_name="__main__")
        assert "RESULT: STATED" in buf.getvalue()

    def test_giris_result_satiri_basarisiz(self, monkeypatch):
        import runpy
        fake = types.ModuleType("pass_sim_en")
        monkeypatch.setitem(sys.modules, "pass_sim_en", fake)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with pytest.raises(SystemExit):
                runpy.run_module("probe_live_demand_en", run_name="__main__")
        assert "RESULT: FAIL" in buf.getvalue()


# ================================================================ yan etki yoklugu
class TestYanEtkiYoklugu:
    """main() safdir: dosya/ag yan etkisi olusturmaz."""

    def test_main_idempotent_tekrar(self):
        rc1, _ = _main_sessiz()
        rc2, _ = _main_sessiz()
        assert rc1 == rc2 is True

    def test_sys_path_kirlenmez(self):
        # modul import sirasinda sys.path.insert(0, '.') yapar ama
        # sys.path ayni kalmali (idempotent) ve mevcut kok zaten orada
        import pass_sim_en  # noqa: F401  (importu tetikler)
        # tekrarli import sys.path'i degistirmemeli
        n = sys.path.count(".")
        import probe_live_demand_en  # noqa: F401
        assert sys.path.count(".") == n

    def test_stdout_default_false_degil_true(self):
        # main() bool doner (None degil) — sozlesme testi
        rc, _ = _main_sessiz()
        assert isinstance(rc, bool)
