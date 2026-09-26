# SEC "Regulation Crypto Assets" — Açık Yorum Dönemi: KÖK'ün Pozisyonu

**Tarih:** 27 Eylül 2026
**Kapanış:** 20 Ekim 2026 — bugün itibariyle **23 gün kaldı**, yorum dönemi
AÇIK.

**Durum notu (dürüst):** Bu dosya bir **iç analizdir**, SEC'ye sunulacak bir
yorum taslağı DEĞİL. Kullanıcı (proje sahibi) onaylamadan hiçbir yorum
gönderilmeyecek — bu projenin mail/iletişim yasaklarının bir parçasıdır.
Dosyanın amacı, teklifin KÖK'ün tasarımına ne kadar dokunduğunu **kendi
dürüst değerlendirmemizle** netleştirmektir; okuyan kişi dosyayı alıp kendi
yorumunu yazabilir.

---

## 1. Teklifin kimliği (birincil, doğrulanmış)

Federal Register'ın **kendi API'sinden** (HTML sayfası bot challenge
verdi, API çalıştı; `documents/2026-17183.json`):

| Alan | Değer |
|---|---|
| Başlık | Regulation Crypto Assets |
| Belge no. | 2026-17183 |
| Yayımlama | 21 Ağustos 2026 |
| Atıf | **91 FR 54510** |
| Tür | **Proposed Rule** (öneri — KESİNLEŞMEDİ) |
| Docket | Release Nos. **33-11434; 34-106150**; File No. **S7-2026-27** |
| RIN | **3235-AN38** |
| Yorum kapanışı | **20 Ekim 2026** ("Comments should be received on or before October 20, 2026") |
| Tam metin | 146 sayfa, `federalregister.gov` + `govinfo.gov` |

**Önkoşul yorumlama:** Teklifin dayanağı **2026 Interpretation**, Release
No. **33-11412** (17 Mart 2026), **91 FR 13714** (23 Mart 2026). Rule 400'ün
"cease to exist" mantığı bu yorumlamadan gelir — yani proposed rule, zaten
yürürlükte olan bir yorumlamayı **kodifiye eder**, sıfırdan yaratmaz.

---

## 2. KÖK'ü doğrudan ilgilendiren iki mekanizma

### 2.1 Two offering exemptions (Subpart B, Rules 101-103)

- **Tier 1:** 4 yıllık dönemde **$5M'a kadar**
- **Tier 2:** her 12 ayda **$75M'a kadar** — finansal tablo + sürekli
  raporlama gerektirir
- Her ikisi de antifraud/antimanipulation hükümlerine **tabi kalır**

**KÖK ile ilişkisi — DÜRÜST DEĞERLENDİRME: ILGISIZ, ve bu önemli.** Bu
muafiyetler **ihraç (issuance)** içindir: bir şirket token satarak sermaye
topladığında kayıttan muaf olmasını sağlar. KÖK'ün tasarımı **fair-launch,
no-premine** — hiçbir kuruluş token satışından sermaye toplamaz. Bu nedenle:

- KÖK **bu muafiyetleri kullanmaz**, çünkü kullanacak bir ihraç olayı yok
- Ama bu, KÖK'ün "madenciler ödül alır" gerçeğini değiştirmez: madenci
  ödülü, bir **ihraç** değil, protokolün emisyonudur — bu ayrım paper §9'da
  zaten Howey analizi boyunca yapılır
- **Tezimiz:** bu muafiyetlerin KÖK için yararsız olması bir dezavantaj
  DEĞİL; tasarımın "satıştan sermaye toplama yok" posterunun **kanıtıdır**

### 2.2 Investment contract safe harbor (Subpart D, Rule 400) — BURASI KRİTİK

Rule 400 iki koşulda "covered investment contract"in **sona erdiğini**
sayar:

1. **(a)** ihraççı, temsil ettiği tüm **essential managerial efforts**'ı
   tamamlamış veya kalıcı olarak durdurmuş olmalı + yeni temsil/vaat
   yapmamalı
2. **(b)** EDGAR'da **Form TR** ("transition report") dosyalamalı

Ve 2026 Interpretation (33-11412, 13722-23) gereği sözleşme şunlardan
birinde sona erer: (1) ihraççı vaatlerini yerine getirmiş, veya (2) alıcı
ihraççının çabaları sürdüreceğine makul olarak beklemiyor.

---

## 3. ★ EN DEĞERLİ BULGU — SEC'nin kendi ağacı KÖK'ün ağacıdır

Teklifin tam metninden (§II.A.4.b.i, sayfa 54553 civarı), **verbatim**:

> "once an issuer has satisfied its representations or promises to engage in
> essential managerial efforts under the covered investment contract, the
> associated crypto network or associated crypto application **may be
> functional**. Once such network or application is functional, it is our
> view that services to secure, maintain, improve, or enhance such a
> network or application or its functionality, or to facilitate network
> effects… **would not constitute essential managerial efforts**. As a
> result, any representations or promises… to provide or continue to
> provide or arrange for the provision of such services after the network
> or application is functional **would not satisfy the Howey test**."

> "rather than deriving its value from the essential managerial efforts of
> the issuer, the relevant crypto asset should derive its value from the
> **programmatic operation of the associated crypto network**…, as well as
> the market's supply and demand dynamics"

> "the activities of and contributions made by many parties (including, for
> example, the issuer, other developers, **validators and/or miners**,
> liquidity providers, users, and holders of the crypto asset) would affect
> the failure or success of the associated crypto network"

### Bu neden KÖK için bu kadar değerli?

**SEC, KÖK'ün mimarisinin iki katmanını kendi kelimeleriyle tanımlıyor:**

1. **G layer = "secure, maintain" ağı hizmetleri** — SEC bunları
   "essential managerial efforts" saymıyor, **fonksiyonel ağda**
2. **U layer = "programmatic operation"** — değer çabanın bireyinden değil,
   ağın programatik işleyişinden gelmeli

Yani SEC'nin testi: **ağ fonksiyonel mi?** Fonksiyonelse, madencilerin
(kök için: G-layer MatMul PoW'yu yürütenler) çabaları "managerial effort"
değildir, ve bu **kendi ağacımızı birebir karşılar**.

**KÖK'ün Howey tezi (paper §9) şuydu:** token bir hizmet için ücrettir,
kâr beklentisi bir promoter'ın çabasından gelmez. SEC'nin proposed rule'ı
bu teze **bağımsız bir yanıt verir**: fonksiyonel ağda value, managerial
effort değil programmatic operation'dan gelmeli — bu KÖK'ün U-layer'ının
tam tanımıdır.

### Ama düzeltmemiz gereken bir nüans (dürüst)

KÖK bu safe harbor'u **kullanamaz**, ve nedenini bilmek önemlidir:

- Safe harbor bir **covered investment contract'in sona erdiği** noktadır
- Yani: geçmişte bir investment contract VARDI, ama artık yok
- KÖK tezi "başından beri investment contract YOK" — bu farklı bir argüman
- Safe harbor, KÖK'ün tezini **doğrular** ama KÖK tarafından
  **kullanılmaz**: "sona erdi" demek, "hiç olmadı" demek değil
- **Paper'da doğru olarak:** safe harbor KÖK'ün var olduğu bir durumu
  kapsamıyor olabilir, ama testin mantığı ("programmatic operation"
  vs "managerial effort") KÖK'ün tezine **paralel bir onay** sağlar

---

## 4. Dürüst zayıflatma — teklif KÖK'ü TAMAMEN korumuyor

1. **Teklif, tekliftir.** 20 Ekim'den sonra Commission yorumları
   değerlendirir; nihai kural aylar/senaryo olarak belirsiz sürede sonra
   yayımlanır. **Geri çekilebilir, daraltılabilir, genişletilebilir.**
2. **"Issuer" kavramı KÖK'de kim?** Safe harbor Form TR dosyalamayı
   gerektirir ve bir "issuer" ister. KÖK **fair-launch, no-premine** bir
   tasarım olduğundan, bir ihraççı yoktur ki Form TR dosyalasın. Bu
   **pratik bir boşluk**: safe harbor'un teorik onayına rağmen,
   işleyişi kimin üstleneceği belirsizdir. Dürüst cevap: **bu boşluk
   çözülmemiştir** — permissionless bir ağ için "issuer" kim sorusunun
   SEC tarafından henüz yanıtlanmadığını kaydederiz.
3. **Antifraud her şeye tabi.** Muafiyetler "investment contract"
   sorununu çözer; dolandırıcılık, piyasa manipülasyonu veya kayıt dışı
   takas yine yasaktır. KÖK'ün dürüst operasyonu bu başlıkta bir
   muafiyet beklemez.
4. **Torres'ten gelen gerçek (paper §9):** kurumsal satışlar üzerindeki
   injunction **anlaşmayla kaldırılamaz**. SEC'nin teklifi bunu değiştirmez
   — Torres, "taraflar anlaşıp mahkeme emrini bozamaz" dedi; SEC bir
   kural teklif ediyor, mahkeme kararını değiştirmiyor.
5. **KÖK'de "fonksiyonel" ne demek?** SEC'nin testi ağın **fonksiyonel**
   olmasına dayanır. KÖK daha mainnet'te DEĞİL — bu analiz, paper'ın
   prototip aşamasında olduğunu unutmaz. "Fonksiyonel" statü, ancak
   ağ çalışırken ileri sürülebilir; bugün **tasarım argümanıdır**.

---

## 5. KÖK'ün pozisyonu (netleştirme)

**Tek cümleyle:** Teorik olarak onaylayıcı, pratikte kullanılmayan, ve
hiçbir koşulda dayanılacak bir argüman değildir.

**Paper'ın ne yapacağı (§9.1'de zaten yatıyor):** Teklifi **gelişme olarak**
kaydeder, **temel olarak dayanmaz**. Howey analizi kendi başına durur;
safe harbor bağımsız bir yol olur ama var olmayan bir kurala
güvenilmez. Aşağıdaki üç nokta paper'da zaten doğru şekilde duruyor — bu
dosya sadece arka planı derinleştirir:

- **§9.1 FAQ**: "if the conditions are satisfied, the conclusion follows by
  rule" — ama "nothing in the proposal has been adopted"
- **§9.1**: "the Howey argument stands on its own analysis and the safe
  harbor is recorded as a development that could simplify, not establish,
  the conclusion"
- **§9.1**: "a proposed rule can be withdrawn or narrowed"

**Yorum dönemine katkı olarak ne yapılabilir?** DİKKAT — bu bir öneri
değildir, kullanıcı onayı olmadan hiçbir şey gönderilmez. Ama KÖK'ün
olarak öne sürebileceği dürüst nokta şudur: **"issuer" tanımının
permissionless ağlarda netleştirilmesi** — Rule 400(b) Form TR
dosyalamayı bir ihraççıya bağlar, ama hiçbir ihraççısı olmayan bir ağ
için bu boşluk kalır. Bu, projenin çıkarına **teorik olarak onaylayıcı**
bir konudur ve dürüst bir yorumda ileri sürülebilir.

---

## 6. Önemli NOT: bu dosyayı kullanma kuralları

- **Mail/iletişim yasak.** Bu dosya iç analizdir; kullanıcı açıkça
  onaylamadan SEC'ye veya herhangi bir yere gönderilmez
- **Tarih sınırı:** 20 Ekim 2026'dan sonra bu dosyanın "yorum dönemi
  açık" bölümleri **tarihi hale gelir** — kullanılmadan önce
  `federalregister.gov` API'sinden güncel durum teyit edilmelidir
- **Doğrulama yöntemi:** federalregister.gov **HTML sayfası bot
  challenge verir** (302 → unblock.federalregister.gov). Doğru yol
  `https://www.federalregister.gov/api/v1/documents/2026-17183.json`
  API'sidir — programatik erişim için resmi olarak yönlendirilen yol budur

---

## 7. Kaynak durumu

| Kaynak | Tür | Durum |
|---|---|---|
| 91 FR 54510 (proposed rule) | BİRİNCİL | Doğrulandı (API + tam metin, 13.701 satır) |
| 2026 Interpretation 33-11412, 91 FR 13714 | BİRİNCİL | Atıf olarak teyit edildi (tam metin bu oturumda okunmadı — düz sınırlama) |
| KÖK_V2_PAPER §9, §9.1 | İkincil (proje) | Güncel; bu analizle tutarlı |
| Torres Doc 874/989 | BİRİNCİL | 27.09.2026 tam metin (hukuk_howey_mica.md §1, §6) |
