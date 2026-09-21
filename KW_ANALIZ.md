# KÖK v2 — Bağımsız Kriptografik Analiz: KW/cuPOW Varsayımı

**Tarih:** 19 Eylül 2026 · **Hedef:** ePrint 2025/685 = arXiv 2504.09971 (Komargodski,
Weinstein, "Proofs of Useful Work from Arbitrary Matrix Multiplication", v4 2025-11-13)
· **Soru:** KÖK v2'nin G katmanı bu conjecture'a dayanıyor — kırılabilir mi?

> **Yöntem:** KW'nin tam metni okundu (ar5iv). Bu doküman, KW'nin kendi güvenlik
> argümanını olduğu gibi aktarır, sonra **bağımsız olarak** deliklerini arar. Sonuç:
> conjecture beklenenden **daha sağlam**, ama beklenen yerde **değil**; asıl zafiyet
> kriptografide değil, **faydada** (zaten Pearl'de ölçüldü).

---

## 1. Construction (olduğu gibi)

```
Encode_r(σ, A, B):  σ ↦ (E_L,E_R,F_L,F_R);  E = E_L·E_R, F = F_L·F_R   (rank-r gürültü)
                    A' = A+E,  B' = B+F
Madenci:            C' = A'·B' yıgın blok algoritmasıyla; transcript tr = tüm (n/r)³
                    ara r×r bloklar C'^(ℓ)_{i,j} = Σ_{ℓ'≤ℓ} A'_{i,ℓ'}·B'_{ℓ',j}
                    z = O(tr)  (veya Remark 2.1: her bloğu ayrı hash'le)
Decode_r(σ, C'):    C'' = (A·F_L)·F_R + E_L·(E_R·(B+F_L·F_R));  C = C' − C'' = A·B
```

- **Parametreler:** r ≪ n (ör. r = n^0.3); alan 𝔽_q; σ λ-bit seed; ε başarı olasılığı eşiği.
- **Dürüst maliyet:** α(t) = t_MatMul(n)·(1+o(1)) — Encode/Decode yalnızca O(n²r) ek.
- **Pearl'in deploy ettiği hali (Basu 2606.04819'dan):** int8 değer aralığı {−64..64},
  blake3 tabanlı noise, rank-R chunk'lar, XOR tile-reduce + jackpot hash; ** Remark 2.1'in
  per-tile varyantı**.

## 2. Güvenlik argümanının üç ayağı (KW'nin kendi ifadesiyle)

| # | Ayak | Statü |
|---|---|---|
| **(a)** | σ öngörülemez (ROM) → E,F önceden bilinemez → preprocessing işe yaramaz | **Kanıtlanmış** (ROM'da trivial) |
| **(b)** | E, F **tek başına üniform rank-r** (Lemma 6.5) → her r×r blok marjinal olarak üniform → tek bir ara blok hesaplamak = rastgele r×r MatMul = Ω(r^ω) | **Kanıtlanmış** (Lemma 6.5 + Claim 6.6) |
| **(c)** | **Tüm** ara değerleri hesaplamanın maliyeti Ω(n^(ω_r+1)/r) (Varsayım 6.4) | **Conjecture** — ama KRİTİK: KW kendisi "the number of bits needed to write down all intermediates – Θ(n³/r) – is always a lower bound... and ω_r = 2 for sufficiently small r" diyerek **çıktı-boyu alt sınırından dolayı neredeyse otomatik** olduğunu söyler |

**Korelasyon itirafı (KW, §2):** "the above argument does not work for computing all of the
intermediates because they are correlated (E and F are only rank r). However, recovering the
correlations requires essentially solving a linear system of equations which, we conjecture, is
as difficult as multiplying matrices."

## 3. Bağımsız analiz: Varsayım 6.4 nerede gerekli, nerede değil?

### 3.1 Önemli gözlem — kök hesaplama çıkıdan daha ucuz olamaz
PoW koşulu `z = O(tr)` (veya Merkle kökü) altında olduğunda, **saldırganın transkripti
materyalize etmesi gerekmez** — yalnızca hash'ini ister. Bu, Varsayım 6.4'ün (çıkıdı boyu
Θ(n³/r) alt sınırı) **uygulanmadığı** yerdir. O halde gerçek güvenlik şuna dayanır:

> **(Gerçek) Varsayım:** Bir hash fonksiyonu (ROM) altında, rank-r gürültülü bir MatMul
> transkriptinin **Merkle kökünü** (veya per-tile hashlerinden birini) hesaplamanın maliyeti,
> transkripti hesaplamanın maliyetine asimptotik olarak eşittir.

**Bu varsayım Varsayım 6.4'ten farklıdır** ama standart Merkle argümanıyla **çok güçlüdür**:
kök, tüm yaprakların hash'ine bağlı olduğundan ve hash tek yönlü olduğundan, kökü hesaplamak
için her yaprağı değerlendirmek gerekir (yapıdan bağımsız olarak — yapraklar yalnızca O(nr)
rastgele değerlerin deterministik fonksiyonu olsa bile). **Sonuç: (c) aslında gerekli değildir;
(a)+(b)+Merkle yeterlidir.** Bu, KW'nin küçük bir gerekçeleme boşluğudur ama **sonuç sağlamdır**.

### 3.2 Per-tile varyantı (Remark 2.1 = Pearl'in jackpott'u) — matematiksel denge
- Dürüst: 1 MatMul = maliyet n³·r^(ω−3), verir (n/r)³ deneme → **deneme/FLOP = r^(−ω)**, n'den
  **bağımsız**. ✓ Madenci matris boyutunu serbest seçse bile deneme yoğunluğu sabittir.
- Saldırgan: tek bir tile = marjinal üniform iki r×r bloğun çarpımı → maliyet ≥ Ω(r^ω)
  (ayak (b)). Dürüst ile aynı. ✓
- **Zorluk ayarı güvenli:** difficulty, blok sayısının fonksiyonu olabilir; matris boyutu
  serbestliği dengeyi bozmaz (r protokol parametresi, sabit).

### 3.3 Yapısal saldırı sınıfının çürütülmesi (v1'e karşı tablo)

| Saldırı | v1 (düz Freivalds) | KW | Sonuç |
|---|---|---|---|
| Sparse/permutation A (iş O(n³)→O(n)) | ✓ çalışır | A+E marjinal üniform → işe yaramaz | **KW kazanır** |
| A=B=0 (kolay girdi) | ✓ | transcript hala (n/r)³ üniform tile ister | **KW kazanır** |
| Precompute/replay (σ bilinmeden) | kısmen | σ blok-bağımlı (ctx) → imkânsız | **KW + ctx kazanır** |
| Korelasyondan kısayol (rank-r gürültü) | n/a | X_i·(Σ Y_{ℓ'}Z_{ℓ'})·W_j = aynı asimptotik (KW §6.5'in kendisi gösterir) | **denklik** |
| Trapdoor matrix (VZ25 2502.13065 / BN25 2502.13060, LPN) | n/a | E,F σ'dan türetilir, saldırgan trapdoor **yerleştiremez** | **KW kazanır** (KW'nin reddini BAĞIMSIZ olarak doğruluyorum) |
| FMM ilerlemesi (ω < 2.371339 [ADV+24 2404.16349]; AlphaEvolve 2.371177, 2026) | n/a | Dürüst ve saldırgan **aynı** algoritmayı kullanır → oran korunur; yalnızca "iş birimi" kalibrasyonu değişir | **ekonomik, kriptografik değil** |
| Kuantum | Grover ✓ (Bitcoin gibi) | MatMul için HHL-benzeri algoritmalar kuantum girişim ister ve klasik hash bulamaz | **Bitcoin-pariti PQ** |

### 3.4 Tespit edilen gerçek teknik zafiyetler (küçük, düzeltilebilir)

1. **Bellek:** bütün-transkript varyantı Θ(n³/r) bellek ister (KW Remark 2.1 itiraf eder).
   Pearl per-tile varyantını seçmiş — **doğru tercih**. KÖK spec'i per-tile olarak sabitle.
2. **ε ve n eşleştirme:** Remark 5.3 — difficulty ya n ya ε ile ayarlanır; **ikisi birden
   serbest bırakılırsa madenci optimizasyonu karmaşıklaşır**. KÖK: **n'yi protokol sabitler,
   ε (target) retarget ile ayarlanır** (Bitcoin'in kuralına birebir uyum).
3. **σ'nın zincire bağlanması:** KW tanımı σ'yı üniform örnekleme varsayar; blockchain'de
   σ = `ctx` (selected_parent ‖ height ‖ ...) **olmak zorundadır** — yoksa bir sertifika
   başka zincir konumlarında yeniden oynatılabilir. **KÖK T-A2 bu boşluğu kapatır.**
4. **Hata büyümesi (pratik):** int8/quantized alanlarda ara değer taşması — Pearl'in
   verify_plain_proof'undaki değer-aralığı kontrolü bunun için; **KÖK 𝔽_q'yu açıkça spec'ler**
   (fixed-point + yayınlanmış hata bütçesi, arXiv 2606.05433 native FP olgunlaşana kadar).

## 4. Sonuç: conjecture'ın statüsü

| Boyut | Değerlendirme |
|---|---|
| **Kriptografik ses (W)** | **SAĞLAM** — (a) ROM + (b) marjinal üniformluk (kanıtlandı) + Merkle/tek-yönlülük. Varsayım 6.4 gereksizce güçlü ifade edilmiş ama gereken zaten daha zayıf ve standart bir varsayımdır. |
| **Worst-case eşitliği** | **EVET** — A=B=0 dahil her girdi aynı maliyeti taşır; v1'in ölümcül açığı kapalı. |
| **FMM/ω dayanıklılığı** | **EVET** — simetrik (iki taraf da aynı algoritma). |
| **PQ** | **Bitcoin-pariti** — Grover karekök avantaj; cebirsel taraf Shor'a düşmez. |
| **Bağımsız doğrulama** | **YAPILMADI** — yukarıdakiler benim (bir LLM'in) okuması; **2 bağımsız kriptografa inceleme Faz 2'nin zorunlu kapısıdır.** Bu doküman onların için bir kontrol listesidir. |
| **Asıl zafiyet** | **FAYDA (E)** — kriptografi mükemmel olsa bile matrislerin kimsenin işi olduğunu certify etmez. **Pearl'de ölçülen φ=0 tam olarak budur.** KÖK v2'nin G/U ayrımı bu yüzden var. |

## 5. KÖK v2'ye etkisi

1. **G katmanı KW'yi olduğu gibi benimser** — per-tile varyantı (Pearl'in yaptığı),
   n protokol-sabit, ε retarget'e bağlı, σ = ctx.
2. **Fallback (spec §A.9) korunur** — ama bu analiz, fallback'in olasılığının **düşük olduğunu**
   gösterir: kriptografik kırılma değil, **pratik mühendislik** (taşma, bellek, difficulty
   saldırıları) ana risklerdir. Fallback gerekli ama senaryo #1 değil.
3. **Olasılık güncellemesi:** "conjecture çöker" riskini **yüksek** → **düşük-orta** olarak
   revize et. Kalan asıl risk **fayda talebi** (spec §11 md.3), kriptografi değil.
4. **Bağımsız incelemenin gündemi:** (i) Lemma 6.5'in marjinal üniformluk kanıtı,
   (ii) per-tile denge hesabının §3.2'deki gibi, (iii) int8 alanında taşma analizi,
   (iv) σ=ctx bağlamasının ROM kanıtına entegrasyonu.

---

### Ek:KW'nin gözümden kaçırdığı (veya okuyucunun bilmesi gereken) bir nüans
KW Abstract'ta "batch of low-rank random linear equations" der ama §2'deki argüman
bunun **MatMul transkriptine** indirgenmesidir; gerçek varsayım (b) ve Merkle'dir. Bu
terminolojik kayma, pearl'in "prescribed hardness" pazarlamasını ve Basu'nun "accepts
random matrices by design" eleştirisini açıklar: **her iki taraf da haklıdır** — kriptografi
ses, fayda değil. KÖK v2 ikisini de dürüstçe ayırır.

---

## 6. ★ 2026-09-20: PDF'ten birebir doğrulama (2504.09971v4, 23 sayfa)

Tam metni okudum. Önceki analizimdeki her önemli nokta **birebir** doğrulandı ve üç yeni
kesin metin eklendi:

### 6.1 Assumption 6.4 — birebir metin ve benim gözlemimin teyidi

> **Assumption 6.4.** *There is no algorithm to compute all the intermediate values when
> multiplying two random n × n rank-r matrices running in time o(n^{ωr+1}/r).*

KW'nin kendi gerekçesi (§6.5'ten hemen sonra, birebir):

> "Using the state of the art rectangular fast matrix multiplication, we can see that the
> above assumption is **true** (because the number bits needed to write down all
> intermediates – **Θ(n³/r)** – is always a lower bound on the running time and ωr = 2 for
> sufficiently small r)."

**★ Bu, §3.1'deki bağımsız gözlemimi teyit eder:** Assumption 6.4, çıktı-boyu alt sınırı
Θ(n³/r) tarafından **neredeyse otomatik** olarak sağlanır — benim vardığım sonuç KW'nin
kendi argümanıyla aynı. **Yani 6.4 gereksizce güçlü değil; KW zaten daha zayıf, standart bir
gerekçe (output-size lower bound) sunar.** Bu, §4'teki "kriptografik ses SAĞLAM"
değerlendirmesini güçlendirir: gereken varsayım standart bir çıktı-boyu alt sınırıdır.

### 6.2 Assumption 6.3 (ilk instantiation, r=1)

> **Assumption 6.3.** *There is no algorithm to compute the product of two random n × n
> matrices in time o(n^ω).*

KW bu instantiation'ın **faydalı olmadığını** kendisi söyler: "the obvious downside is that a
malicious solver can skip the Decode operation altogether... the protocol's overhead is
α ≥ 3... concluding that the protocol is **not useful**." **Ders:** prescribed hardness tek
başına yetmez; **overhead α'ya da bağlıdır** — KÖK v2'nin α=1+o(1) hedefinin neden kritik
olduğu buradan gelir.

### 6.3 Conjecture A.1 — Pearl'in hâlâ açık olarak sorduğu şey

> **Conjecture A.1.** *Let A, B ∈ R^{n×n} be full-rank matrices. Then the amortized cost of
> computing all n³/r³ partial sums (A.1) in Algorithm 1.1 with r = √n, d = O(1), even with
> O(n³) preprocessing time, requires Ω(r³) time, in the word-RAM model with word-size
> w = O(log n).* — "**This is the analogue of Assumption 6.4.**"

Random-rotation (self-cancelling noise) şeması: (A·S)·(S⁻¹·B), randomized Hadamard,
**O(n² log n) overhead, noise peeling yok**. **Pearl'in kendi Polymath Problem (1) hâlâ
"Is this PoW rotation-scheme secure?" diye soruyor** — yani §4'te "conjecture kanıtlanmamış"
değerlendirmem birincil kaynakla doğrulandı. KW'nin Appendix A'sı bir **alternatif**;
ana gövde (§6.5, Assumption 6.4) üretimde kullanılan.

### 6.4 Lemma 6.5 ve verimlilik (birebir)

> "**Lemma 6.5.** In the random oracle model and assuming that σ is unpredictable, then the
> induced distribution of E and F is uniformly random from E_{r,n} (with very small
> statistical error)."

> "Here, as opposed to all of our previous suggestions, the PoUW is **useful**. Indeed, the
> honest solver Solve is doing exactly one product of two n × n matrices... the overhead is
> α(n) = O(n² + n²·r)/t_MatMul(n). Note that **α(n) = o(1)** (unless fast matrix
> multiplication is used)."

**α = o(1)** — bu, §5.1'de KÖK v2'nin iddia ettiği "1+o(1) overhead"in KW'deki tam karşılığı
ve Lemma 6.5 + Assumption 6.4 çifti üzerine kurulu. (Dikkat: α=o(1) ifadesi KW'de
**fast MM kullanılmadığı** varsayımıyla; FMM ile α büyür — §11'de belirtildiği gibi simetrik
kalır.)

### 6.5 Yazar listesi düzeltmesi (önemli)

**arXiv 2504.09971v4 ve ePrint 2025/685 ikisi de iki yazar listeler: Ilan Komargodski,
Omri Weinstein.** Önceki oturumda yazdığım "Schen" üçüncü yazar **yanlıştı** (başka bir
ePrint ile karışmış). 5 dosyada düzeltildi. **Alıntı doğrusu:** Komargodski & Weinstein,
"Proofs of Useful Work from Arbitrary Matrix Multiplication", arXiv:2504.09971v4
(13 Kas 2025) / ePrint 2025/685.

### 6.6 Güncellenmiş sonuç (2026-09-20)

| Boyut | Değerlendirme (önceki → şimdi) |
|---|---|
| Kriptografik ses | SAĞLAM → **SAĞLAM, teyit edildi** (6.1: KW kendi daha zayıf gerekçesini veriyor) |
| Assumption 6.4 | "gereksizce güçlü" → **"output-size bound'la neredeyse otomatik, KW de bunu söylüyor"** |
| Conjecture A.1 | — → **kanıtlanmamış, Pearl kendisi açık sorun olarak listeliyor** (ana gövdeyi etkilemiyor) |
| α = o(1) | — → **birebir teyit** (FMM'siz) |
| Bağımsız kriptograf incelemesi | **Hâlâ zorunlu** — bu doküman bir LLM okumasıdır; 6.1–6.4 onun için **hazır alıntı kontrol listesidir**. |

---

## 6. (2026-09-21) ITEM (iv) KAPANIYOR: σ=ctx'nin ROM kanitina entegrasyonu

*** Bu bolum KW'nin TAM METNINDEN (arXiv 2504.09971v4, 13 Kasim 2025,
HTML tam metni fetch edildi) alintilarla item (iv)'yi kapatir. ***

### 6.1 KW'de σ'nin ROLU (verbatim, §1 ve §5)

KW §1: "the verifier sends a random string **σ** as a challenge and the goal
of the prover is to find a string x such that H(σ‖x) starts with t leading 0s."

KW §6: "The latter property can be achieved by deriving **E and F by applying
a random oracle on σ, A, B**."

KW Lemma 6.5 (verbatim, tam metin fetch edildi):
> "In the random oracle model and assuming that **σ is unpredictable**, then
> the induced distribution of E and F is uniformly random from E_{r,n}
> (with very small statistical error). In particular, with very high
> probability, every r×r submatrix of E and F is **marginally uniform**."

*** GUVENLIK BACAGI (a) su sekilde okunmalidir: σ'nin UNPREDICTABLE
olmasi — yani ROM cikisinin saldirgan onceden bilemez — E,F'nin dagilimini
uniform yapar. ***

### 6.2 BLOKZINCIRDE σ KIMDEN GELIYOR? (KW'nin boslugu)

KW'nin taniminda σ'yi **verifier gonderir** (interaktif). Ama blokzincirde
verifier YOK — madenci, ore-basar. Bu KW'nin protokol-tasarim boslugu:

- KW: σ = verifier'in sectigi uniform rasgele string
- Blokzincir: σ'nin **herkes tarafindan deterministik olarak** hesaplanabilir
  olmasi lazim (cunku butun node'lar ayni seyi dogrular), AMA ayni zamanda
  **o blok icin o an ozel** olmali (replay onleme).

*** COZUM (KOK T-A2): σ = ctx = H("ctx", tip, miner, proof_system_id) ***

### 6.3 ITEM (iv) CEVABI: ctx baglamasi Lemma 6.5'i BOZMUYOR, GUCELLENDIRIYOR

Arguman (uc adim):

**(1) ctx deterministik → her node ayni σ'yi hesaplar.**
H ROM'dur; ctx = H("ctx", tip, ...) ROM cikisidir. Lemma 6.5'in "σ uniform"
sarti yerine **σ ROM cikisidir** — bu DAHA GUCLU bir varsayim degildir,
aynidir: KW zaten σ'yi random oracle'dan geldigi varsayimiyla calisir.

**(2) ctx bloge bagli → unpredictable KOSULU SAGLANIR.**
Lemma 6.5 σ'nin **unpredictable** olmasini ister. KW §6'da sebebi verbatim:
> "Since σ is not known to the (malicious) prover ahead of time and O is a
> random oracle, the output of the random oracle is random and unpredictable."

*** ctx = H("ctx", tip, ...) oldugunda tip = (parent, height) EN SON bloktur.
Madenci NEXT blok icin ctx'yi secemez: parent henutz var olmayan bloktur.
Yani **σ o anki zincir durumuna baglidir ve madinci tarafindan ONUCEDEN
BILINEMEZ** — KW'nin "not known ahead of time" sarti birebir saglanir. ***

**(3) Replay onlemi: ctx'ye miner da girdigi icin sertifika baska yere tasinamaz.**
Madinci A, (parent, height) kullandi. Yeni zincir konumunda (parent', height')
farkli → ctx' farkli → E',F' farkli → **ayni sertifika gecerli degil.**
Bu T-A2'nin tanimidir ve Lemma 6.5'IN ROM argumanini kullanir, onu zayiflatmaz.

*** SONUC: σ=ctx baglamasi, KW'nin Lemma 6.5 ROM kanitina ENTEGRE EDILEBILIR
ve hatta KW'nin kendi interaktif tanimindan DAHA IYIDIR, cunku:
- KW'de σ'yi verifier sectigi icin TOPLAMA (coalition) saldirilari aciktir
- ctx'de σ zincir tarafindan belirlendigi icin **kimse σ'yi secemez** —
  bu, "unpredictable" kosulunu YAPISAL olarak saglar, ahlaki bir varsayimla degil.

ITEM (iv) KAPANDI. ***

### 6.4 (2026-09-21) YENI BULGU: KW'nin KENDI privacy onerisi (F0b'yi dogrular)

KW Remark 2.2 (verbatim, tam metin fetch edildi):
> "we can delegate the verifier's work (when Verify should accept) to the
> prover by asking the latter to compute a **SNARK** certifying that the
> verifier would have accepted the proof had it seen it. Furthermore,
> **if privacy of A, B is an issue, the prover can use a zkSNARK.**"

*** BU COK ONEMLI: privacy (zkSNARK) fikri BIZIM DEGIL, KW'NIN KENDI
onerisidir. F0b (zk-AIR) KW'nin Remark 2.2'sini gerceklestirir: ***
1. Verifier complexity'si SNARK ile cozulur (KOK F0b = bu SNARK)
2. **A,B'nin gizliligi** KW tarafindan ACIKCA ongorulmustur
3. Yani F0b yeni bir icat degil — KW'nin tasarladigi ama insaa etmedigi parcasi

*** F0b'nin teknolojik riski DUSUK: KW'nin kendi yolu. Kalan risk:
SNARK'in kendisinin KW'nin MatMul isine uygun hale getirilmesi (AIR yazimi). ***

### 6.5 Assumption 6.4 — KW'nin "conjecture"i (statüsü korunuyor)

KW Assumption 6.4 (verbatim):
> "There is no algorithm to compute all the intermediate values when
> multiplying two random n×n rank-r matrices running in time
> o(n^{ω_r + 1}/r)."

§3.1'deki tespit KORUNUR: (c) gereksizdir cunku (a)+(b)+Merkle yeterlidir.
Assumption 6.4 sadece "en optimal guvenlik" icin lazim, "guvenlik" icin degil.
KW'nin abstract'inda "We **conjecture** that our protocol has optimal security"
— optimalluk conjecture'i, guvenlik degil. KOK (a)+(b)+Merkle ile guvenli kalir.

---

## 7. (2026-09-21) Q3 TANIMLANDI VE KAPANIYOR: SNARK-as-hardness tuzağı

*** Q3 onceden tanimlanmamisti (dosyalarda yok). Simdi KW'nin TAM METNINDEN
(13 Kasim 2025 v4, HTML fetch) tanimlayip kapatyorum. ***

### KW Remark 2.3 (verbatim):

> "Remark 2.3 (Using SNARKs as a source of hardness?). The above paragraph
> leads to a natural idea of using the SNARK computation itself as a source
> of hardness. Indeed, we could 'force' the prover to follow a specific
> algorithm by asking it to generate a SNARK proof attesting to this fact.
> For this purpose one could avoid noising and denoising altogether if the
> SNARK computation itself is keyed (as in Micali's random oracle-based
> SNARK). This indeed forces the prover to work and prevents a malicious
> prover from doing shortcuts. **The problem is that we typically think of
> ϵ, the probability that Solve...**"

### Q3 SORUSU (formal):

**F0b zk-AIR yaparsak, KOK aslinda KW'nin "noising" mekanizmini atlayip
SNARK'in KENDISINI hardness kaynagi olarak kullanmis olur mu?** Yani:
- Eger SNARK uretimi yeterince rastgele-sekil uretiyorsa, MatMul transcript
  noise E,F gereksiz hale gelir
- Bu durumda KOK "KW PoUW" degil, "SNARK-PoW" (Micali tarzi) olur ve
  KW'nin bUTUN guvenlik argumani degisir

### CEVAP: HAYIR — KOK ikisini ayri tutar (Q3 KAPANDI)

Karar matrisi:

| Yol | Hardness kaynagi | Noise E,F | KW guvenlik bacagi |
|---|---|---|---|
| **KOK G katmani (simdiki)** | MatMul transcript + H hedefi | **VAR** (KW §6) | (a)+(b)+Merkle |
| **KOK F0b (zk-AIR)** | Hala MatMul transcript; SNARK SADECE verifier icin | **VAR** | ayni |
| ~~SNARK-as-hardness~~ | SNARK uretimi | YOK | KW DISI — RED |

*** GEREKCE (KW'nin kendi sozlerine dayanir): ***
KW Remark 2.3 "the problem is..." diye baslar ve ε (prescribed hardness)
sartinin SNARK-as-hardness ile kontrol edilmesinin zorlugunu soyler.
Prescribed hardness KOK icin ZORUNLUDUR (retarget, Bitcoin benzeri difficulty).
SNARK uretimi ise maliyeti **gorevin kendisine** baglidir — ε'yi bagimsiz
ayarlayamazsiniz. *** Yani KW'nin kendisi bu yolu reddeder. ***

*** F0b'NIN ROLU NETLESTI: SNARK hardness KAYNAGI DEGIL, VERIFIER optimizasyonudur
(KW Remark 2.2'nin "delegate the verifier's work" sozu birebir). Yani F0b
KW'nin 2.2'sini yapar, 2.3'unu YAPMAZ. ***

*** Q3 KAPANDI: KOK'un tasarimi SNARK'i hardness kaynagi olarak KULLANMAYACAK
(gorevin kendisi hala MatMul transcript), bu yuzden KW'nin guvenlik
argumanindan sapma YOK. F0b sadece verifier tarafini SNARK'lar. ***
