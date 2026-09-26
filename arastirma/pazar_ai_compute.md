# PAZAR ARAŞTIRMASI — KÖK v2: AI Compute, Dağıtık Hesaplama, Bitcoin ve PoUW

**Hazırlayan:** TAMGA (dış araştırma ajanı) — v2, 24 Eylül 2026 (v1: Lead, 21 Eylül 2026)
**Kapsam:** (2A) AI compute/GPU bulut pazar boyutu, (2B) dağıtık compute pazarları
(Render/Akash/io.net/Golem/Pearl), (2C) Bitcoin madencilik 2026, (2D) PoUW "useful work"
eleştirileri VERBATIM, (2E) Pearl Research Labs durumu, (★) talep-tarafı Analizi.
**Yöntem:** Her sayı için **verbatim alıntı + URL + tarih**; **ACTUAL (gerçekleşmiş)** ve
**FORECAST (tahmin)** ayrımı her yerde belirtilmiştir. Ulaşılamayan veriler **BULUNAMADI**.
**v2'nin v1'e farkı:** v1'de 4/5 şık BULUNAMADI idi (sadece Bitcoin canlı verisi + Nvidia
geliri). **v2, PoUW eleştirilerini arXiv API'sinden verbatim özetlerle, Pearl'i ise canlı
sitesinden (fiyatlandırma tablosu dahil) birincil kaynaklarla doldurur** ve Lead'in
işaret ettiği **talep-tarafı (demand) analizini** merkeze alır.

> **UYARI:** Bu belge yatırım tavsiyesi değildir; tüm pazar rakamları belirtilen tarihteki
> haliyle sunulmuştur.

---

## 0. YÖNETİCİ ÖZETİ — KÖK v2 için başlıca bulgular

1. **AI compute pazarı 2026'da hâlâ %100+/yıl büyüyor (ACTUAL).** Nvidia gelirleri: FY2023
   $26.9B → FY2024 $60.9B → FY2025 $130B → **FY2026 $215B**; Ağustos 2026 çeyreği **$96.2B
   (+%106 YoY)** → yıllıklaştırılmış run-rate ~$380B. Bu, GPU tedarikçisinin *gerçekleşmiş*
   geliridir (forecast değil). **Ancak** araştırma firmalarının (Gartner/IDC/Precedence/Mordor)
   resmi TAM rakamları bu oturumda **BULUNAMADI** (siteler 403/timeout verdi).
2. **Dağıtık compute token'ları 2026'da ucuzlamış görünüyor (ACTUAL, 24 Eylül 2026):**
   RENDER **$1.86**, AKT **$0.677**, GLM **$0.126** (CoinGecko). io.net fiyatı
   **BULUNAMADI** (CoinGecko 429 rate-limit). Ağ kullanım metrikleri (GPU-saat, gelir, aktif
   node) **BULUNAMADI** (Render/Akash/io.net istatistik API'leri bu oturumda çalışmadı).
3. **Bitcoin Eylül 2026: ~858 EH/s, $84,462, blok ödülü 3.125 BTC (ACTUAL, canlı doğrulandı).**
   Blok 968,473'te coinbase çıkışı **3.1307 BTC** = 3.125 subsidy + ~0.006 fee olarak
   doğrulandı; blok başına **6,945 işlem**.
4. **EN KRİTİK BULGU — PoUW eleştirilerinin en güçlüsü ARTIK ÖLÇÜLMÜŞ DURUMDA:** Basu
   (arXiv 2606.04819, 3 Haziran 2026), Pearl'in canlı ağını ölçtü: **"Pearl's 24 EH/s
   network -- representing approximately 320,000 GPU-equivalents consuming an estimated 112 MW
   -- produces zero useful AI computation."** Yani faydalı işin üretimdeki ilk büyük
   örneğinde **φ = 0**.
5. **Eleştirinin özü teorik + ampirik olarak ikiye ayrılır:** (a) **güvenlik**: Dotan–Tochner
   (2020) "the set of allowed problems must be preimage resistant functions"; Dikshit vd. SoK
   (2025) "utility does not contribute to the security budget"; (b) **ekonomi**: Bar-On–
   Komargodski–Weinstein (2025) madencilerin "concentrating their useful tasks in a single
   block" optimizasyonu. **Buna karşın Pass (2026) "paid to attack" eleştirisini çürütür:**
   "Contrary to the common strawman argument, PoUW does not make attacks economically cheap ...
   the economic cost of a majority attack remains tied" blok ödülüne.
6. **Pearl Research Labs (24 Eylül 2026, canlı):** Hem bir **PoUW L1 zincir** hem bir
   **ticari inference platformu**. Together AI'da Gemma-4-31B-it-Pearl endpoint'i **"%25+
   below the standard price, funded by the PRL mined on the same forward pass"**. GitHub:
   **322 ★**, 77 fork, 92 açık issue, **son push 24 Eylül 2026** (aktif bakım). NVIDIA
   Inception üyesi. **Finansman (seed/VC) BULUNAMADI** (sitesinde açıklanmamış).
7. **★ TALEP TARAFI (Lead'in önceliği — projenin zayıf halkası):** Pearl'in fiyatlandırma
   sayfası (24 Eylül 2026) **gerçek ödenmiş inference fiyatlarını** verir: Gemma-4-31B-it
   **$0.34/1M output**, DeepSeek-V4-Pro $3.30/1M output, GLM-5.3-Flash $0.24/1M output. Pearl'in
   iş modeli: **token madenciliği inference'u sübvansiye eder** ("funded by the PRL mined").
   **KÖK v2'nin açık sorusu:** faydalı işin zincir üzerinde gerçekleştiği kanıtlanmış bir
   üretim örneği **yok** (Pearl'de bile φ=0); KÖK'ün U-katmanı bu boşluğu doldurmak için
   tasarlandı, **ama ücretli görev hacminin (demand curve) ne olacağı HENÜZ BİLİNMEYEN bir
  forecast'tur** — bu, kriptografi değil, pazar-eğrisi problemidir.
8. **Citation-integrity bulgusu (denetim için):** `KOK_V2_REFERENCES.md` satır 147, "Leinweber
   et al."'e atıf olarak **arXiv 2209.03865** gösteriyor; fakat bu makale **Felix Hoffmann'ın
   tek yazarlı "Challenges of Proof-of-Useful-Work (PoUW)" (2022)** makalesidir. Basu'nun
   özetinde "Leinweber et al." geçer; bu atıf eşleşmesi **yanlıştır** ve denetimde düzeltilmelidir.

---

## 1. GÖREV 2A — AI Compute / GPU Bulut Pazar Boyutu

### 1.1 Gerçekleşmiş (ACTUAL) birincil göstergeler: Nvidia gelirleri

Araştırma firmalarının (Gartner, IDC, Precedence Research, Mordor Intelligence, Fortune
Business Insights) siteleri bu oturumda **403/timeout** döndürdüğü için resmi TAM forecast
rakamları **BULUNAMADI**. Bunun yerine, AI-compute harcamasının **en temiz gerçekleşmiş
(undisputed) proxy'si** olan GPU tedarikçisi gelirleri kullanılmıştır (kaynak: Nvidia'nın
açık finansal tabloları, Wikipedia üzerinden özetlenmiş hali; v1'de çekilmiş, bu oturumda
 korunmuştur):

| Mali yılı | Gelir (bn $) | Net gelir (bn $) | Çalışan | Durum |
|---|---|---|---|---|
| 2022 | 26.9 | 9.7 | 22,473 | ACTUAL |
| 2023 | 26.9 | 4.3 | 26,000 | ACTUAL |
| 2024 | 60.9 | 29.7 | 29,600 | ACTUAL |
| 2025 | 130 | 72.8 | 36,000 | ACTUAL |
| **2026** | **215** | **120** | **42,000** | **ACTUAL** |

**Momentum (ACTUAL, şirket açıklamaları üzerinden):**
- **Şubat 2026:** Q4 FY2026 gelir **$68.1B**; envanter $50.3B → $95.2B; Q1 FY27 rehberi **$78B**.
- **Ağustos 2026:** Q2 FY2027 geliri **$96.2B** — bir önceki yılın aynı çeyreğine ($46.7B)
  göre **+%106**. Yıllaklaştırılmış run-rate **~$380B**.
- **Doğrudan yatırım:** Nvidia → OpenAI **$100 milyar** MOU (22 Ekim 2025), **en az 10 GW**
  sistem gücü planı; Nvidia → Nebius (AI cloud) **$2 milyar** (2026).

#### 1.1.1 ÇEYREK SERİSİ — BİRİNCİL KAYNAK DOĞRULAMASI (26 Eylül 2026)

Yukarıdaki yıllık ve momentum rakamları **Nvidia newsroom'un kendi basın bültenlerinden birebir doğrulandı**. Bu, Wikipedia özetinden değil, **şirketin açıkladığı orijinal metinlerden** alınmıştır.

| Çeyrek | Bülten tarihi | Gelir ($B) | Data Center ($B) | Y/Y | Kaynak URL'si |
|---|---|---|---|---|---|
| Q1 FY2026 | 28 Mayıs 2025 | 44.062 | 39.1 | +69% | .../first-quarter-fiscal-2026 |
| Q2 FY2026 | 27 Ağustos 2025 | 46.743 | 41.1 | +56% | .../second-quarter-fiscal-2026 |
| Q3 FY2026 | 19 Kasım 2025 | 57.006 | 51.2 | +62% | .../third-quarter-fiscal-2026 |
| **Q4 FY2026** | **25 Şubat 2026** | **68.1** | **62.3** | **+75%** | .../fourth-quarter-and-fiscal-2026 |
| **FY2026 tam yıl** | **25 Şubat 2026** | **215.9** | — | **+65%** | aynı bülten |
| **Q1 FY2027** | **20 Mayıs 2026** | **81.615** | **75.2** | **+85%** | .../first-quarter-fiscal-2027 |
| **Q2 FY2027** | **26 Ağustos 2026** | **96.221** | **89.0** | **+106%** | .../second-quarter-fiscal-2027 |

**Doğrulamadan çıkan yeni bulgular:**
- Dosyadaki **"FY2026 = 215"** yıllık rakamı **birebir doğrulandı**: şirket $215.9B açıklamış (25 Şubat 2026).
- **Q2 FY2027'nin Data Center breakdown'u ilk kez**: $89.0B, **+117% Y/Y** — gelirin %92.5'i Data Center. Bu, AI-compute harcamasının NICEL BÜYÜKLÜĞÜNÜN birincil kanıtıdır: tek bir çeyrekte $89B'lik AI altyapı geliri.
- **H20 Çin ihracat kontrolü olayı** (Q1 FY2026): $4.5B stok zararı + $2.5B sevk edilemedi — Nvidia'nın "AI altyapısı jeopolitik tedarik kısıtı altında" olduğunu kanıtlar; KÖK'ün izin gerektirmeyen (permissionless) konumlandırması için doğrudan ilgilidir: merkezi tedarikçinin kısıtlandığı yerde, ağ tabanlı compute piyasası bir alternatiftir.
- **Huang'ın Q2 FY2027 sözleri (birebir):** "AI has reached its inflection point. It's doing useful work. Its tokens are productive and profitable. Now, **compute is revenue**." — KÖK'ün teziyle (useful compute = fee-generating work) aynı çerçeveyi kullanıyor.

Bu bölüm önceki sürümdeki rakamların güncel olduğunu ama ikincil kaynaktan (Wikipedia özeti) geldiğini gösterir; şimdi her rakam orijinal şirket bültenine tarihiyle bağlı. Üç noktalı birincil kanıt zinciri: bülten tarihi + URL + çeyrek/Y/Y tablosu.

### 1.2 KÖK v2 için analiz ve SINIRLAMASI (açıkça belirtilmelidir)

- Bu rakamlar AI-compute pazarının **büyüklüğünü ve hızını** kanıtlar: GPU tedarikçisinin
  geliri 3 yılda **8 katına** çıktı (26.9 → 215) ve hâlâ **%100+/yıl** büyüyor.
- **Üç sınırlama (TAMGA):** (1) Nvidia geliri = "bütün AI harcaması" **değildir**; tümleşik
  sistemler, enerji, tesis, personel bu sayının **dışındadır** (yani TAM çok daha büyüktür);
  (2) "permissionless bir zincirde ücretli görev olarak fiyatlanan **alt-küme**" hâlâ
  **BİLİNMEZ** — bu KÖK'ün testnet'i (F3) ile ölçülecektir; (3) araştırma firmalarının resmi
  TAM rakamları bu oturumda **BULUNAMADI** (403/timeout).
- **Sonuç:** KÖK v2 paper'ı bu rakamları "$215B gerçekleşen 2026 geliri + %106 Q2 artışı +
  $100B/10GW OpenAI yatırımı" ile somut bir pazar büyüklüğü argümanı olarak kullanabilir;
  kalan bilinmez (permissionless alt-küme) **açıkça "bilinmiyor"** olarak yazılmalıdır.

---

## 2. GÖREV 2B — Dağıtık Compute Pazarları (Render/Akash/io.net/Golem/Pearl)

### 2.1 Token fiyatları (ACTUAL — 24 Eylül 2026)

Kaynak: CoinGecko public API
(`https://api.coingecko.com/api/v3/simple/price?ids=render-token,akash-network,io.net,golem&vs_currencies=usd`),
**erişim 24 Eylül 2026, HTTP 200** (ilk başarılı çağrı). Sonraki çağrılar **HTTP 429
rate-limit'e** düştüğü için market-cap / 24h-change / io.net fiyatı alınamadı.

| Token | CoinGecko ID | Fiyat (USD) | Durum |
|---|---|---|---|
| Render | `render-token` | **$1.86** | ACTUAL, 24.09.2026 |
| Akash | `akash-network` | **$0.677272** | ACTUAL, 24.09.2026 |
| Golem | `golem` | **$0.125794** | ACTUAL, 24.09.2026 |
| io.net (IO) | `io-net` | **BULUNAMADI** | CoinGecko 429 (ilk çağrıda yanlış ID, sonra rate-limit) |
| Pearl (PRL) | — | **$1.27** (26.09.2026) — **ATH $1.67** (23.09.2026) | ACTUAL — CryptoRank, token açıklaması "L1 blockchain with Proof-of-Useful-Work based on AI matrix multiplications" ile **doğru proje teyit edildi**; Basu v2'nin ölçüm anı **$0.76** (canonical abs ile teyit; **v1 $0.21'di, revize edildi** — aşağıdaki sürüm tuzağına bak) |
### 2.2 Ağ kullanım metrikleri — KISMEN DOLDURULDU (26 Eylül 2026)

**v1'de tamamen BULUNAMADI idi; bu oturumda Akash için BİRİNCİL kaynak bulundu.**
Render, io.net, Golem için hala BULUNAMADI (aşağıda).

#### Akash — Q1 2026 raporu (BİRİNCİL, akash.network/blog, 1 Nisan 2026)

> Kaynak: https://akash.network/blog/akash-network-q1-2026-report/ — "Akash Network: Q1 2026
> Report", Michelle Javed, 1 Nisan 2026. **HTTP 200, 26 Eylül 2026'da alındı.**

- **2026'nın ilk 90 gününde tüm zamanların en yükseği olan $5 milyon compute spend aşıldı.**
- **BME (Burn Mint Equilibrium) mainnet'e 23 Mart 2026'da geldi** (Proposal 318). Mekanizma
  BİREBİR ŞU ŞEKİLDE: kullanıcı compute aldığında, ödemesi açık piyasadaki **AKT'yi otomatik
  satın alır, burn ederek ACT (transfer-edilemez stablecoin) üretir**, ve ACT ile işlemi
  settle eder. Sağlayıcı ACT alır ve cari fiyattan AKT'ye geri mintler.
- **Homenode Beta**: Tüketici GPU sahipleri (RTX 4090, RTX 5090, Quadro RTX 6000 Ada) ağa
  doğrudan compute katkısı yapar — AI inference için tasarlandı. Raporun dayanıklılık
  argümanı (birebir): "If a data center in the Middle East takes a strike, nodes in Seoul
  and Frankfurt keep running."
- **AkashML**: OpenRouter üzerinde **günde 1.7 milyar token** inference trafiği.
- **AEP-23 öncül modelin açık itirafı (birebir):** "tenants pay in USDC, demand for AKT
  weakens. **Usage grew while AKT's role as the network's core economic unit eroded.**"
  — KÖK'ün tezi için ÇOK ÖNEMLİ: bir DePIN ağı fiili kullanım büyürken token'ini
  ekonominin dışına iten bir ödeme modelini denedi ve **bilinçli olarak terk etti**.
  KÖK'ün her görevin yalnızca yerel token ile ödenmesi yaklaşımı, bu deneyimden
  çıkarılmış bir piyasa dersidir.

#### ÖLÇÜM ETİKETİ UYARISI — "compute spend" ≠ "lease revenue"

İki rakam çeşitli kaynaklarda dolanır ve **farklı şeyler ölçer**:

| Rakam | Kaynak | Ne ölçer | Güvenilirlik |
|---|---|---|---|
| **$5,000,000** "compute spend" | Akash'in kendi Q1 2026 raporu (birincil) | tümleşik fiilen ödenen compute (tüm lease tipleri; kapsamı net değil) | birincil |
| **$253,000** "GPU lease revenue" | Messari (ikincil, hoge.gg üzerinden) | yalnızca GPU lease'lerinin on-chain geliri | ikincil, dar ama doğrulanabilir |
| **43,540** leases, ~34% GPU utilization | Messari (ikincil) | Q1 2026 GPU lease sayısı + kullanım oranı | ikincil |

**Yaklaşık 20 katlık fark ($5M vs $253K) muhtemelen kapsamdan gelir, sağlıksız veriden değil.**
Ama bu, KÖK paper'ındaki en önemli disiplin hatlarından biridir: **pazar büyüklüğü iddia
ederken hangi etiketi kullandığınızı yazmalısınız.** KÖK'ün kendi ledger'ında bu sınıf
daha önce bulundu: "500 per-mille vs 500 basis-points" hatası (bug sınıfı 4). Aynı
yanılgı şimdi pazar verilerinde karşımıza çıkıyor. **Paper bu iki rakamı yan yana
koyup neden farklı olduklarını açıklamalıdır** — yoksa okuyucu $5M'i "GPU pazarı"
zannedip $253K ile çelişir.

#### Diğer ağlar — hala BULUNAMADI

- **Render, io.net, Golem**: GPU-saat, gerçekleşen iş geliri, aktif node metrikleri
  **BULUNAMADI**. Denenenler: `api.akash.network/v1/metrics/global` (DNS çözülemedi),
  `stats.akash.network/api/metrics` (404, SPA HTML), `stats.io.net/api/metrics` (DNS
  çözülemedi), CoinGecko fiyat API (429 rate-limit).
- **Yapısal neden (düzeltme):** v1 bu boşluğu "JS yükleyen siteler" diye açıklamıştı.
  Asıl neden daha basit: bu ağların metrik API'leri **statik fetch ile erişilebilir
  public endpoint olarak yayınlanmıyor** (DNS hatası veya 404). Tarayıcı gerektirir.
  **Akash için çeyreklik resmi rapor kullanılabilecek tek birincil kanıt oldu — bu,
  diğer ağlar için de doğru yaklaşımdır: "dashboard API'si" aramak yerine "çeyreklik
  resmi rapor" aramak.**

### 2.3 Pearl ağı (ACTUAL — ampirik ölçüm)

> **Basu, arXiv 2606.04819 (3 Haziran 2026), özetten verbatim:** "Pearl's 24 EH/s network --
> representing approximately **320,000 GPU-equivalents** consuming an estimated **112 MW** --
> produces **zero useful AI computation**. Budget GPU rental prices rose **38%** and utilization
> surged from **57% to 94%** following the mining software's public release, displacing
> legitimate research workloads."
> — *Kaynak:* https://arxiv.org/abs/2606.04819 (**BİRİNCİL — arXiv API'sinden 24 Eylül 2026'da
> alındı; tam başlık: "The Usefulness Gap in Proof-of-Useful-Work: An Empirical Study of
> Pearl's cuPOW Protocol", yazar: Abhinaba Basu.*)

**Tutarlılık notu:** `PEARL_DOCS_ANALIZ.md` ve `KOK_V2_REFERENCES.md`'deki 24 EH/s / ~320,000
GPU / ~112 MW rakamları bu bağımsız akademik ölçüm ile **uyumludur** — KÖK paper'ındaki Pearl
iddiaları doğrulanmıştır.

---

## 3. GÖREV 2C — Bitcoin Madencilik 2026 (CANLI VERİ, ACTUAL)

Kaynak: blockchain.info açık API (`https://blockchain.info/q/*`). Erişim: 24 Eylül 2026 (1.+2. okuma) ve **26 Eylül 2026 (3. okuma)** — her oklama HTTP 200.

| Metrik | Değer | API | Durum |
|---|---|---|---|
| Hashrate | **857,920,689,134 TH/s ≈ 857.9 EH/s** (1. okuma 24.09.2026) — **957,920,689,134 TH/s ≈ 957.9 EH/s** (2. okuma, ~10 dk sonra) — **851,321,299,217 TH/s ≈ 851.3 EH/s** (3. okuma 26.09.2026); v1'de 956.9 EH/s (21.09.2026) | `/q/hashrate` | ACTUAL (3 oklama, yüksek varyans — aşağıdaki not) |
| Fiyat | **$84,461.74** (24.09.2026) — **$84,038.62** (26.09.2026) — v1'de $81,162.26 (21.09.2026) | `/q/24hrprice` | ACTUAL |
| Difficulty | **1.3276 × 10¹⁴** | `/q/getdifficulty` | ACTUAL |
| Blok yüksekliği | **968,473** (24.09.2026) — **968,620** (26.09.2026; +147 blok ≈ 1 gün, 10 dk/blok ile tutarlı) | `/q/getblockcount` | ACTUAL |
| Blok ödülü | **3.125 BTC subsidy** — blok 968,473 coinbase çıkışı **3.13072657 BTC** (subsidy + ~0.006 fee) olarak **canlı bloktan doğrulandı** | `/rawblock/968473` | ACTUAL (doğrulandı) |
| İşlem sayısı | **6,945 işlem** (blok 968,473) | `/rawblock/968473` | ACTUAL |

**Hashrate notu (dürüst, ARTIK 3 NOKTAYLA):** blockchain.info `/q/hashrate` uç noktası bir
**anlık/yuvarlanan tahmin** döndürür. Üç oklama — **857.9, 957.9, 851.3 EH/s** (24, 24, 26
Eylül 2026) — aralığı **~851–958 EH/s** yani **~%12 varyans** gösterir. Bu, uç noktanın
çıktısının yüksek varyanslı olduğunu tek noktaya kıyasla çok daha güçlü kanıtlar: "958 EH/s"
değeri bir **yaklaşıktır**, kesin bir ağ ölçüsü değildir. Resmi (difficulty'den hesaplanan)
ortalama hashrate için zorluktan hesap yapmak gerekir.

**Enerji tüketimi (Cambridge CBECI) — DOLDURULDU (26 Eylül 2026):** v1 ve önceki sürümde
BULUNAMADI idi. `ccaf.io/cbeci/` bizzat denendi (HTTP 200 döndü ama **sıkıştırılmış ikili
payload**, metin çıkarılamadı — PDF sorunuyla aynı). Bunun yerine rakam **üç bağımsız
ikincil kaynakta** bulundu:

| Kaynak | Rakam | Tarih | Güvenilirlik |
|---|---|---|---|
| solcard.cc/blog/how-much-energy-does-bitcoin-use | **138.2 TWh/yıl** (CBECI'den) | 29 Temmuz 2026 | ikincil, düşük-orta |
| coinlaw.io/bitcoin-energy-consumption-statistics | **138 TWh** (Cambridge survey tabanlı); Digiconomist **204.44 TWh** | 2026 | ikincil, düşük-orta |
| sqmagazine.co.uk | **138 TWh** (≈ global tüketimin %0.5'i); Digiconomist 204.44 TWh | 2026 | ikincil, düşük-orta |

- **Üç kaynakta da aynı 138 TWh rakamı** çıkıyor → rakam muhtemelen gerçek CBECI değerini
  yansıtıyor, ama **CCAF'ın kendi sitesinden alınmadı** — ikincil kaynak olarak işaretlenmelidir.
- **Metodoloji aralığı (KÖK tezi için kritik):** Cambridge **138.2 TWh** vs Digiconomist
  **204.4 TWh** — yaklaşık **%48 fark**, çünkü metodolojiler farklı (Cambridge survey-tabanlı,
  Digiconomist varsayımsal verim). Bu aralık, "Bitcoin ne kadar enerji harcıyor?" sorusunun
  **kendisinin bir tahminler-aralığı** olduğunu gösterir; KÖK paper'ı herhangi bir enerji
  rakamı kullanırken kaynağını ve metodolojisini açıklamalıdır.
- **KÖK ile ilgili:** 138–204 TWh/yıl, ~17–23 GW sürekli yük'e karşılık gelir — bu
  **kayıp/çöp iş** (secure-by-waste). KÖK'ün tezi bu enerjiyi useful work'a yönlendirmektir;
  yukarıdaki aralık PoUW'ın adreslediği sorunun **ölçülebilir büyüklüğüdür**.


**Paper ile tutarlılık (v1'den gelen, hâlâ geçerli):** KÖK v2 paper'ı BTC için spesifik bir
hashrate/fiyat iddiasında bulunmaz; paper'daki "24 EH/s" Pearl'e aittir (Basu'dan kaynaklı)
ve yukarıdaki ölçümle **aynıdır**. **Sonuç: paper ile pazar verileri arasında ÇELİŞKİ YOK.**

---

## 4. GÖREV 2D — PoUW "Useful Work" Eleştirileri (2020–2026, VERBATIM)

Tüm özetler **arXiv/ePrint API'sinden 24 Eylül 2026'da birebir alınmıştır**. Bunlar, KÖK v2'nin
G/U iki-katmanlı mimarisini zorlayan **negatif sonuçların** kaynağıdır.

### 4.1 En güçlü eleştiri: "usefulness gap" ÜRETİMDE ÖLÇÜLDÜ (2026)

> **Başlık:** "The Usefulness Gap in Proof-of-Useful-Work: An Empirical Study of Pearl's
> cuPOW Protocol" · **Yazar:** Abhinaba Basu · **arXiv 2606.04819**, yayım **3 Haziran 2026**
> · *Kaynak:* https://arxiv.org/abs/2606.04819

> **VERBATIM (özetteki beş bulgu):**
> 1. "(1) network composition analysis of **8,012 workers** shows all have inference-capable
>    hardware, **yet the dominant mining software contains no inference code**;"
> 2. "(2) the verification protocol **accepts random matrices by design**, confirmed by 44
>    pool-accepted shares from our open-source miner across NVIDIA, AMD, CPU, and Apple
>    Silicon hardware;"
> 3. "(3) statistical distribution checks are **trivially defeated by adversarial Gaussian
>    sampling**;"
> 4. "(4) mining economics are marginal at current PRL prices ($0.76), with **ROI ranging from
>    -1% to +67%** depending on GPU tier -- near breakeven for most hardware;"
> 5. "(5) the mining computation is **commodity integer arithmetic portable to any hardware
>    platform, offering no vendor lock-in**."
>
> **Ekonomik zarar (verbatim):** "Budget GPU rental prices rose 38% and utilization surged
> from 57% to 94% following the mining software's public release, **displacing legitimate
> research workloads**."
> **Teorik çapa (verbatim):** "These findings **quantify the verifiability-usefulness tension**
> identified theoretically by Leinweber et al., providing concrete measurements of its
> magnitude and economic consequences in a deployed system."

> **★ ÖNEMLİ SÜRÜM TUZAĞI (26 Eylül 2026) — bu kağıdın İKİ FARKLI HALİ VAR, ve
> yanlış olanı çekmek çok kolaydır:**
> arXiv 2606.04819'un **iki rendering'i birbiriyle ÇELİŞİYOR**:
>
> | Kaynak | Fiyat | ROI | Kime atıf | Sürüm |
> |---|---|---|---|---|
> | `arxiv.org/abs/2606.04819` (canonical abstract) | **$0.76** | **−1% .. +67%**, "marginal, near breakeven" | **Leinweber et al.** | **v2 (5 Haz 2026) — GÜNCEL** |
> | `ar5iv.labs.arxiv.org/html/2606.04819` | $0.76 | −1% .. +67%, aynı | **Hoffmann** | **v2** (ama kime-atıf adı farklı!) |
> | `arxiv.org/html/2606.04819v1` | **$0.21** | **−54% .. −72%**, "unprofitable" | Hoffmann | **v1 (3 Haz 2026) — REVİZE EDİLDİ** |
>
> **Submission history (abs sayfasından):** "[v1] Wed, 3 Jun 2026 (37 KB)",
> "[v2] Fri, 5 Jun 2026 (39 KB) — **last revised (this version, v2)**".
> **Yazar 3 Haziran'da gönderdi, 5 Haziran'da REVİZE ETTİ, ve revizyon ekonomik
> bulguyu bütünüyle değiştirdi: $0.21 → $0.76, −54..−72% → −1..+67%,
> "unprofitable" → "marginal, near breakeven".**
>
> **★ BU DOSYANIN ALINTISI DOĞRUDUR (v2, güncel sürüm):** "mining economics are
> marginal at current PRL prices ($0.76), with ROI ranging from −1% to +67%
> depending on GPU tier -- near breakeven for most hardware". Bu, canonical
> abs sayfasıyla birebir aynıdır. **Bu not, önceki hatalı bir "düzeltme"
> girişiminin yerini alır** — 26 Eylül'de `arxiv.org/html/2606.04819v1`
> çekilip v1'in ekonomik figürleri "gerçek" zannedilmiş ve alıntı yanlış
> olarak v1'e çevrilmiştir; **sonra canonical abs sayfası v2'yi gösterdiği
> için geri çevrildi.** Hata, sürüm numarası URL'de açıkça yazmasına rağmen
> `v1` son ekinin FARK EDİLMEMESİYDİ.
>
> **★ DERS (en önemlisi):** arXiv HTML endpoint'i `.../html/XXXX.XXXXX`
> **güncel sürümü**, `.../html/XXXX.XXXXXv1` **belirli bir sürümü** verir —
> ve bu kağıtta **ardışık iki sürümün ekonomik sonucu tamamen farklıdır**.
> **Bir alıntıyı doğrularken her zaman `abs` sayfasını (canonical abstract +
> submission history) çekin** — o, "last revised (this version, v2)" satırını
> verir ve hangi sürümün güncel olduğunu söyler. **Sadece `/html/` çekmek,
> ister v1 ister v2 olsun, sürümün GÜNCEL olup olmadığını söylemez.**
>
> **★ KALAN ÇELİŞKİ (dürüst açık item):** v2'nin **kendi içinde** iki rendering'i
> farklıdır — canonical abstract **"Leinweber et al."** derken, ar5iv'in v2'si
> **"Hoffmann"** der (fiyat ve ROI aynı, yalnızca atıf adı farklı). **Bu,
> ar5iv'in bağımsız bir rendering'i olmasından veya yazarın v2'de atıf adını
> değiştirip abstract'u güncellememesinden kaynaklanıyor olabilir** — hangisi
> olduğu bu oturumda ÇÖZÜLEMEDİ, çünkü iki rendering da tam referans listesini
> (sırasıyla) yükleyemedi. **Açık item olarak kalır:** "Leinweber et al."
> kimdir, henüz **belirlenemedi**. Bu projenin tezi için kritik değildir
> (KÖK'ün φ=0 bulgusu fiyat/atıf bağımsızdır), ama **alıntı bütünlüğü için
> doğrulanmamış bir ad olarak kaydedilir.**
>
> **★ FİYAT HAREKETİ (gerçek taban = $0.76, güncel):** Basu **$0.76'da** ölçtü
> (Haziran 2026, v2'ye göre). PRL o tarihten beri **$1.27'ye yükseldi**
> (26.09.2026, CryptoRank HTTP 200): ATH **$1.67** (23 Eyl 2026), ATL $0.194
> (23 Tem 2026), FDV $253.51M. **$0.76 → $1.27, ~1.7×'lik bir artıştır** —
> yani Basu'nun −1..+67% ROI'si **ölçüm anında doğruydu ama güncel ekonomik
> durum olarak alıntılanmamalıdır**: fiyat ~1.7× artınca aynı donanımın
> gelirle ROI'si daha da yukarı kayar. **Tarih olarak alıntıla, güncel olarak
> değil.**
>
> **★ YİNE DE FİYAT-BAĞIMSIZ OLAN BULGU AYNIDIR:** Basu'nun asıl bulgusu
> **φ=0'dır** (sıfır faydalı hesaplama): 8.012 worker'ın hiçbirinde inference
> kodu yoktu, random matrix'ler kabul edildi, istatistiksel kontroller
> adversarial Gaussian sampling'le kolayca alt edildi. **Fiyat onu
> değiştirmez.** Yalnızca ekonomik analiz fiyat-bağımlıdır; **faydalılık
> bulgusu değildir. İkisini karıştırmak alıntıyı çarpıtır.**
>
> **★ TOKEN KİMLİĞİ TUZAĞI (neden üç farklı fiyat göründü):** "Pearl" araması en az
> **üç farklı projeyi** döndürür — Pearl Network (PoUW L1, doğru olan), "Perle" (tamamen
> farklı bir token, $0.12–$0.38 aralığında) ve "pearlresearch.ai" (başka bir proje).
> İlk aramada görünen $0.0412 ve $0.3801 **yanlış projelerdir**. CryptoRank'ın token
> açıklaması ("L1 blockchain with Proof-of-Useful-Work based on AI matrix multiplications")
> **doğru projeyi teyit eden tek kesin sinyaldir** — sembol (PRL) üçünde de aynıdır ve
> yalnızca sembole güvenilirse yanlış fiyat alınır. **Ders: sembol, proje kimliği için
> yeterli bir tanımlayıcı değildir.**

**KÖK v2 için anlamı (TAMGA):** Bu, projenin "Pearl φ=0" bulgusunun **bağımsız akademik
doğrulamasıdır**. Eleştirinin özü şudur: **doğrulanabilirlik ile faydalılık arasında bir
gerilim vardır** ve bu gerilim, "proof of useful work" iddiasının üretimde **sıfır** faydalı
iş üretmesine yol açabilir. KÖK'ün U-katmanı (fee-paid görev pazarı) bu gerilimi **ayrı bir
katmanda** çözmeyi hedefler: faydalı iş, madenciliğin yan ürünü değil, **ücret talep eden
ayrı bir işlem** olarak tasarlanmıştır.

### 4.2 Güvenlik eleştirisi: "wasteless mining" imkânsızlığı (2020)

> **Başlık:** "Proofs of Useless Work -- Positive and Negative Results for Wasteless Mining
> Systems" · **Yazarlar:** Maya Dotan, Saar Tochner · **arXiv 2007.01046**, yayım 2 Temmuz 2020
> · *Kaynak:* https://arxiv.org/abs/2007.01046
>
> **VERBATIM ana sonuç:** "In our main result, we conclude that under realistic assumptions,
> **the set of allowed problems must be preimage resistant functions in order to keep the
> system secure and efficient.**"
> **Gerekçe (verbatim):** "We formally define three properties that are necessary for
> wasteless PoW systems: (1) solve 'meaningful' problems (2) solve them efficiently and (3) be
> secure against double-spend attacks. ... The security of the system stems from the economical
> incentive created by the demand for solutions to these problems."

**KÖK v2 için anlamı:** KÖK'ün PoUW çekirdeği (KW MatMul construction'ı) bu kısıtın farkında
olmalıdır: **faydalı problemlerin "preimage resistant" yapıda olması gerekir**; aksi halde
sistem ya güvensiz ya da verimsiz hale gelir. KW'nin MatMul PoUW'unda bu, gürültü bloklarının
**rastgele ve öngörülemez** olmasıyla sağlanır (KOK_V2_REFERENCES #2).

### 4.3 SoK: "utility does not contribute to the security budget" (2025)

> **Başlık:** "Is Proof-of-Useful-Work Really Useful?" (SoK) · **Yazarlar:** Pratyush Dikshit,
> Emami, Sedlmeir, Fridgen · **ePrint 2025/1814**, 3 Ekim 2025 (onay 8 Ekim 2025) · *Kaynak:*
> https://eprint.iacr.org/2025/1814 ·
> **★ 26.09.2026 GÜNCELLEME — tam abstract artık DOĞRULANDI** (ePrint'in kendi sayfasından,
> HTTP 200): "We examine more than **50 PoUW constructions** where we find recurring
> shortcomings. We introduce a formal economic model of PoUW for miner incentives, **solution
> reusability**, and external market value to the security budget... Our findings show that
> **PoUW is actually not as useful as expected, since the economic and societal utility do not
> contribute to the security budget.**" Ayrıca yazarların **tümü, kurumları ve tarihleri**
> ilk kez bu çekimle teyit edildi (Luxembourg ×3, Münster ×1; CC0). **Tam PDF hâlâ
> alınamadı** (`.pdf` ikili döndü; arXiv mirror'u yok — yanlış ID denendi, alakasız bir
> biyoloji makalesi geldi), dolayısıyla taksonomi, formal ekonomi modeli ve Toulmin
> değerlendirmesi **doğrulanmamış olarak kalır** — yalnızca abstract'ın kendi cümleleri
> alıntılanır. `KOK_V2_REFERENCES.md`'deki giriş bu güncellemeyi yansıtır.

### 4.4 Dış ödül teşvik saldırısı: görev tek blokta toplanması (2025)

> **Başlık:** "Proof of Work With External Utilities" · **Yazarlar:** Yogev Bar-On, Ilan
> Komargodski, Omri Weinstein · **arXiv 2505.21685**, yayım 27 Mayıs 2025 · *Kaynak:*
> https://arxiv.org/abs/2505.21685
>
> **VERBATIM ana bulgu:** "Our findings suggest that in some cases, **miners with access to
> external incentives will optimize profitability by concentrating their useful tasks in a
> single block.** We also explore the implications of external rewards for decentralization,
> modeling it as the Shannon entropy of computational effort distribution among participants."

**KÖK v2 için anlamı:** Madenciler faydalı görevleri **tek bir blokta toplamaya** teşvik
edilir; bu da güvenlik-fayda dengesini bozabilir. KÖK'ün cevabı **C_FEE anti-aggregation
cap**'idir (KOK_V2_REFERENCES #10).

### 4.5 "Paid to attack" eleştirisi ve onun çürütülmesi (2026)

> **Başlık:** "The Economics of Proof-of-Useful-Work" · **Yazar:** Rafael Pass · **arXiv
> 2606.06700**, yayım **4 Haziran 2026** · *Kaynak:* https://arxiv.org/abs/2606.06700
>
> **VERBATIM eleştirinin ifadesi:** "However, PoUW is often criticized on economic grounds:
> **if the work is useful, attackers might be 'paid to attack,' potentially weakening
> security.**"
> **VERBATIM çürütme:** "We develop a competitive-equilibrium model of a PoUW blockchain in
> which compute can be allocated across pure mining, pure useful work -- instantiated as
> machine-learning inference -- or 'duplex' work that produces both with computational
> overheads. ... This characterization reveals three regimes: '**Bitconia**,' in which the
> economy reduces to classical PoW; '**Fortessia**,' in which duplex replaces mining,
> increasing security while useful output remains unchanged; and '**Duplexia**,' in which token
> rewards subsidize inference, lowering prices and expanding inference supply. **Contrary to
> the common strawman argument, PoUW does not make attacks economically cheap: once equilibrium
> prices are taken into account, the economic cost of a majority attack remains tied** [to the
> block reward]."

**KÖK v2 için anlamı:** Pass'ın modeli, "faydalı iş saldırganı ödüllendirir" endişesinin
**teoric olarak haksız** olduğunu gösterir — saldırı maliyeti her rejimde blok ödülüne
bağlı kalır. Bu, KÖK'ün PoUW ekonomik argümanının **resmi** temelidir ve Pearl'in kendi
araştırma sayfasında "The Economics of Proof-of-Useful-Work" olarak listelenmiştir (bkz. §5).

### 4.6 Erken dönem katalog eleştirisi (2022)

> **Başlık:** "Challenges of Proof-of-Useful-Work (PoUW)" · **Yazar:** Felix Hoffmann ·
> **arXiv 2209.03865**, yayım 8 Eylül 2022 · *Kaynak:* https://arxiv.org/abs/2209.03865
> **VERBATIM:** "In the second part, theoretical PoUW concepts such as Coinami, CoinAI and the
> first successful PoUW cryptocurrency Primecoin are analyzed with respects to **how PoW
> properties can be retained while doing useful work**."
> **Citation-integrity uyarısı:** Bu makale **tek yazarlıdır (Felix Hoffmann)**.
> `KOK_V2_REFERENCES.md` satır 147'de "Leinweber et al." atfı için **arXiv 2209.03865**
> gösterilmiştir — **bu eşleşme yanlıştır** (Basu'nun özetinde geçen "Leinweber et al."
> ayrı bir makaledir, bu oturumda bağımsız olarak doğrulanamamıştır). **Denetimde
> düzeltilmelidir.**

### 4.7 ZK ile AI eğitimi doğrulama (2026 — "tomorrow" rotası)

> **Başlık:** "Zero knowledge verification for frontier AI training is possible" ·
> **Yazarlar:** Pierre Peigné, Ky Nguyen, Paul Wang · **arXiv 2606.05433**, yayım 3 Haziran
> 2026 (v2 22 Ağustos 2026, 44 sayfa) · *Kaynak:* https://arxiv.org/abs/2606.05433
> **VERBATIM:** "the impracticality is paradigm-bound rather than fundamental ... verified
> through a zero-knowledge Virtual Machine (zkVM) with **native BF16/FP32 precompiles**. The
> proof checks the **actual floating-point computation** the GPU performed rather than a
> fixed-point approximation ... We estimate a deployable proof of concept within approximately
> **36 months** at **single-digit-percent training-side overhead**."

**KÖK v2 için anlamı:** Bu, KÖK'ün 𝔽_q sabit-noktalı (fixed-point) yaklaşımından **yerel
kayan-noktalı (native FP) ZK'ya geçişinin** "tomorrow" rotasıdır (~36 ay).

---

## 5. GÖREV 2E — Pearl Research Labs: Güncel Durum (24 Eylül 2026, CANLI)

### 5.1 Kurumsal kimlik — iki katmanlı yapı (BİRİNCİL)

Kaynak: `https://pearlresearch.ai/network` ve `.../research`, **erişim 24 Eylül 2026,
HTTP 200** (tüm metin bu oturumda çekildi).

> **Ağ sayfasından verbatim:** "**Pearl's mathematical breakthrough enables every GPU cycle
> powering AI systems to simultaneously produce a native digital currency.**"
> **Together AI endpoint (verbatim):** "Gemma-4-31B-it-Pearl, an instruction-tuned checkpoint
> running on Pearl's Proof of Useful Work, is **live as a serverless endpoint on Together AI at
> 25%+ below the standard price, funded by the PRL mined on the same forward pass.**"
> **Kurumsal:** "NVIDIA Inception Program", "© 2026 Pearl Research Labs".
> **SSS bölümü (kendi eleştirilerine verdikleri yanıtlar):** FAQ başlıkları arasında "How does
> useful work produce intelligence and consensus from the same forward pass?", "How does the
> network stay secure?", "**Doesn't useful work make a 51% attack cheaper?**", "Is Pearl
> post-quantum?", "How is PRL issued?" yer alır.

**Domain notu (önceki oturumlardan):** `pearl.network` GoDaddy park sayfası, `pearl.foundation`
DNS ölü, `pearlnetwork.io` DNS ölü. **Canlı alan `pearlresearch.ai`'dir** (Pearl Research Labs).

### 5.2 Araştırma yayınları (24 Eylül 2026, canlı araştırma sayfasından VERBATIM)

| Yayın | Açıklama (Pearl'in kendi metni) | Bağlantı |
|---|---|---|
| **Hawkeye: Reproducing GPU-Level Non-Determinism** | "Reproduces the exact bit-level matrix multiplication an NVIDIA GPU ran by re-executing it on a CPU with no precision loss, so an auditor can check any training or inference run against a deterministic reference at essentially no overhead." | arXiv (Hawkeye, arXiv 2603.20421) |
| **Optimizing Grouped GEMM for MoE on Blackwell** | "How we squeezed up to **15% more performance** out of MoE's core kernel." | site |
| **A Fused Blockwise Hadamard Quantization Kernel in CuTe DSL** | "folds the blockwise Hadamard transform into INT quantization, benchmarked against vLLM and **running in production behind models like Gemma 4**. Much of it was written by our **in-house agentic kernel tool**." | X |
| **400x Faster Hashing on GPUs** | "Pearl mining has to hash large tensors that already live on the GPU ... a cryptographically secure **BLAKE3 kernel** that optimizes a single digest on-device with no host I/O" | X |
| **Proofs of Useful Work From Arbitrary Matrix Multiplication** | "gives a proof of useful work for matrix multiplication with **1 + o(1) overhead**, so GPUs can reuse their AI compute to secure a chain." | arXiv (KW, arXiv 2504.09971) |
| **The Economics of Proof-of-Useful-Work** | "closed-form prices across mining, inference, and 'duplex' work, plus **why a majority attack stays tied to the block reward once prices adjust**." | arXiv (Pass, arXiv 2606.06700) |
| **Pearl Polymath (open problems)** | "The open questions in mathematics, cryptography, and consensus that Pearl is still working to solve." | pearlpolymath.com |
| **Pearl INT Whitepaper** | "The original whitepaper: the Pearl protocol with an exact integer (INT) matrix-multiplication mining kernel." | site |

**FP8 whitepaper'ı (önceki oturumdan, Eylül 2026):** "Pearl Floating Point Scheme
Specification" — FP8 PoUW; **tickets hash the output tiles directly (no transcript needed)**;
**Assumption 1 (quantized-subspace hardness)**; §5 jackpot policy = 4 somut kontrol + §5.2'de
6 saldırı vektörü + §7'de 5 hızlandırma sınıfı; **doğrulama = Hawkeye ile bit-exact replay**.
Hawkeye yazarları: **Badash, Boneh, Komargodski, Srivastava** (Komargodski hem KW'nin hem
Hawkeye'nin yazarı).

### 5.3 Ağ yazılımı durumu (ACTUAL, GitHub API)

Kaynak: GitHub API `https://api.github.com/repos/pearl-research-labs/pearl`,
**erişim 24 Eylül 2026**:

| Metrik | Değer |
|---|---|
| Yıldız | **322** (v1'de 311 ★ — 21 Eylül 2026) |
| Fork | **77** |
| Açık issue | **92** |
| Son push | **2026-09-24T15:00:04Z** (bugün) |
| Dil/depolar | Go + Python + C kernelları (`zk-pow/`, `pearl-blake3/`, `plonky2/`, `xmss/`, `miner/`, `node/`, `wallet/`, `py-pearl-mining/`) |

**Sonuç:** Pearl **aktif olarak bakım yapılan, canlı bir projedir**; 3 günde 11 yeni yıldız,
bugün push yapılmış.

### 5.4 Finansman — BULUNAMADI

- Pearl Research Labs'ın **finansman durumu (seed/VC turu, değerleme, yatırımcılar) bu
  oturumda BULUNAMADI.** `pearlresearch.ai`'de finansman/press/basın bülteni sayfası yoktur;
  şirket yalnızca **"NVIDIA Inception Program"** üyeliğini belirtir (bu bir **accelerator
  üyeliğidir**, yatırım değildir).
- **Bilinen ama DOĞRULANMAMIŞ:** Pearl'ün "high-profile AI industry endorsements" ifadesi
  Basu'nun özetinde geçer ("Pearl, a Layer-1 blockchain with high-profile AI industry
  endorsements") — ancak **hangi endorsement'lar olduğu belirtilmemiştir**; spekülasyon
  yapılmamıştır.
- **Sonraki adım:** Crunchbase/PitchBook veya Pearl'in X (Twitter) duyuruları üzerinden
  finansman haberi aranmalıdır (bu oturumda sosyal medya kaynaklarına ulaşılamadı).

### 5.5 Pearl'in kendi ekonomik itirafı (Polymath açık problemi, VERBATIM)

> **Pearl Polymath Project'in 1. ekonomik açık problemi (Pearl'in kendi metni):** "the
> marginal cost of mining is ~0 and hence also the cost of attacking ... the key scarce
> resource in PoUW mining is the ability to collect useful data (matrices). **What should be
> the value/price of the Pearl coin at 0 mining overhead? Is it 0? infinity?**"
> — *Kaynak:* `pearlpolymath.com` (önceki oturumda okundu, KOK_V2_REFERENCES #Polymath ile
> uyumludur.)

**Bu, KÖK v2 için en çarpıcı öngörüdür:** Pearl'in kendisi, **madencilik marjinal maliyetinin
~0 olduğu** bir PoUW'da tokenin değeri sorusunu **açık** bırakmaktadır. KÖK'ün U-katmanı
(ücretli görev pazarı + geri alınamaz burn) tam olarak bu soruyu **yapısal** olarak yanıtlamayı
hedefler: tokenin değeri, madencilik maliyetinden değil, **gerçek ödenen görev talebinden**
gelir.

---

## 6. ★ TALEP-TARAFI ANALİZİ (Lead'in belirttiği öncelik: "talep, kriptografiden daha zayıf")

Lead'in notu: "*Pearl's φ=0 canlı tek örnek; pazar_ai_compute.md talep eğrisi / gerçek
ücretli-AI-işlem-hacmi verisi içermelidir.*" Bu bölüm bu isteğe doğrudan yanıt verir.

### 6.1 Gerçek ödenmiş inference fiyatları (ACTUAL — 24 Eylül 2026)

Kaynak: `https://pearlresearch.ai/pricing`, **erişim 24 Eylül 2026, HTTP 200**. Başlık:
"**Now at special launch pricing** — Serverless inference pricing for Pearl Inference Platform
models, now available at special launch discounts. **Pay only for the tokens you use.**"

| Model | Input $/1M | Cached $/1M | **Output $/1M** |
|---|---|---|---|
| Qwen/Qwen3.8-27B | $0.20 | $0.05 | **$2.00** |
| Qwen/Qwen3.8-Flash-Next | $0.14 | $0.015 | **$0.45** |
| Z.AI: GLM-5.3-Flash | $0.07 | $0.015 | **$0.24** |
| Z.AI: GLM-5.3 | $1.10 | $0.23 | **$3.50** |
| DeepSeek-V4-Pro-0813 | $1.10 | $0.043 | **$3.30** |
| DeepSeek-V4-Flash-0731 | $0.06 | $0.016 | **$0.17** |
| DeepSeek-V4.1-Flash | $0.14 | $0.004 | **$0.42** |
| **Google: Gemma 4 31B (gemma-4-31B-it)** | $0.09 | $0.05 | **$0.34** |

**Bu veri neden KÖK v2 için kritiktir?** Çünkü Pearl'in **gerçek gelir modelini** gösterir:
Pearl bir inference platformudur ve PRL madenciliği bu inference'u **sübvansiye eder**
("funded by the PRL mined on the same forward pass"). Yani **gerçek ücretli işlem hacmi
Pearl'in inference platformundadır; zincirin PoUW madenciliğinde DEĞİLDİR** — bu, Basu'nun
φ=0 ölçümünün **nedensel** açıklamasıdır.

### 6.2 Talep eğrisi problemi — KÖK v2'nin açık sorusu (TAMGA analizi)

Pearl'den çıkarılacak dersleri sıralayalım:

1. **Faydalı iş, "madenciliğin yan ürünü" olmuyor (ÜRETİM KANITI):** Pearl'in 24 EH/s'lik
   ağı, 8,012 inference-capable workera sahip olmasına rağmen **sıfır** faydalı AI hesaplama
   üretmektedir (Basu). "Dominant mining software contains no inference code" — yani
   madenciler **ekonomik olarak faydalı yolu seçmemektedir**. Pearl'in kendi benchmark'ı
   (Llama 3.3 70B, 4×H200, 806–981 TMADs/s) ise **Pearl'in kendi hosted inference
   altyapısında** çalışmaktadır, madencilerde değil.
2. **Talep, üretimden GELİYOR:** Pearl'in iş modeli, kullanıcıların **sunucudan inference
   satın alması**dır (yukarıdaki fiyat tablosu) ve bu gelirin bir kısmı madenciliği finanse
   eder. KÖK'ün U-katmanı bu modeli **protokol seviyesine** taşımayı hedefler: kullanıcı fee
   öder → escrow → görev gerçekleştirilir → bir kısım **BURN** edilir (geri alınamaz).
3. **Ancak hiçbir yerde "ücretli görev hacmi" verisi YOK (BILINMEYEN):** Ne Pearl'in sitesinde
   ne de bağımsız kaynaklarda, **permissionless bir zincirde kaç ücretli AI görevinin
   gerçekleştiği** ölçülmemiştir. Pearl, Together AI endpoint'ini **"live"** olarak duyurmuş
   olsa da **hacim/token sayısı/ücret açıklamamıştır**.
4. **KÖK v2 için FORECAST (tahmin, gerçek değil):** KÖK'ün U-katmanı için talep eğrisi
   **henüz bir hipotezdir**. Testnet (F3) bu eğriyi ölçecek ilk fırsattır. **Tahmin edilen
   mekanizma:** fiyat = (task supply × task completion rate) / (fee burn rate). **Ama bu bir
   FORECAST'tir, ACTUAL üretim verisi YOKTUR.**
5. **En zayıf halka (Lead ile aynı fikirde):** KÖK'ün kriptografik çekirdeği (KW MatMul PoUW)
   **akademik olarak sağlamdır**; projenin gerçek riski **"kim bu görevler için ücret
   ödeyecek?"** sorusudur. Pearl — sektörün en gelişmiş PoUW örneği — bu soruyu **ticari bir
   inference platformu** kurarak yanıtlamıştır; yani **gerçek talep, zincirin dışından**
   gelmektedir. KÖK'ün tercih ettiği yol (protokol-içi görev pazarı) **daha yenidir ve
   kanıtlanmamıştır**.

### 6.3 Talep-tarafı için bulunamayan veriler (BULUNAMADI)

- **Pearl Together AI endpoint'inin işlem hacmi** (token sayısı, ücret dolar) — BULUNAMADI
  (Pearl veya Together AI açıklamamış).
- **Akash/Render/io.net'in gerçekleşen GPU-saat / iş geliri metrikleri** — BULUNAMADI
  (API'ler bu oturumda çalışmadı; §2.2).
- **Araştırma firmalarının resmi AI-compute TAM forecast'ları (Gartner/IDC/Precedence/Mordor)**
  — BULUNAMADI (403/timeout).
- **Cambridge CBECI Bitcoin enerji tüketimi (TWh/yıl), güncel değer** —
  **BULUNDU (26 Eylül 2026), ÜÇ NOKTA İLE, ÇELİŞKİYİ AÇIKÇA TUTARAK.**
  ccaf.io'nun sayfası sıkıştırılmış binary döndürür (gzip+brotli SPA —
  önceki oturumun "API 404" notunun sebebi), bu yüzden sayı üç bağımsız
  ikincil kaynaktan gelmektedir:
  - **138.2 TWh** — "Cambridge CBECI ... a live estimate of 138.2 TWh as of
    July 29, 2026" (solcard.cc, CBECI'ye atıfla; Digiconomist'i 204.4 TWh
    verir)
  - **170–180 TWh** — "roughly 170–180 terawatt-hours of electricity a year
    in 2026 — about 0.7–0.8% of world electricity"
    (oneminers.com, 9 Temmuz 2026, HTTP 200 ile doğrulandı)
  - **138–205 TWh aralığı** — "three independent methodologies converge on
    Bitcoin's annualised electricity demand in a range of ≈138-205 TWh·y⁻¹,
    corresponding to a continuous network load of ≈17–23 GW. This is
    approximately 0.5–0.6% of global electricity"
    (observatory.cryptoguru.org, Mayıs 2026)

  **ÇELİŞKİ GERÇEK VE KASİTLI OLARAK KORUNUR.** Üç kaynak üç farklı sayı
  veriyor çünkü CBECI'nin kendi metodolojisi tek bir nokta değil bir
  **aralıktır** (alt/orta/üst bantlar) ve farklı özetleyiciler farklı bandı
  alırlar. 138.2 (CBECI alt-orta), 170-180 (orta), 204.4 (Digiconomist üst)
  aralığın üçtepe noktasıdır. **KÖK'ün enerji argümanı için kullanım:**
  makale, tek bir sayı vermek yerine bu aralığı vermelidir — tek bir nokta
  yanlış hissedilir ve "en az 3 nokta" kuralı zaten aralığı talep eder.
  **ÖNEMLİ DÜRÜSTLÜK NOTU:** bunların hiçbiri CBECI'nin kendi API'sinden
  değildir; hepsi CBECI'yi alıntılayan ikincil kaynaklardır. Birincil API
  hâlâ erişilemez durumdadır, bu yüzden sayıların kaynağı ikincil olarak
  işaretlenir ve düşük-orta güvenilirlik derecesiyle kaydedilir.

---

## 7. BULUNAMADI LİSTESİ (bir sonraki oturumda tamamlanacak)

| # | Eksik veri | Neden ulaşılamadı | Önerilen sonraki adım |
|---|---|---|---|
| 1 | ~~**io.net (IO) token fiyatı**~~ | **BULUNDU (26.09.2026)** — CryptoRank: **IO $0.17**, 24h $0.1593–$0.1731, açıklama "decentralized computing network... ML applications on Solana" ile doğru proje teyit edildi. CoinGecko `io-net` ID'si de çalışıyor; önceki 429 rate-limit geçti | ~~Rate-limit sonrası yeniden çağrı~~ → **YAPILDI** |
| 2 | **CoinGecko market-cap / 24h / YTD değişim** | 429 rate-limit | Ücretli API veya bir sonraki gün |
| 3 | **Akash/Render/io.net ağ kullanım metrikleri** (GPU-saat, gelir, node) | İstatistik siteleri JS ile veri yüklüyor; API uç noktaları 404/bağlantı hatası | JS kaynağından gerçek API uç noktasını çıkarmak |
| 4 | **Araştırma firması TAM forecast'ları** (Gartner/IDC/Precedence/Mordor) | 403/timeout | Farklı UA/proxy ile veya özet press release'ları |
| ~~5~~ | ~~**Cambridge CBECI güncel TWh/yıl**~~ | **BULUNDU (26.09.2026)** — ccaf.io sayfası sıkıştırılmış binary (SPA), bu yüzden üç ikincil kaynak alınd: 138.2 TWh (CBECI'ye atıf, 29 Tem 2026), 170-180 TWh (9 Tem 2026), 138-205 aralık (Mayıs 2026). **Aralık korunur, tek nokta verilmez; hepsi ikincil** | ~~ccaf.io API'sini bulmak~~ → **YAPILDI (ikincille)**; kalan: birincil API |
| 6 | **Pearl finansman durumu (seed/VC/değerleme)** | Sitede finansman sayfası yok; sosyal medyaya ulaşılamadı | Crunchbase/PitchBook veya X duyuruları |
| 7 | **Pearl Together AI endpoint işlem hacmi** | Açıklanmamış | Together AI dashboard / Pearl X |
| 8 | ~~**Dikshit SoK (ePrint 2025/1814) tam özet metni**~~ | **BULUNDU (26.09.2026)** — ePrint'in kendi sayfasından **tam abstract + metadata** çekildi (HTTP 200): "PoUW is actually not as useful as expected, since the **economic and societal utility do not contribute to the security budget**" — 50+ PoUW inşası incelendi. **Tam PDF alınamadı** (`.pdf` ikili döndü, arXiv mirror'u yok) ama abstract tam metni KÖK'ün iki-katmanlı tezinin **bağımsız teyididir**. `KOK_V2_REFERENCES.md`'de tam giriş | ~~ar5iv.org üzerinden tam metin~~ → **YAPILDI (abstract seviyesinde)** |
| 9 | **"Leinweber et al." makalesinin gerçek kimliği** | Basu özetinde geçiyor; bağımsız doğrulanamadı | Basu'nun referans listesinden çıkarmak |
| 10 | **Torres kararları hariç diğer tüm hukuk boşlukları** için bkz. `hukuk_howey_mica.md` §6 | Arama motorları kapalı | Aynı liste |

---

## 8. KAYNAK LİSTESİ

**Birincil kaynaklar (canlı API / resmi sayfalar — 24 Eylül 2026'da erişildi):**
1. **blockchain.info API** — `/q/hashrate`, `/q/24hrprice`, `/q/getdifficulty`,
   `/q/getblockcount`, `/rawblock/968473` — https://blockchain.info/q/hashrate
2. **CoinGecko API** (ilk başarılı çağrı) —
   `https://api.coingecko.com/api/v3/simple/price?ids=render-token,akash-network,io.net,golem&vs_currencies=usd`
3. **arXiv API** (24.09.2026, UA `KOK Research`) —
   `https://export.arxiv.org/api/query?id_list=...` ile: 2606.04819 (Basu), 2606.06700 (Pass),
   2505.21685 (Bar-On/Komargodski/Weinstein), 2606.05433 (Peigné/Nguyen/Wang), 2209.03865
   (Hoffmann), 2007.01046 (Dotan/Tochner)
4. **IACR ePrint 2026/1492** — https://eprint.iacr.org/2026/1492 (Demirel; başlık+yazar
   doğrulandı: **Ömer Demirel**, "Proof of Demand Is Not Proof of Work: On the Limits of
   Demand-Weighted Consensus under Free Pseudonyms", 21 Temmuz 2026)
5. **Pearl Research Labs canlı sitesi** — `https://pearlresearch.ai/research` (HTTP 200),
   `/network` (HTTP 200), `/pricing` (HTTP 200) — **24 Eylül 2026**
6. **GitHub API** — `https://api.github.com/repos/pearl-research-labs/pearl` — 24.09.2026
7. **Nvidia finansal sonuçları** (Wikipedia tablosu üzerinden özetlenmiş şirket verileri,
   v1'den) — FY2022–FY2026 gelir/net gelir/çalışan tablosu

**Projedeki önceden doğrulanmış kaynaklar (bu oturumda kullanıldığı yerde belirtilmiştir):**
8. `KOK_V2_REFERENCES.md` — 11/11 arXiv/ePrint ID'si 21 Eylül 2026'da canlı doğrulanmış
   bibliyografya
9. `PEARL_DOCS_ANALIZ.md` — Pearl INT whitepaper + FP8 whitepaper + Polymath analizleri
   (19–20 Eylül 2026)
10. `hukuk_howey_mica.md` v2 — aynı oturumda üretilen hukuk araştırması

**Doğrulanan yeni bulgular (önceki dosyalara ek):**
- **Basu arXiv 2606.04819 özeti TAMAMEN doğrulandı** (arXiv API, 24.09.2026): 24 EH/s,
  ~320,000 GPU, ~112 MW, zero useful AI computation, 8,012 workers, ROI −1%..+67%, PRL $0.76.
- **Pass arXiv 2606.06700 yayım tarihi: 4 Haziran 2026 (yalnızca v1 mevcut — v2 yok)**
  (arXiv API + `/abs/` sayfası, 24.09.2026) — `KOK_V2_REFERENCES.md` satır 133'teki
  "2026-08-10" tarihi **kesinlikle yanlıştır** (v2 mevcut olmadığı için bir versiyon tarihi de
  olamaz). **Denetimde düzeltilmelidir.**
- **arXiv 2209.03865 = Felix Hoffmann (tek yazar)** — `KOK_V2_REFERENCES.md` satır 147'deki
  "Leinweber et al." atfıyla **çelişmektedir**. **Denetimde düzeltilmelidir.**

---

**Belge sürümü:** **v2** (24 Eylül 2026, TAMGA) — v1'in 4/5 BULUNAMADI şıklarından 2D ve 2E
birincil kaynaklarla dolduruldu; talep-tarafı analizi (§6) Lead'in önceliğine göre eklendi.
Kalan 10 boşluk §7'de listelendi.
