# KÖK v2 — Faz 2 Kriptograf İnceleme Brief'i

**Tarih:** 20 Eylül 2026 · **Sahip:** KÖK v2 protokolü (kağıt: `PROJE_KAGIDI_V2.md`,
spec: `KOK_V2_TEKNIK_SPEC.md`) · **Hedef:** 2 bağımsız insan kriptograf

> **Bu brief'in amacı:** KÖK v2'nin G katmanının güvenlik argümanını **bağımsız
> kriptografların denetlemesi için** paketlemek. Her soru, **tam metin alıntıları** ve
> **bizim (bir LLM'in) ulaştığımız ön-sonuç** ile birlikte sunulur. Sizden beklenen:
> ön-sonucu **doğrulamak veya çürütmek**. "Kabul ediyorum" yeterli değildir; **nedenini**
> yazmanız gerekir.

---

## 0. Arka plan (30 saniyede)

KÖK v2, iki katmanlı bir L1'dir:

- **Katman G (güvenlik):** KW/cuPOW MatMul PoUW + memoryless difficulty. **Güvenlik talepten
  bağımsızdır** (Demirel ePrint 2026/1492 Thm 2'yi construction-level karşılar: φ=0 filler
  ile canlılık korunur, TV-4/TV-8).
- **Katman U (fayda):** fee-ödemeli verifiable-compute pazarı (escrow + bond + geri-alamaz
  burn). **Asla leader elect etmez** (E-gap mimariye yedirildi: `DEGERLENDIRME_100.md` §9,
  Pearl'in kendi Polymath itirafı ile doğrulandı).

**Bu brief yalnızca Katman G'nin kriptografisini** denetler. Katman U'nun oyun-teorisi
(spec §A.4–A.6) ve ekonomisi (`pass_sim.py`) ayrı bir denetim gerektirir; o brief
`KOK_V2_TEKNIK_SPEC.md` Ek C'dedir.

**Sizi neden arıyoruz:** `KW_ANALIZ.md` bir **LLM'in** okumasıdır. Faz 2'nin zorunlu kapısı,
**iki bağımsız insan kriptografın** onayıdır (V2 §10 F2/F6). Aşağıdaki sorular o kapının
anahtarıdır.

---

## 1. Denetlenecek çekirdek: KW yapısı ve üç güvenlik ayağı

**Kaynak:** Komargodski & Weinstein, "Proofs of Useful Work from Arbitrary Matrix
Multiplication", arXiv:2504.09971v4 (13 Kas 2025) = ePrint 2025/685. (Tam metin
`extracted/KW_full.txt`.)

```
Encode_r(σ, A, B):  σ ↦ (E_L,E_R,F_L,F_R);  E = E_L·E_R, F = F_L·F_R   (rank-r gürültü)
                    A' = A+E,  B' = B+F
Madenci:            C' = A'·B';  transcript tr = tüm (n/r)³ ara r×r bloklar
                    z = O(tr)     (veya Remark 2.1: her bloğu ayrı hash'le)
Decode_r(σ, C'):    C'' = (A·F_L)·F_R + E_L·(E_R·(B+F_L·F_R));  C = C' − C'' = A·B
```

Parametreler: r ≪ n (bizde r = n^0.3 önerisi; Pearl üretimde r ∈ {32..1024} ile sabit r
kullanır); alan 𝔽_q; σ λ-bit seed; ε başarı eşiği. Dürüst overhead α = 1+o(1)
(KW §6.5 birebir: "α(n) = O(n² + n²·r)/t_MatMul(n)... α(n) = o(1)").

| # | Ayak | Statü (ön-sonuç) |
|---|---|---|
| **(a)** | σ öngörülemez (ROM) → E,F önceden bilinemez → preprocessing işe yaramaz | **Kanıtlanmış** (ROM'da trivial) |
| **(b)** | E,F tek başına üniform rank-r (Lemma 6.5) → her r×r blok marjinal üniform → tek blok = rastgele r×r MatMul = Ω(r^ω) | **Kanıtlanmış** (Lemma 6.5 + Claim 6.6) |
| **(c)** | Tüm ara değerleri hesaplama Ω(n^(ω_r+1)/r) (Assumption 6.4) | **Conjecture** — ama KW'nin kendisi çıktı-boyu bound'undan dolayı neredeyse otomatik olduğunu söylüyor (§6.1) |

**Korelasyon itirafı (KW §2, birebir):** "the above argument does not work for computing all
of the intermediates because they are correlated (E and F are only rank r). However,
recovering the correlations requires essentially solving a linear system of equations which,
we conjecture, is as difficult as multiplying matrices."

---

## 2. SORU-1: Assumption 6.4 gerçekten gereksiz mi? (en kritik soru)

**Birebir metin (KW §6.5):**

> **Assumption 6.4.** *There is no algorithm to compute all the intermediate values when
> multiplying two random n × n rank-r matrices running in time o(n^{ωr+1}/r).*

**KW'nin kendi gerekçesi (birebir):**

> "Using the state of the art rectangular fast matrix multiplication, we can see that the
> above assumption is **true** (because the number bits needed to write down all
> intermediates – **Θ(n³/r)** – is always a lower bound on the running time and ωr = 2 for
> sufficiently small r)."

**Bizim ön-sonuçumuz:** Assumption 6.4, **çıktı-boyu alt sınırı** Θ(n³/r) tarafından
neredeyse otomatik olarak sağlanır — KW'nin argümanı da tam olarak budur. Dolayısıyla (c)
**gereksizce güçlü** bir şekilde ifade edilmiştir; gerçek güvenlik (a)+(b)+Merkle üzerinden
daha zayıf, standart bir varsayımla dahi ayakta durur.

**Ancak şu nüansı özellikle denetlemenizi istiyoruz (KW_ANALIZ §3.1):** PoW koşulu
`z = O(tr)` veya **Merkle kökü** altında olduğunda, saldırganın transkripti **materyalize
etmesi gerekmez** — yalnızca hash'ini ister. Bu, çıktı-boyu bound'unun **uygulanmadığı**
yerdir. O halde gerçek güvenlik varsayımı şudur:

> **(Gerçek) Varsayım:** Bir hash fonksiyonu (ROM) altında, rank-r gürültülü bir MatMul
> transkriptinin **Merkle kökünü** (veya per-tile hashlerinden birini) hesaplamanın maliyeti,
> transkripti hesaplamanın maliyetine asimptotik olarak eşittir.

**Sorular:**
- **(1a)** Bu "gerçek varsayım" standart bir Merkle/one-way argümanıyla **kanıtlanabilir**
  mi, yoksa ek bir varsayım mı? Kök, tüm yaprakların hash'ine bağlı olduğundan ve hash tek
  yönlü olduğundan, kökü hesaplamak için her yaprağı değerlendirmek gerekir (yapıdan
  bağımsız olarak — yapraklar yalnızca O(nr) rastgele değerin deterministik fonksiyonu olsa
  bile). **Bu argümanda bir delik görüyor musunuz?**
- **(1b)** KW'nin Θ(n³/r) çıkış-boyu argümanı, ω_r = 2 varsayımına (rectangular FMM)
  dayanır. Eğer ω_r < 2 olursa (yani rectangular multiplication'da ilerleme olursa)
  Assumption 6.4 **çöker mi**? Çökse bile (a)+(b)+Merkle ayakta kalır mı? (Bizim
  ön-sonuçumuz: evet; ama ω_r < 2, aynı zamanda dürüst madencinin de hızlanması demektir —
  oranı korumak için difficulty ayarı yeterlidir, §3.3'teki FMM satırı.)
- **(1c)** "Correlated intermediates" itirafındaki linear-system reduction (KW §2), gerçekten
  MatMul kadar zor mu? Bu, KW'nin **abstract'ta** "batch of low-rank random linear
  equations" dediği şey midir, ve terminolojik kayma (transcript vs. linear equations)
  güvenlik argümanını **zayıflatıyor** mu, yoksa yalnızca sunum mu?

---

## 3. SORU-2: Lemma 6.5'in marjinal üniformluğu — ROM+σ yeterli mi?

**Birebir metin:**

> **Lemma 6.5.** *In the random oracle model and assuming that σ is unpredictable, then the
> induced distribution of E and F is uniformly random from E_{r,n} (with very small
> statistical error). In particular, with very high probability [her satırı...]*

**Sorular:**
- **(2a)** Lemma 6.5'in kanıtı, σ'nın **blockchain bağlamına** bağlanmasıyla (KÖK
  `ctx` = `selected_parent_hash ‖ miner_pubkey ‖ task_ref ‖ height ‖ proof_system_id ‖
  nonce`) **bozulur mu**? σ artık üniform değil, **ctx'den türetiliyor**. Bizim
  ön-sonuçumuz: hayır — Lemma'nın koşulu "σ öngörülemez"dir, ctx-bağlı σ hâlâ öngörülemez
  (adil değil) ve ROM'da H çıktısı üniform kalır. **Ama bu entegrasyon bizim tarafımızdan
  yapılıyor, KW değil** — lütfen doğrulayın. (Bu, `KW_ANALIZ.md` §5'in 4. maddesidir.)
- **(2b)** "Very small statistical error" — bu hata, (n/r)³ bloğun **hepsinin** aynı anda
  zayıf olması ihtimalini nasıl bağlıyor? Birleşik hata (union bound over (n/r)³ tiles)
  yeterince küçük mü, yoksa ε ile n'yi eşlemede (Aşağıda SORU-4) bir sorun çıkıyor mu?

---

## 4. SORU-3: Per-tile denge — difficulty güvenli mi? (Remark 2.1 = Pearl'in jackpot'u)

KÖK v2, **per-tile varyantı** kullanır (Pearl'in üretimdeki seçimi; KW Remark 2.1).
Bizim denge hesabımız (`KW_ANALIZ.md` §3.2):

- **Dürüst:** 1 MatMul (maliyet n³) (n/r)³ tile denemesi verir → **deneme/FLOP = r^(−ω)**,
  n'den **bağımsız**.
- **Saldırgan:** tek tile = marjinal üniform iki r×r bloğun çarpımı → maliyet ≥ Ω(r^ω)
  (ayak (b)). Dürüst ile aynı.
- **Sonuç:** difficulty, blok sayısının (veya DAG yüksekliğinin) fonksiyonu olabilir;
  **matris boyutu serbestliği dengeyi bozmaz** (r protokol parametresi, sabit).

**Sorular:**
- **(3a)** Bu denge hesabı doğru mu? Özellikle: saldırgan **çok sayıda küçük matris**
  (küçük n) seçerek tile başına düşen FLOP'u düşüremeyeceğini doğrulayın — çünkü
  deneme/FLOP = r^(−ω) ve **r sabit**. Ama ya saldırgan **büyük n** seçerse? Tile sayısı
  (n/r)³ ile artar, ama her tile'ın maliyeti **değişmez** (r×r blok). Overhead'ı
  (Encode/Decode'nin O(n²r)'i) amorti ederek deneme/FLOP'u **artırabilir** mi?
  (Bizim ön-sonuçumuz: sadece sınırlı bir şekilde — O(n²r)/n³ = r/n → 0; yani deneme/FLOP
  yalnızca artar, saldırgan **kazanmaz**, dürüst tarafından da aynı avantaj kullanılabilir.
  **Doğrulamak istiyoruz.**)
- **(3b)** Pearl'in jackpot politikası (TV-11..TV-14, `g_layer_tests.py`'deki `JackpotToy`)
  bu dengenin **FP/quantized** ortamındaki karşılığı mıdır? Özellikle: **unpredictable
  summands** kontrolü (FP'de yuvarlanan summand'ı atma saldırısı), INT ortamında bir
  **anlamı var mı**? Bizim ön-sonuçumuz: INT'de precision shortcut yok (yuvarlama yok),
  bu yüzden TV-14 yalnızca FP'ye (Faz 3) göredir; INT G katmanında gereksizdir.
  **Katılıyor musunuz?**

---

## 5. SORU-4: ε ve n eşleştirme (Remark 5.3) — difficulty ayarının kuralı

KW Remark 5.3: difficulty **ya n ya ε** ile ayarlanır; ikisi birden serbest bırakılırsa
madenci optimizasyonu karmaşıklaşır. KÖK v2'nin kuralı: **n protokol sabitidir, ε (target)
retarget ile ayarlanır** (Bitcoin'in kuralına birebir uyum, spec Ek B).

**Soru:**
- **(4a)** Bu kural, per-tile varyantında (SORU-3) hâlâ doğru mu? Per-tile'da tile sayısı
  n'ye bağlı, ama her tile'ın maliyeti **r'ye** bağlı. O halde difficulty'yi ε ile ayarlamak,
  **r sabit** olduğu sürece güvenli midir? (Ön-sonuçumuz: evet; r protokol parametresi
  olduğu için fork gerektirmeden değiştirilemez — §7 katman A.)
- **(4b)** Bellek: bütün-transkript varyantı Θ(n³/r) bellek ister (KW Remark 2.1 itiraf
  eder). Per-tile seçimi bunu O(nr)'e düşürür. **Doğru mu?** Ve O(nr), madenci için
  **hâlâ anlamlı bir donanım eşiği** midir (ASIC'ye karşı)?

---

## 6. SORU-5: Yapısal saldırı sınıfı — eksik bir saldırı var mı?

Aşağıdaki tabloyu çürütün veya doğrulayın. **Eksik bir satır** (yani tabloda olmayan bir
saldırı) bulursanız, bu brief'in en değerli çıktısı olur.

| Saldırı | v1 (düz Freivalds) | KW + KÖK ctx | Sonuç |
|---|---|---|---|
| Sparse/permutation A (iş O(n³)→O(n)) | ✓ çalışır | A+E marjinal üniform → işe yaramaz | KW kazanır |
| A=B=0 (kolay girdi) | ✓ | transcript hâlâ (n/r)³ üniform tile ister | KW kazanır |
| Precompute/replay (σ bilinmeden) | kısmen | σ = ctx (selected_parent ‖ ...) → imkânsız | KW + ctx kazanır (TV-1) |
| Korelasyondan kısayol (rank-r gürültü) | n/a | X_i·(Σ Y_{ℓ'}Z_{ℓ'})·W_j = aynı asimptotik (KW §6.5'in kendisi gösterir) | **denklik** |
| Trapdoor matrix (VZ25 2502.13065 / BN25 2502.13060, LPN) | n/a | E,F σ'dan türetilir, saldırgan trapdoor **yerleştiremez** | KW kazanır (KW'nin reddini **bağımsız** olarak doğruluyoruz) |
| FMM ilerlemesi (ω < 2.371339; AlphaEvolve 2.371177, 2026) | n/a | Dürüst ve saldırgan **aynı** algoritmayı kullanır → oran korunur | **ekonomik, kriptografik değil** |
| Kuantum | Grover ✓ (Bitcoin gibi) | MatMul için HHL-benzeri algoritmalar kuantum girişim ister ve klasik hash bulamaz | **Bitcoin-pariti PQ** |
| **Low-entropy donanım (Polymath 6: "1-bit hardware enough?")** | n/a | G katmanı MatMul tabanlı; düşük-alfabeli özel devre **hem Pearl'i hem KÖK'ü** etkiler | **ORTAK AÇIK** — TV-12 noise-floor toy kanıtı; üretimde Hawkeye whitelist + jackpot policy |

**Sorular:**
- **(5a)** Yukarıdaki "denklik" satırı (korelasyon kısayolu) — gerçekten **denk** mi, yoksa
  saldırgan için sabit-katsayı bir avantaj var mı? (Pearl'in jackpot politikası
  ε_idle/ε_tame/ε_pred eşikleri bu sabit avantajları sınırlandırmak için; bizim
  toy adaptasyonumuz var ama **üretim kalibrasyonu yok**.)
- **(5b)** **Eksik saldırı** arayın. Özellikle şu üç yönde:
  (i) **Algebraic:** E,F'nin rank-r yapısından (E = E_L·E_R) kaynaklanan ve
  Y = Σ_{ℓ'≤ℓ} A'_{i,ℓ'}·B'_{ℓ',j} prefix-sum yapısını sömüren bir kısayol;
  (ii) **Hash:** BLAKE3'ün (Pearl) veya kullanılan RO'nun MatMul çıktıları üzerindeki
  **yapıdan** (düşük-rank) kaynaklanan bir kısayol — yani hash'in düz-random davranmaması;
  (iii) **Sosyal/stratejik:** madencinin **birden fazla kimlikle** (sybil) oylama veya
  task assignment'ı (VRF ataması, spec §A.10.3) etkilemesi — **bu G katmanı dışıdır** ama
  G'yi zayıflatabilir mi?

---

## 7. SORU-6: Conjecture A.1 (random-rotation) — KÖK'ü etkiler mi?

**Birebir metin (KW Appendix A):**

> **Conjecture A.1.** *Let A, B ∈ R^{n×n} be full-rank matrices. Then the amortized cost of
> computing all n³/r³ partial sums (A.1) in Algorithm 1.1 with r = √n, d = O(1), even with
> O(n³) preprocessing time, requires Ω(r³) time, in the word-RAM model with word-size
> w = O(log n).* — "**This is the analogue of Assumption 6.4.**"

**Bağlam:** Random-rotation (self-cancelling noise) şeması (A·S)·(S⁻¹·B), randomized
Hadamard, **O(n² log n) overhead, noise peeling yok**. **Pearl'in kendi Polymath Problem (1)
hâlâ "Is this PoW rotation-scheme secure?" diye soruyor.**

**Soru:**
- **(6a)** KÖK v2 bu şemayı **kullanmaz** (§6.5'in instantiation'ı). Ama Conjecture A.1
  kanıtlanırsa, **KÖK'ün Assumption 6.4'ü için bir sonuç doğar mı**? (Ön-sonuçumuz: hayır —
  iki farklı şema; A.1, 6.4'ün *analogu* olarak sunuluyor ama bağımsız.)
- **(6b)** A.1 **çökerse** (Pearl'in korktuğu gibi), KÖK'ün G katmanı (transcript varyantı)
  etkilenir mi? (Ön-sonuçumuz: hayır — A.1 yalnızca rotation şemasını bağlar.)

---

## 8. İnceleme çıktısı beklediğimiz format

Her SORU için:
1. **Verdikt:** DOĞRULANDI / ÇÜRÜTÜLDÜ / KISMEN / BELİRSİZ (kanıt yetersiz).
2. **Gerekçe:** matematiksel veya alıntı referansı ile.
3. **Eğer çürütüldüyse:** somut saldırı veya counterexample verin — biz prototype
   (`u_layer_prototype.py`, `g_layer_tests.py`) üzerinde **çalıştırabiliriz** ve
   `KOK_V2_TEKNIK_SPEC.md`'i güncelleriz.
4. **Eğer belirsizse:** hangi ek kanıtın/deneyin gerektiğini yazın.

**Önemli:** "Kabul ediyorum" **yeterli değildir.** Verdiktin nedenini yazmak zorunludktur —
çünkü KÖK v2'nin puanı (`DEGERLENDIRME_100.md` §9: teknik 82/100) bu incelemenin
**sonucuna** bağlıdır ve biz "kriptograf onayladı" demek istiyorsak, onayın **neyi**
onayladığını bilmemiz gerekir.

---

## 9. Çalıştırılabilir kanıtlar (sizin de kullanabileceğiniz)

- `u_layer_prototype.py` — TV-5..TV-10 (escrow/burn, VRF, fraud, slash, PQ gate); stdlib
  only, 2,5 sn. `KWKernel(q=97, n=8, r=2)` — **toy boyut**, ama arayüz üretim spec'i
  (`§A.10`) ile birebir.
- `g_layer_tests.py` — TV-1..TV-4 (replay reddi, prescribed hardness, easy-instance, φ),
  TV-11..TV-14 (jackpot policy toy adaptasyonu), RT-1..RT-3 (retarget); 12,8 sn.
- `pass_sim.py` — Pass 2606.06700 kapalı-form çözücü, Pearl kalibrasyonlu (canlı ağı
  %5,8 içinde yeniden üretir).
- `extracted/KW_full.txt`, `extracted/Pass_full.txt`, `extracted/Pearl_new_wp.txt` —
  tam metinler.

**Toy boyut uyarısı (dürüst):** q=97, n=8, r=2 — bu, **asimptotik** argümanları test
etmez, yalnızca **arayüz ve ekonomi** davranışını. Asimptotik güvenlik bu brief'in
**sizin** uzmanlığınız olan kısmıdır; prototip onun yerine **ekonomik ve protokol**
davranışını kanıtlar.

---

## 10. Zaman çizelgesi ve tazminat

- Faz 2'nin bu incelemesi **testnet öncesi zorunludur** (V2 §10 F2/F6).
- İnceleme sonucuna göre: DOĞRULANDI → testnet roadmap'i (§12.1) başlar; ÇÜRÜTÜLDÜ →
  fallback (`spec §A.9`, pure-PoW modu) devreye girer ve G katmanı yeniden tasarlanır.
- Tazminat: `PROJE_KAGIDI_V2.md` §8'deki hazine (%5–8) kapsamında, ya PRL-gibi token
  ile ya da sabit ücret. **Bu brief'i kabul etmeniz herhangi bir ödeme vaadi değildir.**

---

## Ek: KW'nin gözümden kaçırdığı (veya okuyucunun bilmesi gereken) bir nüans

KW Abstract'ta "batch of low-rank random linear equations" der ama §2'deki argüman bunun
**MatMul transkriptine** indirgenmesidir; gerçek varsayım (b) ve Merkle'dir. Bu terminolojik
kayma, Pearl'in "prescribed hardness" pazarlamasını ve Basu'nun "accepts random matrices by
design" eleştirisini açıklar: **her iki taraf da haklıdır** — kriptografi ses, fayda değil.
KÖK v2 ikisini de dürüstçe ayırır.

---

## 11. ★ BAĞIMSIZ KRİPTOGRAF ADAYLARI (2026-09-20)

> **Bağlılık kuralı (kesin):** bir aday **Pearl Research Labs ile** herhangi bir
> bağlantısı varsa (çalışan, danışman, ortak yazar, fon alıcısı) **bağımsız değildir**.
> Bu kuralın nedeni §12.1'deki bulgu: Pass makalesi *"This work was done while
> consulting for Pearl Research Labs"* diyor ve Pearl'in FAQ'ı bunu
> "Pearl is at least as expensive to attack" olarak **bağımsız doğrulama gibi**
> sunuyor. **Aynı hata bizde olmayacak.**

### 11.1 Aday tablosu (hepsi ePrint/arXiv sayfalarından doğrulandı)

| # | Aday | Kurum | Uzmanlık | Pearl bağı | Değerlendirme kapsamı |
|---|---|---|---|---|---|
| 1 | **Pratyush Dikshit** | University of Luxembourg | PoUW SoK (2025/1814); 50+ construction incelemesi; **utility≠security** tezi | **YOK** (akademik) | SORU-1, SORU-5 (yapısal saldırı sınıfı — SoK bunları katalogladı), SORU-6 |
| 2 | **Ashkan Emami** | University of Luxembourg | aynı SoK; **Toulmen-based claim evaluation** yöntemi | **YOK** | SORU-5 + §8 verdikt formatı (Toulmin yöntemi bizimkinden daha sistematik) |
| 3 | **Johannes Sedlmeir** | University of Münster | SoK; **PoUW ekonomi-modelleri** (utility-aware difficulty) | **YOK** | SORU-4 (ε/n eşleştirme — SoK "difficulty adjustment" başlığı tam burası) |
| 4 | **Gilbert Fridgen** | University of Luxembourg | SoK; sistemleştirme metodolojisi | **YOK** | genel denetim + §9 toy-sınır değerlendirmesi |
| 5 | **Ömer Demirel** | Snowfall Finance LLC | **Proof of Demand ≠ PoW** (2026/1492); W/B/E ayrımı; Thm 2 (talepten bağımsız leader election); **Pearl cuPOW denetimi yapmış** ("one reported audit (Pearl cuPOW)") | **KISMEN** — Pearl'i denetlemiş (bu İYİ: Pearl'ü bilir ama Pearl'den DEĞİL) | **SORU-1, SORU-3** + G/U mimarisinin kendi tezine karşı testi (en güçlü aday) |
| 6 | **Omri Weinstein** | (KW yazarı) | KW'nin kendisi | **YOK gibi** — ama **Komargodski ile ortak**; Komargodski Hawkeye yazarı (Pearl) | **ÇATIŞMA RİSKİ**: Weinstein'ı bağımsız saymak için Komargodski ile olan ortak çalışmalarını beyan etmeli |
| 7 | **Dan Boneh** | Stanford | Hawkeye yazarı (Pearl'in doğrulama yolu) | **VAR** — Hawkeye = Pearl'in FP doğrulaması | **DIŞLANIR** (Hawkeye'ı değerlendirirse çıkar çatışması) |

### 11.2 Önerilen iki-kişilik ekip (zorunlu Faz 2 kapısı)

**Birincil (G katmanı + teorik): Ömer Demirel.**
- Neden: kendi Thm 2'si **KÖK v2'nin G/U mimarisinin teorik temelidir** — yani mimarimizi
  **onun tezine karşı** test edebilir. Ayrıca "one reported audit (Pearl cuPOW)"
  notundan **Pearl'ü biliyor**; bu, farklılaşma iddialarımızı (§12) gerçekten
  anlayabileceği anlamına gelir. Pearl'e **bağlı değil** (Snowfall Finance).
- **Risk (dürüst):** Demirel'in "irrecoverable burn = security resource" tezi
  KÖK v2'nin tasarımına **ilham vermiş** olabilir — yani tezi doğrulamak
  **kendi konumunu da doğrulamak** anlamına gelir. Bu önyargıyı gidermek için
  ikinci inceleyici bağımsız bir ekolden gelmeli.

**İkincil (SoK ekolü + metodoloji): Pratyush Dikshit veya Johannes Sedlmeir.**
- Neden: PoUW SoK'unu yazdılar; **"utility güvenlik bütçesine katkı vermez"** tezleri
  KÖK v2'nin G/U ayrımının **aynı fikri bağımsızca** savunuyor. Toulmin-tabanlı
  değerlendirme yöntemleri §8'deki verdikt formatımızdan daha sistematik —
  onların yöntemini bizim brief'imizle birleştirmek mümkün.
- **Ek avantaja:** KÖK v2'nin "fayda = güvenlik değil" iddiası, SoK'un kendi
  bulgusu — yani inceleyici **önyargılı DEĞİL**, konuya **zaten katılıyor**;
  geriye sadece **KÖK v2'nin bunu gerçekten başarılıp başaramadığını** denetlemek kalır.

**Üçüncü (opsiyonel, sadece SORU-3 için): Omri Weinstein** — KW'nin yazarı.
- **Sadece** Komargodski ile bağını beyan etmesi ve SORU-3 (per-tile denge) ile
  sınırlı kalması koşuluyla. Asıl dengenin **farklılaşma analizini** yapamaz.

### 11.3 İletişim planı (gönderilecek paket)

1. **Bu brief** (`KRIPTOGRAF_BRIEF.md`) — SORU-1..SORU-6 + §8 verdikt formatı.
2. **`KOK_V2_TEKNIK_SPEC.md`** Ek A (görev pazarı protokolü) — A.0–A.10.7.
3. **`KAYNAKLAR.md` KANIT İNDEKSİ** — her iddianın nerede kanıtlandığı.
4. **Çalışan prototipler** (4 dosya) + çalıştırma komutları.
5. **§11.1 çıkar-çatışması beyarı** — Pass'in Pearl danışmanlığı ve bizim buna
   rağmen Pass modelini kullandığımız (§12.1'de itiraf edildiği gibi).

### 11.4 Ret/koşullar (adil oyun)

- İnceleyici **KW'nin kendisinin desteğini alamaz** (aynı zamanda KW'yi denetliyor).
- İnceleme sonucu **ne olursa olsun yayınlanır** — ÇÜRÜTÜLDÜ durumunda KÖK v2
  fallback'e (spec §A.9) düşer ve bu karar dokümante edilir.
- Tazminat: `PROJE_KAGIDI_V2.md` §8 hazine (%5–8) kapsamında, **brief'in kabulü
  ödeme vaadi değildir** (§10'da belirtildiği gibi).

### 11.5 ★ KÖK v2'nin kendi standartına uygulanması (dürüst ayna)

Bu çıkar-çatışması analizi **bize de uygulanır**: `KW_ANALIZ.md`'in tümü bir LLM'in
okumasıdır (†) ve `pass_sim.py` **Pass'in (Pearl danışmanı) modelini** kullanır.
Yani:
- `pass_sim.py`'nin Pearl kalibrasyonu (%5,8) **geçerlidir** — model denklemleri
  matematiktir, kim yazdığına bakmaz; **ama** modelin varsayımlarının
  (rekabetçi denge, ε=2) Pearl'in φ=0 gerçeğinde **zayıf olduğu** §12.1'de
  belirtilmiştir.
- **2 bağımsız inceleyici, Pass'in modelini de bağımsızca denetlemelidir.**
  Brief'in SORU-1'ine bu maddeyi ekleyin.
