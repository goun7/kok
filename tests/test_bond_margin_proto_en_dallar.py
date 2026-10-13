#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for bond_margin_proto_en.py — TV-31..TV-33 bond-margin olcumu.

bond_margin_proto_en.py 7 genel sembol icerir ve bu dosya HER BIRININ dalini keser:

    censor_net(fee, bond, b_out, n_events, refill, slash_mode)
        dal 1: slash_mode == "capped"  -> slash = min(cur, fee)
        dal 2: slash_mode == "full"    -> slash = min(cur, bond)
        dal 3: baska her string        -> ValueError (ROUND-4 fix #23)
        alt dal: refill=True/False (her olaydan sonra bond tamamlanir/tuketilir)
    critical_fee_capped(b_out)         bisection: en kucuk fee = B_out
    critical_margin_full(fee, b_out)   bisection: margin = B_out - fee; NEGATIF
                                       sonuc "margin gerekmez" demektir (ROUND-4 fix #25)
    tv31_capped_deterrent_bounded_by_fee()   TV-31: capped'da bond>fee ise yaramaz
    tv32_full_margin_linear()                TV-32: full'da margin dogrusal
    tv33_free_censorship_window()            TV-33: refill yoksa bedava sansur penceresi
    main()                                   3 testi kosturur; hepsi gecer 0,
                                             biri coker 1 doner

Diger test dosyasi (test_bond_margin_proto.py) EN-OLMAYAN modulu hedefler;
bu dosya ozel olarak _en versiyonunun ValueError duzeltmesini, negatif-margin
duzeltmesini ve tv31/tv32/tv33/main fonksiyonlarini keser.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
Saf in-memory: dis ag/HTTP/DB/subprocess cagrisi YOK.
"""

from __future__ import annotations

import contextlib
import io

import pytest

import bond_margin_proto_en as bm


# ================================================================ censor_net: capped
class TestCensorNetCapped:
    """censor_net dal 1: slash_mode='capped' -> slash = min(cur, fee)."""

    def test_tek_olay_fee_kadar_kesilir(self):
        # slash = min(100, 100) = 100 -> net = 60 - 100 = -40
        assert bm.censor_net(100.0, 100.0, 60.0, 1, slash_mode="capped") == pytest.approx(-40.0)

    def test_bond_fee_ustunde_etkisizdir(self):
        # TV-31: cap = fee; bond'u yukseltmek neti degistirmez
        n100 = bm.censor_net(100.0, 100.0, 60.0, 1, slash_mode="capped")
        n500 = bm.censor_net(100.0, 500.0, 60.0, 1, slash_mode="capped")
        n2000 = bm.censor_net(100.0, 2000.0, 60.0, 1, slash_mode="capped")
        assert n100 == pytest.approx(n500) == pytest.approx(n2000)

    def test_bond_fee_altinda_bond_kadar_kesilir(self):
        # min(25, 100) = 25 -> net = 60 - 25 = 35
        assert bm.censor_net(100.0, 25.0, 60.0, 1, slash_mode="capped") == pytest.approx(35.0)

    def test_fee_b_out_altinda_karli(self):
        net = bm.censor_net(10.0, 30.0, 60.0, 5, refill=True, slash_mode="capped")
        assert net == pytest.approx(5 * 60.0 - 5 * 10.0)
        assert net > 0

    def test_refill_her_olayda_fee_keser(self):
        # refill=True: toplam kesinti = n*min(bond,fee) (dogrusal caydiricilik)
        assert bm.censor_net(100.0, 100.0, 60.0, 20, refill=True, slash_mode="capped") == pytest.approx(20 * 60.0 - 20 * 100.0)

    def test_refill_yoksa_ilk_olayda_tuketilir(self):
        # bond=300, fee=100: 3 olayda tuketilir, sonrasi BEDAVA
        # toplam kesiti 300 ile sinirlidir
        net = bm.censor_net(100.0, 300.0, 60.0, 20, refill=False, slash_mode="capped")
        assert net == pytest.approx(20 * 60.0 - 300.0)

    def test_refill_yoksa_toplam_kesinti_bond_i_gecmez(self):
        for n in (1, 3, 5, 50):
            net = bm.censor_net(100.0, 300.0, 60.0, n, refill=False, slash_mode="capped")
            # net = b_out*n - toplam_slash; toplam_slash <= 300
            assert net >= 60.0 * n - 300.0 - 1e-12

    @pytest.mark.parametrize("bond", [100.0, 300.0, 1000.0])
    def test_bond_sabit_refill_da_kararli(self, bond):
        # refill=True iken capped modda bond>=fee ise sonuc bond'da bagimsiz
        assert bm.censor_net(100.0, bond, 60.0, 4, refill=True, slash_mode="capped") == pytest.approx(4 * (60.0 - 100.0))

    def test_bond_fee_altinda_refill_ile_bond_kadar_kesilir(self):
        # bond=50 < fee=100: slash=50 -> net = 4*(60-50) = +40 (kapsam disi, ayri dal)
        assert bm.censor_net(100.0, 50.0, 60.0, 4, refill=True, slash_mode="capped") == pytest.approx(4 * (60.0 - 50.0))


# ================================================================ censor_net: full
class TestCensorNetFull:
    """censor_net dal 2: slash_mode='full' -> slash = min(cur, bond)."""

    def test_tum_bond_kesilir(self):
        # slash = min(300, 300) = 300 -> net = 60 - 300 = -240
        assert bm.censor_net(100.0, 300.0, 60.0, 1, slash_mode="full") == pytest.approx(-240.0)

    def test_full_capped_daha_sert_caydiricidir(self):
        n_full = bm.censor_net(100.0, 300.0, 60.0, 1, slash_mode="full")
        n_cap = bm.censor_net(100.0, 300.0, 60.0, 1, slash_mode="capped")
        assert n_full < n_cap

    def test_full_refill_her_olayda_bond_keser(self):
        # refill=True: her olayda tam bond -> toplam = n*bond
        assert bm.censor_net(100.0, 300.0, 60.0, 5, refill=True, slash_mode="full") == pytest.approx(5 * 60.0 - 5 * 300.0)

    def test_full_refillsiz_bond_tukenir(self):
        # bond=300, b_out=60, n=5: toplam kesinti 300 (tuketim), net = 0
        assert bm.censor_net(100.0, 300.0, 60.0, 5, refill=False, slash_mode="full") == pytest.approx(5 * 60.0 - 300.0)

    def test_full_refillsiz_cok_olayda_bedava(self):
        # bond tukendikten sonra slash=0: 100 olayda da toplam 300
        net5 = bm.censor_net(100.0, 300.0, 60.0, 5, refill=False, slash_mode="full")
        net100 = bm.censor_net(100.0, 300.0, 60.0, 100, refill=False, slash_mode="full")
        assert net100 - net5 == pytest.approx(95 * 60.0)

    def test_full_bond_fee_altinda_bond_kadar_kesilir(self):
        # min(25, 25) = 25 -> full ile bond<fee ayni kalir (capped ile ayni)
        assert bm.censor_net(100.0, 25.0, 60.0, 1, slash_mode="full") == pytest.approx(60.0 - 25.0)


# ================================================================ censor_net: ValueError
class TestCensorNetUnknownMode:
    """censor_net dal 3: bilinmeyen slash_mode -> ValueError (ROUND-4 fix #23).

    Eskiden sessiz catch-all vardi: "CAPPED", "capped ", "fulll", "" gibi
    tek-karakter tipolar FULL ekonomisini sessizce sectiriyordu. Simdi hata.
    """

    @pytest.mark.parametrize("kotu_mod", ["CAPPED", "capped ", " capped", "fulll",
                                           "ful", "", "FULL", "cappd", "none",
                                           "min(bond,fee)", "capped\n"])
    def test_bilinmeyen_mod_valueerror(self, kotu_mod):
        with pytest.raises(ValueError, match="unknown slash_mode"):
            bm.censor_net(100.0, 300.0, 60.0, 1, slash_mode=kotu_mod)

    def test_hata_mesaji_modu_icerir(self):
        with pytest.raises(ValueError) as ei:
            bm.censor_net(100.0, 300.0, 60.0, 1, slash_mode="capped ")
        assert "capped " in str(ei.value)
        assert "'capped'" in str(ei.value) and "'full'" in str(ei.value)

    def test_mod_sayisal_da_hata(self):
        with pytest.raises(ValueError):
            bm.censor_net(100.0, 300.0, 60.0, 1, slash_mode=0)

    def test_refill_false_da_hata_ayni(self):
        # hata refund dalinda da ayni sekilde atilir
        with pytest.raises(ValueError):
            bm.censor_net(100.0, 300.0, 60.0, 5, refill=False, slash_mode="cap")


# ================================================================ censor_net: sinir degerleri
class TestCensorNetSinirDegerler:
    """censor_net'in sifir/negatif/erisim sinir degerleri."""

    def test_sifir_olay_sifir_net(self):
        assert bm.censor_net(100.0, 300.0, 60.0, 0, slash_mode="capped") == pytest.approx(0.0)
        assert bm.censor_net(100.0, 300.0, 60.0, 0, slash_mode="full") == pytest.approx(0.0)

    def test_sifir_b_out_tum_maliyet(self):
        # getiri yok: net = -toplam_slash
        assert bm.censor_net(100.0, 300.0, 0.0, 3, refill=True, slash_mode="capped") == pytest.approx(-300.0)

    def test_sifir_fee_sifir_bond_bedava_sansur(self):
        assert bm.censor_net(0.0, 0.0, 60.0, 10, slash_mode="capped") == pytest.approx(600.0)
        assert bm.censor_net(0.0, 0.0, 60.0, 10, slash_mode="full") == pytest.approx(600.0)

    def test_negatif_b_out_negatif_net(self):
        net = bm.censor_net(100.0, 300.0, -60.0, 2, refill=True, slash_mode="capped")
        assert net < 0

    def test_determinizm(self):
        args = (100.0, 300.0, 60.0, 7)
        assert bm.censor_net(*args, refill=False, slash_mode="capped") == bm.censor_net(*args, refill=False, slash_mode="capped")

    @pytest.mark.parametrize("n", [1, 2, 5, 20, 100])
    def test_capped_refill_dogrusal_n(self, n):
        # refill=True + capped + bond>=fee: net = n*(b_out - fee) (dogrusal)
        assert bm.censor_net(100.0, 500.0, 60.0, n, refill=True, slash_mode="capped") == pytest.approx(n * (60.0 - 100.0))


# ================================================================ critical_fee_capped
class TestCriticalFeeCapped:
    """critical_fee_capped: capped modda sansuru durduran en kucuk fee = B_out."""

    @pytest.mark.parametrize("b_out", [60.0, 100.0, 250.0, 999.0])
    def test_esittir_b_out(self, b_out):
        assert bm.critical_fee_capped(b_out) == pytest.approx(b_out, abs=1e-6)

    def test_sifir_b_out_sifir_verir(self):
        # b_out=0: bisection [0, 1] araliginda 0'a yakinsar
        assert bm.critical_fee_capped(0.0) == pytest.approx(0.0, abs=1e-12)

    def test_kucuk_b_out(self):
        assert bm.critical_fee_capped(0.001) == pytest.approx(0.001, abs=1e-9)

    def test_kritik_degerde_net_sifir(self):
        # "critical" sozunun testi: cf'de censor_net net = 0
        b_out = 77.0
        cf = bm.critical_fee_capped(b_out)
        net = bm.censor_net(cf, 3 * cf, b_out, 1, refill=True, slash_mode="capped")
        assert net == pytest.approx(0.0, abs=1e-6)

    def test_kritik_altinda_karli_ustunde_zararli(self):
        b_out = 77.0
        cf = bm.critical_fee_capped(b_out)
        assert bm.censor_net(cf * 0.9, 3 * cf, b_out, 1, slash_mode="capped") > 0
        assert bm.censor_net(cf * 1.1, 3 * cf, b_out, 1, slash_mode="capped") < 0

    def test_bisection_araligi_b_out_iki_kati(self):
        # hi = b_out*2+1: net(hi) < 0 garantisi (fee > b_out her zaman negatif)
        b_out = 60.0
        hi = b_out * 2 + 1.0
        assert bm.censor_net(hi, 3 * hi, b_out, 1, slash_mode="capped") < 0

    def test_determinizm(self):
        assert bm.critical_fee_capped(123.0) == bm.critical_fee_capped(123.0)


# ================================================================ critical_margin_full
class TestCriticalMarginFull:
    """critical_margin_full: full modda margin = B_out - fee; NEGATIF olabilir.

    ROUND-4 fix #25: B_out < fee iken gercek kritik margin NEGATIFTIR (margin
    gerekmez — sansur zaten zararlidir). Eski [0, B_out+1] araligi bunu
    gosteremiyordu; simdi aralik sifirin altindan baslar.
    """

    @pytest.mark.parametrize("b_out", [120.0, 150.0, 200.0, 300.0, 500.0])
    def test_margin_b_out_eksi_fee(self, b_out):
        fee = 100.0
        assert bm.critical_margin_full(fee, b_out) == pytest.approx(b_out - fee, abs=1e-6)

    def test_b_out_fee_altinda_negatif_margin(self):
        # ROUND-4 fix #25'in testi: -40 doner (margin gerekmez)
        assert bm.critical_margin_full(100.0, 60.0) < 0
        assert bm.critical_margin_full(100.0, 60.0) == pytest.approx(-40.0, abs=1e-6)

    def test_b_out_fee_esitse_margin_sifir(self):
        assert bm.critical_margin_full(100.0, 100.0) == pytest.approx(0.0, abs=1e-9)

    def test_b_out_fee_ustunde_pozitif_margin(self):
        assert bm.critical_margin_full(100.0, 300.0) == pytest.approx(200.0, abs=1e-6)

    def test_negatif_margin_sifir_margin_ile_ayristirilabilir(self):
        # eski kod 0.0 donduruyordu; simdi -40 ile 0 arasinda kesin ayrim var
        assert bm.critical_margin_full(100.0, 60.0) != bm.critical_margin_full(100.0, 100.0)

    def test_kritik_degerde_net_sifir(self):
        fee, b_out = 100.0, 77.0
        m = bm.critical_margin_full(fee, b_out)
        net = bm.censor_net(fee, fee + m, b_out, 1, refill=True, slash_mode="full")
        assert net == pytest.approx(0.0, abs=1e-6)

    def test_margin_altinda_karli_ustunde_zararli(self):
        fee, b_out = 100.0, 300.0
        m = bm.critical_margin_full(fee, b_out)
        assert bm.censor_net(fee, fee + m * 0.5, b_out, 1, slash_mode="full") > 0
        assert bm.censor_net(fee, fee + m * 1.5, b_out, 1, slash_mode="full") < 0

    def test_sifir_fee_margin_b_out(self):
        # fee=0: margin = B_out - 0 = B_out
        assert bm.critical_margin_full(0.0, 50.0) == pytest.approx(50.0, abs=1e-6)

    def test_esit_fee_b_out_yakin_sifir(self):
        assert bm.critical_margin_full(50.0, 50.0) == pytest.approx(0.0, abs=1e-9)

    def test_determinizm(self):
        assert bm.critical_margin_full(100.0, 250.0) == bm.critical_margin_full(100.0, 250.0)


# ================================================================ TV-31
class TestTv31CappedDeterrentBoundedByFee:
    """tv31_capped_deterrent_bounded_by_fee: capped'da bond>fee ise yaramaz."""

    def test_pass_doner(self):
        sonuc, notu = bm.tv31_capped_deterrent_bounded_by_fee()
        assert sonuc == "PASS"
        assert isinstance(notu, str)
        assert len(notu) > 0

    def test_not_spec_duzeltmesini_icerir(self):
        _, notu = bm.tv31_capped_deterrent_bounded_by_fee()
        assert "SPEC CORRECTION" in notu
        assert "FULL" in notu

    def test_bond_seviyesinden_bagimsiz(self):
        # fonksiyonun kendi iddialari: 100/500/2000 ayni net verir
        n100 = bm.censor_net(100.0, 100.0, 60.0, 1, refill=True, slash_mode="capped")
        n500 = bm.censor_net(100.0, 500.0, 60.0, 1, refill=True, slash_mode="capped")
        n2000 = bm.censor_net(100.0, 2000.0, 60.0, 1, refill=True, slash_mode="capped")
        assert n100 == n500 == n2000 == -40.0

    def test_kritik_fee_b_out(self):
        # TV-31'in iddia ettigi esik: critical fee = B_out
        assert abs(bm.critical_fee_capped(60.0) - 60.0) < 1.0

    def test_hic_istisna_atmaz(self):
        # TV-31 icindeki assert'ler her zaman gecerli olmali (regression guard)
        for _ in range(3):
            assert bm.tv31_capped_deterrent_bounded_by_fee()[0] == "PASS"


# ================================================================ TV-32
class TestTv32FullMarginLinear:
    """tv32_full_margin_linear: full modda margin = B_out - fee, dogrusal."""

    def test_pass_doner(self):
        sonuc, notu = bm.tv32_full_margin_linear()
        assert sonuc == "PASS"
        assert isinstance(notu, str)

    def test_not_r2_icerir(self):
        _, notu = bm.tv32_full_margin_linear()
        assert "R^2" in notu

    @pytest.mark.parametrize("b_out", [120, 150, 200, 300, 500])
    def test_margin_dogrusal_b_out_eksi_fee(self, b_out):
        # TV-32'nin icindeki 5 noktanin her biri (fee=100)
        m = bm.critical_margin_full(100.0, b_out)
        assert abs(m - (b_out - 100)) < 1.0

    def test_dogrusal_uyum_r2_bir(self):
        # TV-32'nin kendi R^2 hesabi: margin = B_out - fee tam dogrusal → R^2 = 1
        fee = 100.0
        pts = [(b, bm.critical_margin_full(fee, b)) for b in [120, 150, 200, 300, 500]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        r2 = (sxy ** 2) / (sxx * syy)
        assert r2 == pytest.approx(1.0, abs=1e-9)

    def test_max_hata_birden_kucuk(self):
        fee = 100.0
        pts = [bm.critical_margin_full(fee, b) for b in [120, 150, 200, 300, 500]]
        beklenen = [b - fee for b in [120, 150, 200, 300, 500]]
        assert max(abs(m - e) for m, e in zip(pts, beklenen)) < 1.0


# ================================================================ TV-33
class TestTv33FreeCensorshipWindow:
    """tv33_free_censorship_window: refill yoksa bedava sansur = bond/fee olay."""

    def test_pass_doner(self):
        sonuc, notu = bm.tv33_free_censorship_window()
        assert sonuc == "PASS"
        assert isinstance(notu, str)

    def test_not_pencere_sayisi_icerir(self):
        _, notu = bm.tv33_free_censorship_window()
        assert "window" in notu

    def test_refillsiz_toplam_kesinti_bond_kadar(self):
        # bond=300, fee=100, n=20: toplam kesiti = 300 (3 olayda tuketilir)
        net = bm.censor_net(100.0, 300.0, 60.0, 20, refill=False, slash_mode="capped")
        assert net == pytest.approx(20 * 60.0 - 300.0)

    def test_refillli_toplam_kesinti_n_fee(self):
        net = bm.censor_net(100.0, 300.0, 60.0, 20, refill=True, slash_mode="capped")
        assert net == pytest.approx(20 * 60.0 - 20 * 100.0)

    def test_refillsiz_karli_refillli_zararli(self):
        # TV-33'un ozet iddiasi: refill yok +20 olay = +900, refill var = -800
        noref = bm.censor_net(100.0, 300.0, 60.0, 20, refill=False, slash_mode="capped")
        ref = bm.censor_net(100.0, 300.0, 60.0, 20, refill=True, slash_mode="capped")
        assert noref > 0
        assert ref < 0
        assert noref - ref == pytest.approx(20 * 100.0 - 300.0)

    def test_bedava_pencere_bond_bolum_fee(self):
        # bond=300, fee=100 → 3 olay
        assert 300.0 / 100.0 == pytest.approx(3.0)
        # 3 olayda tuketilir: 3 olayin sonunda toplam kesiti 300
        assert bm.censor_net(100.0, 300.0, 60.0, 3, refill=False, slash_mode="capped") == pytest.approx(3 * 60.0 - 300.0)
        # 4. olay bedava: 3 ve 4 olayin neti ayni fark ile
        n3 = bm.censor_net(100.0, 300.0, 60.0, 3, refill=False, slash_mode="capped")
        n4 = bm.censor_net(100.0, 300.0, 60.0, 4, refill=False, slash_mode="capped")
        assert n4 - n3 == pytest.approx(60.0)


# ================================================================ main
class TestMain:
    """main(): 3 TV testini kosturur; hepsi gecerse 0, biri cokerse 1 doner."""

    def test_hepsi_gecerse_sifir_donar(self):
        with contextlib.redirect_stdout(io.StringIO()):
            assert bm.main() == 0

    def test_biri_cokerse_bir_donar(self):
        # tv31'i kasitli olarak coken bir fonksiyonla degistir
        orig = bm.tv31_capped_deterrent_bounded_by_fee
        bm.tv31_capped_deterrent_bounded_by_fee = lambda: (_ for _ in ()).throw(
            AssertionError("kasitli basarisizlik"))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                assert bm.main() == 1
        finally:
            bm.tv31_capped_deterrent_bounded_by_fee = orig

    def test_gecerli_cikti_result_all_passed_icerir(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = bm.main()
        assert rc == 0
        assert "ALL PASSED" in buf.getvalue()

    def test_coken_cikti_failed_icerir(self):
        orig = bm.tv33_free_censorship_window
        bm.tv33_free_censorship_window = lambda: (_ for _ in ()).throw(
            AssertionError("kasitli"))
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = bm.main()
            assert rc == 1
            assert "FAILED" in buf.getvalue()
        finally:
            bm.tv33_free_censorship_window = orig

    def test_baslik_ve_toy_limitleri_basarir(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bm.main()
        out = buf.getvalue()
        assert "TV-31..TV-33" in out
        assert "TOY LIMITS" in out
        assert "capped" in out and "full" in out

    def test_ana_modul_gecerli_rc_sifir(self):
        # modulun kendi __main__ geri donusu ile ayni satis sozlesmesi
        with contextlib.redirect_stdout(io.StringIO()):
            assert bm.main() == 0
