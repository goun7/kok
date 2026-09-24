# KÖK Network v2 — PoW L1 + Verifiable-Compute Pazarı: Kâğıt Üzerinde Mümkün Olan En İyi Sistem

**Tarih:** 19 Eylül 2026 (KW/Pearl/Demirel güncellemesi) · **Durum:** Tasarım dokümanı (v1 kâğıdının yerine)
**Sembol:** `$KOK` · **Konsensüs:** GHOSTDAG + KW MatMul PoUW (talepten bağımsız güvenlik) · **Fair launch**
**Teknik spec:** `KOK_V2_TEKNIK_SPEC.md` (Ek A görev pazarı, Ek B difficulty, Ek C ekonomi)

> **Pitch (eski → yeni):**
> ~~"Madenciler AI matrisi çözer, doğrulayıcılar bunu mikrosaniyede, enerji harcamadan doğrular."~~
> **"Fair-launch bir PoW L1: güvenlik, Komargodski–Weinstein MatMul PoUW sertifikalarının
> memoryless rejection-sampling zorluğundan gelir — tamamen talepten bağımsız (Pearl'in
> 'faydalı iş = güvenlik' yanılgısına düşmeden). Üzerinde bir fee-ödemeli verifiable-compute
> pazarı: istemciler governance proof'ları ve provable inference için ödeme yapar, talep
> escrow'daki gerçek fee ile dışsallaşır. Kriptografi hash-tabanlı ve post-kuantumdur;
> acil-fork şemaları önceden commit edilmiştir."**
> Bu **"bedava AI inference" vaadi değildir.** Vaat şudur: **Bitcoin ile aynı güvenlik matematiği
> (saldırı = PR/2), ama aynı elektrikle ödenen ve gerçek paralar için satın alınabilen bir
> verifiable-compute çıktısı da üretilir.** Enerji hâlâ harcanır; fayda bir **bonus**'tur,
> güvenliğin kaynağı değildir — 2026'nın üç çalışması bunu zorunlu kılar (§3.2).

---

## 1. Tasarım Felsefesi: Üç Kırılmaz İnvariant

v1'in beş ölümcül boşluğundan üçü, doğrudan üç invaryanta dönüştü:

- **I1 — İş, tanımı gereği worst-case zor olmalı.** İş = **KW MatMul PoUW sertifikası**
  (ePrint 2025/685): prescribed hardness girdi seçiminden bağımsızdır, 1+o(1) overhead, FMM'ye
  dayanıklı. v1'in Freivalds denklemi KW'ye göre "trivial O(1) overhead ama işe yaramaz" —
  structured-matris saldırısına açıktır. (Güvenlik bir **conjecture**'a dayanır; §3.1.)
- **I2 — Sertifikanın statement'ı zincire bağlı olmalı.** `ctx = selected_parent_hash ‖
  miner_pubkey ‖ task_ref ‖ height ‖ proof_system_id ‖ nonce`. Böylece precompute, replay ve
  grinding imkânsız (SNARKChain'ın "chain integrity + miner identity" zorunluluğu, arXiv 2510.09729).
- **I3 — Zorluk memoryless olmalı.** Blok geçerlilik koşuluna `H(FS_digest ‖ nonce) < target`
  eklenince blok aralıkları üssel dağılır → **Bitcoin'in retarget matematiği birebir geçerli**,
  DAG blok hızı korunur. Deterministik işte "görev boyutu = zorluk" yerine bu kullanılır
  (tam formülasyon: `KOK_V2_TEKNIK_SPEC.md` Ek B).

Geri kalan iki boşluk (ekonomi, hukuk) §7 ve §9'da.

---

## 2. Mimari

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  KATMAN 6 — EKONOMİ: tail emission + %hazine + görev-fee pazarı (Pass 2026)    │
├───────────────────────────────────────────────────────────────────────────────┤
│  KATMAN 5 — CRYPTO-AGILITY DÜZLEMİ:                                            │
│   versioned schemas (statement_schema_id, proof_system_id, activation_epoch)   │
│   çift-doğrulama penceresi · formal-doğrulama kapısı · madenci lead-time       │
│   hardness monitoring + önceden-committed acil-fallback şeması                 │
├───────────────────────────────────────────────────────────────────────────────┤
│  KATMAN 4 — KONSENSÜS: GHOSTDAG (PHANTOM, ePrint 2018/104)                     │
│   + rejection-sampling difficulty (I3) + teşvik-uyumlu görev/tx seçimi         │
│   + per-block STARK agregasyonu (ZK-ACE: ~160 B/tx)                            │
├───────────────────────────────────────────────────────────────────────────────┤
│  KATMAN 3 — İSPAT SİSTEMİ (PQ, transparent setup):                              │
│   S2 için: Circle STARK / S-two AIR (Lean ile sesi doğrulanmış, arXiv 2606.04311) │
│   + non-lineer operasyonlar için lookup argümanları (Jolt Atlas, 2602.17452)   │
│   + recursif aggregation: Arc (hash-tabanlı, sınırsız derinlik, CRYPTO 2025)   │
├───────────────────────────────────────────────────────────────────────────────┤
│  KATMAN 2 — DETERMİNİSTİK HESAP HARNESS (S2 için):                               │
│   pinned kernel/reduction-order/seed · Merkle trace commitment                │
│   fixed-point + yayınlanmış hata bütçesi (bugün) → native FP precompile        │
│   (arXiv 2606.05433) olgunlaşınca GPU'nun yaptığı GERÇEK hesabı doğrular        │
├───────────────────────────────────────────────────────────────────────────────┤
│  KATMAN 1 — İŞ KATMANI (faydalı çıktının kaynağı):                               │
│   S1: KW-native — madencinin KENDİ AI workload'u (1+o(1), 2-for-1)             │
│   S2: premium SNARK hizmeti — governance proof'ları + provable inference      │
│   Filler: dense-random MatMul = dürüst pure-PoW modu (canlılık)                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. İş Fonksiyonu ve Görev Pazarı (Çekirdek)

> **2026-09-19 GÜNCELLEME — kritik:** Bu bölüm, Pass (arXiv 2606.06700) üzerinden yapılan
> **2026-09-19 GÜNCELLEME — KRİTİK (2. revizyon):** Pass (arXiv 2606.06700) üzerinden yapılan
> araştırma **Komargodski–Weinstein yapısını** (IACR ePrint 2025/685) ortaya çıkardı: permissionless
> ayarda MatMul için **1+o(1) overhead** ile **prescribed hardness** — v1'in "structured-matrix"
> açığını kriptografik olarak kapatır. Ama üç 2026 çalışması **PoUW'ün fayda iddiasını da sınırladı**:
> (i) Basu (arXiv 2606.04819) Pearl'in **24 EH/s'lik canlı ağının sıfır faydalı AI hesaplaması
> ürettiğini** ölçtü — protokol rastgele matrisleri "tasarımdan dolayı" kabul ediyor; (ii) Demirel
> (ePrint 2026/1492) **talep ≠ iş** ispatladı: güvenli+canlı bir mekanizmanın **talepten bağımsız
> bir leader-election yolu olmak zorunda** (Thm 2); (iii) SoK (ePrint 2025/1814): "utility güvenlik
> bütçesine katkıda bulunmuyor". **Bu yüzden KÖK v2'nin mimarisi ikiye ayrıldı: GÜVENLİK katmanı
> (talepten bağımsız PoW) + FAYDA katmanı (fee-ödemeli verifiable-compute pazarı). "Faydalı iş
> zinciri güvendir" vaadi yoktur — olamaz.**

### 3.1 Kriptografik taban: Komargodski–Weinstein MatMul PoUW
- **Yapı:** ePrint 2025/685 (2025-04-15, 3 revizyon, son 2025-12-08). Arbitrary MatMul,
  miner-chosen input, **1+o(1) multiplicative overhead**, prescribed hardness; FMM algoritmalarına
  (ω<2.371177, Ağu. 2026) karşı dayanıklılık iddiası.
- **Ne sağlar / ne sağlamaz:** KW **work soundness (W)** sağlar — geçerli sertifika için h(n)
  çalışmak şart, girdi seçiminden bağımsız. **Demand exogeneity (E) sağlamaz** — matrislerin
  kimsenin işi olduğunu certify etmez (Pearl bunu "ekonomik bir özellik, kriptografik garanti
  değil" diye pazarladı; Basu bunun tam çöküşünü ölçtü).
- **⚠ Bağımlılık (dürüst):** KW'nin güvenliği bir **conjecture**'dır (sertlik, "batch of
  low-rank random linear equations" problemine indirgeme). Bu protokolün tek kriptografik
  varsayımıdır; bağımsız inceleme Faz 2'nin kapısıdır; çöküşü için acil fallback spec'te
  tanımlıdır (`KOK_V2_TEKNIK_SPEC.md` §A.9).

### 3.2 İki katmanlı dürüst mimari

**KATMAN G — GÜVENLİK (talepten bağımsız, Demirel Thm 2'yi construction-level karşılar):**
- İş = **KW sertifikası + memoryless difficulty** (`H(FS_digest‖nonce) < target`).
- Madenci kendi MatMul girdisini seçer (serbest); **prescribed hardness** sayesinde seçim çalışmayı
  azaltamaz → sybil/easy-instance kapalı. **Ama "faydalı" olduğu iddia edilmez** —Pearl'in
  hatasına düşmemek için.
- **Filler:** görev talebi yetersizken protokol dense-random MatMul ürettirir = **pure-PoW modu**
  (Pass'ın Bitconia'sı). Zincir **her koşulda** yaşar; bu, Demirel'in "null-demand projection"
  gereğinin tam karşılığıdır.
- Saldırı maliyeti = **PR/2**, talep ne olursa olsun (Pass). Ekonomi: tail emission + %5 hazine.

**KATMAN U — FAYDA (fee-ödemeli verifiable-compute pazarı, E exogenous-by-construction):**
- İstemci **önce** zincire görev + fee commit eder (escrow, içinde **geri-alamaz burn bileşeni**
  — Demirel'in "irrecoverable tax"ı). Talep, ödeme nedeniyle **dışsaldır**; matris içeriği
  **istemci tarafından belirlenir**, madenci tarafından değil.
- Görev, **VRF ile** madenciye atanır (grinding/collusion'e karşı); madenci **o görev için** tam
  zkVM/STARK ispatı üretir. Utility: (a) **frontier-AI governance proof'ları** (arXiv 2606.05433 —
  regülatörler kümülatif eğitim compute'ını denetliyor, denetim self-reporting'e dayalı; native
  BF16/FP32 precompile ile gerçek GPU hesabını doğrulama, ~36 ay horizon); (b) **provable
  inference** (gizli reasoning'de %1.469 tahşişi tespit edilemiyor, arXiv 2605.30040).
- **Köşe taşı:** U katmanı **lider seçimini belirleyemez** — sadece **sınırlı, fiyatsız bir
  boost** (Demirel Corollary 4) ve fee geliri. Güvenlik her zaman G katmanından gelir.
- **Anti-aggregation (arXiv 2505.21685):** per-block useful-fee cap `C_fee` + görevlerin sonraki
  bloklara kayması (madencilerin tüm yüksek-fee görevleri tek blokta toplamasını engeller).

### 3.3 Zincir bağlama ve görev yaşam döngüsü
- **ctx binding:** her çözümün statement'ı `selected_parent ‖ miner_pubkey ‖ task_ref ‖ height ‖
  proof_system_id ‖ nonce` içerir → **precompute/replay imkânsız** (T-A2, spec §A.3).
- **U katmanı yaşam döngüsü:** submit+fee+burn → escrow → VRF ataması (epoch seed, N-64 blok
  öncesi) → proof → block inclusion → `W_s` blok fraud penceresi → settle (fee + reward);
  hileli ispat → bond slash + itirazcıya reward. Tam pseudocode: `KOK_V2_TEKNIK_SPEC.md` Ek A.
- **Ölçüm zorunluluğu:** Pearl'in başarısızlığı, "madenci yazılımı inference yapıyor mu"
  sorusunun **kanıtla** cevaplanması gerektiğini gösterdi. KÖK, U katmanı için zincir-üstü
  **φ (faydalı-task oranı)** ve fee-burn hacmini yayınlar (spec §C.4).

---

## 4. Güvenlik Modeli (Teorem Iskeletleri)

- **T1 (Statement binding):** Statement'a `ctx` gömülü olduğu için, bir ispat yalnızca belirli bir
  zincir konumunda ve belirli bir madenci anahtarında geçerlidir; **replay ve precompute
  imkânsız** (zincir hash'i önceden bilinemez). Redüksiyon: aksi, FS transcript'ın
  determinizmini ihlal eder.
- **T2 (Prescribed hardness):** KW (ePrint 2025/685) altında iş maliyeti `h(n) = Θ(n³)` FLOP'dur
  ve **girdi seçiminden bağımsızdır** — structured-matris/easy-instance kısayolu yoktur. FMM'ye
  (ω<2.371177) dayanıklılık KW tarafından iddia edilir. **Bağımlılık:** bu, KW'nin low-rank
  random linear equations conjecture'ına dayanır (§3.1); bağımsız inceleme + acil fallback şart.
- **T3 (Soundness):** STARK'lar için ses hatası `2^-λ`; parametreler `λ ≥ 128` için
  tek-proof yeterli (agregasyonda ek amplify). Under-constrained devre riski → **ZEBRA**
  (arXiv 2609.15020, Eyl. 2026) tarzı otomatik **çözüm-küme kardinalite** doğrulaması + **Lean**
  ile AIR sesi (S-two modeli, arXiv 2606.04311) + bağımsız denetim. (ZEBRA 5 gerçek zkVM'de
  11 zero-day buldu; bu, gerçek saldırı yüzeyidir.)
- **T4 (Ekonomik saldırılar):** Pass (arXiv 2606.06700): **denge fiyatları hesaba katılınca
  majority saldırı maliyeti blok ödülüne bağlı kalır** (`PR/2`, tüm rejimlerde); "saldırana
  ödeme" saman adamı çürür. Tasarım, **Fortessia rejimini** hedefler: duplex iş, güvenliği
  artırırken faydalı çıkışı değiştirmez. Parametreler (`θ`, `α`, `γ`) zincir-üstü simülasyonla
  yayınlanır (spec Ek C).
- **T5 (DAG teşvikleri):** GHOSTDAG'in random transaction selection'ı Nash dengesi değildir
  (arXiv 2109.01102, 2305.16757; ACNS 2025 / 2501.10888). KÖK, görev/tx seçim kuralını
  **protokol tarafından belirlenmiş** (serbest değil) hale getirir + havuzlaşma eğilimine karşı
  protokol-kontrollü commitment ve küçük-blok-ceza; selfish mining için ACNS 2025 çözücüsü ile
  sürekli regresyon testi.
- **T6 (ASIC / donanım):** İş, **GPU'ların zaten yaptığı MatMul** olduğundan (KW 1+o(1)),
  özel amaçlı madencilik ASIC'leri için **doğal pazar yok** — madenciler AI compute tüketicisidir,
  donanımları saldırıdan sonra da değerini korur (Pass §1.8'in GPU-vs-ASIC stok analizi).
  Matmul-ASIC merkezileşmesi (v1'in ölümcül zayıflığı) yapısal olarak azalır; yine de
  tek-adres/havuz payı metrikleri sürekli yayınlanır (spec §C.4 alarmı).

---

## 5. Zorluk, Blok Üretimi ve Doğrulama Maliyeti

- **Blok geçerliliği:** (i) atanmış görev için geçerli ispat, (ii) `H(FS_digest ‖ nonce) <
  target`, (iii) GHOSTDAG sıralaması kuralları.
- **Memorylessluk:** Beklenen deneme sayısı `1/p`, `p = target/2^256` → aralıklar üssel;
  **retarget algoritması Bitcoin'le aynı formdadır** (2016-blok penceresi yerine DAG yüksekliği).
- **Zorluk birimi:** "expected proof-FLOPs" — doğrulanabilir, manipüle edilemez.
- **Retarget tasarımı (2026-09-20, Pearl'den dürüst alternatif):** KÖK v2 **pencere + medyan
  filtre** kullanır (`Λ̂ = D·W/T_act`, 4× clip, medyan; RT-1..RT-3 doğrulandı). Pearl ise
  **WTEMA** (weighted transposed EMA, per-block, 7-gün decay) kullanır — her blokta ayar,
  pencereli gecikme yok. **İkisi de defansif:** WTEMA daha hızlı tepki verir ama tek bir
  yavaş bloğu tam yansıtır (D'yi düşürür); pencere+medyan daha yavaş ama ani tekil
  anomalilere dayanıklı. KÖK v2 spesifikasyonu **WTEMA'yı B.3'ün alternatifi olarak tutar**
  (testnet'te ikisi birden koşulup karşılaştırılır; karar verisi için).
- **Üretim parametre aralıkları (Pearl §4.8'den alınan, KÖK G katmanı için başlangıç):**
  rank `r ∈ {32..1024}`; `16r ≤ k ≤ 4r²`; `k ≤ 2¹⁶`; `64 | k`; `h·w ≥ 32`; `k(h+w) ≤ 2²²`;
  `m, n ≤ 2²⁴`. KÖK bunları **testnet kalibrasyonu** olarak alır, sabit olarak değil
  (TV-2'nin prescribed-hardness ölçütü her aralıkta yeniden koşturulur).
- **Doğrulama asimetrisi (gerçek sayılarla):** ZK-ACE Circle STARK backend: **14.5 ms prove /
  1.1 ms verify / ~107 KB proof** (2603.07974); genel programlar için zkVM (Prezta, RISC Zero):
  prove onlarca saniye / verify onlarca ms (2607.11466). **Agregasyon:** per-block STARK
  aggregasyonu ile consensus-visible veri **~160 byte/tx**.
- **Validator maliyeti:** 1.1 ms verify × blok; 10 BPS hedefinde bile saniyede ~11 ms — sürdürülebilir.
  **Önemli düzeltme:** "Doğrulayıcı enerji harcamaz" palavrası yok; gerçekçi bir maliyet tablosu
  spec'in parçasıdır.

---

## 6. Aritmetik ve Determinizm (v1'in "Çözülmez" dediği yer)

- **Bugün:** tüm ispatlanabilir iş **sonlu cisim / fixed-point** + **yayınlanmış hata bütçesi**.
  FP işler için hata eşiği aşılırsa görev reddedilir; bu, "verification-grade compute"un
  tanımıdır (premium niş).
- **Yarın (somut yol):** zkVM + **native BF16/FP32 precompile** (arXiv 2606.05433, **doğrulandı**:
  Peigné–Nguyen–Wang, "Zero knowledge verification for frontier AI training is possible", v2
  2026-08-22, 44 sayfa) olgunlaşınca ispat, **GPU'nun yaptığı gerçek kayan nokta hesabını**
  doğrular. Makale: pre-committed training spec + inter-node network observations + on-the-fly
  Merkle commitments + zkVM native BF16/FP32 precompiles; üç ispat tipi (genesis / in-training
  step / ex-ante attestation); **~36 ay deployable PoC, tek-haneli-% training-side overhead**
  iddiası, özel silikona karşı 6–10 yıllık döngü; 13 açık problem kataloğu. Bu, KÖK'ün
  **planlı, versioned geçişi** olur (§7'deki makineye tam oturur).
- **Determinizm:** pinned harness (kernel sürümleri, reduction order, seed) + Merkle trace
  commitment; GPU non-determinizmi (Hawkeye, MLSys 2026) için **üçüncü-taraf reproduksiyon
  denetimi** talep edilir; aynı sonucun CPU'da kayıpsız re-produksiyonu protokol standardıdır.
- **★ İki yol (2026-09-20, Pearl birincil kaynaktan; tam tablo spec §A.9b'de):**
  **Yol A = Hawkeye bit-exact replay** (MLSys 2026, Pearl mainnet'te üretimde; *Komargodski
  hem KW'nin hem Hawkeye'nin yazarı*) — **Faz 2 için karar**. **Yol B = Peigné native-FP zkVM**
  (~36 ay) — Faz 3. **Honest risk:** Yol A KÖK v2'yi GPU nesillerine bağlar (sm90 whitelist);
  whitelist genişletme governance'i Faz 2'de tanımlanmalı (§11 ASIC-merkeziyet endişesi
  gerçek, ama yönetilebilir).
- **★ Pearl FP şemasının yapısal farkı:** Pearl'de entrywise quantization nonlineer
  (`Q(A+N) ≠ Q(A)+Q(N)`) → düşük-rank kısayol bozulur → **ticket doğrudan çıktı tile'ını
  hashler, (n/r)³ transcript gerekmez**. KÖK'ün INT kerneli transcript'e bağlı kalmalı
  (INT'de kısayol açık, Assumption 6.4'ün konusu); transcript'siz tasarım FP'ye (Faz 3)
  ertelenir. **Jackpot policy (TV-11..TV-14) Yol A'nın üstüne inşa edilmiştir.**

---

## 7. Geleceğe Dayanıklılık: Crypto-Agility Doğru Katmanda

Migration, dört katmandır (DEGERLENDIRME_100.md §7'nin özeti) ve sadece **A katmanı** PVI'nin
sorumluluğundadır:

| Katman | Politika |
|---|---|
| **A. Proof system / verifier** | PVI + **versioned schema** + **çift-doğrulama penceresi** (eski+yeni N epoch) + **formal kapı** (Lean + ZEBRA-sınıfı otomatik doğrulama + denetim) + **madenciye 6–12 ay lead-time**. Kural: *sadece verifier değişiyorsa **iş fonksiyonu sabit kalmak zorunda*** — "seamless" ancak bunu tutarsa doğrudur. |
| **B. İş fonksiyonu** | **Mümkün olduğunca asla değiştirme.** Değişirse bu bir **hard fork'tur** ve madenci sermayesini sıfırlar (BTC SegWit/BCH, ETH merge/ETC dersleri). Değişiklik, en az 12 aylık sinyal + phased rollout + opsiyonel eski zincirle birliktelik gerektirir. |
| **C. İmza & hash** | **Bugünden PQ:** STARK/hash zaten PQ; imzalar **ZK-ACE** (identity-bound ZK yetkilendirme, chain'de imza nesnesi yok → kilobyte-scale PQC artifact'den kurtul). Hash değişimi = en patlayıcı eylem; sadece önceden-commit edilmiş acil durumda. |
| **D. Zorluk varsayımı** | **v1'in gözden kaçırdığı asıl risk.** KW ile prescribed hardness girdiden bağımsızdır (structured-matris kısayolu yok); FMM'ye (ω<2.371177) dayanıklı iddia. **Agility'nin koşulu, zorluğun yapısal olmasıdır** — KW bunu sağlar, düz Freivalds sağlamaz. |

**Acil durum makinesi:** Zincire önceden commit edilmiş bir **yedek proof system**; ses hatası
veya kırılma raporlanırsa (hardness monitoring + responsible disclosure), threshold aktivasyonuyla
`proof_system_id` değişir, eski doğrulayıcı emekli olur. **"Sıfır kesinti" değil, "planlı minimum
kesinti"** olarak iletişim kurulur — aksi iddia yanlış (v1'in hatası).

**Asla forksuz göç mümkün olmayanlar (dürüst liste):** iş fonksiyonu; emisyon politikası; PoW
hash'i; adres/imza formatı. Bunlar için migration planları **öncünden** yazılır.

### 7.1 ★ Pearl'in iki gerçek hard-fork'undan öğrenilenler (2026-09-20, birincil kaynak)

Pearl mainnet **iki kez hard fork** yaptı (`docs/moe-fork-upgrade-guide.md`,
`docs/salted-seed-fork-upgrade-guide.md`). Bunlar teori değil, **canlı bir zincirin üretim
prosedürleri** — ve KÖK v2 §7'sinin A katmanı için bir **sınıflandırma tablosu** veriyor:

| | **MoE fork (V1→V2)** | **Salted-seed fork (V2→V3)** |
|---|---|---|
| Ne değişti | dense → MoE sertifikası (fayda alanı genişledi) | noise seed türetmesi matris boyutlarına **keyed BLAKE3** ile bağlandı (grinding'e karşı) |
| **Eski madenci çalıştı** | **EVET** — "old dense proofs work before and after the fork" | **HAYIR** — "everything must be upgraded: node, ZK proving code, **and miners**" |
| Upgrade zorunlu olan | node + ZK proving kodu (sadece) | node + proving + **madenci** |
| Fork height | (rehberde TBD; V3'ten anlaşıldığıyla gerçekleşti) | **Mainnet 99.000** / Testnet 38.484 |
| Commitment | `double_sha256(cert_version_le32 ‖ public_data)` — **versiyon-önekli** | aynı, prefix 3 |
| Şablon mekanizması | `getblocktemplate` → `requiredcertversion`; **"fork height'ı hardcode etme, şablondan oku"** | aynı |

**★ Sınıflandırma kuralı (KÖK v2 §7 A katmanına alınan kalıp):**

> **Türetme madenciliğin kendisini beslemiyorsa → geriye uyumlu (soft-ish); besliyorsa →
> zorunlu (tüm katmanlar).**

Pearl bunu ampirik olarak ayırt etti: MoE sadece *verifier*'ın gördüğü sertifika *formatını*
değiştirdiği için eski proof'lar hâlâ geçerliydi; salted-seed ise *gürültünün nasıl
türetildiğini* değiştirdiği için — bu madencinin hesapladığı şeyi doğrudan etkiler — eski
madenci yazılımı fork'tan sonra **geçersiz share** üretti. **KÖK v2 bu ayrımı önceden
belirler:** her A-katmanı değişikliği için "türetme madenciliği besliyor mu?" sorusu spec'te
yanıtlanmak zorundadır; yanıt EVYESA upgrade zinciri (node→prover→miner) ve **fork height
önceden yayınlanır** (Pearl'in Testnet/Testnet2/Mainnet tablosu gibi); HAYIRSA eski madenciler
bir epoch boyunca paralel çalışmaya devam eder (çift-doğrulama penceresi).

**Alınan üç somut mekanizma:**
1. **Versiyon-önekli commitment** `H(cert_version ‖ public_data)` — KÖK'ün ctx-binding'ine
   (T-A2) üretim kanıtı: Pearl *iki fork'ta arka ardışık* bağlamayı güçlendirmek zorunda kaldı.
2. **`requiredcertversion` şablon alanı** + "hardcode etme, şablondan oku" kuralı — KÖK'ün
   `proof_system_id` mekanizmasının canlı öncülü: node yayınlar, madenci/pool okur.
3. **`check_cert_version_eligible` + `*_for_cert_version` dispatcher'ları + pinned test
   vector'leri** — KÖK'ün Faz 2'si için bir **implementasyon reçetesidir**: her proof system
   sürümü için ayrı prover cache, eski+yeni formatı ikili kabul eden `deserialize_compat`,
   ve fork öncesi "MoE share'i geçersizdir" (boşa kürek) kuralı.

**Asıl ders (fayda genişlemesi vs güvenlik tamiri):** Pearl MoE fork'uyla **fayda alanını
genişletti** (dense → MoE = yeni harness = yeni fayda). **KÖK v2 bunu fork'a gerek kalmadan
yapar:** U katmanı görev-odaklı olduğu için yeni bir inference harness (MoE, FP4, training)
**yeni görev tipi** olarak eklenir, G katmanına dokunulmaz. **Sadece güvenlik tamiri**
(seed türetmesi, commitment güçlendirme) fork gerektirir — ve Pearl bunu da önceden
duyurup pinned test vector'leriyle yaptı.

---

## 8. Ekonomi ve Para Politikası (2026 gerçeklerine göre)

> **2026-09-19: bu bölümün iddiaları artık çalıştırılabilir bir simülasyonla
> destekleniyor** — `pass_sim.py` (Pass 2606.06700 kapalı-form çözücü, Pearl kalibrasyonlu;
> çıktı `sim_out.txt`). Aşağıda **ölçülen** değerler kalın, teorik beklenti parantezli.

- **Kalibrasyon (en güçlü doğrulama kancası):** Pearl'in **canlı** ağı (320.000 GPU, 800
  blok/gün, 2.674 PRL/blok, $0,76) modelin Tullock tam-ödeme koşulu `eS = PR` ile
  yeniden üretildi: **S = PR/e = 338.707** vs ölçülen 320.000 GPU — **%5,8 sapma**;
  gelir/maliyet **1,058** vs Basu'nun ölçtüğü **1,06**. Yani model ilk ilkelerden gerçek
  bir ana ağı tahmin ediyor, törpülenmiş parametrelerle değil.
- **Emisyon:** **tail emission** — azalan ama **asla sıfır olmayan** blok ödülü (Monero/Grin
  geleneği). v1'in kopyaladığı Kaspa eğrisi 2026'da **tükenmiştir** (max arzun %96,5'i çıktı,
  kalan ~$40M). Güvenlik bütçesi sonsuz ufukta sıfıra düşmemeli.
  *Ölçüm (sim §5):* halvings ile ekonomi Duplexia → Fortessia'ya iner (~14. yıl) ve saldırı
  maliyeti tail `R_∞ = 2` PRL ile **$0,76 tabanına** oturur — Kaspa gibi **sıfıra gitmez**.
- **Hazine:** blok ödüllerinin **%5–8'i** geliştirme fonuna (escrow + milestone-gated vesting).
  Fair launch ile **çelişmez** (Kaspa da böyle yürüdü); VC yok, ön madencilik yok, kurucuya
  bedava token yok. Bu olmadan §11'deki Ar-Ge finanse edilemez.
- **Görev-fee pazarı:** klientler görev fee'si öder (duplex model); madenci = task fee + blok
  ödülü. **Talep sıfırken (c) sınıfı pure-PoW filler** ile zorluk korunur; bu rejim spec'te
  yazılıdır (Pass'ın "Bitconia" düşüşü).
  *Ölçüm (sim §6):* talep çökerse (`K→0`) `Q→0` ama **S → PR/e = 338.707** — zincir
  pure-PoW olarak yaşar, güvenlik Bitcoin-eşit kalır (Demirel Thm 2 ✓). **Fayda sıfırdır,
  güvenlik değildir** — "faydalı iş = güvenlik" vaadinin olmadığının resmi itirafı.
- **Hedeflenen rejim:** **Fortessia** (güvenlik artar, faydalı çıkış korunur). Parametreler
  (`token-inference ratio`, duplex overhead) yayınlanır ve zincir üstü simülasyonla denetlenir.
  *Ölçüm (sim §3):* aynı θ'da güvenlik tam **1/(γ(1−1/α)) = 3,33×** artar, faydalı çıkış aynı
  (theori ile birebir; α=γ=1,3).
- **Saldırı maliyeti:** her rejimde **PR/2** (Pass Thm). *Ölçüm:* heterojen maliyette (b=1)
  toplam S %38 düşse de akım saldırı maliyeti hala **PR/2 = $1.016** — stok etkileri
  (donanım yeniden satış değeri) modelin dışında, Pass'in açık sınırı.
- **Pearl'den alınan acı ders:** Pearl'in gerçek PR seviyesi endojen **θ = 1,05 → saf
  Duplexia** rejimi; yani ekonomisi **inference'ı süside etmesi gereken rejimdeydi** — ama
  ölçülen **φ = 0**: fayda hiç gerçekleşmedi. Sebebi **E-gap** (Demirel 2026/1492): protokol
  matrislerin kimsenin işi olduğunu certify edemedi. **Pearl Bitconia gibi davrandı,
  Duplexia gibi pazarlandı.** KÖK v2 bu açığı G/U ayrımıyla mimariye yedirir (§3.2).
- **Taahhüt:** emisyon eğrisi bir kez yayınlanır, **gelecekte değiştirilemez** (değişiklik en
  büyük güven sinyali kırılmasıdır; lütfen v1'in "lansman öncesi kesinleştirilecek" rahatlığını
  kaldır).

---

## 9. Hukuk ve Uyum

- **"AI'ya endeksli" ifadesi kaldırıldı.** Yerine: **protokol, doğrulanabilir hesaplama
  yerleşim katmanıdır**; token'ın değeri ağ güvenliğine ve görev fee pazarına bağlıdır.
  Howey analizine göre bu framing, "yatırım getiri vaadi"ni zayıflatır (ancak kaldırmaz).
- **TR:** kripto varlık hizmet sağlayıcı lisans rejimi (2025'ten yürürlükte) listeleme/custody
  için geçerli; madencilik ve fair-launch promotion'ın durumu ayrı başlık olarak yasal
  danışmanca netleştirilmeli (bu dokümanda **doğrulanmadı**, bir açık noktadır).
- **AB/AI Yasası + ABD compute raporlama:** §3.2(a)'daki governance-proof pazarının **regülatif
  rüzgârı** budur; ters rüzgâr (verification talebinin regülasyonsuz kalması) senaryosu için
  risk kaydında yer ayrılır.
- **Protokol ↔ promosyon ayrımı:** protokol açık kaynak ve ekipten bağımsızdır; promosyon
  hiçbir getiri vaadi içermez. "AI washing" eylemleri (SEC) başlıca uçtur.
- **★ 2026-09-20: Pearl'in Polymath Ekonomik (2) ile kesişim — uyum avantajı mi, riski mi?**
  Pearl kendisi üç uygulama listeler: **(a) AI ajanlar için oylama sistemi** (async koordinasyon,
  GPU finansmanı, compute marketplace), **(b) model tracing** (retroaktif inference ispatı, ZK),
  **(c) "compute için stablecoin"** ("Bitcoin enerjiyi dolar sistemi dışında ticaret yapıyorsa,
  Pearl compute'ı"). KÖK v2'nin escrow+burn görev pazarı **(a) ve (c)'nin altyapısı olabilir** —
  ama bu, dokümanın **kasten ertelediği** bir alan: **(a) oylama = protokol-üzeri uygulama**,
  KÖK v2 scope'unda değildir (protokol sadece görev-pazarı + konsensüs sağlar; uygulama
  katmanı üçüncü taraflarındır). **(c) compute-stablecoin ise KÖK v2'nin bilinçli olarak
  iddia etmediği bir şey** — "stable" kelimesi, bir token'ı compute'a sabitleme vaadi
  **değil**, yalnızca "compute'ı token ile ticarete açma" anlamında kullanılır. **Hukuki
  disiplin: KÖK v2 hiçbir uygulamayı vaat etmez; sadece altyapıyı.**
- **★ Regülasyon zorunlu değil, ama uyum avantandır.** Polymath'in "model tracing" uygulaması
  ile KÖK v2'nin provable-inference görevleri **aynı regülatif talebi** (AB AI Yasası
  madde-level dokümante edilmiş hesaplama; ABD compute raporlama) karşılar. Yani KÖK v2'nin
  U katmanı, eğer regülasyon gelirse **zaten uyumlu altyapıdır** (first-mover avantajı);
  gelmezse **fayda talebi opsiyoneldir** (G katmanı yine de ayakta). **Bu, KÖK v2'nin
  regülasyonu risk olarak değil, opsiyonel olarak konumlandırılmasını sağlar** — en kötü
  durum "sadece dürüst bir GHOSTDAG PoW" olur (§11 md.3).

---

## 10. Kanıt, Denetim ve Yol Haritası

| Faz | İçerik | Ölçüt (tanımlı başarı) |
|---|---|---|
| **F1 — Formal spec** | statement schema, görev pazarı protokolü, GHOSTDAG+rejection-sampling spec, ekonomik model | Bağımsız kriptograflarca walk-through; T1–T6 iskeletleri. **✅ kâğıt üstü tamam: `KOK_V2_TEKNIK_SPEC.md`** |
| **F1b — Çalışan prototip** | görev yaşam döngüsü + ceza ekonomisi + difficulty retarget | **✅ `u_layer_prototype.py` (TV-5..TV-10), `g_layer_tests.py` (TV-1..TV-4, RT-1..RT-3) — hepsi PASS** |
| **F2 — Ses doğrulaması** | AIR'nin Lean ile doğrulaması + ZEBRA-sınıfı kardinalite kontrolü | Under-constrained bug = 0 (üçüncü taraf denetim) |
| **F3 — Devnet** | `kok-node` (Rust), S-two/Circle STARK verifier, görev pazarı, filler görevler | 10 BPS, verify ≤2 ms/blok, difficulty 7 günde hedefe yakınsar |
| **F4 — Ekonomik simülasyon** | Pass modelinin zincir-üstü simülasyonu (3 rejim) | Zero-demand senaryosunda pure-PoW moduna kontrollü geçiş. **✅ kapalı-form çözücü: `pass_sim.py` — Pearl kalibrasyonu %5,8, Fortessia ×3,33, zero-demand S→PR/e, tail $0,76** |
| **F4b — Kriptografik analiz** | KW conjecture'ının bağımsız değerlendirmesi | **✅ `KW_ANALIZ.md`: risk yüksek → düşük-orta (Varsayım 6.4 gerekli değil; asıl risk E-gap)** |
| **F5 — Testnet + madenci** | açık testnet, `kok-miner`, ekosistem görev kanalları | 1000+ madenci, gerçek (a)/(b) görevlerinden ≥1 ödeyen talep |
| **F6 — Denetim + mainnet** | 2 bağımsız güvenlik denetimi + bug bounty | Kritik bulunmamış; madenci ekosistemi 6 ay stabil |

### 10.1 ★ Testnet roadmap'i — özellikle "protokol-dışı testnet" (2026-09-20)

§12.1'in stratejik sonucu şunu söyler: **hızlı olması gereken şey mimari değil, prototipin
protokol-dışı bir testnete çıkmasıdır** (Pearl'in fayda alanını genişletme riskine karşı).
O yüzden F3'ü **iki alt-faza** böleriz:

| Faz | İçerik | Ölçüt | Süre (hedef) |
|---|---|---|---|
| **F3a — Ekonomi testnet'i (protokol-dışı)** | Sadece **U katmanı**: görev pazarı + escrow/burn/slash + VRF ataması, **konsensüzsüz** — merkezi bir sıralayıcı (mock leader) blok üretir, G katmanı yerine dummy proof. Token'lar test token'ı. Amaç: **gerçek talep ve ceza ekonomisini ölçmek** — KÖK'ün en ölçülmemiş varsayımı budur (φ>0). | ≥1 **gerçek ödeyen** görev; slashing tetiklenen bir saldırı vaka; escrow iade oranı ölçülür | **3–4 ay** (kriptograf incelemesiyle paralel) |
| | **★ Çalışan prototip (2026-09-20): `f3a_sequencer_proto.py` — TV-15..TV-19 hepsi PASS: iade-garantisi, görev-göçü, sansür-ucretsizlik, dilemmasız doğrulama, honest yaşam döngüsü.** Toy sınırları dosyada. |
| **F3b — Konsensüs devnet'i** | `kok-node` (Rust), GHOSTDAG parent-set seçimi, KW per-tile G katmanı, difficulty retarget (pencere+medyan), filler görevler (φ=0). **Tüm protokol**, gerçek proof'larla. | 10 BPS, verify ≤2 ms/blok, difficulty 7 günde hedefe yakınsar (F3'ün orijinal ölçütü) | F3a'dan sonra **4–6 ay** |
| **F5 — Açık testnet** | İkisi birleştirilir; `kok-miner`; ekosistem görev kanalları. | 1000+ madenci, gerçek (a)/(b) görevlerinden ≥1 ödeyen talep | F3b'den sonra **3–4 ay** |

**★ Neden F3a önce (dürüst gerekçe):** F3b'nin (kriptografi) başarısı `KRIPTOGRAF_BRIEF.md`'in
sonucuna bağlı ve **zamanlama olarak dışsal** — biz hızlandıramayız. F3a **sıfır kriptografik
risk** taşır (dummy proof) ve KÖK'ün **en büyük ölçülmemiş varsayımını** (φ>0: kimse gerçek
AI inference için fee öder mi?) ölçer. Pearl'in φ=0 sonucuna bizim cevabımız **mimari + gerçek
talep ölçümü** olmalı; sadece mimari yetmez. **Ayrıca F3a, G katmanı hazır olmadan pazar
geçerliliğini sınayan tek yoldur** — eğer kimse ödemezse, KÖK v2'nin "devrim değil, dürüst bir
GHOSTDAG PoW" olacağı (§11 md.3) **henüz F3b'ye yatırım yapmadan** öğrenilir.

**★ Ölçüm metrikleri (F3a, zincir-üstü yayınlanır):** görev başına ortalama fee; escrow
tutma süresi; slashing olay sayısı; **gerçek ödeyen kullanıcı oranı** (toplam görevlerin
% kaç'ı gerçek AI workload'u); verifier's dilemma tetiklenme sayısı (spec §A.5).

**★ DÜRÜST LİMİT (kanca testinden bulundu, `pass_sim.py` §9):** F3a'nın küçük ağ verisi
(~1200 madenci), `pass_sim.py`'i **yeniden kalibre edemez** — model Pass Thm 2'nin
"competitive equilibrium" varsayımına dayanır ve küçük ağlarda sabit maliyetler marjinal
maliyetleri domine eder (hipotetik test: **%86 sapma**). Pass'in kendi kalibrasyonu $30B
inference pazarına ve 52.560 blok/yıl'a dayanır; F3a bu ölçeğin dışındadır. **O yüzden
F3a'nın rolü nettir:** U katmanının talebini (φ>0) ölçer — **Pass modelini değil**. Pass
kalibrasyonu **mainnet ölçeğinde** geçerlidir (Pearl %5,8 ile kanıtlandı) ve F3a'dan
**beklenen** sıfır-φ sonucu, modelin "Bitconia" düşüşü ile tutarlıdır, onu kalibre etmez.
Bu, `pass_sim.py`'nin §9'unda çalışan bir regression-guard ile sabitlendi (Pearl %5,8
korunuyor).

**★ Risk (dürüst):** F3a'nın merkezî sıralayıcısı, testin **asıl değerini sınırlar** —
merkezi sıralayıcı sansür edebilir ve bu, U katmanının **sansür direncini** ölçmez. O yüzden
F3a'ya bir **sansür direnci ölçütü** eklenir: sıralayıcı kasıtlı olarak görev X'i reddettiğinde,
sistemin (görev sahibi → alternatif sıralayıcı → iade) yolunun çalıştığı gösterilir. Bu, F3b'de
GHOSTDAG ile değiştirilecek olan **geçici** bir merkezîliktir ve dokümanda açıkça "test
sınırlaması" olarak yazılır.

---

## 11. Bilinen Sınırlar ve Kâğıdın Tavanı

Dürüst olmayan bir 100/100 iddiası olmaz; bu doküman şunları kabul eder:

1. **Enerji hâlâ harcanır ve "faydalı iş güvenliği artırmaz".** 2026'nın üç çalışması bunu
   zorunlu kıldı: SoK (2025/1814) "utility güvenlik bütçesine katkı vermez"; Demirel
   (2026/1492) leader-election'ın **talepten bağımsız** olması gerektiğini ispatladı (Thm 2);
   Basu (2606.04819) Pearl'in **24 EH/s'lik canlı ağının sıfır faydalı hesap ürettiğini** ölçtü.
   KÖK v2 bunu dürüstçe mimariye yedirdi: güvenlik talepten bağımsızdır (G katmanı), fayda
   sadece **fee-ödemeli** U katmanında gerçekleşir. **"Faydalı = güvenli" satılmaz.**
2. **Kriptografik bağımlılık tek noktada:** KW'nin prescribed-hardness güvenliği bir
   **conjecture**'dır (low-rank random linear equations). Çökerse ağ pure-PoW fallback'e düşer
   (spec §A.9) ama "faydalı iş" iddiası o an ölür. **2026-09-20 PDF doğrulaması sonrası risk
   düşük-orta:** `KW_ANALIZ.md` §6, KW'nin *kendisinin* Assumption 6.4 için "the number of bits
   needed to write down all intermediates – **Θ(n³/r)** – is always a lower bound on the running
   time" dediğini birebir çıkardı — yani varsayım, standart bir **çıktı-boyu alt sınırıyla**
   neredeyse otomatik olarak sağlanır (benim bağımsız §3.1 gözlemimle aynı sonuç). Ayrıca
   Lemma 6.5 (ROM'da E,F üniform rank-r) ve **α = o(1)** overhead birebir teyit edildi.
   Conjecture A.1 (random-rotation alternatifi) **hâlâ kanıtlanmamış** — Pearl'in kendi
   Polymath Problem (1) "Is this secure?" diye soruyor; ana gövde bunu kullanmaz. Tüm
   yapısal saldırılar ve trapdoor-matrix literatürü çürütüldü. **Ama bu bir LLM okumasıdır —
   2 bağımsız insan kriptograf incelemesi hâlâ zorunludur** (F2/F6).
3. **U katmanı talep riski:** governance-proof ve provable-inference talebi **regülasyona ve
   pazar eğilimine** bağlıdır. Olmazsa ağ "sadece dürüst bir GHOSTDAG PoW" olur — ki o bile
   Kaspa\'dan (emisyon tükendi) ve Pearl\'den (fayda iddiası çöktü) iyi bir konumdadır, ama
   **devrim değil**.
4. **Pearl ile çekirdek paylaşımı:** KW yapısını her ikisi de kullanır. KÖK v2\'nin katkısı
   **E-gap\'i kabul edip mimariye yedirmektir** — Pearl\'in yapamadığıdır. **2026-09-19
   birincil-kaynak düzeltmesi:** Pearl\'in kendi §7 benchmark\'ı coupling\'in overhead\'siz
   olabildiğini gösteriyor (Pearl-certified Llama 3.3 70B, Meta\'dan +12,7% hızlı, 806
   TMADs/sn faydalı iş). O halde canlı ağda ölçülen φ=0\'nın sebebi **overhead değil,
   workflow hizalamasıdır**: certified yol belirli modelleri plugin ile çalıştırmayı
   gerektirir, permissionless madencinin optimumu raw filler\'dır; faydalı iş Pearl\'in
   **ayrı** hosted inference işinde gerçekleşir. Pearl\'in eksikliği teknik değil
   **mimariseldir**: marketplace\'i whitepaper §1\'de gelecek vizyon olarak bırakması
   (escrow/bond/burn/anti-aggregation yok). KÖK v2 bunu kurar — detay §12\'de.
5. **FP doğrulama: iki yol, ikisi de henüz KÖK'te çalışmıyor.** Pearl yolu (**Hawkeye
   bit-exact replay**, MLSys 2026, üretimde) **bugün kanıtlanmış** ama KÖK v2'yi GPU
   nesillerine bağlar (sm90 whitelist; whitelist genişletme governance'i tanımlanmadı — bu
   alt maddenin kendisi bir sınırdır). Native zkVM yolu (arXiv 2606.05433) **~36 ay**
   horizonu. O güne kadar: fixed-point + hata bütçesi + INT KW kerneli (transcript'le;
   Pearl'in FP şemasındaki transcript'siz tasarım FP'ye ertelendi, spec §A.9b).
6. **Kâğıdın tavanı ~85/100.** Kalan 15 puan **kanıtladır**: F3–F6'nın ölçütleri, canlı güvenlik
   bütçesi, gerçek ödeyen görev talebi, bağımsız denetimler. **Kusursuz bir kâğıt, çalışan bir
   zincire eşit değildir** — bunu dokümanın başına yazmaktır ki mükemmelliyetçilik dürst olsun.

---

## 12. Farklılaşma (2026 öncül sanatına karşı)

> **2026-09-19 güncelleme:** Pearl artık **birincil kaynaktan** karşılaştırılıyor
> (INT whitepaper + canlı site + GitHub; bkz. `PEARL_DOCS_ANALIZ.md`). Önceki tablo
> yalnız Basu'nun ölçümüne dayanıyordu; şimdi Pearl'in kendi belgeleri de var.

| | **KÖK v2** | **Pearl Network (canlı, birincil kaynak)** | HadAgent (2604.18614) | SNARKChain (2510.09729) | Kaspa |
|---|---|---|---|---|---|
| Güvenlik kaynağı | **talepten bağımsız PoW** (filler + memoryless) — Demirel Thm 2 ✓ | **"faydalı iş"** (E-gap mimaride karşılanmaz) | deterministic inference | SNARK marketplace | amaçsız hash |
| Fayda kaynağı | **sadece fee-ödemeli görevler** (escrow + bond + **burn**) | madencinin seçimi → **ölçülen: sıfır**; fayda hosted inference işinde | inference kendisi | piyasa | yok |
| İş | KW MatMul PoUW (G) + zkVM ispat (U) | **KW INT kernel** (r ∈ {32..1024}, 16r ≤ k ≤ 4r²) | deterministic LLM inference | SNARK proof | hash |
| Overhead | 1+o(1) (G) / yüksek (U) | 1+o(1); **certified modellerde +12,7% throughput** (kendi benchmark'ı) | 1:1 re-execution | yüksek | n/a |
| Konsensüs | **GHOSTDAG (BlockDAG)**, ~10 BPS hedefi | **Bitcoin fork: UTXO + linear longest-chain, 194 sn blok (GHOSTDAG YOK)** | tek zincir | tek zincir | **GHOSTDAG** |
| Zorluk | **pencere + medyan filtre** (RT-1..3 doğrulandı) | **WTEMA** (per-block EMA, 7-gün decay) | deterministik | "—" | klasik |
| Kriptografi | **PQ seti zorunlu** (TV-10) + Lean/ZEBRA + agility + acil fallback | Plonky2 ZK (input gizliliği!); **XMSS rezerve ama devre dışı**; P2MR | re-exec | SNARK | hash |
| Ekonomi | **tail emission (R_∞ tabanı)** + %5 hazine + Pass simülasyonu | S=2,1M; **1/t² polinomsal (halving yok, R(t)→0 — tail YOK)**; 24 EH/s, 1,06× gelir/maliyet | — | marketplace | **tükendi** (%96.5) |
| Görev pazarı | **escrow + bond + burn + C_FEE anti-agg + VRF + W_s=100** | **YOK** — marketplace §1'de gelecek vizyon | — | var | yok |
| **Novel** | **E-gap'i mimariye yedirmek: güvenlik ≠ fayda** | **ilk KW uygulaması; kendi iş modeli fiilen G/U ayrımı** (inference platformu + zincir) | PoI consensus | PoUW + binding | GHOSTDAG |

**Dürüst ifade:** **Pearl Network, KÖK v1 fikrinin akademik-commerical sahibidir** (KW = Komargodski
& Weinstein; ekonomi = Pass'ın danışmanlığı) — ve **canlı bir PoUW zinciri olarak tek örnektir.**
Ama Basu (2606.04819) onu ölçtü: **24 EH/s, ~320 bin GPU, ~112 MW → sıfır faydalı AI hesaplaması**;
doğrulama rastgele matrisleri kabul ediyor (44 havuz-onaylı share, NVIDIA/AMD/CPU/Apple Silicon);
madenci yazılımında inference kodu yok (0/4.803 string); GPU kira fiyatları +%38, araştırmaya
**~$600K/yr deadweight loss**; madenciler >%200 volatilite altında "call option" için kazıyor.

**Pearl'in kendi belgeleri bunu nasıl açıklar (2026-09-19, önemli):** Pearl'in §7 benchmark'ı
**Pearl-certified Llama 3.3 70B'nin Meta'nın orijinalinden DAHA HIZLI** olduğunu gösteriyor
(17.206 vs 15.270 tok/s, 4×H200, PP=4; MMLU 0.8190 vs 0.8198) ve **806 TMADs/sn** faydalı iş
üretiyor — madencilik quantization kütüphanesinin kendisi, yani **coupling'in maliyeti yok**.
O halde canlı ağda φ=0'nın sebebi **overhead değil, workflow hizalaması**: certified yol belirli
modelleri plugin ile çalıştırmayı gerektirir; permissionless madencinin ekonomik optimumu raw
filler'dır. **Faydalı iş Pearl'in hosted inference işinde (pearlresearch.ai + Together AI'da
%25+ ucuz Gemma-4-31B-it-Pearl endpoint'i) gerçekleşir; zincirin madencilerinde değil.**
Pearl'in hatası: **"faydalı iş = güvenlik" pazarlayıp E-gap'i mimariye yedirmemek** — kendi
iş modeli fiilen G/U ayrımıyken, zincirde bunu bağlamamak. KÖK v2 tam da bu bağlamayı kurar:
**Demirel'in geri-alamaz burn'u ile görev-pazarı** (Pearl'in whitepaper'ında yok) + **GHOSTDAG**
(Pearl'de yok) + **tail emission tabanı** (Pearl'in 1/t²'si sıfırlanır, KÖK'ünki gitmez) +
**PQ zorunlu gate** (Pearl XMSS'i rezerve bırakır).

**★★ Pearl'in kendi E-gap itirafı (20 Eylül 2026, birincil kaynak):** Pearl'ün açık problem
sayfası "Polymath Project" (*pearlpolymath.com*) Ekonomik Problem (1)'de itiraf ediyor:

> "A common criticism of (0-overhead) PoUW is that the **marginal cost of mining is ~0 and
> hence also the cost of attacking the network**. However, the last statement is only true if
> one has an **infinite stream of useful work**—i.e., the ability to collect AI workloads for
> which an external consumer is willing to pay. This observation highlights the difference
> between Pearl and Bitcoin—**the key 'scarce' resource in PoUW mining is the ability to
> collect useful data (matrices)**. ... **What should be the value/price of the Pearl coin at
> 0 mining overhead? Is it 0? infinity?**"

**Bu alıntı, bu dokümanın tezinin birincil kaynakla doğrulanmasıdır.** Pearl E-gap'in
farkında ve savunması **ekonomik**: "kıt kaynak = faydalı veri toplamak". Ama Basu'nun
ölçtüğü φ=0 dünyada (hiç kimse matris göndermiyor) bu savunma **çöker** — talep depresyonunda
"kıt kaynak" ucuzlar ve saldırı maliyeti düşer; Pearl'in kendi sorusu ("Is it 0?") bunu
sorguluyor. **KÖK v2'nin cevabı protokol-seviyesindedir:** Demirel'in geri-alamaz burn'u,
talepten bağımsız olarak güvenlik bütçesini sabitler. **İki cevap arasındaki fark KÖK'ün
"novel" iddiasının özüdür: Pearl pazarın merhametine güvenir, KÖK kriptografiye.** (Tüm
açık problemler için `PEARL_DOCS_ANALIZ.md` §11.2.)
### 12.1 Rakip hamle senaryoları (Pearl ne yaparsa KÖK v2 nerede kalır?)

Pearl'in **kendi açık problem listesi** (Polymath) bir yol haritasıdır; her birine karşı
KÖK v2'nin konumu **önceden** yazılmalıdır — aksi halde "farklılaşma" iddiası bugüne özeldir:

| Pearl hamlesi | Olasılık | KÖK v2'nin hâlâ farklı olduğu | Tehdit derecesi |
|---|---|---|---|
| **Training'e uzanır** (Polymath 4: cuPOW inference-only; SGD robustness conjecture) | orta-yüksek | **U katmanı görev-odaklıdır**: training görevi, KÖK'te yeni *görev tipi* olarak eklenir; G katmanına ve fork'a dokunulmaz. Ama Pearl bu hamleyi yaparsa **ilk olma avantajını kaptırır** — KÖK'ün zamanlaması Faz 2'ye bağlı. | **YÜKSEK zamanlama riski** |
| **U_layer benzeri escrow/burn ekler** (marketplace §1'den protokole taşınır) | düşük-orta | O zaman Pearl ve KÖK v2 **aynı mimariye** kavuşur; geriye KÖK'ün **GHOSTDAG + tail emission + PQ-zorunlu-gate + WTEMA-alternatifi** kalır. Fark azalır ama sıfırlanmaz. | ORTA (farklılaşmanın yarısı erer) |
| **FP4'e geçer** (Polymath 3: NVFP4 scale optimizasyonu) | yüksek (FP8'den sonraki doğal adım) | **KÖK v2 için irrelevant**: U katmanı her precision'ı görev tipi olarak kabul eder; G katmanı INT/FP8 sabit. Pearl FP4'te olsa KÖK'ün G katmanı aynı. | DÜŞÜK |
| **Polymath (1) random-rotation'ı ispatlar** | düşük (kendileri bile sorguluyor) | KW ana gövdesini değiştirmez; sadece Appendix A alternatifi. KÖK yine §6.5 instantiation'ı kullanır. | DÜŞÜK |
| **ASIC-resistance'ı çözer** (Polymath 6: "1-bit hardware enough?") | orta | **DİKKAT — bu KÖK için de açık**: KÖK v2 G katmanı da MatMul tabanlı; low-entropy donanım saldırısı **her iki protokolü de** etkiler. **TV-21 ölçtü (2026-09-20):** INT toy'da saldırı 10→400 peak taramasında **0/10 geçer** — ama bu sonucun FP8'de **kanıt olmadığını** itiraf ediyoruz: toy'un RMS-gürültü modeli FP8'in per-tensor scale sıkıştırmasının **tersi** yönde (Pearl wp §5.1.2). FP8'de noise modeli quantization-aware yeniden yazılmalı (Faz 3, Yol A). Üretimde **Hawkeye whitelist + jackpot policy** birlikte savunur. | ORTAK RİSK — INT toy'da dayanıklı, FP8'de **AÇIK** |
| **0%-overhead whole-model PoI'ı güvenli kılar** (Polymath 7) | düşük (SNARK yok, backdoor açık) | Pearl bunu başarırsa "2-for-1" tam anlamına ulaşur — ama **E-gap'i kapatmaz** (güvenlik hâlâ talebe bağlı). KÖK v2'nin Demirel ayrımı hâlâ geçerli. | DÜŞÜK |

**★ Stratejik sonuç (dürüst):** KÖK v2'nin farklılaşmasının **yarısı mimari (E-gap + GHOSTDAG +
tail + PQ), yarısı zamanlamadır.** Pearl'in Polymath listesi gösteriyor ki Pearl **mimari
olarak E-gap'i kapatmaya yaklaşmıyor** (hiçbir problem escrow/burn/anti-aggregation içermiyor);
ama **uygulama alanlarında (training, FP4) ilerliyor.** Yani tehdit "Pearl KÖK olur" değil,
**"Pearl fayda alanını genişletirken KÖK hâlâ kâğıtta kalır"** — bu yüzden Faz 2'nin zamanlaması
(paylaşım prototipi → testnet) farklılaşmanın kendisi kadar kritiktir. **KÖK v2'nin "hızlı
olması gereken" şey mimari değil, PROTOTİP'in protokol-dışı bir testnete çıkmasıdır.**

KÖK v2'nin iddiası KW çekirdeğini icat etmek **değildir**; şu katmanları inşa etmektir:
**(i) güvenliğin talepten bağımsızlığı** (filler + memoryless difficulty → Demirel Thm 2'yi
construction-level karşılar), **(ii) faydanın yalnızca fee-ödemeli görevlerle tanımlanması**
(E exogenous-by-construction: escrow + geri-alamaz burn), **(iii) GHOSTDAG paralelliği**,
**(iv) formal-doğrulanmış PQ agility düzlemi** (Lean + ZEBRA + acil fallback), **(v) Pass
modeliyle yayınlanmış tail-emission ekonomisi**. Tüm öncüller atıflıdır; **Pearl'in çöküşü bu
farklılaşmanın zorunlu olduğunu kanıtlar.**
---

## 13. Kaynaklar (20 Eylül 2026, canlı)

> **Doğrulanmış tam liste + erişim notları için: `KAYNAKLAR.md`** (ePrint PDF raw binary verir,
> tam metin için ar5iv.org kullanılır). **Çalışan kanıtlar:** `pass_sim.py` (Pass ekonomisi,
> Pearl kalibrasyonlu), `u_layer_prototype.py` + `g_layer_tests.py` (protokol prototipi),
> `KW_ANALIZ.md` (kriptografik analiz), `KOK_V2_TEKNIK_SPEC.md` (formal spec).

**Çekirdek kriptografi:** ePrint 2025/685 = arXiv 2504.09971v4 (Komargodski–Weinstein,
MatMul PoUW) · arXiv 2502.13065 + 2502.13060 (trapdoor matrices, LPN — tehdit olarak
değerlendirildi, çürütüldü) · 2404.16349 (ADV+24, ω<2.371339) · Pearl Network
(KW üzerine kurulu, inşa halinde) ·
PoUW/ekonomi: 2606.06700 (Pass, tam model) · 2606.04819 (Basu, Pearl'ün ölçümü) · ePrint
2026/1492 (Demirel, PoD≠PoW) · ePrint 2025/1814 (SoK) · 2510.09729 (SNARKChain) · 2505.21685 (external
utilities) · 2405.19027 · 2209.03865 · 2512.13666 (SEDULity) · 2404.09005 (incentive security) ·
İş/uygulama: 2604.18614 (HadAgent) · 2606.05433 (frontier-AI ZK) · 2605.30040 (token inflasyon) ·
2603.19025 (SaTML) · 2602.17452 (Jolt Atlas) · 2506.11458 ·
İspat/PQ: 2606.04311 (S-two Lean) · 2603.07974 (ZK-ACE) · ePrint 2024/1731 (Arc) · 2501.05500 ·
Güvenlik/zkVM: 2609.15020 (ZEBRA) · 2605.25493 (ZK-Tracer) · 2607.11466 (Prezta) · 2603.20421
(Hawkeye = Pearl'in FP doğrulama yolu, MLSys 2026) · 2606.16146 (NTT vs SumCheck) ·
**Pearl birincil:** pearlresearch.ai/research/int-whitepaper · pearlpolymath.com · github.com/
pearl-research-labs/pearl · Pass 2606.06700 · Basu 2606.04819 ·
DAG: 2018/104 (PHANTOM) · 2109.01102 / 2305.16757 / 2501.10888 ·
Zorluk: 2608.16884 (ω<2.371177) ·
Piyasa: CoinGecko (BTC/KAS/TAO/RNDR/AKT/DNX) · Digiconomist · blockchain.info
