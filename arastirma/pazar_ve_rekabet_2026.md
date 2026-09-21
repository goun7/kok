# KÖK Network v2 — Pazar Araştırması (Doğrulanmış Gerçekler)
Tarih: 2026-09-21 | Dil: İngilizce arandı, Türkçe rapor

KAYNAK NOTU: Tüm fiyatlar canlı fiyatlandırma sayfalarından fetch edilmiştir.
"BULUNAMADI" = canlı kaynaktan doğrulanamadı.

---

## 1. AI INFERENCE COMPUTE PRICING (2026)

### Lambda Labs — lambda.ai/pricing (CANLI FETCH EDİLDİ, 2026-09-21)
Güven: YÜKSEK (resmi fiyatlandırma sayfası, doğrudan fetch)

**Instances (on-demand, self-serve), per GPU/hr:**
| GPU | 8x plan | 4x plan | 2x plan | 1x plan |
|---|---|---|---|---|
| B200 SXM6 180GB | $6.69 | $6.79 | $6.89 | $6.99 |
| H100 SXM 80GB | $3.99 | $4.09 | $4.19 | $4.29 |
| H100 PCIe 80GB | — | — | — | $3.29 |
| GH200 96GB | — | — | — | $2.29 |
| A100 SXM 80GB | $2.79 | — | — | — |
| A100 40GB | $1.99 | $1.99 | $1.99 | $1.99 |
| A6000 48GB | — | $1.09 | $1.09 | $1.09 |
| A10 24GB | — | — | — | $1.29 |
| V100 16GB | $0.79 | — | — | — |
| RTX 6000 24GB | — | — | — | $0.69 |

**1-Click Clusters (reserved/committed, 2 hafta–1 yıl):**
- HGX B200: 16 GPU $9.86/GPU/hr | 64 GPU $9.36 | 256+ $8.87
- H100: 16 GPU $6.16/GPU/hr | 64 GPU $5.85 | 256 GPU $5.54

**Noteworthy anomaly:** Lambda'da reserved 1-Click Cluster fiyatları on-demand instance'lardan DAHA YÜKSEK (B200: $9.86 vs $6.69). Yani reserved = daha pahalı. Bu ağ/altyapı dahil olmasından kaynaklanıyor olabilir.
**H200:** Lambda instances sayfasında H200 listelenmemiştir (sayfa başlığı H200 dese de tablolarda yok; GH200 $2.29 var). Lambda H200 instance fiyatı: BULUNAMADI.

### RunPod — runpod.io/pricing (CANLI FETCH, sayfa "Updated September 13, 2026")
Güven: YÜKSEK (resmi sayfa, güncelleme tarihi yazıyor)

**Pods (Community Cloud, on-demand):**
- B300 288GB: $7.89/hr
- H200 141GB: $4.59/hr
- B200 180GB: $6.79/hr
- H100 NVL 94GB: $3.19/hr
- H100 SXM 80GB: $3.49/hr
- H100 PCIe 80GB: $2.89/hr
- RTX Pro 6000 96GB: $2.09/hr
- A100 80GB (PCIe/SXM): $1.59/hr
- L40S 48GB: $1.09/hr | L40 48GB: $0.82/hr | RTX 6000 Ada: $0.84/hr
- A40 48GB: $0.49/hr | A6000: $0.53/hr
- RTX 5090 32GB: $0.99/hr | RTX 4090: $0.74/hr | RTX 3090: $0.50/hr
- L4 24GB: $0.49/hr | A5000: $0.27/hr

**Serverless (API inference):**
- B300: $9.98/hr | B200: $8.64/hr | H200: $5.93/hr | H100: $4.79/hr | A100: $2.72/hr

**Clusters (on-demand):** H200 SXM $4.31/hr | A100 SXM $1.79/hr | L40S/H100/B200: contact sales

### Together AI — together.ai/pricing (CANLI FETCH EDİLDİ)
Güven: YÜKSEK (resmi sayfa)

**Serverless inference, $/1M tokens (input/output):**
- DeepSeek V4 Pro 0813: $1.32 / $3.96 (cached input $0.13)
- DeepSeek V4.1 Flash: $0.30 / $1.20 (cached $0.006)
- DeepSeek V4 Flash 0731: $0.14 / $0.28 (cached $0.03)
- GLM-5.3: $1.40 / $4.40 | GLM-5.3-Flash: $0.15 / $0.50
- Kimi K3: $3.00 / $15.00
- MiniMax M3: $0.30 / $1.20
- Qwen3.8-2.4T-A95B: $2.00 / $6.00 | Qwen3.5-397B-A17B: $0.60 / $3.60
- Qwen3.6-Plus: $0.50 / $3.00 | Qwen3.7-Plus: $0.32 / $1.28 | Qwen3.7-Max: $2.50 / $7.50
- Llama 3.3 70B: $1.04 / $1.04 | Llama 3 8B Lite: $0.14 / $0.14
- Gemma 4 31B: $0.39 / $0.97 | gpt-oss-120B: $0.15 / $0.60
- Cogito v2.1 671B: $1.25 / $1.25
- En düşük: Ternary Bonsai 27B $0.00 / $0.00

**GPUClusters per-hour fiyatı:** fetch edilen kısımda yok, "contact sales" yönünde. Together GPU $/hr: BULUNAMADI (bu sayfada).

### OpenAI — developers.openai.com/api/docs/pricing (CANLI FETCH, resmi docs .md)
Güven: YÜKSEK (resmi OpenAI API dokümantasyonu)
Not: 2026 itibarıyla modeller ilerledi — "GPT-5" hala listeli ama amiral gemisi **gpt-6-astra**. Opus 4.5 yok (Anthropic tarafında Opus 5 var).

**Standard $/1M tokens (kısa-context input/output):**
- gpt-6-astra: $10.00 / $50.00 (cached input $1.00, cache write $12.50; long-ctx $20/$75)
- gpt-5.6-sol: $4.00 / $20.00 (promosyon, 21 Kasım 2026'ya kadar)
- gpt-5.6-terra: $2.00 / $12.00 | gpt-5.6-luna: $0.20 / $1.20
- gpt-5.5: $5.00 / $30.00 | gpt-5.5-pro: $30.00 / $180.00
- gpt-5: $1.25 / $10.00 | gpt-5-mini: $0.25 / $2.00 | gpt-5-nano: $0.05 / $0.40 | gpt-5-pro: $15.00 / $120.00
- gpt-4o: $2.50 / $10.00 | o3: $2.00 / $8.00
- Batch pricing = Standard'ın yarısı. Fast mode = 2x (gpt-6-astra $20/$100).

### Anthropic — claude.com/pricing (CANLI FETCH)
Güven: YÜKSEK (resmi sayfa)
Not: "Claude Opus 4.5" artık yok; güncel modeller Opus 5, Sonnet 5, Haiku 4.5, Fable 5.1.

**API $/MTok (input/output):**
- Fable 5.1: $10 / $50 | cache read $0.25, write $12.50
- Opus 5: $5 / $25 | cache read $0.50, write $6.25
- Sonnet 5: $2 / $10 | cache read $0.20, write $2.50
- Haiku 4.5: $1 / $5 | cache read $0.10, write $1.25
- "Save 50% with batch processing."

### DeepSeek — api-docs.deepseek.com/quick_start/pricing (CANLI FETCH, resmi)
Güven: YÜKSEK
$/1M tokens (off-peak / peak):
- DeepSeek-V4.1-Flash: input cache-miss $0.15/$0.30; cache-hit $0.003/$0.006; output $0.60/$1.20
- DeepSeek-V4-Pro-0813: input cache-miss $0.66/$1.32; cache-hit $0.022/$0.044; output $1.98/$3.96
- Peak: 01:00-04:00 & 06:00-10:00 UTC, Pazartesi-Cuma. Off-peak = peak'in yarısı.
- **İlginç:** DeepSeek V4-Pro peak fiyatı ($1.32/$3.96) Together AI'daki fiyatla **birebir aynı**.

### Nebius — nebius.com/prices (CANLI FETCH)
Güven: YÜKSEK
$/GPU-hour (preemptible / on-demand):
- HGX B300: $4.30 / $7.85 | HGX B200: $3.95 / $7.15
- HGX H200: $2.45 / $4.50 | HGX H100: $2.15 / $3.85
- RTX PRO 6000: $0.95 / $1.80 | L40S: from $0.74 / $1.55
- GB300 NVL72 & GB200 NVL72: contact us
- Commitment discount: on-demand'in %35'ine kadar indirim

### CoreWeave — coreweave.com/pricing (CANLI FETCH)
Güven: YÜKSEK
Not: Fiyatlar **node başına** (8 GPU'lu HGX node vb.); tek-GPU inference fiyatı ayrıca verilmiş.
Kuzey Amerika, on-demand:
| Node | Node $/hr | Spot $/hr | Tek-GPU inference $/hr | $/GPU (on-dem) |
|---|---|---|---|---|
| HGX H100 (8 GPU) | $49.24 | $19.71 | $6.16 | ~$6.16 |
| HGX H200 (8 GPU) | $50.44 | $20.93 | $6.31 | ~$6.31 |
| HGX B200 (8 GPU) | $68.80 | $34.11 | $8.60 | $8.60 |
| HGX B300 (8 GPU) | contact sales | $35.84 | — | spot $4.48 |
| GB200 NVL72 | $42.00 | N/A | $10.50 | $10.50 |
| RTX PRO 6000 HM (8) | $20.00 | $11.09 | $2.50 | $2.50 |
| GH200 (1 GPU) | $6.50 | N/A | $6.50 | $6.50 |
| L40 (8 GPU) | $10.00 | $6.27 | $1.25 | $1.25 |
| L40S (8 GPU) | $18.00 | — | — | $2.25 |
- CoreWeave iddia: "Cut AI cloud TCO up to 47%" (Futurum Signal65 TCO analizine göre).

### Vast.ai — vast.ai/pricing (CANLI FETCH)
Güven: YÜKSEK sayfa için, ama **spesifik $/hr sayıları BULUNAMADI** — fiyatlar JavaScript ile dinamik yükleniyor, statik HTML'de değil. Vast.ai bir marketplace ("prices set by supply and demand across 40+ data centers").
Yapısal bilgiler (doğrulandı): Interruptible "50%+ cheaper", Reserved "up to 50% off", 68+ GPU tipi, per-second billing.

### Fly.io — BULUNAMADI (bu oturumda fetch denendi/denenecek; fly.io GPU fiyatları docs'ta, ayrı sayfa)

---

### BÖLÜM 1 ÖZET — KÖK tezi için kritik çıkarım
**H100 sınıfı GPU, on-demand $/hr (tek GPU):**
- RunPod $3.49 (SXM) / $2.89 (PCIe) | Nebius $3.85 | Lambda $3.99 (8x)–$4.29 (1x) | CoreWeave $6.16
**B200:** RunPod $6.79 | Lambda $6.69 | Nebius $7.15 | CoreWeave $8.60
**H200:** RunPod $4.59 | Nebius $4.50 | CoreWeave $6.31
**Spot/preemptible H100:** Nebius $2.15 | CoreWeave $2.46 — **on-demand'un ~%55'i.**

Yani: KOK'un "madenciler zaten donanımı çalıştırıyor, compute'u marjinal maliyete satabilir" tezi için piyasa **zaten spot fiyatlarında H100 ~$2.15-2.46/GPU-saat** aralığında. KOK'un faydalı işi bu fiyatların altına düşmeli ki rekabet etsin — bu, tezin test edilecek en zayıf noktası.

---

## 2. MERKEZİ OLMAYAN COMPUTE BLOCKCHAIN'LER — GERÇEK GELİR YAYINLIYORLAR MI?
Kriter: token market cap DEĞİL, compute satışından gerçek USD gelir.

### Akash Network (AKT)
Güven: ORTA-YÜKSEK (resmi site fetch edildi)

Resmi siteden doğrulananlar (akash.network ana sayfa, 2026-09-21):
- **Gelir yayınlamıyor.** Ana sayfada "59 Active Providers, 16k vCPUs, **463 GPUs**, 90 TB Memory, 788 TB Storage" — bu **kapasite**, gelir değil. USD compute-revenue rakamı YOK.
- Fiyat claim'i: "**H100s for $1.33/hr vs AWS at $3.93/hr**" (ana sayfa marketing).
- Fiyatlandırma sayfası (akash.network/pricing/gpus): fiyat tablosu **JS ile render**, statik HTML'de boş. Bireysel GPU $/hr: BULUNAMADI.
- Razer vaka çalışması: "$0.01 per generated image, 3.24s avg end-to-end response, 15x lower inference costs."

**Rakip değerlendirmesi (io.net blog 2026-09-01):**
- "Akash's current provider network (**~2,000–3,000 total GPUs**, predominantly **RTX 3090 from individual miners**)"
- "**It is not an ML training infrastructure platform.** No native NVLink support, NCCL-aware scheduling, or distributed checkpoint coordinator."
- NOT: Rakibin claim'i — önyargılı ama alıntılanabilir. 463 vs 2,000-3,000 GPU çelişkisi var (farklı sayma yöntemleri).

**Akash USD compute geliri: BULUNAMADI** (resmi sitede yok; Token Terminal/Messari JS-arkası/403).

### io.net (IO)
Güven: YÜKSEK (kendi blog makaleleri tam metin fetch edildi)

"Three years of building the future of AI compute" (2026-06-12):
- "**$8 million in enterprise deals closed in just Q1 of 2026 alone.** That means real revenue from real companies running real production workloads, with all of that actual compute demand verified on-chain."
  - ⚠️ NÜANS: "enterprise **deals closed**" = bookings/satış anlaşması, recognize edilmiş gelir değil. Self-reported.
- H100 fiyat claim'i: "a single **H100 for $2.20/hr** instead of eight of them at $35/hr"
- **Dürüst itiraflar:** "Emissions outpaced demand, and we knew it." / "there was still a gap between actual revenue and token emissions."
- IDE (Incentive Dynamic Engine): token burn'leri gerçek compute kullanımına bağlı; "public dashboard, tracking real-time on-chain data."

"GPU Orchestration vs. GPU Rental" (2026-09-01) — **KÖK tezi için kritik**:
- "Every DePIN network's GPU marketing leads with price per GPU-hour... cheaper access to hardware is equivalent to actually usable infrastructure. Well, it isn't that simple."
- "When you rent a GPU from a marketplace, you get a machine. When you need orchestration, you need a system. **most decentralized networks have never built a system**..."
- "**DePIN compute as a category has largely stopped at the marketplace layer.**"
- Marketplace'ler yalnızca şu işe yarıyor: "inference serving for a small model, a one-shot notebook experiment, or a batch transcription job that parallelizes trivially across independent machines."
- Çok-GPU eğitim gerekenler: NVLink 600–900 GB/s, InfiniBand HDR/NDR, dağıtık checkpoint. "Consumer networking, even 10GbE, turns a 4-node gradient sync into a training run that never converges."

### Render Network (RNDR)
Güven: ORTA (resmi site fetch; raporlar 403)
- rendernetwork.com ana sayfa: **gelir rakamı yok**. "© OTOY Inc." Slogan: "unlimited rendering power at a fraction of the cost"; "Simple, on-demand pricing" deniyor ama sayfada rakam yok.
- io.net değerlendirmesi: "Render Network has not made a credible move toward distributed ML training infrastructure."
- Render Network Foundation quarterly raporları (medium.com/render.network): **403 Forbidden**, erişilemedi.
- **Render USD gelir: BULUNAMADI** (bu oturumda canlı doğrulanamadı)

### Aethir (ATH) — GERÇEK GELİR YAYINLIYOR (öne çıkan)
Güven: YÜKSEK (kendi resmi blog makalesi tam metin fetch edildi)

"aethirs-2025-wrap-up-decentralized-gpu-cloud-milestones" (15 Ocak 2026), resmi blog:
- **Key Takeaways (kendi sözleri): "Record revenue: $127.8M+ (Jan-Dec 2025), $166M ARR by Q3, outpacing Filecoin (135x), Render (455x), Bittensor (14x Rev/MC)."**
- "Aethir's annual recurring revenue, first announced in April, was **$36M worth of actual compute purchases**. Throughout the year... reaching an annual recurring revenue of **$166M in Q3 2025**."
- **1.5B+ compute hours delivered**, 440K+ GPU containers, 94 countries, 200+ locations, 150+ partner/müşteri
- **Aethir'in kendi rakip değerlendirmesi (önemli):** "While other DePINs struggle with client acquisition and revenue... Aethir's Rev/MC ratio outpaced Filecoin by 135x, **Render by 455x**, and **Bittensor by more than 14x**, reflecting the most efficient revenue-to-valuation profile among major DePIN compute sector leaders."
  - ⚠️ Bu Aethir'in RAKİBİ olduğu için önyargılı. Ama yayımlanmış bir claim. Ayrıca makalenin kendi içinde tutarsızlık var: "Key Takeaways" kısmında "Filecoin (135%)" yazıyor, gövdede "135x". Bu tutarsızlık not edilmeli.
- ⚠️ NÜANS: Bu self-reported ARR. Aethir'in public dashboard'ı var (dashboard.aethir.com — "compute utilization, GPU capacity, stakeholder earnings"). Ana sayfada "Over **$400m worth of compute capacity**" — bu kapasite değeri, gelir değil.

**Sonuç:** Aethir, listelenen ağlar arasında **gerçek USD compute geliri yayınlayan tek net örnek**. $127.8M (2025) / $166M ARR (Q3 2025).

### Bittensor (TAO) — "Gelir" büyük ölçüde EMISSİON sübvansiyonu
Güven: YÜKSEK (üçüncü taraf canlı dashboard taorevenue.com fetch edildi, 2026-09-21)

taorevenue.com (Bittensor subnet revenue/emissions/profitability tracker) canlı verileri (30D):
- **Total Bittensor Inflow & Burn (30D): 35,467 τ = $9,854,144**
- **Total Bittensor Outflow (30D): −276,341 τ = −$76,778,476**
- ⚠️ **KRİTİK: Ağ 30 günde ~$76.8M ödemesine karşılık yalnızca ~$9.85M giriş alıyor. Sübvansiyon, gelirin ~7.8 katı.** Yıllıklaştırılmış: gelir ~$118M/yr vs ödeme ~$921M/yr → gelir ekonominin ~%12'si.
- **Birçok subnetin SIFIR geliri var** (Inflow "−"): SN3 Teutonic, SN5 Hone, SN6 Numinous, SN7 Allways, SN16 kenju, SN17 404-GEN, SN29 hoτfloaτ, SN38 ChronoLLM, SN40 Ralph, SN48 Quantum Compute, SN50 Synth, SN61 RedTeam, SN66 conjectures, SN74 Gittensor, SN77 Liquidity, SN79 MVTRX, SN82 Compelle, SN83 CliqueAI, SN88 Investing, SN91 cascade, SN97 Albedo, SN98 NeverPlayAlone, SN104 TAOstatus. Bunlar yalnızca emission alıyor, hiç gelir üretmiyor.
- En iyi subnetlerin bile "Surplus" negatif: SN51 lium.io inflow $1.07M / outflow −$5.18M (coverage %24); SN64 Chutes inflow $14.9K / outflow −$4.37M (coverage %0.34); SN4 Targon inflow $119K / outflow −$3.41M (coverage %5.9).
- "Coverage" değeri birçok subnette tıpkı %41'de duruyor — muhtemelen sistem parametresi (daha derin yorum yapılmadı).

**KÖK tezi için kritik ders:** Bittensor, "useful work" subnet modelinin **tüketim tabanlı sübvansiyon olmadan ayakta duramadığının** canlı kanıtıdır. "Faydalı iş" pazarında subnet gelirinin ~%88'i token emisyonundan geliyor. Aethir'in "Bittensor 14x Rev/MC geride" claim'i bu tabloyla tutarlı.

### Qubic (QUBIC) — KOK'UN DOĞRUDAN RAKİBİ, ama "useful work"Ü SATMIYOR
Güven: YÜKSEK (resmi site qubic.org fetch edildi)

- "Qubic is a high-performance Layer 1 protocol enabling instant finality, feeless transactions... **Built on Useful Proof of Work (UPoW)**, it's the first to integrate artificial neural networks for the future of Artificial General Intelligence."
- "**Qubic's Useful Proof of Work (UPoW) transforms the energy used in mining into something greater - artificial intelligence.**"
- "Aigarth is the AI powered by Qubic, drawing intelligence from **hundreds of thousands of Qubic miners** to create billions of artificial neural networks (ANNs)." Hedef: **"AGI by 2027"**.
- Fair launch, no premine/VC; mainnet April 2022; "initial idea 2012"; 15.52M peak TPS (CertiK).
- **💰 Qubic compute geliri: BULUNAMADI.** Qubic "faydalı iş"i (Aigarth ANN eğitimi) **satmıyor** — kendi AI projesi için kullanıyor. "Utility" bir compute pazarından değil, AGI umudundan geliyor. Metrikler (miners, community) JS-counter, statik HTML'de rakam yok.

**⚠️ KOK İÇİN ÇOK ÖNEMLİ:** Mevcut en yakın "Useful Proof of Work" L1 (Qubic), faydalı işi bir **gelir kaynağı olarak pazarlamıyor**. Bu, KOK'un "madencilik compute'u gerçek bir pazarda satılır" tezinin öncüllerinden birinin (faydalı işe fiyat keşfi/veriden gelir) test edilmemiş olduğunu gösterir.

### Gensyn — COMPUTE MARKETPLACE'TEN PİVOT GİBİ GÖRÜNÜYOR
Güven: ORTA-YÜKSEK (resmi site gensyn.ai fetch edildi; yorum dikkatli)
- Mevcut positioning (Eylül 2026): "**Gensyn builds AI that forecasts** – and keeps improving – by verifiably closing the loop between prediction and reality."
- **Delphi** (22 Nisan 2026): "Gensyn Launches Delphi: Decentralised Information Markets", "Pricing, Settlement, and Agentic Trading"
- "Introducing **open-1b: the first model you don't have to trust**" (15 Eylül 2026); "**REE: Reproducible Execution Environment**" (17 Mart 2026)
- Araştırma: "Credibly Neutral AI Oracles", "IR3DE", "Markets That Explain Themselves", feedback alignment / self-distillation
- **Gensyn compute geliri: BULUNAMADI.** Ana sayfada GPU marketplace / training compute satışı öne çıkmıyor; odak tahmin/information market + verify edilebilir model.
- ⚠️ Not: Orijinal Gensyn "decentralized ML training compute fabric" olarak biliniyordu. Mevcut site compute marketplace'i öne çıkarmıyor — ya pivot ya da büyük genişleme. Yorumda dikkatli olunmalı; kesin "pivottur" demek için resmi bir "pivoting" açıklaması doğrulanmadı.

### Dynex (DNX) — İKİNCİ DOĞRUDAN PoUW ZİNCİRİ + TOKEN'I KADENEN İPTAL EDİYOR
Güven: YÜKSEK (resmi site dynexcoin.org fetch edildi)
- "At the core of the DNX ecosystem is our **proof-of-useful-work (PoUW) blockchain algorithm**, supported by thousands of miners who contribute GPU resources... computational power is efficiently utilized for solving practical problems."
- "DNX applies a **digital twin of a neuromorphic quantum computer**" — yani "faydalı iş" kendi neuromorphic çözümcüsü.
- Fair launch Eylül 2022, no ICO/premine; max 110M DNX, deflationary.
- **‼️ Dynex Paragon Program (13 Şubat 2026): "introduced as part of our plan to gradually PHASE OUT THE UTILITY TOKEN"** — "as Dynex continues its institutional and corporate trajectory." Katılım "curated and discretionary", "not automatic and not guaranteed."
- **Dynex compute geliri: BULUNAMADI.**

### CUDOS — BULUNAMADI
cudos.org iki denemede HTTP 429 (rate-limit) ile erişilemedi. Bu oturumda CUDOS gelir verisi doğrulanamadı.

### Morpheus (MOR) & Ryze — BULUNAMADI
- "morpheus.network" adlı site bir **tedarik zinciri şirketi** (Morpheus.Network) — aranan AI/MOR token projesi değil. Doğru projenin resmi sitesi bu oturumda bulunamadı.
- Ryze için resmi gelir verisi doğrulanamadı.
- İkisinin de compute geliri yayınlayıp yayınlamadığı: BULUNAMADI.

### BÖLÜM 2 ÖZET TABLOSU — "Gerçek USD compute geliri yayınlayan var mı?"
| Proje | Gerçek compute geliri yayınlayor mu? | Doğrulanan rakam | Kayıt |
|---|---|---|---|
| **Aethir** | ✅ EVET | $127.8M (2025); $166M ARR (Q3 2025) | Kendi blogu (self-reported) |
| **io.net** | ⚠️ KISMEN | "$8M enterprise deals closed Q1 2026" (bookings, recognize edilmiş gelir değil) | Kendi blogu (self-reported) |
| **Bittensor** | ⚠️ Üçüncü parti tracker | 30D inflow $9.85M vs outflow $76.8M → gelirin ~%88'i emission | taorevenue.com (3. taraf) |
| **Akash** | ❌ HAYIR | Sadece kapasite (463 GPU); fiyat claim $1.33/hr H100 | Resmi site |
| **Render** | ❌ HAYIR (raporlar 403) | — | Resmi site |
| **Qubic (UPoW)** | ❌ HAYIR | Faydalı işi satmıyor (Aigarth) | Resmi site |
| **Dynex (PoUW)** | ❌ HAYIR | Token'ı phased out ediliyor | Resmi site |
| **Gensyn** | ❌ HAYİR | Compute marketplace'e odak değil gibi | Resmi site |
| **CUDOS / Morpheus / Ryze** | BULUNAMADI | — | — |

**KÖK tezi için dersler:**
1. **Gerçek USD gelir yayınlayan neredeyse tek ağ Aethir** ($128M/166M ARR). O da self-reported ve gururla rakiplerle karşılaştırıyor ("Render 455x, Bittensor 14x Rev/MC geride") — yani Aethir'in kendi anlatısına göre DePIN compute alanında gelir **istisna**, kural değil.
2. **İki mevcut Proof-of-Useful-Work zinciri (Qubic, Dynex) compute geliri yayınlamıyor.** Qubic faydalı işi kendi AI'ı (Aigarth) için kullanıyor; Dynex kendi neuromorphic çözümcüsü için — ikisi de "maden compute'unu üçüncü taraflara sat" modelini uygulamıyor. **KOK'un tam iddiasının (PoW güvenliği + compute satışı) çalışan, gelir kanıtlanmış bir öncüsü YOK.**
3. **Dynex utility token'ı kademeli olarak iptal ediyor (Şub 2026)** — DePIN tokenomik zorluğunun somut kanıtı.
4. **Bittensor'da gelir ~%88 emission'dan** — "useful work" subnet'leri dış taleple ayakta durmuyor.

---

## 3. "BEDAVA COMPUTE" EKONOMİK İDDİASI — AKADEMİK / CİDDİ ANALİZ VAR MI?

**Kısa cevap: EVET, hem teorik (rekabetçi denge) hem de ampirik (deploy edilmiş sistemde ölçüm) литератür var ve her ikisi de KOK tezinin SAF haliyle (compute "bedava"/marjinal maliyet) TUTMADIĞINI gösteriyor.**

### ⭐ BULGU 1 (TEORİK): "The Economics of Proof-of-Useful-Work" — Rafael Pass
Kaynak: https://arxiv.org/abs/2606.06700 | Güven: YÜKSEK (arXiv abs sayfası fetch edildi, DOI 10.48550/arXiv.2606.06700)
- Yazar: **Rafael Pass** (tanınmış kriptograf). Gönderim: **4 Haziran 2026**. Alanlar: cs.GT, cs.CR, econ.TH.
- Model: compute üç şekilde tahsis edilebilir — (a) saf madencilik, (b) saf faydalı iş (ML inference olarak), (c) "**duplex**" iş — ikisini de üreten, ama **computational overhead** ile.
- Tek ekonomik parametre: **"token-inference ratio"** (token benimsenmesinin inference pazarına oranı).
- **Üç denge rejimi:** "Bitconia" (klasik PoW'ya indirgenir), "**Fortessia**" (duplex madenciliğin yerini alır, güvenliği artırır ama faydalı çıktı DEĞİŞMEZ), "**Duplexia**" (token ödülleri inference'ı sübvansiyonlar, fiyatları düşürür, inference arzını genişletir).
- **"Paid to attack" eleştirisine cevap:** "Contrary to the common strawman argument, PoUW does not make attacks economically cheap: once equilibrium prices are taken into account, the economic cost of a majority attack remains tied to the block reward."
- **🔥 FRİRENGER ÖZET (KOK tezinin kalbi):** "in **Duplexia, block rewards act as REBATES on inference prices**, generating additional socially useful computation that would not arise without the blockchain."
  - Yani: faydalı compute **"bedava" değil** — **blok ödülü/token emisyonu tarafından sübvansiyon edilen** bir şeydir. KOK'un "madenciler zaten çalıştırıyor, marjinal maliyete satar" çerçevesi, akademik olarak "aslında bunu token enflasyonu ödüyor" şeklinde yeniden çerçeveleniyor. Bu, proje sahibinin sorduğu **opportunity-cost sorusunun tam cevabıdır**: duplex mümkün ama bir maliyet (overhead) var ve fiyat düşüklüğü blok ödülünden geliyor.

### ⭐ BULGU 2 (AMPİRİK, EN ÖNEMLİSİ): "The Usefulness Gap in Proof-of-Useful-Work" — Pearl/cuPOW ölçümü
Kaynak: https://arxiv.org/abs/2606.04819 | Güven: YÜKSEK (arXiv abs sayfası fetch edildi, v2, DOI 10.48550/arXiv.2606.04819)
- Yazar: Abhinaba Basu. Gönderim 3 Haziran 2026, revize 5 Haziran 2026. Alanlar: cs.CR, cs.CY, cs.DC.
- **Pearl** ("high-profile AI industry endorsements" olan bir L1) PoUW protokolünü "hem güvenliği sağlayan hem AI inference yapan" olarak pazarlıyor. Kağıt bunu ölçmüş:
  - **"Pearl's 24 EH/s network — approximately 320,000 GPU-equivalents consuming an estimated 112 MW — produces ZERO useful AI computation."**
  - **Ampirik dış maliyet / fırsat maliyeti:** "Budget GPU rental prices **rose 38%** and utilization surged from **57% to 94%** following the mining software's public release, **displacing legitimate research workloads**."
  - (1) 8,012 worker'ın hepsinde inference-capable donanım var, ama **baskın mining yazılımında hiç inference kodu yok**.
  - (2) Doğrulama protokolü **"random matrices"'i tasarım gereği kabul ediyor** (NVIDIA, AMD, CPU, Apple Silicon'da 44 pool-accepted share ile doğrulandı).
  - (3) İstatistiksel dağılım kontrolleri adversarial Gaussian sampling'le kolayca yeniliyor.
  - (4) **Mining ekonomisi marjinal:** PRL fiyatı $0.76'da ROI **-1% ile +67%** arası, çoğu donanım için breakeven'e yakın.
  - (5) Mining hesaplaması **commodity integer arithmetic**, her platforma taşınabilir — vendor lock-in yok.
  - "These findings quantify the **verifiability-usefulness tension** identified theoretically by **Leinweber et al.**"
- **🔥 KOK İÇİN ANLAM BUĞUNUN ÖNEMLİSİ:** KOK'un iddiasının (KW matris çarpımı PoW'yu AI işine satma) **tam benzerini yapan, AI sektörü tarafından onaylanmış bir L1, gerçekte SIFIR faydalı AI computation üretti** — ve bunun bedelini **gerçek araştırma iş yüklerinden çaldığı GPU kapasitesi olarak ödedi** (fiyatlar %38 arttı). Donanımı çift-kullanma iddiası, ampirik olarak "faydalı iş değil, GPU pazarını bozan bir madencilik" olarak gerçekleşti. Mining ROI'sinin breakeven'e yakın olması da "zaten çalışıyorlar, bedava" argümanını zayıflatıyor: madenciler için **değer, blok ödülünde, compute satışında değil.**
- NOT: "Leinweber et al." paper bağımsız olarak bu oturumda doğrulanmadı (Pearl makalesi içinde referans olarak geçiyor).

### BULGU 3: Diğer PoUW literatürü (arXiv API ile doğrulandı)
Kaynak: arXiv API sorguları. Güven: YÜKSEK (başlıklar/yazarlar/tarihler doğrudan arXiv'den)
- **"Challenges of Proof-of-Useful-Work (PoUW)"** — Felix Hoffmann, arXiv:2209.03865 (2022). Coinami, CoinAI, Primecoin analizi; "This version is a draft."
- **"SNARKChain: Proof-of-Useful-Work Blockchain Consensus with General-Purpose SNARK Marketplace"** — Oleksak, Gazdik, Peresini, Homoliak, arXiv:2510.09729 (2025). **KOK'un "verifiable compute market" fikriyle birebir örtüşüyor:** "computes client-outsourced SNARK proofs as a byproduct... decentralized marketplace for outsourcing SNARK proof generation... first such marketplace operating at the consensus layer."
- **"Optimization-based Proof of Useful Work: Framework, Modeling, and Security Analysis"** — Cao, Ling, Wang, Gao, Ding, arXiv:2405.19027 (2024, rev. 2026). "uncover the **trade-off between useful work efficiency and PoW safeguard**."
- **"SEDULity: A Proof-of-Learning Framework"** — Cao, Doger, Ulukus, arXiv:2512.13666 (2025, rev. 2026).
- **"A Proof of Useful Work for Artificial Intelligence on the Blockchain"** — Lihu vd., arXiv:2001.09244 (2020).
- **"Proofware"** — Dong, Lee, Zomaya, arXiv:1903.09276 (2019).
- **"HDCoin: Proof-of-Useful-Work Blockchain for Trustworthy Biomedical Hyperdimensional Computing"** — Wen vd., arXiv:2202.02964 (2022, rev. 2025).
- **"Quantum-Resilient Decentralized AI Economies: PoUW and Post-Quantum Security"** — Barbaccia, Vhaduri, Dibbo, arXiv:2606.24942 (2026).
- **"Coin.AI: A Proof-of-Useful-Work Scheme"** — arXiv:1903.09800 (2019).

### BULGU 4: "Fungible compute" / "dual-use mining" terimleri
- Bu oturumda spesifik bir akademik kaynak doğrulanamadı. **"fungible compute"/"dual-use mining" adında bilinen bir akademik literatür: BULUNAMADI.** Ancak kavram Pass'ın "duplex" modeliyle yakalandı.

---

## 4. VERIFIABLE COMPUTE'U KİM ALIYOR? ("prove you ran this computation")

**Kısa cevap: Hiçbiri GELİR yayınlamıyor. Ve doğrulanan talep pattern'i CRYPTO-İÇ** (zk-rollup'lar Ethereum ölçeklendirme için proof alıyor), **kurumsal "prove you ran this computation" talebi değil.**

### Şirket bazında doğrulananlar:

**RiscZero (risczero.com)** — Güven: YÜKSEK (resmi site fetch edildi)
- Değer önerisi: "With verifiable computation, you can be cryptographically certain that the output of a computation is correct, regardless of who computes it... prove to anyone that critical processes, including financial transactions, are performed correctly, and in a compliant way... enables technology companies to address trust gaps in software supply chains."
- ⚠️ Bu **pazarlama/aspirasyon**, kanıt değil. Ana sayfada tek bir gelir veya kullanım rakamı YOK. Müşteri logosu/kullananları listesi ana sayfada değil.
- **Gelir: BULUNAMADI. Kullanım metrikleri: BULUNAMADI.**

**Axiom (axiom.xyz)** — Güven: YÜKSEK (resmi site fetch edildi; "© 2026 Intrinsic Technologies")
- Pivot/rebrand: artık **OpenVM** (zkVM) + **Axiom Proving API** (proving infrastructure). Eski "zk-coprocessing for Ethereum" konumlandırması yerine proving altyapısı.
- Yayınladıkları **teknik performans** (gelir değil): "1 GHz proving throughput — Proving scales to 1 GHz on 64 GPUs"; "Real-time proving for Ethereum — Prove Ethereum blocks in less than 10s"; "100 bits of provable, post-quantum security"; "Audited by Cantina and zkSecurity"; OpenVM formally verified in Lean (Nethermind + Ethereum Foundation grant).
- **KULLANIM KANITI (crypto-iç):** "OpenVM is live on EthProofs — OpenVM is now proving **Ethereum mainnet blocks** live" (23 Eki 2025); "Proving Ethereum in Real Time with OpenVM 2.0" (29 Oca 2026); "Proving Ethereum in Real Time on 4 GPUs" (29 Tem 2026); "Powering **Lighter EVM**" (30 Oca 2026) — bir EVM rollup.
- **Gelir: BULUNAMADI.** Alıcılar = Ethereum proof üretimi / başka bir rollup → **crypto-iç talep.**

**=nil; Foundation (nil.foundation)** — Güven: YÜKSEK (resmi site fetch edildi)
- Repositioning: "**=nil; is an Ethereum L2, powered by zkSharding**". Orijinal "Proof Market" (verifiable compute marketplace) ana sayfada öne çıkmıyor.
- Tek kullanım metriği: "**300+ developers onboarded**" (geliştirici sayısı, gelir değil).
- Yol haritası: Temmuz 2024 Devnet, Kasım 2024 Testnet, "MAINNET 2025", "2025 Mainnet Alpha — Coming soon". © 2026'ye rağmen mainnet "coming soon" görünüyordu (gecikme sinyali).
- **Verifiable compute geliri: BULUNAMADI.**

**Layer N → "N1" (layern.xyz → n1.xyz)** — Güven: YÜKSEK (resmi site fetch edildi)
- **Layer N, "N1: the blockchain for finance" olarak rebrand olmuş.** Orijinal zk-rollup-for-finance konumlandırması bir finansal L1'e dönüştü.
- Yayınladığı metrikler **kendi borsasının**, verifiable compute satışının DEĞİL: "volume processed: **$3.72B**" (başka yerde "$3.4B+ TRADED"); "actions processed: **5.64B**" ("4.37B+ TXNS"); "active traders: **24,472**" ("23K+ TRADERS").
  - Not: Ana sayfadaki iki sayaç grubu birbirini tutmuyor ($3.72B vs $3.4B+, 5.64B vs 4.37B) — canlı vs marketing sayaçları.
- "N1 is acquiring 01" (8 Tem 2026) — exchange + network birleşimi.
- **Verifiable compute geliri: BULUNAMADI.** ($3.72B, kendi exchange volume'u; proof satışı değil.)

**Brevis (brevis.space)** — Alan adı çözümlenemedi (DNS "Name or service not known"). **BULUNAMADI.**
**Succinct (succinct.com)** — Hem weblocal hem browser'da timeout (SSL handshake / ERR_TIMED_OUT). **BULUNAMADI** (bu oturumda erişilemedi).

### BÖLÜM 4 ÖZET — KÖK tezi için kritik
1. **Hiçbir şirket verifiable compute geliri yayınlamıyor** (RiscZero, Axiom, =nil;, N1). Yayınladıkları ya teknik performans (Axiom: GHz throughput) ya kendi ürün kullanımı (N1: exchange volume) ya da geliştirici sayısı (=nil;: 300+).
2. **Doğrulanan tek gerçek talep crypto-iç:** Axiom'un proof'ları **Ethereum mainnet bloklarını** (EthProofs) ve **Lighter EVM** rollup'ını çalıştırıyor. Yani alıcılar "prove you ran this computation" isteyen kurumsallar değil, **ölçeklendirme için proof satın alan diğer blockchain'ler.**
3. **Kurumsal "provably correct computation" talebi için kanıt: BULUNAMADI.** RiscZero'un "financial transactions / compliance / supply-chain trust gaps" dilinin kanıt değil aspirasyon olduğu not edilmeli.
4. **KOK'un "fee-paid verifiable compute market" (U layer) için:** Tüketici tarafında bağımsız olarak doğrulanmış bir kurumsal talep piyasası yok; mevcut talep zincir-içi (rollup ölçeklendirme). KOK'un U-layer'ı için gerçekçi talep kaynağı **diğer zincirlerin proof/execute ihtiyacı** olabilir — bu önemli bir stratejik bulgudur.

---

## 5. COLD-START / İKİ TARAFLI PİYASA (TAVUK-YUMURTA) LİTERATÜRÜ

### BULGU 1 (akaademik): Madencilik maliyeti ↔ ödül ↔ güvenlik iç içe geçmiştir
Kaynak: https://arxiv.org/abs/2102.08107 | Güven: YÜKSEK (arXiv abs ile doğrulandı)
- **"Interdependencies between Mining Costs, Mining Rewards and Blockchain Security"** — Pavel Ciaian, d'Artis Kancs, Miroslava Rajcaniova (2021).
- "studies to what extent the cost of operating a proof-of-work blockchain is intrinsically linked to the cost of preventing attacks, and to what extent the underlying digital ledger **security budgets are correlated with the cryptocurrency market outcomes**. We theoretically derive an equilibrium relationship between the **cryptocurrency price, mining rewards and mining costs, and blockchain security outcomes**... empirical evidence of cryptocurrency price and mining rewards indeed being intrinsically linked to blockchain security outcomes."
- **KOK ile bağlantı:** PoW zincirinde güvenlik = ödül × fiyat × maliyet dengesine bağlıdır. Yeni bir zincirde **fiyat yoksa ödül değersizdir, ödül değersizse madenci yoktur, madenci yoksa güvenlik yoktur** — bu, tavuk-yumurta probleminin PoW'daki tam ekonomik formudasyonudur. KOK'un PoW + faydalı iş modeli bunu iki yönlü çözmeye çalışıyor (madencilere hem blok ödülü hem compute geliri), ama Ciaian vd. güvenliğin fiyat/ödül bağımlılığını tek yönlü kurmuştur.

### BULGU 2 (belgelenmiş vaka): Yetersiz madenci/güvenlik → 51% saldırısı → ölüm (PoW cold-start failure mode)
Kaynak: https://en.wikipedia.org/wiki/51%25_attack ("Double-spending" maddesine yönlendirme) | Güven: YÜKSEK (Wikipedia, kaynaklı)
- Wikipedia "Examples of double-spending caused by 51% attacks" (doğrulanan alıntılar):
  - **Bitcoin Gold:** "was hit by two double-spending attacks as the result of a 51% attack. This cost exchanges **$18M in Sept 2018** and **$72k in January 2020**."
  - **Ethereum Classic:** "experienced a 51% attack in **2019**, followed by **multiple more in 2020**, significantly impacting its security and market perception. Attackers attempted a **$1.1M double-spend on Coinbase** and successfully double-spent **$200k on Gate.io**. These attacks... leading to concerns regarding the **long-term viability** of the Ethereum Classic blockchain."
  - Bitcoin (Mart 2013): 0.8.0 istemci hatasından zincir bölünmesi; 24 blok revert edildi — bu kötü niyetli 51% değil, bug kaynaklı.
- **KOK için somut ders:** PoW L1'lerde "kullanıcı/madenci yokluğu" ölümü **belgelenmiş bir modeldir**: düşük hash rate → 51% saldırısı → borsalara zarar → delisting → "long-term viability" endişesi. KOK, KW matris-çarpım PoW kullanacağı için **başlangıçta hash rate'u kim finanse edecek** sorusu bu vakaların ışığında kritiktir. (Ayrıca KW PoW'un Bitcoin/ETH hash power'ı ile aynı donanımda çalışıp çalışmayacağı — yani NiceHash-style kiralama saldırı yüzeyi — bu oturumda doğrulanamayan açık bir sorudur.)

### BULGU 3: "Blockchain cold-start / two-sided market" adanmış akademik literatür
- "blockchain AND bootstrapping", "two-sided market AND cryptocurrency", "network effects AND adoption", "tokenomics AND adoption" arXiv sorguları **bu çerçeveye odaklanmış adanmış bir paper vermedi** (sonuçlar eclipse saldırıları, PBS, Bisq, AI token kullanımı vb. yanlış-isabetler).
- **"Tavuk-yumurta / cold-start / iki-taraflı platform bootstrapping" adında doğrulanmış bir blockchain akademik literatür: BULUNAMADI** (bu oturumda). Kavram YUKARIDAKİ iki bulguyla (güvenlik-bütçe ekonomisi + 51% ölüm vakaları) somutlaştırıldı.
- Not: Klasik iki-taraflı platform ekonomisi (Rochet–Tirole vb.) literatürü crypto'ya uyarlanmış şekilde bu oturumda canlı olarak doğrulanamadı.

---

## GENEL SONUÇ — KOK NETWORK v2 İÇİN EN KRİTİK 5 BULGU

1. **GPU fiyatları zaten marjinalin üstünde ama spot düşük:** H100 on-demand $2.89-6.16/GPU-saat; **spot/preemptible $2.15-2.46**. Akash $1.33, io.net $2.20 iddiası. KOK'un compute'u **$2/GPU-saat'nin altına** satması gerekir — bu, blok ödülü sübvansiyonu olmadan zor (Bak: BULGU 2).
2. **"Bedava compute" yanlış çerçeve:** Rafael Pass'ın (Haziran 2026) rekabetçi-denge modeli, faydalı compute'un **blok ödülüyle sübvansiyon edilen inference rebate'i** olduğunu gösteriyor — "bedava" değil, **token enflasyonunun ödediği** bir sübvansiyon.
3. **Ampirik olarak PoUW "faydalı iş" üretmedi:** Pearl/cuPOW ölçümü (Haziran 2026) — 24 EH/s, 320K GPU, 112 MW, **SIFIR faydalı AI computation**; üstelik **budget GPU kiralama %38 arttı, kullanım %57→%94, araştırma iş yükleri yerinden edildi**. KOK'un tezinin gerçek dünyadaki benzeri fiyaskoyla sonuçlandı.
4. **Gerçek USD gelir yayınlayan yok denecek kadar az:** Aethir ($127.8M/2025, $166M ARR) istisna; **iki mevcut PoUW zinciri (Qubic, Dynex) compute geliri yayınlamıyor** ve Dynex **utility token'ı iptal ediyor** (Şub 2026). Bittensor gelirinin ~%88'i emission. KOK'un "PoW güvenliği + compute satışı" kombosunun **gelir kanıtlanmış çalışan bir öncüsü yok.**
5. **Verifiable compute talebi crypto-iç:** Axiom Ethereum blokları kanıtlıyor (EthProofs), =nil; L2, N1 finansal L1 — **hiçbiri gelir yayınlamıyor, kurumsal "prove this" talebi için kanıt BULUNAMADI.** KOK U-layer'ı için gerçekçi müşteri diğer zincirler olabilir.

---
