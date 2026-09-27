# ECVRF prove maliyeti — ölçüm, çeyrek analiz ve bulunabilir optimizasyon

**Tarih:** 27 Eylül 2026 · **Dosya:** `crates/kok-u-layer/src/ecvrf.rs` ·
**Task 4 (Shift 4)** — "EC scalar mult için donanım hızlandırma ARAŞTIR: batch
inversion veya precompute. Bu gerçek maliyet; belki bir optimizasyon var."

## Özet (önce sonuç)

| Yöntem | Kazanç (ölçülen/tahmin) | Güvenlik riski | Hüküm |
|---|---|---|---|
| **Loop-invariant hoisting of y = x·B** | **1.24× ölçüldü** (0.811 → 0.652 ms/prove) | **YOK** (aynı hesap, başka yerde) | **YAPILDI** — `prove_with_public_key` |
| Fixed-base precompute (generator table) | ~1.3–1.5× kalan 2 mult üzerinden | **VAR** — elle constant-time tablo | ERTELENDİ (insan kriptograf gerekli) |
| Shamir's trick (x·H, k·H aynı H) | ~1.15× | **VAR** — data-dependent branching | ERTELENDİ |
| Batch inversion (Montgomery trick) | **%7** (0.063 ms / 0.87 ms) | Düşük ama efor yüksek | **YAPILMAZ** — kazanım efora değmez |

En değerli bulgu, lead'in önerdiğinin (**precompute / batch inversion**) dışında
çıktı: dört scalar mult'tan biri zaten **loop-invariant**'tır ve onu taşımak
hiçbir kriptografik koda dokunmadan 1.24× verir. En yüksek riskli olan
(precompute) ise en büyük potansiyel kazancı vaat ediyor ama projenin en büyük
açığı (§13 KNOWN GAPS #1: insan kriptograf incelemesi yok) nedeniyle elle
yazılmamalı.

## 1. Maliyetin anatomisi — önce profil, sonra tahmin

Bir tahminle başlanmadı. İki geçici benchmark `prove()`'u parçalara ayırdı
(her ikisi de sayıları verdikten sonra silindi):

**Birinci kırılım** (2000 prove üzerinden):

```
encode_to_curve   0.022 ms/prove    (  2.5%)
RFC 6979 nonce    0.010 ms/prove    (  1.2%)
prove'un geri kalanı 0.867 ms/prove ( 98.8%)  ← maliyet burada
```

**İkinci kırılım** — "geri kalan"ı açan:

```
4 EC scalar multiplication  1.499 ms
5 point encoding            0.025 ms
challenge hash              0.027 ms
```

**Sonuç:** bir prove'un %98.8'i `prove()`'un kendisinde, ve bunun da neredeyse
tümü dört P-256 scalar multiplication. Her şey diğer (encoding, hashing,
nonce) birlikte 0.06 ms — yani prove'u hızlandırmanın tek yolu scalar mult'ları
azaltmaktır.

**Bileşen ölçümü** (1000 tekrar, düşük load):

```
variable-base mult (projective)   0.183 ms
+ to_affine                       0.204 ms   → inversion = 0.021 ms
generator mult (x·B, u·k·B)       0.196 ms   ← variable-base ile AYNI
iki scalar, aynı base (x·H, k·H)  0.401 ms   ← tam 2×, paylaşım yok
```

`generator mult` ile `variable-base mult`'un **aynı** olması, p256 0.13.2'nin
generator için önceden hesaplanmış tablo kullanmadığını kanıtlar (aşağıda §3).

## 2. Yapılan optimizasyon — y = x·B'nin loop dışına alınması

**Gözlem:** `prove()`'un dört mult'undan ilki `y = x·B`'dir — bu **public
key**'in ta kendisidir. `assign_tasks` bir çağrı boyunca **tek bir sk** ile
N görev üzerinde prove yapar. Yani her prove'da aynı y değeri yeniden
hesaplanır; RFC 9381'in fonksiyon imzası (sk, alpha) aldığı için fonksiyon
bunu bilemez, ama çağıran bilir.

**Değişiklik:** `public_key_point(sk)` y'yi bir kez hesaplar;
`prove_with_public_key(sk, pk, &y, alpha)` onu argüman alır ve o mult'ı atlar.
RFC-uyumlu `prove()` **byte-for-byte dokunulmadı** — RFC 9381 Appendix B.1
vektörleri aynı yoldan test edilmeye devam eder.

**Bu bir VRF optimizasyonu DEĞİL, bir hesaplama yerinin değişmesidir.**
Çıktı (sk, alpha)'nın her zaman olduğu gibi aynı fonksiyonudur; hiçbir hesap
çıkarılmaz, aynı y çarpılır — sadece bir kez. Sabit-zamanlılık veya güvenlik
argümanı hakkında hiçbir şey değişmez.

**Güvenlik, güvensizliğe dayanır (failure mode analizi):** y yalnızca sk'nin
saf fonksiyonudur ve çağıran sk'yi de verir, bu yüzden cache'lenmiş y ancak
çağıran tutarsızsa sk'den farklı olabilir — ve o durumda proof doğrulanamaz,
çünkü `verify` y'ye verilen public key'den yeniden hesaplar. Başarısızlık modu
reddedilen prooftur, kabul edilen yanlış proof değil. Test
`a_cached_public_key_from_the_wrong_key_is_rejected` bunu kilitler: başka bir
anahtarın y'si ile üretilen proof `verify()`'da reddedilir.

**Kanıt:**

- `a_cached_public_key_gives_the_byte_identical_proof` — **her iki RFC test
  anahtarı × 64 alpha = 128 proof** üzerinden cached ve direct yolların
  byte-byte aynı olduğunu assert eder ve cached proof'un hala verify
  ettiğini (yani iki özdeş YANLIŞ cevabın birbiriyle uyuşması değil).
- **A/B ölçümü** (1500 prove, interleaved — load iki kolu da eşit etkilediği
  için oran load-robust):

```
direct    0.811 ms/prove
cached-y  0.652 ms/prove
speedup   1.24x
```

Bu, §1'in bileşen ölçümünden çıkan teorik 0.196/0.87 = %22.5 tahminiyle
uyumludur ve bağımsız bir yoldan doğrulanmış olur.

## 3. Fixed-base precompute — NIST tarafından önerilir, ama elle yazılmaz

NIST ECC workshop paper'i (Adalier & Mehmet, "Efficient and Secure ECC
Implementation of Curve P-256") bu şekli tam tarif eder:

> "The scalar multiplication consumes the bulk of the evaluation time, and must
> be implemented carefully to ensure that it does not inadvertently leak
> information about the secret scalar. For ECDSA sign operation of prime
> curves, the point used in the multiplication phase is always the base point
> G, which is a known value and can be pre-calculated. Thus, to reduce the
> latency of the point multiplication, Algorithm 2 can be used, which employs a
> fixed-base NAF windowing method."

ECDSA sign'daki `k·G` bizim `u = k·B`'mizin tam karşılığıdır. Paper'in
sayıları (P-256, w=4):

- scalar mult **~73 point addition**'a iner (düz binary yöntem 128A + 256D);
- storage **~4 KB** (64 önceden hesaplanmış nokta);
- P-256 için **w = 4 ve 5 "well-balanced"**;
- ve önemli olanı: **"Algorithm 2 improves both the performance and the
  regularity compared to Algorithm 1, since it only uses Point Additions,
  rather than both Point Double and Point Add operations, which could be
  detected by SPA methods"** — yani düzgün kurulursa SPA direncini
  *kötüleştirmez, iyileştirir*.

**Bu neden yapılmadı (dürüst engel):** `p256` 0.13.2 **`MulByGenerator`'ı
implemente etmez** (kaynak kodunda grep ile doğrulandı; `elliptic-curve`
0.13.8 trait'i tanımlar ama p256 bağlamaz). Yani tablo elle kurulmalıdır.
Sabir zamanlı tablo erişimi (constant-time selection / blinding) olmadan,
bellek erişim desenlerinden sk veya RFC 6979 nonce k sızar — bu, bir VRF için
**yıkıcıdır**: uniqueness ve pseudorandomness'in temeli o gizliliktir.

**Karar:** proje örgütünün en büyük açığı zaten "hiçbir insan kriptograf
incelemesi yapılmadı" (§13 / KOK_V2_REFERENCES.md KNOWN GAPS #1). Bu
değişiklik, tam olarak o incelemeyi gerektiren türdendir — elle yazılmış
scalar multiplication'ın yan-kanal denetimi olmadan canonical ECVRF anchor'una
konması, o açığı derinleştirir. **Phase 3 / audit item olarak kaydedildi**,
sayılarla birlikte: bir gözden geçiren olduğunda yapılacak ilk iş budur ve
beklenen kazanç kalan iki generator mult üzerinden ~1.3–1.5×, yani prove
başına ek ~%10–15.

## 4. Shamir's trick — aynı risk, daha küçük kazanç

`x·H` ve `k·H` aynı base H'yi paylaşır; simultane iki-scalar yöntem 0.401 ms'i
~0.25–0.30 ms'e indirebilir (~%13–17). Ama interleave pencereleme,
data-dependent branching getirir ve sabir zamanlılık için aynı elle-yazım
sorununu taşır. Aynı §3 gerekçesiyle ertelendi; kazancı precompute'tan küçük,
riski aynı.

## 5. Batch inversion — ölçüldü, değmez

Montgomery trick: n inversion → 1 inversion + 3(n−1) multiplication.
`prove()` dört `to_affine()` çağırır = dört inversion = 4 × 0.021 = 0.084 ms.
Dördünü birleştirmek 1 inversion + 9 mul bırakır; mul, inversion'dan çok
ucuzdur, bu yüzden kazanım ~0.063 ms — **0.87 ms'in %7'si**.

**Buna ek bir maliyet daha:** dört bağımsız mult'ın tek bir batched rutine
yeniden yapısı, ya p256'nın forklanmasını ya da elle field arithmetic
yazılmasını gerektirir; arajective sonuçlar sona kadar affine dönülemez.
**Hüküm: %7 için forklamaya değmez.** Ayrıca inversion, mult maliyetinin
sadece %10.3'üdür (0.021/0.204) — yani bu yöntem yanlış hedefi vurguluyordu;
maliyet scalar multiplication'ın kendisinde, onun bitişindeki inversion'da
değil.

## 6. Ne değişti, ne değişmedi

**Değişti:**

- `public_key_point(sk)` ve `prove_with_public_key(...)` eklendi;
- `assign_tasks` y'yi çağrı başına bir kez hesaplar;
- iki yeni test: byte-identical equivalence (128 proof) ve wrong-key rejection;
- **1.24× ölçülen prove hızlanması** — mining loop'unun VRF maliyeti.

**Değişmedi:**

- `prove()` ve `verify()` — RFC 9381 Appendix B.1 vektörleri byte-for-byte
  aynı yoldan test edilir (üç örnek testin tümü release modda geçer);
- sabir zamanlılık profili — hiçbir hesap eklenmedi/çıkarılmadı, sadece
  yeri taşındı;
- `assign_tasks`'ın çıktısı — aynı prooflar (byte-identical testi bunu
  korur, dolayısıyla önceki regression guard'ları hala aynı sayıları assert
  eder).

**Yan etki, dürüstçe kaydedildi:** `the_gate_filters` testi hala
`ecvrf::prove`'u doğrudan çağırır (cached yoldan değil), bu yüzden bu
optimizasyondan faydalanmaz — bilerek öyle bırakıldı, çünkü o test RFC'yolu
ölçer. `splitting_one_stake` ve üretim mining loop'u `assign_tasks`'ı
kullandığı için 1.24×'i alır. Guard'lar `PROVE_COUNT`'u her iki yolda da
artırır (her iki fonksiyon da artırır), dolayısıyla "6000 prove" assertion'u
hala geçerli ve optimizasyon bir prove'u gizleyemez.

## 7. Kalan potansiyel (sırayla)

Makul bir sıralama, her biri için gerekçesiyle:

1. **Fixed-base precompute (w=4, ~4 KB)** — NIST'in önerdiği, en büyük kalan
   kazanç (~%10–15 daha). **Engel:** insan kriptograf yan-kanal denetimi.
2. **Shamir's trick (x·H, k·H)** — ~%13–17, aynı engel.
3. **Batch inversion** — %7, forklama gerektirir, değmez.
4. **Geriye kalan 2 mult'tan hiçbiri paylaşılamaz** — x·H ve k·H farklı
   scalar'lar ve H alpha'ya bağlı olduğundan VRF'nin input binding'ini
   bozmadan birleştirilemez. Bu, Shift 3'te verilen "batch'lenebilir mi"
   sorusunun negatif cevabıdır ve hala geçerlidir: **batch'lemek güvenliği
   batch'lemek olur.**

Toplam potansiyel: mevcut 0.652 ms/prove üzerinden hepsi birleşse ~0.45–0.50
ms, yani prove başına ~1.3–1.45×. Ama kalan kazancın tümü, projenin şu an sahip
olmadığı bir incelemeyi gerektirir — ve bu dosya, o inceleme geldiğinde
yapılacaklar için ölçümlü bir başlangıç noktasıdır.
