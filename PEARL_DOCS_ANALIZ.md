# Pearl Network — BİRİNCİL KAYNAK ANALİZİ (27 Nisan 2026 whitepaper'ı + canlı site)

**Tarih:** 19 Eylül 2026 · **Kaynak:** `https://pearlresearch.ai/research/int-whitepaper` (INT
whitepaper, HTML, tam metin okundu), `https://pearlresearch.ai/network`, `/research`,
`https://github.com/pearl-research-labs/pearl` (311 ★, 6.803 commit, public) ·
**Domain notu:** `pearl.network` artık GoDaddy park sayfası; `pearl.foundation` DNS ölü;
canlı alan `pearlresearch.ai` (Pearl Research Labs; NVIDIA Inception üyesi).

> Önceki `findings.md §17`'deki "Pearl dokümanlarına ulaşılamaz" kaydı **kapatıldı** —
> alan adı değişmişti. Bu doküman, 4 oturumluk arayışın sonucudur ve `KW_ANALIZ.md`'deki
> tüm çıkarımların **üretimdeki karşılığını** verir.

---

## 1. Pearl'in deployed protokolü = KW construction'ı birebilir

| KW (teori, arXiv 2504.09971) | Pearl INT whitepaper (üretim) | Durum |
|---|---|---|
| E, F rank-r gürültü; A·B = (A+E)(B+F) − (EB+AF+EF), O(n²r) | §3.1.1 aynı identity, aynı O(n²r) | **DOĞRULANDI** |
| Transcript: tüm (n/t)³ ara blok ürünleri | §3.1.2 aynı; "verifiable trace" | **DOĞRULANDI** |
| Lemma 6.5: bloklar marjinal üniform | §3.1.2: "**t ≤ r** olduğu sürece düşük-rank gürültü blok düzeyinde tam-rank gürültüye marjinal olarak eşlenir" | **DOĞRULANDI + pratik koşul** |
| Symmetric-identity kısayolu (A·B'den (A+E)(B+F) üretmek) | §3.1.1 bunu açıkça tanır → transcript zorunluğu ile kapatır | **DOĞRULANDI** (KW_ANALIZ §3.3 ile aynı) |
| Remark 2.1: per-tile hash | §3.1.3: M_{i,j} ∈ {0,1}^512; XOR + rotate-13 güncelleme; **BLAKE3(seed, M_{i,j}) < 2^{256−b}** ile tile "açılır" | **DOĞRULANDI** (Pearl'in jackpot'u) |

**Üretim parametreleri (§4.8):** m,n ≤ 2²⁴; **16r ≤ k ≤ 4r²** (güvenlik için), k ≤ 2¹⁶
(taşma), 64 | k; **rank r ∈ {2⁵ … 2¹⁰}** (32–1024); tile h·w ≥ 32 (entropy); k(h+w) ≤ 2²².
KÖK prototipimdeki oyuncak değerler (r=2, n=8) bunların çok altında — spec üretim
aralığını açıkça benimsemeli.

**Algoritma 4'ün tam detayı:** M = 16×int32; `M[ℓ mod 16] ← (M[ℓ mod 16] ⋘ 13) ⊕ XOR(C_blk)`;
koşul `BLAKE3(M, key=s_A) ≤ 2^{256−b}·r·t_m·t_n`; değişken/dikdörtgen tile boyutları
donanım optimizasyonu için serbest.

## 2. Pearl'in ZK + blok kimliği tasarımı (KÖK v2'ye alınacak iki ders)

- **§4.7:** Plonky2 (hash-based zkSNARK: hızlı, **post-quantum**, transparent setup); elle
  yazılmış AIR (derleyiciye göre verimli); **preprocessed columns** ile gürültü türetimi
  ZK'de değil düz metinde (Jolt karşılaştırması: 1.5×10⁶ cycle/sn prove vs 1.3×10¹¹ cycle/sn
  CPU); **3-katlı recursion → proof < 60 KB**. Açığa çıkan veri: r,k,t_m,t_n, şekiller (m,n),
  tile konumu (i,j), H_A, H_B, BLAKE3(M, key=s_A).
- **Gizlilik motifi:** sıra/sütun şeritleri tescilli veri içerebilir → **ZK yalnızca
  boyut ve gizlilik için değil, aynı zamanda input confidentiality içindir.**
  → **KÖK v2spec'e alınması gereken bir nokta:** KÖK'ün U-katmanı bugün input
  gizliliğini ele almıyor; Pearl'in Plonky2 yaklaşımı kopyalanabilir.
- **§5.1 Malleabilite sorunu ve çözümü:** ZK cert'ler **rastgele** — bir witness'tan
  "ekstra iş olmadan" sonsuz geçerli proof türetilebilir. Pearl: **cert = geçerlilik
  kanıtı, block ID ≠ cert**; ID = 116-byte header'ın double-SHA-256'sı, içinde `pouw_meta`
  (PoUW witness'ına 32-byte SHA-256 commitment). Cert'ler_degisebilir ama block kimliği
  sabit. → **KÖK v2 için kritik uyarı:** prototipimde `S("blk", ctx, nonce, roots, fees)`
  nonce-tabanlı; KÖK ZK cert'lere geçince Pearl'in pouw_meta modelini benimsemeli
  (TV-1 replay testi bu boşluğu zaten doğru kapatıyor, ama spec'e yazılmalı).
- **Adres/VM:** yalnızca Taproot (legacy yok); **OP_CHECKXMSSSIG (#222)** XMSS/SHAKE256
  (~256-bit, 2340-byte imza, **consensus'ta şu an DEVRE DIŞI, rezerve**); P2MR (BIP-360);
  OP_CAT (520-byte cap, ⌈len/64⌉ maliyet).
- **Zorluk: WTEMA** — `target_new = target_old(1 + (t−T)/(N·T))`, N=2016, T=194 sn,
  τ = 7 gün; başlangıç nbits=0x1b00ffff (bilinçli düşük); timestamp kuralları
  (monoton ≥1 sn, future-limit 5 dk vs Bitcoin 120 dk); **tie-breaking: iş farkı
  min(w₁,w₂)/4'ten küçükse önce gelen tip** (backdate teşvikini kırar).

## 3. Ekonomi: Pearl'in "econ-101" modeli = Pass'ın öncülü

- **§5.4:** toplam arz **S = 2.1×10⁹** coin; en küçük birim 10⁻⁸ ("grain"); blok **194 sn**
  (3:14); emisyon **polinomsal 1/t² çürüme**: R(t) = H/(t+H), A(t) = t/(t+H),
  **H = 650.226 blok ≈ 4 yıl** (R(H)=½); per-blok E*(t) = SH/((t+H)(t+H−1)), grain cinsinden
  floor. **Halving yok** (süreklilik seçimi); **ama R(t) → 0** — yani gerçek bir tail
  **yok** (Bitcoin'in eksponansiyelinden çok daha yağlı: 9. yılda kalan ≈ 1/10, ama yine
  sıfıra gider).
- **§6:** C = $1.7/H100-sa (faydasız iş), τ = 0.1 (faydalı işin overhead maliyeti);
  anlık denge **τ·G(t)·D(t) = p(t)·e(t)**; e(0) = 59.931 token/saat; doygunluk grafiği
  (1M faydalı + 2M faydasız GPU, 2.84 / 28.4 doygunluk noktaları); **"future expectations
  multiplier" F = p·e/(τ·G·D) > 1**; §6.4 appreciation ρ_p = ρ_G·ρ_D/ρ_e,
  ρ_e = ((H+t₂)/(H+t₁))² → 1. yılda ≈1.56×, 10. yılda ≈1.07×; "token, dünya faydalı
  hesaplama maliyetine endekslidir (ve biraz fazlası)".
- **§6.3'ün itirafı:** "token fiyatı τ=0 olursa 0 olur... tam genel-denge modeli
  (**yakında gelecek**) AI fiyatını endojen değişken olarak modeller" — **bu "yakında
  gelecek" belge Pass'ın arXiv 2606.06700'ü** (Pearl'in /research sayfasında "The Economics
  of Proof-of-Useful-Work — Read on arXiv" olarak listeleniyor). Yani Pass modeli Pearl'in
  **resmi** ekonomi dokümanıdır; KÖK'ün `pass_sim.py` Pearl'in kendi varsayım zincirini
  çalıştırır.
- **Rebey mekanizması:** madenciler AI maliyetinde indirim yapmak zorunda (τ→0'da bile
  τ>0 kalır, hatta büyür) — Pass'ın Duplexia'sındaki `p = αe/(1+θ) < e` ile aynı sonuç.

## 4. §7 Lansman: "2-for-1" sayılarla (Pearl'in kendi benchmark'ı)

27 Nisan'da node public + chain live + **vLLM plugin** (quantization = PoW) +
**Pearl-certified Llama 3.3 70B**. 4×H200, MMLU + throughput:

| Model | Paralellik | MMLU | tok/sn | Süre (sn) | Faydalı MADs (TMADs/sn) |
|---|---|---|---|---|---|
| Meta LLaMA 70B | PP=4 | 0.8198 | 15.269,81 | 441,100 | — |
| Meta LLaMA 70B | TP=4 | 0.8193 | 13.218 | 510 | — |
| Meta LLaMA 70B | DP=2,TP=2 | 0.8197 | 13.162 | 512 | — |
| **Pearl-certified** | **PP=4** | 0.8190 | **17.206,26** | **391,457** | **806** |
| **Pearl-certified** | **TP=4** | 0.8180 | 13.264,38 | 507,789 | **620** |
| **Pearl-certified** | **DP=4** | 0.8198 | **18.291,66** | **368,229** | **981** |

**Sonuç:** Pearl-certified varyant Meta'nın orijinalinden **DAHA HIZLI** (PP=4: +12,7%;
DP=4: +20% vs DP=2,TP=2) ve ihmal edilebilir MMLU kaybıyla (0.8190 vs 0.8198)
**806–981 TMADs/sn faydalı madencilik** üretir. Sebebi: madencilik **quantization
kütüphanesinin kendisi** — ek yük değil, yerine geçen uygulama.

**Bu, Basu'nun ölçümünü RAFFİNE eder (önemli):** Basu "vLLM coupling hashrate'in %10–30'unu
götürür → madenciler inference'ı atlar" dedi. Pearl'in kendi verisi coupling'in **sıfır veya
negatif maliyetli** olabildiğini gösteriyor. O halde canlı ağda φ=0 ölçülmesinin sebebi
**overhead değil, workflow hizalaması**: certified yol belirli modelleri plugin ile çalıştırmayı
gerektirir; permissionless madencinin ekonomik optimumu raw filler'dır. **Faydalı iş Pearl'in
kendi hosted inference işinde (pearlresearch.ai + Together AI endpoint) gerçekleşir;
zincirin madencilerinde değil.**

## 5. ★ En önemli analitik sonuç: Pearl'in kendi dağıtımı G/U ayrımıdır

Pearl'in 2026'daki gerçek yapısı:

- **pearlresearch.ai = bir inference platformu şirketi**: OpenAI-uyumlu API, serverless /
  managed / on-prem inference, DeepSeek-V4, Qwen3.8, GLM-5.3, Gemma-4; Together AI'da
  **Gemma-4-31B-it-Pearl** endpoint'i (**%25+ ucuz, "aynı forward pass'ta kazınan PRL ile
  finanse edilen"**); Hawkeye (MLSys 2026), Hadamard quantization kernel, **GPU BLAKE3
  (400×)** araştırma makaleleri.
- **Pearl Protocol (chain) = PoUW L1**, Bitcoin fork, UTXO, **linear longest-chain**
  (GHOSTDAG **yok**), 194 sn blok, WTEMA, Plonky2 ZK, XMSS rezerve.
- **Whitepaper'ın pazarladığı 2-for-1 = yazılım kapasitesi**, zincirin garantili ekonomik
  bağı değil. Pearl'in iş modeli fiilen: **inference işi (U) + madencilik zinciri (G)**.

**KÖK v2'nin G/U ayrımı Pearl'in vardığı yeri açık ve dürüst hale getirir:** Pearl
"marketplace"'i §1'de **gelecek vizyon** olarak işaretler ("In the future, one can even
envision native (on-chain) settlement of compute contracts") ama **escrow, bond, burn,
anti-aggregation, VRF ataması, fraud penceresi — hiçbiri yok.** KÖK v2'nin U katmanı
Demirel'in geri-alamaz burn'u ile bu vizyonun **concrete** halidir.

## 6. KÖK v2 vs Pearl — dürüst farklılaşma tablosu (birincil kaynaktan)

| Boyut | Pearl (birincil kaynak) | KÖK v2 | Kazanan / dürüst not |
|---|---|---|---|
| Kriptografi | KW + Plonky2 ZK, üretim parametreleri ile | KW + G katmanı (TV-1..4 doğrulandı) | **Eşit** (aynı çekirdek) |
| Input gizliliği | **Plonky2 ZK ile A,B korunur** | spec'te yok | **Pearl** — KÖK almalı |
| Block identity | pouw_meta binding (ZK random malleability çözümü) | nonce-tabanlı (prototype) | **Pearl** — KÖK ZK'ya geçince almalı |
| DAG | **yok** (linear, longest-chain, 194 sn) | GHOSTDAG, ~10 BPS hedefi | **KÖK** (paralellik gerçek farklılık; Pearl 194 sn'de kalır) |
| Eğri | 1/t² polinomsal, R→0 (halving yok, yağlı ama sıfırlanan) | tail emission **R_∞ tabanı** | **KÖK** (sonsuz ufukta güvenlik sıfıra düşmez) |
| Zorluk | WTEMA (per-block EMA, 7-gün decay) | pencere + medyan filtre (RT-1..3 doğrulandı) | **Eşit** (iki geçerli okul; WTEMA daha sade) |
| PQ | XMSS **rezerve/devre dışı**, Taproot-only, P2MR | **PQ seti zorunlu** (TV-10) | **KÖK** (sert kapı); Pearl'in gradualizmi de savunulabilir |
| Fayda mekanizması | 2-for-1 = **yazılım kapasitesi**; hosted inference işi ayrı | **U katmanı: escrow + bond + burn + C_FEE + VRF** | **KÖK** (Pearl'in vizyonu concrete) |
| Talep → güvenlik | **bağ kurulmamış** (E-gap görmezden gelinmiş) | G talepten bağımsız + burn güvenlik kaynağı | **KÖK** (Demirel Thm 2 mimaride) |
| Kanıt | 24 EH/s canlı; kendi benchmark'ı +3,2 sn (391 vs 441 sn) | prototype (TV-1..10, RT-1..3, pass_sim) | **Pearl** (KÖK testnet'i bekliyor) |

## 7. KÖK v2 spec'ine alınacak somut maddeler (öncelik sırası)

1. **Üretim parametre aralığı** (§4.8): rank r ∈ {32..1024}, 16r ≤ k ≤ 4r², k ≤ 2¹⁶,
   64 | k, h·w ≥ 32, k(h+w) ≤ 2²² — spec Ek B/A.0'a.
2. **pouw_meta-style block identity** — ZK cert'lerin random malleability'sine karşı
   (TV-1 zaten doğru kapatıyor; spec'e yaz).
3. **Input confidentiality**: Plonky2-benzeri hash-based ZK ile A,B koruması (KÖK §7
   crypto-agility düzlemine oturur; Pearl'in öncülü).
4. **WTEMA alternatifi** Ek B'ye dürüst alternatif olarak ekle (Pearl'in tercih ettiği,
   per-block EMA; KÖK pencere+medyan'da ısrar etmeli mi yoksa WTEMA'ya mı geçmeli —
   karar verme gerekçesini yaz).
5. **Pearl'in lansman verisi KÖK'ün V2 §8 ekonomisini güçlendirir**: Pearl kendi
   benchmark'ında +12,7% throughput ile 2-for-1'in **teknik** olarak mümkün olduğunu
   kanıtlar; KÖK'ün iddiası bunu **ekonomik olarak bağlama** (burn + fee pazarı).

## 8. Hala doğrulanmamış (kullanıcıdan istenecek)

- **Yeni whitepaper (PDF)**: `/research/whitepaper` sayfası "Download PDF" verir ama link
  stripped; PDF'leri ben okuyamıyorum. **Kullanıcı PDF'in metnini paste ederse** yeni FP
  PoUW şemasının (§1.1: quantization noise'u PoW perturbasyonu olarak kullanma + pre-
  quantization weight'lerine commitment) detayları alınır.
- **"Problems We Are Working On" listesi**: `/network` ve `/research`'te link var ama
  yolunu bulamadım (404'ler). Açık problem listesi (matematik/kriptografi/konsensüs)
- **FAQ cevapları** (`/network`'te accordion arkasında): "Doesn't useful work make a 51%
  attack cheaper?", "Is Pearl post-quantum?", "How is PRL issued?" — benim için 51% ve
  emisyon soruları öncelikli.
- **Repo derinliği**: `zk-pow/`, `pearl-blake3/`, `py-pearl-mining/` dizinlerinin README'leri.

---

## 9. Repo + iki gerçek hard fork (19 Eylül 2026, devam — ben kendim aldım)

**`github.com/pearl-research-labs/pearl`** (311 ★, 6.803 commit, ISC). README'lerini
raw.githubusercontent.com üzerinden okudum:

- **`miner/`** — **"Currently only mining via vLLM is supported"** (gelecek: SGLang,
  TensorRT-LLM, Ollama). `pearl-gemm/` = CUDA kernel'leri (**NoisyGEMM**, noising/
  denoising, PoW extraction, NVIDIA **CUTLASS**); `vllm-miner/` = "vLLM plugin that
  **replaces quantized linear ops with NoisyGEMM**"; `pearl-gateway/` = node↔miner
  köprüsü (work distribution, block submission, JSON-RPC). Yalnızca **sm90 (H100/H200)**.
  Resmi model: `pearl-ai/Llama-3.3-70B-Instruct-pearl`.
- **`node/` (pearld)** — Go 1.26+ + Rust (ZK doğrulama) + C (XMSS); "includes
  zero-knowledge proof-of-work verification and **XMSS post-quantum signature
  support**"; **Oyster wallet**; simnet integration testleri.
- **`py-pearl-mining/`** — PlainProof → **gateway ZK'ya çevirir** → node. Wire format:
  `ZKCertificate | PearlHeader | TX_COUNT | TRANSACTIONS`.
- **`zk-pow/`** (Rust crate) — README stub; ama fork rehberlerinden `zk_pow::v1::api`
  + `zk_pow::api` (V2/V3) çift devre yapısı okunuyor.

**★ Basu ölçümünün kesinleşmiş açıklaması:** resmi referans madenci **vLLM-zorunlu**
(faydalı iş üretir); Basu'nun ölçtüğü 8.012 worker **"alpha-miner"** = resmi olmayan,
inference'siz topluluk yoluydu. Yani **kapasite resmi yazılımda var, ekonominin
ittiği yer resmi olmayana.** E-gap teknik bir eksiklik değil, **dağıtım ekonomisinin
sonucu**: hashrate'in çoğu kısa yolu seçti. KÖK v2'nin cevabı: kısa yolu **pahalı**
yapmak (U katmanı fee + burn) değil, **faydalı yolun kendisini tek geçerli yol
yapmamak** — zaten öyle (G katmanı serbest); KÖK'ün farkı faydanın **fiyatlandığı**
bir pazar kurması.

### 9.1 MoE hard fork (V1→V2): dense → MoE sertifikası

- Fork height tablosu **TBD** kalmış ama bir sonraki rehber V2'den V3'e geçtiğü için
  **gerçekleşmiş**: zincir canlıda **bir kez** MatMul yapısını değiştirdi (dense →
  Mixture-of-Experts / grouped GEMM).
- **Geriye uyumlu:** "Your hashing miners do not need to change. Old dense proofs work
  before and after the fork." V2 prover **hem dense hem MoE** plain proof kabul eder.
- **Sadece node + ZK proving kodu** fork öncesi upgrade zorunlu.
- Node v1.1.0; `getblocktemplate` artık `requiredcertversion` döner (1/2). "Read the
  version from the template. **Do not hardcode the fork height** in your pool."
- Wire format değişti: V1 `PublicData(164)` sabit → V2 `PublicDataLen(4)|PublicData(N)`
  değişken. **Proof commitment = `double_sha256(cert_version_le32 + public_data)`** —
  versiyon-önekli bağlama (KÖK'ün pouw_meta modelinin üretim hali).
- Rust: çift circuit cache (V1 ve V2 ayrı), `zk_pow::ffi::plain_proof` ile
  `deserialize_compat` (eski+yeni format).

### 9.2 Salted-seed hard fork (V2→V3) — mainnet blok 99.000

- **Fork height'ları YAYINLANMIŞ:** Mainnet **99000**, Testnet **38648**, Testnet2
  **83109**. (Yani zincirde 99K+ blok var → ~227 gün @ 194 sn ≈ Nisan lansmanı ile
  tutarlı.)
- **V3 = gürültü seed türetmesi matris boyutlarına bağlanır** (grinding/bağlama
  saldırısına karşı):
  ```
  bound_a = blake3(hash_a || m_le32 || 0^28, key = blake3("pearl/cert-v3/noise-seed/A"))
  bound_b = blake3(hash_b || n_le32 || 0^28, key = blake3("pearl/cert-v3/noise-seed/B"))
  b_noise_seed = blake3(job_key || bound_b)
  a_noise_seed = blake3(b_noise_seed || bound_a)
  ```
  MoE: `hash_activations = blake3(bound_a || hash_routing)`; n = **per-expert** boyut.
- **Geriye uyumlu DEĞİL:** "everything must be upgraded: node, ZK proving code, and
  miners" — çünkü seed türetmesi madenciliğin kendisini besler. MoE fork'undan farkı
  tam olarak bu.
- Node v1.4.1, pearl-mining v0.3.1; `cert_version` artık `submitPlainProof`'un
  **zorunlu alanı**; pinned test vector'leri `zk-pow/src/api/seed.rs`'te.

### 9.3 KÖK v2'ye doğrudan alınacaklar (öncelik sırasıyla)

1. **Versiyon-önekli commitment** `double_sha256(cert_version_le32 + public_data)` —
   KÖK'ün ctx-binding'ine (T-A2) **üretim kanıtı**: Pearl de bağlamayı iki fork'ta
   arka arkaya güçlendirmek zorunda kaldı. KÖK spec §A.3'e `proof_system_id`
   prefix modelini yaz.
2. **`requiredcertversion`-tarzı şablon alanı** + "fork height'ı hardcode etme"
   kuralı — KÖK'ün §7 agility düzleminin canlı öncülü: **node yayınlar, madenci okur**.
3. **Geriye uyumluluk matrisi** (MoE gibi "eski madenci çalışmaya devam eder" vs
   salted-seed gibi "herkes upgrade etmeli") — KÖK'ün §7 migration katmanları A–D
   için gerçek bir sınıflandırma: **türetme madenciliği beslemiyorsa** uyumlu,
   besliyorsa zorunlu. Bu, spec'te bir tablo olmalı.
4. **MoE = gerçek "faydalı iş" genişlemesi**: Pearl madencilik yapısını değiştirerek
   (dense → MoE) fayda alanını genişletti; KÖK'ün U katmanı **görev-odayaklı** olduğu
   için bu tür bir fork'a ihtiyaç duymaz (yeni harness = yeni görev tipi, fork değil).

## 10. Hala kullanıcıdan (benim alamadıklarım — net liste)

1. **Yeni whitepaper PDF'inin metni** (`pearlresearch.ai/research/whitepaper`) —
   ben PDF okuyamam; FP PoUW şeması (quantization noise = PoW perturbasyonu).
2. ~~**FAQ cevapları**~~ — **ÇÖZÜLDÜ (20 Eylül 2026), bkz. §12** (`agent-browser`
   ile JS-rendered accordion'lar okundu; eski fetcher HTML'yi strip ediyordu).
3. **"Problems We Are Working On"** listesi — linki `/network` ve `/research`'te
   "Open the List" olarak var ama URL'yi göremiyorum (href'ler stripped);
   `/open-problems`, `/problems`, `/research/problems`, `/network/open-problems`
   **hepsi 404**. Bağlantının gerçek adresi gerek. **(Kısmen çözüldü: Polymath
   `pearlpolymath.com` üzerinden 7+2 problem okundu, bkz. §11.2; orijinal liste
   sayfası hâlâ bulunamadı.)**

---

## 11. ★ FP8 whitepaper'ı + Polymath açık problem listesi (20 Eylül 2026, PDF'lerden)

Kullanıcı üç PDF getirdi; **üçü de birincil kaynak ve üçü de yeni bilgi**:

### 11.1 "Pearl Floating Point Scheme Specification" (Eylül 2026) — FP8 şeması

**KÖK v2 §6'yı doğrudan etkileyen yeni paradigm:** KW'nin INT şemasında düşük-rank gürültü
çıktı kısayolu yaratır (**A=B=0 için C̃ = Q(E)Q(F)ᵀ** = ucuz), bu yüzden zorluk
*transcript*'e dayanır (tüm (n/r)³ ara bloklar hashlenir). **FP şemasında entrywise
quantization nonlineer** — `Q(A+N) ≠ Q(A)+Q(N)` — düşük-rank yapıyı bozar, **böylece
ticket'lar doğrudan ÇIKTI tile'larını hashler; transcript gerekmez.**

- **Assumption 1 (quantized-subspace hardness):** "For every admissible k, there is an r ≪ k
  ... With high probability over random r-dimensional subspaces U_A, U_B ⊂ R^k ... computing
  Q(N_A)Q(N_B)ᵀ is not substantially easier than computing Q(A)Q(B)ᵀ" — KW'nin
  transcript-unpredictability varsayımının **FP analoğu** olarak konumlandırılır. **r = 32
  for k ≤ 2¹⁶.**
- **Doğrulama = Hawkeye ile bit-exact replay** [5]: "the verifier recovers the bit-exact
  computation using the technique of Badash et al." — **Hawkeye'nin yazarları: Badash,
  Boneh, Komargodski, Srivastava** — yani **KW'nin yazarı Komargodski aynı zamanda Hawkeye'nin
  yazarı.** Bu iki çizgi (PoUW + GPU determinizmi) kasıtlı olarak birleştirilmiş.
- **§5 Jackpot policy = KÖK'ün aradığı "prescribed hardness"ın üretim versiyonu**, altı
  somut kontrolle:
  1. **Entry liveness** (τ_idle=8, ε_idle=1/64): gürültüden τ_idle kat büyük entry'lerin
     oranı ε_idle'i geçemez (noise-dwarfing saldırısı).
  2. **Noise floor** (σ_min=1): her satır en az 1 quantized unit gürültü taşımak zorunda —
     **"azaltılmış alfabeli özel devre genel FP8 kernel'inden hızlı olur"** düşük lokal
     entropi saldırısını kapatır (KÖK'ün §6'sındaki "özel donanım" endişesinin üretimdeki
     cevabı).
  3. **Tamed products** (τ_tame=256, ε_tame=1/64): uyumlu (coherent) dot product'lerin oranı
     sınırı — M_ij'nin √k·σσ'yı aşması.
  4. **Unpredictable summands** (ε_pred=1/16): "precision shortcut" — yuvarlanacak
     summand'ı atlayıp MAC tasarrufu yapma saldırısının sınırı (FP'ye özgü, INT şemada yok).
- **§5.2 Attack vectors:** NaN/Inf (degenerate arithmetic — yasak), **noise seed grinding**
  (k ≥ 1024, |I_B| ≥ 16, SampleLine ~150 bit min-entropy; "|I_B|/(|I_B|−1) < 1.1 speedup
  acceptable"), no-noise entries, low local entropy, coherent dot products, **low-rank
  planting** (A,B düşük rank → S^A,S^B düşük rank → pahalı tek parça T·T).
- **§7 Known mining speedups (5 sınıf):** input crafting, precision shortcuts, seed/commitment
  grinding (Fiat–Shamir argümanı), **work reuse** (chaining/amortization — "succeed only if
  revealing a noised tile makes the clean tile's ticket cheaper to predict"), better kernels
  (**"not an attack ... the work model charges everyone in the same units"** — KÖK'ün §5
  oyun-teorisiyle birebir).
- **MoE extension (Appendix A):** routing conceptually left operand'ın parçası; e ≤ 1024,
  e|n; expert matmul'lar stacked B'ye tek commit; **noise globally canonical** — miner A'yı
  bir kez noiselar, expert'ler arası yeniden kullanır.
- **ZK verifier (Appendix B):** outer verifier + circuit **split verification** ("bind the
  statement" H_pub, split verification); **witness = A_{I_A}, B_{I_B} + minimal openings**;
  jackpot-policy intermediates private. **σ_d blockchain context'e bağlı** (KÖK'ün ctx
  binding modeliyle aynı).

**KÖK v2 için sonuçlar:** (1) **§6'yı güncelle**: FP doğrulama için iki yol var —
Peigné'nin native-FP zkVM'i (~36 ay) **ve** Pearl/Hawkeye **bit-exact replay** (üretimde,
MLSys 2026). İkincisi bugün çalışıyor; whitelist GPU + deterministik accumulation order.
(2) Jackpot policy'nin dört kontrolü KÖK'ün G katmanı için bir **reçete**: entry-liveness /
noise-floor / tamed-products / unpredictable-summands — bunlar `g_layer_tests.py`'ye
TV-11..TV-14 olarak eklenebilir (şu anki TV-2 sadece kurtosis ölçüyor; Pearl'in dört
kontrolü çok daha güçlü). (3) **Transcript'ten output-tile hash'e geçiş** KÖK v2'nin G
katmanında da düşünülmesi gereken bir basitleştirme — ama **sadece nonlineer quantization
varsa** çalışır; KÖK'ün şu anki INT/sabit-nokta kerneli transcript'e bağlı kalmalı.

### 11.2 ★★ Pearl'in KENDİ E-gap itirafı — "Pearl Polymath Project" (açık problem listesi)

`pearlpolymath.com` — "a shortlist of difficult open problems we've encountered while trying
to create the first Proof-of-Work network secured by native AI computations". **7 matematik +
2 ekonomik problem.** En önemlisi **Ekonomik Problem (1)**:

> "A common criticism of (0-overhead) PoUW is that the **marginal cost of mining is ~0 and
> hence also the cost of attacking the network**. However, the last statement is only true if
> one has an **infinite stream of useful work**—i.e., the ability to collect AI workloads for
> which an external consumer is willing to pay. This observation highlights the difference
> between Pearl and Bitcoin—**the key 'scarce' resource in PoUW mining is the ability to
> collect useful data (matrices)**. At ~0 overhead, every AI workload on earth should in
> theory opt-in to mine Pearl (free option call) in which case the hashrate (and hence
> distribution/entropy) are also maximized. **What should be the value/price of the Pearl coin
> at 0 mining overhead? Is it 0? infinity?**"

**Bu, projemin tezinin birincil kaynakla doğrulanmasıdır.** Pearl E-gap'in farkında ve
cevabı **ekonomik**: "scare resource = faydalı veri toplamak". Ama bu, **talep
depresyonundayken korumaz** — Basu'nun ölçtüğü φ=0 dünyada (faydalı iş yatırılmıyor),
Pearl'in savunması çöker: eğer kimse matris göndermezse "scare resource" ucuzlar ve saldırı
maliyeti düşer. **KÖK v2'nin cevabı protokol-seviyesindedir** (Demirel: geri-alamaz burn =
güvenlik bütçesi, talepten bağımsız). İki cevap arasındaki fark KÖK'ün "novel" iddiasının
özü: **Pearl pazarın merhametine, KÖK kriptografiye güvenir.** V2 §12'ye bu kesin alıntıyla
eklenmeli.

**Diğer önemli problemler (KÖK ile çakışanlar):**
- **(1) Self-cancelling noise / random rotation:** KW Appendix A'nın şeması — (A·S)·(S⁻¹·B),
  randomized Hadamard, **O(n² log n) overhead**, noise peeling yok. **Conjecture A.1** (KW
  PDF'inden doğrulandı): "requires Ω(r³) time ... in the word-RAM model" — **Pearl hâlâ
  "Is this PoW rotation-scheme secure?" diye soruyor** (KÖK'ün KW risk değerlendirmesiyle
  uyumlu: conjecture'lar kanıtlanmamış).
- **(2) Pearl-GEMM:** "Find a noise distribution that is both secure and results in
  negligible end-to-end accuracy loss in LLM inference (e.g., in MMLU)" — FP whitepaper'ı
  bunun cevabı (Assumption 1 + 4 kontrol); **MMLU kaybı ölçüt olarak Pearl'in seçimi**
  (KÖK §6'nın hata bütçesi yaklaşımıyla aynı, ama Pearl üretime aldı).
- **(3) FP4:** NVFP4, scale γ'lerin optimizasyon boyutu olarak kullanılması.
- **(4) Training/finetuning:** "cuPOW only for inference ... commitment hashing can be done
  in preprocessing time"; **SGD robustness conjecture** ("training is very sensitive to
  numerical precision, likely due to enormous curvature of the loss function"); "develop
  numerical scaling laws for finetuning" — KÖK'ün U katmanı için doğrudan bir görev
  alanı: **training şu anda Pearl'de YOK, KÖK bunu görev-pazarında sunabilir.**
- **(5) MatMul-based hash:** "GPU-compatible cryptographic hash, 128-bit collision-resistant,
  not a SoTA hash on CPUs (BLAKE3, 13.1 int32 ops/input byte)? Base it on matrix
  multiplications and harness TensorCores?" — KÖK için açık araştırma sorusu.
- **(6) ASIC-resistance:** Pearl'in iddiası **"not a technical statement, but rather an
  economic one"** — noisy all-zero çarpan ASIC yapılabilir ama "unlikely that such hardware
  will be able to run real AI workloads"; "**Is 1-bit hardware enough to implement
  Pearl-GEMM(A=0,B=0)? How much speedup would such hardware provide, compared to GEMM on
  H100?**" — **Pearl kendi ASIC endişesini açıkça sorun olarak listeliyor.** KÖK v2 §11
  ASIC-riski için bu birincil kanıt: rakip henüz bu sorunu çözmedi.
- **(7) 0%-overhead proof-of-inference:** model ağırlıklarına ±1 gürültü ekle, LLM'(x')
  çalıştır; **"may be vulnerable to backdoors of computing the model faster"**; "doesn't
  have an efficient SNARK ... challenge: provide an efficient SNARK for the whole LLM
  computation". **Break-the-scheme daveti** — KÖK'ün U katmanı (görev-bağlı, fee-gated) bu
  saldırı yüzünden tüm-model PoI yerine **per-layer MatMul**'da kalmayı seçmiştir; Pearl'in
  kendi itirafı bu tasarımın nedenini destekler.
- **Ekonomik (2) Utilities:** AI ajanları için oylama sistemi, retroaktif inference ispatı
  (ZK), **"compute için stablecoin"** — KÖK §9 "yardımcı fayda" listesiyle örtüşme;
  KÖK'ün escrow+pazarı bu uygulamaların altyapısı olabilir (Pearl'de protokol-seviyesinde
  yok).

### 11.3 JS chunk'ları — işe yaramadı (dürüst kayıt)

Kullanıcının getirdiği 5 JS + 1 CSS dosyası Next.js **framework vendor kodu** (webpack,
polyfills, app-router); içinde FAQ metni yok. Boyut farkları hash farkından (ratio 0.007).
**FAQ cevapları hâlâ eksik** — accordion içeriği ancak tarayıcıda JS çalışınca oluşuyor.

### 11.4 Yazar listesi düzeltmesi (KW)

Hem **arXiv 2504.09971v4 PDF'i** hem **ePrint 2025/685 sayfası** hem de yeni Pearl
whitepaper'ı [4] **iki yazar** listeler: **Ilan Komargodski, Omri Weinstein**. Önceki
oturumlardaki "Schen" üçüncü-yazar notu **yanlıştı**; 5 dosyada düzeltildi. (Schen adında
bir yazar bu makalede yok; muhtemelen başka bir ePrint ile karıştırdım.)

## 12. ★ FAQ CEVAPLARI — agent-browser ile çözüldü (20 Eylül 2026)

> **Yöntem notu (önemli):** eski `web_fetch` HTML'yi strip ettiği için FAQ cevapları
> görünmüyordu (§10 md.2). `agent-browser` (Chrome/CDP + accessibility-tree) ile
> `/network` sayfasındaki 8 accordion sorusu **gerçek tarayıcıda** açılıp okundu.
> **İlk defa birincil kaynak:** Pearl'in kendi kelimeleriyle üç kritik cevap.

### 12.1 "Doesn't useful work make a 51% attack cheaper?" — Pearl'in cevabı (birebir)

> "This is the oldest objection to useful work: if the output has value, an attacker
> sells it, recovers the cost, and attacks for free. It sounds right, and it is wrong.
> In a competitive inference market, paying miners in PRL drives the price of inference
> down by exactly the block reward, so buying a single vote still costs the full
> reward, precisely what it costs to attack Bitcoin. **Rafael Pass formalized this in
> The Economics of Proof-of-Useful-Work: under realistic conditions, Pearl is at least
> as expensive to attack as a hash-only chain.**"

**★★★ ÖNCE BİR ÇIKAR-ÇATIŞMASI UYARISI (20 Eylül 2026, PDF'ten bulundu):**
> Pass_full.txt satır 41: *"Pearl Research Labs. Rafael Pass is also a faculty member at
> Cornell Tech and Technion... **This work was done while consulting for Pearl Research
> Labs.**"* — yani **Pass makalesi Pearl'in DANISMANININ makalesi**. Makalede **hiçbir
> çıkar-çatışması beyanı yok** (grep "conflict"/"disclosure" boş döndü).

**Bu ne demek?** Pearl'in FAQ'taki "Pearl is at least as expensive to attack as a
hash-only chain" iddiasının **formal dayanağı, Pearl'in kendi danışmanının teoremidir**.
Bu teoremin **yanlış olduğu anlamına gelmez** — bizim `pass_sim.py` de Thm 2'yi
doğruluyor ve Pearl'in canlı ağını %5,8 içinde yeniden üretiyor. Ama **PEARL'IN
BAĞIMSIZ KANITI olduğu anlamına gelmez.** Pearl'in FAQ'undaki "It sounds right, and it
is wrong" tonu, okuyucuya "üçüncü taraf doğruladı" izlenimi verir — oysa **içeriden
doğrulama**dir. **KÖK v2'nin kendi iddialarını dışarıdan doğrulatma zorunluluğunun
(2 bağımsız kriptograf) nedeni tam olarak budur: aynı standart kendimize de uygulanır.**

**★ KÖK v2 ile ilişkisi — ÇAKIŞMA YOK, teyit var:**
- Pearl'in argümanı **Pass Theorem 2**'ye dayanıyor (Cost₅₀% = PR/2 her rejimde).
  `pass_sim.py` bu teoremi **kapalı-form olarak çözüp çalıştırdı** ve Pearl'in canlı
  ağında %5,8 sapma ile yeniden üretti. Yani Pearl'in FAQ'taki iddiası, **bizim
  simülasyonumuzun modellediği şeyin birebir aynısı**.
- **Ancak KÖK v2'nin itirazı farklı yerde:** Pass Thm 2'nin koşulu
  "in any competitive equilibrium" — yani **talep esnekliği (Jevons, ε=2)** önkoşul.
  Pearl'in φ=0 durumu (Basu: sıfır faydalı hesap) bu önkoşulu **zayıflatır**:
  faydalı çıktı satılamıyorsa "attacker sells it, recovers the cost" tersine döner.
  Pearl'in cevabı bu senaryoyu **ele almıyor** — "It sounds right, and it is wrong"
  diyor ama φ=0'da neden hâlâ doğru olduğunu açıklamıyor.
- **KÖK v2'nin yolu:** G katmanı Demirel Thm 2'yi **construction-level** karşılar
  (talep sıfır olsa da pure-PoW filler ile yaşar — TV-4/TV-8 + sim §6: S→PR/e).
  Yani KÖK v2, Pearl'in argümanının **başarısız olduğu yerde** (φ=0) bile güvenliği
  talepten bağımsız kılar. **Bu, §12 farklılaşma tablosunun tezidir ve şimdi
  Pearl'in kendi FAQ'undan teyit edilmiş halidir.**

### 12.2 "Is Pearl post-quantum?" — Pearl'in cevabı (birebir)

> "Yes. Proof of useful work is hash-based, BLAKE3 commitments verified by a Plonky2
> zkSNARK, so a quantum adversary cannot break mining the way they can break
> elliptic-curve cryptography. Funds can be fully post-quantum too: **Pay-to-Merkle-Root
> (P2MR) addresses have no Schnorr key-path, and OP_CHECKXMSSSIG verifies XMSS**, a
> hash-based signature already in consensus. Together they give addresses and spends
> that do not rely on discrete log."

**★ KÖK v2 ile ilişkisi — KRİTİK FARK:**
- Pearl'de **XMSS consensus'ta "already in consensus"** diyor — ama §5.2 analizimizde
  (INT whitepaper) **OP_CHECKXMSSSIG rezerve-edilmiş ama etkin değil** olarak
  bulmuştuk; Taproot-only. Yani FAQ "already in consensus" ile whitepaper'ın
  "reserved-but-disabled" ifadesi **arasında gerilim var**. (Diplomatik okuma:
  opcode konsensüste tanımlı, ama henüz zorunlu/varsayılan değil.)
- **KÖK v2'nin farklılaşması:** PQ'yu **opsiyon değil, zorunlu gate** yapar (V2 §7
  katman C + §10 F2: imzalar ZK-ACE, chain'de imza nesnesi yok). Pearl XMSS'i
  "geliştirilebilir" tutarken KÖK v2 **ilk günden PQ-önceleyici** kurar.

### 12.3 "How is PRL issued?" — Pearl'in cevabı (birebir)

> "Supply is hard-capped at 2.1 billion PRL, released on a smooth polynomial decay
> rather than discrete halvings. **Remaining supply follows R(t) = H / (t + H)**, and
> the per-block reward falls directly out of it. Issuance tapers continuously, so the
> network never faces the overnight supply shocks that halvings impose on Bitcoin."

**★ KÖK v2 ile ilişkisi — EN ÖNEMLİ DOĞRULAMA:**
- **Formül birebir doğrulandı:** R(t) = H/(t+H). Daha önce INT whitepaper §5.4'ten
  "1/t² polynomial decay" ve "H = 650.226 blok (~4 yıl)" olarak okumuştuk; FAQ
  **paydanın (t+H) olduğunu** netleştiriyor. **R(∞) → 0** — yani Pearl'in emisyonu
  **gerçek bir tail emission DEĞİL**: ödül asimptotik olarak sıfıra gider.
- **KÖK v2'nin farklılaşması (§8):** tail emission **R_∞ = sabit > 0** (Monero/Grin
  geleneği). Pearl'in "never faces overnight supply shocks" argümanı **doğru** ama
  **sonsuz ufukta güvenlik bütçesi sıfıra gider** — Pass'in kendi Thm 2'sine göre
  saldırı maliyeti = PR/2, ve R→0 ile PR→0. **KÖK v2 bunu R_∞ > 0 ile kapatır;
  Pearl'in FAQ'unda bu konu yok.** (V2 §8'de tail emission kararının nedeni
  tam olarak buydu; şimdi Pearl'in kendi formülüyle teyit edildi.)

### 12.4 "How does the network stay secure?" — Pearl'in cevabı (birebir)

> "Pearl rests on the same assumption as Bitcoin: no adversary controls 51% of the
> honest compute. **Low-rank noise on every input closes the obvious shortcut**,
> there is no way to earn a reward without performing the full matrix multiplication.
> And because Pearl runs on the commodity GPUs the entire AI industry is already
> buying, **it never concentrates into the ASIC monoculture** that has quietly
> centralized hash-based chains."

**★ KÖK v2 ile ilişkisi — iki açık yanlış/eksik:**
1. **"Low-rank noise closes the obvious shortcut"** — kısmen doğru (KW Lemma 6.5),
   ama **Basu'nun ölçümü** canlı ağda adversary'nin kurtosis kontrolünü geçtiğini
   gösterdi (N(0,18) → 2,97). Pearl'in "there is no way" ifadesi **aşırı iddialı**;
   jackpot policy'si (TV-11..14) tam olarak bunun için var. Ayrıca **Polymath 6**
  ("Is 1-bit hardware enough?") Pearl'in kendisinin açık sorusu — FAQ "never
  concentrates into ASIC monoculture" derken kendi açık problemini elememiş gibi
  duruyor. TV-21 bu konuyu INT toy'da ölçtü (FP8'de hâlâ AÇIK).
2. **"Commodity GPUs ... never concentrates"** — Hawkeye whitelist (sm90 = H100/H200
   only) ile **çelişiyor**: Pearl'in FP8 şeması belirli GPU nesillerine kilitli.
   "Commodity" doğrudur ama "never concentrates" **aşırı iddialı**; whitelist
   governance'i bunun için gerekli (spec §A.9b).

### 12.5 Diğer 4 FAQ sorusu (başlıklar alındı, cevaplar statüleri)

"What is Pearl?", "How is Pearl different from Bitcoin?", "What is Proof of Useful
Work?", "How does useful work produce intelligence and consensus from the same forward
pass?" — bu dördü pazarlama düzeyinde, teknik bir iddia içermiyor; okunmadı (zaman
tasarrufu). Eğer ileride gerekirse `agent-browser` ile aynı yöntemle açılabilir.

### 12.6 FAQ'tan çıkan en önemli sonuç

**Pearl'in FAQ'undaki üç teknik iddianın tamamı (51%, PQ, emisyon) KÖK v2'nin
dokümanlarında zaten analiz edilmişti — ve hiçbirinde çelişki yok, hepsi teyit.**
Ama **her birinde KÖK v2'nin bir adım ötede durduğu yer netleşti:**

| Pearl'in FAQ iddiası | KÖK v2'nin konumu |
|---|---|
| "at least as expensive to attack as Bitcoin" (Pass Thm 2) | **φ=0'da zayıflar** — G katmanı Demirel ile construction-level bağımsızlaştırır (TV-4/TV-8, sim §6) |
| "already in consensus" (XMSS/P2MR) | **gerilim**: whitepaper'da reserved-but-disabled; KÖK v2 PQ'yu zorunlu gate yapar |
| R(t) = H/(t+H), "no overnight shocks" | **R_∞ → 0**; sonsuz ufukta güvenlik sıfıra gider — KÖK v2 R_∞ > 0 tail |
| "no way to earn a reward without full MatMul" | **Basu yalanladı** (canlıda geçildi); jackpot policy (TV-11..14) bunun için |
| "never concentrates into ASIC monoculture" | **Hawkeye sm90 whitelist ile çelişir**; Polymath 6 hâlâ açık (TV-21) |

**Bu tablo, V2 §12 farklılaşmasının artık "kâğıt analizi" değil, Pearl'in kendi
sözlerine dayandığını gösterir — en güçlü farklılaşma argümanı budur.**
