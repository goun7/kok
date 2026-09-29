# Reg CA Yorum Taslağı — *Regulation Crypto Assets* (91 FR 54510)

**DURUM: TASLAK. DOSYALANMADI.** Bu dosya, proje sahibinin vermemiş olduğu bir karar
için hazırlıktır. Hiçbir şey hiçbir yere gönderilmedi ve projenin iletişim
kısıtlamaları olmadıkça gönderilmeyecek. Bu dosyanın üstündeki "TASLAK" ve
"GÖNDERİLMEDİ" ifadeleri, dosyalama kararından önce ve sonra doğrudur.

**Bu dosyanın sahibi: değil.** Aşağıdaki yorum metnini projenin tasarımcıları
yazdı; proje avukatı değildir ve hiçbir hukuki görüş veremez. Metin, gönderilmeden
önce mutlaka okunmalı; eğer gönderilirse, gönderilmeden önce mutlaka bir hukuk
danışmanı tarafından okunmalıdır (bkz. §6 ve §7).

---

## 0. Takvim ve docket (her şeyin önündeki gerçek)

| Alan | Değer |
|---|---|
| Kural | **Regulation Crypto Assets** (teklif — öneri, kesinleşmedi) |
| Federal Register atıfı | **91 FR 54510** (91 FR 54510–54655, 146 sayfa) |
| Belge numarası | 2026-17183 |
| Docket | Release Nos. **33-11434; 34-106150**; File No. **S7-2026-27** |
| RIN | **3235-AN38** |
| Yayımlanma | 21 Ağustos 2026 |
| **Yorum kapanış** | **20 Ekim 2026** — "Comments should be received on or before October 20, 2026" |
| Bu dosyanın tarihi | **29 Eylül 2026 — 21 gün kaldı** |
| Nereye yorum | `regulations.gov` üzerinden File No. S7-2026-27 docketi (**kullanmadan önce doğrula**) |

**Takvim neden önce:** 20 Ekim'den önce dosyalanan bir yorum Komisyon tarafından
okunur; sonrasında dosyalanan bir yorum rulemaking kaydının parçası olmaz. Bu dosya
yalnızca hazırlıktır ve değeri o tarihte sıfıra iner — yukarıdaki her "açık" ifadesi
21 Ekim'de tarihsel hale gelir ve **Federal Register API'sinden yeniden doğrulanmadan
kullanılamaz** (`/api/v1/documents/2026-17183.json`; HTML sayfa bot challenge verir).

---

## 1. "Reg CA" nedir — ve bu tasarımı ilgilendiren TEK soru

"Reg CA", projenin hazırlık dosyasında ve kağıdında (§9.2) **"Regulation Crypto
Assets"** olarak kaydedilmiş, 21 Ağustos 2026'da önerilen bir SEC kural teklifidir.
Bir yorum süreci olduğunu söyleyen de budur: **20 Ekim 2026'ya kadar açık**.

Teklifin bu tasarımı ilgilendiren iki parçası var:

1. **İki arz muafiyeti** (Securities Act §5'ten): 4 yıllık dönemde **$5M'a kadar**
   ve her 12 ayda **$75M'a kadar** (büyük tier finansal tablo + sürekli raporlama
   gerektirir).
2. **Koşullu güvenli liman** (Subpart D, **Rule 400**): koşullar sağlanırsa kripto
   varlık "investment contract" sayılmaz. Geçiş mekanizması **Form TR**'dir
   (Rule 400(b)) — bir **issuer**'ın EDGAR'a dosyaladığı geçiş raporu.

**Soru:** Rule 400 ve Form TR'in her ikisi de bir **issuer** tarafından yerine
getirilir. **Fair-launch, no-premine, entity'siz bir ağın issuer'ı yoktur.** Satış
yok, vaat yok, promoter yok, Form TR dosyalayacak kimse yok ve formun
tanımlayabileceği kimse yok. Ağ madencilikle başlatılır; token'ın ilk dağıtımı
alıcılara satış değil, madencillere emisyon şeklindedir.

**Bu bir tasarım kusuru değil, teklifin kendi çerçevesinin gerçek bir boşluğudur.**
Teklifin kendi analizi (§II.A.4.b.i) ağın fonksiyonel hale gelmesini ve değerin
**programatik işleyişten** gelmesini tanımlar — ama o geçişi işaretlemek için
sağladığı mekanizmaların hepsi issuer'ın hareket etmesini gerektirir. Issuer'ı
olmayan bir ağın mekanizmanın bir ajanı yoktur.

---

## 2. Analiz — "issuer" kimdir ve PoUW madenciliği issuer faaliyeti midir?

Teklifin §II.A.4.b.i'ından birebir (kaynak: `KOK_V2_PAPER.md` §9.2, provenansı
`arastirma/federal_register_yorum_analizi.md`'de):

> "once an issuer has satisfied its representations or promises to engage in
> essential managerial efforts under the covered investment contract, the
> associated crypto network or associated crypto application **may be
> functional**. Once such network or application is functional, it is our view
> that services to **secure, maintain, improve, or enhance** such a network or
> application or its functionality… **would not constitute essential managerial
> efforts**. … rather than deriving its value from the essential managerial
> efforts of the issuer, the relevant crypto asset **should derive its value from
> the programmatic operation of the associated crypto network**…"

> "the activities of and contributions made by many parties (including, for
> example, the issuer, other developers, **validators and/or miners**, liquidity
> providers, users, and holders of the crypto asset) would affect the failure or
> success of the associated crypto network…"

### Faaliyet tablosu — her satır kendi sınırıyla

| Bu tasarımdaki faaliyet | "Essential managerial effort" mı? | Gerekçe |
|---|---|---|
| Protokolü tasarlayıp kağıdı yayımlamak | **Hayır — ve bu dürüst zor vaka.** | Geliştirme, tanımlanabilir insanlar tarafından gerçek bir emektir. Ama teklifin §II.A.4.b.i analizi tam bunu ele alır: ağ fonksiyonel olduktan sonra "secure, maintain, improve, enhance" hizmetleri essential managerial effort değildir. Geliştirme fonksiyonellikten önce gelir; testin ölçtüğü şey değil, testin işlediği önşarttır. **Dürüst sınır: bu argüman yalnızca ağ fonksiyonel olduktan sonra geçerlidir ve bu ağ fonksiyonel değildir.** |
| G-layer blok madenciliği (MatMul PoW) | **Hayır — teklif bunu adlandırıyor.** | §II.A.4.b.i "**validators and/or miners**"ı ağın başarısını etkileyen taraflar arasında sayar ve fonksiyonel bir ağı güvenli kılmanın essential managerial effort olmadığını belirtir. Bu, teklifin bu tasarımın G katmanı hakkında verebileceği en yakın doğrudan yanıttır. |
| Node çalıştırmak, blok doğrulamak, konsensusu uygulamak | **Hayır** | Aynı hüküm: fonksiyonel bir ağı güvenli kılmak ve sürdürmek. |
| Takımın bir görev piyasası operasyonu | **Evet, olabilir — ve tasarımın saygı gösterdiği asimetri budur.** | Proje U-layer piyasasını bir işletme olarak operasyonel hale getirirse, bu tanımlanabilir bir taraf tarafından yerine getirilen bir hizmettir. **Bu yüzden tasarım protokol ile uygulamayı ayırır** (kağıt §9): protokol açık kaynaktır; bir gün işletilirse pazar ayrı bir varlıktır ve sıradan işletme düzenlemesine tabidir. |
| Gelecekteki değer hakkında vaat | **Evet, kesin olarak.** | Token'ın değerleneceği veya emeklerin süreceği yönünde herhangi bir beyan, Howey'in çekirdek olgu örüntüsüdür. Bu tasarım hiçbiri yapmaz ve yokluğu bir tasarım özelliğidir. |

**Sonucu, iddia ve sınır olarak:** Madencilik ve konsensus katılımı — teklifin kendi
metnine göre — fonksiyonel bir ağda essential managerial effort değildir; dolayısıyla
madencilikle dağıtılan bir fair-launch token, satışla finanse edilen bir tokendan
daha çok teklifin commodity çerçevesine yakın durur. **Sınırı:** bu ağ **fonksiyonel
değildir**, kağıt bir pre-testnet tasarım belgesidir ve "fonksiyonel" yalnızca canlı
bir zincirin iddia edebileceği bir statüdür. Bu analiz bir gelecek durum hakkında
tasarım argümanıdır ve kendini öyle tanımlar.

### Neden bu bir istisna talebi değil

"Hiç issuer'ı olmayan bir ağ için Form TR'yi kim dosyalar?" sorusu, Komisyon'un kendi
çerçevesinin doğal bir sonucudur ve bu tasarımın yönünde yanıtlanması teklifin kendi
belirttiği mantığa **tutarlıdır**, ona zıt değildir. İki okuma mümkündür:

- **Okuma A (aleyhte):** issuer yok demek, güvenli limanın basitçe kullanılamaz
  olması ve "fonksiyonel ağ" analizinin hiç uygulanmaması demektir. Bu tür ağları
  2026 öncesi durumda, bir çıkış rampası olmadan bırakır.
- **Okuma B (leyhte):** hiç issuer'ı olmamış bir ağda, sonlandırulacak bir "covered
  investment contract" hiç var olmamıştır. §II.A.4.b.i mantığı — değer programatik
  işleyişten, essential managerial effort'tan değil — bir **geçişle değil, önşartın
  yokluğuyla** uygulanır. Hiçbir şey sona ermez, çünkü hiçbir şey yaratılmamıştır.

**Bu tasarım Okuma B'yi ileri sürer ve bunun bir hüküm değil bir argüman olduğunu
açıkça söyler.** Teklif iki okuma arasında sessizdir ve sessizlik, bir yorumun
Komisyondan dürüstçe isteyebileceği tek şeydir. Yapmaması gereken, Okuma B'nin
benimsendiğini iddia etmektir — benimsenmedi; kural tekliftür ve bir teklif geri
çekilebilir, daraltılabilir veya yeniden yazılabilir.

---

## 3. YORUM TASLAĞI (İngilizce — dosyalanacak metin)

**Bu metin ne.** Dosyalanabilir bir yorum taslağı. Dosyalanmadı. Talepler dar,
gerekçeleme teklifin kendi metnidir ve hiçbir iddia metnin ötesine geçmez. Sahip
dosyalamaya karar verirse, önce bir hukuk danışmanı tarafından okunmalıdır — bu bir
tasarım belgesidir, hukuk belgesi değildir ve projenin avukatı yoktur.

**Kasıtlı seçilen ton.** Komisyon talep eden yorumlar da alır, soran yorumlar da.
Bu taslak sorar, çünkü talepler teklifte gerçekten açık sorulardan ziyade
şikayetler değildir; pre-testnet bir projenin yanıtı zaten bildiğini iddia etmesi,
Komisyon'un kendi çerçevesinin yarattığı bir boşluğu belirleyen bir projeden daha az
inandırıcı olurdu.

> **Re: Regulation Crypto Assets, File No. S7-2026-27, RIN 3235-AN38**
> *(Comment draft — NOT FILED. Prepared 29 September 2026.)*
>
> The Commission's proposal addresses a question this project has spent
> considerable time on: how the Howey analysis treats a crypto asset whose
> network is functional, and where its value comes from. We write not to
> object but to identify a gap the proposal's own framework creates, and to
> ask the Commission to address it.
>
> We design a proof-of-useful-work layer-1. Its distinguishing structural
> choice is that **no party ever offered the asset for sale**. The asset is
> distributed by mining from genesis, with no premine, no investor round, and
> no entity that collected capital against promises of effort. The network's
> security budget comes from mining alone.
>
> The proposal's §II.A.4.b.i analysis holds that once a network is functional,
> services to "secure, maintain, improve, or enhance" it "would not constitute
> essential managerial efforts," and that the asset "should derive its value
> from the programmatic operation of the associated crypto network," with
> "validators and/or miners" named among the parties whose activities affect
> its success. We share that analysis, and our architecture is built to satisfy
> it: our consensus participants perform exactly the securing and maintaining
> the analysis describes, and nothing else.
>
> We make the architecture concrete, because a design claim is easier to
> evaluate than an adjective. The chain is a two-layer composition. A
> **security layer** selects and orders blocks on a proof-of-useful-work
> certificate over matrix multiplication, whose hardness is structural rather
> than chosen by the miner: the noise matrices are derived from a public
> context value, so a miner cannot present a puzzle instance it finds
> favourable. A **service layer** carries fee-paid verifiable-compute tasks and
> is assigned to miners by a verifiable random function over an epoch seed
> fixed 64 blocks in the past. That service layer carries **exactly zero
> consensus weight**: it cannot influence leader election, by the structure of
> the block type, by the type of the functions that compute weight, and by a
> test that a block carrying many high-fee service proofs has the same
> blockscore as the identical block carrying none. The purpose of that
> separation is that an attacker cannot purchase security by purchasing demand
> for the useful work. A mining certificate is bound to the commissioned task
> and to the matrices actually multiplied, signed under a self-resolving
> decentralized identifier, so that who performed the work and what work was
> performed are part of the proof rather than fields a relayer may rewrite;
> the receipt recomputes with a hash function alone, with no secrets, no
> server and no chain-specific software installed.
>
> **The gap.** The mechanisms the proposal provides to mark the point at which
> a network becomes functional — Rule 400's cessation of a covered investment
> contract, and the Form TR filing in Rule 400(b) — are each performed by an
> **issuer**. A network that distributed its asset solely by mining has no
> issuer: no party made a representation, no party owes essential managerial
> efforts, and no party exists to file a transition report. The proposal does
> not address whether such a network is outside the framework entirely, or
> inside it with nothing to terminate.
>
> We ask the Commission to consider two questions, and we offer no answer to
> either:
>
> 1. Where a crypto network has no issuer because its asset was never sold —
>    only mined — does the Commission regard the network as outside the
>    framework the proposal establishes, or as a network in which no covered
>    investment contract ever arose, such that there is nothing to which
>    cessation could apply?
>
> 2. If the latter, would the Commission consider stating, in the adopting
>    release or in guidance, that the absence of a sale is a fact bearing on
>    the Howey analysis in the same direction the proposal already recognises
>    for functional networks — rather than leaving no-issuer networks to infer
>    it?
>
> We raise this because the omission is not hypothetical for our design, and
> because we believe it is resolvable within the proposal's own logic. We do
> **not** ask the Commission to adopt any particular position on our asset, to
> treat this comment as a ruling, or to exempt proof-of-work distribution from
> the analysis the proposal applies to all crypto assets. The distinction we
> draw is structural — the absence of a sale — not technological, and it is
> available to any network with the same structure regardless of its work
> function.
>
> Two limits we state plainly. First, our network is **not yet
> functional**; it is a pre-testnet design with a specification, prototypes and
> a measured prototype path, not a running chain. The "functional network"
> analysis we reference is one we aspire to satisfy and cannot yet claim to.
> Second, this comment is submitted by the project's designers, not by counsel;
> the legal question is one we have identified but are not competent to answer.

### Taslağın bilinçli yapmadığı üç şey

1. **Güvenli limanın bu tasarıma uygulandığını iddia etmez.** İddia edemez: Rule 400
   bir sözleşmeyi sonlandırır, bu tasarımın tezi ise hiç sözleşme olmadığıdır. Limanı
   iddia etmek, tasarımın kendi konumuyla çelişirdi.
2. **PoUW'nin hukuki olarak özel olduğunu savunmaz.** Çizilen ayrım **satışın
   yokluğu**dur ve bu, madencilikle dağıtılan her varlıkta vardır. Argümanı
   teknolojik yapmak, onu bu projeye daraltır ve zayıflatır.
3. **Muafiyet istemez.** Bir *açıklama* ister. Tek bir proje için muafiyet talebi
   yozlaştırıcı bir istektir; çerçevenin netleştirilmesi meşru bir istektir ve boşluğun
   desteklediği istek budur.

---

## 4. KOD KANITLARI — taslakta anlatılan mimarinin gerçek karşılığı

**Bu bölüm neden var.** §3'teki her mimari iddiası, bu depoda karşılığı olan bir
şeydir. Aşağıdaki referansların her biri bu oturumda çalıştırılarak/okunarak
doğrulandı; uydurulmadı. **Dikkat:** kanıtlar mimarinin *inşa edildiğini* gösterir;
ağın fonksiyonel olduğunu, güvenli olduğunu veya yasal bir konum olduğunu
**göstermez** — bu üçü ayrı şeydir ve aşağıda karıştırılmaz.

### 4.1 Workspace — 16 crate, hiçbiri "şirket" değil

`cargo test --workspace --all-targets` → **262 passed, 0 failed, rc=0** (26 test
binary'si; son commit'teki 240'ın üzerine, working tree'deki yeni `kok-proof` katmanı
19 ve `kok` CLI binary'si 3 test ekledi; hiçbir mevcut test değişmedi).

| Crate | Rolü | Test |
|---|---|---|
| `kok-poum` | **G katmanı** — MatMul PoUW sertifikası (KW-Kernel) | 39 |
| `kok-ghostdag` | G katmanı blok sıralaması (GHOSTDAG) | 28 |
| `kok-consensus` | İki katmanın kompozisyonu — ayrılığın ölçüldüğü yer | 5 |
| `kok-u-layer` | **U katmanı** — fee ücretli doğrulanabilir-hesap piyasası + VRF ataması | 40 |
| `kok-ledger` | U katmanı escrow muhasebesi | 15 |
| `kok-fri` | F0b FRI — yinelemeli düşük-derece testi (toy, q=97) | 36 |
| `kok-pvi` | Proof Verifier Interface — hafif istemci sınırı | 7 |
| `kok-wasm` | WASM doğrulayıcı sınırı (tuzak-free) | 11 |
| `kok-proof` | **Kanıt katmanı** — did:key imzalı, yeniden-hesaplanır makbuz (yeni) | 19 |
| `kok-net`, `kok-mempool`, `kok-chain`, `kok-ffi`, `kok-probes`, `kok-bench`, `kok-cli` | Relay, havuz, zincir seçimi, C ABI, adversarial regresyon probları, benchmark, CLI | 19+10+7+4+19+3 |

### 4.2 "Faydalı işin konsensus ağırlığı sıfırdır" — üç katmanlı savunma

`crates/kok-consensus/src/lib.rs` ayrılığı üç şekilde uygular ve bunları dosyalar:

1. **Yapısal (structural).** GHOSTDAG `Block` tipinin U proof'ları için bir alanı
   **yok**. Ağırlığı hesaplayan graf, göremediği şeye danışamaz. Bir çağıran U
   proof'unu ağırlık hesabına geçemez, çünkü tipin koyacak yeri yoktur.
2. **Tipte (typal).** `kok-u-layer/src/lib.rs:112` —
   `u_task_consensus_weight(_proof: &TaskProof) -> u64` her zaman `0` döner;
   `reward_split` ve `select` imzaları hiç U argümanı almaz — "bu U proof'unu
   ağırlıklandır" imzada ifade edilemez.
3. **Ölçülen (measured).** Çok sayıda yüksek-fee'li U proof'u taşıyan bir blokla
   hiç taşımayan özdeş blok aynı `blue_score` ve aynı `pay_set`'e sahiptir. Bu, bir
   kişi U'yu ağırlık hesabına bağladığı an başarısız olacak testtir.

Bu, §3'te "an attacker cannot purchase security by purchasing demand" cümlesinin
koddaki karşılığıdır ve **neden-okulunun** bir ifadesidir: güvenlik ile fayda
ayrılır, böylece fayda satın alınarak güvenlik satın alınamaz.

### 4.3 Madencilik sertifikası — "güvenli iş" ile "suni iş" arasındaki fark

`crates/kok-poum/src/lib.rs` (KW-Kernel, `KOK_V2_PAPER.md` §B'den port):

- **Sertlik yapısaldır:** `noise(ctx, n)` gürültü matrislerini (E, F) public `ctx`'den
  türetir (`crates/kok-poum/src/lib.rs:153`), bu yüzden adversary dostu bir örnek
  **seçemez**. Bu, saf Freivalds'ın eksik olduğu özelliktir (A=0 saldırısı, kağıt
  satır 253) ve KW'nin seçilme nedenidir.
- **Doğrulama, iddianın hash'i değil, işin kendisidir:** `KwKernel::verify`
  iddia edilen koordinatlarda strided accumulator'ı **yeniden hesapler** ve zorluk
  hedefini kontrol eder.
- **Ölçülen performans:** prove 3.47 ms / verify 0.25 ms (q=97, n=8, target 2^1;
  Python protoptipinden, `g_layer_tests_en.py`, rounds 1–6).

### 4.4 Kanıt katmanı — "kim, ne için" bulmacanın parçasıdır

`crates/kok-proof/src/lib.rs` (bu working tree'de yeni) — akademik gerekçesi
SNARKChain'dir (arXiv 2510.09729): önceki PoUW önerileri "zincirin bütünlüğünü ve
madencinin kimliğini bulmaca çözümlerine gömeyi" başaramaz; Pearl'in cuPOW
ölçümü (arXiv 2606.04819) aynı kusuru ampirik olarak gösterir — doğrulaması
"tasarım gereği rastgele matrisleri kabul eden" bir ağ sıfır faydalı hesaplama yapar.

Katmanın kapanış noktası (kaynak dosyasının kendi sözleriyle): sertifika
görevlendirilen programa ve girdi matrislerine bağlanır ve commitment'lar
**doğrulayıcı tarafından belgenin kendi içeriğinden yeniden hesaplanır** (asla
güvenle alınmaz); MatMul parçası `KwKernel::verify` tarafından **yeniden türetilir**;
madenci kendi-kendine-çözülen bir `did:key` ile tanımlanır ve belge Ed25519 ile
imzalanır; makbuz önceki kanıta zincirlenmiş bir sha256 hash'tir ve **yalnızca
sha256 ile** üçüncü bir taraf tarafından yeniden hesaplanabilir — hiçbir sır, sunucu
 veya KÖK kurulumu gerekmez.

**Canlı doğrulama (bu oturumda çalıştırıldı):**

```
$ kok create --ctx 20261020 --target 2
kok: mining G-layer kanıt (q=97 n=8 r=2, ctx=20261020, target=2^2)
kok: miner did        : did:key:z6MkqwPYkYaP8v26QVXZpLMFR8A2iCv8BpyEgGCKUKRTFhkE
kok: tile (i=0, j=2) value=47 at nonce 1 — mined in 1.8 ms
kok: wrote kanit.json (receipt 91682292c801f83b)

$ kok verify kanit.json
KABUL  kanit.json  (did did:key:z6MkqwPYkYaP8v26QVXZpLMF…, receipt 91682292c801f…, tile (0,2) = 47)
```

`verify` yolu, üçüncü bir tarafın çağıracağı kodun aynısıdır: hiçbir sır okumaz,
ağa bağlanmaz ve bağımsız bir makinede (sadece sha256 + Ed25519 ile) aynı sonucu
verir. §3'teki cümlenin somut karşılığı budur.

### 4.5 VRF ataması — kimin hangi görevi çalışabileceği

`crates/kok-u-layer/src/assign.rs`: her görev için madenci, 64 blok geride sabitlenmiş
epoch seed'i üzerinden (seed, tid) için ECVRF değerlendirir; çıktı eşiğin altına
düşerse görev o madenciye atanır. Kapı **integer-exact**tir (üst 64 bit, kayan
nokta değil — konsensus güvenliği için). Madenci görevini seçemez: atananı kabul
eder veya bonunu kaybeder.

**Dürüst sınır, kodun kendisinde yazılı (gizlenmedi):** madenci VRF'yi **kendi
anahtarıyla** değerlendirir ve splitting one stake across N registered keys, bağımsız
çekiliş sayısını N ile çarpar — tek bir kimlik N bilet alır. VRF bunu düzeltmez:
her çekilişi doğrulanabilir yapar, çekiliş sayısını dürüst yapmaz. Düzeltmek
kayıt (registration) katmanında bir-bonded-kimlik-bir-anahtar gerektirir (bu crate'in
kapsamı dışında) ve ilgili test çoklayıcıyı **ölçer**, yok saymaz
(`assign::tests::splitting_one_stake_into_two_keys_doubles_the_draws`).

### 4.6 Ekonomik parametreler (gerçek değerleriyle)

- `C_FEE = 500` (`kok-u-layer/src/lib.rs:43`) — anti-aggregation fee cap'ı; küçük
  görevleri paketleyip fee piyasasını seyreltme teşvikini sınırlar (Bar-On vd.,
  arXiv 2505.21685'nin denge davranışı).
- `EPOCH_LOOKBACK = 64` — seed 64 blok geride sabit; `MAX_BURN_RATE = 500` —
  burn, bir tedarik-azaltma vaadi değil, bir **protokol fee politikası** olarak
  konumlandırılır (Demirel, ePrint 2026/1492: "geri alınamaz vergi = güvenlik kaynağı").

---

## 5. Kağıdın konumuyla çelişme — göndermeden önce kontrol listesi

Eğer bir yorum dosyalanırsa, kağıdın desteklemediği hiçbir şey iddia edemez.
`KOK_V2_PAPER.md` §9.2–9.3'ün kayıtlı konumu (taslak yukarısı bununla tutarlıdır):

- **§9.2:** teklifin analizi bu mimariyi **bağımsız olarak** tanımlar —
  *corroboration, confirmation değil*. Kural bu tasarım için yazılmadı.
- **§9.2 zayıflama 1:** bu zincir güvenli limanı **kullanamaz**. Rule 400 sona ermeyi
  kodlaştırır; bu tasarımın tezi hiç sözleşme olmadığıdır.
- **§9.2 zayıflama 2:** **Form TR dosyalayacak issuer yok.** Bu, teklifte çözülmemiş
  bir boşluk olarak kaydedildi, tasarımda bir kusur olarak değil.
- **§9.2 zayıflama 3:** **"fonksiyonel" bu tasarımın henüz iddia edemeyeceği bir
  statüdür.**
- **§9.3 madde 3:** "issuer" netleştirmesi tek canlı sorudur ve 20 Ekim 2026'ya kadar
  açık olan yorum dönemi onu canlı yapar.
- **§9.3:** hiçbir hukuk danışmanı görevlendirilmedi. Projedeki her hukuki okuma
  avukat olmayanların okumasıdır.

**Yukarıdaki taslak bu sınırların her birini kendi sözleriyle tekrarlar.** Bunlardan
herhangi biri değişirse yorum da değişmelidir — "güvenli limanı kullanamıyoruz"
itirafını yumuşatan bir yorum, kağıdın kayıtlı konumuyla tutarsız olur ve ikisini de
bulan bir okuyucu haklı olarak nedenini sorar.

---

## 6. Pencerenin aritmetiği — 21 gün (29 Eylül 2026 itibarıyla)

| Günler | Ne olur | Kim |
|---|---|---|
| 1–6 (~5 Ekim) | Taslağı oku, **hiç yorum yapılıp yapılmayacağına** karar ver. Karar, projenin pre-testnetken tasarımını kamuya açık bir düzenleyici konumla ilişkilendirmek isteyip istemediğidir — bu stratejik bir sorundur, taslak sorunu değildir | **İnsan kararı. Devredilemez.** |
| 7–13 (~12 Ekim) | Evetse: hukuk danışmanı incelemesi. Projenin avukatı yok (kağıt §9.3), yani kısa bir yorumun dar bir okunması için bir avukat **bulmak** demektir — bu, tam bir menkul kıymetler görüşünden farklı ve daha ucuz bir görevdir | İnsan + avukat |
| 14–19 (~19 Ekim) | Revize et, regulations.gov'daki docket yolunun doğru olduğunu ve yorumun doğru dosyaya düşeceğini doğrula, dosyala | İnsan |
| 20–21 (20 Ekim) | **Son tarih.** "Received on or before" dosyalandığını ifade eder, taslak hazırlandığını değil | — |

**Gerçekten bir karar olan tek karar.** Dosyalamak, tasarımı düzenleyici bir konum
almış olarak kamu kaydına koyar. Para harcamaz ve geri alınamaz. Projenin mevcut
duruşu — teklifi kağıtta corroboration olarak anıp rulemaking'e katılmamak — meşru bir
seçimdir ve gerekçe gerektirmez. Dosyalamak da meşrudur. Yukarıdaki taslak, hangisi
seçilirse seçilsin işin zaten bitmiş olması için var; tek kısıt saattir.

---

## 7. Bu dosyanın kuralları

- **Buradaki hiçbir şey dosyalanmadı ve proje sahibinin açık kararı olmadan hiçbir şey
  dosyalanmayacak.** Projenin iletişim kısıtlamaları geçerlidir.
- **Hukuki tavsiye değildir.** Bu projenin avukatı yoktur. §2'deki analiz projenin
  yazarları tarafından tasarım analizidir; §3'teki taslak bir taslak alıştırmasıdır.
  İkisi de ancak bir avukat okuduktan sonra başka bir şey olur.
- **Kullanmadan önce tarihi doğrula.** 20 Ekim 2026 kapanış tarihi Federal Register'ın
  kendi API'sinden geldi. O tarih geçtikten sonra bu dosyadaki her "açık" ifadesi
  tarihseldir. Bu dosyadan değil, API'den yeniden doğrula.
- **§II.A.4.b.i dilini bu dosyadan alıntılama.** Birebir alıntılar `KOK_V2_PAPER.md`
  §9.2'de ve `arastirma/federal_register_yorum_analizi.md`'de, provenansı
  kaydedilmiş halde durur. Oradan alıntıla, kaynağın ekli olduğu yerden.
- **Bu dosya skoru hareket ettirmez.** Kod, test veya ölçüm değişmedi. Bu bir insan
  kararı için hazırlıktır ve hazırlığın dürüst hali, hiçbir şey kanıtlamadığıdır.
- **Dosyalamadan önce oku.** Sahibin okuması için yazıldı; sahibi gönderir. Bu
  dosyayı değil, §3'teki metni gönderir.
