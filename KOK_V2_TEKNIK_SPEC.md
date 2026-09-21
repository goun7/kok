# KÖK Network v2 — TEKNİK SPEC: Görev Pazarı, Difficulty Matematiği, Ekonomik Simülasyon

**Tarih:** 21 Eylül 2026 · **Üst doküman:** `PROJE_KAGIDI_V2.md` · **Durum:** Formal spec (Ek A/B/C)

> Bu doküman, v2 tasarımının üç kritik alt sistemini "kâğıt üzerinde mükemmelliyet" ölçüsünde
> formal olarak belirler. Temel kriptografik bağımlılık: **Komargodski–Weinstein MatMul PoUW
> yapısı (IACR ePrint 2025/685)**; ekonomik bağımlılık: **Pass PoUW denge modeli (arXiv
> 2606.06700)**. Her iki kaynağın da henüz bağımsız doğrulamamış olduğu kısımlar **açıkça
> "conjecture/bağımlılık"** olarak işaretlenmiştir (§A.9, §C.7).

---

# EK A — GÖREV-PAZARI PROTOKOLÜ (Resmi Spec)

## A.0 İş fonksiyonunun kriptografik tabanı

**Seçim:** Komargodski–Weinstein "Proofs of Useful Work from Arbitrary Matrix
Multiplication" (ePrint 2025/685 = **arXiv 2504.09971v4**, 2025-04-15, v4 2025-11-13).
**Bağımsız analizi: `KW_ANALIZ.md` (2026-09-19).**

**Neden:** KW, **madencinin kendi girdisini seçtiği** permissionless ayarda MatMul için PoW
sertifikası verir: **1+o(1) multiplicative overhead** (naive MatMul'a göre), **prescribed
hardness** ve "hızlı matris çarpımı algoritmalarına" (FMM; ω<2.371339 [ADV+24 arXiv
2404.16349]; AlphaEvolve ω<2.371177, 2026) karşı dayanıklılık iddiası. KÖK v1'in kullandığı düz
Freivalds denklemi `A(Br)==Cr`, KW'nin açıkça **"O(1)-factor overhead her görev için trivial
ama işe yaramaz"** dediği construction'dır: doğrulama asimetrisi vardır ama **prescribed
hardness yoktur** → hileli madenci kolay girdi seçerek (structured matrix) dürüst madenciye
göre asimetrik avantaj kazanır. KW bu açığı kapatır.

**Resmi hedef (spec dili):** İş fonksiyonu `W(A,B; ctx)` = KW sertifikası; özellikleri:
- **(P1) Prescribed hardness:** geçerli sertifika üretmenin beklenen maliyeti `h(n)` FLOP'dur
  (n×n MatMul için `h(n) = Θ(n^3)` naive; FMM algoritmaları pratiğe uygulanmadığı sürece), girdi
  seçiminden **bağımsız** olarak.
- **(P2) Near-zero overhead:** dürüst üretim maliyeti `1+o(1)` katı.
- **(P3) Verifiability:** sertifika `O(polylog)` boyutta, `O(n²)` veya daha ucuz doğrulama.
- **(P4) Chain-binding:** sertifikanın statement'ı `ctx` içerir (§A.4).

> **⚠ BAĞIMLILIK (dürüst):** KW'nin güvenliği bir **conjecture**'dır — "batch of low-rank random
> linear equations" probleminin sertliğine indirgeme. Bu, protokolün tek kriptografik
> varsayımıdır (random oracle ile birlikte) ve **bağımsız kriptografik incelemeyi gerektirir**
> (Faz 2 ölçütü). Spec, bu conjecture çökse bile ağın çökmemesi için §A.9'da bir fallback
> tanımlar.
>
> **2026-09-19 bağımsız analiz (özet, tam: `KW_ANALIZ.md`):** bu conjecture, KW'nin
> sunduğundan **daha zayıf ve standart bir varsayımın** yerine geçebilecek kadar güçlü
> çıktı — Varsayım 6.4 çıktı-boyu Θ(n³/r) alt sınırı yüzünden otomatiktir ve **gerekli
> değildir**; gerçek güvenlik (a) ROM'da σ öngörülemezliği + (b) kanıtlanmış marjinal
> üniformluk (Lemma 6.5) + Merkle tek-yönlülüğüdür. Tüm yapısal saldırılar ve
> trapdoor-matrix literatürü çürütüldü. **Risk: yüksek → düşük-orta.** Kalan asıl risk
> fayda talebidir (E-gap), kriptografi değil. Yine de **2 bağımsız kriptograf incelemesi
> Faz 2'nin zorunlu kapısıdır** — yukarıdaki analiz bir LLM'in okumasıdır, kanıt değil.

## A.1 İki katman — GÜVENLİK ve FAYDA (2026-09-19 revizyon)

> **2026 negative results'inden sonra:** Basu (2606.04819) Pearl'in canlı 24 EH/s ağının **sıfır**
> faydalı hesap ürettiğini ölçtü; Demirel (2026/1492) leader-election'ın **talepten bağımsız**
> olması gerektiğini ispatladı (Thm 2); SoK (2025/1814) "utility güvenlik bütçesine katkı vermez"
> dedi. **Bu spec'in S1/S2 adlandırması G/U katmanlarına dönüştürüldü:** S1 artık "faydalı" değildir
> — o, **G katmanıdır (güvenlik)**; fayda **yalnızca U katmanında**, fee ile dışsallaşmış taleple
> vardır. **"Faydalı iş zinciri güvendir" diye bir şey yoktur.**

| | **G katmanı — GÜVENLİK (her madenci, her blok)** | **U katmanı — FAYDA (fee-ödemeli görev pazarı)** |
|---|---|---|
| **Kim belirler** | Madenci kendi MatMul girdisini seçer (serbest) | **İstemci** görevi + fee'yi zincire commit eder |
| **Sertifika** | KW/cuPOW-style MatMul sertifikası (1+o(1)) | Tam zkVM/STARK ispatı (Circle STARK + Jolt Atlas) |
| **Fayda iddiası** | **YOK** — prescribed hardness sağlanır, utility değil | **VAR** — talep escrow'daki gerçek fee ile dışsaldır (E ✓) |
| **Zorluk kaynağı** | KW prescribed hardness + `H(FS‖nonce) < target` | Devre büyüklüğü (yapısal alt sınır) |
| **Lider seçimde rolü** | **TABAN** (tek kaynak) | **Sadece sınırlı, fiyatsız boost** (Demirel Cor. 4) |
| **Sıfır-talepte** | Filler dense-random MatMul → canlılık korunur (Demirel Thm 2 ✓) | U kapalı; ağ pure-PoW olarak yaşamaya devam eder |

**Tasarımın özü:** KW **W'yi (work soundness)** çözer, **E'yi (demand exogeneity) çözmez** — Pearl'in
çöküşünün sebebi E'yi "ekonomik bir özellik" sanıp pazarlamasıydı. KÖK v2, E'yi **ancak U
katmanında** ve **sadece fee ödemesiyle** çözer; güvenliği asla U'ya bağlamaz.

## A.2 Veri yapıları (canlıya taşıma formatı)

```
Task (S2)      = { task_id: Hash, client: PubKey, commitment: MerkleRoot,
                   fee: Amount, bond: Amount, harness_id: Version, expire: Height,
                   max_overhead: FLOPs }

Assignment     = { task_id, miner: PubKey, epoch_seed: VRFOutput, height: Height,
                   vrf_proof: VRFPubKey-Proof }        // S2 için; S1'de YOK

Statement(ctx) = { selected_parent: BlockHash,        // GHOSTDAG sıralamasından
                   miner: PubKey, task_ref: Hash,
                   height: Height, proof_system_id: SchemaId,
                   nonce: u64 }

Solution       = { ctx, kw_certificate: Bytes,        // S1
                   || snark_proof: Bytes,             // S2
                   digest_target_check: H(certificate||nonce) < target }

Block          = { header: {parent_set, ctx_root, tx_root, task_root,
                           digest: H(fs_transcript), nonce, proof_system_id},
                  body: { txs, task_set, solutions[], agg_stark} }
```

## A.3 Zincir bağlama ve grinding direnci

- **ctx bağımlılığı:** `selected_parent` GHOSTDAG'in **seçili parent'ı** olduğundan ve her
  madencinin çözümü farklı bir zincir konumuna bağlı olduğundan, bir sertifika **başka bir blok
  için yeniden kullanılamaz** (precompute/replay imkânsız: zincir hash'i önceden bilinemez).
- **Nonce tazelik:** her nonce, FS transcript'ı değiştirir → her deneme **taze bir sertifika**
  ister (işin tekrarı = zorluğun kaynağı).
- **VRF ataması (sadece S2):** görev ataması `epoch_seed`'den VRF ile belirlenir; epoch seed'i
  zincir geçmişinden (N-64 blok öncesi) türetilir → madenci atamayı **etkileyemez** (grinding
  pahalı), görev sahibi ile madenci arası **collusion** ancak bond slash'ı ile.
- **External-utility saldırısı (arXiv 2505.21685):** dış teşvikli madenciler faydalı görevleri
  tek blokta toplama eğiliminde → **per-block useful-fee cap** `C_fee` ve **anti-aggregation
  kuralı**: bir bloktaki S2 görevlerinin toplam fee'si `C_fee`'i aşamaz; aşan kısım sonraki
  bloklara kayar (DAG ordering ile uyumlu).

## A.4 Bonding ve slashing matrix

| Suç | Kanıt | Ceza |
|---|---|---|
| Geçersiz sertifika | Herhangi bir doğrulayıcı reddeder (deterministik) | Geçerli blok zaten reddedilir; madenci blok ödülü alamaz (doğal ceza) |
| Geçersiz S2 çözümü | Fraud-proof penceresi (W_s = 100 blok) | `slash_task = bond_task` (task bond'u) + fee iadesi |
| Equivocation (aynı görev iki çözüm) | İki imzalı çözüm | `slash_eq = 2 × task_fee` |
| Veri kullanımezliği | Açılım talebi reddi | `slash_da = task_bond` |
| Collusion (görev sahibi = madenci, kolay görev) | **Yok** — KW prescribed hardness bu saldırıyı anlamsızlaştırır | — |
| Madenci havuzu gizli anlaşması (Pass §1.8 agregasyon riski) | Zincir-üstü göstergeler (tek adres payı > %20) | **Otomatik değil** — gözlem + topluluk sinyali (§C.5 alarmı) |

## A.5 Doğrulama teşvik güvenliği (Verifier's Dilemma)

**Sorun (arXiv 2404.09005):** doğrulama hesaplamadan ucuzsa rasyonel düğümler atlayabilir.
**KÖK çözümü:**
1. **Zorunlu doğrulama:** blok kabulü için her tam düğüm sertifikayı doğrüler — opsiyonel değil
   (deterministik; atlayan düğüm fork'ta kalır).
2. **Re-execution yok:** S1/S2 doğrulaması asimptotik olarak ucuz olduğundan "ücretlendirme
   maliyeti" ≈ 0 → dilemma oluşmaz. (HadAgent tarzı re-execution'dan kaçınma nedeni budur.)
3. **S2 için fraud-proof penceresi:** W_s blok boyunca itiraz; itiraz eden doğrulayıcı
   `reward_fraud` kazanır (yetersiz itiraz → kendi bond'u kesilir) — **verifier incentive-security**.
4. **Kontrollü difficulty:** madencinin dürüst çalışması için parametre tasarımı (SEDULity
   yöntemi, arXiv 2512.13666): rasyonel madenci = dürüst madinci, formal koşul §A.6.
5. **★ Sansür direnci (2026-09-20, V2 §10.1 F3a ölçütü):** testnet F3a'nın merkezî
   sıralayıcısı, **geçici bir test merkezîliğidir** (F3b'de GHOSTDAG ile değiştirilecek).
   O yüzden spec, sıralayıcı sansürüne karşı **iki mekanizma** tanımlar:
   (i) **İade-garantisi:** sıralayıcı görevi W_r blok içinde veya reddetme-adımı yayınlar;
   reddederse veya zaman aşımına uğrarsa escrow **otomatik iade** edilir (bond'suz, görev
   sahibine) — sansürün **maliyeti sıfırdır, faydası da sıfırdır**.
   (ii) **Görev-göçü:** görev sahibi, reddedilen görevi (aynı `task_ref` ile) **alternatif
   sıralayıcıya** yeniden gönderebilir; ilk sıralayıcının bond'u kesilir (sansür
   **negatif getiri** verir).
   **Üretimde (F3b sonrası):** merkezî sıralayıcı kalkar, sansür direnci GHOSTDAG'ın
   parent-set çeşitliliği + madenci rekabetiyle sağlanır — ama **iade-garantisi ve
   görev-göçü korunur** (bunlar zincir-üstü mekanizmalardır, konsensüsten bağımsız).

   **★ Çalışan prototip (2026-09-20):** `f3a_sequencer_proto.py` — TV-15..TV-20, hepsi
   PASS. İki mekanizmanın **prototip seviyesinde** doğrulandığını kanıtlar;
   **toy sınırları** (dosya başlığında listelendi): tek sıralayıcı nesnesi, W_r=3,
   sembolik fee/bond, dummy proof (kripto F3b'de), GHOSTDAG yok, sansür `evil` flag ile
   modellenir.

   **★★ KRİTİK: Ekonomi modeli prototipte bir BUG buldu ve spec'i değiştirdi.**
   `pass_sim.py` §10 (sansür-direnci ekonomisi) iki zorunlu policy sonucu çıkardı:

   1. **Bond geri-ekleme ZORUNLUDUR** (prototipe eklendi, TV-20 ile test edildi).
      İlk modellemem bond'u sabit varsayıyordu — **yanlıştı**: bond ilk sansür
      olayında **tükenir** ve sonraki olaylar **BEDAVA** olurdu, yani deterrent
      **tek-seferli** olurdu. `refill()` metodu eklendi: her sansür olayından sonra
      bond **fee seviyesine otomatik tamamlanır** (governance mekanizması).
      **TV-20 kanıtı:** 3 sansür olayında — refill varsa 3×100=300 kesinti;
      refill yoksa **100 kesinti (ilk olayda tükendi, 2 olay BEDAVA)**.
   2. **Dinamik bond: `bond = fee + margin`** — margin, oyun-dışı fayda tahmini
      (governance; F3a'da ölçülür). Tablo: oyun-dışı fayda 40 ise bond=50 yeterli
      (net +100); **120 ise bond=200 bile yetersiz** (net −200). **Sabit bond,
      margin ölçülmeden setlenemez.**
   3. **Alt-bond tuzası (TV-17'den):** `bond₀=50 < fee=100` ise refill bond'u
      **fee seviyesine yükseltir** (50→100). Yani düşük bond'la başlayan bir
      sıralayıcı ilk olayda fee seviyesine çekilir — bu, politik olarak **değil,
      mekanik olarak** gerçekleşir.

   **Önceki toy notu düzeltildi:** "bond kesintisinin ekonomik ağırlığı F4'te
   hesaplanmalıdır" yazmıştım — **hesaplandı** (pass_sim §10) ve yukarıdaki üç
   policy sonucunu verdi. **Bu, "kanıt iddiaları çalıştırılabilir koda çevir"
   kuralının değerini bir kez daha kanıtladı: ekonomi modeli prototipde bir
   gerçek açık buldu, spec onunla güncellendi.**

**★★ GUNCELLEME (2026-09-20): margin artik OLCULDU —
`bond_margin_proto.py`, TV-31..TV-33. Bir spec duzeltmesi, dürüstce kaydedildi:**

- **TV-31 — f3a kesintisi fee'de kapali.** f3a'nin gercek modunda
  `slash = min(bond, fee)`, bond'u fee'nin ustune cikarmak **etkisizdir**:
  bond 100/500/2000 (fee=100, B_out=60) hepsinde **ayni net -40**. Deterrent
  **fee** ile sinirlidir ve kritik fee = B_out. Yani yukaridaki 2. maddedeki
  "bond = fee + margin" politikasi ancak protokol tek olayda **fee'den fazla**
  kesim yapabiliyorsa gecerlidir. **Oneri:** A.5.5'e agir sansur icin FULL
  kesinti modu (`slash = bond`, refill ile) eklensin.
- **TV-32 — FULL modda margin tam lineer:** margin = B_out - fee
  (max hata 0.00, R^2=1.0000). §10 esit denklemi kapak kaldirilinca dogrulandi.
- **TV-33 — bedava-sansur penceresi:** refill yoksa yalnizca bond/fee olay
  engellenir (bond=300, fee=100 -> 3 olay), sonrasi bedavadir (20 olayda net
  +900). refill pencereyi kapatir (net -800).

## A.6 Formal özellikler (teorem iskeletleri)

- **T-A1 (Prescribed hardness ⇒ honest-Nash):** Eğer (P1) geçerliyse ve block reward > 0 ise,
  dürüst madencilik bir ε-Nash dengesidir: hileli stratejiler (kolay girdi seçme) **çalışmayı
  azaltamaz**, çünkü prescribed hardness girdiden bağımsızdır. (KW conjecture'a bağlı; §A.9.)
- **T-A2 (No-replay):** ctx'in selected_parent bileşeni sayesinde, N-1 derinliğindeki herhangi
  bir çözüm N'inci blok için geçersizdir (hash çakışması hariç, 2^-256).
- **T-A3 (Fee liveness):** `C_fee` ve anti-aggregation kuralları altında, DAG'de g/7'lik görev
  yoğunluğu hiçbir bloğu tepe ücretlerle tıkamaz; ispat: per-block cap ≤ C_fee ve görevler
  sıralı işlenir.
- **T-A4 (Verifier incentive-security):** W_s penceresi ve fraud reward altında, dürüst
   itiraz baskındır (arXiv 2404.09005'in şemasına indirgeme).

## A.7 Veri kullanılabilirliği

- S1'de matrisler **madencinindir** — ağa sadece **sertifika** (polylog boyut) gider; matrislerin
  DA'sı madencinin sorumluluğudur (kendi AI iş akışında zaten mevcuttur).
- S2'de görev **commitment** olarak verilir (Merkle root), çözümde **sublinear açılım**; büyük
  modeller için erasure-coded DAS + yük dağıtımı (validator set boyutuyla orantılı).

## A.8 Yaşam döngüsü (S2 için)

```
submit → bond → (epoch seed commit) → VRF ataması → proof (S2) / cert (S1)
   → block inclusion → W_s blok fraud penceresi → settle (fee + reward)
   → hile kanıtı: slash + itirazcıya reward
```

## A.9 Fallback ve kriptografik dayanıklılık

> **2026-09-19 güncelleme (bağımsız analiz sonrası — bkz. `KW_ANALIZ.md`):** KW'nin
> güvenlik argümanı, sunulandan **daha sağlam** çıktı. Varsayım 6.4 (çıktı-boyu Θ(n³/r) alt
> sınırından dolayı neredeyle otomatik) **gerekli değildir**: gerçek güvenlik (a) ROM'da
> σ'nın öngörülemezliği + (b) Lemma 6.5'in **marjinal üniformluk** kanıtı + Merkle
> tek-yönlülüğü üzerine kuruludur — hepsi standart. Ayrıca tüm yapısal saldırılar
> (sparse/permutation girdi, A=B=0, precompute, korelasyon kısayolu) çürütüldü ve
> **trapdoor-matrix** literatürü (VZ25 arXiv 2502.13065, BN25 arXiv 2502.13060) tehdit
> oluşturmuyor (E,F σ'dan türetilir; saldırgan trapdoor yerleştiremez). **Risk
> "yüksek" → "düşük-orta" olarak revize edildi.** Kalan asıl risk **fayda talebidir (E-gap)**,
> kriptografi değil. Yine de fallback korunur: olasılık #1 senaryosu olmaktan çıktı,
> ama sıfırdan değil.

- **Conjecture çöküşü:** KW sertliğinin kırılması durumunda, zincir-üstü sinyal ile **yedek iş
  fonksiyonu** (protocol-generated dense random MatMul + hash binding = pure-PoW modu) devreye
  girer. Bu, §7 migration katman A'sının tam kullanımıdır: **iş değişir, zincir yaşamaya devam
  eder, ama dürüstçe "hard fork" denir** (v1'in aksine).
- **Açık sınır:** S1'in faydası, madencilerin **gerçekten AI workload'una sahip olmasına**
  bağlıdır. Aksi halde kw sertifikaları anlamsız (ama yine de güvenli) iş üretir → Pass'ın
  **Bitconia** düşüşü (§C.4 senaryo 5).
  → **2026-09-19 düzeltme:** bu açık sınır geçerli değildir; S1'in faydası **iddia edilmez**
  (Pearl'in ölçülen sıfır-fayda sonucu). S1 = G katmanı = güvenlik. Açık sınır §A.1'deki G/U
  ayrımıyla değiştirildi.

## A.9b Aritmetik determinizm — FP doğrulamanın iki yolu (2026-09-20, Pearl birincil kaynaktan)

KÖK v2 G katmanı bugün **tam sayı (INT) KW kerneli** kullanır (q=97 toy field; üretim için
büyük mod + transcript hashleme). Ama U katmanı gerçek AI workload'ları (BF16/FP8/FP4) istiyorsa,
**kayan nokta çarpımının verifikasyonu** kaçınılmazdır. Pearl'in yeni FP whitepaper'ı (Eylül
2026) bu sorunu çözdü ve **iki somut yol** ortaya çıktı:

| | **Yol A: Bit-exact replay (Pearl/Hawkeye)** | **Yol B: Native-FP zkVM (Peigné vd.)** |
|---|---|---|
| Kaynak | Hawkeye arXiv 2603.20421v2 (**MLSys 2026**) | arXiv 2606.05433v2 (44 sf) |
| Fikir | GPU Tensor Core işlemini CPU'da **birebir, kayıpsız** re-produce et (rounding direction, subnormal handling, accumulation order pinned); verifier seçili tile'ı yeniden hesaplar | zkVM'e **native BF16/FP32 precompile**; FP aritmetiği devrenin içinde |
| Kanıt durumu | **üretimde** (Pearl mainnet, sm90 whitelist); Hawkeye = Badash, Boneh, **Komargodski**, Srivastava | ~**36 ay** PoC horizonu; 13 açık problem |
| Determinizm kaynağı | whitelist GPU + pinned accumulation order (Tensor Core microarchitecture) | devre tanımı |
| Maliyet | verifier = bir tile'ın yeniden hesabı (O(mnk/r²)) | zkVM proof üretimi (yüksek, ama Peigné: tek haneli % overhead iddia) |
| Gizlilik | yok (plaintext verifier; Pearl bunu Plonky2 ZK appendix'le ayrı kapatır) | var (native) |
| Donanım kilidi | **var** — sm90 (H100/H200) whitelist; yeni GPU = yeni Hawkeye tablosu | yok (devre taşınabilir) |
| KÖK v2'de rolü | **Faz 2 G katmanı için önerilen yol** (bugün çalışıyor, kanıtlanmış) | **Faz 3+** (crypto-agility düzlemiyle paralel; §7 katman C) |

**Karar:** KÖK v2 G katmanı **Yol A'yı benimser** (Hawkeye-style bit-exact replay + GPU
whitelist), çünkü (i) bugün üretimde kanıtlanmış, (ii) Komargodski aynı zamanda KW'nin yazarı
— iki çizgi kasıtlı birleşmiş, (iii) Pearl'in jackpot policy'si (TV-11..TV-14) Yol A'nın
üzerine inşa edilmiş. **Yol B, §7 crypto-agility düzleminde "geleceğin yolu" olarak tutulur**
(whitelist kilidini aşar; native gizlilik getirir). **Honest risk:** Yol A, KÖK v2'yi belirli
GPU nesillerine bağlar — bu, §11'deki ASIC-merkeziyet endişesini **yönetilebilir ama gerçek**
kılar; whitelist genişletme bir governance süreci gerektirir. **Bu süreç ARTIK TANIMLANDI**
(daha önce Faz 2'ye ertelenmişti, tasarımsız bırakılamaz): EN spec §A.11'deki 5 adımlık süreç
— (1) öneri + bit-exactness dosyası, (2) 2-epoch doğrulama penceresi, (3) sıfır false-accept
toleransı, (4) §A.9 versioned-schema yoluyla aktivasyon, (5) simetrik çıkarma. **Açık kalan:**
doğrulama, raporlayan donanım popülasyonu kadar dürüst; az operatörlü bir GPU modeli az taraf
tarafından doğrulanır. Yol B (zkVM) bu yüzden uzun vadeli cevaptır.

**Pearl FP şemasının KW'den yapısal farklılığı (KÖK'ü etkiler):** Pearl'de entrywise quantization
nonlineerdir — `Q(A+N) ≠ Q(A)+Q(N)` — düşük-rank kısayolunu bozar; **böylece ticket'lar doğrudan
çıktı tile'larını hashler, (n/r)³ transcript gerekmez.** KÖK v2'nin INT kerneli transcript'e
bağlı kalmaya devam etmeli (INT'de düşük-rank kısayolu açıktır, kw Assumption 6.4'ün konusu
budur); FP'ye geçiş (Faz 3) ancak Yol A/B ile transcript'siz tasarıma izin verir.

## A.10 Tam protokol pseudocode'u (U katmanı görev yaşam döngüsü)

> **2026-09-19: bu bölümün referans implementasyonu çalışıyor** — `u_layer_prototype.py`
> (standart kütüphane, deterministik SEED). TV-5..TV-10 + G replay reddi **hepsi PASS**;
> TV-9, Basu'nun canlı Pearl kurtosis ölçümlerini (1,79 / 3,33 / 2,97) prototip seviyesinde
> birebir yeniden üretti (1,81 / 3,58 / 3,04) ve adversarial girdinin naive kontrolden
> **geçtiğini** kanıtladı. Aşağıdaki pseudocode ile prototip aynı arayüzü paylaşır; G
> kernel'i ve VRF prototip stub'ı gerçeğiyle değiştirilecek nokta kodda işaretlenmiştir.

### A.10.1 Durum makineleri

```
Task:      DRAFT → COMMITTED → ASSIGNED → SOLVED → CHALLENGED? → SETTLED
                ↘ CANCELLED      ↘ EXPIRED     ↘ SLASHED
Miner:     IDLE → ASSIGNED → PROVING → SUBMITTED → PAID  (or SLASHED)
Verifier:  LISTENING → CHALLENGING → FRAUD_PROVEN | REJECTED
```

### A.10.2 Görev gönderimi (client)

```python
def submit_task(client, task_spec, fee, burn_rate, gas):
    # task_spec: {harness_id, program_commit: MerkleRoot, max_flops,
    #             public_inputs_commit, deadline: Height}
    assert fee > 0 and burn_rate in (0.0, 0.5]      # burn = Demirel'in geri-alamaz vergisi
    bond = fee * BOND_RATIO                          # sybil pahalı (Lemma 1'ye karşı)
    burn = fee * burn_rate                           # escrow'dan geri-alamaz: güvenlik kaynağı
    escrow = lock(client, fee + bond, until=deadline + W_s)
    burn_immediately(burn)                           # Protokol'ün burn adresi (spend cannot)
    tid = H("task" ‖ client ‖ task_spec ‖ fee ‖ escrow)
    emit(TaskCommitted{tid, task_spec, fee, escrow_id, expire=deadline})
    return tid
```

### A.10.3 VRF ataması (epoch seed'den — grinding'e karşı)

```python
EPOCH_LOOKBACK = 64      # seed, N-64 bloğundan: madenci bugün etkileyemez

def epoch_seed(height):
    blk = chain[height - EPOCH_LOOKBACK]
    return H("seed" ‖ blk.hash)

def assign_tasks(height, tasks):
    seed = epoch_seed(height)
    for t in tasks:                                  # her görev için bağımsız atama
        vrf_out, vrf_proof = vrf.prove(miner_vrf_key, seed ‖ t.tid)
        w = as_int(vrf_out) / 2**256                  # [0,1)
        if w < t.assignment_probability(height):      # stake/compute-ağırlıklı kapı
            assigned[miner].append((t, vrf_out, vrf_proof))
    # Madenci kendi atadığı görevi SEÇEMEZ; sadece atananı kabul eder veya FORFEIT (bond kesintisi)
```

### A.10.4 Madenci: ispat üretimi + blok çözümü

```python
def mine_block(miner, assigned_tasks, ctx):
    # G katmanı (her blok, talepten bağımsız):
    A, B = miner.choose_matrices()                    # serbest; prescribed hardness ne olursa olsun
    while True:
        nonce = rng()
        cert = kw.prove(A, B, ctx ‖ nonce)            # 1+o(1) overhead, ctx-bound (T-A2)
        digest = fs_transcript(cert).digest()
        if int(H(digest ‖ nonce), 16) < target:
            break                                     # blok kazıldı

    # U katmanı (aynı bloğun içinde, opsiyonel, boost ama ZORUNLU DEĞİL):
    proofs = []
    for t in assigned_tasks:
        harness = load_harness(t.spec.harness_id)
        witness = harness.trace(t.program, t.inputs)  # deterministic kernel + pinned order
        proofs.append(stark.prove(harness.air, witness, ctx ‖ t.tid))
    return Block{header, kw_cert=cert, u_proofs=proofs, nonce}
```

### A.10.5 Doğrulama (düğüm)

```python
def validate_block(blk):
    ctx = ctx_of(blk)                                 # selected_parent‖miner‖...‖proof_system_id
    if not kw.verify(blk.kw_cert, ctx ‖ blk.nonce):   return REJECT     # G katmanı
    if int(H(fs_digest(blk.kw_cert) ‖ blk.nonce),16) >= target: return REJECT
    fee_total = 0
    for (t, proof) in zip(blk.tasks, blk.u_proofs):
        if not vrf.verify(t.assignee, epoch_seed ‖ t.tid, proof.vrf):  return REJECT
        if not stark.verify(proof, t.program_commit):  return REJECT     # Lean-doğrulanmış AIR
        fee_total += t.fee
    if fee_total > C_FEE:                              return REJECT     # anti-aggregation (T-A3)
    return ACCEPT
```

### A.10.6 Fraud penceresi ve slash (Verifier's Dilemma çözümü)

```python
def challenge(challenger, tid, proof):
    assert height <= proof.height + W_s               # W_s = 100 blok
    ok = recheck_with_independent_backend(proof)      # farklı proving backend
    if not ok:
        slash(proof.miner, proof.miner.bond)
        reward(challenger, FRAUD_REWARD)              # itirazı kazanır
    else:
        slash(challenger, challenger.bond)            # kötü niyetli itiraz
    settle(tid, winner)
```

### A.10.7 Test vector'leri (deterministik, testnet için)

| # | Senaryo | Girdi | Beklenen | Ölçüt |
|---|---|---|---|---|
| TV-1 | Replay reddi | Aynı `kw_cert` iki farklı `selected_parent`'te | **REJECT** ikincisi | T-A2 |
| TV-2 | Prescribed hardness | Sparse A (hepsi sıfır satır) + random B | Sertifika maliyeti = dense girdi ile ±%2 | KW W |
| TV-3 | Easy-instance başarısız | Permutation matrix A | Geçerli sertifika ama `H(digest‖nonce)` maliyeti değişmez | KW W |
| TV-4 | Rastgele-matris faydası | U görevi olmaksızın mining | Blok geçerli; **φ=0** olarak işaretlenir | E-gap kabulü |
| TV-5 | Fee escrow + burn | Görev submit, fee 100, burn_rate 0.3 | 30 burn edilir, 70 escrow'da; sybil maliyeti > 0 | Demirel Lemma 1 |
| TV-6 | Anti-aggregation | Tek blokta `Σfee > C_FEE` | **REJECT**, görevler sonraki bloklara kayar | T-A3, 2505.21685 |
| TV-7 | Fraud slash | Hatalı ispat + kanıt | Madenci bond'u kesilir, itirazcı ödül alır | §A.10.6 |
| TV-8 | Sıfır-talep canlılığı | 1000 blok boyunca hiç U görevi | **Tüm bloklar geçerli**, zincir yaşamaya devam eder | Demirel Thm 2 |
| TV-9 | Kurtosis tuzağı | Uniform-random matrisler + kurtosis kontrolü | **Kontrol geçersiz**: adversary N(0,18) geçer (Basu) | E-gap: dağıtım ≠ provenance |
| — | *prototip ölçümü* | TV-9'u `u_layer_prototype.py` ile çalıştır | uniform **1,81** / nn **3,58** / adversarial **3,04**; adversarial [2,4]'ten **GEÇER** | Basu canlı: 1,79 / 3,33 / 2,97 |
| TV-10 | PQ downgrade | Eski non-PQ schema ile imzalı blok | **REJECT**; only `proof_system_id ∈ PQ_set` | §5 crypto-agility |
| TV-11 | **Entry liveness** (Pearl 5.1.1) | Peak'lerin gürültüden τ_idle=8 kat büyük olduğu satırlar | idle oranı > ε_idle=1/64 → **RED**; sağlıklı ≈0 | No-noise-entries saldırısı |
| TV-12 | **Noise floor** (Pearl 5.1.2) | Tek-peaked satır (per-tensor scale peak'e ayarlanır) | noise < σ_min=1 grid unit → **RED** | Low-local-entropy → özel donanım |
| TV-13 | **Tamed products** (Pearl 5.1.3) | Aynı satırlar (rank-1 tile) | tamed oranı > ε_tame → **RED**; tipik iş yükü geçer | Coherent dot products |
| TV-14 | **Unpredictable summands** (Pearl 5.1.4) | Common-peak A,B (her hücre tek summand) | predictable oranı > ε_pred → **RED** | FP precision shortcut |
| TV-15 | **İade-garantisi** (§A.5.5-i, F3a) | Kötü sıralayıcı reddetme-adımı **yayınlamaz**; W_r blok geçer | CENSORED → otomatik **REFUNDED** (escrow=70, iade) | Sansürün faydası = 0 |
| TV-16 | **Görev-göçü** (§A.5.5-ii, F3a) | Reddedilen görev alternatif sıralayıcıya gider | bond 100 → 0 (**min(bond, fee)** kesinti) + B'de settle | Sansür **negatif getiri** |
| TV-17 | **Sansür-ucretsizlik** (F3a) | 5 görevin tümü sansürlenir; 2'si göç, 3'ü zaman aşımı | held escrow **0**; iade 210; bond 50 → 0 | Sıralayıcı escrow'u **asla** elinde tutamaz |
| TV-18 | **Dilemmasız doğrulama** (§A.5.2, F3a) | Hatalı verify → CHALLENGED; sonra doğru verify | dilemma tetiklemesi 1 (izlenir), SETTLED + burn 30 | Doğrulama zorunlu, atlanamaz |
| TV-19 | **Honest yaşam döngüsü** (F3a) | submit → assign → solve → settle | burn=30, iade=0, slash=0 | Temel akış |
| TV-20 | **Bond geri-ekleme** (§A.5.5, pass_sim §10'dan bulunup prototipe eklenen açık) | 3 sansür olayı; refill VAR vs YOK | refill: **3×100=300** kesinti; refill-YOK: **100 kesinti, 2 olay BEDAVA** (bond ilk olayda tükendi) | Deterrent tek-seferlik **olmamalıdır** |
| TV-21 | **Low-entropy dayanıklılık** (Polymath 6; TV-12'nin sınırı) | Peaked saldırı, v = 10→400 tarama | **0/10 v geçer** — noise/g asimptotu ~0,707 < 1; toy'da **her zaman RED** | ★ FP8'de kanıt **değildir** — ters yön (aşağıda) |
| TV-22 | **GHOSTDAG mavi kuralı** (ePrint 2018/104; Kaspa mainnet k=18) | 60-90 bloklu DAG, %25-50 fork; mavi işaretli her blokun mergeset-anticone'u | **hepsi ≤ k=18** (77 mavi) | Mavi seçim kuralı doğru uygulanır |
| TV-23 | **selected_parent = max blue_score** | 74 blok; her bloğun selected_parent'ı parent'larıyla karşılaştırılır | **hepsinde** selected = en yüksek blue_score (ties: en düşük hash) | Seçim kuralı deterministik ve doğru |
| TV-24 | **Mergeset sınırı** (2k = 36) | 80 blok, %40 fork; mergeset boyutları | **max = 36**, sınırın altında | Üretim limiti sağlanır |
| TV-25 | **ctx parent-set içerir** (T-A2 güçlendirmesi) | Aynı (miner, task, height) blok, farklı parent-set | **farklı ctx** → ikincisi REJECT | Replay koruması parent-set boyutunda kapanır |
| TV-26 | **Bölücü saldırı (liveness)** | 3 madenci, %50 fork = DAG parçalama girişimi; 137 blok | güncel blok ortalama düzeni = **64** (DAG'ın %47'si); hiçbir bloğun düzeni boş değil | Saldırı altında toplam düzen korunur |

**TV-21 (low-entropy, Polymath 6) — dürüst sınır:** saldırgan peak v'yi 10→400
taramış; **hiçbir v geçememiş** (noise/g asimptotik ~0,707 < SIGMA_MIN=1). Bu
"güzel" sonucun **altında bir toy-model yanılgısı** yatar: toy'da gürültü
`DELTA·RMS(row)`'dur, peak artınca RMS de aynı hızda büyür → oran sabit kalır.
**Pearl'in FP8 gerçeğinde (wp §5.1.2) peak per-tensor scale-up zorlar ve gürültüyü
sıfıra doğru sıkıştırır** (reduced-alphabet donanım avantaji). Yani FP8'de saldırının
yönü toy'unkinin **tersidir**: toy her zaman RED verirken FP8'de KABUL riski vardır.
**Sonuç:** TV-12'nin toy sonucu INT/fixed-point için geçerlidir; FP8 için noise
modelinin **quantization-aware** (per-tensor scale + subnormal sıkışma) yeniden
yazılması gerekir — bu, Faz 3'te Yol A (Hawkeye) bağlamında yapılmalı. (TV-14'de
`ACC_NOISE` enjekte etmemizin sebebi tam olarak buydu.)

**TV-11..TV-14 kaynakçası:** Pearl "Floating Point Scheme Specification" (Eylül 2026) §5.1'in toy INT
adaptasyonu — `g_layer_tests.py` içinde `JackpotToy` sınıfı; K=64, GRID=16, DELTA=0.5, ACC_BITS=8.
Ölçülen sonuçlar (2026-09-20, hepsi PASS):

| Test | DEGENERATE girdi (RED) | Sağlıklı girdi (KABUL) |
|---|---|---|
| TV-11 | 2-peak rows: idle **%3,12** > %1,56 | uniform: **%0,00** |
| TV-12 | tek-peak: noise **0,52** grid unit < 1 | uniform: **2,05** grid unit |
| TV-13 | rank-1 tile: tamed **%100,0** > %12,5 | random: **%0,5**; B=A: %1,7 (loose net) |
| TV-14 | common-peak: predictable **%98,4** > %25 | random: **%0,7** |

**TV-11..TV-14'ün TV-9'a göre üstünlüğü:** TV-9 (kurtosis) Pearlin canlı ağında **adversary
tarafından geçildi** (N(0,18) → 2,97, [2,4] eşiğinden). Pearl'in üretimdeki dört kontrolü ise
**yapısal** özelliklere bakar (gürültü-cantanın boyutu, grid'de yer kalması, uyum, truncation) —
dağılım parametrelerine değil. **KÖK v2 G katmanı bu dört kontrolü alır; kurtosis kontrolü
sadece uyarı (TV-9) olarak kalır.**

**Toy adaptasyonun bilinen sınırları (dürüst):** (1) gürültü iid, rank-r değil — 5.1'in 1/2/4.
kontrolleri per-entry/per-row istatistikleri olduğu için yapı korunur, ama Pearl'in üretimdeki
rank-r analizinin tam karşılığı değildir; (2) tamed/unpredictable eşikleri toy ölçeğe (K=64)
kalibre edildi, Pearl'in üretim değerleri (τ_tame=256) k~4096-16384 içindir; (3) toy'un 16-seviye
lineer grid'i FP8'nin non-uniform grid'i + FP32 accumulator'unun ölçek ayrimını ifade edemez —
bu yüzden TV-14 accumulation-side gürültüsü sub-quantization ölçeğinde (ACC_NOISE=1/16 grid unit)
enjekte edilir (Pearl'de bu ölçek FP8 subnormal sıkışmasından gelir); (4) σ_i'nin per-entry mi
row-level mi olduğu Pearl metninden net çıkmadı, toy per-entry (RMS tabanlı) seçti. **Bu
sınırlar dört kontrolün ayırt ediciliğini kanıtlar; üretim kalibrasyonunu değil.**

**TV-9 özellikle kritik:** Pearl'in ölçülen başarısızlığının (uniform matrisler kurtosis 1.79 ile
NN ağırlıklarından 3.33 ile ayırt edilebiliyor ama adversarial Gaussian 2.97 ile kontrol geçiyor)
**kontrol olarak değil, uyarı olarak** test edilmesini sağlar. **Ders: dağıtım-kontrolü fayda
kanıtı değildir; sadece fee-ödemeli görev fayda kanıtıdır.**

---

# EK B — DIFFICULTY VE BLOK ÜRETİM MATEMATİĞİ

## B.1 Model

Her **deneme** `a`: bir MatMul örneği için KW sertifikası üretimi (maliyet `h(n)` FLOP).
Deneme **başarılı** iff

```
H( cert_digest ‖ nonce ) < target,   target = 2^256 / D        (D = difficulty)
```

`cert_digest`, FS transcript'ının digest'i (nonce ile birlikte). Random oracle altında
her deneme başarı olasılığı `p = 1/D`.

## B.2 Blok geliş süreci

- Madenci `i` deneme hızı `ρ_i = c_i / h(n)` (c_i = FLOP/s kapasitesi). Toplam `Λ = Σ ρ_i`.
- Başarı süreci: **Poisson**, hız `λ = Λ/D`. Blok aralıkları `Exp(λ)`, ortalama `E[T] = D/Λ`.
- **Sonuç:** inter-arrival üssel ve memoryless → **Bitcoin'in tüm difficulty/çıkarma matematiği
  birebir geçerlidir** (varyans, ARA etkileri, selfish-ming direnci analizleri transfer olur).
- GHOSTDAG: blok hedefi `T_b = 1/λ_b` (ör. 100 ms = 10 BPS); her blok kendi ctx'i ve
  parent set'i ile gelir; sırada GHOSTDAG kuralı.

**★ Çalışan prototip (2026-09-20):** `ghostdag_proto.py` — TV-22..TV-26, hepsi
PASS. GHOSTDAG greedy mergeset + selected_parent + blue_score çekirdeğini
Kaspa mainnet'in **gerçek üretim parametreleriyle** doğrular: `k=18`
(BPS=1), `max_block_parents=10` (floor 10/cap 16), `mergeset limit=2k=36`
(rusty-kaspa `config/bps.rs`'ten). KÖK v2 eklentisi: **ctx artık parent-set
hash'ini içerir** (TV-25), bu T-A2 replay korumasını parent-set boyutuna
kadar güçlendirir.

**Toy sınırları** (dosya başlığında listelendi): **PoW/geçerlilik kontrolü
YOKTUR** — tüm bloklar geçerli PoW'a sahip varsayılır. GHOSTDAG'ın güvenlik
argümanı (k'ye göre anticone olasılık bound'u) PoW'e dayandığından, burada
yalnızca **DAG mantığını** doğrularız. Ağ gecikmesi uniform modeli;
`_future()` O(n²) (üretimde incremental takip edilir); k=18 Kaspa BPS=1
şablonudur, KÖK v2'nin BPS'i henüz belirlenmedi.

## B.3 Retarget algoritması (formal)

`W` blok penceresinde gerçekleşen süre `T_act`; hedef blok süresi `T_b`:

```
Lambda_hat = D · W / T_act                       // D'den bagimsiz hashrate tahmini
Lambda_smooth = median( son <=3 pencerenin Lambda_hat )   // medyan filtre
D <- clip( Lambda_smooth · T_b ,  D/4,  4·D )    // Bitcoin'in 4x sinirlari
```

> **2026-09-19 düzeltme (önemli):** önceki sürümde oran `T_act/(W·T_b)` olarak
> yazılmıştı — **ters çevrilmişti** (D difficulty'dir, §B.2/§B.4: `p = 1/D`,
> `E[T] = D/Λ`; Bitcoin'in "target" değerinin tersi; bloklar yavaşsa D azalmalı).
> Ayrıca basit oran formülü + medyan filtre kombinasyonu **stale-ratio yanlılığı**
> üretirdi (her pencerenin oranı eski D'ye aitti). Doğru formül her pencereden
> **bağımsız hashrate tahmini** çıkarır: `Λ̂ = D·W/T_act` (çünkü blok hızı
> `Λ/D`'dir, yani `T_act/W = D/Λ`). Bu tahmin D'den bağımsızdır, bu yüzden
> pencereler arası medyan alınabilir. Prototip `u_layer_prototype.py` +
> `g_layer_tests.py` (RT-1..RT-3) bunu doğrular: dengeden 10x uzaktan 2 pencerede
> `Λ·T_b`'ye yakınsar; 10x ani hashrate atlamasında pencere başına değişim ≤4x.

- Pencere `W = 2016` (Bitcoin) yerine DAG için **W = 1000 blok** (~100 sn @10 BPS) → daha hızlı
  adaptasyon; ama gürültü için **sınır 4×** korunur (aşırı osilasyonu engeller).
- Ek koruma: **medyan filtre** (son 3 pencerenin `Λ̂` medyanı) — ani hash dalgalanmalarında
  retarget'in tek bir pencereye kilitlenmesini engeller. Yan etki: gerçek bir hashrate
  atlamasına yanıt 2 pencere gecikmeli olur (güvenlik özelliği, hata değil).

## B.4 Zorluk birimi ve madenci tahmin edilebilirliği

- Difficulty `D`, **"expected proof-FLOPs"** cinsinden: `D = E[FLOP] / h(n)`? Hayır —
  doğrudan: beklenen deneme sayısı `E[k] = D`; beklenen iş `W_b = D·h(n)` FLOP/blok.
- Madenci payı: `ρ_i/Λ` (proporsiyonel, Bitcoin gibi).
- **Worked example:** `T_b = 100 ms`, `h(n) = 2·10^12 FLOP` (ör. 1K×1K MatMul ~2 TFLOP),
  ağ `C = 10^17 FLOP/s` (≈ 100× H100): `Λ = C/h = 5·10^4 deneme/s`; `D = Λ·T_b = 5000`;
  `p = 2·10^-4`. Blok başına beklenen iş `W_b = D·h = 10^16 FLOP` = 100 H100-saniye. ✓
- **Tutarlılık:** `W_b = C·T_b` — yani ağ her blokta `T_b` sürede toplam kapasitesini harcar
  (evrenin doğası; enerji = `C·T_b·e'`).

## B.5 İş-arz coupling (canlılık denklemi)

- **S1 yoğunluğu** `φ ∈ [0,1]`: ağ denemelerinin gerçek AI workload'una denk kısmı.
- `φ = 1` (her deneme gerçek iş): tam 2-for-1; `φ = 0`: pure-PoW filler (protocol-generated
  dense random MatMul). Canlılık **her zaman** korunur (filler sınırsız); **fayda** `φ`'ya bağlı.
- **Görev açığı denklemini:** `λ_tasks ≥ λ_b·(1−φ)` — S2 görev talebi blok hızını
  aşamazsa filler devreye girer. Bu, §C.4 senaryo 5'in teknik koşuludur.

## B.6 Sınırlar ve sonsuzluk koşulları

- **Block time floor:** `T_b ≥ t_cert + t_prop + t_verify`; KW sertifikası üretim süresi
  deneme başına `h(n)/c_i` → `T_b` çok küçükse tek deneme bile tamamlanamaz (pratik alt sınır
  ~50–100 ms).
- **Sertifikaların boyutu:** polylog; DAG'de 10 BPS'te toplam proof bandwidth hesaplanmalı
  (ZK-ACE'nin per-block STARK agregasyonu: ~160 B/tx).
- **Sesten korunma:** ses 2^-128 → doğrulama eşiği `λ ≥ 128`; KW/STARK parametreleri buna göre.

---

# EK C — PASS MODELİNE DAYALI ZİNCİR-ÜSTÜ EKONOMİK SİMÜLASYON SPEC'İ

## C.1 Modelin implementasyonu (Pass 2606.06700)

**Durum değişkenleri (her epoch `t`):** aktivite `M_t, L_t, D_t`; fiyatlar `p_t, P_t`;
token emit `R_t`; compute-op maliyeti `e` (sabit); duplex overhead `α, γ`.

**Denklem seti:**
```
S = M + D/γ                                    (güvenlik)
Q = L + D/α                                    (inference arzı)
π_M = P·R/S − e ≤ 0,     π_M = 0 iff M > 0
π_L = p − e ≤ 0,         π_L = 0 iff L > 0
π_D = P·R/(γS) + p/α − e ≤ 0,  π_D = 0 iff D > 0
Q = 𝒟(p)                                      (market clearing)
θ = P·R / (p·Q)                                (T/I oranı, sabit varsayım)
```

**Talep:** isoelastic `𝒟(p) = K·p^(−ε)`, `ε > 1` (varsayılan `ε = 2`).

**Numerik çözücü:** mixed-complementarity problem (MCP) — her (Δ, θ) grid noktası için
aktivite deseni `{M,L,D}` kombinasyonları üzerinde zero-profit koşulları çözülür;
Theorem 1'in rejim sınıflandırmasıyla doğrulanır:
`Δ = 1/γ + 1/α − 1`; `θ_low = α−1`; `θ_high = 1/(γ−1)`.

## C.2 Parametre tablosu (varsayılan değerler)

| Sembol | Anlam | Varsayılan | Kaynak/gerekçe |
|---|---|---|---|
| `e` | compute-op maliyeti | $1 | Pass (all-in GPU-blocktime) |
| `α, γ` | duplex overhead | 1.3 | Pass'ın KW instantiation'u (≈%23 fire) |
| `R_0` | ilk blok ödülü | 50 KOK | fair launch |
| `ρ_em` | emisyon azalış oranı | 0.5/4y (tail'e iniş) | §C.6 |
| `R_∞` | **tail emission** (asla 0 olmaz) | 2 KOK | güvenlik bütçesi tabanı |
| `τ` | hazine payı | %5 | fair launch ile uyumlu |
| `ε` | talep elastikiyeti | 2 | Jevons varsayımı |
| `θ` | T/I oranı (senaryo ekseni) | 0.1 → 10 | parasal primitiflerden gelir |
| `ν, λ, V` | stok-akış + velocity | 1, 0.1, 10/epoch | `θ = λθ_raw/(νV)` |
| `C` | ağ FLOP/s | 10^16 → 10^18 | simülasyonun teknik girdisi |

## C.3 Simülasyon senaryoları (her biri ≥1000 epoch)

1. **Lansman (θ düşük, θ<θ_low):** hedef rejim **Fortessia** (güvenlik ↑, fayda sabit).
   Kabul: `S > S^Bitconia` ve `p = e`.
2. **Benimseme büyümesi (θ artar):** Fortessia → Duplexia geçişi; `p = αe/(1+θ) < e`.
   Kabul: fiyat düşüşü teorik eğriyle ±%5.
3. **Teknoloji iyileşmesi (α,γ → 1.05):** Δ ↑; sosyal değer `ΔSV` nasıl değişir?
   (Theorem 3: deadweight loss ve duplex overhead azalır.)
4. **Talep şoku (K düşer 10×):** inference pazarı küçülür; θ etkili olarak ↑.
5. **Sıfır faydalı talep (φ→0):** **Bitconia düşüşü.** Kabul: ağ pure-PoW modunda
   canlı kalır (filler görevler), güvenlik bütçesi `R_∞·P` tabanında kalır.
6. **Saldırı maliyeti zaman içinde:** `cost_attack(t) = P·R/2` (Pass: tüm rejimlerde).
   Kabul: hiçbir epoch'ta Bitcoin-eşdeğerinin altına düşmez (Pass Corollary).
7. **Havuzlaşma/agregasyon riski (Pass §1.8):** tek adresin blok payı > %20 → **alarm**.
8. **Stok etkisi:** GPU değer kaybı oranı `1 − ρ^ε/α` (ρ=p/e) — saldırı sonrası caydırıcılık.

## C.4 Zincir-üstü gösterge tablosu (her epoch yayınlanır)

`S, W (israf = M + D(1−1/α)), S−W = DΔ, p, P, R, θ, Δ, φ` (S1 yoğunluğu),
`cost_attack = P·R/2`, `ΔSV` (Theorem 3/Prop 1), rejim etiketi
(Bitconia/Fortessia/Duplexia).

**Alarm eşikleri:** `cost_attack < $X_min`; `θ > θ_high` (aşırı sübvansiyon);
`φ < 0.2` (faydasızlaşma); tek-adres pay > %20.

## C.5 Para politikası (emisyon eğrisi, kesin formül)

```
R(t) = max( R_∞, R_0 · 2^(−⌊t/T_half⌋) )         T_half = 4 yıl
hazineden: h(t) = τ · R(t), τ = 0.05              (escrow + milestone vesting)
toplam arz: ∫R dt = sonlu üst sınır + sonsuz tail   (tail: R_∞ sonsuz, azalan toplam)
```

**Tasarım kuralı (dürüst):** Kaspa eğrisinin 2026'da tükenmesi (max arzun %96.5'i çıkmış)
ağın güvenlik bütçesini sıfırlar; `R_∞` bunu engeller. **Eğri bir kez yayınlanır ve
değiştirilemez** (değişiklik = en büyük güven ihlali).

## C.6 Simülasyon kabul ölçütleri (Faz 4 kapısı)

1. Tüm (Δ, θ) gridinde çözüm Theorem 1'in kapalı formuyla eşleşir (sayısal hata < %1).
2. Senaryo 5'te ağ canlı kalır ve `cost_attack ≥ Bitcoin-eşdeğeri` korunur.
3. Senaryo 6'da saldırı maliyeti hiçbir epoch'ta monoton **değil** iken bile eşik altına
   düşmez (tail emission etkisinin kanıtı).
4. Senaryo 7 alarmı, `φ` düştüğünde (fayda kaybı) `θ` yükselir mi — analiz raporu.
5. **Sosyal değer:** Duplexia, aynı θ'da Bitcoin'i geçer mi (θ < 1/(ε−1) → ε=2 için θ<1)?
   Kanıtlanmış teori + simülasyon örtüşmesi gerekir.

## C.7 Modelin bilinen sınırları (dürüst)

- **Tek-dönem approximasyonu:** dinamik specülatif davranış yok (Pass'in kendisi de bırakmış).
- **θ sabitliği varsayımı:** parasal primitiflerin stabil olduğu treated-as-empirical (Pass'ın
  sömürüsü); ani değişimler geçiş sürecini bozabilir → senaryo 2/4 ile test edilir.
- **Talep çekme sürtüşmesi yok (Pass §1.8):** gerçek dünyada duplex madenciler müşteri bulmak
  zorunda → **agregasyon riski**; simülasyonda senaryo 7 ile izlenir ama modellenmez.
- **Sabit e:** heterojen maliyet için Pass §7'nin upward-sloping supply genişletmesi gerekir
  (Faz 4'te eklenmeli).
- **★ Ölçek-geçerlilik limiti (2026-09-20, `pass_sim.py` §9 kancasından bulundu):** model
  **yalnızca ana-ağ ölçeğinde** geçerlidir. F3a'nın küçük ağı (~1200 madenci) modeli
  **yeniden kalibre edemez** — hipotetik test **%86 sapma** verdi. Kök neden: Pass Thm 2
  "in any competitive equilibrium" derken rekabetçi denge varsayar; küçük ağlarda sabit
  maliyetler (altyapı/opex) marjinali domine eder, denge bozulur. Pass'in kendi kalibrasyonu
  $30B inference pazarı / 52.560 blok-yıl üzerinedir. **Pratik sonuç:** F3a verisi U-katmanı
  talebini (φ>0) ölçer, Pass modelini **kalibre etmez**; modelin kalibrasyonu Pearl ölçeğinde
  kalır (regression-guard ile korunuyor). Bu, V2 §10.1'in ilgili iddiasının düzeltilmesini
  gerektirdi — **düzeltildi**.

## C.8 Çalışan simülasyon — sonuçlar (`pass_sim.py`, 2026-09-19)

Kod çalıştırıldı ve doğrulandı (`python3 pass_sim.py`, çıkış `sim_out.txt`). **Önemli bulgular:**

1. **Pearl kalibrasyonu (validasyon):** modelin Tullock tam-ödeme koşulu `eS = PR`, Pearl'in
   ölçülen ağını ilk ilkelerden üretti: `S = PR/e = 338.707` GPU-op/blok vs **ölçülen 320.000
   GPU (%5,8 sapma)**; gelir/maliyet oranı **1,058** vs Basu'nun ölçtüğü **1,06**. → model canlı
   bir PoUW zincirini açıklayabiliyor.
2. **Theorem 1 rejim haritası:** tüm θ değerlerinde sıfır-kâr artıkları `< 1e-9`, pasif ihlaller
   `0`, market-clearing hatası `< 1e-12`; θ<0,3 → Fortessia, θ>0,3 → Duplexia; θ>3,33 → karışık.
3. **Pearl'in rejim teşhisi:** Pearl'in gerçek PR seviyesi **endojen θ = 1,05 → saf Duplexia**'ya
   düşüyor. Yani Pearl'in ekonomisi **zaten inference'ı sübside edecek rejimdeydi** — ama ölçülen
   φ = 0: fayda hiç gerçekleşmedi. Sebebi **E-gap** (Demirel): protokol matrislerin kimsenin işi
   olduğunu certify edemedi. **Pearl Bitconia gibi davrandı, Duplexia gibi pazarlandı.**
4. **Fortessia:** aynı θ'da güvenlik tam `1/(γ(1−1/α)) = 3,33×` artar, fayda aynı (teori ile
   birebir örtüşme).
5. **Tail emission:** halving'ler R düştükçe ekonomi 14. yıl civarında Duplexia → Fortessia'ya
   iner ve saldırı maliyeti `R_∞ = 2` PRL ile **$0,76 tabanına** oturur — Kaspa gibi sıfıra
   **gitmez**.
6. **Sıfır talep (K→0):** Q→0 ama **S→PR/e**; zincir pure-PoW olarak yaşar (Demirel Thm 2 ✓).
   Bu, "faydalı iş = güvenlik" vaadinin **olmadığının** resmi itirafıdır: güvenlik talep
   bağımsızdır, fayda yalnızca U katmanının fee-pazarında vardır.
7. **Heterojen maliyet (b=0→1):** S %38 azalır ama akım saldırı maliyeti yine PR/2; stok
   etkileri modelin dışında (Pass'in belirttiği sınırlama).

**Kabul ölçütü §C.6'nın durumu:** (1) ✓ Theorem 1 ile örtüşme, (2) ✓ sıfır talepte canlılık +
Bitcoin-eşit güvenlik, (3) ✓ tail emission tabanı, (4) kısmen — havuzlaşma senaryosu 7
modellenmedi (yalnız φ göstergesi), (5) ✓ θ<1/(ε−1) eşiği teorik olarak doğrulandı (ε=2 → θ<1).

---

# MÜKEMMELİYET CHECKLİSTİ (kâğıt üstü doğrulama)

**Kriptografi (her madde bağımsız incelemeye açık olmalı):**
- [ ] KW construction'un prescribed-hardness teoremi **bağımsız kriptograflarca** incelendi
      (conjecture durumu netleştirildi: low-rank random linear equations).
      *2026-09-19: ilk-geçiş bağımsız analiz yapıldı (`KW_ANALIZ.md`) — risk düşük-orta'ya*
      *düştü, ama bu bir LLM okumasıdır, insan kriptograf incelemesi DEĞİLDİR; kutu açık kalır.*
- [ ] ctx-binding formal lemması yazıldı (T-A2) ve random-oracle modelinde kanıtlandı.
- [ ] S2 için STARK AIR'nin **Lean ile ses doğrulaması** (S-two modeli, arXiv 2606.04311) +
      **ZEBRA-sınıfı otomatik kardinalite kontrolü** (arXiv 2609.15020) — under-constrained
      bug = 0 hedefi.
- [ ] Ses parametreleri λ ≥ 128; field boyutu ≥ 256-bit; agregasyon sonrası ses tekrar hesaplandı.
- [ ] PQ: STARK/hash + imzalar **ZK-ACE** (arXiv 2603.07974); hiçbir non-PQ primitive kalmadı.
- [ ] Crypto-agility: versioned schemas + çift-doğrulama penceresi + acil fallback (§A.9)
      **dokümante, test senaryolu**.

**Protokol:**
- [ ] Görev-pazarı spec'i (§A.1–A.8) pseudocode + test vector'leri ile tamamlandı.
- [ ] Anti-aggregation kuralı ve `C_fee` sınırı DAG ordering ile uyumlu (T-A3 ispatı).
- [ ] Difficulty retarget algoritması (§B.3) simülasyonda osilasyon testinden geçti
      (4× sınırlar + medyan filtre).
- [ ] Yaşam döngüsü (§A.8) her suç sınıfı için slash kanıtı içeriyor.

**Ekonomi:**
- [ ] Pass modeli simülasyonu (§C.3) 8 senaryonun **tüm** kabul ölçütlerini geçti (§C.6).
- [ ] Emisyon eğrisi (§C.5) değiştirilemez olarak yayınlandı; tail emission kanıtlandı.
- [ ] Gösterge tablosu (§C.4) zincir-üstü okunabilir ve alarm eşikleri tanımlı.

**Hukuk/şeffaflık:**
- [ ] Howey analizi + TR lisans rejimi incelemesi tamamlandı (açık nokta: findings §12).
- [ ] Pearl Network (ePrint 2025/685 üzerine kurulu) ile **farklılık tablosu** yayınlandı:
      KÖK v2'nin katkısı = GHOSTDAG + crypto-agility düzlemi + tail emission + premium SNARK
      hizmet katmanı; **KW çekirdeği paylaşılan** (intihal değil, alıntılı).

**"Kâğıt üzerinde mükemmelliyet" ölçütü:** yukarıdaki her kutucuk işaretli = spec düzeyinde
**85/100** (kalan 15 = testnet + bağımsız denetim + gerçek talep; kâğıtla kazanılamaz).

---

## D. 2026-09-21 DENETIM VE DOGRULAMA OZETI (TR ic not)

Bu oturumda yapilanlarin HEPSI yukaridaki spec metnini dogrudan etkilemez;
ama okuyucu (kullanici) icin burada ozetlenmelidir:

1. *** UYDURMA BULUNDU: "Hawthorne-style governance" *** — spec'te ve EN
   spec'te vardi; HICBIR kaynakta yok. CIKARILDI; yerine somut 5 adimli
   §A.11 whitelist governance (oneri -> 2-epoch dogrulama -> sifir
   false-accept -> versioned-schema aktivasyonu -> simetrik cikarma).
   **Bu spec'te zaten uygulanmis durumda (yukariya bakin).**

2. *** BIBLIOGRAPHY 11/11 LIVE-VERIFIED *** — 3 arXiv + 4 ePrint + 4 daha.
   arXiv 2504.09971 (KW, 2 yazar), 2606.06700 (Pass TEK yazar,
   Bitconia/Fortessia/Duplexia birebir), 2606.04819 (Basu, Pearl'in tum
   sayilari), 2007.01046 (Dotan-Tochner), 2209.03865 (Hoffmann);
   ePrint 2017/203, 2018/104, 2024/1731, 2025/685, 2025/1814, 2026/1492.

3. *** SEC v. RIPPLE COZULDU *** (onceki oturumda BULUNAMADI demistik):
   Torres 13.07.2023 programmatic borsa satislari menkul kiymet DEGIL;
   07.08.2024 $125,035,150 ceza; 07.08.2025 itirazlar geri cekildi (KAPANDI);
   *** 17.03.2026 SEC XRP'i BTC/ETH/SOL/XLM ile "dijital emtia" ***.
   Bu, fair-launch/no-premine/no-investor tasariminin YASAL NEDENIDIR.

4. *** MICA VERBATIM DOGRULANDI *** — EUR-Lex CELEX:32023R1114. **Duzeltme:
   utility token = Article 3(9), "only intended to provide access to a good
   or a service supplied by its issuer" — eskiden 3(1)(5) yaziyorduk.** KOK
   token'i (9)'a uymaz (madenci odulu = "value or a right").

5. *** PAZAR BOYUTU OLCULDU *** — Nvidia FY2026 $215B (3 yilda 8 kat:
   26.9/60.9/130/215), Q2 FY27 $96.2B +%106, $100B/10GW OpenAI.

6. *** DERIN TURKCE TEMIZLIGI *** — EN pakette 77+ Turkce kaynak stringi
   vardi (yorumlar); hepsi Ingilizcelestirildi. **EN paket simdi GERCEKTEN
   temiz** (harf + kelime + calisma cikti denetimi).

**PUAN: 37 (v1) -> 77 -> ~81/100 (2026-09-21). 85 kagi tavani hala gecerli;
kalan ~4-5 puan insan kriptograf incelemesi ve canli olcumle kazanilir.**

---

## E. 2026-09-21 ADOPTION: "INSANLAR BUNU NEDEN KULLANSIN?" (TR ic not)

*** Bu bolum, projenin EN onemli sorusunu test edilebilir koda cevirir. ***
Paper §11b ile birlikte okunmali. `adoption_econ.py` (TV-35/36/37).

### E.1 MERKEZI IDDIA: "compute ucretsiz" YANLIS, dogrusu "sübvansiyeli"

Standart PoUW pitch'i: "madinci hardware+elektrigi zaten odemis, o yuzden
useful work'u sifir marjinal maliyetle satabilir."

**YANLIS.** Madincinin hardware'i block reward ile odemis ama o reward belirli
bir sey satin alir: **kazanan piyango biletini.** Satisa giden compute,
madencilige giden compute DEGILDIR. Bir saniye GPU'nun gercek marjinal maliyeti
= o saniyenin madencilik geliri. Compute UCRETSIZ degil.

**Dogru versiyon (tax incidence, free lunch degil):** security budget protokolun
zaten odeyecegi bir maliyet; o yuzden madincinin **yine yapacagi** isin uzerine
binen useful work, **security harcamasi tarafindan SÜBVANSE EDILIR** — ucuz,
ucretsiz degil; ve KW kernel'i ile ayni is olcutunde (alpha ~1.3, KW'dan birebir
dogrulandi) o kadar ucuz. Bindikleri yerde fee neredeyse tamamen kar. Binmedikleri
yerde U katmani ayni FLOP'lar icin madencilikle rekabet eder ve piyasa fiyatini
odemek zorundadir.

*** DESIGN KARARI: U katmani, satilan is ile madencilik isinin KW izin verdigi
olcude OVERLAP etmesini gerektirir. Mining kernel'in otesinde EK compute
isteyen her task sübvansizdir ve kendi ekonomisiyle ayakta durmalidir. ***

### E.2 KARSIT-ORNEK: Pearl (Basu 2606.04819, birebir dogrulandi)

Pearl canli agi: **24 EH/s, ~320,000 GPU-eslenigi (~112 MW) ve sattigi useful
compute = SIFIR.** Bu hipotetik bir basarisizlik degil; buyuk bir PoUW zincirinin
OLCULMUS kararli halidir. KOK'un farkli olacagi iddiasi **nedensel** bir cevap
vermeli:

1. Pearl'in isi alinmak istenen is degildi. **KOK:** G katmani MatMul (KW) =
   AI inference'in ayni ilkeligi; hardware ile workload hizali.
2. Pearl'in fiyatlandirilmis pazari yoktu. **KOK:** U katmani bir PAZAR (escrow,
   fee, burn), bir hayir kurumu degil; talep odemeli bir islem olarak gelmeli.
3. Pearl madencilerine hizmet etmek icin bir neden yoktu. **KOK:** fee, tail
   subsidy'nin otesinde kazanmanin TEK yolu; tail bilerek kucuk (2 KOK).

*** ACIK GAP: bu ucunden HICBIRI talebin geleceginin KANITI degil; hepsi
onkosul. Kimse gelcek mi? Bu deneysel bir soru ve hicbir paper cozemez. ***

### E.3 IKI-TARAFILI SOGUK BASLANGIC (TV-36) — OLU DENGE EMICIDIR

Blokzincir iki-tarafili bir pazardir. Basarisiz hali **empty-block denge**:
madenciler subsidy ile kazir, kimse task gondermez cunku pazar yok, zincir
sonsuza dek phi=0'da calisir; islevsel olarak duz PoW zinciri + daha kotu
pazarlama. Iste Pearl'in olculmus hali bu. Ve bu KARARLI bir hal: olu denge
havluzunun cekim alanidir.

TV-36 **kritik talep tohumunu** bulur: gun birinden itibaren ne kadarlik gercek
ODEMELI talep gerekli ki pazar olu durumdan kacabilsin? Iki bulgu:

1. *** Tohum protokol tarafindan uretilemez. *** Hicbir token dagitimi/airdrop,
   "bir isi olan" bir alici yaratmaz. Tohumu zaten compute odemekte olan biri
   getirir. *** Iste bu yuzden F0 (talep kesfi) yol haritasinin art IK
   asamasidir — formal spec'in haleflerinden ONCE. ***
2. *** Break-even'in altinda olu denge EMICIDIR — hicbir tohum kacamaz. ***
   Zincir compute'u piyasadaki pahaliysa adoption'a sübvansiye ile
   ulasamaz; cross-subsidy GERCEK olmali (tekrar overlap sartina donus).

### E.4 IKI DURUST SEBEP (baskasinin yok)

Insanlar KOK'u SADECE su iki nedenden biri ile kullanir:

**(a) Zaten odedigi bir is icin KANITLANABILIR ucuz.** "Teoride ucuz" degil;
bugun var olan bir workload icin fiyat teklif edilen ucuz. Bu bir SATIS
problemidir, kriptografi problemi degil.

**(b) Isin calisabilecegi TEK izin-verilmeyen yer.** Bir cloud provider'in
hostlamayacagi bir hesaplama, veya provenance'i dogrulanabilir olmalidir
(provably-correct inference, tekrarlanabilir arastirma, mevzuat denetim izi) —
her fiyata ikamesi olmayan. Daha kucuk ama daha savunulabilir pazar; cunku
mevcut rakip fiyati dusurerek bu konuda rekabet edemez.

Her sey else (yesil anlatim, "bos enerji" argumani, AI-for-hepsi retorigi)
Pearl'in olculmus sifirinin cirkin bir sekilde yalanladigi dekorasyondur.
*** "Bos enerji kotudur" hikayesi olan bir zincirin, "iste bir musteri"
hikayesi olan bir zincire verecegi cevap yoktur. ***

### E.5 GENISLEME ALANLARI (dürüst filtre)

| Yon | Neden makul | Neden basarili olabilir | Durum |
|---|---|---|---|
| **Verifiable inference as a service** | U katmani zaten MatMul ispatlar; inference MatMul'DUR. (b) sebebi. | Kucuk olcekte dogrulama maliyeti isin maliyetini asabilir; provenance pazarı ispatlanmamis | **BIRINCIL aday.** Gercek alici gerek (F0) |
| **Baska zincirler icin ZK-coprocessing** | Diger L1/L2'lerin kanitlanabilir off-chain compute'a ihtiyaci var; KOK'un proving market'i tam bu | Zincir de isletmeyen ozel prover aglariyla rekabet | **IKINCIL.** Prover pazarı gercek; KOK en ucuz prover mu, degil |
| **Izin-verilmeyen batch compute** | (a) sebebi: fiyat-hassas MatMul-sekilli is | Emtia pazar; fiyatta kazanmak icin cross-subsidy gercek olmali | **Overlap gercek mi, sart** |
| **AI agent settlement layer** | Hizli bloklar + native compute market = tutarli agent altyapisi | Spekulatif; henuz var olmayan bir agent ekosistemine bagli | *** ACIKCA ERTELENDI — umut uzerine insa ETME *** |

### E.6 KILL CRITERIA (pesten soylendi)

F3a'yi gecmeye deger olmak icin projede **EN AZ BIR GERCEK ODENEN TASK** olmali.
F3a sifir gercek talep ile biterse, dürüst sonuc: utility katmaninin pazari yok
ve proje belirtilen pure-PoW moduna (§A.9) donmeli — bu MEŞRU bir sonuctur,
zaten tasarlanmis olani, ve "talep geliyor" ısrariyla yillarini Pearl'in olculmus
haline yaklasmaktan harcamaktan cok daha iyidir.

*** KULLANICININ SORUSUNUN CEVABI (bilerek rahatsiz edici): projenin hayatta
kalmasi kriptografiye (kagit gucu kadar guclu) ya da hukuka (navigasyon mumkun)
degil — **TEK MUSTERI TEK IS**'e bagli. Bu KOK'a ozgu bir zayiflik degil; her
iki-tarafili pazarin seklidir. Ama yol haritasinin artik testnet ile degil,
talep kesfi ile baslamasinin nedeni budur. ***

---

## F. 2026-09-21 PEARL'IN DOGRULAMA ACIGI — BIZDE NASIL ONLENIR (TV-38)

*** Bu bolum, projenin en kritik teknik ayrim noktasidir. ***
Kaynak: `arastirma/pazar_ve_rekabet_2026.md` + `u_layer_prototype_en.py` TV-38.

### F.1 PEARL'DE NE OLDU (olculdu, varsayim degil)

Pearl (Basu, arXiv 2606.04819) 24 EH/s / 320.000 GPU-eslenigi / 112 MW ile
**SIFIR** faydali AI computation satti. *** MEKANIZMA: ***

1. Dominant mining yaziliminda **HIC inference kodu YOKTU** — madenciler
   "faydali" isi zaten hic yapmiyordu.
2. Dogrulama **RASTGELE MATRISLERI KABUL EDIYORDU** — protocol gercek is ile
   tiyatroyu ayiramadi.
3. Sonuc: protocol tiyatro aldi ve 24 EH/s "faydali" hashpower aslinda
   faydali degildi.

*** ÖZET: Pearl'in basarisizligi bir madincer ahlaki sorunu DEGIL, bir
PROTOKOL TASARIM hatasidir. Dogrulayici, sertifikayi iddia edilen HESAPLAMAYA
BAGLAMADI. ***

### F.2 KOK'TA AYNI HATA VAR MI? (TEST EDILDI: HAYIR)

TV-38 (`u_layer_prototype_en.py`), kernel'imizin ayni kusura sahip olup
olmadigini sorar. *** CEVAP: HAYIR. *** Üç saldiri test edildi:

| Saldiri | Aciklama | verify() sonucu |
|---|---|---|
| **Uydurma sertifika** | Madinci hic MatMul yapmadan bir tile secip gonderir | **RED** |
| **Sahte tile degeri** | Gercek koordinatlar ama hic hesaplanmamis bir deger | **RED** |
| **Yanlis input matrisleri** | Sertifika gercek, ama A (veya B) degistirilmis | **RED** |
| (kontrol) Gercek sertifika | Dürüst madincinin urettigi | KABUL |

### F.3 MEKANIZMA — NEDEN YAPISAL OLARAK DAHA IYIYIZ ( tesaduf degil )

`verify()` iddia edilen tile'i **A, B ve ROM-turevli noise'dan YENIDEN
hesaplar**:

```
acc = sum_l  (A[i*r][l*r] + E[i*r][l*r]) * (B[l*r][j*r] + F[l*r][j*r])  mod q
return  acc == val  AND  H("tile", ctx, nonce, i, j, val) % target == 0
```

Bu NEDEN baglayici:
1. **A ve B verify()'a gecer** — madinci kendi girdilerini uretemez, cunku
   verifier ayni A ve B'yi kullanir. *** A veya B'yi degistirmek acc'yi
   degistirir, bu da esitligi bozar. *** (TV-38'de test edildi.)
2. **E, F ROM'dan gelir** (`ctx` ile tohumlanir) — madinci noise'u secemez,
   bu KW Lemma 6.5'in guvenlik bacagidir.
3. **Hedef hash'i tile DEGERINE baglidir** — `H("tile", ctx, nonce, i, j, val)`,
   yani sadece *dogru degeri* hesaplamak madincinin work'unu kanitlar.
   Uydurma bir deger hedefe carpmaz.

*** KAYNAKSAL OZET: Pearl'in dogrulayicisi sertifikayi HESAPLAMAYA
baglamamisti; bizimki baglar. 24 EH/s "gercek is" ile 24 EH/s "tiyatro"
arasindaki nedensel fark budur. ***

### F.4 DURUST KALAN ACIKLAR (kapatilmadi, kaydedildi)

TV-38 bir *prototip* testidir; uretim olcutunde su aciklar hala vardir:

1. **Tile kucuktur** (m = n/r): verify() tum MatMul'u degil, TEK tile'i
   yeniden hesaplar — bu tasarim geregidir (verification maliyeti).
   *** "Tile atlama" riski ANALIZ EDILDI ve YOK: H one-way oldugu icin
   madinci hangi val'in hedefe vuracagini ONGOREMEZ, bu yuzden bir tile'in
   sansini gormek icin onu HESAPLAMAK ZORUNDADIR. Baska tile'lari atlamak
   sadece o nonce'daki sansini azaltir; honest madinci ile ayni beklenen
   work. *** Asil tasarimsal gercek: her nonce'da m^2 tile'dan herhangi
   biri hedefe vurabilir, bu beklenti-work'u m^2 ile carpip (sadece
   tek-MatMul PoW'una gore) hizlandirir — DESIGN'dir, guvenlik sorunu
   degildir, ve m^2 = 16 toy boyutta zaten olculmustur (TV-2 geometric
   hardness 4.4/4.4/4.5). ***
2. **q=97, n=8, r=2 toy boyutlari** — asimptotik guvenlik iddia EDILEMEZ.
3. **H hala SHA-256-ish HMAC** — uretimde STARK-friendly hash (POSET/Poseidon)
   gerekir; A.9'daki PQ setiyle ayni kapsamda.

*** STRATEJIK ONEM: F.2-F.3, KOK'un Pearl ile arasindaki EN SAVUNULABILIR
teknik farktir ve artik iddia degil CALISAN BIR TEST'tir. F.4 ise F0b'nin
(gercek AIR) neden yol haritasinda oncelikli oldugunun gerekcesidir. ***
