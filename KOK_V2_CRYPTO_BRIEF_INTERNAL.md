# KÖK v2 — İÇ BELGE: aday seçimi ve çıkar-çatışması (gönderilmez)

> **Bu dosya KOK_V2_CRYPTO_BRIEF.md'nin eki DEĞİLDİR.** İç kullanım içindir —
> alıcıya gönderilemez, çünkü alıcının kendisini değerlendiren bir tablo içerir.
> İngilizce brief'te bilinçli olarak yer almaz.

## Aday tablosu (hepsi ePrint/arXiv sayfalarından doğrulandı, 2026-09-20)

| # | Aday | Kurum | Uzmanlık | Pearl bağı | Değerlendirme kapsamı |
|---|---|---|---|---|---|
| 1 | **Pratyush Dikshit** | University of Luxembourg | PoUW SoK (2025/1814); 50+ construction incelemesi; **utility≠security** tezi | **YOK** (akademik) | SORU-1, SORU-5 (yapısal saldırı sınıfı), SORU-6 |
| 2 | **Ashkan Emami** | University of Luxembourg | aynı SoK; **Toulmin-based claim evaluation** yöntemi | **YOK** | SORU-5 + §8 verdikt formatı |
| 3 | **Johannes Sedlmeir** | University of Münster | SoK; **PoUW ekonomi-modelleri** | **YOK** | SORU-4 (ε/n eşleştirme) |
| 4 | **Gilbert Fridgen** | University of Luxembourg | SoK; sistemleştirme metodolojisi | **YOK** | genel denetim + §9 toy-sınır |
| 5 | **Ömer Demirel** | Snowfall Finance LLC | **Proof of Demand ≠ PoW** (2026/1492); Thm 2; **Pearl cuPOW denetimi yapmış** | **KISMEN** — Pearl'i denetlemiş (İYİ: Pearl'ü bilir ama Pearl'den DEĞİL) | **SORU-1, SORU-3** + G/U mimarisinin kendi tezine karşı testi (en güçlü aday) |
| 6 | **Omri Weinstein** | (KW yazarı) | KW'nin kendisi | **YOK gibi** — Komargodski ile ortak; Komargodski Hawkeye yazarı (Pearl) | **ÇATIŞMA RİSKİ**: beyan şartı |
| 7 | **Dan Boneh** | Stanford | Hawkeye yazarı (Pearl) | **VAR** | **DIŞLANIR** |

## Önerilen iki-kişilik ekip

**Birincil: Ömer Demirel** (omer@progfi.xyz). Kendi Thm 2'si G/U mimarisinin teorik
temeli; Pearl'ü biliyor ama Pearl'den değil. **Risk:** tezi tasarımımıza ilham vermiş
olabilir → ikinci inceleyici bağımsız ekolden gelmeli.

**İkincil: Pratyush Dikshit** (pratyush.dikshit@uni.lu — uni.lu'dan RESMEN teyit edildi).
SoK ekolü; "utility güvenlik bütçesine katkı vermez" tezi G/U ayrımının fikri.

**Opsiyonel: Omri Weinstein** — sadece SORU-3 ile sınırlı, bağını beyan şartıyla.

## Adres teyit durumları
- pratyush.dikshit@uni.lu — RESMEN teyit (uni.lu/snt-en/people/pratyush-dikshit/, FINATRAX)
- johannes.sedlmeir@uni-muenster.de — kişi teyit (Acting Professor, Statistics Security
  & Trust), mail sayfada JS-obfuscation → ePrint adresi kullanılır
- omer@progfi.xyz — ePrint'ten (2026/1492 "Contact author(s)")
- ashkan.emami@uni.lu — ePrint'ten (2025/1814)

## Kendi standardımıza dürüst ayna
KW_ANALIZ.md'nin tamamı bir LLM okumasıdır (†); pass_sim_en.py Pass'in (Pearl danışmanı)
modelini kullanır → 2 inceleyici modelin kendisini de denetlemelidir (brief SORU-1).
