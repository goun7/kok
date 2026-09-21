# Pazar Araştırması — KÖK v2

**Araştıran:** Lead (Tamga ağ hatası verdi, bizzat alındı)
**Tarih:** 2026-09-21
**Yöntem:** blockchain.info açık API (anlık, başarılı). CoinGecko 429 rate-limit.
DuckDuckGo/Bing bot koruması. EUR-Lex çalıştı.

---

## C) Bitcoin madencilik — CANLI VERI (blockchain.info API)

Kaynak: https://blockchain.info/q/* (anlık sorgu, her biri 2026-09-21 ~02:40 UTC+3)

| Metrik | Deger | API |
|---|---|---|
| Hashrate | **956,911,537,880 TH/s ≈ 956.9 EH/s** | /q/hashrate |
| Fiyat | **$81,162.26** | /q/24hrprice |
| Difficulty | **1.3276 × 10¹⁴** | /q/getdifficulty |
| Blok yüksekligi | **967,912** | /q/getblockcount |

**Not:** hashrate bir onceki cekiste 963.5 EH/s geldi (dogal dalgalanma). ~957-964 EH/s
araliginda.

### Paper ile tutarlilik: IYI
- Paper'daki "24 EH/s" Pearl'e aittir (Basu 2606.04819'dan kaynakli), BTC'ye degil.
- Paper'da BTC icin spesifik bir sayi iddia EDILMIYOR — sadece "Pearl 24 EH/s" var.
- **Sonuc:** paper'in pazar verileriyle celiskisi YOK. Canli BTC verisi paper'da
  kullanilmadigi icin guncelleme gerekmez; bu kayit gelecekteki kullanim icindir.

**Eski kayit (progress.md / v1):** "BTC 204.44 TWh/yr, ~904 EH/s, $81,448" — bu v1
  zamanindan. 904 EH/s -> ~957 EH/s olmus (yukari); fiyat $81,448 -> $81,162 (yakin).
  **v2 paper'i bu sayilari kullanmadigi icin duzeltme gerekmez.**

---

## A) AI compute pazar boyutu — BULUNAMADI
## B) Dagitik compute pazarlari (Render/Akash/io.net) — BULUNAMADI (CoinGecko 429)
## D) PoUW elestirileri — BULUNAMADI
## E) Pearl Labs 2026 durumu — BULUNAMADI

**DURUST NOT:** 4/5 sikkada dis arama bu oturumda basarisiz oldu. Paper'in mevcut
pazar iddialarinin hepsi **kaynakli** (Basu, Pearl'in kendi dokumanlari) — bu
oturumda uydurma riski tasimiyorlar. Bosluk: pazar boyutu TAHMINI hic yok (paper
"pazar boyutu tahmini yok" olarak puan kaybediyor; bu acik ve bilinen bir bosluk).

---

## A/B) *** AI COMPUTE PAZAR BOYUTU — COZULDU (2026-09-21) ***

**Yontem:** Arastirma firmalari (Gartner/Statista/McKinsey/GrandView/Fortune)
403/timeout verdi. *** Wikipedia API (calisiyor) ile Nvidia sayfasindan
resmi gelir rakamlari cekildi *** — Nvidia geliri AI-compute harcamasinin
en temiz VERGININ-FARKINDA proxy'sidir (GPU pazarinin baskin saglayicisi).

### NVIDIA YILLIK GELIR (Wikipedia tablosu, kaynakli)

| FY | Gelir (bn $) | Net gelir (bn $) | Calisan |
|----|----|----|----|
| 2022 | 26.9 | 9.7 | 22,473 |
| 2023 | 26.9 | 4.3 | 26,000 |
| 2024 | 60.9 | 29.7 | 29,600 |
| 2025 | 130 | 72.8 | 36,000 |
| *** 2026 | 215 | 120 | 42,000 *** |

**3 yilda 8 kat:** 26.9 (2023) -> 60.9 (2024) -> 130 (2025) -> *** 215 (2026) ***.
Bu artisin baskin kaynagi data-center AI compute.

### CEYREK (daha guncel, momentum)

- **Subat 2026:** Q4 FY2026 gelir **$68.1B** (rehberi ~$3B asti, onceki cevre
  uzerine %20); envanter $50.3B -> **$95.2B**; Q1 FY27 rehberi **$78B**.
- *** Agustos 2026: Q2 FY2027 geliri **$96.2B** — onceki yilin ayni ceyregine
  ($46.7B) gore **%106 artis**. *** (Yilliklestirilmis run-rate ~$380B.)

### DOGRUDAN YATIRIM (veri merkezi insasi)

- Nvidia -> OpenAI: **$100 milyar**yatirim MOU (22 Ekim 2025); OpenAI yeni AI
  veri merkezleri kuracak — *** en az 10 GW sistem gucu ***.
- Nvidia -> Nebius (AI cloud): **$2 milyar** (2026).

### KOK v2 ICIN ANALIZ (artik kaynakli)

Bu rakamlar "AI compute pazarinin ne kadar buyudugu" icin *** primer gosterge ***
sunar: GPU saglayicisinin geliri 2026'da $215B, hala %100+/yil buyuyor. Ama
*** onemli sinirlama acikca soylenmeli: *** Nvidia geliri = "butun AI harcamasi"
degildir (tumlesik sistemler, enerji, fasilye, personel bu sayinin disinda);
ayrica "permissionless bir zincirde ucretli gorev olarak fiyatlanan alt-kume"
hala BILINMEZ (F3a onu olecekle).

**SONUC: B SIKKI KAPANDI. Paper §8.1 artik "$215B 2026 geliri + %106 Q2 artisi
+ $100B/10GW OpenAI" ile somut bir pazar boyutu verebilir; kalan bilinmez
(permissionless alt-kume) hala acik ve boyle yazilmali.**
