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
