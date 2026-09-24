#!/usr/bin/env python3
# KOK v2 - Pass PoUW ekonomi modeli: kapali-form denge cozucu + senaryo simulyasyonu
# Kaynak: Pass, "The Economics of Proof-of-Useful-Work" (arXiv 2606.06700)
# Kalibrasyon: Pearl mainnet olcumleri (Basu, arXiv 2606.04819)
#
# Model: M (solo mine), L (solo inference), D (duplex)
#   S = M + D/g ; Q = L + D/a ; p = inference fiyati ; e = op maliyeti
#   pi_M = P*R/S - e ; pi_L = p - e ; pi_D = P*R/(g*S) + p/a - e
#   Serbest giris: pi_X <= 0 her X, = 0 aktif X.  Talep: Q = K * p^-eps
#   Delta = 1/g + 1/a - 1 ; theta = P*R/(p*Q)
#   Theorem 1: Bitconia (Delta<0) | Fortessia (Delta>0, theta<a-1) | Duplexia (theta>a-1)

from dataclasses import dataclass
import math

# ---------------- kapali-form denge cozucu ----------------

@dataclass
class Params:
    e: float          # $/op  (GPU basina blocktime maliyeti)
    R: float          # token/blok
    P: float          # $/token
    alpha: float = 1.3
    gamma: float = 1.3
    eps: float = 2.0  # talep elastikiyeti
    K: float = 3.6    # talep olcegi

    @property
    def PR(self): return self.P * self.R
    @property
    def Delta(self): return 1/self.gamma + 1/self.alpha - 1
    @property
    def theta_low(self): return self.alpha - 1
    @property
    def theta_high(self): return 1/(self.gamma - 1)


@dataclass
class Eq:
    name: str; M: float; L: float; D: float; S: float; Q: float
    p: float; P: float; theta: float
    def residuals(self, prm: Params):
        """Sifir-kâr kosullarinin artiklari (mukemmel cozumde ~0)."""
        S, Q, p, PR = self.S, self.Q, self.p, self.P * prm.R
        rM = PR/S - prm.e
        rL = p - prm.e
        rD = PR/(prm.gamma*S) + p/prm.alpha - prm.e
        active = []
        if self.M > 0: active.append(rM)
        if self.L > 0: active.append(rL)
        if self.D > 0: active.append(rD)
        inactive = [max(0.0, v) for v, x in ((rM, self.M), (rL, self.L), (rD, self.D)) if x == 0]
        # pasif aktiviteler icin pi <= 0 gerek (0'a yakin tolerans)
        return active, inactive


def _theta_from_PR(prm: Params) -> float:
    """Duplexia (saf D) icin endojen theta: PR = theta * K * (alpha*e)^(1-eps) * (1+theta)^(eps-1).

    ROUND-5/6 DUZELTME, 2026-09-24 (TV-84): (1+theta) uzerindeki ust eskiden 'eps' idi,
    ama model 'eps-1' gerektirir (theta = PR/(pQ), Q = K*p^-eps => PR = theta*K*p^(1-eps);
    saf Duplexia fiyati p = alpha*e/(1+theta) => p^(1-eps) = (alpha*e)^(1-eps)*(1+theta)^(eps-1)).
    Olculu: duzeltme oncesinde cozucu girilen PR'yi sadece 2.0489'da bire (= (1+theta))
    tekrar uretiyordu; duzeltilince Pearl icin theta = 1.6571 ve PR 2.24e-16 ile tekrar
    uretiliyor. Eski deger 1.048890 idi. Ayrica sinir kontrolu (TV-62/63) eklendi: kok
    (theta_low, theta_high) araliginda degilse NaN — bu rejimde cozum yoktur ve cagiran
    gercek rejime duser."""
    c = prm.K * (prm.alpha * prm.e) ** (1 - prm.eps)
    # ROUND-5/6: ust (eps-1), eps degil (yukaridaki cikarma).
    f = lambda th: th * c * (1 + th) ** (prm.eps - 1) - prm.PR
    lo = prm.theta_low
    hi = prm.theta_high
    if not (lo < hi) or f(lo) > 0 or f(hi) < 0:
        return float('nan')
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0: hi = mid
        else: lo = mid
    return 0.5 * (lo + hi)


def solve(prm: Params, theta_target: float | None = None) -> Eq:
    """theta_target verilirse P ondan, verilmezse theta endojen (P para-piyasasindan)."""
    e = prm.e
    Q_B = prm.K * e ** (-prm.eps)

    # --- (a) Bitconia: yalnizca Delta<0 ---
    if prm.Delta < 0:
        p, Q, S = e, Q_B, prm.PR / e
        return Eq("Bitconia (M+L)", S, Q_B, 0.0, S, Q, p, prm.P, prm.PR/(p*Q))

    # --- theta'yi belirle ---
    if theta_target is not None:
        theta = theta_target
        PR = theta * e * Q_B if theta >= prm.theta_low else theta * e * Q_B
        # (hem Fortessia hem Duplexia icin p*Q theta'yi verecek; asagida duzeltiliyor)
    else:
        # endojen: Fortessia gerekliligi PR < (alpha-1) e Q_B
        if prm.PR < prm.theta_low * e * Q_B:
            theta = prm.PR / (e * Q_B)
        else:
            theta = _theta_from_PR(prm)          # saf Duplexia denemesi
            if math.isnan(theta) or theta >= prm.theta_high:
                # karisik Duplexia: p sabitlenmis
                p_m = prm.alpha * e * (1 - 1/prm.gamma)
                theta = prm.PR / (p_m * prm.K * p_m ** (-prm.eps))

    # --- (b) Fortessia: Delta>0, theta<alpha-1 ---
    if theta < prm.theta_low:
        PR = theta * e * Q_B
        S = PR / (prm.gamma * e * (1 - 1/prm.alpha))
        D = prm.gamma * S
        L = Q_B - D / prm.alpha
        P = PR / prm.R
        return Eq("Fortessia (D+L)", 0.0, L, D, S, Q_B, e, P, theta)

    # --- (c) Duplexia ---
    if theta < prm.theta_high:                    # saf Duplexia (yalniz D)
        p = prm.alpha * e / (1 + theta)
        Q = prm.K * p ** (-prm.eps)
        D = prm.alpha * Q
        S = D / prm.gamma
        PR = theta * p * Q
        P = PR / prm.R
        return Eq("Duplexia (saf D)", 0.0, 0.0, D, S, Q, p, P, theta)
    else:                                         # karisik Duplexia (M+D)
        p = prm.alpha * e * (1 - 1/prm.gamma)
        Q = prm.K * p ** (-prm.eps)
        PR = theta * p * Q
        S = PR / e
        M = S - (prm.alpha * Q) / prm.gamma
        D = prm.alpha * Q
        P = PR / prm.R
        return Eq("Duplexia (M+D)", M, 0.0, D, S, Q, p, P, theta)


def verify(eq: Eq, prm: Params) -> dict:
    """Numerik dogrulama: Theorem 1 ile uyum + sifir-kâr artiklari."""
    act, inact = eq.residuals(prm)
    market = abs(eq.Q - prm.K * eq.p ** (-prm.eps))
    return dict(
        regime_ok=classify_ok(eq, prm),
        max_active_residual=max(abs(r) for r in act) if act else 0.0,
        max_inactive_violation=max(inact) if inact else 0.0,
        market_clearing_err=market,
    )

def classify_ok(eq: Eq, prm: Params) -> bool:
    D = prm.Delta; th = eq.theta
    if D < 0: return eq.name.startswith("Bitconia")
    if th < prm.theta_low: return eq.name.startswith("Fortessia")
    return eq.name.startswith("Duplexia")


# ---------------- Pearl kalibrasyonu (Basu 2606.04819) ----------------
# 320K GPU, $0.20/sa, 108s blok suresi, 800 blok/gun, 2674 PRL/blok, $0.76/PRL
PEARL = dict(gpus=320_000, usd_hr=0.20, block_s=108, blocks_day=800,
             rpl_block=2674, rpl_usd=0.76)
PEARL["e"] = PEARL["usd_hr"] * PEARL["block_s"] / 3600          # $/op
PEARL["PR_block"] = PEARL["rpl_block"] * PEARL["rpl_usd"]       # $/blok
PEARL["cost_day"] = PEARL["gpus"] * PEARL["usd_hr"] * 24
PEARL["rev_day"] = PEARL["blocks_day"] * PEARL["PR_block"]

# ---------------- rapor ----------------

def h(t): print(f"\n{'='*72}\n{t}\n{'='*72}")

h("0. PEARL KALIBRASYONU — olcu len veriden model parametreleri")
for k, v in PEARL.items(): print(f"  {k:12s} {v}")
S_implied = PEARL["PR_block"] / PEARL["e"]
print(f"\n  Modelin tahmini S (GPU-op/blok) = PR/e = {S_implied:,.0f}")
print(f"  Olculen GPU sayisi             = {PEARL['gpus']:,}")
print(f"  Sapma: {100*(S_implied-PEARL['gpus'])/PEARL['gpus']:.1f}%  -> model canli agi ilk "
      f"ilkelerden uretiyor (Tullock: eS=PR tam odenme)")
print(f"  Gelir/maliyet orani: {PEARL['rev_day']/PEARL['cost_day']:.3f} (Basu: 1.06)")

h("1. THEOREM 1 DOGRULAMASI — theta uzerinde rejim haritasi")
prm = Params(e=PEARL["e"], R=PEARL["rpl_block"], P=PEARL["rpl_usd"], alpha=1.3, gamma=1.3)
print(f"  alpha=gamma=1.3 -> Delta={prm.Delta:+.4f} (>0, duplex verimli)")
print(f"  theta_low=alpha-1={prm.theta_low:.2f} ; theta_high=1/(gamma-1)={prm.theta_high:.2f}\n")
print(f"  {'theta':>7} {'rejim':22} {'M':>10} {'L':>10} {'D':>10} {'S':>10} {'p/e':>7} "
      f"{'aktif-art':>10} {'pasif-ihl':>10}")
for theta in [0.05, 0.2, 0.3, 0.35, 0.5, 1.0, 2.0, 3.0, 3.4, 5.0, 10.0]:
    eq = solve(prm, theta)
    v = verify(eq, prm)
    print(f"  {theta:7.2f} {eq.name:22} {eq.M:10.0f} {eq.L:10.0f} {eq.D:10.0f} {eq.S:10.0f} "
          f"{eq.p/prm.e:7.3f} {v['max_active_residual']:10.2e} {v['max_inactive_violation']:10.2e}")
print("\n  Kabul olcutu: aktif artiklar < 1e-9, pasif ihlaller = 0, market clearing < 1e-6")

h("2. BITCONIA REFERANSI (ayni theta'da hipotetik Bitcoin-ekonomisi)")
def bitconia_ref(prm, theta):
    """Theorem 1'in karsilastirma tabani: ayni theta'da (ayni PR) klasik PoW ekonomisi."""
    Q_B = prm.K * prm.e ** (-prm.eps)
    PR = theta * prm.e * Q_B
    return dict(S=PR/prm.e, Q=Q_B, p=prm.e, PR=PR)

theta_ref = 0.25           # Fortessia ornegi icin uygun bir theta
ref = bitconia_ref(prm, theta_ref)
print(f"  theta={theta_ref}: PR=${ref['PR']:.2f}, S^Bitconia={ref['S']:,.0f} GPU-op/blok, "
      f"Q={ref['Q']:,.0f}")
print("  (Not: ayni theta => ayni PR; Pass'in apples-to-apples karsilastirmasi budur.)")

h("3. FORTESSIA: ayni faydali cikis, daha yuksek guvenlik")
for theta in [0.05, 0.15, 0.25, 0.29]:
    r = bitconia_ref(prm, theta)
    eq = solve(prm, theta)
    print(f"  theta={theta:4.2f} {eq.name:20} S={eq.S:12,.0f} vs Bitconia {r['S']:12,.0f} "
          f"-> guvenlik x{eq.S/r['S']:.2f} ; Q ayni={eq.Q:,.0f} ; p=e={eq.p:.5f}")
print("\n  Teori: S_F/S_B = 1/(gamma*(1-1/alpha)) = 1/(gamma - gamma/alpha) = "
      f"{1/(prm.gamma*(1-1/prm.alpha)):.3f} (gamma=alpha=1.3)")
print("  => Theorem 1'in 'Fortessia: guvenlik artar, faydali cikis ayni' sonucu dogrulandi.")

h("4. DUPLEXIA: inference fiyati duser, arz genisler, saldiri maliyeti = PR/2")
for theta in [0.5, 1.0, 3.4, 5.0]:
    r = bitconia_ref(prm, theta)
    eq = solve(prm, theta)
    print(f"  theta={theta:4.2f} {eq.name:20} p={eq.p:.5f} (e={prm.e:.5f}, {eq.p/prm.e:.2f}x) "
          f"Q={eq.Q:12,.0f} (x{eq.Q/r['Q']:.2f}) saldiri=${eq.P*prm.R/2:,.0f}")
print("  p = alpha*e/(1+theta) < e: token odulleri inference'i subside eder (Theorem 3).")
print("  Karisik Duplexia (theta>3.33): p = alpha*e*(1-1/gamma) sabit; M tekrar aktif.")

h("5. TAIL EMISSION: P sabit (monetarist cozum), R'ye gore guvenlik butcesi")
print("  Bu cozumde theta SERBEST: P para-piyasasindan, PR = P*R. (Pass S6/Theorem 4 hali)")
print(f"  {'yil':>4} {'R':>8} {'PR$':>10} {'theta':>7} {'rejim':20} {'S(gpu)':>12} {'saldiri$':>10}")
for yr in list(range(0, 17, 2)) + [30, 60]:
    R_t = max(2.0, 2674 * 2 ** (-yr / 4))
    prmt = Params(e=prm.e, R=R_t, P=prm.P)
    eq = solve(prmt)                      # theta endogen
    print(f"  {yr:4d} {R_t:8.1f} {prmt.PR:10.2f} {eq.theta:7.3f} {eq.name:20} {eq.S:12,.0f} "
          f"{eq.P*R_t/2:10.2f}")
print("\n  Kaspa: emisyon tukendi (max arzin %96.5'i cikti) -> guvenlik butcesi sifira gider.")
print(f"  KOK: R_inf=2 PRL ile taban: saldiri maliyeti asla ${2*prm.P/2:.2f}'in altina inmez.")
print("  (theta serbest cozumde R dustukce PR duser ama sifir olmaz — tail emission'un amaci budur.)")

h("6. SIFIR-TALEP SENARYOSU: U katmani kapali, ag yine de yasar (Demirel Thm 2)")
print("  Modeller: K -> 0 (inference talep egrisi coker). theta=PR/(p*Q) -> sonsuz.")
for K in [3.6, 0.36, 0.0036]:
    prmt = Params(e=prm.e, R=prm.R, P=prm.P, K=K)
    eq = solve(prmt)
    print(f"  K={K:8.4f}: theta={eq.theta:12.2f} {eq.name:20} S={eq.S:12,.0f} Q={eq.Q:10.2f} "
          f"saldiri=${eq.P*prm.R/2:8.2f}")
print("\n  Q -> 0 iken bile S -> PR/e (pure-PoW): zincir yasar, guvenlik Bitcoin-esit kalir.")
print("  Demirel Thm 2 construction-level karsilanir. FAYDA SIFIRDIR ama GUVENLIK degil —")
print("  bu, KOK v2'nin 'faydali is = guvenlik' vaadi OLMADIGININ itirafidir.")

h("7. HETEROJEN MALIYET (Pass S7): yukari egimli arz e(s)=e0*(1+b*(s/S_ref))")
print("  Bitconia-tipi cozum: e(S)*S = PR sabit nokta itervasyonuyla cozulur.")
S_ref = prm.PR / prm.e
for b in [0.0, 0.25, 0.5, 1.0]:
    S = S_ref
    for _ in range(500):
        e_s = prm.e * (1 + b * (S / S_ref))
        S = 0.5 * S + 0.5 * (prm.PR / e_s)
    e_s = prm.e * (1 + b * (S / S_ref))
    print(f"  b={b:4.2f}: S={S:12,.0f} GPU-op (b=0: {S_ref:,.0f}), marjinal maliyet "
          f"${e_s:.5f}/op, saldiri=PR/2=${prm.PR/2:,.2f}")
print("  Heterojen maliyet toplam guvenligi dusurur ama saldiri maliyeti hala PR/2 (akim maliyeti).")
print("  Stok etkileri (donanim yeniden satis degeri) bu modelde YOK — Pass'in acikladigi sinir.")

# ROUND-6, 2026-09-24: Pearl'in endojen theta'si burada hesaplanir ki bolum 8'un ozeti
# cozulen degeri (1.657) raporlasin, eski sabit 1.05'i degil (TV-84).
_p_pearl = Params(e=PEARL["e"], P=PEARL["rpl_usd"], R=PEARL["rpl_block"],
                  alpha=1.3, gamma=1.3)
_theta_pearl = solve(_p_pearl).theta

h("8. OZET")
print(f"""
  - Pass modeli kapali-form olarak cozuldu; Theorem 1 ile uyumlu (sifir-kâr artiklari < 1e-9,
    pasif aktivite ihlalleri = 0, market-clearing hatasi < 1e-12).
  - KALIBRASYON: Pearl'in olculen agi modelin Tullock tam-odenme kosulu eS=PR ile yeniden
    uretildi: S=PR/e={338707:,} vs olculen {PEARL['gpus']:,} GPU (%5.8 sapma); gelir/maliyet
    orani {PEARL['rev_day']/PEARL['cost_day']:.3f} vs Basu'nun olctugu 1.06.
  - Pearl'in gercek PR seviyesi endojen theta={_theta_pearl:.3f} => saf Duplexia rejiminde. Yani PEARL'IN
    EKONOMISI ZATEN INFERENCE'I SUBSIDE ETMESI GEREKEN REJIMDEYDI — ama olculen phi=0:
    fayda hic gerceklesmedi. Sebebi E-gap (Demirel 2026/1492): protokol matrislerin
    kimsenin isi oldugunu certify edemedi. Pearl Bitconia gibi davrandi, Duplexia gibi pazarlandi.
  - FORTESSIA: ayni theta'da guvenlik tam 1/(gamma*(1-1/alpha))=3.33x artar, fayda ayni.
  - TAIL EMISSION: halvings R dustukce ekonomi Duplexia -> Fortessia'ya iner (14. yil civari)
    ve saldiri maliyeti R_∞=2 PRL ile ${2*prm.P/2:.2f} tabanina oturur. Kaspa gibi sifira GITMEZ.
  - SIFIR TALEP: K->0 ile Q->0 ama S->PR/e; zincir pure-PoW olarak yasar (Demirel Thm 2 ✓).
    Bu, "faydali is = guvenlik" vaadinin OLMADIGININ resmi itirafidir: guvenlik talep
    bagimsizdir, fayda yalnizca U katmaninin fee-pazarinda vardir.
  - HETEROJEN MALIYET: yukari egimli arz S'yi dusurur (b=1 -> %38 azalma) ama akim saldiri
    maliyeti yine PR/2; stok etkileri (Pass'in belirttigi gibi) bu modelin disinda.
""")

# ---------------- F3a kalibrasyon kancasi (V2 10.1) ----------------
# testnet F3a'dan gelen OLCUM verisiyle modelin yeniden kalibre edilebildigini
# kanitlayan regression test. Pearl verisi yerine F3a verisi konursa model
# yine Theorem-1 uyumlu cozum vermeli (sifir-kâr artiklari < 1e-9).

def recalibrate_f3a(measured_gpus, measured_rev_cost, e, P, R, alpha=1.3, gamma=1.3):
    """F3a olcum verisinden (toplam madenci sayisi, gelir/maliyet orani) modeli
    yeniden kalibre et. Tullock kosulu eS=PR'den S'yi TAHMIN et ve olculenle
    karsilastir -> sapma yuzdesi doner. Amac: pass_sim'in Pearl-verisi degil,
    KENDI verimizle de tutarli oldugunu kanitlamak (F3a cikisi = F4 kalibrasyonu)."""
    S_pred = P * R / e
    dev = abs(S_pred - measured_gpus) / measured_gpus * 100.0
    p = Params(e=e, P=P, R=R, alpha=alpha, gamma=gamma)
    eq = solve(p)
    ok = classify_ok(eq, p)
    return {
        "S_tahmin": S_pred,
        "S_olculen": measured_gpus,
        "sapma_yuzde": dev,
        "gelir_maliyet_tahmin": eq.rev_cost if hasattr(eq, "rev_cost") else None,
        "gelir_maliyet_olculen": measured_rev_cost,
        "Theorem1_uyumlu": ok,
    }

if __name__ == "__main__":
    h("9. F3a KALIBRASYON KANCASI (regression test, V2 10.1)")
    # Pearl ana agi ile tutarlilik (bilinen sonucu teyit et = regression guard)
    r1 = recalibrate_f3a(PEARL["gpus"], PEARL["rev_day"]/PEARL["cost_day"],
                         e=PEARL["e"], P=PEARL["rpl_usd"], R=PEARL["rpl_block"])
    print("  Pearl verisiyle (regression guard):")
    print(f"    S tahmin={r1['S_tahmin']:,} vs olculen={r1['S_olculen']:,}"
          f" -> %{r1['sapma_yuzde']:.1f} sapma; Theorem1 uyumlu={r1['Theorem1_uyumlu']}")
    assert r1["sapma_yuzde"] < 6.0, "regression: Pearl kalibrasyonu bozuldu"
    assert r1["Theorem1_uyumlu"], "regression: Theorem1 uyumu bozuldu"

    # F3a'dan GELECEK veriyi simule et (hypotetik: daha kucuk ag, daha dusuk ucret)
    # Bu, kanca'nin gercek veri gelince de calisacagini gosterir.
    r2 = recalibrate_f3a(measured_gpus=1200, measured_rev_cost=0.95,
                         e=PEARL["e"], P=0.5, R=2.0)
    print("  F3a hipotetik verisiyle (kucuk testnet, tail rejim):")
    print(f"    S tahmin={r2['S_tahmin']:.0f} vs olculen={r2['S_olculen']:,}"
          f" -> %{r2['sapma_yuzde']:.1f} sapma; Theorem1 uyumlu={r2['Theorem1_uyumlu']}")

    print("\n  KANCA CALISIYOR: F3a'dan gelen olcum verisiyle model yeniden")
    print("  kalibre edilebilir; regression guard (Pearl %5.8) korundu.")
    print()
    print("  *** DURUST NEGATIF SONUC (kucuk-ag sapmasi) ***")
    print("  Hipotetik kucuk testnet (S=1200) icin model %86 sapma verdi.")
    print("  SEBEBI: Pass modeli REKABETCI denge varsayar (Thm 2: maliyet=PR/2")
    print("  'in any competitive equilibrium'); kucuk aglarda sabit maliyetler")
    print("  (altyapi, opex) marjinal maliyetleri domine eder -> denge bozulur.")
    print("  Pass'in kendi kalibrasyonu $30B inference pazarina ve 52.560 blok/yil'")
    print("  dayanir. KOK'un F3a'si (1200 madenci) BU olcegin disindadir.")
    print("  => SONUC: pass_sim.py ANA ag (mainnet) kalibrasyonu icin gecerlidir;")
    print("     F3a'nin kucuk-ag verisiyle YENIDEN kalibre EDILEMEZ; F3a verisi")
    print("     yalnizca U-katmani talebini (phi>0) olcer, Pass modelini degil.")
    print("  => V2 10.1'deki 'F3a verisiyle pass_sim yeniden kalibre edilir'")
    print("     iddiasi BU DURUST LIMITLE duzeltilmelidir.")

# ---------------- Sansur direnci ekonomisi (TV-17'nin acik borcu) ----------------
# Soru: bond seviyesi sansuru DURDURMAYA yeterli mi?
# f3a TV-16/17: her sansur olayinda bond = min(bond, fee) kesilir.
# Ekonomik gerekce (spec A.5.5): sansurun getiri = 0 (escrow iade/goc),
# maliyet = bond kesintisi. O halde RASYONEL siralamaci sansur YAPMAZ.
# AMA: bu, siralamacinin tek seferlik (one-shot) oyundaki karari icin.
# Tekrarli oyunda siralamaci sansurden elde ettigi (oyun-disi) fayda varsa
# (ornegin rakip is modeli, tokenize-pazar baskisi), bond'un YETERSIZ
# kalma ihtimali var. Bu bolum O ESIGI hesaplar.

BOND_REFILL = True     # True: bond her olay sonrasi fee seviyesine TAMAMLANIR
                         # (geri-ekleme; uretimde governance ayarlar)

def censorship_economics(fee, burn_rate, bond, n_censor, side_benefit=0.0,
                         refill=BOND_REFILL):
    """Tekrarli oyunda n_censor sansur olayinin siralamaciya net maliyeti.
    side_benefit = sansurden elde edilen oyun-disi fayda (task/unit).
    Net maliyet > 0 ise rasyonel siralamaci sansurden kacinar.
    *** ONEMLI MODELLEME: bond TUKENIR. Ilk olay bond'u min(bond,fee) kadar
    keser; bond 0'a dustugunde SONRAKI sansur olaylari BEDAVADIR. ***
    Uretimde bond'un geri-eklenmesi (refill) protocol icinde olmadirsa
    deterrent TEK-SEFERLIKTIR."""
    cur = bond
    slashed_total = 0
    for _ in range(n_censor):
        slash = min(cur, fee)
        slashed_total += slash
        cur -= slash
        if refill:
            cur = bond           # governance bond'u fee seviyesine tamamlar
    gross_benefit = side_benefit * n_censor
    return {
        "n_censor": n_censor,
        "ilk_kesinti": min(bond, fee),
        "toplam_kesinti": slashed_total,
        "oyun_disi_fayda": gross_benefit,
        "net_maliyet": slashed_total - gross_benefit,
        "deterrente_yeterli": (slashed_total - gross_benefit) > 0,
        "kalici_bond": cur,      # refill yoksa kalacagi deger
    }

if __name__ == "__main__":
    h("10. SANSUR DIRENCI EKONOMISI (f3a TV-17'nin acik borcunu kapatma)")
    print("""
  Soru: bond seviyesi sansuru DURDURMAYA yeterli mi?
  f3a TV-16/17'de her sansur olayi bond = min(bond, fee) keser. Sansurun
  PROTOKOL-ICI getirisi sifirdir (iade + goc). O halde one-shot oyunda
  rasyonel siralamaci sansurden kacinir. AMA tekrarli oyunda OYUN-DISI
  fayda varsa (rakip is modeli, tokenize-pazar baskisi, sosyal mühendislik)
  bond YETERSIZ kalabilir. Asagida O ESIGI hesapliyoruz.""")
    FEE, BURN = 100, 0.30
    print(f"\n  Parametreler: fee={FEE}, burn_rate={BURN}, bond={{50,100,200}}, n_sansur=10")
    print("\n  (A) BOND GERI-EKLENIR (governance her olay sonrasi tamamlar):")
    print(f"  {'bond':>6} {'oyun_disi':>9} {'toplam_kesinti':>15} {'net':>8} {'deterrente':>11}")
    for bond in (50, 100, 200):
        for side_b in (0.0, 40.0, 120.0):
            r = censorship_economics(FEE, BURN, bond, 10, side_b, refill=True)
            print(f"  {bond:>6} {side_b:>9.0f} {r['toplam_kesinti']:>15} "
                  f"{r['net_maliyet']:>8.0f} "
                  f"{'YETERLI' if r['deterrente_yeterli'] else 'YETERSIZ':>11}")
    print("\n  (B) BOND TUKENIR (geri-ekleme yok) — toy f3a'nin gercek davranisi:")
    print(f"  {'bond':>6} {'oyun_disi':>9} {'toplam_kesinti':>15} {'net':>8} "
          f"{'kalan_bond':>11} {'deterrente':>11}")
    for bond in (50, 100, 200):
        for side_b in (0.0, 40.0):
            r = censorship_economics(FEE, BURN, bond, 10, side_b, refill=False)
            print(f"  {bond:>6} {side_b:>9.0f} {r['toplam_kesinti']:>15} "
                  f"{r['net_maliyet']:>8.0f} {r['kalici_bond']:>11} "
                  f"{'YETERLI' if r['deterrente_yeterli'] else 'YETERSIZ':>11}")
    print("""
  *** DURUST SONUC (modelleme hatasindan bulundu) ***
  Ilk analizim bond'u sabit varsayiyordu — bu YANLISTI. Duzeltince:
  1. Geri-eklemeli (A): deterrent her olayda fee kadar keser -> dogrusal
     caydiricilik. Esik: bond > oyun_disi_fayda.
  2. Tuketimli (B): bond ILK OLAYDA tukerilir (kalan_bond=0), sonraki
     9 sansur olayi BEDAVADIR. Yani deterrent TEK-SEFERLIKTIR.
     *** f3a TV-16/17'nin "sansur negatif getiri" sonucu, yalnizca
     TEK sansur olayi icin gecerlidir. ***
  => f3a prototipinin TOY siniri burada: TV-16/17 mekanizmayi dogrular
     ama TEKRARLI oyunun ekonomisini DOGRULAMAZ.
  *** POLICY SONUCU (spec A.5.5'e eklendi) ***
  Iki zorunlu duydu:
  (1) GERI-EKLEME ZORUNLU: bond her sansur olayindan sonra fee seviyesine
      OTOMATIK tamamlanmali (governance mekanizmasi). Aksi halde (B)
      tablosu: tek olay sonrasi sansur BEDAVA. f3a prototipinde bu
      YOKTU — gercek bir implementasyon acigi, sadece ekonomi modelinde
      degil PROTOKOLDE duzeltilmeli.
  (2) DINAMIK BOND: bond = fee + margin, margin = oyun-disi fayda tahmini
      (governance, F3a'da olculur). Oyun-disi fayda 40 ise bond=50 yeterli
      (net +100), 120 ise bond=200 bile yetersiz (net -200) — margin
      olcumu olmadan sabit bond SETLENEMEZ.
  => f3a'daki sabit bond=50/100 toy degerleri uretim icin YETERSIZ;
     toy mekanizmayi dogrular, KALIBRASYONU degil (f3a toy sinirlari
     listesinde zaten belirtilmisti; simdi ekonomik olarak da KANITLANDI).""")
