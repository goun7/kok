# ROUND-6 VERDICT DOGRULAMASI (IC DENETIM — SESTER)

**Denetci:** SESTER (ic denetim, fabrication audit)
**Tarih:** 20 Eylul 2026
**Kapsam:** Round-6 (commit `036917b`, `b2f4dde`, `f81618c`, `251d3e7`, `a61323f`, `a7b7c25`, `4845487`, `96efb48`) tarafindan duzeltilen sayilarin ve verdict siniflarinin EN paket ile tutarligi.
**Yontem:** Tum iddialar KOD CALISTIRILARAK teyit edildi (doc okumasi degil). `suite_gate_en.py` + her probe ayri ayri kosturuldu.

**ONEMLI NOT (denetim metodolojisi):** Bu oturumun basinda calisma alani snapshot'i STALE'di (Round-6 oncesi durum). Ilk `ls`, `read` ve hatta ilk `python3 pass_sim_en.py` calistirma sonucu eski snapshot'tan geldi (o snapshot'ta `eps in (0,1)` validasyonu varsayilan `eps=2.0`'i reddederek crash yapiyordu). Taze `bash` + `git blame` ile durum cozuldu: diskteki ve HEAD'deki dosya `prm.eps > 0.0` kullanir ("ROUND-6 NOTE: eps > 1 is LEGITIMATE ... rejecting eps > 1 would have broken the default run") ve rc=0 calisir. **ROUND-6'nin bu "fix"i dogru ve crash geri donmus degil.** Bu olay denetimin tum dosya okumalarinin taze bash ile caprazlanmasi gerektigini gosterdi; asagidaki her sonuc o sekilde alindi.

---

## SONUC: ROUND-6 VERDICT DOGRULANDI (4/4 ana sayi + verdict siniflari)

### 1. theta 1.05 -> 1.657, residual 2.24e-16 — TEYIT EDILDI

`python3 pass_sim_en.py` rc=0, sonuc:
```
- Pearl's real PR level gives endogenous theta=1.657 => the pure Duplexia regime.
  ROUND-5 endogenous PR consistency: implied PR reproduces the input to 2.24e-16
RESULT: PASS_SIM SOLVED — the equilibrium is an identity, input_consistency is the check that can fail
```
- TV-84 duzeltilmis `_theta_from_PR` (ustel `eps-1`, `eps` degil) calisiyor; `Eq.input_consistency()` (residual identity'sinin yapamadigini yapan falsifiable kontrol) geciyor.
- Nitel iddia da ayakta: 1.657 hala (theta_low=0.30, theta_high=3.33) icinde -> pure Duplexia.
- Eski deger 1.05 spec'te kalmamis: `grep "1.657"` spec C.8, TV-72, TV-77, TV-82 satirlarinda ve KOK_V2_PAPER.md icinde guncel degeri veriyor.

### 2. 184/199 kacis — TEYIT EDILDI (bagimsiz yeniden hesaplama)

`adoption_econ.py` rc=0. Sayi dosyanin PRINT ciktsinda degil (sadece comment+doc'ta), bu yuzden bagimsiz olarak yeniden hesaplandim (`tv36_cold_start` import edildi):
```
199-seed sweep (0.0001..0.0199) ratio 0.5 -> escapes: 184 of 199
all-seed absorbing threshold (199 seeds): 0.0893
ratio 0.0200 -> 0 of 199 (ABSORBING); 0.0800 -> 0 of 199 (ABSORBING)
ratio 0.0900 -> 2 of 199; 0.1000 -> 24 of 199; 0.7930 -> 198 of 199
```
- **184/199 dogru.** all-seed absorbing threshold 0.0893, dosyanin soyledigi "~0.08-0.10" ile tutarli. 0.79'un sadece seed 0.0002'nin 400 adimda gorunurluk cizgisini gectigi yer oldugu iddiasi da olculmus (0.7930'da 198/199 kacar, yani neredeyse hepsi).
- **Honest provenance notu (uydurma degil, teslimat gap'i):** 184/199 hicbir calistirilabilir ciktida gozukmez — sadece `adoption_econ.py:262` comment'inde ve paper/spec/progress'te "measured count" olarak sunulur. Ben olctum ve dogru; ama repo kendi bu sayiyi basmiyor. Ayrica dosyanin kendi icinde `line 262` "199 sub-barrier seeds" derken `line 531` "ALL 99 sub-barrier seeds" der (iki farkli seed kumesi: 0.0001..0.0199 vs 0.0002..0.0198). Sayilarin her ikisi de kendi olcumu acisindan dogru, ama bu provenance karmasasi bir temizlik maddesidir.

### 3. "2^256 (prod)" (2^255 degil) — TEYIT EDILDI

`python3 probe_field_scale_en.py` rc=0:
```
2^256 (prod) 2^256            2^768            2^64         infeasible
  256-bit field puts it at (2^256)^3 = ~2^768 at m=4.
  at 2^256 the same loop would need q^(m-1) = (2^256)^3 ~ 2^768 iterations, i.e. 1.5e+218
RESULT: SOUND
```
- ROUND-4'un "FIX: bit_length()" comment'inin kodda hic uygulanmamasi (her satir 1 eksik ust basiyordu: 2^256-1 -> 2^255) duzeltilmis; baslik artik `2^256 (prod)` ve kapali form `q^(m-1)` dogru veriliyor.

### 4. TV-46 burn=0 design — TEYIT EDILDI

`python3 probe_edges_en.py` rc=0, probes: 5/5:
```
TV-45 challenged-then-repaired settles   ACCEPT ch=CHALLENGED rep=SETTLED paid=1 burned=30 (expected 30)
TV-46 partial slash, buyer whole         ACCEPT state=SLASHED refund=100 slashed=30 burned=0
        (design: nothing delivered -> nothing burned, buyer made whole)
```
- burn artik her iki yolda bagli: SETTLED yolu 30 yakar (teslim edildi), SLASHED yolu 0 yakar (diger, tasarim karari). Bu "design, not bug" ayrimi olculmus olarak mevcut.

### Verdict siniflari (Round-6'nin tespit ettigi 3 sinif) — TEYIT EDILDI

`probe_ghostdag_en.py` rc=0, probes: 4/4:
```
TV-56 mergeset stays within past(B)         ACCEPT greedy=0 exact=0 X-in-past=False X-in-ms=False outside-past=0
TV-57 selected parent is a direct parent    ACCEPT violations=0
TV-58 blue_score strictly increases child->selected-parent  ACCEPT violations=0 over 396 edges
```
- **Ozdeslik sinifi kapanmis:** TV-56'nin `extra == set()` yeniden-hesaplama ozdesligi, `past(B)`'e karsin asiri-dahil etme testi ile degistirilmis (disarida birakma = 0). TV-58 aritmetik olarak imkansiz kontrol (`child = sp + blue + 1`) yerine yapisal `delta >= 1` testi konmus (396 kenar, 0 ihlal). TV-57 self-comparison olarak belgelenmis (regression guard).

- **Verdict baglanmamasi sinifi kapanmis:** `probe_g_layer_size_en.py` RESULT: PASS rc=0 (verdict artik FINDING'de sifirdan farkli cikis yapiyor — su an PASS); `probe_live_demand_en.py` RESULT: STATED rc=0 (phi=0 literal'i yerine ratio tanimi, veri yokken verdict fail ediyor); `probe_blindspot_en.py` rc=0 (escrow/burn gecisleri basiliyor, 572 literal'i hesaplanan listeden geliyor, bare `except Exception` artik KeyError'i raporluyor).

### Suite gate — TEYIT EDILDI

`python3 suite_gate_en.py` rc=0:
```
files reporting a self-consistent verdict: 39
files broken or verdictless:              0
```
Tum 39 in-scope EN dosyasi rc=0 ve kendi verdict'ini basiyor. (Not: `fp8_noise_proto_en.py` gibi "negative result" dosyalari rc=1 donerse de gate onlari verdict'lerinden tanir; Round-6 commit'inin "39/39, 0 broken" iddiasi dogrulandi.)

---

## YAPILDI / TEYIT EDILDI / SUPHELI / BULUNAMADI

- **YAPILDI**: Round-6'in 4 ana duzeltmesinin (theta 1.657 + 2.24e-16, 184/199, 2^256 prod, TV-46 burn=0) ve 3 verdict sinifinin (ozdeslik, verdict-baglanmamasi, "FIX comment ama kod ayni") EN paket ile tutarli oldugu, hepsi kosturularak olculdu.
- **TEYIT EDILDI**: suite_gate 39/39, 0 broken; tum probelar rc=0.
- **SUPHELI (teslimat, uydurma degil)**: 184/199 "measured count" olarak sunuluyor ama repodaki hicbir cikti uretmiyor (bagimsiz olcumum dogruluyor); ayrica ayni dosyada 199-seed (line 262) ile 99-seed (line 531) ifadeleri ayniymis gibi okunabilir.
- **BULUNAMADI**: Round-6 duzeltmelerinde uydurma (Hawthorne tipi) bir kaynak/protokol/sayi tespit edilmedi.

**Karar:** ROUND-6 verdict dogrulandi. Round-6'nin duzeltilen sayilari gercek olcumlerle elde ediliyor ve doc ile kod arasinda tutarli.
