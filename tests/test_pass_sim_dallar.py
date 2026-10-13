#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dal-kesen testler for pass_sim.py — Pass PoUW kapali-form denge cozucu.

pass_sim.py 10 genel sembol icerir ve bu dosya HER BIRININ dalini keser:

    Params.PR / Delta / theta_low / theta_high   (4 property, 3 rejim dali)
    Eq.residuals(prm)                            (M/L/D aktif+pasif dallari)
    _theta_from_PR(prm)                          (bisection basari + 3 NaN dali)
    solve(prm, theta_target)                     (a) Bitconia Delta<0
                                                 (b) Fortessia theta<theta_low
                                                 (c1) Duplexia saf D
                                                 (c2) Duplexia karisik M+D
                                                 + endojen theta 3 dali)
    verify(eq, prm)                              (dict satis sozlesmesi)
    classify_ok(eq, prm)                         (3 rejim dali)
    h(t)                                         (banner yazdirma)
    bitconia_ref(prm, theta)                     (karsilastirma tabani)
    recalibrate_f3a(...)                         (Pearl regression + F3a + sifir bolme)
    censorship_economics(...)                    (refill True/False, bond<fee, esik)

Sayisal iddialar KODDAKI uretilen degerlerle (Pearl: e=0.006, PR=2032.24,
K=3.6, alpha=gamma=1.3) onceden olculmustur; sabit olarak ezberlenmemistir.

KURALLAR: production koduna DOKUNULMADI; sadece tests/ altinda yeni dosya.
Saf in-memory: dis ag/HTTP/DB/subprocess cagrisi YOK. pass_sim modul duzeyinde
rapor yazdirmaktadir → import sirasinda stdout contextlib ile yutulur.
"""

from __future__ import annotations

import contextlib
import io
import math

import pytest

# pass_sim import sirasinda tum raporini (bolum 0-8) basar; test ciktisini
# kirletlememek ve Kural-4 (saf in-memory, yan etki yok) icin stdout yutulur.
with contextlib.redirect_stdout(io.StringIO()):
    import pass_sim as ps

# --- Pearl kalibrasyon sabitleri (pass_sim.PEARL ile ayni) ---
E = 0.006              # 0.20 $/sa * 108 s / 3600
R = 2674               # PRL/blok
P = 0.76               # $/PRL
PR = P * R             # 2032.24 $/blok
Q_B = 3.6 * E ** -2.0  # = 100000: K * e^-eps (Bitconia talebi)


def _pearl(**kw):
    """Varsayilan Pearl parametreleri; kw ile ezilebilir (alpha/gamma/K/PR)."""
    base = dict(e=E, R=R, P=P, alpha=1.3, gamma=1.3)
    base.update(kw)
    return ps.Params(**base)


# ================================================================ Params properties
class TestParamsProperties:
    """Params'in 4 property'si ve varsayilan alanlari."""

    def test_varsayilan_degerler(self):
        # alpha/gamma=1.3, eps=2.0, K=3.6 spec'teki varsayilanlardir
        prm = ps.Params(e=E, R=R, P=P)
        assert prm.alpha == 1.3
        assert prm.gamma == 1.3
        assert prm.eps == 2.0
        assert prm.K == 3.6

    def test_pr_carpimdir(self):
        assert _pearl().PR == pytest.approx(PR)
        # P veya R degisince PR ayni oranda degisir
        assert ps.Params(e=E, R=R, P=2 * P).PR == pytest.approx(2 * PR)

    @pytest.mark.parametrize("alpha,gamma,beklenen", [
        (1.3, 1.3, 1 / 1.3 + 1 / 1.3 - 1),   # Pearl: +0.5385 (duplex verimli)
        (3.0, 3.0, 1 / 3 + 1 / 3 - 1),       # -0.3333 (Bitconia rejimi)
        (2.0, 2.0, 0.0),                     # tam sinir: Delta == 0
        (10.0, 1.2, 1 / 10 + 1 / 1.2 - 1),   # negatif, asimetrik ornek
    ])
    def test_delta_rejimi(self, alpha, gamma, beklenen):
        prm = _pearl(alpha=alpha, gamma=gamma)
        assert prm.Delta == pytest.approx(beklenen)

    @pytest.mark.parametrize("alpha,beklenen", [(1.3, 0.3), (1.0, 0.0), (2.5, 1.5)])
    def test_theta_low_alpha_eksibir(self, alpha, beklenen):
        assert _pearl(alpha=alpha).theta_low == pytest.approx(beklenen)

    @pytest.mark.parametrize("gamma,beklenen", [(1.3, 1 / 0.3), (2.0, 1.0), (1.1, 10.0)])
    def test_theta_high_gamma_bir_eksi_bolum(self, gamma, beklenen):
        assert _pearl(gamma=gamma).theta_high == pytest.approx(beklenen)

    def test_rejim_sinirlari_ayri(self):
        # Pearl icin theta_low=0.3 < theta_high=3.333: (lo,hi) araligi gecerli
        prm = _pearl()
        assert prm.theta_low < prm.theta_high


# ================================================================ _theta_from_PR
class TestThetaFromPR:
    """Duplexia endojen theta cozucu: basari + 3 NaN (cozum yok) dali."""

    def test_pearl_endojen_theta(self):
        # TV-84 duzeltmesinin olculen degeri: 1.6571 (eski sabit 1.05 degildi)
        th = ps._theta_from_PR(_pearl())
        assert th == pytest.approx(1.6571246293774187, abs=1e-9)

    def test_cozum_dogrulugu_ozgu_yazilimla(self):
        # f(theta) = theta*c*(1+theta)^(eps-1) - PR koktur; cozum f'yi sifirlar
        prm = _pearl()
        c = prm.K * (prm.alpha * prm.e) ** (1 - prm.eps)
        th = ps._theta_from_PR(prm)
        f = th * c * (1 + th) ** (prm.eps - 1) - prm.PR
        assert abs(f) < 1e-6

    def test_cozum_aralikta(self):
        # cozum daima (theta_low, theta_high) icindedir
        prm = _pearl()
        th = ps._theta_from_PR(prm)
        assert prm.theta_low < th < prm.theta_high

    def test_determinizm(self):
        assert ps._theta_from_PR(_pearl()) == ps._theta_from_PR(_pearl())

    def test_nan_dali_lo_hi_gecersiz(self):
        # theta_low >= theta_high (alpha-1 >= 1/(gamma-1)) → cozum yok → NaN
        prm = _pearl(alpha=20.0, gamma=1.1)   # lo=19 > hi=10
        assert prm.theta_low > prm.theta_high
        assert math.isnan(ps._theta_from_PR(prm))

    def test_nan_dali_f_lo_pozitif(self):
        # PR cok kucuk: f(lo) > 0 → kokun solunda → NaN (Fortessia'ya dusulur)
        prm = ps.Params(e=E, R=1.0, P=1e-4, alpha=1.3, gamma=1.3)
        lo, hi = prm.theta_low, prm.theta_high
        c = prm.K * (prm.alpha * prm.e) ** (1 - prm.eps)
        assert lo * c * (1 + lo) ** (prm.eps - 1) - prm.PR > 0   # f(lo)>0 sart
        assert math.isnan(ps._theta_from_PR(prm))

    def test_nan_dali_f_hi_negatif(self):
        # PR cok buyuk: f(hi) < 0 → kokun saginda → NaN (karisik Duplexia'ya dusulur)
        prm = ps.Params(e=E, R=R, P=1e5, alpha=1.3, gamma=1.3)
        hi = prm.theta_high
        c = prm.K * (prm.alpha * prm.e) ** (1 - prm.eps)
        assert hi * c * (1 + hi) ** (prm.eps - 1) - prm.PR < 0   # f(hi)<0 sart
        assert math.isnan(ps._theta_from_PR(prm))


# ================================================================ solve: Bitconia
class TestSolveBitconia:
    """solve dal (a): Delta<0 → Bitconia (M+L), D=0, p=e, S=PR/e."""

    def _neg_delta(self):
        return _pearl(alpha=3.0, gamma=3.0)   # Delta = -1/3 < 0

    def test_rejim_adi_ve_delta_isareti(self):
        prm = self._neg_delta()
        assert prm.Delta < 0
        assert ps.solve(prm, 0.5).name.startswith("Bitconia")

    def test_d_sifir_m_ve_s_esit(self):
        eq = ps.solve(self._neg_delta(), 0.5)
        assert eq.D == 0.0
        assert eq.M == pytest.approx(eq.S)

    def test_tullock_tam_odeme_s_pr_bolum_e(self):
        # eS = PR (Tullock): S = PR/e
        prm = self._neg_delta()
        eq = ps.solve(prm, 0.5)
        assert eq.S == pytest.approx(prm.PR / prm.e)

    def test_fiyat_maliyete_esit(self):
        # Bitconia'da fayda yok: p = e
        prm = self._neg_delta()
        eq = ps.solve(prm, 0.5)
        assert eq.p == pytest.approx(prm.e)

    def test_talep_q_b(self):
        prm = self._neg_delta()
        eq = ps.solve(prm, 0.5)
        assert eq.Q == pytest.approx(Q_B)
        assert eq.L == pytest.approx(Q_B)

    def test_theta_pr_bolum_pq(self):
        prm = self._neg_delta()
        eq = ps.solve(prm, 0.5)
        assert eq.theta == pytest.approx(prm.PR / (eq.p * eq.Q))

    def test_theta_target_yoksayilir_delta_oncelikli(self):
        # Delta<0 once kontrol edilir: theta_target verilse bile Bitconia
        prm = self._neg_delta()
        for th in (0.05, 0.3, 5.0):
            assert ps.solve(prm, th).name.startswith("Bitconia")

    def test_endojen_theta_da_bitconia(self):
        prm = self._neg_delta()
        eq = ps.solve(prm)
        assert eq.name.startswith("Bitconia")
        assert eq.theta == pytest.approx(prm.PR / (prm.e * Q_B))


# ================================================================ solve: Fortessia
class TestSolveFortessia:
    """solve dal (b): Delta>0, theta<theta_low → Fortessia (D+L)."""

    @pytest.mark.parametrize("theta", [0.05, 0.20, 0.29])
    def test_rejim_adi_ve_sifir_m(self, theta):
        eq = ps.solve(_pearl(), theta)
        assert theta < _pearl().theta_low
        assert eq.name.startswith("Fortessia")
        assert eq.M == 0.0

    def test_fiyat_maliyete_esit(self):
        # Fortessia'da p = e (inference'u token odulleri subsidize etmez)
        prm = _pearl()
        assert ps.solve(prm, 0.2).p == pytest.approx(prm.e)

    def test_talep_q_b_sabit(self):
        # faydali cikis Bitconia ile ayni: Q = Q_B
        prm = _pearl()
        eq = ps.solve(prm, 0.2)
        assert eq.Q == pytest.approx(Q_B)

    def test_d_gamma_carpi_s(self):
        prm = _pearl()
        eq = ps.solve(prm, 0.2)
        assert eq.D == pytest.approx(prm.gamma * eq.S)

    def test_s_formulu_pr_bolum_gamma_e_eksi_alpha_bolum(self):
        # S = PR / (gamma*e*(1-1/alpha)); PR = theta*e*Q_B
        prm = _pearl()
        theta = 0.2
        PR_t = theta * prm.e * Q_B
        eq = ps.solve(prm, theta)
        assert eq.S == pytest.approx(PR_t / (prm.gamma * prm.e * (1 - 1 / prm.alpha)))

    def test_l_q_b_eksi_d_bolum_alpha(self):
        prm = _pearl()
        eq = ps.solve(prm, 0.2)
        assert eq.L == pytest.approx(Q_B - eq.D / prm.alpha)
        assert eq.L > 0

    def test_guvenlik_bitconia_daha_yuksek(self):
        # Theorem 1: ayni theta'da S_F/S_B = 1/(gamma*(1-1/alpha)) = 3.333
        prm = _pearl()
        theta = 0.2
        s_f = ps.solve(prm, theta).S
        s_b = ps.bitconia_ref(prm, theta)["S"]
        assert s_f / s_b == pytest.approx(1 / (prm.gamma * (1 - 1 / prm.alpha)))
        assert s_f > s_b

    def test_endojen_dal_pr_esigin_altinda(self):
        # PR < theta_low*e*Q_B → theta = PR/(e*Q_B) → Fortessia
        prm = ps.Params(e=E, R=R, P=0.05)   # PR=133.7 < 180 = theta_low*e*Q_B
        esik = prm.theta_low * prm.e * Q_B
        assert prm.PR < esik
        eq = ps.solve(prm)
        assert eq.name.startswith("Fortessia")
        assert eq.theta == pytest.approx(prm.PR / (prm.e * Q_B))


# ================================================================ solve: Duplexia saf
class TestSolveDuplexiaSaf:
    """solve dal (c1): theta_low<=theta<theta_high → saf D, p<e."""

    @pytest.mark.parametrize("theta", [0.5, 1.0, 2.0, 3.0])
    def test_rejim_adi_ve_sadece_d_aktif(self, theta):
        prm = _pearl()
        eq = ps.solve(prm, theta)
        assert prm.theta_low <= theta < prm.theta_high
        assert eq.name.startswith("Duplexia (saf D)")
        assert eq.M == 0.0
        assert eq.L == 0.0
        assert eq.D > 0

    @pytest.mark.parametrize("theta", [0.5, 1.0, 2.0, 3.0])
    def test_fiyat_inference_u_zerinde_subside(self, theta):
        # p = alpha*e/(1+theta) < e (Theorem 3: tokenler inference'u subsidize eder)
        prm = _pearl()
        eq = ps.solve(prm, theta)
        assert eq.p == pytest.approx(prm.alpha * prm.e / (1 + theta))
        assert eq.p < prm.e

    def test_talep_genisler_q_k_p_eksi_eps(self):
        prm = _pearl()
        eq = ps.solve(prm, 1.0)
        assert eq.Q == pytest.approx(prm.K * eq.p ** -prm.eps)
        assert eq.Q > Q_B   # dusuk fiyat → daha cok talep

    def test_d_alpha_carpi_q_ve_s_d_bolum_gamma(self):
        prm = _pearl()
        eq = ps.solve(prm, 1.0)
        assert eq.D == pytest.approx(prm.alpha * eq.Q)
        assert eq.S == pytest.approx(eq.D / prm.gamma)

    def test_theta_pr_tutarliligi(self):
        # PR = theta*p*Q (cozucu kendini tekrar uretir)
        prm = _pearl()
        eq = ps.solve(prm, 1.0)
        assert eq.P * prm.R == pytest.approx(theta := 1.0 * eq.p * eq.Q)

    def test_pearl_endojen_saf_duplexia(self):
        # Pearl'un gercek PR seviyesi endojen theta=1.657 → saf Duplexia
        eq = ps.solve(_pearl())
        assert eq.name.startswith("Duplexia (saf D)")
        assert eq.theta == pytest.approx(1.6571246293774187, abs=1e-9)

    def test_theta_hedef_esik_degeri_degil(self):
        # theta tam theta_low'da Fortessia dalina gecit vermez (>= esik)
        prm = _pearl()
        eq = ps.solve(prm, prm.theta_low + 1e-9)
        assert eq.name.startswith("Duplexia")


# ================================================================ solve: Duplexia karisik
class TestSolveDuplexiaKarishik:
    """solve dal (c2): theta>=theta_high → karisik (M+D), p sabitlenmis."""

    @pytest.mark.parametrize("theta", [3.34, 5.0, 10.0])
    def test_rejim_adi_ve_m_tekrar_aktif(self, theta):
        prm = _pearl()
        eq = ps.solve(prm, theta)
        assert theta >= prm.theta_high
        assert eq.name.startswith("Duplexia (M+D)")
        assert eq.M > 0
        assert eq.L == 0.0
        assert eq.D > 0

    def test_fiyat_sabitlenmis_alpha_e_eksi_gamma(self):
        # karisik rejimde p = alpha*e*(1-1/gamma); theta'ya bagli degil
        prm = _pearl()
        p1 = ps.solve(prm, 3.34).p
        p2 = ps.solve(prm, 50.0).p
        assert p1 == pytest.approx(prm.alpha * prm.e * (1 - 1 / prm.gamma))
        assert p2 == pytest.approx(p1)

    def test_d_alpha_q_sabit(self):
        prm = _pearl()
        eq = ps.solve(prm, 5.0)
        assert eq.D == pytest.approx(prm.alpha * eq.Q)

    def test_m_s_eksi_alpha_q_bolum_gamma(self):
        prm = _pearl()
        eq = ps.solve(prm, 5.0)
        assert eq.M == pytest.approx(eq.S - (prm.alpha * eq.Q) / prm.gamma)

    def test_s_pr_bolum_e(self):
        # karisik rejimde M+D arzi yine Tullock: S = PR/e
        prm = _pearl()
        eq = ps.solve(prm, 5.0)
        PR_t = 5.0 * eq.p * eq.Q
        assert eq.S == pytest.approx(PR_t / prm.e)

    def test_endojen_dal_kucuk_talep(self):
        # K -> 0: _theta_from_PR >= theta_high verir → karisik Duplexia
        prm = _pearl(K=0.36)
        eq = ps.solve(prm)
        assert eq.name.startswith("Duplexia (M+D)")
        assert eq.theta >= prm.theta_high
        assert eq.M > 0


# ================================================================ Eq.residuals
class TestResiduals:
    """Eq.residuals: aktif (x>0) ve pasif (x==0) aktivite dallari."""

    def test_hepsi_aktif_uc_residual(self):
        eq = ps.Eq("Karishik", 100.0, 100.0, 100.0, 500.0, 500.0, E, P, 1.0)
        act, inact = eq.residuals(_pearl())
        assert len(act) == 3
        assert inact == []

    def test_hepsi_pasif_uc_ihlal(self):
        eq = ps.Eq("Bos", 0.0, 0.0, 0.0, 500.0, 500.0, E, P, 1.0)
        act, inact = eq.residuals(_pearl())
        assert act == []
        assert len(inact) == 3

    def test_karisik_iki_aktif_bir_pasif(self):
        eq = ps.Eq("D+L", 0.0, 100.0, 100.0, 500.0, 500.0, E, P, 1.0)
        act, inact = eq.residuals(_pearl())
        assert len(act) == 2
        assert len(inact) == 1

    def test_bitconia_cozumunde_sifir_artik(self):
        eq = ps.solve(_pearl(alpha=3.0, gamma=3.0), 0.5)
        act, inact = eq.residuals(_pearl(alpha=3.0, gamma=3.0))
        assert max(abs(r) for r in act) < 1e-9
        assert max(inact) == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.parametrize("theta", [0.05, 0.2, 0.5, 1.0, 3.0, 5.0])
    def test_cozulen_denge_sifir_artik(self, theta):
        # her rejimde aktif aktivitelerin artiklari ~0 (serbest giris)
        prm = _pearl()
        eq = ps.solve(prm, theta)
        act, inact = eq.residuals(prm)
        assert max(abs(r) for r in act) < 1e-9
        assert max(inact) < 1e-9   # pasif aktiviteler zarar etmez

    def test_pasif_ihlal_işaretlenir(self):
        # p > e iken L=0 ise rL = p-e > 0 → ihlal listesinde
        eq = ps.Eq("Yanlis", 0.0, 0.0, 100.0, 500.0, 500.0, 2 * E, P, 1.0)
        prm = _pearl()
        _, inact = eq.residuals(prm)
        assert any(v > 0 for v in inact)


# ================================================================ verify
class TestVerify:
    """verify: dict satis sozlesmesi + Theorem 1 uyumu."""

    @pytest.mark.parametrize("theta", [0.05, 0.5, 1.0, 3.0, 5.0])
    def test_cozulen_denge_temiz(self, theta):
        prm = _pearl()
        v = ps.verify(ps.solve(prm, theta), prm)
        assert v["max_active_residual"] < 1e-9
        assert v["max_inactive_violation"] < 1e-9
        assert v["market_clearing_err"] < 1e-6
        assert v["regime_ok"] is True

    def test_anahtarlar(self):
        v = ps.verify(ps.solve(_pearl()), _pearl())
        assert set(v) == {"regime_ok", "max_active_residual",
                          "max_inactive_violation", "market_clearing_err"}

    def test_regime_ok_classify_ile_ayni(self):
        prm = _pearl()
        for theta in (0.05, 0.5, 5.0):
            eq = ps.solve(prm, theta)
            assert ps.verify(eq, prm)["regime_ok"] == ps.classify_ok(eq, prm)

    def test_market_clearing_hatasi_olculur(self):
        # Q ile K*p^-eps arasindaki sapma: p'yi bozarsak hata > 0
        prm = _pearl()
        eq = ps.solve(prm, 1.0)
        eq2 = ps.Eq(eq.name, eq.M, eq.L, eq.D, eq.S, eq.Q * 2, eq.p, eq.P, eq.theta)
        assert ps.verify(eq2, prm)["market_clearing_err"] > 0.1

    def test_aktif_yoksa_residual_sifir(self):
        # act bos listeyse max_active_residual = 0.0 (bos-max dali)
        eq = ps.Eq("Bos", 0.0, 0.0, 0.0, 500.0, 500.0, E, P, 1.0)
        v = ps.verify(eq, _pearl())
        assert v["max_active_residual"] == 0.0


# ================================================================ classify_ok
class TestClassifyOk:
    """classify_ok: 3 rejim dali (Delta<0 / theta<theta_low / else)."""

    def test_bitconia_dali_delta_negatif(self):
        prm = _pearl(alpha=3.0, gamma=3.0)
        assert prm.Delta < 0
        assert ps.classify_ok(ps.solve(prm, 0.5), prm) is True
        # ayni Eq ama Delta>0 parametreyle isim uyumsuz → False
        assert ps.classify_ok(ps.solve(prm, 0.5), _pearl()) is False

    def test_fortessia_dali_theta_kucuk(self):
        prm = _pearl()
        eq = ps.solve(prm, 0.2)
        assert prm.Delta > 0 and eq.theta < prm.theta_low
        assert ps.classify_ok(eq, prm) is True
        # isim Fortessia degilse ayni theta'da False
        fake = ps.Eq("Bitconia (M+L)", eq.M, eq.L, eq.D, eq.S, eq.Q, eq.p, eq.P, eq.theta)
        assert ps.classify_ok(fake, prm) is False

    def test_duplexia_dali_geri_kalan(self):
        prm = _pearl()
        for theta in (0.5, 1.0, 3.0, 5.0):
            eq = ps.solve(prm, theta)
            assert eq.theta >= prm.theta_low
            assert ps.classify_ok(eq, prm) is True

    @pytest.mark.parametrize("isim,on_ek", [
        ("Bitconia (M+L)", "Bitconia"),
        ("Fortessia (D+L)", "Fortessia"),
        ("Duplexia (saf D)", "Duplexia"),
        ("Duplexia (M+D)", "Duplexia"),
    ])
    def test_isim_on_ekine_gore_duz_fallback(self, isim, on_ek):
        # Delta>0 ve theta >= theta_low durumunda yalnizca on-ek belirler
        eq = ps.Eq(isim, 100.0, 100.0, 100.0, 500.0, 500.0, E, P, 1.0)
        prm = _pearl()   # Delta>0, theta_low=0.3 < theta=1.0
        beklenen = isim.startswith("Duplexia")
        assert ps.classify_ok(eq, prm) is beklenen

    def test_fortessia_ismi_theta_esiginde_false(self):
        # Delta>0, theta >= theta_low iken "Fortessia" ismi False doner
        eq = ps.Eq("Fortessia (D+L)", 0.0, 1.0, 1.0, 1.0, 1.0, E, P, 2.0)
        assert ps.classify_ok(eq, _pearl()) is False


# ================================================================ h(t)
class TestHYardimci:
    """h(t): banner basar (yan etki: stdout)."""

    def test_banner_formati(self, capsys):
        ps.h("BASLIK")
        out = capsys.readouterr().out
        satir = "=" * 72
        assert out == f"\n{satir}\nBASLIK\n{satir}\n"

    def test_baslik_degisince_icerik_degisir(self, capsys):
        ps.h("BASKA")
        assert "BASKA" in capsys.readouterr().out

    def test_once_bosluk_satiri(self, capsys):
        ps.h("X")
        assert capsys.readouterr().out.startswith("\n")


# ================================================================ bitconia_ref
class TestBitconiaRef:
    """bitconia_ref: ayni theta'da klasik PoW karsilastirma tabani."""

    def test_pearl_referans_degerleri(self):
        prm = _pearl()
        ref = ps.bitconia_ref(prm, 0.25)
        # PR = theta*e*Q_B = 0.25*0.006*100000 = 150
        assert ref["PR"] == pytest.approx(150.0)
        # S = PR/e (Tullock)
        assert ref["S"] == pytest.approx(150.0 / prm.e)
        # Q = Q_B, p = e
        assert ref["Q"] == pytest.approx(Q_B)
        assert ref["p"] == pytest.approx(prm.e)

    def test_anahtarlar(self):
        assert set(ps.bitconia_ref(_pearl(), 0.25)) == {"S", "Q", "p", "PR"}

    @pytest.mark.parametrize("theta", [0.05, 0.25, 1.0, 3.4])
    def test_s_pr_bolum_e_tum_thetalarda(self, theta):
        prm = _pearl()
        ref = ps.bitconia_ref(prm, theta)
        assert ref["S"] == pytest.approx(ref["PR"] / prm.e)

    def test_ayni_theta_ayni_pr_apples_to_apples(self):
        # Pass'in karsilastirmasinin omurgasi: esit theta → esit PR
        prm = _pearl()
        eq = ps.solve(prm, 0.25)
        ref = ps.bitconia_ref(prm, 0.25)
        assert eq.P * prm.R == pytest.approx(ref["PR"])


# ================================================================ recalibrate_f3a
class TestRecalibrateF3a:
    """F3a kalibrasyon kancasi: regression guard + sapma + sifir-bolme."""

    def test_pearl_regression_guard(self):
        # bilinen sonucu teyit: %5.85 sapma, Theorem1 uyumlu
        r = ps.recalibrate_f3a(320_000, 1.06, e=E, P=P, R=R)
        assert r["S_tahmin"] == pytest.approx(P * R / E)
        assert r["S_olculen"] == 320_000
        assert r["sapma_yuzde"] < 6.0
        assert r["Theorem1_uyumlu"] is True

    def test_anahtarlar(self):
        r = ps.recalibrate_f3a(1000, 1.0, e=E, P=P, R=R)
        assert set(r) == {"S_tahmin", "S_olculen", "sapma_yuzde",
                          "gelir_maliyet_tahmin", "gelir_maliyet_olculen",
                          "Theorem1_uyumlu"}

    def test_gelir_maliyet_tahmin_her_zaman_none(self):
        # Eq dataclass'inda rev_cost alani YOK → hasattr daima False → None
        r = ps.recalibrate_f3a(1000, 1.0, e=E, P=P, R=R)
        assert r["gelir_maliyet_tahmin"] is None
        assert r["gelir_maliyet_olculen"] == 1.0

    def test_f3a_kucuk_ag_buyuk_sapma(self):
        # 1200 GPU'luk hipotetik testnet: rekabetci denge varsayimi bozar
        r = ps.recalibrate_f3a(1200, 0.95, e=E, P=0.5, R=2.0)
        assert r["S_tahmin"] == pytest.approx(1.0 / E)   # 0.5*2/0.006
        assert r["sapma_yuzde"] > 80.0
        assert r["Theorem1_uyumlu"] is True

    def test_sapma_yuzde_formulu(self):
        # sapma = |S_pred - olculen| / olculen * 100
        r = ps.recalibrate_f3a(100_000, 1.0, e=E, P=P, R=R)
        beklenen = abs(P * R / E - 100_000) / 100_000 * 100.0
        assert r["sapma_yuzde"] == pytest.approx(beklenen)

    def test_tam_eslesme_sifir_sapma(self):
        # olculen tam PR/e ise sapma 0
        r = ps.recalibrate_f3a(P * R / E, 1.0, e=E, P=P, R=R)
        assert r["sapma_yuzde"] == pytest.approx(0.0)

    def test_sifir_gpus_sifira_bolme_hatasi(self):
        # measured_gpus=0 → ZeroDivisionError (kotu veriyi sessizce yutma)
        with pytest.raises(ZeroDivisionError):
            ps.recalibrate_f3a(0, 1.0, e=E, P=P, R=R)

    def test_alpha_gamma_aktarilir(self):
        # Theorem1 uyumu kullanilan alpha/gamma'dan etkilenir
        r = ps.recalibrate_f3a(1000, 1.0, e=E, P=P, R=R, alpha=3.0, gamma=3.0)
        assert r["Theorem1_uyumlu"] is True


# ================================================================ censorship_economics
class TestCensorshipEconomics:
    """Sansur ekonomisi: refill True/False, bond<fee, oyun-disi fayda esigi."""

    def test_refill_true_dogrusal_caydiricilik(self):
        # her olayda fee kadar kesilir: toplam = n*fee
        r = ps.censorship_economics(100, 0.30, 100, 10, 0.0, refill=True)
        assert r["toplam_kesinti"] == pytest.approx(10 * 100)
        assert r["kalici_bond"] == pytest.approx(100)
        assert r["deterrente_yeterli"] is True

    def test_refill_false_tek_seferlik(self):
        # bond ilk olayda tukenir; sonraki olaylar BEDAVA
        r = ps.censorship_economics(100, 0.30, 100, 10, 0.0, refill=False)
        assert r["toplam_kesinti"] == pytest.approx(100)
        assert r["kalici_bond"] == pytest.approx(0)
        assert r["deterrente_yeterli"] is True

    def test_bond_fee_altinda_kesinti_bond_kadar(self):
        # bond<fee: slash = min(bond, fee) = bond
        r = ps.censorship_economics(100, 0.30, 25, 3, 0.0, refill=True)
        assert r["toplam_kesinti"] == pytest.approx(3 * 25)
        assert r["ilk_kesinti"] == pytest.approx(25)

    def test_bond_fee_altinda_refillsiz_hemen_tukenir(self):
        r = ps.censorship_economics(100, 0.30, 25, 5, 0.0, refill=False)
        assert r["toplam_kesinti"] == pytest.approx(25)
        assert r["kalici_bond"] == pytest.approx(0)

    def test_oyun_disi_fayda_esigi_asilirsa_yetersiz(self):
        # side_benefit*toplam_slash'i gectiginde net < 0 → YETERSIZ
        r = ps.censorship_economics(100, 0.30, 50, 10, 120.0, refill=True)
        assert r["oyun_disi_fayda"] == pytest.approx(1200.0)
        assert r["net_maliyet"] < 0
        assert r["deterrente_yeterli"] is False

    def test_oyun_disi_fayda_esigin_altinda_yeterli(self):
        r = ps.censorship_economics(100, 0.30, 50, 10, 40.0, refill=True)
        assert r["net_maliyet"] > 0
        assert r["deterrente_yeterli"] is True

    def test_net_sifir_esigi_kesindir(self):
        # net == 0 durumunda kat'i kosul (net>0) False → YETERSIZ
        r = ps.censorship_economics(100, 0.30, 100, 1, 100.0, refill=True)
        assert r["net_maliyet"] == pytest.approx(0.0)
        assert r["deterrente_yeterli"] is False

    def test_sifir_olay(self):
        # n_censor=0: kesinti yok, ama ilk_kesinti yine min(bond,fee) raporlanir
        r = ps.censorship_economics(100, 0.30, 100, 0)
        assert r["n_censor"] == 0
        assert r["toplam_kesinti"] == 0.0
        assert r["oyun_disi_fayda"] == 0.0
        assert r["net_maliyet"] == 0.0
        assert r["ilk_kesinti"] == pytest.approx(100)
        assert r["deterrente_yeterli"] is False
        assert r["kalici_bond"] == pytest.approx(100)

    def test_anahtarlar(self):
        r = ps.censorship_economics(100, 0.30, 100, 1)
        assert set(r) == {"n_censor", "ilk_kesinti", "toplam_kesinti",
                          "oyun_disi_fayda", "net_maliyet",
                          "deterrente_yeterli", "kalici_bond"}

    def test_ilk_kesinti_min_bond_fee(self):
        for bond in (25, 100, 500):
            r = ps.censorship_economics(100, 0.30, bond, 3)
            assert r["ilk_kesinti"] == pytest.approx(min(bond, 100))

    @pytest.mark.parametrize("n", [1, 2, 5, 10, 50])
    def test_refill_true_toplam_kesinti_dogrusal(self, n):
        # refill varsa toplam kesinti n*min(bond,fee) — dogrusal caydiricilik
        r = ps.censorship_economics(100, 0.30, 100, n, 0.0, refill=True)
        assert r["toplam_kesinti"] == pytest.approx(n * 100)

    def test_refill_false_toplam_min_bond(self):
        # refill yoksa toplam kesinti asla bond'u gecemez
        for n in (1, 5, 100):
            r = ps.censorship_economics(100, 0.30, 70, n, 0.0, refill=False)
            assert r["toplam_kesinti"] <= 70 + 1e-12
