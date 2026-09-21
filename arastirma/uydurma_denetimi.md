# İç Denetim Raporu — KÖK v2 EN Paketi

**Denetleyen:** Lead (Sester agent iki kez başlarken çöktü; görev bizzat alındı)
**Tarih:** 2026-09-21
**Kapsam:** uydurma referans taraması, sayısal tutarlılık, citasyon doğrulama,
EN/TR spec çapraz kontrol, test tablosu bütünlüğü.

---

## A) PROPER NOUN / UYDURMA TARAMASI — YAPILDI

**Yöntem:** 4 EN belgedeki tüm büyük harfli özel isimler çıkarıldı, kaynak
dosyalarda (KW_ANALIZ.md, PEARL_DOCS_ANALIZ.md, PROJE_KAGIDI_V2.md, KAYNAKLAR.md)
geçip geçmediğine bakıldı.

### BULGULAR:

1. **"Hawthorne-style governance" — UYDURMA, ÇIKARILDI.**
   - **Nerede:** KOK_V2_TECHNICAL_SPEC.md:281 (ve TR spec'te karşılığı).
   - **Kanıt:** kaynak dosyaların HİÇBİRİNDE geçmiyor; web'de "Hawthorne
     governance blockchain" araması boş döndü.
   - **Düzeltme:** somut 5 adımlı §A.11 whitelist governance ile değiştirildi
     (öneri → 2-epoch doğrulama → sıfır false-accept → versioned-schema
     aktivasyonu → simetrik çıkarma). TR spec'e de işlendi.

2. **Diğer tüm proper noun'lar — TEYİT EDİLDİ.**
   Hawkeye, Badash, Srivastava, Komargodski, Weinstein, Pass, Basu, Demirel,
   Sompolinsky, Wyborski, Zohar, Kaspa, Pearl, Freivalds, Peigné,
   Vaikuntanathan, Zamir, Polymath — hepsi kaynaklarda mevcut.
   **"Itamar Schen"** doğru şekilde **eski sürüm notu** olarak geçiyor
   (REFERENSLAR.md:60-61: "3 authors... Schen later withdrew" — bu bir hata
   değil, doğru düzeltmenin kaydı).

3. **Kaspa parametreleri — DÜZENLENDİ (uydurma değil, doğrulama-riski).**
   - `ghostdag_k=18, max_block_parents=10, mergeset=36` daha önce canlı
     rusty-kaspa repo'sundan okundu; **2026-09-21'de yeniden doğrulama
     denemesi github.com'a ulaşamadı (ağ bu oturumda kısıtlı).**
   - **Düzeltme:** KOK_V2_REFERENCES.md 6b girişine "verified earlier, not
     re-verified this session" notu eklendi; prototip bu değerleri
     **parametre** olarak aldığı için kod doğruluğundan ödün verilmedi.

**SONUÇ A: Bilinen bir uydurma referans kalmadı. Hawthorne tek ististi.**

---

## B) SAYISAL TUTARLILIK — YAPILDI, TÜMÜ TUTARLI

Spec'teki her sayısal iddia prototip çıktısıyla karşılaştırıldı:

| İddia | Dosya | Sonuç |
|---|---|---|
| TV-31 "bond 100/500/2000 same net (−40)" | bond_margin_proto_en.py | TUTARLI |
| TV-30 "DELTA=0.5 → 6.64%" | fp8_noise_proto_en.py | TUTARLI |
| TV-30 "analytic 0.217 → 3.52%" | fp8_noise_proto_en.py | TUTARLI |
| TV-30 "DELTA≤0.06 → 1.37%" | fp8_noise_proto_en.py | TUTARLI |
| TV-33 "+900 (no refill)" | bond_margin_proto_en.py | TUTARLI |
| TV-33 "−800 (refill)" | bond_margin_proto_en.py | TUTARLI |
| TV-32 "R²=1.0000" | bond_margin_proto_en.py | TUTARLI |
| Pass "Pearl calibration 5.8%" | pass_sim_en.py | TUTARLI |

**Sabit parametreler (spec vs kod):** W_r=3 ✓, fee=100 ✓, burn=30 ✓,
W_s=100 ✓, k=18 ✓, q=97 ✓, K=64 ✓. **Bir n=8/N=64 belirsizliği vardı
(g_layer'da JackpotToy K,N=64,64; KWKernel n=8) — bu bir çelişki değil:
iki farklı nesnenin boyutu (jackpot toy grid vs kernel). Spec her ikisini de
doğru kullanıyor.**

**SONUÇ B: Sayısal tutarsızlık bulunmadı.**

---

## C) CITASYON DOĞRULAMA — KISMEN YAPILDI

- **MiCA Regulation (EU) 2023/1114 — TEYİT EDİLDİ** (EUR-Lex CELEX:32023R1114,
  OJ L 150/40, 9.6.2023, tam metin 1.68 MB çekildi). Article 3 tanımları
  verbatim çıkarıldı: (5) crypto-asset, (6) ART, (7) e-money token,
  **(9) utility token**, (10) issuer. Uygulama tarihi 30 Dec 2024.
  **DÜZELTME: eski not "Article 3(1)(5)" diyordu; resmi numaralandırma (9).**
- **SEC v. Ripple — TEKRAR DOĞRULANAMADI.** CourtListener REST v4 sorgulandı
  (court=ca2, court=nysd, docket 20-cv-10932, docket id 646160) → **kayıt
  yok** (RECAP kapsamı dışında olabilir). sec.gov 403; arama motorları bot
  koruması. **Paper Ripple'dan alıntı yapmıyor** (Howey analizi iç kaynaklı,
  zaten "not verified" etiketli) — bu yüzden kusur değil, açıklamadır.
- **Diğer bibliyografi girişleri** (arXiv/ePrint ID'leri) bu oturumda ağ
  kısıtı nedeniyle **tekrar doğrulanamadı**; daha önceki oturumlarda
  doğrulanmıştı. **Risk kabul edildi ve açıkça yazıldı.**

**SONUÇ C: MiCA teyit edildi + numaralandırma düzeltildi. Ripple doğrulanamadı
(açıkça belirtildi). Kalan bibliography riski belgeli.**

---

## D) EN vs TR SPEC ÇAPRAZ KONTROL — YAPILDI

| Madde | EN spec | TR spec | Sonuç |
|---|---|---|---|
| TV-31..33 test tablosu | satır 430-432 | A.5.5 güncelleme bloğu | **TUTARLI** (TR'de tablo satırı yok ama güncelleme metni var — TR internal olduğu için kabul) |
| §A.5.5 bond-margin UPDATE | var | var | TUTARLI |
| Hawthorne → §A.11 | düzeltildi | düzeltildi | TUTARLI |
| GPU whitelist governance | §A.11 tanımlandı | §A.5.5 sonrası özet | TUTARLI |

**SONUÇ D: İki spec teknik olarak tutarlı.**

---

## E) TEST TABLOSU BÜTÜNLÜĞÜ — YAPILDI, EKSİKSİZ

- **Spec'te 33 TV (TV-1..TV-33), kodda hepsi mevcut.**
- spec'te olup kodda OLMAYAN: **YOK**
- kodda olup spec'te OLMAYAN: "TV-123" — **false positive** (regex
  birleşimi: TV-1 ve TV-23'ün aynı satırda; gerçek bir test değil).
- **7/7 EN prototip çalışıyor** (g_layer, u_layer, f3a, pass_sim, ghostdag,
  fp8 [negatif sonuçtan exit 1], bond_margin). Sayısal çıktılar TR ile özdeş.

**SONUÇ E: Test bütünlüğü tam.**

---

## TOPLAM SONUÇ

| Alan | Durum |
|---|---|
| Uydurma referans | **1 bulundu (Hawthorne), çıkartıldı, yerine gerçek tasarım kondu** |
| Sayısal tutarlılık | **0 çelişki** |
| Citasyon | MiCA teyit edildi + numaralandırma düzeltildi; Ripple doğrulanamadı (belgeli) |
| EN/TR tutarlılık | Tutarlı |
| Test bütünlüğü | 33/33 tam |

**Denetim öncesi puan: 77 → sonra: 79** (aşağıdaki kapatmalarla).

---

## C2) BIBLIOGRAPHY TEKRAR DOGRULAMA — 2026-09-21 (ePrint calisti)

ePrint HTML sayfalari (HTTP 200) ile 4 kritik girisi **birebir** teyit ettim:

| ePrint ID | Baslik (dogrulandi) | Yazarlar (dogrulandi) | Spec ile |
|---|---|---|---|
| 2025/685 | Proofs of Useful Work from Arbitrary Matrix Multiplication | **Ilan Komargodski, Omri Weinstein** (2 yazar) | UYUMLU (Schen duzeltmesi dogru) |
| 2018/104 | PHANTOM and GHOSTDAG: A Scalable Generalization of Nakamoto Consensus | **Yonatan Sompolinsky, Shai Wyborski, Aviv Zohar** | UYUMLU |
| 2017/203 | Proofs of Useful Work | **Marshall Ball, Alon Rosen, Manuel Sabin, Prashant Nalini Vasudevan** | UYUMLU (spec "Ball, Rosen, Sabin, Vasudevan" diyor, tamami teyit) |
| 2026/1492 | Proof of Demand Is Not Proof of Work: On the Limits of Demand-Weighted Consensus under Free Pseudonyms | **Omer Demirel, Snowfall Finance LLC** | UYUMLU (baslik tam; "Demirel Thm 2" referansi dogru) |

**SONUC C2: 4/4 kritik cryptography bibliography girisi 2026-09-21'de TEKRAR
DOGRULANDI. Kalan risk: sadece arXiv ID'leri (2504.09971, 2606.06700,
2606.04819) bu oturumda arXiv API bos dondugu icin teyit edilemedi —
daha onceki oturumlarda dogrulanmisti.**

---

## C3) *** BUTUN BIBLIOGRAPHY DOGRULANDI — 11/11 (2026-09-21) ***

Oturum 18'in basinda 4/4 ePrint teyit etmistim; simdi kalan 7 tanesi de
canli sayfalarla teyit edildi. **KOK v2 EN paketinin tum citasyon tabani
2026-09-21 itibariyle LIVE-VERIFIED.**

| # | ID | Baslik (dogrulandi) | Yazarlar (dogrulandi) | Kaynak |
|---|---|---|---|---|
| 1 | arXiv 2504.09971 | Proofs of Useful Work from Arbitrary Matrix Multiplication | Ilan Komargodski, Omri Weinstein | /abs/ 200 |
| 2 | arXiv 2606.06700 | The Economics of Proof-of-Useful-Work | **Rafael Pass** (tek yazar) | /abs/ 200 |
| 3 | arXiv 2606.04819 | The Usefulness Gap in PoUW: Pearl's cuPOW | **Abhinaba Basu** | /abs/ 200 |
| 4 | arXiv 2007.01046 | Proofs of Useless Work -- Positive and Negative Results | Maya Dotan, Saar Tochner | /abs/ 200 |
| 5 | arXiv 2209.03865 | Challenges of Proof-of-Useful-Work (PoUW) | Felix Hoffmann | /abs/ 200 |
| 6 | ePrint 2017/203 | Proofs of Useful Work | Marshall Ball, Alon Rosen, Manuel Sabin, Prashant Nalini Vasudevan | HTML 200 |
| 7 | ePrint 2018/104 | PHANTOM and GHOSTDAG | Yonatan Sompolinsky, Shai Wyborski, Aviv Zohar | HTML 200 |
| 8 | ePrint 2025/685 | (= arXiv 2504.09971) | Komargodski, Weinstein | HTML 200 |
| 9 | ePrint 2026/1492 | Proof of Demand Is Not Proof of Work | Omer Demirel, Snowfall Finance LLC | HTML 200 |
| 10 | ePrint 2024/1731 | Arc: Accumulation for Reed-Solomon Codes | Benedikt Bunz, Pratyush Mishra, Wilson Nguyen, William Wang | HTML 200 |
| 11 | ePrint 2025/1814 | SoK: Is Proof-of-Useful-Work Really Useful? | **Pratyush Dikshit (Uni Luxembourg)**, Ashkan Emami, Johannes Sedlmeir (Uni Muenster), Gilbert Fridgen | HTML 200 |

### *** ONEMLI YAN BULGU: ELESTIRMEN SECIMI DOGRULANDI ***
SoK ePrint 2025/1814'in ilk yazarı **Pratyush Dikshit — University of Luxembourg**.
Yani EPOSTA_SOK.md'deki elestirmen (pratyush.dikshit@uni.lu) bir PoUW
uzmanina isabet ediyor: "Is Proof-of-Useful-Work Really Useful?" SoK'unun
ilk yazari, 50'den fazla PoUW insasini incelemis. Bu, gonderi secimimizin
kurulmus nedenini aciklar — ve ulasilabilirlik (uni.lu people search) zaten
dogrulanmisti.

### Pass 2606.06700'DEKI " affiliation " NOTU (daha onceki bulgu)
Pass'in tek yazar oldugu teyit edildi. (Daha onceki oturumda "done while
consulting for Pearl Research Labs" ifadesi tespit edilmisti — COI
aciklamasi yok. Bu, paper'da ve e-postalarda ACIKLANMIS durumda.)

**SONUC C3: Bibliyografyada HIC dogrulanmamis veya supheli giris kalmadi.
Puan tablosundaki ">=10 bibliography girisi dogrulanmali" acigi TAMAMEN KAPANDI.**
