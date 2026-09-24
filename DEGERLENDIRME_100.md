# KÖK Network — Mükemmelliyetçi 100/100 Değerlendirmesi

**Değerlendirme tarihi:** 19 Eylül 2026
**Değerlendirilen:** `PROJE_KAGIDI.md` — "KÖK Network: Faydalı Yapay Zeka Madenciliği ve Modüler Kriptografik Konsensus L1"
**Yöntem:** First-principles review + 19 Eylül 2026 tarihli canlı akademik (arXiv / IACR ePrint) ve
piyasa (CoinGecko / Digiconomist / blockchain.info) verilerle iddia-iddia doğrulama.

## 0. Cevap (TL;DR)

**100/100 değil. Gerçek puan: 37/100.**

> **2026-09-20 güncellemesi (§9'ya bakın):** bu puan **v1'e** aittir. Sonraki oturumlar
> v1'i yeniden tasarladı (`PROJE_KAGIDI_V2.md`, `KOK_V2_TEKNIK_SPEC.md`): KW G katmanı +
> G/U ayrımı + ctx binding + jackpot policy (TV-11..TV-14) + Pass ekonomisi + tail emission.
> **v2'nin kâğıt puanı ≈ 77/100** (aynı rubrik); kalanın ~15'i **empirik kanıt** (insan
> kriptograf incelemesi, canlı φ>0, güvenlik bütçesi) gerektirir — kâğıt hatası değil.
> **100/100 yine değil; ama 37 → 77'lik sıçramanın sebebi §4.1'in "en büyük delik"
> dediği güvenlik açığının kapatılmasıdır.** Aşağıdaki eleştirilerin çoğu v2 için
> artık geçerli değil; §9'da hangilerinin kapandığı, hangilerinin açık olduğu tek tek
> yazılıdır. **85 kâğıt tavanı hâlâ geçerli — mükemmel kâğıt çalışan zincir değildir.**

Kâğıt, bu havuzdaki çoğu fikirden **daha iyi** bir yerde: ileri sürdüğü kriptografi gerçekten var
(GKR, sumcheck, lattice folding, GHOSTDAG hepsi gerçek ve doğru bağlamda anılmış), problem
tespiti (PoW enerjisi, PoS oligarşisi, AI compute kıtlığı) 2026'da hâlâ geçerli, ve "fair launch"
konumlandırması samimi. Ama bir **paradigm shift** iddiası için beş ölümcül boşluk var; üç tanesi
tek başına projeyi **birkaç saatlik bir incelemede çökertir**:

1. **Güvenlik bağlamı yok (SNARKChain hatası):** Matris ispatı bloğun içeriğine, zincir
   geçmişine ve madencinin kimliğine bağlanmamış. Precompute / replay / grinding saldırıları
   $KOK basıldığı andan itibaren mümkün.
2. **Görev seçim saldırısı (structured matrix):** Madenci A'yı permütasyon/seyrek matris seçerse
   "O(n³) faydalı iş" O(n)'ye, hatta O(1)'ye düşer. "Faydalı iş" zorunluğu çöker. Çözüm,
   matrisleri protokolün üretmesi (random dense) ise o iş artık faydalı değildir — sadece farklı bir
   türde amaçsız iş. **Bu ikilem kâğıtta fark edilmiyor bile.**
3. **İspat overhead'i faydayı boğuyor:** 2026 kanıtı (SaTML 2026): milyar parametreli modeller
   için kriptografik ispat **yüzlerce saniye**; inference'ın kendisi **milisaniyeler**. Enerjinin
   ~%99.999'u "faydalı AI çıkarımı"na değil, ispat üretimine gider. Premsinin tam tersi.
4. **Kayan nokta vs. sonlu cisim:** GKR/sumcheck exact arithmetic ister; gerçek GPU inference
   FP8/FP16 tensor core non-associative'dir (MLSys 2026, Hawkeye). Ya ispat ses olmaz ya da
   tensor core'lardan vazgeçilir ve "faydalı" olmaktan çıkar.
5. **Fikir zaten yayımlandı:** HadAgent (Nisan 2026) Proof-of-Inference konsensüsünü **çalışan
   prototiple** (%100 tespit, sub-ms validasyon) yayımladı. KÖK'ün "paradigm shift"i Eylül 2026'da
   yeni değil; üstelik çözülmesi gereken sorunların çözülmüş hali mevcut.

Ayrıca ekonomi tarafında **Kaspa emisyon modeli 2026'da tükenmiş durumda** (max arzun %96.5'i
çıktı, kalan hepsi ~$40M) ve "sıfır hazine + fair launch" ile GKR seviyesinde kriptografi
Ar-Ge'si finanse edilemez. Rekabette: bu kategorinin en yakın örneği **Dynex, 3 gün önce kendi
tüm zamanların en düşük seviyesinde** (ATH $1.39 → $0.0012, market cap $128 bin).

---

## 1. İlk İlkeler Üzerinden İnceleme (Five-Line Review)

```text
First Principle: Bir L1'in göz ardı edilemez amacı: Permissionless şekilde sansüre dayanıklı,
  değiştirilemez bir ledger. Bunun bedeli, saldırganın rewind/playback yapamayacağı, zincire
  sıkı sıkıya bağlı, "tekrar üretilemez" bir hesaplama harcamasıdır.

Non-negotiables: (1) İş bloğa + madenci kimliğine + zincir geçmişine bağlı olmalı (precompute/
  replay yok). (2) Görev, madencinin kolay varyasyonunu seçmesini engelleyecek şekilde
  worst-case zor olmalı. (3) Doğrulama, ispatlanandan asimptotik olarak çok daha ucuz olmalı
  VE blok başına doğrulama maliyeti ağın blok hızına yetmeli. (4) Ses ~2^-128 olmalı.

Assumptions to Drop: (a) "Matris çarpımı = zor iş" — yapısal matrislerde O(n)'ye düşer.
  (b) "Doğrulayıcı enerji harcamaz" — O(n²) verification + A,B'nin data availability'si
  saniyede 10 blokta değil. (c) "O(log n) mikrosaniye" — sumcheck sequential round'lardan
  muzdarip (Haziran 2026, arXiv 2606.16146). (d) "10.000x" — Freivalds için n ≈ 10⁴ gerekir
  (3 matris × 10⁸ giriş ≈ 1.2 GB/blok). (e) "WASM güncellemesi = forksuz göç" — kural
  değişikliği tanımı gereği fork'tur; itiraz olursa chain split.

Known Prior Art: HadAgent (arXiv 2604.18614, Nisan 2026) — Proof-of-Inference konsensüsü,
  çalışan prototip; SNARKChain (arXiv 2510.09729) — PoUW'da zincir bütünlüğü + madenci
  kimliği gömme zorunluluğu; Pass (arXiv 2606.06700) — PoUW ekonomisinin formal dengesi.

Smallest Sufficient Path: Konsensüsün "faydalı iş" kısmını bir PoUW problemi olarak değil,
  SNARKChain gibi "ispat üretiminin kendisi" ( outsourced proof marketplace) olarak yeniden
  tasarla; veya HadAgent'in deterministic-reexecution + Merkle modelini benimse. Matris
  çarpımını bırak: o, PoUW için resmen kötü problem sınıfı.

Escalation Signal: Görev-pazarı tasarımı (kim matrisleri veriyor, nasıl bağlanıyor, sybil
  nasıl önleniyor) spec'e girmeden Faz 1 whitepaper'ı yazmaya başlanmamalı; bu protokolün
  güvenlik ispatının özüdür, bir "detay" değildir.
```

---

## 2. İddia-İddia Doğrulama (Claim-by-Claim)

### İddia 1: "Bitcoin/Kaspa enerjisi tamamen boşa harcanıyor" — KISMEN DOĞRU, ama 2026'da çift yönlü
- **Doğru:** Bitcoin ~**204.44 TWh/yıl**, 114 Mt CO₂ (Digiconomist, 19.09.2026). Şu anki BTC
  fiyat $81,448 ve hashrate **~904 EH/s**. Enerji tartışması geçerli.
- **Ama kâğıdın kaçırdığı:** Digiconomist'in kendi "latest research"i (Mayıs 2025) diyor ki
  **"AI could consume more power than Bitcoin by the end of 2025."** Yani KÖK'ün ikna edeceği
  muhatap için "enerji israfı" argümanı zaten AI'ya kaymış durumda. "PoW enerjisi boşa, onun
  yerine AI hesaplayalım" tezi, "AI da aynı büyüklükte enerji yiyecek" gerçeğiyle yumuşıyor.
  Etkili bir pitch, bunu önceden karşılamalı.

### İddia 2: "GKR/Sumcheck ile O(log n) doğrulama" — ASIMPTOTİK OLARAK KISMEN, PRATİKTE YANLIŞ
- Kâğıdın **kendi diyagramındaki denklem yanlış değil**: `A×(B×r) == C×r` tam olarak Freivalds
  (1979). Pratik verifier karmaşıklığı **O(n²)**, O(log n) değil. O(log n), sumcheck'in
  *round* sayısıdır (oracle modelinde); her blokta uygulanabilir formda değil.
- **"10.000'de 1" iddiası:** Freivalds ile oran = 1/n. 10.000x için **n ≈ 10⁴** gerekir. Bu,
  her blok için 3 matris × 10⁸ giriş ≈ **1.2 GB (32-bit)** veri demografi; saniyede hedeflenen
  DAG blok hızında (Kaspa ~10 BPS) saniyede ~12 GB — fiziksel olarak imkânsız.
- **Ses (soundness):** Freivalds'in hata olasılığı her round'da 1/|F|. Blokzincir için
  2⁻¹²⁸ gerekir; 256-bit cisim ile tek round yeterli ama kâğıtta hiç belirtilmemiş.
- **Donanım gerçekliği:** arXiv 2606.16146 (Haziran 2026, B. Bünz dahil) **"SumCheck suffers from
  sequential, dependent rounds"** diyor; NTT daha hardware-friendly. "Mikrosaniyede doğrulama"
  ifadesi, round sayısı network latency'siyle çarpışınca çöküyor (zaten blockchain'de Fiat-Shamir
  + round-trip yok ama prover-side sequential dependency madencilik latency'sini patlatır).

### İddia 3: "2025-2026 GKR + Lattice Folding bu engeli tarihe gömdü" — AŞIRI ÖVGÜ
- **Lattice folding** (BCLMS, 2024) gerçektir; IVC için lattice tabanlı folding açar. Ama:
  (a) Kâğıdın "Lattice-Jolt" adı spekülatif — öyle bir standart yok.
  (b) **Daha önemli:** IACR ePrint 2024/1731 = **"Arc" (CRYPTO 2025)**: *hash-tabanlı*
  accumulation scheme; homomorphic vector commitment'e (ve kuantum zafiyetine) ihtiyaç duymadan
  **sınırsız derinlikte** PCD. Yani **post-kuantum folding için lattice'lere gerek bile yok**;
  daha basit bir yol zaten CRYPTO 2025'te yayınlandı. Kâğıdın geleceğe-yönelik "modüler ispat
  motoru" fikri aslında doğru yöndedir ama olgun ekosistemden habersiz sunuluyor.
- **Kuantum çerçevesi yanlış yerde:** Grover, hash bulmacayı karesel hızlandırır; SHA-256
  256-bit çıktıyla PoW için yeterince güvenlidir. Asıl kuantum riski **imzalarda** (ECDSA →
  Dilithium/Falcon). "Kuantum-dayanıklılık"u ispat motoruna bağlamak, önceliği şaşırıyor.

### İddia 4: "Madenciler faydalı AI tensör işi yapar" — EN ZOR İDDİA, EN ÇOK DELİK
- **(a) Yapısal-matris saldırısı (ölümcül):** Matris çarpımı *worst-case* zor, *average-case*
  kolay değildir. Madenci `A`'yı bir **permutation matrix** (veya seyrek/identity) seçerse
  `C = A×B`'yi O(n)'de hesaplar, ispat yine geçerli olur, "O(n³) faydalı iş" sıfırlanır.
  Freivalds denklemi `C`'nin *doğruluğunu* kanıtlar; **prover'ın gerçekten O(n³) harcadığını
  kanıtlamaz.** Bu, PoUW literatürünün bilinen birinci dersi (SNARKChain'ın "chain integrity +
  miner identity must be embedded in the puzzle" eleştirisi, arXiv 2510.09729).
- **(b) İspat overhead'i faydayı boğar:** SaTML 2026 (arXiv 2603.19025): *"existing
  cryptographic proof systems ... introduce prohibitive prover overhead (e.g., hundreds of
  seconds per query for billion-parameter models)."* Aynı makalenin verdiği çıkış yolu
  (sampling-based, Merkle commitment) **sesi verimliliğe takas ediyor** — blokzincir consensus'ı
  ise tam 2⁻¹²⁸ ses ister. Bu, "az soundness, tekrarlanan sorgularda yakalanma" mantığıdır;
  **bir blok bir kez doğrulanır, "tekrarlanan sorgu" yoktur.**
- **(c) Kayan nokta (çözülmez gerilim):** GKR/sumcheck sonlu cisim ister. Gerçek AI inference
  FP8/FP16 tensor core'larda yapılır ve **non-associative accumulation** nedeniyle
  non-deterministtir (Hawkeye, MLSys 2026, arXiv 2603.20421). `A×(B×r) == C×r` FP'de ses
  değildir (yuvarlama hataları birikir, adversarial rounding ile atlanabilir). Exact cisme
  geçilirse tensor core'lar kullanılamaz → bu "AI çıkarımı" olmaktan çıkar.
- **(d) Veri kullanılabilirliği:** Doğrulayıcının `A` ve `B`'ye ihtiyacı var. Her blokta n²
  giriş. Saniyede on blokta (DAG hızı) bu miktar, küçük n'de bile kasıtlı bir taşıma yükü.
- **(e) ASIC merkeziyetsizleşmesi:** Matris çarpımı, GPU/TPU'nun **tam olarak** işidir. Özel
  bir matmul ASIC'i (veya TPU sınıfı donanım) Generic GPU'yu ezerek geçer; KÖK'ün iddia ettiği
  "GPU madencisi demokrasisi" birkaç ay içinde donanım oligarşisine döner. Kaspa'da bile
  ASIC'leşme tartışmalı bir konuydu; matmulde bu kesindir.

### İddia 5: "GHOSTDAG paralel blok DAG'si" — Doğru protokol, ama teşvik açığı mevcut
- GHOSTDAG (Sompolinsky & Zohar; PHANTOM: IACR ePrint 2018/104) gerçek ve Kaspa tarafından
  kanıtlanmış bir protokol. Seçim mantıklı.
- **Ama:** Üç akademik saldırı makalesi (arXiv 2109.01102, 2305.16757 ve ACNS 2025 / 2501.10888)
  gösteriyor ki GHOSTDAG'in **random transaction selection stratejisi Nash dengesi değildir**:
  açgözlü sapmalar daha çok kazandırır, throughput düşer ve madenciler **ortak havuz kurmaya
  teşvik edilir** → merkeziyetsizlik bozulur. KÖK kâğıdı DAG'in teşvik-uyumluluğundan tek kelime
  bahsetmiyor. Üstelik KÖK'de transaction seçimi yok ama matris görevlerini de aynı DAG'a
  yerleştirme zorunluluğu olacak; bu saldırı sınıfı doğrudan transfer olur.
- **Zorluk ayarı paradoksusu:** Bitcoin'de PoW'un üssel dağılımı,difficulty ayarını doğal yapar.
  Deterministik matmul işinde blok süresi donanım hızıyla sabitlenir; ağ toplam hızını
  bilmeden difficulty (matris boyutu n) hedeflenen blok hızında tutulamaz. Kâğıtta
  difficulty-adjustment algoritması yok — bu, bir L1 için olmazsa olmaz.

### İddia 6: "Modüler İspat Motoru (PVI/WASM) ile forksuz göç" — Güzel fikir, yanlış satış
- Ayrıştırma (consensus motoru ↔ verifier) **doğru bir mühendislik içgüdüsüdür**; crypto-agility
  gerçek bir değer. Kaspa'nın Rust yeniden yazımı bile benzer bir modülerlik felsefesi izledi.
- **Ama "sıfır kesinti, hard-fork yemez" yanlış:** Konsensüs kurallarını değiştirmek *tanımı
  gereği* fork'tur. Eğer tüm düğümler aynı anda güncellemezse chain split olur. "On-chain
  sinyal + WASM güncellemesi" en fazla **yumuşak aktivasyon** (soft-fork benzeri) olabilir;
  "forksuz" iddiası, consensus'ın doğasını yanlış anlatıyor.
- **Saldırı yüzeyi:** On-chain verifier modülü güncellemeleri bir **yönetişim saldırı vektörü**
  yaratır: kötü niyetli/bug'lı bir WASM verifier, zincirin tüm sesini tek sinyalle çökertebilir.
  WASM determinizmi ve node uygulamaları arası taşınabilirlik de (külçük bile olsa) consensus
  riskidir. Modülerlik gerekli, ama "bir seferde tüm ağ'ı runtime'da değiştir" bir L1'de
  ancak çok denetimli bir akışla (audit + hata testi + phased rollout) yapılabilir; kâğıtta
  bitti.

### İddia 7: "%100 Fair Launch, Kaspa emisyon modeli" — 2026'da tehlikeli kopya
- **Kaspa emisyonu tükenmiş durumda:** Circulating 27.71B / max 28.70B KAS = **%96.5 madencilikle
  çıktı** (CoinGecko, 19.09.2026). Kalan tüm emisyon ~995M KAS ≈ **$40M**. Yani 2026'da Kaspa
  modelini kopyalamak, "güvenlik bütçesini birkaç yıl içinde sıfıra indiren bir eğri"
  seçmektir. Kaspa bunu based-rollup + global sequencer vizyonuyla (akıllı sözleşme fee
  geliri) telafi etmeye çalışıyor — CoinGecko tanımına göre Kaspa 2026'da kendini zaten
  *"world's global sequencer for traditional finance"* olarak konumluyor, **useful-work
  değil**.
- **Güvenlik bütçesi matematiği:** Pass'ın 2026 modeli (arXiv 2606.06700) şunu gösteriyor:
  PoUW'da bile **majority saldırı maliyeti blok ödülüne bağlı kalır**. Blok ödülü hızla
  sıfırlanan bir zincir, gün 1'den itibaren fee gelirine muhtaçtır; yeni bir zincirde fee
  yoktur. **Çıkmaz.**
- **"Sıfır VC, sıfır hazine" = uygulama riski:** GKR seviyesinde kriptografi + WASM VM + DAG
  consensus + madenci yazılımı; bu, Kaspa'nın yapacağından çok daha derin bir Ar-Ge. Kaspa
  bile bunu gönüllü/community-funding modeliyle yürüttü ve yıllar aldı. Hazinesiz bir fair
  launch ile bu ekibi kim finanse edecek? Kâğıt bu çelişkiyi görmüyor.

### İddia 8: "Basılan her $KOK küresel AI çıkarımına endekslidir" — En riskli cümle
- Bu, "gerçek fayda" vaadi en cazip kısmı ama **hukuki olarak en tehlikelisi**: bir token'ı
  somut bir dış ekonomik çıktıya (AI inference) bağlamak, menkul kıymet/emtia düzenlemesinde
  "investment contract" testinin (Howey) kıyısında gezinir. "Fair launch, ön madencilik yok"
  bunu kaldırmaz; kurucu ekibin teşvik + teşvik + teşvik modeli, teşvik eden "tüzel kişi"
  olarak teşvik edilebilir. Kâğıtta hukuk bölümü **yok**. Türkiye'de kripto varlık hizmet
  sağlayıcılarına yönelik lisans rejimi (2025'ten itibaren yürürlükte) listeleme/custody
  tarafını kapsarken madenciliğin durumu ayrı bir başlık; ABD tarafında SEC'in yapay zeka
  vaatleriyle ilgili "AI-washing" eylemleri önceliklidir. **Doğrulanması zorunlu bir alandır,
  kâğıt dokunmamış.**

### İddia 9: İsim felsefesi / kurucu gizliliği — Pazarlama, değil teknik değer
- "Roots of Unity / Root Node / Kök Tengri" kelime oyunları etkilidir ama **etimolojide hata**
  var: Eski Türkçede **"Kök Tengri" = Mavi/Gök Tengri'dir** (kök = gök/mavi renk); "kök =
  menşe/soy" modern bir homograftır. İki anlamı birbirine karıştırmak, akademik bir okuyucuda
  (ki hedef kitle bu olmalı) güven zedeliyor.
- **"Dünyadaki hiçbir analist bu ismi kurucuyla bağdaştıramaz"** kanıtlanamaz bir iddiadır; opsec
  iddiaları bu şekilde yapılmaz. Üstelik kasıtlı olarak Türk/Altay mitolojisine (Kök Tengri /
  Tengra) bağlanan bir isim, jeopolitik olarak **bağlamı daraltır** — "tarafsız evrenel" iddiasıyla
  çelişir.

### İddia 10: Yol haritası — Eksik kritik maddeler
- Faz 1–4 akla yatkın sırada. Ama **zaman çizelgesi, ekip, bütçe, güvenlik denetimi, ekonomik
  simülasyon ve difficulty-adjustment spec'i yok.** Faz 1'de "formal matematiksel makale"
  isteniyor; o makalenin asıl zor kısmı **görev-pazarı ve güvenlik bağlamı modelidir**, GKR
  denklemleri değil.

---

## 3. Ağırlıklı Puan Rubriği (100 üzerinden)

| Kategori | Ağırlık | Puan | Ağırlıklı | Temel gerekçe |
|---|---:|---:|---:|---|
| **Teknik doğruluk & güvenlik modeli** | %40 | **40** | 16.0 | Freivalds denklemi doğru; ama O(log n)/mikrosaniye/10.000x tutarsız; ses spec'i yok; **gürev-seçim ve blok-bağlama saldırıları çözülmemiş** (en büyük delik) |
| **Tokenomics & ekonomi** | %20 | **35** | 7.0 | Fair launch samimi; ama Kaspa emisyonu 2026'da tükenmiş (%96.5 çıktı), hazine yok, security-budget çıkmazı, Pass modelinin parametreleri yok |
| **Piyasa / farklılaşma / öncül sanat** | %15 | **30** | 4.5 | HadAgent (Nisan 2026) fikri çalıştırılabilir prototip ile yayımladı; Dynex fiyaskosu; AI-compute tokenleri genel olarak −65%…−93% |
| **Uygulanabilirlik & mühendislik** | %15 | **45** | 6.75 | PVI/crypto-agility içgüdüsü doğru; ama forksuz-göç yanlış; veri kullanılabilirliği, difficulty ayarı, ASIC merkeziyetsizleşmesi yok; timeline/ekip/bütçe yok |
| **Hukuki & uyum** | %5 | **20** | 1.0 | Hiç ele alınmamış; "AI'ya endeksli token" en riskli tasarım; TR lisans rejimi + SEC AI-washing |
| **İsim / pazarlama / opsec** | %5 | **40** | 2.0 | Kelime oyunları etkili ama etimoloji hatalı; opsec iddiası kanıtlanamaz; coğrafi bağlam vizyonla çelişiyor |
| **TOPLAM** | %100 | — | **37.25 ≈ 37/100** | |

**Not:** Bu puan, "fikir havuzu kâğıdı" standardıyla; bir whitepaper veya yatırım dokümanı
standardıyla değil. Havuz kâğıdı olarak bu, ortalamadan üstün (kriptografi referansları doğru,
problem hâlâ geçerli). Ama **100/100 mükemmelliyetçi** standardında 37'dir ve puanın %70'ini
kaybettiren şey **vizyon değil, üç beş somut teknik boşluktur.**

---

## 4. 100/100 İçin Ne Gerekir? (Düzeltilebilirlik Analizi)

İyi haber: **bu boşlukların hepsi kapatılabilir** ve her biri kapandığında puan somut atlar.

### 4.1 Güvenlik bağlamı (40 → 70'e atlatır) — ZORUNLU
Matris ispatını şunlarla bağla:
- **Zincir bağlamaya:** İspatın canonical statement'ine `prev_block_hash` (veya seçili
  parent block'ların GHOSTDAG sıralaması) dahil olsun; böylece precompute ve replay imkânsız.
- **Madenci kimliği:** Blok ödül adresi, ispatın statement'ine gömülsün (SNARKChain'ın
  "chain integrity + miner identity" gerekliliği).
- **Görev-commit:** Görev (A,B) ya (i) zincirdeki bir "task ledger"'dan gelsin, ya da (ii)
  **VRF/seed ile protocol-level** belirlensin. (ii) durumunda iş "sentetik" olur — o zaman
  "faydalı" olduğunu iddia etmek yerine PoW-görevi olarak dürüstçe tanıt.

### 4.2 Görev seçim saldırısına çözüm — ZORUNLU
- **Kök çözüm:** "Faydalı iş" için matris çarpımını **bırak**. PoUW için iyi problem sınıfı
  *değil*: worst-case zorluk garanti edilemiyor. Yerine:
  - **(a) SNARKChain modeli:** Faydalı iş = **ispat üretiminin kendisi** (outsourced SNARK
    marketplace). Doğrulama zaten ucuz; "faydalı" ile "ispat" arasındaki gerilim ortadan kalkar.
  - **(b) HadAgent modeli:** Deterministic LLM inference + Merkle trace commitment + ağ
    tarafından re-execution (consensus-speed verification). KÖK'ün GKR fikrini bununla
    hibridle: GKR *lineer* omurgayı doğrula, non-lineer kısımlar için sampling.
  - **(c) Eğer matris kalacaksa:** Matrisler **zincirdeki görev havuzundan** gelmeli ve
    yoğunluk/rastgelelik protokol tarafından doğrulanmalı (madenci seçemez).

### 4.3 Ekonomik modeli yeniden tasarla (35 → 65)
- Kaspa emisyon eğrisini **kopyalama**: 2026'da ömrünü doldurmuş. Bunun yerine: uzun bir
  **tail emission** (Bitcoin-Litecoin değil, Monero/Grin tarzı sonsuz-ama-azalan) ile güvenlik
  bütçesini kalıcı kıl.
- **Hazine:** "Sıfır VC, sıfır ön madencilik" ile **çelişmiyor**: blok ödüllerinin küçük bir
  yüzdesi (%5–8) geliştirme fonuna — bu, tam fair launch ile uyumlu ve Kaspa'nın yaptığı da
  bu. Aksi halde GKR seviyesi Ar-Ge finanse edilemez.
- **Pass modelinin parametrelerini spec'e koy:** duplex overhead, token-inference ratio ve
  üç rejim (Bitconia / Fortessia / Duplexia) için ağın hangi rejimde çalışacağını modelle
  (arXiv 2606.06700).

### 4.4 Mühendislik spec'leri (45 → 70)
- **Difficulty adjustment** algoritmasını tanımla (matris boyutu n + k tolerated başarısızlık).
- **Veri kullanılabilirliği:** Matrisler için commitment + sublinear opening (ör. Merkle root
  + sumcheck ile random-point açılımı); validator'ların n² veriyi indirmesini engelle.
- **PQ stratejisini güncelle:** Lattice spekülasyonu yerine **hash-tabanlı folding (Arc, CRYPTO
  2025)** + hazır STARK'lar; imzalar için Dilithium/Falcon.
- **Teşvik-uyumluluk:** GHOSTDAG tx-seçim saldırılarını (2109.01102 / 2305.16757 / ACNS'25)
  DAG görev ataması için ele al; madenci havuzu eğilimine karşı protocol-level önlem.

### 4.5 Hukuk + şeffaflık (20 → 50)
- "AI'ya endeksli token" ifadesini hukuki danışmanla yeniden yaz; Howey/ TR lisans rejimi
  analizini belgeye koy. Madenciliğin ve fair-launch promotion'ın TR'deki durumu.
- Faz 1'e **güvenlik modeli + görev-pazarı spec'i**; Faz 2'ye formal audit + ekonomik simülasyon.

### 4.6 Düzeltme sonrası tahmini puan
40+70→teknik-güvenlik ≈ 70, ekonomi 65, piyasa/farklılaşma 55 (HadAgent'e fark yaratmak gerekir),
mühendislik 70, hukuk 50, isim 50 ⇒ **ağırlıklı ≈ 64/100**. Geriye kalan ~36 puan, sadece
**çalışan bir testnet + bağımsız güvenlik denetimi + gerçek fayda-talep kanıtı** ile gelir — yani
kâğıtla değil, kanıtla.

---

## 5. Sonuç

KÖK Network, **doğru problemi, yanlış araçla** çözüyor. PoW enerji israfı (204 TWh), PoS
oligarşisi ve AI compute kıtlığı 2026'da da gerçek sorunlar; ve "faydalı iş" araştırma
hattı canlı (Pass 2026, SNARKChain 2025–26, HadAgent 2026). KÖK'ün içgüdüleri (asymmetric
verification, crypto-agility, fair launch, DAG paralelliği) sağlam.

Ama **matris çarpımı, PoUW için teknik olarak yanlış problem**: yapısal-matris saldırısına
açık, ispat overhead'i faydayı boğuyor, kayan nokta ile exact-arithmetic arasında çözülmez bir
gerilim var ve veri kullanılabilirliği 10 BPS'lik bir DAG'da patlıyor. Üstelik "paradigm shift"
Eylül 2026 itibarıyla **HadAgent tarafından zaten yayımlanmış durumda** ve ekonomi tarafı
(Kaspa emisyonu tükenmiş, hazine yok) ilk günden çıkmaz.

**Karar:** Revize et. Pivot önerisi: **(1)** faydalı işi "ispat üretimi" (SNARKChain) veya
"deterministic re-execution" (HadAgent) olarak tanımla; **(2)** güvenlik bağlamını (zincir +
madenci kimliği) ispatın içine göm; **(3)** tail emission + küçük geliştirme hazinesi ile
emisyonu 2026 gerçeklerine uydur; **(4)** hukuki çerçeveyi ekle. O zaman 37 → ~64; gerisi
kanıtlara bağlı.

---

## 6. Güncellilik Analizi: Kâğıt "en iyilenmiş" durumda mı?

**Hayır — vintage uyumsuzluğu var:** kâğıt 1979–2024 vintage kriptografiyi (Freivalds 1979,
sumcheck 1990/1992, GKR 2008/2015, lattice folding 2024, GHOSTDAG 2021–2023) anıp onu
"2025–2026 kırılması" olarak sunuyor. Oysa projenin kaderini belirleyen 2025–2026 işlerinden
**hiçbirini** içermiyor:

| 2025–2026 gelişmesi | Kâğıdın durumu |
|---|---|
| Pass — PoUW ekonomisi, 3 rejim (Haz. 2026, 2606.06700) | Yok |
| SNARKChain — zincir bütünlüğü + madenci kimliği gömme zorunluluğu (Ekim 2025, 2510.09729) | Yok — tam da bu hataya düşülmüş |
| HadAgent — Proof-of-Inference konsensüsü, çalışan prototip (Nis. 2026, 2604.18614) | Yok — "paradigm shift" artık yeni değil |
| SaTML — ispat overhead'i milyar-parametrede yüzlerce sn (Mart 2026, 2603.19025) | Yok — premsini çürütüyor |
| Jolt Atlas — ONNX için lookup-arg zkML (Şub. 2026, 2602.17452) | Yok — kullanması gereken yığın |
| Arc — hash tabanlı, PQ, sınırsız-derinlik folding (CRYPTO 2025, ePrint 2024/1731) | Yok; "Lattice-Jolt" = **gerçekte olmayan standart** |
| **ω < 2.371177, AlphaEvolve ile (17 Ağu. 2026, 2608.16884)** | Yok — işin zorluk varsayımı AI ile aşınıyor |

**Tarih teşhisi de yanlış:** "15 yıl önce madencilerin matris çarpması, diğer düğümlerin hızlı
doğrulayamaması yüzünden engelliydi" iddiası **yanlış** — Freivalds (1979) zaten O(n²) olasılıklı
doğrulama veriyordu; sumcheck/GKR bunu log-round'a indirir. Gerçek tarihsel engeller şunlardı ve
hiçbiri kâğıtta yok: (a) işin **bloğa/madenciye bağlanmaması** (precompute/replay), (b) **görev
pazarı ve sybil**, (c) serbest seçilen görevlerin **worst-case zor olmaması** (structured
matrisler), (d) **prover overhead'i**. Kâğıdın "çözüldü" dediği şey, asıl çözülmesi gerekeni
ıskalıyor; bu yüzden §2'deki ölümcül boşluklar ortaya çıkıyor.

**Sonuç:** Kâğıt 37/100'de; araştırma-temelli kâğıt tavanı ~85. Yani "güncel" olan sadece etiketler,
içerik 2021–24'te takılı. Boşluklar somut ve kapatılabilir — `PROJE_KAGIDI_V2.md` bunu yapar.

---

## 7. Migration Analizi: Yeni bir kriptografik gelişme gelirse göç kolay mı?

Kâğıdın "on-chain sinyal + WASM modülü = sıfır kesinti, hard-fork yemez" iddiası **teknik olarak
yanlış**: konsensüs kuralı değişimi *tanımı gereği* fork'tur; en iyi durum **threshold aktivasyonlu
yumuşak göç** (çift-doğrulama penceresi) olabilir. Doğru cevap katmanlara bölünmeli:

| Katman | Zorluk | PVI kurtarır mı? |
|---|---|---|
| **A. Doğrulama/ispat primitive'i** (GKR → başka proof system) | **Orta-kolay** | **Evet, disiplinle:** statement schema ile proof system'i versiyonlandır (`proof_system_id`, `statement_schema_id`, `activation_height`); eski+yeni N blok çift-doğrulama, sonra emekli; her WASM verifier'ın **formal doğrulaması + determinizm spec'i + cross-impl test vector'leri**; madinciye **6–12 ay önceden sinyal**. Kritic numara: *sadece verifier* değişiyorsa **iş fonksiyonunu sabit tut** — ancak o zaman "seamless" doğrudur. |
| **B. İş fonksiyonu** (madencinin ne hesapladığı) | **Zor / siyasi** | **Hayır.** Değişim = madencinin yazılım+donanım+operasyon sermayesini sıfırlar. Validator'ın "kolay"ı madencinin iflasıdır. Ampirik taban oranı: BTC SegWit (2017) → yıllarca savaş + chain split (BCH); ETH merge (2022) → ~8 yıl + ETC. **Konsensüs migrasyonu teknik değil siyasi bir olaydır.** |
| **C. İmzalar & PoW hash'i** — asıl merak edilen iki göç | **Zor** | **En az.** İmza değişimi her UTXO'yu etkiler (uzun kuyruk); PoW hash'i değişimi madincileri sıfırlar → en patlayıcı değişiklik. (Not: 2026 çözümü **ZK-ACE**, arXiv 2603.07974 — imza nesnesini chain dışına taşıyan identity-bound ZK yetkilendirme; Circle STARK backend: 14.5 ms prove / 1.1 ms verify / ~107 KB proof; in-circuit PQC imza doğrulamasına göre 500–2300× küçük.) |
| **D. Zorluk varsayımının çöküşü** — **asıl risk** | **WASM ile imkânsız** | **Hayır.** Yapısal-matris saldırısı: iş O(n³)→O(n). **AI bizzat üsteli küçültüyor:** ω < **2.371177** (17 Ağu. 2026, AlphaEvolve; çizgi Duan 2022 → Williams 2024 → Alman 2025 → 2026); pratikte Strassen (2.807) ve ML-keşifli algoritmalar zaten sub-cubic. Matmul ASIC/TPU'nun tam işi → donanım merkeziyetsizleşmesi günlerce çöker. Hiçbir modül "matris çarpımı zor kalmaya devam edecek" varsayımını değiştiremez. |

**Teşhis:** Kâğıdın crypto-agility içgüdüsü doğru, ama **yanlış katmana** yapışmış. Geleceğe dayanıklı
ancak şu anlama gelir: **zorluğu yapısal** olan bir iş fonksiyonu seç (ispat üretiminin kendisi —
SNARKChain; orada "iş" = "doğrulanabilirlik" ve göç yüzü tam PVI'nin kapladığı A katmanına denk
gelir, D katmanı tehlikesi ortadan kalkar). Aksi halde PVI en fazla %20'lik katmanı kurtarır.

---

## 8. Rekabet Güncellemesi: Gerçek Rakip Dynex Değil, **Pearl Network**

İlk değerlendirmede (§0/§2) "faydalı PoW L1" kategorisinin en yakın örneği olarak Dynex'i
(3 gün önce kendi ATL'inde, mkt cap $128 bin) gösterdim — bu, **pazardaki ceset** için doğrudur.
Ama Pass'ın ekonomi makalesinin (arXiv 2606.06700) tam metni, asıl rakibi ortaya çıkardı:

- **Komargodski & Weinstein, "Proofs of Useful Work from Arbitrary Matrix Multiplication"**
  (IACR ePrint 2025/685; 2025-04-15, 3 revizyon, son 2025-12-08): madencinin **kendi girdisini
  seçtiği** permissionless ayarda MatMul için **1+o(1) overhead** ile **prescribed hardness**.
  **KÖK v1'in Freivalds denklemi `A(Br)==Cr`, KW'nin açıkça "O(1)-factor overhead her görev için
  trivial ama işe yaramaz" dediği construction'dur.** Yani §2/iddia-4'teki "yapısal-matris
  saldırısı" eleştirisinin resmi adı budur — ve **KW bunu çözmüştür**.
- **Pearl Network**: KW'nin üzerine inşa edilen blockchain ("currently under construction");
  Pass'ın danışmanlık yaptığı Pearl Research Labs'ın ekonomi çerçevesi.

**Bu, değerlendirmeyi iki yönde günceller:**

1. **v1'in suçu daha keskin:** sadece "görev seçimi saldırısına açık" değil, ** literatürde
   'işe yaramaz' olarak işaretlenmiş spesifik bir construction'ı kullanıyor**. Çözümü de var,
   ama o çözüm **başka bir ekibin çekirdeği**.
2. **Farklılaşma zorunlu:** "Matris çarpımı PoUW" artık **Pearl'in alanı**. Bir KÖK projesi
   ancak şu katmanlarla var olabilir: GHOSTDAG paralelliği + memoryless difficulty + formal
   doğrulanmış PQ agility düzlemi + premium SNARK hizmet katmanı + tail emission ekonomisi.
   `PROJE_KAGIDI_V2.md` (2026-09-19 KW güncellemesi) tam olarak bu revizyonu yapar.

**Puan etkisi:** v1'in "Farklılaşma" alt puanı (30/100) yerinde kalır — aslında Pearl'in
varlığıyla **daha da zordur**; ama v2'nin farklılaşma stratejisi (§12 tablosu) bu gerçeğe
dayanır. Ayrıca §2/iddia-4'ün "çözülmez" dediği gerilim (FP vs exact field) KW'nin 1+o(1)
overhead'i ile büyük ölçüde aşılır; S2 hizmet katmanında kalan kısmı ~36 ay horizonlu
native-FP precompile (arXiv 2606.05433) çözer. **Dürüst olan budur: v1 yanlış, ama vizyon
yanlış değildi — sadece sahibi vardı.**

---

### Kaynaklar (19 Eylül 2026 itibarıyla canlı erişildi)
- arXiv 2606.06700 — Pass, *The Economics of Proof-of-Useful-Work* (Haz. 2026)
- arXiv 2510.09729 — Oleksak ve diğerleri, *SNARKChain: PoUW with General-Purpose SNARK Marketplace*
- arXiv 2604.18614 — Jimenez ve diğerleri, *HadAgent: Proof-of-Inference Blockchain Consensus* (Nis. 2026)
- arXiv 2603.19025 — Anchuri ve diğerleri, *Lightweight Cryptographic Proofs of Inference* (SaTML 2026)
- arXiv 2603.20421 — Badash, Boneh, Komargodski, Srivastava, *Hawkeye: GPU-Level Non-Determinism* (MLSys 2026)
- arXiv 2606.16146 — Mo ve diğerleri, *NTT vs SumCheck in Zero-Knowledge Systems* (Haz. 2026)
- arXiv 2504.12217 — Zhang ve diğerleri, *zkVC* (DAC 2025)
- arXiv 2607.21162 — Liang ve diğerleri, *GKR Protocols for Transformer Inference* (Tem. 2026)
- arXiv 2501.05500 — Wang, *A Survey of Interactive Verifiable Computing* (Oca. 2025)
- arXiv 2405.19027 — Cao ve diğerleri, *Optimization-based Proof of Useful Work* (rev. Ağu. 2026)
- arXiv 2209.03865 — Hoffmann, *Challenges of Proof-of-Useful-Work*
- arXiv 2109.01102 / 2305.16757 / 2501.10888 — GHOSTDAG incentive & selfish-mining saldırıları
- IACR ePrint 2024/1731 — Bünz, Mishra, Nguyen, Wang, *Arc* (CRYPTO 2025)
- IACR ePrint 2018/104 — Sompolinsky & Zohar, *PHANTOM* (Kaspa whitepaper)
- arXiv 2608.16884 — Dupont ve diğerleri, *Matrix Multiplication Exponent + AlphaEvolve* (Ağu. 2026)
- arXiv 2603.07974 — Wang, *ZK-ACE: PQ On-Chain Authorization* (May. 2026)
- arXiv 2606.04311 — Avigad ve diğerleri, *Formal Verification of the S-two AIR* (Haz. 2026)
- arXiv 2609.15020 — Takahashi, Jana, Yang, *ZEBRA: zkVM Constraint Verification* (Eyl. 2026)
- arXiv 2606.05433 — Peigné, Nguyen, Wang, *ZK Verification for Frontier AI Training* (Haz. 2026)
- arXiv 2605.25493 — *ZK-Tracer: zkVM Frontend Accelerator* (May. 2026)
- arXiv 2607.11466 — Wei ve diğerleri, *Prezta: zkVM Zero-Trust Authorization* (Tem. 2026)
- **IACR ePrint 2025/685 — Komargodski & Weinstein, *Proofs of Useful Work from Arbitrary Matrix
  Multiplication*** (2025; 3 revizyon, son 2025-12-08) — v1'in Freivalds construction'ının
  "trivial ama işe yaramaz" olduğu yer; **Pearl Network** bunun üzerine inşa ediliyor
- arXiv 2505.21685 — *Proof of Work With External Utilities* (May. 2025)
- arXiv 2512.13666 — *SEDULity: Proof-of-Learning* (rev. Haz. 2026)
- arXiv 2404.09005 — *Proof-of-Learning with Incentive Security* (rev. May. 2026)
- CoinGecko API — BTC, KAS, TAO, RNDR, AKT, DNX (19.09.2026)
- Digiconomist — Bitcoin Energy Consumption Index (19.09.2026)
- blockchain.info — Bitcoin hashrate (19.09.2026)

---

## 9. ★ GÜNCEL PUAN — v1 (37/100) vs v2 (kağıt tavanı 85/100) — 20 Eylül 2026

> Bu doküman v1'i değerlendirdi (**37/100**). Sonraki oturumlar v1'i tamamen yeniden
> tasarladı (`PROJE_KAGIDI_V2.md` + `KOK_V2_TEKNIK_SPEC.md`). Aşağıda **aynı rubrik** ile
> v2'nin **kâğıt-üzerinde** puanı ve **kanıt gereği** kalan açık fark.

| Kategori | Ağırlık | **v1 puan** | **v2 puan (kâğıt)** | Temel gerekçe (v2) |
|---|---:|---:|---:|---|
| **Teknik doğruluk & güvenlik modeli** | %40 | 40 | **89** | KW G katmanı (LLM-bağımsız PDF doğrulaması: Assumption 6.4'ün output-size gerekçesi KW'de birebir, Lemma 6.5, α=o(1); jackpot policy TV-11..TV-14 çalışıyor); G/U ayrımı Demirel Thm 2'yi *construction ile* sağlar; ctx binding T-A2; fallback §A.9; **kalan −16: 2 bağımsız insan kriptograf incelemesi YOK — Demirel CEVAP VERDİ VE RET ETTİ ($215/saat + funding'den bağımsız ödeme şartı, 2026-09-23; cevap + kullanıcı kararı `EPOSTA_DEMIREL_TESEKKUR.md`'de; erteleme argümanı DAİRELİ olduğu için makale artık onu yapmıyor, `STAGE4_HUMAN_MONEY_GAP.md`). ~~GHOSTDAG parent-set prototip dışı~~ KAPANDI (ghostdag_proto.py TV-22..TV-26, Kaspa k=18); ~~mergeset sapması 572 (TV-59)~~ KAPANDI 2026-09-23 Aşama 1.1 (mergeset ∩ past(B), 572→0, probe tersine); ~~replay TV-25 geri çekme~~ KAPANDI Aşama 1.2 (ctx kimlikte, T-A2 implemented); FP8 noise modeli YAZILDI (TV-27..TV-30, reversal doğrulandı + DELTA 0.5→0.06 spec düzeltmesi); ~~toy field (q=97) bir YAPISAL limit gibi görünüyor~~ — TV-71'de PARAMETRE seçimi olduğu ÖLÇÜLDÜ, TV-76'da 256-bit asal + 32-byte digest ADIM 1-2 olarak İNŞA EDİLDİ, TV-78'de FRI RECURSION ADIM 3 İNŞA EDİLDİ (olumsuz sonuç: sibling inversion bir preimage problemi olduğu için SADECE field büyütmek kapatmazdı; digest genişliği kapatır)** |
| **Tokenomics & ekonomi** | %20 | 35 | **82** | Pass modeli PDF'ten teyit (Thm 2 Cost=PR/2 her rejimde, ν→(1−ν)PR/2; Thm 3 p=(α/(1+θ))e); `pass_sim.py` Pearl canlı ağını %5,8 içinde yeniden üretiyor; tail emission R_∞ (Pearl'in 1/t²'si ve Kaspa'nın tükenmiş eğrisine karşı); hazine %5–8. **Kalan −18: gerçek ödeyen görev talebi ölçülmedi (φ>0 kanıtı yok), canlı güvenlik bütçesi yok; ~~TV-17'nin ekonomik ağırlığı açık~~ KAPANDI (bond_margin_proto.py TV-31..TV-33: margin = B_out − fee R²=1.0000, fee-capped slash düzeltmesi)** |
| **Piyasa / farklılaşma / öncül sanat** | %15 | 30 | **86** | Pearl'in **kendi** E-gap itirafı (Polymath Ek.1: "marginal cost ~0... Is it 0? infinity?") tezimizin birincil doğrulaması; iki gerçek fork'tan migration sınıflandırması; FP iki-yol tablosu; §12.1'de **6 rakip-hamle senaryosu** (her biri: olasılık + tehdit seviyesi + kalıcı farklılık); §8.1 pazar boyutu artık **kaynaklı somut rakamlarla** (Nvidia FY2026 $215B geliri, 3 yılda 8 kat; Q2 FY27 $96.2B +%106; $100B/10GW OpenAI), **permissionless alt-küme bilinçli olarak 'ölçülmedi'** (F3a). **§8.1 artık somut pazar boyutu sunuyor: Nvidia FY2026 $215B geliri (3 yılda 8 kat: 26.9→60.9→130→215), Q2 FY27 $96.2B +%106, $100B/10GW OpenAI yatırımı** — hepsi NVIDIA'nın kendi raporladığı rakamlar. *** 2026-09-21 ADOPTION ÇALIŞMASI (paper §11b, `adoption_econ.py` TV-35/36/37): ***
"compute ucretsiz" iddiasi MATEMATIKSEL OLARAK YANLIŞ (TV-35: madincinin hardware'i block reward ile odemis ama o reward KAZANAN PIYANGO BILETI satin alir; satisa giden compute madencilige giden compute DEGIL). Dogru versiyon: tax incidence — KW kernel'i ile ayni is olcutunde (α~1.3) security harcamasi compute'u SÜBVANSE EDER. *** Crossover token fiyati: launch'ta $10, tail'de $250 (TV-37) — token DEĞER KAZANDIKÇA madencilik compute satisini geçiyor; utility'nin fiyat kazanma penceresi ERKEN pencere. *** TV-36: empty-block denge GERÇEK ve EMİCİ (break-even altında hiçbir tohum kaçamıyor); Pearl bunun ÖLÇÜLMÜŞ hali (24 EH/s, 0 useful compute). *** Yol haritasına F0 (talep keşfi) eklendi: 10 görüşme + 1 imzalı niyet mektubu, kill-criteria = F3a sonunda 1 gerçek ödeyen task yoksa pure-PoW fallback'e dönüş (§A.9). *** F0 bir ÇALIŞAN ARAÇ oldu (`f0_demand_discovery.py`): rubrik + fiyat testi + append-only log. *** Kullanıcının "neden kullansınlar?" sorusu artık 2 nedende (a: kanıtlanabilir ucuz, b: izin-verilmeyen tek yer) ve dekorasyon olarak işaretlenen yesil/enerji retoriği Pearl'in sıfırıyla çürütüldü. *** **Kalan −15: hâlâ ÖLÇÜLMEMİŞ gerçek talep — ama artık bu bir KUSUR DEĞIL, F0'ın TANIMLI HEDEFİ; crossover senaryodan bağımsız bir sayı** |
| **Uygulanabilirlik & mühendislik** | %15 | 45 | **80** | Çalışan prototipler: `u_layer_prototype.py` (TV-5..TV-10), `g_layer_tests.py` (TV-1..TV-4, TV-11..TV-14, RT-1..RT-3, 12,8s), `pass_sim.py` (regression-checked); retarget formül düzeltildi + medyan filtre. *** 2026-09-21: whitelist governance §A.11'de SOMUT 5 adımla TANIMLANDI; §10.2 bütçe/timeline YAZILDI ***. *** **2026-09-23 AŞAMA 1-3 (kod ile kapatıldı, puan ARTMADI):** mergeset sapması TV-59 **572→0** (probe tersine çevrildi, sessiz dönüşü önler); replay TV-25 geri çekmesi KAPANDI (ctx blok kimliğine bağlı, T-A2 artık implemented); settle-then-slash + slash-then-settle her iki sıra GUARDED; VRF pk artık sk'nin digest'i (TV-56, verifier limiti dürüstçe yazılı); E-gap bağlaması TV-77 **4/4** (TV-72'nin φ=0 nedenini ortadan kaldırdı, φ>0 iddia EDİLMİYOR); FRI recursion TV-78 **3/3** (ölçüm sırasında x-uzayı fold hatası yakalandı, u=x²'de düzeltildi). *** **2026-09-24 ROUND-5A/5B/5D/5E/5F (kod ile kapatıldı, puan ARTMADI):** FRI'nin CHALLENGE'i PROVER'IN KENDI RNG'sinden geliyordu — FRI'nin tek seslenme kaynagi seslenen taraftan geliyordu, yani seslenme = SIFIR; Fiat-Shamir yapildi (alpha, prover'in meydan öncesi commit etmek zorunda oldugu polinomun digest'i). E-gap baglamasi (TV-77) COMMITMENT STRING'ini bagliyordu, COMPUTATION'i DEGIL — ÖLÇÜLDÜ: commissioned [[2,3],[4,5]] (tile 26), madenci [[2,3],[4,6]] (tile 30) kullanilarak serve ediliyordu ve VERIFY ACCEPT ediyordu; TV-82 olarak düzeltildi (verifier artik committed programdan tile degerini tek referans hesaplamasiyla yeniden türetiyor). *** **Kalan −20: toy sınırlar (q=97 hâlâ — TV-76 adım 1-2 İNŞA EDİLDİ ama FRI hâlâ q=97 üzerinde; VRF gerçek ECVRF değil; FP8 IEEE-754 değil — ARAŞTIRMA prototipleri, üretim iddiası değil); gerçek dağıtım ekibi/yol yok (finanse değil). VE: bu kapatılanların HİÇBİRİ adı veya parası riskte olan bir taraf tarafından yapılmadı — puan 83.65'de TUTULDU (kullanıcı kararı)** |
| **Hukuki & uyum** | %5 | 20 | **75** | *** 2026-09-21: hem EU hem US artık KAYNAKLI. *** MiCA resmi metin (EUR-Lex, Article 3(9) düzeltmesi) + *** SEC v. Ripple TAMAMEN çözüldü: Torres 13.07.2023 (programmatic borsa satışları menkul kıymet DEĞİL), 07.08.2024 $125,035,150 ceza, 07.08.2025 itirazlar geri çekildi (DAVA KAPANDI), *** 17.03.2026 SEC yorumu XRP'i BTC/ETH/SOL/XLM ile "dijital emtia" olarak belirledi *** — ama "işlem koşullarına göre yine yatırım sözleşmesi olabilir" uyarısı da var. Bu, fair-launch/no-premine/no-investor tasarımının *** yasal nedenini *** oluşturuyor (premine/investor round = menkul kıymet). §10.2 bütçe/anonimlik. **Kalan −37:** resmi menkul kıymet görüşü yok (avukat değiliz), yargı seçimi kararı yok. *** AMA MiCA white-paper BEYAN METNI artık yazıldı (paper §9, regulation'ın kendi kelimeleriyle 4 zorunlu beyan) — legal vehicle (şirket) yok, içerik var. *** | (2026-09-21, EUR-Lex):** utility-token tanımı makalede verbatim alıntılandı; KÖK token'ının (9) altına girmediği (madenci ödülü = "value or a right") dürüstçe belirtildi; white-paper beyan yükü çıkarıldı. §10.2 bütçe/anonimlik defteri eklendi. **Kalan −60 → −20 (2026-09-23):** ABD Howey analizi artık İÇ kaynaklı DEĞİL. Üç gün önce "CourtListener'de kayıt yok, sec.gov 403" diye yazılan yerde, doğrulama ajanı CourtListener'ın PDF host'unun ve API'sinin çalıştığını keşfetti — bu bir RETRİEVAL problemiydi, bir fakt hatası değil. 4/4 Ripple/SEC iddiası BİRİNCİL KAYNAKLARLA doğrulandı (SDNY 1:20-cv-10832 doc 874/973/989, 2d Cir. 24-2648/24-2705, 91 FR 13714). Yargı seçimi ve resmi avukat görüşü hâlâ yok (−20). |
| **İsim / pazarlama / opsec** | %5 | 40 | **60** | **§12.2 ile düzeltildi:** etimoloji hatası ("Kök Tengri" homograf karışıklığı) düzeltildi; "kök = root/origin" doğru kullanıldı; **opsec artık iddia değil mevcut durum** ("kullanıcı/yatırımcı yok" — kanıtlanamaz bir iddia olarak değil); anonimliğin bütçe olayında bırakılacağı belirtildi. **Kalan −40:** isim hâlâ bir Türkçe kelime (evrenellik iddiasıyla gerilim var, ama artık telafi ediliyor). |
| **TOPLAM** | %100 | **37** | **≈ 83.65/100 (kâğıt)** — *38.25 → 37 → 74.8 → 76.6 → 78.6 → 79.6 → 80.6 → 80.9 → 81.85 → 82.65 → 83.05 → 83.65* | |

**★ Kritik dürüstluk notu — "85 tavanı" hâlâ geçerli:** v2 kâğıtta ≈79 puanda; kalan
**21 puanın ~15'İ KÂĞIT HATASI DEĞİL — EMPİRİK KANIT GEREKTİRİR**: bağımsız kriptograf
incelemesi (−18'nin çoğu), canlı ağda φ>0 (gerçek görev talebi), gerçek güvenlik bütçesi,
denetim raporları. **Mükemmel bir kâğıt çalışan bir zincire eşit değildir** — V2 §11 md.6'nın
ta kendisi. **Kalan ~8 puan saf kâğıt işi:** hukuk (−3,75), pazar senaryoları (−3,3), isim (−0,25). ~~parent-set prototipi~~ KAPANDI. **Bu oturumda kapanan 3 isimli boşluk:** GHOSTDAG parent-set (TV-22..TV-26), FP8 noise modeli (TV-27..TV-30 — NEGATİF: reversal doğrulandı, σ_min zorunlu, DELTA 0.5→0.06), TV-17'nin ekonomik ağırlığı (TV-31..TV-33). 76→77: küçük artış, çünkü en büyük kalan boşluklar (insan kriptograf incelemesi — Demirel'e GÖNDERİLDİ, cevap bekleniyor; canlı φ>0 talebi) bu oturumda ellenmedi.


**v1 → v2'nin puan sıçramasının asıl nedeni (37 → 77):** teknik kategorideki
**+42 puanın tamamı**, "görev-seçim ve blok-bağlama saldırıları çözülmemiş" eleştirisinin
KW + G/U + ctx binding + jackpot policy ile **kapatılmasından** gelir. Yani §4.1'in
"en büyük delik" dediği şey artık delik değil — **ama kanıtlanmış değil, yalnızca
tasarlanmış.** İşte tam da bu yüzden Faz 2'nin zorunlu kapısı insan kriptograflardır.

**Pearl referansı bağlamında:** Pearl'in canlı ağı (24 EH/s, 320 bin GPU) kâğıt puanı
alamaz — **kanıtı var ama E-gap'i mimariye yedirmemiş** (kendi itirafı). KÖK v2 ters
durumda: **mimari doğru ama kanıt yok.** İkisi de 100/100 değil; Pearl ~55 (kanıtlı ama
yanlış mimari), KÖK v2 ~76 (doğru mimari ama kanıtsız). **Yarış kararlı değil — KÖK'ün
kazanma yolu Faz 2'yi gerçekten yapmaktır.**
