# KAYNAKLAR — KÖK Network v2 değerlendirmesi ve yeniden tasarımı

Tüm referanslar **doğrulanmış** (2026-09-19 itibarıyla; erişim yöntemleri not edilmiştir).
Sistem tarihi: 19 Eylül 2026.

## Pearl Network (birincil kaynaklar — 2026-09-19/20, tamamı doğrulandı)

- **INT Whitepaper (tam metin, HTML):** `https://pearlresearch.ai/research/int-whitepaper`
  — KW construction'ın üretime uygulanmış hali; §3.1 noise identity + transcript +
  per-tile BLAKE3 jackpot (Algorithm 4); §4.8 üretim parametreleri (rank r ∈ {32..1024},
  16r ≤ k ≤ 4r², k ≤ 2¹⁶, 64|k); §4.7 Plonky2 ZK (<60 KB, 3-katlı recursion); §5.1
  pouw_meta block identity (ZK random malleability'ye karşı); §5.2 Taproot-only +
  OP_CHECKXMSSSIG rezerve (XMSS/SHAKE256) + P2MR (BIP-360); §5.4 S=2,1×10⁹, 194 sn blok,
  1/t² emisyon (H=650.226 blok), WTEMA difficulty; §6 econ-101 (C=$1.7/H100-sa, τ=0.1,
  τ·G·D = p·e; Pass'ın "yakında gelecek" resmi ekonomi dokümanı = 2606.06700);
  §7 lansman benchmark'ı (Llama 3.3 70B, 4×H200: Pearl-certified 17.206 tok/s vs Meta
  15.270, 806 TMADs/sn).
- **Canlı site:** `https://pearlresearch.ai` (Pearl Research Labs, NVIDIA Inception) +
  `/network` (Together AI'da Gemma-4-31B-it-Pearl endpoint'i, %25+ ucuz) + `/research`
  (makale listesi).
- **GitHub:** `https://github.com/pearl-research-labs/pearl` — 311 ★, 6.803 commit,
  public; `zk-pow/`, `pearl-blake3/`, `plonky2/`, `xmss/`, `miner/`, `node/`, `wallet/`,
  `py-pearl-mining/` (Go + Python + C kernels).
- **★ Polymath Project (açık problem listesi, `pearlpolymath.com`):** 7 matematik
  + 2 ekonomik açık problem. **Ekonomik (1) = Pearl'in KENDİ E-gap itirafı** (tam alıntı
  `PROJE_KAGIDI_V2.md` 12'de): "the marginal cost of mining is ~0 and hence also the cost
  of attacking ... the key scarce resource in PoUW mining is the ability to collect useful
  data (matrices). What should be the value/price of the Pearl coin at 0 mining overhead?
  Is it 0? infinity?" Ayrıca: (1) KW Appendix A random-rotation guvenligi -- **hâlâ açık**;
  (2) Pearl-GEMM noise dağılımı; (3) FP4/NVFP4 scale optimizasyonu; (4) **training/
  finetuning** (şu an inference only); (5) MatMul-tabanlı 128-bit hash (BLAKE3'e GPU
  alternatifi); (6) **ASIC-resistance -- Pearl kendisi sorun olarak listeliyor** ("Is 1-bit
  hardware enough?"); (7) 0%-overhead whole-model PoI ("doesn't have an efficient SNARK").
- **★ "Pearl Floating Point Scheme Specification" (Eylül 2026, yeni whitepaper PDF):**
  **FP8** PoUW -- entrywise quantization nonlineer oldugu icin düşük-rank kisayolu bozar,
  **ticket'lar doğrudan çıktı tile'larini hashler (transcript gerekmez)**. **Assumption 1
  (quantized-subspace hardness)** = KW transcript-unpredictability'in FP analoğu; r=32
  (k <= 2^16). **5 jackpot policy = 4 somut kontrol** (entry-liveness, noise-floor,
  tamed-products, unpredictable-summands) + 5.2 altı saldırı vektörü (NaN/Inf, seed
  grinding k>=1024, no-noise, low-local-entropy -> özel donanım, coherent, low-rank
  planting) + 7 beş speedup sınıfı. **Dogrulama = Hawkeye ile bit-exact replay** -- Hawkeye
  yazarları **Badash, Boneh, Komargodski, Srivastava** (Komargodski hem KW'nin hem
  Hawkeye'nin yazari). MoE extension (e <= 1024), ZK appendix (split verification).
  Detay: `PEARL_DOCS_ANALIZ.md` 11.1.
- **Domain notu:** `pearl.network` → GoDaddy park; `pearl.foundation` → DNS ölü;
  `pearlnetwork.io` → DNS ölü. Wayback Machine'de **Pearl'e ait tek kayıt yok**.

## Kriptografi / PoUW çekirdeği

1. **Komargodski, Weinstein — "Proofs of Useful Work from Arbitrary Matrix
   Multiplication."** IACR ePrint **2025/685** = **arXiv 2504.09971v4** (alındı 2025-04-15,
   v4 2025-11-13). *Tam metin: `https://ar5iv.org/abs/2504.09971` (ePrint PDF raw binary
   verir; r.jina.ai 403).* KÖK v2 G katmanının kriptografik tabanı. Bağımsız analiz:
   `KW_ANALIZ.md`.
2. **Alman, Duan, Vassilevska Williams, Xu, Xu, Zhou — "More asymmetry yields faster matrix
   multiplication."** arXiv **2404.16349** (2024). ω < 2.371339 (KW'nin alıntısı).
   *(AlphaEvolve ek gelişma: ω < 2.371177, 2026 — kriptografik değil, kalibrasyon etkisi.)*
   **⚠ ar5iv uyarısı (2026-09-20):** `ar5iv.org/abs/2504.09971` KW'yi **3 yazar**
   (Komargodski, **Itamar Schen**, Weinstein) olarak render ediyor — bu **eski bir
   sürümdür** (Schen sonradan çekilmiş). Doğru kaynak: **ePrint 2025/685 (son rev
   2025-12-08) + PDF v4 (2025-11-13) = 2 yazar** (Komargodski, Weinstein). ePrint
   "Contact author(s)": `ilankom10@gmail.com`, `omri.weins@gmail.com`.
3. **Vaikuntanathan, Zamir — "Improving algorithmic efficiency using cryptography."**
   arXiv **2502.13065** (2025). LPN tabanlı **trapdoor matrices** — gizli anahtarla
   near-linear matris çarpımı. *Tehdit olarak değerlendirildi ve çürütüldü* (E,F σ'dan
   türetilir; saldırgan trapdoor yerleştiremez).
4. **Braverman, Newman — "Practical Secure Delegated Linear Algebra with Trapdoored
   Matrices."** arXiv **2502.13060** (v3 2025-10-06, TCC 2025). Aynı teknik, güvenli
   delegasyon. Aynı çürütme.
5. **"Hawkeye: Reproducing GPU-Level Non-Determinism"** — arXiv **2603.20421v2**
   (2026-03-20; **MLSys 2026 kabul**; *Pearl'in kendi araştırması*). GPU Tensor Core
   işlemlerinin (rounding direction, subnormal handling, non-associative accumulation;
   Ampere/Hopper/Lovelace; FP16/BFP16/FP8) CPU'da **birebir, kayıpsız** re-produksiyonu;
   üçüncü-taraf denetim için. Kod: `github.com/badasherez/gpu-simulator`.
   **KÖK v2 §6'nın "determinizm" yolunun doğrulanmış kaynağı** (native-FP ZK'ya alternatif:
   reproducibility-based auditing).
5. **Ball, Rosen, Sabin, Vasudevan — "Proofs of useful work."** ePrint 2017/203 → CRYPTO
   2018 ("Proofs of work from worst-case assumptions"). İlk formal PoUW; **usefulness
   iddialarını geri çektiler** (poly-log overhead). KW bunun halefi.
6. **Dotan, Tochner — "Proofs of useless work."** arXiv 2007.01046 (2020). Öncül PoUW
   sistemlerinin neden başarısız olduğunun envanteri.

## 2026 negative results (KÖK v2'nin G/U ayrımını zorlayan kanıtlar)

7. **Basu — Pearl Network'ün ampirik ölçümü.** arXiv **2606.04819** (2026): 24 EH/s,
   ~320.000 GPU, ~112 MW → **sıfır faydalı AI hesabı**; NoisyGEMM rastgele matrisleri
   tasarım gereği kabul ediyor (44 pool-accepted share); 8.012 AlphaPool worker, 0/4.803 ML
   string; kurtosis 1.79 (uniform) vs 3.33 (NN) vs **2.97 (adversarial N(0,18) — kontrolü
   geçiyor)**; ekonomi 1.06 gelir/maliyet; vLLM coupling hashrate'in %10–30'unu götürüyor.
8. **Demirel — "Proof of Demand Is Not Proof of Work."** ePrint **2026/1492** (2026-07-21,
   rev 2026-08-23): W/B/E çerçevesi; **Lemma 1** (koalisyon kontrollü ödemeler geri alınabilir
   transfer); **Theorem 2** (leader-election talepten bağımsız yol gerektirir); **Corollary
   4**; çözüm: **geri alınamaz burn/vergi = güvenlik kaynağı.** KÖK U katmanının burn
   mekanizmasının teorik gerekçesi.
9. **Dikshit, Emami, Sedlmeir, Fridgen — SoK: "Is Proof-of-Useful-Work Really Useful?"**
   ePrint **2025/1814** (2025-10-03): 50+ construction; **utility güvenlik bütçesine katkı
   vermez**; verifiable computation + kısmi teşvik tahsisi önerisi.
10. **Komargodski, Weinstein — dışsal ödürlü PoW dengelemeleri.**
    arXiv **2505.21685** (2025): madenciler faydalı görevleri tek blokta toplayabilir →
    KÖK'ün **C_FEE anti-aggregation cap'i** (T-A3, TV-6).
11. **"SEDULity."** arXiv **2512.13666** (2025): template block'u training'e kodlayarak zincir
    bağlama — KÖK'ün ctx-binding'inden (T-A2) farklı bir yaklaşım.
12. **Proof-of-Learning with incentive security.** arXiv **2404.09005** (2024):
    Θ(1)→O(log E/E) overhead, Verifier's Dilemma aşımı.

## Ekonomi

13. **Pass — "The Economics of Proof-of-Useful-Work."** arXiv **2606.06700** (2026-08-10):
    M/L/D aktiviteleri, Δ = 1/γ + 1/α − 1, θ = PR/(pQ), **Theorem 1** (Bitconia /
    Fortessia / Duplexia rejimleri), **Theorem 3** (p = αe/(1+θ), ΔSV), **Prop 1**,
    saldırı maliyeti = PR/2 (her rejimde), Fisher temeli. KÖK `pass_sim.py`'in teorik
    tabanı; Pearl kalibrasyonu (eS=PR Tullock) canlı ağı %5,8 içinde yeniden üretti.
    *PDF'ten tam doğrulama (2026-09-20):* **Theorem 2 = Cost₅₀% = PR/2 "in any competitive
    equilibrium, regardless of which regime"**; kısmi geri ödeme ν ile **(1−ν)PR/2**;
    saldırı tanımı[block rewards geri alınamaz (token çöküşü) — "if the attacker can also
    redeem block rewards at their full current USD price, the net cost of attacking is zero
    even for Bitcoin"]; **Theorem 3** p = (α/(1+θ))·e < e; **α = γ = 1.3 ≈ %23 tasarruf**
    ("for the price of one compute op, duplex delivers 1/1.3 ≈ 0.77 units of inference and
    1/1.3 ≈ 0.77 units of security"); Talep esnekliği (Jevons, ε=2) tüm sonuçların
    önkoşulu; kalibrasyon $30B inference market / 52.560 blok.
14. **"Verifiability–usefulness tension" — arXiv 2209.03865** (Basu'nun alıntısı; tam
    yazar listesi doğrulanmadı).
15. **Peigné, Nguyen, Wang — "Zero knowledge verification for frontier AI training is
    possible."** arXiv **2606.05433v2** (2026-06-03, v2 2026-08-22, 44 sayfa). *Doğrulandı
    (2026-09-19):* zkVM + native BF16/FP32 precompiles ile **gerçek kayan nokta** hesabının
    doğrulanmesi (fixed-point yaklaşımı değil); pre-committed training spec + inter-node
    observations + on-the-fly Merkle commitments; genesis/in-training/ex-ante ispat tipleri;
    ~36 ay deployable PoC, tek-haneli-% training overhead; 13 açık problem. **KÖK v2 §6'nın
    "yarın" yolunun kaynağı** — native FP ZK olgunlaşınca 𝔽_q fixed-point'ten geçiş.

## Kullanılan araç / yöntem (erişim notları)

- `web_search` (401) kullanılamaz; **Bing/Google engelli** → tüm araştırma
  `mcp__weblocal__web_fetch` ile **arXiv API** (`http://export.arxiv.org/api/query?...`,
  tek tırnaklı phrase; `AND` boş döner; `ti:"..."` çalışır) ve **ePrint arama**
  (`https://eprint.iacr.org/search?q=...`, kağıt sayfaları `https://eprint.iacr.org/2025/685`)
  üzerinden. **ePrint PDF raw binary verir**; tam metin için **ar5iv.org**.
- **Wayback Machine** çalışıyor (`archive.org/wayback/available?url=...` + CDX API) —
  Pearl için **boş** çıktı (arşivlenmiş kayıt yok).
- **PDF'ler okunamıyor** (raw binary) — PDF gerektiğinde kullanıcı metni paste eder
  (ilk örneği: Pearl'in yeni whitepaper'ı, bkz. `PEARL_DOCS_ANALIZ.md` §8).
- Kanıt deposu: `findings.md` (§9–§18), `DEGERLENDIRME_100.md` (§6–§8, §13),
  `PEARL_DOCS_ANALIZ.md` (Pearl birincil kaynak analizi).

## Pazar verileri (2026-09-19)

BTC 204,44 TWh/yl, ~904 EH/s, $81.448 (ATH $126.080'den −%35,4); Kaspa 27,71B/28,70B KAS
madenciligi (%96,5, ~$40M kaldı); Dynex mcap $128k ATL'de (−%99,91); AI-compute token'ları
TAO −%65, RNDR −%88, AKT −%93. Pearl: 800 blok/gün (108 s), 2.674 PRL/blok, $0,76.

---

## ★ KANIT İNDEKSİ — her iddia nerede kanıtlanıyor (2026-09-20)

> Bu indeks, `KRIPTOGRAF_BRIEF.md`'in eki ve dış denetimin hız başlangıcıdır:
> her iddia → **dosya + bölüm + doğrulama tipi** (çalışan test / PDF alıntısı /
> canlı URL / model çıktısı). "LLM okuması" olanların başında † işareti var.

### G katmanı (kriptografi)

| İddia | Kanıt | Tip |
|---|---|---|
| KW güvenliğinin asıl ayağı (a)+(b)+Merkle, (c) değil | `KW_ANALIZ.md` §3.1, §6.1 | **KW birebir alıntı** + † analiz |
| Assumption 6.4'ün Θ(n³/r) output-size bound'undan neredeyse otomatik | `KW_ANALIZ.md` §6.1 | **KW birebir** ("the number bits... is always a lower bound") |
| Conjecture A.1 (random-rotation) hâlâ açık | `KW_ANALIZ.md` §6.3; Pearl Polymath Problem 1 | **Pearl'in kendisi** soruyor |
| α = o(1) overhead | `KW_ANALIZ.md` §6.4 | **KW birebir** |
| Lemma 6.5 (E,F üniform rank-r, ROM) | `KW_ANALIZ.md` §6.4 | **KW birebir** |
| Prescribed hardness: easy-instance avantajı yok | `g_layer_tests.py` **TV-2** | **çalışan test** (yayılma <%15) |
| Permutation/seyrek saldırısı işe yaramaz | `g_layer_tests.py` **TV-3** | **çalışan test** |
| A=B=0 kötü girdi yok | `g_layer_tests.py` **TV-4** + V1X | **çalışan test** |
| ctx-binding replay saldırısını kapatır | `g_layer_tests.py` **TV-1** | **çalışan test** |
| Jackpot policy 4 kontrolü | `g_layer_tests.py` **TV-11..TV-14** | **çalışan test** (toy INT) |
| Low-entropy (Polymath 6) dayanıklılığı | `g_layer_tests.py` **TV-21** | **çalışan test** — INT için; FP8 için **AÇIK** (§A.10.7 notu) |
| FMM ilerlemesi oranı korur | `KW_ANALIZ.md` §3.3 satır 6 | † analiz (simetri argümanı) |
| Trapdoor matrix tehdidi değil | `KW_ANALIZ.md` §3.3 satır 5 | † analiz (E,F σ'dan) |
| Retarget güvenli (pencere+medyan) | `g_layer_tests.py` **RT-1..RT-3** | **çalışan test** |

### U katmanı (görev pazarı + sansür)

| İddia | Kanıt | Tip |
|---|---|---|
| Escrow+burn+fraud penceresi çalışıyor | `u_layer_prototype.py` **TV-5..TV-10** | **çalışan test** |
| İade-garantisi sansürün faydasını sıfırlar | `f3a_sequencer_proto.py` **TV-15** | **çalışan test** |
| Görev-göçü bond keser (negatif getiri) | `f3a_sequencer_proto.py` **TV-16, TV-17** | **çalışan test** |
| **Bond geri-ekleme zorunlu** (deterrent tek-seferlik olmasın) | `f3a_sequencer_proto.py` **TV-20** + `pass_sim.py` §10 | **çalışan test + model** — † ekonomi modeli prototipte açık buldu |
| Dinamik bond = fee + margin | `pass_sim.py` §10 (oyun-dışı 120 → bond 200 yetersiz) | **model çıktısı** |
| Verifier's dilemma tetiklenmez | `f3a_sequencer_proto.py` **TV-18** | **çalışan test** |

### Ekonomi

| İddia | Kanıt | Tip |
|---|---|---|
| Saldırı maliyeti = PR/2 her rejimde | Pass **Theorem 2** (PDF birebir) | **PDF alıntı** (`extracted/Pass_full.txt`) |
| p = (α/(1+θ))·e < e; ~%23 tasarruf | Pass **Theorem 3** (PDF birebir) | **PDF alıntı** |
| Model canlı ağı ilkelerden üretir (Pearl %5,8) | `pass_sim.py` §0, §9 regression guard | **model çıktısı** |
| Zero-talep → pure-PoW yaşar (Demirel Thm 2) | `pass_sim.py` §6 | **model çıktısı** |
| Fortessia ×3,33 güvenlik | `pass_sim.py` §3 | **model çıktısı** (α=γ=1,3) |
| **F3a pass_sim'i kalibre edemez** (küçük-ölçek limiti) | `pass_sim.py` §9 (%86 sapma) | **model çıktısı** — † negatif sonuç, V2 §10.1'i düzeltti |
| E-gap: Pearl'in kendi itirafı | Polymath Ekonomik (1) | **birebir alıntı** (yukarıda, `PROJE_KAGIDI_V2.md` §12) |
| φ=0 canlı ağda | Basu arXiv 2606.04819 | **yayın** (24 EH/s, sıfır fayda) |

### Determinizm / FP

| İddia | Kanıt | Tip |
|---|---|---|
| Hawkeye bit-exact replay üretimde | Pearl FP wp + Hawkeye MLSys 2026 | **canlı URL + yayın** |
| Yol A (Hawkeye) Faz 2, Yol B (Peigné) Faz 3 | `KOK_V2_TEKNIK_SPEC.md` §A.9b | † karar + yayınların statüsü |
| Pearl FP'de transcript gerekmez | Pearl FP wp §5.1 | **birebir alıntı** (Q(A+N) ≠ Q(A)+Q(N)) |
| GPU whitelist riski | `KOK_V2_TEKNIK_SPEC.md` §A.9b | † honest risk |

### Farklılaşma / migration

| İddia | Kanıt | Tip |
|---|---|---|
| Pearl iki gerçek hard fork yaptı | Pearl `docs/{moe,salted-seed}-fork-upgrade-guide.md` | **canlı GitHub** |
| MoE geriye uyumlu, salted-seed zorunlu | aynı rehberler | **birebir** ("old dense proofs work..."; "everything must be upgraded") |
| E-gap mimariye yedirildi (G/U) | `PROJE_KAGIDI_V2.md` §A.1, §12; Demirel Thm 2 | † tasarım + **yayın** |
| Rakip hamle senaryoları | `PROJE_KAGIDI_V2.md` §12.1 | † analiz (Pearl Polymath üzerinden) |

### BİLİNEN AÇIKLAR (dış denetim odak noktası)

1. **2 bağımsız insan kriptograf incelemesi YOK** — `KRIPTOGRAF_BRIEF.md` gönderilmedi.
   `KW_ANALIZ.md` §1–6'nın tamamı **† LLM okumasıdır**.
2. **FP8 low-entropy AÇIK** — TV-21 INT için dayanıklı; FP8 için noise modeli
   quantization-aware yazılmadı (Faz 3).
3. **TV-17'nin ekonomik ağırlığı kısmen açık** — bond=fee+margin'in margin'i
   F3a'da ölçülecek; pass_sim §10 yalnızca eşik denklemini verdi.
4. **Toy boyut** — q=97, n=8, r=2, K=64: **asimptotik argümanları test etmez.**
5. **GHOSTDAG parent-set seçimi prototipde YOK** (tek parent).
6. **FAQ cevapları eksik** (51% saldırı, PQ, PRL emisyonu — JS accordion'da).

### Erişim yöntemi özeti (araç kısıtları)

- `web_search` **401** (ölü) → tüm fetch `mcp__weblocal__web_fetch` ile.
- **arXiv API**: `http://export.arxiv.org/api/query?...` (tek tırnaklı phrase, `AND` boş).
- **ePrint PDF raw binary** → tam metin **ar5iv.org** veya kullanıcı-pasted PDF.
- **Kullanıcı-pasted PDF'ler**: `pdftotext -layout` → `extracted/KW_full.txt` (1.258
  satır), `extracted/Pass_full.txt` (3.430), `extracted/Pearl_new_wp.txt` (1.223).
- **Wayback çalışıyor** ama Pearl için **boş**.
- **JS-rendered sayfalar okunamıyor** (SPA/accordion) → FAQ eksikliğinin sebebi.
