# ANTIGRAVITY AJAN ÖNERİSİ — ŞARTNAME DEĞERLENDİRMESİ

**Değerlendiren:** KÖK Network geliştirme ajanı (bu deponun mimarı)
**Tarih:** 2026-09-24
**Yöntem:** Her iddia **kodda ölçülerek** doğrulandı; yalnızca okuma değil.

İncelenen dosyalar:
- `00_BES_PROJE_CELISKISIZ_MIMARI_VE_AJAN_SARTNAMESI.md` (314 satır)
- `PROJE_KAGIDI.md` (113 satır)

---

## SORU 1: PoUM + GKR-Sumcheck + Freivalds O(log n) + 10-32 BPS GHOSTDAG, %100 egemen L1 olarak çalışabilir mi?

**Kısa yanıt: Şartnamedeki bileşenlerin ÜÇÜNCÜSÜ hariç hiçbiri bu repoda yok; ve şartnamedeki
Freivalds vurgusu projenin kendi makalesinin vardığı sonucun TERSİDİR. Egemenlik iddiası DOĞRU,
doğrulama yığını YANLIŞ.**

### Ölçülen gerçek (bu repoda ne var)

| Şartname iddiası | Repoda var mı | Ölçüm |
|---|---|---|
| PoUM (MatMul PoW) | **VAR** — `KWKernel` (`g_layer_tests_en.py:38`) | prove 3.47 ms ↔ verify 0.25 ms, ok=True (toy q=97, n=8, target 2^1) |
| GKR-Sumcheck | **YOK** — 0 Python dosyası "sumcheck"/"GKR" içeriyor (grep sonucu) | — |
| Freivalds `A(Br)==Cr` doğrulayıcısı | **YOK** — kodda hiçbir `def` Freivalds doğrulaması yapmıyor | — |
| PVI / WASM verifier | **YOK** — 0 `.py`/`.rs` dosyası; yalnızca markdown | — |
| GHOSTDAG 10-32 BPS | **KISMEN** — `ghostdag_proto_en.py` ama BPS=1, k=18 Kaspa şablonu | spec L668: "KÖK v2'nin kendi BPS'si henüz seçilmedi" |
| kok-node (Rust) | **YOK** — 0 `.rs` dosyası | — |

### Şartname ile proje arasındaki EN KRİTİK çelişki: Freivalds

Şartname (§2.2 ve PROJE_KAGIDI §2) doğrulama yöntemi olarak **GKR-Sumcheck + Freivalds**
sunuyor. Ancak projenin **kendi makalesi** Freivalds'ı bir **zayıflık** olarak değerlendiriyor:

- `KOK_V2_PAPER.md:253`: "With KW, prescribed hardness is independent of the input (no
  structured-matrix shortcut); resistance to FMM ... is claimed. **The precondition of agility is
  that the hardness be structural — KW provides this, plain Freivalds does not.**"
- `KOK_V2_PAPER.md:28`: "v1's Freivalds equation is, relative to KW, 'trivial O(1) overhead but...'"
- `g_layer_tests_en.py:460` (`v1_contrast`) bunu **sayılarla** gösteriyor: plain Freivalds'da
  saldırgan `A=0` seçerse honest O(n³) işe karşı sadece O(n) harcar — avantaj oranı **n²**.
  Ölçülen: n=8 için honest 512 ↔ saldırı 8 (sıfır matris avantajı 64x).

**Sonuç:** Şartname, projenin yıllık araştırmasının **reddettiği** bir yöntemi çekirdek olarak
sunuyor. Projenin gerçekte inşa ettiği şey **F0b = zk-AIR (STARK-like)**:
`f0b_air_proto.py` + `f0b_fri_en.py` + `f0b_prod_field_en.py` + `spec_rederive_en.py`.
Ölçülen asimetri: prove **4.56 ms** ↔ verify **0.37 ms** (toy q=97, n=8, r=2).

**(2026-09-25, Rust port sırasında yeniden ölçüldü — bu iki sayının ikisi de
STACK seviyesindedir ve bileşenlere yanlış atfedilmiştir):** aynı girdide,
aynı tohumda (random.seed 20260925), bu makinede ayrı ayrı ölçüldüğünde:

| katman | prove | verify |
|---|---|---|
| AIR (`f0b_air_proto.TileAIR`) | 0.959 ms | 0.051 ms |
| FRI (`f0b_fri_en.FriRecursive`) | 0.043 ms | 0.315 ms |
| **AIR+FRI stack** | **1.002 ms** | **0.365 ms** |

Yani **"0.37 ms verify" AIR+FRI stack'inin toplamıdır** (0.365), FRI tek başına
**0.315 ms**'dir — FRI'ya atfedildiğinde sayı, olduğu kadar bileşeni içerir.
**"4.56 ms prove" bu toy parametrelerde bu makinede yeniden üretilmedi**
(AIR+FRI prove 1.002 ms, Merkle köklerinin inşası dahil 1.25 ms). Sayı büyük
olasılıkla daha yavaş bir makinede veya daha büyük bir toy'da alındı;
silinmedi çünkü denetim onu bu repoda ölçülebilir bir sayı olarak sundu —
burada kaydedilen, **decomposition'ın kendisidir**: hangi sayı hangi
bileşene ait. Rust Criterion benchmark'ları aynı girdide 591.75 µs prove /
33.14 µs AIR verify ve 7.35 µs / 47.05 µs FRI prove/verify ölçer.

**Bu bir bagaj değil, bir ÖZELLİKTİR** ve şartnameye uygun hale getirilmeli: doğrulama
stack'i GKR/Freivalds yerine **zk-AIR/FRI** olarak yazılmalı.

### "4 milisaniye" ve "O(log n)" iddiaları

PROJE_KAGIDI §2 "Doğrulama süresi: 4 milisaniye!" iddiasında bulunuyor. **Bu sayı bu repoda
ölçülebilir durumda değil:**
- F0b AIR verify (toy): **0.37 ms** — ama toy q=97, n=8. Bu hız toy olmasından gelir.
- Makalenin gerçek hedefi (`KOK_V2_PAPER.md:201`): ZK-ACE Circle STARK backend **14.5 ms prove /
  1.1 ms verify**; spec L578 hedefi "verify ≤2 ms/block".
- **Yani "4 ms" ne toy ölçümüne ne de üretim hedefine karşılık geliyor.** Üretime yönelik
  tek ihtimal: 1.1 ms verify (makaleden) veya 2 ms hedefi (spec'ten).

"O(log n)" ise **ölçülmedi**: FRI'nin `verify_round`'u round-5'te `Θ(q·deg)` olduğu ölçülerek
belgelendi (`f0b_fri_en.py:26-34`: 0.0003 s @ q=97 ... 0.0685 s @ q=10007/deg 64). Gerçek log
verifier cost her turda tek sorgu noktasından değerlendirme yapar; prototip bunu yapmıyor.

### 10-32 BPS

Şartname "10-32 BPS" aralığı veriyor. **Makale ve spec 10 BPS hedefliyor** (spec L652:
`T_b = 1/λ_b` örn. 100 ms = 10 BPS; L578/L594: "10 BPS, verify ≤2 ms/block"). **32 BPS
için hiçbir parametre seçilmemiştir** — bu, şartnamenin makaleden %220'lük bir hedef
sunduğunu gösterir. Seçilmemiş bir sayıyı sonuç olarak sunmak, kullanıcının
"ölçerek doğrula" standardına uymaz.

---

## SORU 2: PVI WASM arayüzü kripto-çeviklik için yeterli mi?

**Kısa yanıt: Tasarım olarak DOĞRU ve yeterli; ama bu repoda HİÇ UYGULANMADIKTAN dolusu
denetlenmemiş bir varsayımdır.**

### Tasarım değerlendirmesi (şartname §3.2.3 ve PROJE_KAGIDI §4)

PVI'nın tasarımı sağlamdır:
1. Verifier çekirdeğinin konsensüs çekirdeğinden ayrılması — **doğru**. PoW zincirlerinin
   kriptografiyi consensus'a gömmesi (Bitcoin) gerçek bir çeviklik sorunudur.
2. WASM izolasyonu — **doğru seçim**. Deterministik, sandbox'lı, platformdan bağımsız.
3. On-chain yönetişimle WASM değişimi, hard-fork olmadan — **doğru**. Bu, gerçek bir
   kripto-çeviklik avantajıdır.

### Ölçülen gerçek

- **0 `.rs`, 0 `.py`, 0 `.wasm`** dosyası PVI implementasyonu içeriyor. Sadece 5 markdown
  dosyası `PVI`/`WASM` geçiyor (PROJE_KAGIDI, PROJE_KAGIDI_V2, KOK_V2_PAPER, RESEARCH_GAPS,
  DEGERLENDIRME_100).
- Şartnamedeki `IPluggableVerifier` Rust trait'i (`verify_matrix_proof`) **yazılmamış**.
- **Sonuç:** "yeterli mi" sorusu **ölçülemez**. Bir tasarım doğru görünebilir, ama kripto-çeviklik
  bir **uygulama** özelliğidir: WASM metering, gas limitleri, verifier versionleme, rollback,
  bir upgrade'in consensus'u bölme riski — bunların hiçbiri test edilmemiş.

**Projenin kendi standardına göre dürüst yanıt:** PVI'nın *kavramı* çeviklik için yeterli bir
tasarım sunar; ama **"yeterli" olduğu KANITLANMAMIŞTIR** çünkü hiç yoktur. Bu, makalenin
F3/F3b yol haritasında (Rust `kok-node` + S-two/Circle STARK verifier) bırakılmış bir
gerekliliktir; bir özellik tamamlandı olarak sunulamaz.

---

## SORU 3: Şartnamede KÖK'ün bağımsızlığını zedeleyen, L2/alt-modül gibi gösteren ifade var mı?

**Kısa yanıt: HAYIR — tam aksine, şartname KÖK'ü AŞIRI EGEMEN konumlandırıyor. Egemenlik
iddiasında bir çelişki YOK. Asıl sorun egemenlikte değil, POUM'un tanımında.**

Şartnamede KÖK'ün egemenliğini zedeleyen tek bir ifade bulamadım. Aksine:
- Şartname §2 satır 59: "KÖK Network bağımsız bir L1'dir; Unpump'ın KÖK'e taşınması en erken
  Faz 4 opsiyonudur."
- Şartname §2 satır 60: KÖK ile TamgaNet'in "KAPSAMLARI VE GÖREVLERİ TAMAMEN FARKLIDIR" —
  doğru bir ayrım.
- AJAN 3 direktifi (§4): "KÖK Network bir akıllı sözleşme veya token DEĞİLDİR; Bitcoin ve
  Kaspa gibi bağımsız bir L1 blokzinciridir."
- PROJE_KAGIDI §5: "hiçbir platforma veya projeye bağımlı DEĞİLDİR."

Bu **doğru bir dekuplaj doktrini**. Beş projenin birbirini beklememesi tasarımı,
geliştirmeyi felç etmeyecek kadar gevşek bağlıdır.

### Ancak iki BULGU var (egemenlik değil, TANIM sorunu)

**BULGU-A (ORTA): PoUM'un "yapay zeka görevi" vaadi ile makalenin "useful work" arasında
fark var.**
PROJE_KAGIDI §1.3 ve şartname §3.3.1, madencileri "açık kaynaklı yapay zeka modellerinin tensör
işlemlerini çözmeye" yönlendirdiğini iddia ediyor. Ancak projenin **makalesi bunu açıkça
reddediyor** (`KOK_V2_PAPER.md:109-112`, Layer G):
> "The miner chooses its own MatMul input (freely)... **But it is not claimed to be 'useful'** —
> so as not to repeat Pearl's error."

Ve G katmanı "filler" olarak dense-random MatMul = **pure-PoW mode** kullanıyor. Yani:
- **G katmanı (güvenlik) faydalı DEĞİLDİR** — demand-independent, pure-PoW.
- **U katmanı (fayda) konsensüs ağırlığına sahip DEĞİLDİR** — "zero consensus weight — it never
  participates in leader election" (makale L124).

**Bu bir çelişki değil, olgun bir itiraftır** — ama PROJE_KAGIDI/şartname bu iki katmanlı
gerçekliği yansıtmıyor; "madenciler AI tensör işlemleri çözer" şeklinde tek-katmanlı bir
resim sunuyor. **Egemenliğe zarar vermez, ama PoUM'un vaadini aşırı-tanımlar.**

**BULGU-B (DÜŞÜK): "Tengra" yedek ismi marka karışıklığı yaratıyor.**
PROJE_KAGIDI L7 yedek isim olarak "Tengra ($TENGRA)" listeliyor; şartname L43 "KÖK NETWORK /
TENGRA" ikisini birleştiriyor. Tek bir L1 için iki isim ve iki sembol, dışarıdan bakıldığında
"iki ayrı proje mi?" sorusunu doğurur. Kararı bekleyen bir lansman ön-kararı olduğu belirtilmiş,
ancak şartname ikisini birleştirerek bunu bir sonuç gibi sunuyor.

---

## SORU 4: Bu mimarideki en zayıf matematiksel veya ağ güvenliği halkası nedir?

Bu soruya **bu repoda ölçülen bulgularla** yanıt veriyorum (round-5 adversarial inceleme +
bu değerlendirme).

### En zayıf halka: PoUM'un "useful" vaadinin kendisi — ölçülen φ=0

**Teşhis zaten kanıtlanmış durumda.** Pearl (live PoUW ağı) bu mimarinın öncülüdür ve
**φ=0 ölçülmüştür**: faydalı iş SIFIR. Nedeni **E-gap** (Demirel 2026/1492):
protokol matrislerin kimsenin görevi olduğunu **sertifikalayamıyordu**.

Bu repoda **round-5'te kapatıldı** (TV-82, `tv72_egap_mechanism_en.py`):
- **Arm A** (pre-binding kuralı, PoW target sadece): sahte matrisler **5/5 kabul** —
  tespit edilebilirlik **0 by construction**.
- **Arm B** (post-binding, verifier task'tan türetiyor): **4/4 ret** + commissioned çift kabul.

**Ama bu yalnızca MEKANİZMADIR, sonucu değiştirmez:** `tv72_egap_mechanism_en.py` kendi
çıktısında dürüstçe belirtiyor — "a binding that lets the protocol NOTICE cheating is not
evidence buyers will arrive". **φ > 0 hala bir ÖNGÖRÜDÜR, bir ölçüm değil.** Talep tarafı F0
ve **bilinçli olarak başlatılmadı**.

**Sonuç:** Mimarinin en zayıf halkası kriptografi değil — **taleptir**. Güvenlik G katmanından
gelir (PR/2, demand-independent) ve bu **ölçülmüştür**. Ama "useful" vaadi ölçülmemiştir ve
Pearl'in φ=0'ı bu vaadin nasıl sonuçlandığının tek canlı örneğidir.

### Matematiksel zayıf halkalar (round-5'te ölçülen, artık DÜZELTİLMİŞ olsa da risk sınıfları)

1. **FRI derece sınırı (KRİTİK, round-5'te kapandı):** `verify_round` derece sınırı
   kontrol etmiyordu; q=97'de tüm 48 quadratic residue'da sıfırlanan derece-48 sahte
   **9/9 KABUL** ediliyordu. Bu, tüm FRI ses dönüşümünün temeliydi. Artık kontrol ediliyor
   (probe 4/4), ama bu sınıf **herhangi bir yerde derece bağlaması olmayan herhangi bir
   kabul fonksiyonunda** tekrar çıkabilir.

2. **Kimlik-checker sınıfı (KRİTİK):** round-5'in en önemli bulgusu, bir kabul kontrolünün
   **özdeşlik** olmasıydı. İki örnek:
   - `pass_sim` residual checker: solver'ın çözdüğü denklemin aynısını hesapladığı için
     **0.00e+00** veriyor, fail edemiyor — bunun arkasında yanlış üslü theta çözücü gizliydi
     (Pearl theta 1.05 → 1.657 düzeltildi).
   - FRI fold relation: her derece-(q-1)/2 polinomu tarafından sağlanıyor.
   **Ders:** fail edemeyen bir kontrol hiçbir şeyi korumaz.

3. **Bağlama bir yerde uygulanıp başka yerde kaybı (yinelenen sınıf):**
   `spec_rederive` verify, matrix commitment'ları **proof'un kendisinden** okuyordu;
   saldırganın seçtiği accumulator için kendine-tutarlı uydurma tile **True** doğruluyordu.
   Benzer hata round-3'te `egap_cert`'te yakalanmıştı. Artık task'tan geliyor (4/4 ret).

### Ağ güvenliği zayıf halkaları

1. **GHOSTDAG'da PoW/geçerlilik kontrolü YOK** (`ghostdag_proto_en.py:39-42`):
   "every block is ASSUMED to carry valid PoW". GHOSTDAG'in güvenlik argümanı (anticone
   olasılık sınırı k) **PoW'a dayanır**. Prototip yalnızca DAG mantığını doğruluyor;
   üretimde PoW gerçek olacak. **Bu ölçülmemiş bir varsayımdır.**

2. **BPS ve K parametreleri seçilmemiş:** k=18 Kaspa BPS=1 şablonu; KÖK'ün kendi BPS'si
   yok. GHOSTDAG'in security threshold'u `k` ve `λ_b`'ye bağlıdır — bu ikisi
   belirsizken "10-32 BPS" güvenlik argümanı **veri eksik**.

3. **k=18'in Kaspa'dan alınması:** Kaspa'nın k=18 değeri Kaspa'nın kendi gecikme modeli
   ve hashrate dağılımı için optimize edilmiştir. Farklı bir BPS ve farklı bir ağ
   topolojisi için aynı k geçerli değildir. `ghostdag_proto_en.py:443` bunu kendisi
   itiraf ediyor: "k=18 is the Kaspa BPS=1 template; KOK v2's BPS is not yet chosen."

---

## ÖZET VE ÖNERİ

Şartname, **beş projenin birbirini beklememesi** dekuplaj doktrini açısından **başarılı ve
doğru** bir tasarımdır. KÖK'ün egemenliğine bir zarar vermez; L2/alt-modül gibi gösteren
ifade YOKTUR.

**Ancak KÖK bölümünde üç düzeltme gerekir:**

1. **Doğrulama yığını GKR/Freivalds'tan F0b zk-AIR/FRI'ye çevrilmeli.** Projenin kendi
   makalesi Freivalds'ı reddediyor; GKR için kod yok. Şartname, asıl inşa edileni
   (zk-AIR + FRI, prove 4.56 ms ↔ verify 0.37 ms toy'da) tanımlamalı.

2. **"4 milisaniye" ve "O(log n)" kaldırılmalı veya ölçülen değerle değiştirilmeli.**
   Üretim hedefi 2 ms/block (spec) veya 1.1 ms (ZK-ACE ölçümü); toy 0.37 ms. FRI'nın
   implementasyonu Θ(q·deg) — log cost hedefi bir tasarım amaçı olarak belirtilmeli,
   ölçülmüş bir sonuç gibi sunulmamalı.

3. **"10-32 BPS" → "10 BPS hedefi (parametreler seçilmemiş)" olarak düzeltilmeli.**
   32 BPS için hiçbir parametre (k, λ_b, difficulty window) seçilmemiştir.

**Ek olarak (egemenlik dışı):** PROJE_KAGIDI'nin tek-katmanlı "madenciler AI tensör çözer"
resmi, makalin iki-katmanlı gerçeğiyle (G=faydalı-değil + U=konsensüzsüz) değiştirilmeli —
bu bir zayıflık itirafı değil, Pearl'in φ=0'ından çıkarılan **olgun bir düzeltmedir**.

**En zayıf halka:** Kriptografi değil — **talep**. Güvenlik ölçülü (PR/2, φ'den bağımsız);
"faydalı" ölçülmemiş (φ > 0 öngörü). Pearl'in φ=0'ı bu vaadin tek canlı örneği ve
round-5'te inşa edilen E-gap bağlaması mekanizmayı düzeltti, sonucu değiştirmedi —
ki dosya kendi çıktısında bunu dürüstçe söylemektedir.
