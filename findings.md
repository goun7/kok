# ARAŞTIRMA BULGULARI (19 Eylül 2026) — KÖK Network değerlendirmesi

> Tüm veriler 2026-09-19 tarihinde canlı kaynaklardan alınmıştır. Kaynaklar: arXiv API, IACR ePrint,
> CoinGecko API, Digiconomist.

## 1. PoUW (Faydalı İş) Ekonomisi — GÜNCEL AKADEMİK (2026)
- **arXiv 2606.06700 — "The Economics of Proof-of-Useful-Work" (Rafael Pass, Haziran 2026):**
  PoUW'nin "saldırana ödeme yapılır" (paid-to-attack) eleştirisini formal bir rekabet-dengesi
  modeliyle çürütüyor. Useful work makinesi **ML inference** olarak alınmış. Üç rejim:
  "Bitconia" (klasik PoW'ya indirgenir), "Fortessia" (duplex madenciliği replaces mining,
  güvenlik artar, faydalı çıkış değişmez), "Duplexia" (token ödülleri inference fiyatını
  sübvansiye eder). **Sonuç:** PoUW saldırıları ucuzlatmaz; denge fiyatları hesaba katılınca
  majority saldırı maliyeti blok ödülüne bağlı kalır. Duplexia'da blok ödülleri inference
  fiyatlarına rebate gibi çalışır.
  → KÖK'ün vizyonu akademik olarak savunulabilir; ANCAK model "duplex overhead" ve
  "token-inference ratio" gibi parametrelere dayanır — KÖK kâğıdı bunlardan hiç bahsetmiyor.
- **arXiv 2510.09729 — "SNARKChain" (Ekim 2025, rev. Temmuz 2026; Oleksak, Gazdik, Peresini, Homoliak):**
  PoUW consensus + SNARK marketplace. **KRİTİK ELEŞTİRİ:** "existing PoUW proposals often fail to
  embed the integrity of the chain and the identity of the miner into the puzzle solutions, not
  meeting the necessary requirements for PoW and thus rendering them vulnerable."
  → KÖK kâğıdı tam da bu hataya düşüyor: matris ispatını blok içeriğine/madenci kimliğine
  bağlayacak (grinding/precompute/replay önleyici) hiçbir mekanizma yok.
- **arXiv 2209.03865 — "Challenges of Proof-of-Useful-Work" (Hoffmann, 2022):** Primecoin, Coinami,
  CoinAI analizleri; PoW'nin gerekli özelliklerini useful work yaparken korumanın koşulları.
- **arXiv 2405.19027 — "Optimization-based PoUW" (Cao ve diğerleri, rev. Ağustos 2026):** PoUW için
  güvenlik koşulları, **"lower bound for security overhead"** ve "useful work efficiency ↔ PoW safeguard"
  arasındaki trade-off; reward function tasarımı gerekli; long-range attack'a karşı koşul.
- **arXiv 2001.09244 — "A Proof of Useful Work for AI on the Blockchain" (2020):** ML training tabanlı
  PoUW (Thorough/ AI chainline). Öncül iş.

## 2. Doğrulama Kriptografisi (GKR / Sumcheck / zkML)
- **arXiv 2501.05500 — "A Survey of Interactive Verifiable Computing: Low-degree Polynomials"
  (Ocak 2025):** sumcheck + GKR temelleri, modern zkSNARK'lara köprü.
- **arXiv 2607.21162 — "Agree on the Model, Verify the Inference: GKR Protocols for HND-Based
  Transformer Inference" (Temmuz 2026):** GKR ile Transformer inference doğrulama; verifier
  pahalı public değerlendirmeleri bir compute worker'a delege ediyor (honest-verifier +
  prover-worker non-collusion varsayımı). → GKR inference doğrulama 2026'da aktif araştırma.
- **arXiv 2606.16146 — "When Proofs Meet Hardware: NTT vs SumCheck" (Haziran 2026; NYU/CMU
  ekibi, B. Bünz dahil):** SumCheck **ardışık bağımlı round'lardan** muzdarip; NTT
  hardware-friendly (locality + data reuse). "Evrensel kazanan yok." → KÖK'ün "sumcheck =
  mikrosaniyede doğrulama" iddiası donanım gerçekliğiyle uyuşmuyor: sumcheck sequential round'ları
  yüksek latency yaratır.
- **arXiv 2602.17452 — "Jolt Atlas: Verifiable Inference via Lookup Arguments" (Şubat 2026):**
  ONNX tensör operasyonları için lookup-argument zkML; sumcheck kullanır; streaming proving;
  "on-device, specialised hardware olmadan" doğrulama iddiası.
- **arXiv 2508.21393 — "VeriLoRA" (NDSS 2026):** LoRA fine-tuning için ZKP, sumcheck + lookup +
  polynomial commitment; 13B parametreye kadar.

## 3. Post-Kuantum Folding / IVC
- **ePrint 2024/1731 — "Arc: Accumulation for Reed–Solomon Codes" (Bünz, Mishra, Nguyen, Wang;
  CRYPTO 2025, 3 revizyon):** Hash-tabanlı (random-oracle-only) accumulation scheme; homomorphic
  vector commitment'e (ve dolayısıyla kuantum zafiyetine) ihtiyaç yok; **sınırsız accumulation
  depth**. → KÖK'ün "Lattice Folding" spekülasyonundan başka bir yol: **hash-tabanlı folding
  zaten post-kuantum güvenli ve daha basit.** KÖK kâğıdı bu olgunluğu göstermiyor; "Lattice-Jolt"
  adı spekülatif.

## 4. GHOSTDAG / BlockDAG Teşvik Saldırıları (KÖK'ün seçtiği DAG protokolü)
- **arXiv 2109.01102 (2021) ve 2305.16757 (2023) — Perešíni, Homoliak, Benčić, Malinka:**
  PHANTOM/GHOSTDAG'in **random transaction selection (RTS) stratejisi Nash dengesi değildir**;
  protokolden sapan açgözlü madenciler daha çok kazanır, throughput düşer ve **ortak mining pool
  kurmaya teşvik edilir → merkeziyetsizlik bozulur.**
- **arXiv 2501.10888 (ACNS 2025) — Keller:** DAG tabanlı PoW protokolleri için otomatik selfish
  mining MDP çözücüsü (GhostDAG dahil).
- Kaspa whitepaper: IACR ePrint 2018/104 (PHANTOM).
- **Kaspa CoinGecko tanımı (2026):** Kendini artık "world's global sequencer for traditional
  finance and decentralized crypto markets" olarak konumluyor; akıllı sözleşmeler **based-rollups**
  ile. Yani Kaspa'nın 2026 vizyonu useful-work değil, sequencing + rollup'tır.

## 5. PİYASA VERİLERİ (19 Eylül 2026, CoinGecko canlı)
| Varlık | Fiyat | Mkt Cap | Rank | ATH | ATH'ten |
|---|---|---|---|---|---|
| BTC | $81,448 | $1.637T | 1 | $126,080 (2025-10-06) | −35.4% |
| KAS (Kaspa) | $0.0399 | $1.104B | 75 | $0.2074 (2024-07-31) | −80.8% |
| TAO (Bittensor) | $264.2 | $3.00B | 36 | $757.6 (2024-03-07) | −65.1% |
| RNDR (Render) | $1.58 | $820M | 87 | $13.53 (2024-03-17) | −88.3% |
| AKT (Akash) | $0.568 | $170M | 202 | $8.07 (2021-04-06) | −93.0% |
| **DNX (Dynex)** | **$0.00119** | **$128,225** | **5641** | $1.39 (2023-11-20) | **−99.91%** |

- **Kaspa arz:** circulating 27.71B / max 28.70B KAS → **%96.5 çoktan madencilikle çıktı.**
  Kalan tüm emisyon ~1B KAS (~$40M). Kaspa emisyon modeli 2026'da tükenmiş durumda.
- **Dynex:** "Proof of Useful Work" + neuromorphic computing iddiası olan en yakın analog;
  **3 gün önce (2026-09-16) kendi tüm zamanların en düşük seviyesinde.** market cap $128 bin.
- Qubic (QBIC) CoinGecko'da listeli değil / delist — "useful work" L1 kategorisi piyasada yoksul.

## 6. ENERJİ (Digiconomist, 19 Eylül 2026)
- Bitcoin yıllık **204.44 TWh** (Tayland kadar), 114.03 Mt CO2, tx başına 769.43 kWh.
- Digiconomist'in "latest research" (Mayıs 2025): **"AI could consume more power than Bitcoin by
  the end of 2025."** → AI'nin enerji talebi PoW'yu geçiyor; iklim argümanı artık çift yönlü.

## 7. EK BULGULAR (2. tur)

### 7.1 ÖNCEL SANAT (Prior Art) — FİKRİN ZATEN YAYIMLANDIĞI KANIT
- **arXiv 2604.18614 — "HadAgent: Harness-Aware Decentralized Agentic AI Serving with
  Proof-of-Inference Blockchain Consensus" (Nisan 2026, Jimenez, Weatherspoon, Shen, Sheng, Liu, Li):**
  Hash-based mining'i **Proof-of-Inference (PoI)** ile değiştirir; düğümler deterministic LLM inference
  görevlerini çalıştırarak blok oluşturma hakkı kazanır. Doğrulama "tek bir forward pass'in aynı
  koşullarda re-execution'ı" ile consensus hızında. Üç şeritli blok gövdesi (DATA / MODEL / PROOF,
  her biri ayrı Merkle root), two-tier trusted/non-trusted düğüm mimarisi, optimistic execution,
  harness (heartbeat + anomali tespiti + otomatik trust yönetimi). **Prototip sonuçları:** bozulan
  kayıtlarda %100 tespit, %0 false positive, sub-ms validasyon latency'si; adversarial düğümleri
  2 turda dışlama, honestları 5 turda trusted'a yükseltme.
  → KÖK'ün "paradigm shift" iddiası Eylül 2026 itibarıyla **yeni değil**: 5 ay önce çalışan
  prototiple yayımlandı ve KÖK'ün hiç çözmediği sorunları (deterministik re-execution, model
  kanalı, trust yönetimi) çözüyor.
- **arXiv 2603.19025 — "Towards Verifiable AI with Lightweight Cryptographic Proofs of Inference"
  (SaTML 2026, Mart 2026; Anchuri, Campanelli, Cesaretti, Gennaro, Jois, Kayman, Ozdemir):**
  **"existing cryptographic proof systems ... introduce prohibitive prover overhead (e.g., hundreds
  of seconds per query for billion-parameter models)."** Çözümleri: Merkle tabanlı trace commitment +
  rastgele örneklenmiş yollar üzerinde az sayıda açılım; soundness'i verimliliğe takas eder;
  "rationally incentivized provers who face penalties upon detection" senaryosu (tam blokzincir
  madenciliği) için uygundur. Dakikalar → milisaniyeler. ResNet-18 ve Llama-2-7B'de doğrulandı.
  → **ÖLÜMCÜL:** Kriptografik ispat = milyar parametreli model başına **yüzlerce saniye** prover
  süresi. Yani KÖK modelinde enerjinin ezici çoğunluğu "faydalı inference" değil, **ispat
  üretimine** gider. Fayda/total oranı ~1/100.000. Premisin tam tersi.

### 7.2 ZKML'DE MATRİS İSPATI MALİYETİ
- **arXiv 2504.12217 — "zkVC" (DAC 2025):** "even basic operations like matrix multiplication
  require an extensive number of constraints, resulting in significant overhead"; öncül yöntemlere
  göre **12 kat** proof hız artışı. → Matmul için ZK ispat hala çok pahalı.
- **arXiv 2606.11458 — "Computational Attestations of Polynomial Integrity" (FTC 2024/2025):**
  50.000 örnekli DP linear regression'ın correct training ispatı tek makinede **<6 dk**, doğrulama
  **0.17 sn**. → Küçük görevler bile saniyeler-saatler mertebesinde.

### 7.3 KAYAN NOKTA / DETERMİNİZM SORUNU (ÇÖZÜCÜ TEKNİK NOKTA)
- **arXiv 2603.20421 — "Hawkeye: Reproducing GPU-Level Non-Determinism" (MLSys 2026; Badash, Boneh,
  Komargodski, Srivastava):** GPU matmul **non-determinist** — rounding direction, subnormal handling
  ve **non-associative accumulation** + Tensor Core reduction order. Aynı sonucun CPU'da kayıpsız
  re-produksiyonu için özel test dizisi gerekiyor. "Prior approaches to verifiable ML either
  introduce significant computation overhead ... or suffer from non-robustness and quality
  degradation."
  → GKR/sumcheck **sonlu cisim** (exact arithmetic) ister; gerçek AI inference **FP8/FP16/BF16
  tensor core**'larla yapılır ve non-associative'dir. KÖK'ün "A×(B×r) == C×r" eşitliği FP'de
  ses değildir (yuvarlama hataları birikir); exact cisimde yapmak ise tensor core'lardan vazgeçmek
  demektir — yani "faydalı" iş olmaktan çıkar. **Çözülmez bir gerilim.**

### 7.4 ÖLÇEKLENDİRME VERİLERİ
- **Bitcoin hashrate: ~904 EH/s** (blockchain.info /q/hashrate, 2026-09-19).
- **Bitcoin emisyonu:** circulating 20.087M / 21M → ~%95.7 madencilikle çıktı; blok ödülü (2024
  halving sonrası) 3.125 BTC. Güvenlik bütçesi ~$4.4B/365 gün (fiyattan). Kaspa'nın kalan
  emisyonu ~1B KAS ≈ $40M — Kaspa da artık tail-emission'da.

### 7.5 İŞ FONKSİYONUNUN ZORLUK VARSAYIMI ÇÖKÜYOR (Ağustos 2026)
- **arXiv 2608.16884 — "Improving the matrix multiplication exponent with modern optimization and
  AlphaEvolve" (17 Ağustos 2026; Dupont, Eisenberger, Kozlovskii, Mehrabian, Ruiz, See, Zhou,
  Alman, Vassilevska Williams, Balog):** **ω < 2.371177** (önceki en iyi 2.371339). Çizgi:
  Duan ve diğerleri 2022 → Williams ve diğerleri 2024 → Alman ve diğerleri 2025 → 2026. **Laser
  method + combination loss analysis** optimizasyonu ML (AlphaEvolve) ile çözülüyor.
  → KÖK'ün güvenlik varsayımı "matris çarpımı = O(n³) zor iş" — ama bu üstel, **projenin
  tapındığı yapay zeka tarafından bizzat küçültülüyor**. Pratikte Strassen (2.807) ve
  ML-keşifli algoritmalar (AlphaTensor benzeri) zaten sub-cubic. İşin zorluk katmanı **akışkan**.

### 7.6 "Lattice-Jolt" ADI BOŞ (gerçek Jolt ayrı bir şey)
- arXiv'te "Lattice-Jolt" / "lattice-based lookup argument" **hiç yok**. Gerçek Jolt = lookup
  argument proving system (Arasu ve diğerleri, 2024); Şubat 2026'da **Jolt Atlas** (arXiv
  2602.17452) ile ONNX tensör operasyonları için zkML'ye genişletildi (sumcheck tabanlı, non-lineer
  fonksiyonlar için lookup, "on-device, specialised hardware olmadan" doğrulama).
- KÖK kâğıdının "Lattice-Jolt veya yeni bir PQC standardı" ifadesi **gerçek olmayan bir standart
  adı**. Gerçek PQ seçenekler: lattice tabanlı folding (BCLMS 2024) veya **hash tabanlı folding
  (Arc, CRYPTO 2025)**.

## 9. PASS POUM EKONOMİSİ — TAM MODEL (arXiv 2606.06700, ar5iv üzerinden)

**Aktiviteler:** M (solo mine), L (solo inference), D (duplex). Compute-op maliyeti e (all-in, ~$1).
Her D op → 1/α inference + 1/γ security (α,γ ≥ 1; KW için ~1.3, yani %23 fire).
**Toplamlar:** S := M + D/γ (güvenlik; majority saldırısı S/2 op); Q := L + D/α (inference arzı).
**Kâr:** π_M = PR/S − e; π_L = p − e; π_D = PR/(γS) + p/α − e. Rekabetçi denge: π_X ≤ 0 her X,
π_X = 0 aktif X. Mining = **Tullock contest** (tam ödül dağılımı: eS = PR); inference = **Bertrand**
(p = e whenever L aktif).
**Duplex index:** Δ := 1/γ + 1/α − 1. Δ<0 → duplex dominated; Δ>0 → duplex aktif.
**T/I oranı:** θ := PR/(pQ). Parasal temel (Fisher): ℰ = θ_raw·pQ = PVX; X = (ν/λ)R;
**θ = (λ/(νV))·θ_raw** — sadece parasal primitiflere bağlı, α,γ'den bağımsız.
**Theorem 1 (3 rejim):**
1. **Bitconia (Δ<0):** M>0, D=0, L>0, p=e, Q=D(e), S=M. Klasik PoW.
2. **Fortessia (Δ>0, θ<θ_low := α−1):** M=0, D>0, L>0, p=e, Q=Q^Bitconia, S=D/γ > S^Bitconia.
   Faydalı çıkış aynı, güvenlik ↑.
3. **Duplexia (Δ>0, θ>θ_low):** M≥0, D>0, L=0, p<e, Q=D(p)>Q^Bitconia, S>S^Bitconia.
   Karışık (D+M) için θ>θ_high := 1/(γ−1) (γ=1.3 → θ>3.33).
**Theorem 3 (pure Duplexia):** p = (α/(1+θ))·e; ΔSV = V_chain − [deadweight loss] − e(α−1)·D(p).
**Prop 1:** Bitconia/Fortessia'da p=e, ΔSV = V_chain − PR.
**Duplexia, Bitcoin'i aynı θ'da geçer iff θ < 1/(ε−1)** (isoelastic D(p)=Kp^−ε, ε>1; ε=2 → θ<1).
**Saldırı maliyeti:** tüm rejimlerde **PR/2** (Fortessia'da Bitcoin'e eşit, Duplexia'da ≥).
**Israf:** W := M + D(1−1/α); **S − W = DΔ** (Δ>0 iken güvenlik israfı aşar).
**Theorem 4 genel sınıflandırma:** her rejim için P formülleri (ör. Fortessia: P=(γS/R)·e(1−1/α)).
**Stok etkileri (§1.8):** Bitcoin ASIC filosu ~$20B (1000 EH/s × $20/TH/s), madenci BTC'leri ~$50B;
Duplexia'da saldırı sonrası GPU değer kaybı oranı = 1 − ρ^ε/α (ρ=p/e). Yönlendirilebilirlik
(Fortessia'da solo-inference GPU'ları saldırıya redirect edilebilir) + gözlemlenebilirlik
(ASIC stoklama gizli, GPU diversion gözlemlenebilir).
**Açık sınırlama (§1.8 "Availability of Useful Work"):** duplex madencilerinin talep çekme
sürtüşmesi modelde yok → **büyük inference sağlayıcıları etrafında agregasyon** (Bitcoin havuzları
gibi) beklentisi açıkça belirtilmiş.

## 10. ÖNCEL SANATTA DEVRİM — KW YAPISI VE PEARL NETWORK

- **IACR ePrint 2025/685 — "Proofs of Useful Work from Arbitrary Matrix Multiplication"
  (Ilan Komargodski, Omri Weinstein; 2025-04-15, 3 rev., son 2025-12-08):**
  Nakamoto PoW'u **gerçek bir görev** T(x) üzerine kurma sorusu — **madencinin kendi girdi x'ini
  seçtiği** permissionless ayar. **1+o(1) multiplicative overhead** naive MatMul'a göre;
  **prescribed hardness**; "even in the presence of Fast Matrix Multiplication-style algorithms,
  which are currently impractical" (yani ω<2.371177 bulgusuna karşı dayanıklı iddiası).
  Güvenlik: "batch of low-rank random linear equations" sorununa indirgeme — **conjecture**
  (kanıtı yok). **"O(1)-factor overhead is trivial for any task T, but also useless"** — KÖK v1'in
  Freivalds denklemi tam olarak budur. "This blockchain is currently under construction."
  → **v1'in en yakın akademik-commercial rakibi Pearl Network'tür** (Pass'ın danışmanlığı,
  KW yapısı üzerine). Dynex bir ceset; Pearl ise eşlerinden oluşan bir ekip.
- **arXiv 2505.21685 — "Proof of Work With External Utilities" (May. 2025, Komargodski dahil):**
  Fiat ve diğerlerini devamı; heterojen maliyet + **dış ödüller** (external rewards) altında PoW
  denge. Bulgu: dış teşvikli madenciler **faydalı görevleri tek bir blokta toplamaya** optimize
  edebilir → DAG/task-atama tasarımı için uyarı.
- **arXiv 2512.13666 — SEDULity (rev. Haz. 2026):** Proof-of-Learning; **template block'u eğitim
  sürecine kodlama** (= zincir bağlama tekniği); "difficult to solve but easy to verify" fonksiyon;
  rasyonel madenciyi dürüst eğitime teşvik parametreleri.
- **arXiv 2404.09005 — "Proof-of-Learning with Incentive Security" (rev. May. 2026):**
  **incentive-security** kavramı; controllable difficulty; Θ(1) → O(log E/E) overhead;
  **güvenilmeyen problem sağlayıcılarına** karşı frontend incentive-security;
  **Verifier's Dilemma'yı aşan** verifier incentive-security. → Görev pazarı için zorunlu kavramlar.

## 11. DEĞERLENDİRME GÜNCELLEMESİ (KW/Pearl sonrası)
- KÖK v1'in "yapısal-matris saldırısı" eleştirisi hâlâ doğru (Freivalds = trivial O(1) overhead,
  KW'ye göre işe yaramaz), **ama çözümü var**: KW. Bu, v2'nin iş fonksiyonunu **"proof generation"
  yerine "KW MatMul PoUW + üzerinde premium SNARK hizmet katmanı"** olarak revize etmeyi gerektirir.
- ω<2.371177 tehdidi KW tarafından explicitly addresslenmiş (FMM'ye dayanıklılık iddiası);
  güvenlik hâlâ bir **conjecture** (low-rank random linear equations sertliği) — bu dürüst bir
  bağımlılık olarak spec'e yazılmalı.

## 12. DOĞRULANACAK / AÇIK NOKTALAR
- Türkiye kripto varlık düzenlemesinin 2026'daki tam durumu (kanun + CMB/MASAK ikincil mevzuat,
  madenciliğin ve fair-launch token'ın hukuki durumu) — doğrudan erişilebilir kaynakla doğrulanmadı.
- Kaspa canlı hashrate / saniye blok sayısı (kaspa.stream JS-ağır; API bulunamadı) — ~10 BPS
  hedefi literatürde var ama canlı veri çekilmedi.
- Pearl Network'ün teknik dokümanları/protokol detayları (KW yapısını nasıl uyguladıkları,
  DAG mi yoksa chain mi kullandıkları, emisyon modeli) — resmi sitesi üzerinden doğrulanmadı.
- KW güvenlik conjecture'ının durumu (kanıtlandı mı?) — 2025-12-08 son revizyon itibarıyla hâlâ
  conjecture olarak okunuyor; bağımsız kriptografik inceleme gerekir.

## 13. PEARL'İN ÇÖKÜŞÜ — EMPİRİK KANIT (arXiv 2606.04819, Basu, Haz. 2026)

**"The Usefulness Gap in Proof-of-Useful-Work: An Empirical Study of Pearl's cuPOW Protocol"**
(Abhinaba Basu, NIELIT/IIITA; code: github.com/abhinaba/pearl-usefulness-gap). Pearl mainnet'inde
ilk sistematik PoUW ölçümü:

- **24 EH/s'lik ağ (~320.000 GPU, ~112 MW) sıfır faydalı AI hesaplaması üretiyor.**
- **Doğrulama protokolü "tasarımdan dolayı" rastgele matrisleri kabul ediyor**: 44 havuz-onaylı
  share ile kanıtlandı (NVIDIA 3, AMD MI300X 41 = **ilk non-NVIDIA Pearl share'leri**, CPU EPYC
  1.283 tiles/s, Apple M2 Metal 21.693 tiles/s → **donanım kilidi yok**).
- 8.012 AlphaPool worker'ının (24 EH/s'nin ~%21'i = 5.08 EH/s) hepsinde inference-capable donanım
  var; **baskın madenci yazılımında (alpha-miner v1.6) tek bir ML framework string'i yok**
  (vllm/transformer/llama/safetensor: 0/4.803 string; 95% CI [0, 0.0007]); runtime profili
  (2.7–3.7 GB VRAM, %95–100 compute, <%30 memory bw) saf GEMM'i gösteriyor.
- **Kurtosis kontrolü yenilebilir**: uniform random 1.79 vs quantized NN ağırlıkları 3.33;
  adversarial Gaussian 𝒩(0,18) clipped → 2.97 → naive eşik kontrolü geçer (sıfır ek maliyetle).
- **GPU dışsallığı**: vast.ai budget GPU kullanımı %57→94, fiyat +38%; DID ile Pearl'e atfedilen
  +%23 → **araştırma topluluğuna ~$600K/yr deadweight loss**; gerçek işleri etti.
- **Ekonomi**: 800 blok/gün (108s) × 2.674 PRL × $0.76 = **$1.63M/gün gelir** vs ~$1.54M/gün
  maliyet (320K GPU × $0.20/sa) → oran 1.06 = **dengeye yakın**. Breakeven PRL $0.46–0.77
  (GPU tier'a göre; RTX 3060 Ti +67%, RTX 3090 −1%, MI300X −99%). vLLM coupling'in 10–30%
  hashrate fire'si → madenciler inference'ı **rasyonel olarak atlar**. PRL volatilitesi >%200
  → madenciler spot'u düşse bile "call option" için kazıyor (spekülatif madencilik).
- **cuPOW'nun Pearl'deki uygulaması (NoisyGEMM):** A∈Z^{M×K}, B∈Z^{N×K}, girişler {−64..64}
  (int8, 129 değer); commit blake3 → commitment'tan structured noise → rank-R chunk'larında
  noised GEMM → XOR tile-reduce + jackpot hash → blake3(jackpot) < target → Merkle proof.
  verify_plain_proof: (i) değer aralığı, (ii) Merkle tutarlılığı, (iii) recomputed tile = jackpot,
  (iv) hash hedefi. **"Critically, it does not check whether the matrices originate from an AI
  model."** Reference implementation: `rng.random_range(-64..=64)` = düz rastgele.
- **Basu'nun teorik atıfı:** Hoffmann (arXiv 2209.03865, "Challenges of PoUW") —
  **verifiability-usefulness gerilimi**: kolay doğrulanan görevler faydalı değildir, faydalı
  görevleri verimli doğrulamak zordur. (arXiv listeleme özetinde "Leinweber et al." yazıyor ama
  ar5iv tam metninde atıf Hoffmann'dır.)

## 14. POUM'UN TEORİK SINIRLARI (2025–2026 negative results)

- **ePrint 2026/1492 — Demirel, "Proof of Demand Is Not Proof of Work"** (Snowfall Finance;
  2026-07-21, rev. 2026-08-23): iş makbuzlarında **W (work soundness), B (job binding), E (demand
  exogeneity)** ayrımı; açıklık **E'de**. Lemma 1: koalisyon-kontrollü requester/worker arası
  ödemeler **recoverable transfer**'dır → Sybil-dirençli maliyet katmaz, güvenlik alt sınırı
  nominal değerini sayamaz. Theorem 1: endogenous receipts E'yi certify edemez. **Theorem 2:
  sıfır-talep tasarım normu altında, her admissible talep ortamında safe+live olan ve null-demand
  projection'a kapalı bir mekanizmanın, hizmet makbuzlarının talep bileşeninden BAĞIMSIZ bir
  leader-election yoluna sahip olması zorunludur.** Corollary 4: receipt boost'ları
  profile-dependent sizing'e tabi. Fork-independent salvage value güvenliği nötr, negatif veya
  pozitif bırakabilir. **Constructive: her ödemede geri-alamaz bir vergi (burn) güvenlik
  kaynağıdır.** Sonuç: faydalı-hesap makbuzları ödeme/kollateral/zarar paylaşımı ve **sınırlı,
  fiyatsız** bir seçim boost'u için uygundur — **leader-election tabanı için değil.**
  ("Deployed evidence comprises one reported audit (Pearl cuPOW)" — Pearl'in bir auditi var.)
- **ePrint 2025/1814 — Dikshit, Emami, Sedlmeir, Fridgen, "SoK: Is PoUW Really Useful?"**
  (2025-10-03): 50+ PoUW construction'ın sistematizasyonu; **"PoUW is actually not as useful as
  expected, since the economic and societal utility do not contribute to the security budget."**
  Toulmin-tabanlı değerlendirme; tasarım önerileri: verifiable computation, partial incentive
  allocation, **utility-aware difficulty adjustment**.
- **ePrint 2025/2091 — Fitzi, Kiayias, Michel, Panagiotakos, Russell**, "Efficient and
  PoUW-Friendly Local-Search for Distributed Consensus" (2025-11-13).
- **Sonuç (KÖK v2 için):** "Faydalı iş güvenliği artırır" iddiası **artık savunulamaz**. KW,
  **W'yi (prescribed hardness) çözer**; Pearl'in çöküşü **E'nin çözülmediğini** kanıtlar.
  KÖK v2'nin dürüst mimarisi: (1) güvenlik tabanı = **talepten bağımsız** PoW (filler + memoryless
  difficulty) [Demirel Thm 2'yi construction-level olarak karşılar], (2) fayda = **S2 fee-ödemeli
  görev pazarı** (talep, escrow'a yatırılan fee ile exogenous-by-construction; burn bileşeni
  Demirel'in geri-alamaz vergisi), (3) **"faydalı iş zinciri güvendir" vaadi yok** — sadece
  "Bitcoin-güvenliği + üzerinde gerçek bir verifiable-compute pazarı".

- Türkiye kripto varlık düzenlemesinin 2026'daki tam durumu (kanun + CMB/MASAK ikincil mevzuat,
  madenciliğin ve fair-launch token'ın hukuki durumu) — doğrudan erişilebilir kaynakla doğrulanmadı.
- Kaspa canlı hashrate / saniye blok sayısı (kaspa.stream JS-ağır; API bulunamadı) — ~10 BPS
  hedefi literatürde var ama canlı veri çekilmedi.

---

## 15. Bağımsız KW/cuPOW analizi (19 Eylül 2026) — detay `KW_ANALIZ.md`

KW tam metni **ar5iv** üzerinden alındı (`https://ar5iv.org/abs/2504.09971`; ePrint PDF hala
raw binary, r.jina.ai 403). Formal yapılar:

- **Encode_r/Decode_r:** E=E_L·E_R, F=F_L·F_R rank-r gürültü; decode
  C''=(A·F_L)·F_R+E_L·(E_R·(B+F_L·F_R)), 5 MatMul ama hepsi n×r → O(n²r). Dürüst maliyet
  α(t)=t_MatMul(n)·(1+o(1)).
- **Varsayım 6.4:** "tüm ara değerleri (rank-r iki matrisin çarpımında) hesaplamanın
  maliyeti o(n^(ω_r+1)/r) değil." KW'nin kendisi: çıktı-boyu Θ(n³/r) alt sınırından dolayı
  **otomatik** (ω_r=2 yeterince küçük r için). Açık uç: A=B=0'da dahi aynı maliyet.
- **Lemma 6.5:** E, F tek başına üniform rank-r → her r×r alt blok **marjinal üniform**
  (Claim 6.6 ile birlikte).
- **Remark 2.1:** transcript yerine **her ara bloğu ayrı hash'le** → deneme sayısı matris
  boyutuyla ölçeklenir; bellek Θ(n³/r) sorununu çözer. Pearl'in deploy ettiği varyant budur.
- **Appendix A:** high-rank matrisler için pseudorandom rotation (FastJL, R orthonormal):
  A'=AR, B'=R^T B → A'B=AB, decode'e gerek yok; Θ(r³) per tile varsayımı; SNARK proof of
  proximity için rank testi açık problem olarak bırakılmış.

**Bağımsız değerlendirme (benim, bir LLM olarak — 2 bağımsız kriptograf incelemesi
zorunlu):**

1. **(KRİTİK) Varsayım 6.4 gereksizdir.** PoW yalnızca hash/Merkle kökü ister; kök tüm
   yaprakları gerektirdiğinden (tek-yönlülük), güvenlik (a) ROM + (b) marjinal üniformluk +
   Merkle ile gelir. KW'nin "batch of low-rank random linear equations" ifadesi bu nedenle
   abartılıdır; gereken varsayım **daha zayıf ve standarttır**. → G katmanı için risk
   **düşürüldü**.
2. **Per-tile denge:** deneme/FLOP = r^(−ω), n'den bağımsız → madenci matris boyutunu serbest
   seçse bile difficulty dengesi bozulmaz (r protokol parametresi). ✓
3. **Yapısal saldırıların hepsi çürütüldü** (sparse/permutation, A=B=0, precompute,
   korelasyondan kısayol → X_i·(ΣY·Z)·W_j aynı asimptotik).
4. **Trapdoor matrix (VZ25 arXiv 2502.13065; BN25 arXiv 2502.13060, TCC 2025, LPN tabanlı
   pseudorandom matrisler gizli anahtarla near-linear çarpım):** KW'nin reddini bağımsız
   doğruladım — E,F σ'dan türetilir, saldırgan trapdoor **yerleştiremez** (σ öngörülemez).
   Tehdit yok.
5. **FMM:** simetrik (iki taraf aynı algoritma); ω<2,371339 [ADV+24 arXiv 2404.16349];
   AlphaEvolve 2,371177 (2026). Yalnızca kalibrasyon → ekonomik, kriptografik değil.
6. **Kuantum:** Grover karekök (Bitcoin-pariti); HHL-benzeri algoritmalar klasik hash
   bulamaz. PQ açısından G katmanı Bitcoin ile aynı statüde.
7. **Pratik zafiyetler (küçük, düzeltilebilir):** bellek (per-tile ile çözüldü), ε/n
   eşleştirme (n sabit + ε retarget'te), σ=ctx bağlaması (KÖK T-A2 kapatır), int8 taşması
   (Pearl'in değer-aralığı kontrolü; 𝔽_q spec).

**Sonuç:** G katmanı kriptografik olarak sağlam; **asıl risk fayda talebi (E-gap)**, kriptografi
değil. Spec §A.9 fallback senaryosu "olasılık #1"den "düşük-orta"ya revize edildi.

---

## 16. U-katman prototipi çalıştı (19 Eylül 2026) — kod `u_layer_prototype.py`

Gerçek Python, standart kütüphane only, deterministik. **TV-5..TV-10 + G replay reddi PASS.**

| TV | Sonuç | Beklenen | Önemli |
|---|---|---|---|
| TV-5 | burned=30 escrow=70 bond=100 | 30/70 | burn anında + geri-alamaz (Demirel) ✓ |
| TV-6 | 600>C_FEE=500 REJECT; 250+250 OK | REJECT | anti-aggregation (T-A3) ✓ |
| TV-7 | SLASHED, slash=100, reward=50 | slash | fraud penceresi W_s=100 ✓ |
| TV-8 | 1000/1000 ACCEPT sıfır talepte | canlılık | Demirel Thm 2 ✓ |
| **TV-9** | **uniform 1,81 / nn 3,58 / adversarial 3,04** | Basu 1,79/3,33/2,97 | **Prototip Pearl'in ölçülen başarısızlığını yeniden üretti; adversarial GEÇTİ → dağıtım kontrolü güvenlik DEĞİL** |
| TV-10 | legacy schema REJECT | REJECT | PQ schema gate ✓ |
| G | replay reddi: cert başka ctx'te REJECT | REJECT | T-A2 ✓ |

**TV-9 çarpıcı doğrulama:** prototipin rastgele ürettiği matrislerin kurtosis değerleri
(Basu'nun Pearl ağında **ölçülen** değerlerle neredeyse aynı) ve adversarial N(0,18)'in naive
[2,4] kontrolünden geçmesi, E-gap'in kodda nasıl tezahür ettiğini gösterir. **Ders
(spelllenmiş): dağıtım-kontrolü = uyarı, kanıt değil; fayda yalnızca ödenen fee + burn ile
sertleştirilir.**

---

## 17. Pearl canlı dokümanları — ÇÖZÜLDÜ (19 Eylül 2026, kullanıcı domain'i buldu)

> Kullanıcı domain'i buldu: `pearl.network` GoDaddy park sayfasına düşmüş; canlı alan
> **`pearlresearch.ai`** (Pearl Research Labs, NVIDIA Inception). Önceki denemelerim bu
> nedenle boş 200'ler verdi. **Tam INT whitepaper HTML olarak okundu** — kapsamlı analiz:
> `PEARL_DOCS_ANALIZ.md`. Aşağıdaki "ULAŞILAMAZ" kaydı tarihsel olarak korunur.

### 17.1 Önceki denemeler (tarihsel, domain ölü olduğu için başarısız)

Önceki oturumda `pearl.foundation` DNS ölüydü. Bu oturumda tüm alternatifler denendi:

| Hedef | Sonuç |
|---|---|
| `https://pearl.foundation` | `[Errno -5] No address associated with hostname` (DNS ölü) |
| `https://pearlnetwork.io` | `[Errno -2] Name or service not known` |
| `https://pearl.network` | HTTP 200, **gövde boş** (park veya JS-only; metin çıkmıyor) |
| `https://pearl.network/docs`, `/whitepaper` | HTTP 200, **boş** |
| `https://pearl.xyz` | HTTP 200, **boş** |
| `https://docs.pearl.network` | `TLSV1_UNREGNIZED_NAME` (subdomain yok) |
| `https://github.com/pearl-network` | **404** (org bilinmiyor) |
| `r.jina.ai` proxy | **403 Forbidden** (ePrint'te olduğu gibi) |
| `mcp__weblocal__web_search` (DuckDuckGo) | `Connection reset by peer` |

**Sonuç:** Pearl'in iddia edilen 24 EH/s / ~320.000 GPU / ~$1,6M-gün gelirine sahip canlı
ağı için **resmi dokümantasyonu bağımsız olarak doğrulamak imkânsızdır.** Elimizdeki
kanıtlar: (1) KW makalesi "This blockchain is currently under construction", (2) Basu
2606.04819'ün **bağımsız ölçümü** (yukarıdaki tüm sayılar), (3) Pass 2606.06700'ün "Pearl
Research Labs" danışmanlığı atıfı.

**Bu bulgunun kendisi bir veri noktası:** 24 EH/s iddia eden bir ağın dokümanlarının
ulaşılamaması, projenin temel epistemik dersini özetler — **pazarlamayı değil, bağımsız
ölçümü esas almak.** KÖK v2'nin tüm Pearl rakamları Basu'nun üçüncü taraf ölçümünden gelir;
Pearl'in kendi dokümanlarından hiçbir iddia alınmamıştır (alınamazdı). Bu, `DEGERLENDIRME_100.md`
ve `PROJE_KAGIDI_V2.md`'deki her Pearl referansı için geçerlidir.

### 17.2 Çözüm: birincil kaynaktan çıkan kritik sonuçlar (tüm detay `PEARL_DOCS_ANALIZ.md`)

1. **KW construction birebir üretime uygulanmış** — §3.1.1 aynı E,F rank-r identity'si,
   transcript, per-tile BLAKE3 jackpot; **t ≤ r** koşulu Lemma 6.5'in pratik halidir.
   Üretim parametreleri: rank r ∈ {32..1024}, 16r ≤ k ≤ 4r², k ≤ 2^16, 64|k.
2. **Pearl = Bitcoin fork, UTXO, LİNEAR longest-chain, 194 sn blok — GHOSTDAG YOK.**
   KÖK v2'nin DAG'i gerçek bir farklılaşmadır (Pearl 194 sn'de kalır; KÖK ~10 BPS hedefler).
3. **Ekonomi:** S = 2.1×10^9, 1/t² polinomsal emisyon (halving yok), **R(t) → 0 — gerçek
   tail YOK** (Bitcoin'den yağlı ama yine sıfırlanan). Pass'ın 2606.06700'ünün,
   whitepaper §6.3'te "yakında gelecek" diye ilan edilen **resmi** ekonomi dokümanı
   olduğu doğrulandı — KÖK'ün pass_sim.py Pearl'in kendi varsayım zincirini çalıştırır.
4. **§7 Lansman benchmark'ı:** Pearl-certified Llama 3.3 70B, 4×H200'de Meta'nın
   orijinalinden **DAHA HIZLI** (17.206 vs 15.270 tok/s, PP=4; MMLU 0.8190 vs 0.8198) ve
   **806 TMADs/sn** faydalı iş üretir — madencilik quantization kütüphanesinin kendisi,
   coupling overhead'siz. **Bu Basu'nun "vLLM coupling %10–30 maliyetlidir" sonucunu
   raffine eder:** canlı ağda φ=0'nın sebebi overhead değil, **workflow hizalaması** —
   faydalı iş Pearl'in hosted inference işinde (pearlresearch.ai + Together AI endpoint'i)
   gerçekleşir, zincirin permissionless madencilerinde değil.
5. **★ Pearl'in kendi dağıtımı G/U ayrımıdır:** pearlresearch.ai bir **inference platformu
   şirketi**; zincir ayrı. Pearl'in whitepaper'ında escrow, bond, burn, anti-aggregation,
   VRF, fraud penceresi **YOK** — marketplace §1'de gelecek vizyon olarak işaretlenir.
   KÖK v2'nin U katmanı (Demirel'in geri-alamaz burn'u ile) bu vizyonun concrete halidir.
6. **KÖK'ün alacağı iki ders:** (a) **Plonky2 ZK ile input gizliliği** (KÖK spec'te yok);
   (b) **pouw_meta-style block identity** (ZK cert'ler random → malleable; nonce-tabanlı
   ID yanlış olur). Üretim parametre aralığı da spec'e alınmalı.

**Hala açık (kullanıcıdan istendi):** yeni whitepaper PDF'inin metni (ben PDF okuyamıyorum),
"Problems We Are Working On" listesinin yolu, FAQ cevapları (51% saldırı, PQ, PRL emisyonu),
`zk-pow/` ve `pearl-blake3/` repo README'leri.

---

## 18. İki açık noktanın kapanması (19 Eylül 2026, devam)

1. **arXiv 2606.05433 DOĞRULANDI** (önceki oturumda "yazar adı bilinmiyor" diye işaretlenmişti):
   **Peigné, Nguyen, Wang — "Zero knowledge verification for frontier AI training is
   possible"**, v2 2026-08-22, 44 sayfa. zkVM + native BF16/FP32 precompiles; gerçek FP
   doğrulaması (fixed-point değil); ~36 ay PoC, tek-haneli-% overhead. KÖK v2 §6 "yarın"
   yolunun resmi kaynağı; `KAYNAKLAR.md` md.15 ve `PROJE_KAGIDI_V2.md` §6 güncellendi.
   *Önemli:* makale fixed-point APPROXIMATION değil, GPU'nun yaptığı gerçek FP hesabını
   doğruladığını özellikle vurgular — KÖK'ün bugünkü 𝔽_q seçimi "henün olgunlaşmadı"
   konumunu korur, "yaklaşım yeterli" konumuna çekilmez.

2. **Pearl için Wayback Machine de BOŞ:** `archive.org/wayback/available` her iki alan için
   `archived_snapshots: {}` döndü; CDX wildcard (`url=pearl.*`) yalnızca 2004 tarihli ilgisiz
   bir `pearl/robots.txt` kaydı verdi. Yani Pearl Network'ün **arşivlenmiş hiçbir genel
   dokümanı yok** — canlı site de boş. Sonuç: Pearl hakkında bağımsız doğrulanabilir tek
   kaynak **Basu'nun ölçüm makalesi** olmaya devam ediyor. Kullanıcı kendi tarayıcısında
   deneyebilir (aşağıdaki istek listesi `PROJE_KAGIDI_V2.md` konuşmasında paylaşıldı).
