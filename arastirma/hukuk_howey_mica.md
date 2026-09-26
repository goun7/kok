# HUKUK / UYUM ARAŞTIRMASI — KÖK v2: Howey, MiCA ve Yargı Karşılaştırması

**Hazırlayan:** TAMGA (dış araştırma ajanı) — v2, 20 Eylül 2026 (v1: Lead, 21 Eylül 2026)
**Kapsam:** KÖK v2 token modeli — (i) madencilere blok ödülü (fair-launch PoW), (ii) GÖREV
PAZARI: kullanıcı fee öder → ESCROW → bir kısmı BURN (geri alınamaz), (iii) token ile
ödenebilir verifiable-compute (AI inference).
**Yöntem:** Her iddia için **(a) verbatim alıntı + (b) URL + (c) tarih**. Ulaşılamayan her
veri **BULUNAMADI**. Tahmin (forecast) ile gerçek (actual) ayrımı her yerde belirtilmiştir.
**v2'nin v1'e farkı:** v1'de Ripple ve yargı bölümleri Wikipedia özetlerine dayanıyordu ve
SEC/ABD bölümü BULUNAMADI idi. **v2, tamamen birincil kaynaklarla (SEC litigation
releaseleri, 68 sayfalık SEC yorum release'i, Atkins konuşmaları, Federal Register teklif
metni, FINMA ICO Guidelines PDF'i, Singapur PSA konsolide metni, EUR-Lex MiCA tam metni)
yazılmıştır.**

> **UYARI:** Bu belge hukuki tavsiye değildir; mühendislik/strateji kararları için
> derlenmiş birincil kaynak araştırmasıdır. Testnet öncesi anonim proje kararlarında
> lisanslı hukuk danışmanına başvurulmalıdır (bkz. §7).

---

## 0. YÖNETİCİ ÖZETİ — KÖK v2 için başlıca bulgular

1. **ABD — PoW madencilik blok ödülleri menkul kıymet işlemi DEĞİLDİR.** SEC'in 17 Mart 2026
   tarihli Yorum Release No. 33-11412'si açıkça der ki: "Protocol Mining Activities ... **do
   not involve the offer and sale of a security**". KÖK Layer G'nin blok ödülleri bu
   yorumun kapsamındadır — **şu önkoşulla:** KOK tokeni bir **"digital commodity"** olarak
   sınıflandırılabilir olmalıdır (fungible + utility + arz-talep değeri + çalışan sistem).
2. **ABD — KOK için doğru kategori "digital commodity", "digital tool" DEĞİL.** SEC'nin
   "digital tool" tanımı **non-transferrable / "soul-bound"** örneklerle (ENS isimleri, bilet
   NFT'leri) verilir. KOK transfer edilebilir ve ikincil piyasada işlem görecek; o yüzden
   "digital commodity" kategorisi geçerlidir (bkz. §2.2).
3. **ABD — token menkul kıymet olmasa bile "investment contract" ile satışı menkul kıymet
   olabilir.** Yorum: "**Absent such representations or promises being conveyed to
   purchasers, it would not be reasonable for a purchaser to expect profits**". KÖK'ün
   sıfır-premine / sıfır-VC / anonim-kurucu modeli, "issuer tarafından kâr vaadi" unsurlarını
   mimari olarak zayıflatır — en güçlü savunma hattı budur (bkz. §2.4).
4. **ABD — Ağustos 2026'da RESMİ TEKLIF: "Regulation Crypto Assets"** (FR 21 Ağustos 2026,
   Release 33-11434): startup exemption (4 yılda $5M), fundraising exemption (yıllık $75M),
   ve **investment contract safe harbor** (issuer "essential managerial efforts"i kalıcı
   bıraktığını sertifikalandırırsa token menkul kıymetten çıkar). **Henüz TEKLİF,
   yürürlükte DEĞİL** (bkz. §2.5).
5. **Ripple dava KAPALI; ama "borsa satışı = menkul kıymet değil" EMSAL DEĞİL.** 7 Ağustos
   2025'te taraflar temyizleri ortak stipülasyonla geri çekti; **$125,035,150 ceza ve
   ihtiyati hüküm aynen yürürlükte kaldı** (SEC LR-26369, birincil). Yaygın "$50M ödedi"
   özeti yanıltıcıdır. İkinci Circuit merits kararı vermediği için Torres'in öğretisi
   **bağlayıcı emsal haline gelmemiştir** (bkz. §1).
6. **MiCA — madencilik ödülü whitepaper'dan muaf; AMA borsada listelenme niyeti tüm
   muafiyetleri DÜŞÜRÜR.** Article 4(3)(b): "the crypto-asset is automatically created as a
   reward for the maintenance of the distributed ledger or the validation of transactions"
   → Title II (whitepaper rejimi) uygulanmaz. **Ancak Article 4(4):** offerör herhangi bir
   iletişimde listelenme niyetini belli ederse **bütün muafiyetler düşer**. KÖK için EN
   KRİTİK AB riski (bkz. §3.3).
7. **MiCA — "utility token" tanımında transfer yasağı YOK.** Article 3(9): "'utility token'
   means a type of crypto-asset that is only intended to provide access to a good or a
   service supplied by its issuer". Transfer edilemeyen varlık zaten "crypto-asset" bile
   sayılmaz (Recital 17). KOK transfer edilebilir olduğu için utility-token kategorisinde
   değerlendirilebilir, **ancak** "only intended to provide access" sıfatı ve "supplied by
   **its issuer**" ifadesi fair-launch/issuer'siz modelle gerilimlidir (bkz. §3.2).
8. **MiCA — 2026-09 itibariyle TAM UYGULANIYOR** (30 Aralık 2024'ten beri; ART/EMT
   başlıkları 30 Haziran 2024'ten beri). ~21 aydır yürürlükte (bkz. §3.5).
8b. **★ ESMA rehberi (17 Aralık 2024, BİRİNCİL) — kullanıcının TEMEL sorusuna doğrudan yanıt:**
   "such expectation of a future profit should not in itself be sufficient to qualify a
   crypto-asset as a financial instrument"; bir utility token "should give neither financial
   rights ... nor voting rights". **Yani: kâr beklentisi TEK BAŞINA bir utility token'ı menkul
   kıymet YAPMAZ** — finansal haklar (temettü/faiz/sermaye/oy) gerekir. Ayrıca finansal-aracı
   testi ÖNCE yapılır ("primary focus before considering alternative classifications, such as
   utility tokens") ve "öz, etiketten önce" gelir (bkz. §3.4).
9. **İsviçre — saf utility token için LİSANS GEREKMEZ; AML istisnası KOŞULLU.** FINMA ICO
   Guidelines (16 Şubat 2018): "Utility tokens will not be treated as securities if their
   sole purpose is to confer digital access rights to an application or service..." — AML
   istisnası ancak "provide access rights to a **non-financial** application" ise geçerli.
   KOK'un compute-ödeme işlevi bunu tartışmalı kılar (bkz. §4.1).
10. **Singapur — KOK muhtemelen "digital payment token" (DPT) tanımına girer.** PSA 2019
    tanımı: "is, or is intended to be, a medium of exchange accepted by the public ... as
    payment for goods or services" + "can be transferred, stored or traded electronically".
    **Fakat** lisansa tabi olan **DPT hizmetleridir** (takas/custody); madencilik/ihraç
    lisanslı bir ödeme hizmeti **değildir** (bkz. §4.2).
11. **El Salvador DA ÇÖZÜLDÜ (24 Eylül 2026, BİRİNCİL) — ve sonucu FARKLI:** Decreto N.° 643
    (Ley de Emisión de Activos Digitales, 11 Ocak 2023) dijital varlıkların "títulos valores"
    (menkul kıymet) olmadığını belirtir **AMA** her kamu teklifini CNAD **habilitación**'ına
    (sertifikatör raporuyla) bağlar (Art. 26). KOK transfer edilebilir olduğu için dar Art. 4(c)
    "únicamente" istisnasına girmez. **Net kontrast:** İsviçre/Singapur/ADGM'de lisans
    gerekmezken, El Salvador'da yetkilendirme gerekir. Böylece **1D'nin dört yargısı da tamam**.
     **Hâlâ BULUNAMADI (kalan tek madde):** token burning'in **vergi** açısından
     kesin analizi — **AMA 26 Eylül 2026'da DURUM DEĞİŞTİ.** **IRS birincil
     kaynağı bulundu** (Rev. Rul. 2023-14, IRB 2023-33 + IRS newsroom 04.04.2024):
     "rewards income" IRS'nin resmen adlandırdığı bir gelir kategorisidir ve
     ödülün FMV'si **"dominion and control" anında** gelir yazılır. Bu,
     KÖK'ün phantom-income endişesini bir ikincil blog yorumundan **IRS'nin
     yazılı kuralına** taşır. **Hâlâ burn'A ÖZEL bir görüş yok** — Rev. Rul.
     staking hakkındadır, burn'ü ele almaz; bkz. §6.E. Yani tek kalan boşluk
     **daha da daraldı**: birincil kural phantom-income'ın "gelir yazılma
     anını" cevaplar, **sadece burn'ün o yükümlülüğü azaltıp azaltmadığını**
     cevaplamaz. §6.5'teki phantom-tax riski *çözülmemiş bir argüman* olarak
     duruyor, *yerleşmiş bir kural* olarak değil. Bu listedeki öteki üç madde
     v2.6'da kapatıldı ve listenin güncel kalması için buradan çıkarıldı:
     ESMA rehberleri (§6.2, Guideline 9 + ESMA75453128700-1323), MAS'ın DTO
     rehberi (§6.3, Case study 1), SEC/ABD bölümünün tamamı (§1).

---

## 1. GÖREV 1A — SEC v. Ripple (SDNY 2023) ve 2025–2026 GÜNCEL Durumu

### 1.1 Torres'in 13 Temmuz 2023 özet kararı — üç kategorik ayrım

**★ GÜNCELLEME (27.09.2026) — ARTIK BİRİNCİL:** Kararın **tam metni**
çıkarıldı (**Document 874, 34 sayfa, 1.802 satır**, bkz. §6 madde 7) —
SDNY'nin kendi sunucusundan `curl` ile indirilip `pdftotext` ile çıkarıldı.
Aşağıdaki verbatim pasajlar artık **mahkemenin kendi metnünden**;
ortadaki ikincil kaynak (Gordon Law) çapraz kontrol için korunur.

> **Tokenin kendisi (birincil):** "XRP, as a digital token, is not in and of
> itself a 'contract, transaction[,] or scheme' that embodies the Howey
> requirements of an investment contract."
> **Kurumsal satışlar (birincil):** *"Therefore, having considered the
> economic reality and totality of circumstances surrounding the
> Institutional Sales, the Court concludes that Ripple's Institutional Sales
> of XRP constituted the unregistered offer and sale of investment contracts
> in violation of Section 5 of the Securities Act."* (≈$728.9M değerlendirildi)
> **Programatik (borsa) satışlar (birincil):** *"Therefore, having considered
> the economic reality and totality of circumstances, the Court concludes
> that Ripple's Programmatic Sales of XRP did not constitute the offer and
> sale of investment contracts."* — **özellikle:** "the record does not
> establish the third Howey prong as to the Programmatic Sales" (≈$757.6M).
> — *Kaynak:* SDNY Document 874, `nysd.uscourts.gov` (**BİRİNCİL**);
> ikincil çapraz kontrol: Gordon Law Group, "Partial Ripple Victory..."

**Yorum (TAMGA):** Torres'in yeniliği **transaction-by-transaction** analiz: aynı token
kurumsal satışta menkul kıymet, borsada perakende satışta menkul kıymet değil olabilir.
KÖK dersi: belirleyici olan tokenin kendisi değil, **hangi işlemin yapıldığı**.

### 1.2 8 Mayıs 2025 — uzlaşma çerçevesi (BİRİNCİL)

> **SEC Litigation Release No. 26306 / May 8, 2025** — "SEC Announces Settlement Agreement to
> Resolve Civil Enforcement Action Against Ripple and Two of Its Executives": "The settlement
> agreement provides, among other things, that the Commission and Ripple would jointly request
> the district court to issue an indicative ruling as to whether it would dissolve the
> injunction against Ripple in the district court's August 7, 2024 final judgment and order
> the escrow account holding the **$125,035,150** civil penalty imposed by the final judgment
> be released, with **$50 million paid to the Commission in full satisfaction of that penalty**
> and the remainder paid to Ripple. The Settlement Agreement further provides that, following
> an indication from the district court that it would dissolve the injunction and release the
> escrowed penalty amounts as requested, the Commission and Ripple will seek a limited remand
> ... after which they would move to dismiss their respective appeals..."
> — *Kaynak:* https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26306
> (**BİRİNCİL kaynak; sec.gov bu oturumda `User-Agent: KOK Research <e-posta>` ile erişildi.**)

> **SEC'nin 2025 politik dönüşünü gösteren gerekçe (aynı release, verbatim):** "The
> Commission's decision to exercise its discretion and seek a resolution of this pending
> enforcement action rests on its judgment that such resolution will facilitate the
> Commission's ongoing efforts to reform and renew its regulatory approach to the crypto
> industry, **not on any assessment of the merits of the claims alleged in the action**."

### 1.3 26 Haziran 2025 — Torres ortak talebi reddetti

> "Judge Analisa Torres has rejected a $50 million settlement between Ripple and the SEC that
> would have dissolved the permanent injunction blocking the institutional sales of XRP. The
> June 26 ruling maintains Ripple's business restrictions indefinitely, despite both parties
> agreeing to reduce the original $125 million penalty by 60%. ... Torres determined that the
> parties failed to show the 'exceptional circumstances' required to vacate a final judgment..."
> — *Kaynak:* Cryptonews, "Ripple Settlement Denied as Judge Torres Rejects $50M Deal..."
> (**26 Haziran 2025**, yazar Anas Hassan),
> https://cryptonews.com/news/ripple-settlement-denied-as-judge-torres-rejects-50m-deal-xrp-institutional-sales-remain-limited/
> (**İKİNCİL kaynak — kararın aslı için bkz. §6 madde 8.**)

**★ GÜNCELLEME (27.09.2026) — ARTIK BİRİNCİL:** Kararın **tam metni**
çıkarıldı (**Document 989, 5 sayfa**, bkz. §6 madde 8). Cryptonews'un
özeti doğrulandı ve **iki önemli detay eklendi**:

> *"Plaintiff ... and Defendant, Ripple Labs, Inc. ('Ripple'), ask the Court
> to state that it would (1) 'dissolve' the Court's permanent injunction
> ordering Ripple to obey the law, and (2) cut the monetary penalty imposed
> against Ripple by more than half. ... **The request is DENIED.**"*

> *"But the parties do not have the authority to agree not to be bound by a
> court's final judgment that a party violated an Act of Congress in such a
> manner that a permanent injunction and a civil penalty were necessary to
> prevent that party from violating the law again. ... For that, the parties
> must show exceptional circumstances that outweigh the public interest or
> the administration of justice. ... **They have not come close to doing so
> here.**"*

**TAMGA'nın 2026-09 yorumu keskinleşti:** "taraflar anlaştı, mahkeme
boşversin" diye bir yol bulunmadı — Torres, mahkeme emirlerinin
**tarafların ortak iradesiyle kaldırılamayacağını** yazdı; tek iki çıkış
yolu temyizi **geri çekmek** veya **temyiz etmek** ("primary route"). Yani
kalıcı injunction, anlaşma onaylansa bile yürürlükte kalır.

### 1.4 7 Ağustos 2025 — Temyizlerin reddi; DAVA KAPALI, final karar aynen yürürlükte (BİRİNCİL)

> **SEC Litigation Release No. 26369 / Aug. 7, 2025** — "SEC Announces Joint Stipulation to
> Dismiss Appeals, Resolving Civil Enforcement Action Against Ripple and Two of Its
> Executives": "The Securities and Exchange Commission today filed a **Joint Stipulation of
> Dismissal** entered into with defendants Ripple Labs, Inc., Bradley Garlinghouse, and
> Christian A. Larsen ('Defendants') that **dismisses the Commission's appeal and Ripple's
> cross-appeal** pending in the United States Court of Appeals for the Second Circuit, and
> resolves the Commission's civil enforcement action against Defendants. Those cross-appeals
> followed a final judgment by the district court that imposed a **$125,035,150 civil
> penalty** against Ripple and **an injunction prohibiting Ripple from violating the
> registration provisions of the Securities Act of 1933. Following the dismissal of the
> cross-appeals, that final judgment will remain in effect.**"
> — *Kaynak:* https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26369
> (**BİRİNCİL kaynak.**) Dava numaraları: Case No. 1:20-cv-10832 (S.D.N.Y., filed Dec. 22,
> 2020); Appeal Nos. 24-2648(L) ve 24-2705 (XAP) (2d Cir.).

**2026-09 itibariyle DURUM (TAMGA):** Medyadaki "$50M ödedi / dava kazanıldı" özeti
**birincil kaynağa göre yanıltıcıdır**: LR-26369, $125,035,150 ceza ve ihtiyati hükmün
**yürürlükte kaldığını** açıkça yazar. Yani Mayıs 2025'deki $50M'lık indirim mekanizması
(distinct court'un ihtiyatı kaldırmasına koşullu) **işletilmemiştir**. İkincil bir izleme
kaynağı da bunu destekler: "a permanent injunction on Ripple's future institutional XRP sales
remains in place — the case did not end without any injunction. No new developments in this
matter have occurred so far in 2026." (Lawfold, 17 Eylül 2026,
https://lawfold.com/ripple-sec-lawsuit-status-2026/ — **düşük güvenilirlikli SEO kaynağı,
yalnızca destekleyici.**)

**EN ÖNEMLİ HUKUKİ SONUÇ:** İkinci Circuit'te çekaplar **ortak stipülasyonla reddedildiği**
için **merits kararı verilmemiştir**. Torres'in "programatik (borsa) satışlar menkul kıymet
değil" öğretisi **appellate onaydan geçmemiştir** → ABD'de "borsa satışı = menkul kıymet
değil" tezi **bağlayıcı emsal (precedent) değildir**, yalnızca SDNY kararlığında kalır.

### 1.5 Ek: SEC artık XRP'yi "digital commodity" olarak listeliyor (2026, BİRİNCİL)

> **SEC Yorum Release No. 33-11412 (17 Mart 2026):** "Examples of digital commodities include
> Aptos (APT); Avalanche (AVAX); Bitcoin (BTC); Bitcoin Cash (BCH); Cardano (ADA); Chainlink
> (LINK); Dogecoin (DOGE); Ether (ETH); Hedera (HBAR); Litecoin (LTC); Polkadot (DOT); Shiba
> Inu (SHIB); Solana (SOL); Stellar (XLM); Tezos (XTZ); **and XRP (XRP)**."
> — *Kaynak:* https://www.sec.gov/files/rules/interp/2026/33-11412.pdf (s. 14) (**BİRİNCİL.**)

Beş yıllık dava, XRP'nin "digital commodity" olarak resmen listelenmesiyle kapanmıştır —
2026'daki regülatif dönüşümün somut kanıtı.

---

## 2. GÖREV 1B — Howey Testi 2026: SEC'nin Yeni Tutumu, Sınıflandırma ve Safe Harbor

### 2.1 Çerçeve: SEC Yorum Release No. 33-11412 (17 Mart 2026) — BİRİNCİL

> **Başlık:** "Application of the Federal Securities Laws to Certain Types of Crypto Assets
> and Certain Transactions Involving Crypto Assets" · **Release No. 33-11412; 34-105020** ·
> **SEC Issue Date: 17 Mart 2026 · Effective Date: 23 Mart 2026 · Federal Register Publish
> Date: 23 Mart 2026 · File Number: S7-2026-09** (CFTC eşliğinde rehberlik içerir.)
> *Kaynaklar:* https://www.sec.gov/rules-regulations/2026/03/s7-2026-09 ve PDF
> https://www.sec.gov/files/rules/interp/2026/33-11412.pdf
> (**BİRİNCİL — 68 sayfa; tam metin bu oturumda PDF'ten çıkarıldı.**)

> **Beş kategorik sınıflandırma (verbatim):** "we classify crypto assets into five categories
> based on their characteristics, uses, and functions: (i) digital commodities; (ii) digital
> collectibles; (iii) digital tools; (iv) stablecoins; and (v) digital securities. **Digital
> commodities, digital collectibles, and digital tools, each as further described below, are
> not themselves securities.** However, as with any asset that is not a security, **a
> non-security crypto asset can be offered and sold subject to an investment contract, which
> is a security.**" — *33-11412, §III, s. 14.*

> **Atkins'in aynı günkü açıklaması (BİRİNCİL):** "our interpretation—grounded in existing law
> and informed by extensive public input—establishes four asset categories that are not deemed
> securities: digital commodities, digital collectibles, digital tools, and payment stablecoins
> under the GENIUS Act. With these categories in place, the interpretation then clarifies that
> only one crypto asset class remains subject to the securities laws: digital securities,
> namely traditional securities that are tokenized. ... **We are not the Securities and
> Everything Commission, anymore.**"
> — *Kaynak:* Paul S. Atkins, "Regulation Crypto Assets: A Token Safe Harbor", DC Blockchain
> Summit, Washington D.C., **17 Mart 2026**,
> https://www.sec.gov/newsroom/speeches-statements/atkins-remarks-regulation-crypto-assets-031726

### 2.2 "Digital commodity" — KÖK için EN OLASI kategori (BİRİNCİL)

> "A digital commodity is a crypto asset that is intrinsically linked to and derives its value
> from the programmatic operation of a crypto system that is 'functional', as well as supply
> and demand dynamics, rather than from the expectation of profits from the essential
> managerial efforts of others. A digital commodity does not have intrinsic economic properties
> or rights, such as generating a passive yield or conveying rights to future income, profits,
> or assets of a business enterprise or other entity, promisor, or obligor, but may have
> certain other rights (as discussed below)." — *33-11412, §III.A, s. 14.*

> **Footnote 48 (ekonomik anlam):** "we are using the term 'commodity' in an economic and
> commercial sense (i.e., assets that are **fungible, have utility, and whose value is
> determined by supply and demand**)."
> **Footnote 49 ("functional"):** "a crypto system is 'functional' if the system's native
> crypto asset can be used on the system in accordance with the programmatic utility of the
> system."
> **Footnote 50 ("decentralized"):** "a crypto system is 'decentralized' if the crypto system
> functions and operates autonomously with no person, entity, or group of persons or entities
> having operational, economic, or voting control of the crypto system."

> **Amacı:** "The programmed purpose of a digital commodity is to facilitate and incentivize
> the validation, ordering, and confirmation of transactions on the associated functional
> crypto system, serve as a mechanism to maintain the functioning and/or security of the
> associated functional crypto system, and foster network effects." — *33-11412, s. 15.*

**KÖK v2'ye uygulama (TAMGA analizi):** KOK (a) fungible, (b) compute/fee ödemesinde gerçek
faydaya sahip, (c) arz-talep ile değerlenen, (d) fair-launch olduğu için "essential managerial
efforts" beklentisi zayıf bir varlıktır. **Koşullar:** sistemin **fonksiyonel** olması
(mainnet'te tokenin gerçek compute ile kullanılması) ve ekibin kâr vaadinde bulunmaması.
**Önemli:** "digital commodity" bile olsa, token bir **investment contract** ile satılırsa o
işlem menkul kıymet olur (§2.4).

### 2.3 "Digital tools" — DAR kategori; KÖK buraya DÜŞMEZ (BİRİNCİL)

> "A digital tool is a crypto asset that performs a practical function, such as a membership,
> ticket, credential, title instrument, or identity badge. ... **Digital tools often are
> non-transferrable or 'soul-bound,'** and their value is derived from their practical
> functionality. ... Examples of digital tools available in the markets today, based on our
> understanding of their characteristics, terms, and functions as of the date of this release,
> include **Ethereum Name Service domain names** and **CoinDesk's 'Microcosms' NFT Consensus
> Ticket**. A digital tool itself, as described in this release, is not a security because it
> does not have the economic characteristics of a security. ... **Digital tools are onchain
> analogues to physical utilities, which generally have not been regulated as securities.**"
> — *33-11412, §III.C, s. 20–21.*

> **Ağ etkisi (network effects) notu (footnote 72):** "If the creator of a digital tool
> facilitates network effects, including through the use of a digital tool, such activities do
> not constitute essential managerial efforts."

**Kullanıcının sorusunun yanıtı — "Transfer edilebilen ama hizmete erişim veren token ne
gerektirir?" (TAMGA):** SEC çerçevesinde "utility" işlevi **tek başına** belirleyici değildir.
Belirleyici olan **(1) sınıflandırma** (digital commodity mi, digital tool mu) ve **(2)
tokenin hangi işlemle sunulduğu**. Transfer edilebilir bir utility token "digital commodity"
olarak sınıflanır; çünkü "digital tool" tanımı non-transferrable/soul-bound örneklerle
yazılmıştır. Ardından: (i) geliştirici tarafından kâr vaadiyle satılırsa **investment
contract** (menkul kıymet) olur; (ii) yalnızca madencilik ödülü olarak dağıtılırsa ve sistem
fonksiyonel ise **menkul kıymet işlemi olmaz** (§2.4). Yani "utility" kimlik reçete değil;
**dağıtım mekanizması + vaadler** belirleyicidir.

### 2.4 Investment contract analizi + "PROTOCOL MINING" yorumu (KÖK Layer G için KRİTİK)

> **Ne zaman investment contract oluşur (verbatim):** "A non-security crypto asset becomes
> subject to an investment contract when an issuer offers it by inducing an investment of
> money in a common enterprise with representations or promises to undertake essential
> managerial efforts from which a purchaser would reasonably expect to derive profits. A
> purchaser's reasonable profit expectations depend on the issuer's representations or promises
> to engage in such essential managerial efforts. **Absent such representations or promises
> being conveyed to purchasers, it would not be reasonable for a purchaser to expect profits
> from the contract, transaction, or scheme.**" — *33-11412, §IV.A, s. 25.*

> **Açık-net olma ve "whitepaper" kanalları:** "representations or promises are more likely to
> create reasonable expectations of profit when they are **explicit and unambiguous** as to the
> essential managerial efforts to be undertaken by the issuer, contain sufficient details
> demonstrating the issuer's ability to implement the proposed project, and explain how the
> issuer's efforts will produce the profits that purchasers reasonably expect." ... "documents
> clearly attributable to the issuer (**such as a whitepaper**)" bu kanallardandır. — *Aynı
> bölüm, s. 27–28.* (Footnote 92: "whitepaper ... describes the technical aspects of a crypto
> asset project ... along with other relevant details.")

> **Satış sonrası vaatler geriye dönük etki yapmaz:** "the issuer's post-sale representations or
> promises would not convert the prior sale into an offer or sale of an investment contract."
> — *Aynı bölüm, s. 27.*

> **Ayrılma (separation):** "A non-security crypto asset that was offered and sold subject to
> an investment contract does not necessarily remain subject to the associated investment
> contract in perpetuity. ... When a purchaser of a non-security crypto asset ... could no
> longer reasonably expect the issuer's representations or promises ... to remain connected to
> the non-security crypto asset, the non-security crypto asset **separates** from such
> representations or promises, and thereafter the non-security crypto asset is not subject to
> the Federal securities laws." — *33-11412, §IV.B, s. 29.* (İki gösterge: (1) vaadlerin
> **yerine getirilmesi**; (2) vaadlerin **yerine getirilememesi**. Çözülme "immediately upon
> delivery" dahil her an olabilir.)

**PoW madenciliği — KÖK Layer G için doğrudan yorum (BİRİNCİL):**

> **Kapsam:** "Federal securities laws to: (1) certain digital commodity activities known as
> 'mining' on **public, permissionless crypto networks that use proof-of-work ('PoW')** as a
> consensus mechanism ('PoW Networks'); ... In this release, we refer to mining digital
> commodities on PoW Networks as 'Protocol Mining'" — *33-11412, §V girişi, s. 35.*

> **PoW tanımı (dikkat):** "PoW is a consensus mechanism that incentivizes transaction
> validation by rewarding participants, called 'miners,' who operate nodes adding computational
> resources to the PoW Network. ... **The 'work' in PoW is the computational resources that
> miners contribute to validate transactions and add new blocks to the PoW Network.** Miners do
> not have to own the PoW Network's digital commodity to validate transactions. ... Miners use
> computers to solve complex mathematical equations in the form of cryptographic puzzles."
> — *33-11412, §V.A.1, s. 36.*

> **SONUÇ (verbatim):** "**Protocol Mining Activities**, in the manner and under the
> circumstances described in this release, **do not involve the offer and sale of a security**
> within the meaning of section 2(a)(1) of the Securities Act and section 3(a)(10) of the
> Exchange Act. Accordingly, participants in Protocol Mining Activities **do not need to
> register transactions with the Commission** under the Securities Act or fall within an
> available exemption from registration in connection with these Protocol Mining Activities."
> — *33-11412, §V.A.3, s. 39.*

> **Gerekçe (verbatim):** "By adding its computational resources to the PoW Network, the miner
> merely is engaging in an **administrative or ministerial activity** to secure the PoW
> Network, validate transactions and add new blocks, and receive rewards. A miner's expectation
> to receive rewards is not derived from any third party's essential managerial efforts upon
> which the PoW Network's success depends. ... As such, **rewards are payments to the miner in
> exchange for services it provides to the PoW Network rather than profits derived from the
> essential managerial efforts of others.**" — *Aynı bölüm, s. 39.*

> **Madencilik havuzları (verbatim):** "whether a miner self (or solo) mines or mines as a
> member of a mining pool does not alter the nature of Protocol Mining for purposes of the
> Howey test. In either case, Protocol Mining, as described in this release, remains an
> administrative or ministerial activity." — *Aynı bölüm, s. 39–40.* **Footnote 105 uyarısı:**
> "This assumes miners receive a **pro rata** share of the rewards from the pool based on their
> contribution of computational power, rather than where non-miners can **purchase interests in
> the pool**, or miners can pay to receive greater than a pro rata share..."

**KÖK v2'ye uygulama (TAMGA analizi — dikkatli belgelenmesi gerek):**
- KÖK Layer G, MatMul tabanlı **PoUW**'dur. SEC'nin yorumu somut olarak "cryptographic
  puzzles" ifadesi kullanır; **ancak** "work" tanımı daha geniştir: "the computational
  resources that miners contribute to validate transactions and add new blocks." KÖK'ün
  PoUW'u da "madencilerin hesaplama kaynağı katıp protokol tarafından ödüllendirildiği" bir
  mimaridir; havuz operatörünün çabası da "administrative or ministerial" sayılır.
- **İki dikkat noktası:** (i) Yorum, mining'i **"digital commodity"** madenciliği olarak
  tanımlar — KOK'un digital commodity sınıflanması **önkoşuldur**; (ii) yorumun madenciliği
  "administrative or ministerial" nitelemesi, KÖK madencilerinin **faydalı** (AI inference)
  hesaplama yapmasıyla **görünürde gerilimlidir** — fakat iki işlemin hukuki niteliği
  **ayrıdır**: (a) madencinin protokolden aldığı **blok ödülü** = "services ... provided to
  the PoW Network" → menkul kıymet değil; (b) task market'ta kullanıcının **fee karşılığı
  compute satın alması** = normal ticari hizmet alımıdır (emir/komisyon ilişkisi, herhangi bir
  investment contract içermez). **Bu ayrım dokümantasyonda açıkça yapılmalıdır.**
- **Öneri:** Whitepaper/pazarlama metinlerinde KOK'un değer artışına yönelik **hiçbir vaat**
  kullanılmamalı; "absent such representations or promises ... it would not be reasonable ...
  to expect profits" diline sadık kalınmalıdır. Anonim-kurucu + sıfır-premine + sıfır-VC
  yapısı bu dilin **samimi** olmasını sağlar (issuer olarak kimin kâr vaadinde bulunacağı
  belirsizdir).

### 2.5 Ağustos 2026 — RESMİ TEKLİF: "Regulation Crypto Assets" (teklif, yürürlükte DEĞİL)

> **Federal Register (BİRİNCİL):** "SECURITIES AND EXCHANGE COMMISSION 17 CFR Parts 200, 201,
> 228, 230, 232, and 239 [Release Nos. **33–11434; 34–106150**; File No. **S7–2026–27**]
> RIN 3235–AN38 **Regulation Crypto Assets** ACTION: **Proposed rule**. SUMMARY: The
> Securities and Exchange Commission (''Commission'') is proposing new rules to create a
> tailored offering regime for certain investment contracts involving crypto assets. ... The
> proposed rules would be set forth in a new regulation titled ''Regulation Crypto Assets'' and
> would include **two exemptions** from the registration requirements of section 5 of the
> Securities Act of 1933. **The first exemption would permit offerings of up to $5 million
> during a four-year period. The second exemption would permit offerings of up to $75 million
> during each 12-month period.**"
> — *Kaynak:* Federal Register, **Vol. 91, No. 161, Friday, August 21, 2026**, s. 54510,
> https://www.govinfo.gov/content/pkg/FR-2026-08-21/pdf/2026-17183.pdf
> (**BİRİNCİL — 146 sayfalık tam metin bu oturumda çekildi.**)

> **Safe harbor (Subpart D, Rule 400, verbatim):** "Subpart D of Regulation Crypto Assets would
> set forth a **non-exclusive safe harbor** from the term ''investment contract'' in the
> definitions of ''security'' in section 2(a)(1) of the Securities Act and section 3(a)(10) of
> the Exchange Act. As proposed, if the conditions of the safe harbor are satisfied, then a
> covered investment contract will be deemed by the Commission to have **ceased to exist**, and
> the crypto asset that was subject to the covered investment contract will be deemed by the
> Commission not to be subject to such investment contract..." — *Aynı FR dokümanı, s. 54554
> (§II.D).* Aynı bölüm, 2026 Yorumu'nun iki ayrılma koşulunu teyit eder: "(1) the issuer has
> fulfilled its representations or promises to engage in essential managerial efforts under the
> covered investment contract, or (2) the purchaser would not reasonably expect..." (s. 54554).

> **Atkins'in açıklaması (18 Ağustos 2026, BİRİNCİL):** "the proposed rules include an
> '**investment contract safe harbor**.' Under this safe harbor, **if the issuer certifies to
> the Commission that it has ceased or terminated all essential managerial efforts that it
> promised to undertake under the investment contract** and satisfies certain other conditions,
> then the Commission would no longer deem the non-security crypto asset to be subject to an
> investment contract and, therefore, no longer subject to the authority of the Commission."
> — *Kaynak:* Paul S. Atkins, "Regulation Crypto Assets: Fit-for-Purpose Exemptions for Crypto
> Market Innovation", **18 Ağustos 2026**,
> https://www.sec.gov/newsroom/speeches-statements/atkins-statement-regulation-crypto-assets-081826

> **Köken (Atkins, 17 Mart 2026):** "the proposal that I will discuss today, my vision for
> Regulation Crypto Assets, traces its lineage directly to the framework that she first
> introduced in **February 2020 as the Token Safe Harbor**" (Commissioner Hester Peirce'a).
> Atkins ayrıca Kongre'deki **CLARITY Act**'ı destekler: "Regulation Crypto Assets is a
> framework that would draw heavily from Congressional work over recent years, particularly the
> CLARITY Act."

**Durum (2026-09-20, TAMGA):** Regulation Crypto Assets **henüz bir TEKLİFTİR** (proposed
rule); yorum süreci devam etmektedir, **yürürlükte değildir**. KÖK planlaması **mevcut
hukuka** (Howey + 33-11412 yorumu) göre yapılmalı; safe harbor ancak yürürlüğe girerse bir
opsiyon olur. **Forecast (önerilen kural) vs actual (yürürlükteki yorum) ayrımı burada
kritiktir.**

### 2.6 Özet tablosu — ABD'de KÖK token modelinin üç ayağı

| KÖK ayağı | ABD hukuki nitelik (2026 yorumuna göre) | Dayanak |
|---|---|---|
| (i) Blok ödülü (madencilik) | **Menkul kıymet işlemi değil** — "Protocol Mining Activities ... do not involve the offer and sale of a security" | 33-11412 §V.A.3 |
| (ii) Fee → escrow → burn | Hizmet alımı + protokol fee'si; **investment contract öğesi yok** (kâr beklentisi değil, hizmet ödemesi). Burn'ün hukuki analizi için literatüre **ULAŞILAMADI** (bkz. §5) | 33-11412 §IV.A + BULUNAMADI |
| (iii) Token ile ödenebilir compute | Tokenin kendisi **"digital commodity"** → menkul kıymet değil; sistem **"functional"** olmalı | 33-11412 §III.A, fn 48–49 |

---

## 3. GÖREV 1C — MiCA (AB): 2026-09 Tam Uygulama Durumu

### 3.1 Temel veriler (BİRİNCİL — EUR-Lex tam metni)

> **Yönetmelik:** "REGULATION (EU) 2023/1114 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL of
> **31 May 2023** on markets in crypto-assets, and amending Regulations (EU) No 1093/2010 and
> (EU) No 1095/2010 and Directives 2013/36/EU and (EU) 2019/1937" — Official Journal of the
> European Union, **L 150/40, 9.6.2023**.
> *Kaynak (EUR-Lex; 1.9 MB'lık tam metin bu oturumda çekildi):*
> https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114 (**BİRİNCİL.**)

**Başlık yapısı (bu oturumda EUR-Lex'ten doğrulandı):** TITLE I — Subject Matter, Scope and
Definitions (Art. 1–3); **TITLE II — Crypto-assets other than asset-referenced tokens or
e-money tokens** (Art. 4 ve devamı; **whitepaper rejimi burada**); TITLE III — Asset-Referenced
Tokens; TITLE IV — E-Money Tokens; TITLE V — Authorisation and operating conditions for
crypto-asset service providers (CASPs); TITLE VI — Prevention and prohibition of market abuse;
TITLE VII — Competent authorities, EBA and ESMA.

### 3.2 "Utility token" tanımı — VERBATIM ve "transfer edilebilir olmalı mı?" (BİRİNCİL)

> **Article 3, point (9):** "**'utility token' means a type of crypto-asset that is only
> intended to provide access to a good or a service supplied by its issuer**;"
> **Article 3, point (2):** "'crypto-asset' means a digital representation of a value or of a
> right that is **able to be transferred and stored electronically** using distributed ledger
> technology or similar technology;"
> **Article 3, point (10):** "'issuer' means a natural or legal person, or other undertaking,
> who issues crypto-assets;"
> **Article 3, point (12):** "'offer to the public' means a communication to persons in any
> form, and by any means, presenting sufficient information on the terms of the offer and the
> crypto-assets to be offered so as to enable prospective holders to decide whether to
> **purchase** those crypto-assets;"
> **Article 3, point (13):** "'offeror' means a natural or legal person, or other undertaking,
> or the issuer, who offers crypto-assets to the public;"
> — *Hepsi Regulation (EU) 2023/1114, Article 3(1).*

> **Recital 17 (BİRİNCİL):** "**Digital assets that cannot be transferred to other holders do
> not fall within the definition of crypto-assets.** Therefore, digital assets that are
> accepted only by the issuer or the offeror and that are technically impossible to transfer
> directly to other holders should be excluded from the scope of this Regulation. An example of
> such digital assets includes loyalty schemes where the loyalty points can be exchanged for
> benefits only with the issuer or offeror of those points."

> **NUMARALANDIRMA NOTU (v1'deki düzeltme korunmuştur):** Görev kağıdında "Article 3(1)(5)"
> olarak belirtilen utility-token tanımı, **nihai Regulation'da Article 3(9)'dur**. Resmi
> metinde tanımlar tek bir numaralandırılmış listedir: (2) crypto-asset, (5) 'distributed
> ledger technology', (6) asset-referenced token, (7) e-money token, (8) official currency,
> **(9) utility token**, (10) issuer. "(1)(5)" numaralandırması **Avrupa Komisyonu'nun 2020
> taslağına (COM(2020) 593)** uymaktadır; nihai metinde geçerli numara **(9)**'dur.

**"Transfer edilebilen ama hizmete erişim veren token ne gerektirir?" — Yanıt (TAMGA):**
- MiCA'da "utility token" tanımı **non-transferability şartı koymaz**. Aksine, "crypto-asset"
  tanımı (Art 3(2)) transfer edilebilme kabiliyeti ister ve **Recital 17** transfer edilemeyen
  dijital varlıkları MiCA kapsamı **dışında** tutar. Yani: **bir token hem transfer edilebilir
  hem utility token olabilir.**
- **Üç gerilim (TAMGA analizi):** (1) "only intended to provide access" sıfatı — KOK hem
  compute erişimi sağlar hem de ikincil piyasada değeri olan bir ödeme aracıdır; bu "only"
  sıfatı ile gerilimlidir (MiCA madde içi çözüm vermez; Recital 11'in "substance over form"
  ilkesine göre değerlendirme yapılacaktır). (2) "supplied by **its issuer**" — KÖK fair-launch,
  **issuer'siz** bir modeli hedeflediği için bu sıfat da gerilimlidir (bkz. Recital 22).
  (3) Whitepaper'da **zorunlu beyanlar** vardır (v1'de tespit edildiği üzere): "the crypto-asset
  may not always be transferable; (c) the crypto-asset may not be liquid; (d) where the offer to
  the public concerns a utility token, that utility token may not be exchangeable against the
> good or service..." (Article 13'teki whitepaper içeriği).

> **Recital 22 (issuer'siz varlıklar — yalnızca RECIAL, operatif değil):** "This Regulation
> applies to natural and legal persons ... **including when part of such activities or services
> is performed in a decentralised manner. Where crypto-asset services are provided in a fully
> decentralised manner without any intermediary, they should not fall within the scope of this
> Regulation.** This Regulation covers the rights and obligations of issuers of crypto-assets,
> offerors, ... **Where crypto-assets have no identifiable issuer, they should not fall within
> the scope of Title II, III or IV of this Regulation.** Crypto-asset service providers
> providing services in respect of such crypto-assets should, however, be covered by this
> Regulation."
> **TAMGA notu:** "no identifiable issuer" muafiyeti **operatif metinde (Article 2) yer
> almaz**; yalnızca yorum aracıdır (recital). Operatif hukuk (Art 2(1)) "natural and legal
> persons ... engaged in the issuance, offer to the public and admission to trading of
> crypto-assets" der. Bu, KÖK için **belirsizlik kaynağıdır**.

### 3.3 Whitepaper zorunluluğu + MADENCİLİK MUAFİYETİ (KÖK için KRİTİK) (BİRİNCİL)

> **Article 4(1) (zorunluluk):** "A person shall not make an offer to the public of a
> crypto-asset other than an asset-referenced token or e-money token in the Union unless that
> person: (a) is a legal person; (b) has drawn up a crypto-asset white paper in respect of that
> crypto-asset in accordance with Article 6; (c) has notified the crypto-asset white paper in
> accordance with Article 8; (d) has published the crypto-asset white paper in accordance with
> Article 9; (e) has drafted the marketing communications, if any, ...; (f) has published the
> marketing communications, if any, ...; (g) complies with the requirements for offerors laid
> down in Article 14."

> **Article 4(2) (kısmi muafiyetler — yalnızca (b),(c),(d),(f) yükümlülüklerini kaldırır):**
> "...shall not apply to any of the following offers ...: (a) an offer to fewer than **150**
> natural or legal persons per Member State where such persons are acting on their own account;
> (b) over a period of 12 months ... the total consideration of an offer ... does not exceed
> **EUR 1 000 000**, or the equivalent amount in another official currency or in crypto-assets;
> (c) an offer ... addressed solely to **qualified investors** where the crypto-asset can only
> be held by such qualified investors."

> **Article 4(3) (TITLE II'nin TAMAMINDAN muafiyet — MADENCİLİK BURADA):** "**This Title shall
> not apply to offers to the public of crypto-assets other than asset-referenced tokens or
> e-money tokens where any of the following apply: (a) the crypto-asset is offered for free;
> (b) the crypto-asset is automatically created as a reward for the maintenance of the
> distributed ledger or the validation of transactions; (c) the offer concerns a utility token
> providing access to a good or service that exists or is in operation; (d) the holder of the
> crypto-asset has the right to use it only in exchange for goods and services in a limited
> network of merchants with contractual arrangements with the offeror.**"

> **"Free" istisnasının sınırı (aynı paragraf):** "a crypto-asset shall not be considered to be
> offered for free where purchasers are required to provide, or to undertake to provide,
> personal data to the offeror in exchange for that crypto-asset, or where the offeror of a
> crypto-asset receives from prospective holders of that crypto-asset **any fees, commissions,
> or monetary or non-monetary benefits in exchange for that crypto-asset**."

> **Article 4(4) (muafiyetleri KALDIRAN koşul — BORSA LİSTELEME TUZAĞI):** "**The exemptions
> listed in paragraphs 2 and 3 shall not apply where the offeror, or another person acting on
> the offeror's behalf, makes known in any communication its intention to seek admission to
> trading of a crypto-asset** other than an asset-referenced token or an e-money token."

> **Article 4(6) (henüz var olmayan hizmetler için 12-ay sınırı):** "Where the offer to the
> public of the crypto-asset ... concerns a utility token providing access to goods and
> services that **do not yet exist or are not yet in operation**, the duration of the offer to
> the public as described in the crypto-asset white paper **shall not exceed 12 months** from
> the date of publication of the crypto-asset white paper."

> **Article 4(7):** "Any subsequent offer to the public ... shall be deemed a separate offer to
> the public to which the requirements of paragraph 1 apply, without prejudice to the possible
> application of paragraph 2 or 3..."

**KÖK v2'ye uygulama (TAMGA analizi):**
- KOK madencilik ödülleri **Article 4(3)(b)** kapsamında görünebilir ("automatically created as
  a reward for the maintenance of the distributed ledger or the validation of transactions").
  Destekleyici yorum: Article 3(12) "offer to the public" tanımı **"purchase"** (satın alma)
  unsuruna vurgu yapar — madenciler tokeni **satın almaz, kazanır**. Bu, madencilik ödülünü
  "offer to the public" tanımı dışında bırakmayı destekleyen bir **çıkarımdır** (resmi bir
  ESMA/AB görüşüyle teyit edilmemiştir — bkz. §3.4).
- **EN KRİTİK RİSK — Article 4(4):** offerör (veya adına hareket eden herhangi biri) **herhangi
  bir iletişimde** borsada listelenme niyetini belli ederse **bütün muafiyetler (4(2) ve 4(3))
  düşer** ve whitepaper rejimi tam uygulanır. KÖK gibi amaç-mainnet sonrası listelenmeyi
  planlayan bir proje için pratik öneri: **listelenme niyeti herhangi bir resmi iletişimde
  açıklanmadan ÖNCE MiCA whitepaper hazırlığı başlatılmalı**; veya niyet açıkça beyan
  ediliyorsa whitepaper süreci hiç geciktirilmemelidir.
- **"offeror" kimdir?** KÖK'ün tokenleri **satmayan** anonim bir ekibi varken "offeror"
  sayılıp sayılmayacağı belirsizdir (Recital 22 sinyal verir ama operatif değildir).

### 3.4 ESMA Rehberi — BİRİNCİL Kaynakla ÇÖZÜLDÜ (24 Eylül 2026) ★

**Kaynak (BİRİNCİL):** ESMA, "Final Report — Guidelines on the conditions and criteria for the
qualification of crypto-assets as financial instruments", **ESMA75453128700-1323**, **17 Aralık
2024**, 49 sayfa. Erişim: 24 Eylül 2026, HTTP 200.
https://www.esma.europa.eu/sites/default/files/2024-12/ESMA75453128700-1323_Final_Report_Guidelines_on_the_conditions_and_criteria_for_the_qualification_of_CAs_as_FIs.pdf
*(MiCA Article 2(5)'in yerine getirdiği rehberdir; "The Guidelines will apply from three months
after the publication of the translations" — 17.12.2024'te yayımlandığı için 2025 içinde
uygulamaya girmiştir, Eylül 2026 itibariyle **yürürlükte**dir.)*

> **★ EN KRİTİK BULGU — "kâr beklentisi tek başına yeterli DEĞİL" (verbatim, §23):** "An
> example is that of crypto-assets which are designed as **utility tokens within a specific
> ecosystem such as tokens used to access services** ... In such case, if the tokens do not
> provide any financial returns comparable to financial instruments (e.g. dividends or interest
> payments) and are lacking the element of pertaining to a class of securities, **then the tokens
> should not be qualified as transferable securities. This reasoning would apply even if such
> tokens were bought by investors with the expectation of profit due to their potential
> appreciation in value.**"

> **Aynı kuralın operatif hali (verbatim, Guideline 62):** "although a utility token may be
> accompanied by governance rights (i.e. governance crypto-assets), it should not replicate the
> rights attached to financial instruments, starting with those attached to transferable
> securities within the meaning of MiFID II. The same applies to crypto-assets accompanied by an
> expectation of profits. National competent authorities and financial market participants
> should therefore consider that **such expectation of a future profit should not in itself be
> sufficient to qualify a crypto-asset as a financial instrument** in accordance with MiFID II."

> **Finansal haklar testi (verbatim, footnote 56):** "In contrast to traditional shares, **a
> utility token should give neither financial rights that would be related to a company's
> profits, capital, or liquidation surpluses** - and thus representing an ownership position in a
> company's capital ... **nor voting rights** which would lead the investor to participate to the
> company's decision-making process..."

> **Protokol yönetişimi = hisse hakkı DEĞİL (verbatim, §22):** "crypto-assets that would grant
> **governance rights solely on technical matters and/or operational changes, such as protocol
> upgrades and fee adjustments**, without giving holders any influence over corporate governance
> decisions, **should not confer rights equivalent to shares** and should be distinguished from
> securities that provide traditional shareholder powers."

> **Değerlendirme SIRASI ve "öz, etiketten önce" (verbatim, Guideline 9, §74–75):** "when
> determining whether a crypto-asset has hybrid characteristics should **first evaluate if the
> crypto-asset meets the criteria of a financial instrument. If the hybrid token displays
> features of a financial instrument, such nature should take precedence** in its classification.
> This assessment should be the **primary focus before considering alternative classifications,
> such as utility tokens.**" + "should **prioritise assessing a crypto-asset's inherent attributes
> over the labels provided by issuers**, especially for hybrid tokens whose functions or
> attributes might evolve during their life-cycle..."

> **Transfer edilemeyenler (verbatim, Guideline 63):** "crypto-assets that are non-transferable to
> other holders and that are only accepted either by the issuer or by the offeror do not fall
> within the scope of MiCA" (Recital 17 ile uyumlu — bkz. §3.2).

> **MiCA muafiyeti MiFID II'yi kaldırmaz (verbatim, Guideline 66):** "regardless of the
> exemptions under MiCA, if [crypto-assets] meet the criteria of financial instruments they will
> be subject to MiFID II and other relevant EU regulations."

**KÖK v2'ye uygulama (TAMGA analizi) — bu, kullanıcının temel sorusuna DOĞRUDAN yanıttır:**
- Kullanıcının sorduğu çerçeve: token "kâr beklentisi olmayan" saf utility/compute token. ESMA
  **bunu açıkça yanıtlıyor:** bir tokenin "transferable security" (menkul kıymet) sayılması için
  **finansal haklar** (kâr payı, faiz, sermaye/likidasyondan pay, şirket yönetimine oy hakkı)
  gerekir; **yalnızca değer artışı beklentisi YETERLİ DEĞİLDİR.**
- KOK: temettü/faiz **yok**, sermaye/likidasyon hakkı **yok**, şirket yönetimine oy hakkı **yok**
  (varsa bu yalnızca "protocol upgrades and fee adjustments" gibi **teknik** konulardır →
  ESMA'ya göre hisse hakkı doğurmaz). **→ KOK bir finansal araç (transferable security) olarak
  nitelenmemelidir** — alıcılar fiyatta artış umsa bile.
- **İki uyarı:** (i) **Değerlendirme sırası**: finansal araç testi ÖNCE yapılır, "utility token"
  sonra düşünülür (Guideline 9). Yani KOK'un "utility" olduğu iddiası, önce finansal araç
  olmadığının gösterilmesine bağlıdır. (ii) **"Öz, etiketten önce"**: ESMA whitepaper'daki
  "utility token" ifadesine değil, tokenin **gerçek özelliklerine** bakar — özellikleri
  "evolving" olan hybrid tokenlar için bu önemlidir. KOK'un fee-burn + compute-payment işlevi,
  bir **finansal araç özelliği** (getiri/vade/teminat) taşımamalıdır.
- **MiCA muafiyeti + MiFID II etkileşimi:** KOK bir finansal araç değilse MiCA uygulanır
  (MiFID II değil). Eğer bir gün finansal araç özellikleri kazanırsa (örn. getiri vaadi),
  **MiCA'daki muafiyetler MiFID II'yi kaldırmaz** (Guideline 66).

> **Article 2(5) dayatma notu (MiCA metninden, BİRİNCİL):** "By **30 December 2024**, ESMA
> shall ... issue guidelines in accordance with Article 16 of Regulation (EU) No 1095/2010 on the
> conditions and criteria for the qualification of crypto-assets as financial instruments." —
> *ESMA bu yükümlülüğü yukarıdaki 17 Aralık 2024 tarihli Final Report ile yerine getirmiştir.*

### 3.5 Uygulama durumları — 2026-09 itibariyle TAM UYGULAMA (BİRİNCİL)

> **Nihai hükümler (verbatim):** "1. This Regulation shall **enter into force on the twentieth
> day following that of its publication** in the Official Journal of the European Union.
> 2. **This Regulation shall apply from 30 December 2024.** 3. By way of derogation from
> paragraph 2, **Titles III and IV shall apply from 30 June 2024.** 4. By way of derogation
> from paragraphs 2 and 3 ... Articles 2(5), 3(2), 6(11) and (12), ... shall apply from
> **29 June 2023**." — *Aynı Regulation, nihai hükümler.* ("Done at Brussels, 31 May 2023";
> OJ'de 9.6.2023'de yayımlandı → yürürlüğe giriş 29 Haziran 2023'tür.)

**2026-09 durumu (TAMGA):** MiCA Eylül 2026 itibariyle **~21 aydır tam uygulanıyor**.
Title II (utility token/whitepaper rejimi) ve Title V (CASP yetkilendirme) **30 Aralık
2024**'ten; Title III/IV (ART/EMT ihraççı yetkilendirme) **30 Haziran 2024**'ten beri.

> **Kapsam (Article 2(1)):** "This Regulation applies to natural and legal persons and certain
> other undertakings that are engaged in the issuance, offer to the public and admission to
> trading of crypto-assets or that provide services related to crypto-assets in the Union."
> **Dışlamalar:** Article 2(3) — "This Regulation does not apply to crypto-assets that are
> **unique and not fungible** with other crypto-assets"; Article 2(4) — finansal araçlar,
> mevduatlar, fonlar, securitisation pozisyonları, sigorta/emeklilik ürünleri vb.

> **Geçiş hükümleri (Recital 113):** "In order to avoid disrupting market participants ...
> issuers of such crypto-assets should be exempt from the obligation to publish a crypto-asset
> white paper and certain other requirements of this Regulation. However, certain obligations
> should apply when such crypto-assets were **admitted to trading before the date of
> application** of this Regulation."

**CASP açısından KÖK:** Eğer KÖK ekibi KOK'un **takası, custodysi veya transfer hizmetini**
AB'de profesyonel olarak sağlayacaksa **Title V kapsamında CASP yetkilendirmesi** (Article 59)
gerekir. **Yalnızca madencilik/ihraç** CASP yetkilendirmesi gerektirmez. Tetikleyici yine
"satış/listeleme/hizmet" eylemidir.

---

## 4. GÖREV 1D — Yargı Karşılaştırması: "Kâr beklentisi OLMAYAN saf utility/compute token için LİSANS gerekir mi?"

### 4.1 İsviçre (FINMA / DLT Act / FINMA ICO Guidelines) — BİRİNCİL

> **Yasal çerçeve:** "The Federal Act on the Adaptation of Federal Legislation to Developments
> in Digital Ledger Technology (DLT Act) and the associated blanket ordinance **came into force
> on 1 August 2021**. With the DLT Act, Switzerland has created legal certainty for tokenised
> assets and trading venues. The Act enables the issuance of securities on blockchain and the
> licensing of trading venues for this purpose..." — *Kaynak:* Swiss State Secretariat for
> International Finance (SIF), "DLT / blockchain / tokenisation",
> https://www.sif.admin.ch/en/dlt-blockchain-en (**BİRİNCİL; erişim 20 Eylül 2026.**)
> Not: DLT Act'ın ledger-based securities kısmı **1 Şubat 2021**'de, geri kalanı **1 Ağustos
> 2021**'de yürürlüğe girdi (aynı sayfadaki 18 Haziran 2021 / 11 Aralık 2020 basın bültenleri).

> **2025–2026 gelişmesi (actual):** "**22 October 2025** Federal Council moves forward with
> stablecoins and crypto: consultation launched — During its meeting on 22 October 2025, the
> Federal Council initiated the consultation on an amendment to the Financial Institutions Act.
> ... The consultation will run until **6 February 2026**." — *Aynı SIF sayfası.* (MiCA ile
> uyumlu stablecoin/kripto çerçevesini güçlendirme çalışması.)

> **Utility token sınıflandırması (BİRİNCİL):** "Utility tokens will not be treated as
> securities if **their sole purpose is to confer digital access rights to an application or
> service** and if the utility token can actually be used in this way at the point of issue. In
> these cases, the underlying function is to grant the access rights and the connection with
> capital markets, which is a typical feature of securities, is missing." — *Kaynak:* FINMA,
> "Guidelines for enquiries regarding the regulatory framework for initial coin offerings
> (ICOs)", **yayımlanma: 16 Şubat 2018**, s. 5,
> https://www.finma.ch/en/~/media/finma/dokumente/dokumentencenter/myfinma/1bewilligung/fintech/wegleitung-ico.pdf?la=en
> (**BİRİNCİL — 11 sayfalık PDF bu oturumda çekildi.**)

> **Yatırım amcı varsa:** "If a utility token additionally or only has an investment purpose at
> the point of issue, FINMA will treat such tokens as securities (i.e. in the same way as asset
> tokens)." — *Aynı rehber, s. 5.*

> **Menkul kıymet sayılırsa LİSANS:** "Underwriting and offering tokens constituting
> securities of third parties publicly on the primary market, is, if conducted in a
> professional capacity, **a licensed activity** (Art. 3 para. 2 SESTO)." — *Aynı rehber, s. 6.*

> **AML açısından (KRİTİK nüans):** "The issuing of payment tokens constitutes the issuing of
> a means of payment subject to this regulation **as long as the tokens can be transferred
> technically on a blockchain infrastructure**. ... **In the case of utility tokens,
> anti-money laundering regulation is not applicable as long as the main reason for issuing the
> tokens is to provide access rights to a non-financial application of blockchain technology**
> (see Art. 2 para. 2 let. a no. 3 AMLO, FINMA Circ. 11/1 'Financial intermediation under
> AMLA' margin no. 13 et seq.)." — *Aynı rehber, s. 7.*

**İsviçre yanıtı (TAMGA):** **Saf utility token için LİSANS GEREKMEZ** — menkul kıymet
sayılmadığı sürece FINMA lisansı (bankacılık/komisyonculuk) gerekmez. **İki uyarı:** (1) AML
istisnasının koşulu tokenin **finansal OLMAYAN** uygulamaya erişim sağlamasıdır; KOK'un
**compute ödemesi/ödeme aracı** işlevi bunu tartışmalı kılar — "payment token"a yaklaştıkça
AMLA kapsamına girme (SRO üyeliği veya doğrudan FINMA denetimi) riski doğar. (2) "sole purpose
... digital access rights" ve "**at the point of issue**" koşulu: tokenin ihraç anında
işlevsel olması gerekir (testnet öncesi token buna uymaz).

### 4.2 Singapur (MAS / Payment Services Act 2019) — BİRİNCİL

> **DPT tanımı (verbatim):** "'digital payment token' means any digital representation of value
> (other than an excluded digital representation of value) that — (a) is expressed as a unit;
> (b) is not denominated in any currency, and is not pegged by its issuer to any currency;
> **(c) is, or is intended to be, a medium of exchange accepted by the public, or a section of
> the public, as payment for goods or services or for the discharge of a debt;** (d) **can be
> transferred, stored or traded electronically**; and (e) satisfies such other characteristics
> as the Authority may prescribe;" — *Kaynak:* Payment Services Act 2019, Section 2 yorumlar
> (**Act 1 of 2021 ile değişik, yürürlük 04/04/2024**),
> https://sso.agc.gov.sg/Act/PSA2019 (**BİRİNCİL — Singapore Statutes Online; bu oturumda
> erişildi.**)

> **DPT hizmeti:** "'digital payment token instrument' and 'digital payment token service'
> have the meanings given by **Part 3 of the First Schedule**" — *Aynı bölüm.*

> **Lisans zorunluluğu (interpretasyon maddesinden, verbatim):** "'exempt payment service
> provider', in respect of any payment service, means a person that is exempt under section
> 13(1) from **the requirement under section 5(1) to have in force a licence that entitles the
> person to carry on a business of providing that payment service**" — *Aynı kaynak.*
> (**Not:** Section 5(1)'in operatif metni SSO'nun ayrı alt-sayfasında olduğundan bu oturumda
> doğrudan alıntılanamadı; yukarıdaki atıf lisans zorunluluğunun **birincil kanıtıdır**. Bir
> sonraki oturumda Section 5(1) metni doğrudan alınmalıdır.)

**Singapur yanıtı (TAMGA):**
- **KOK büyük ihtimalle DPT'dir:** birim şeklinde ifade edilir, bir para birimine sabitli
  değildir, "goods or services" (compute) ödemesi olarak kullanılması amaçlanmıştır ve
  elektronik olarak transfer edilebilir → DPT tanımına açıkça uyar.
- **Fakat lisansa tabi olan DPT *hizmetleridir* (takas/custody), ihraç/madencilik DEĞİL.**
  PSA'nın lisanslanabilir ödeme hizmetleri (money-changing, domestic/cross-border money
  transfer, account issuance, e-money issuance, merchant acquisition, **DPT service = DPT
  takası ve custodysi**) arasında **"token ihraç etme" veya "madencilik" yoktur**. Dolayısıyla:
  **saf utility/compute token ihraç eden (satmayan) bir proje için PSA lisansı gerekmez**;
  ancak KOK takas/custody/transfer hizmetlerini Singapur'da sağlarsa **DPT lisansı** (major /
> standard payment institution) gerekir.
- **SFA açısından:** token "capital markets product" değilse SFA lisansı da gerekmez. MAS'ın
  **"A Guide to Digital Token Offerings"** rehberi bu ayrımı yapar — **BİRİNCİL Kaynakla
  ÇÖZÜLDÜ (24 Eylül 2026):**

> **Kaynak (BİRİNCİL, resmi MAS dokümanı):** Monetary Authority of Singapore, **"A GUIDE TO
> DIGITAL TOKEN OFFERINGS"**, **[Last updated on 30 November 2018]**, 23 sayfa, **erişim 24
> Eylül 2026, HTTP 200** — IOSCO arşivi üzerinden (resmi mas.gov.sg sürümü bu oturumda 404):
> https://www.iosco.org/library/ico-statements/Singapore%20-%20MAS%20-%20A%20Guide%20to%20Digital%20Token%20Offerings%20-%20updated%20Nov%2030%202018.pdf
> *(⚠ Sürüm notu: Bu **30 Kasım 2018** tarihli sürümdür; daha yeni bir **Mayıs 2020** sürümünün
> var olduğu ikincil kaynaklardan bilinmektedir (ANU Tech Policy Atlas kaydı). Bu dokümandaki
> alıntılar 2018 sürümüne aittir.)*

> **MAS'ın testi (verbatim, §2.1–2.2):** "Offers or issues of digital tokens may be regulated by
> MAS if the digital tokens are **capital markets products** under the SFA. Capital markets
> products include any securities, units in a collective investment scheme, derivatives contracts
> and spot foreign exchange contracts for purposes of leveraged foreign exchange trading. ...
> **MAS will examine the structure and characteristics of, including the rights attached to, a
> digital token** in determining if the digital token is a type of capital markets products under
> the SFA."

> **★ EN KRİTİK BULGU — MAS'ın compute-rental case study'si KÖK'ün tam modelidir (verbatim,
> Case study 1):** "Company A plans to set up a platform to enable **sharing and rental of
> computing power** amongst the users of the platform. Company A intends to offer digital tokens
> ("Token A") ... **Token A will give token holders access rights to use Company A's platform.
> The token can only be used to pay for renting computing power provided by other platform
> users.** Token A will not have any other rights or functions attached to it and **is not or is
> not intended to be, a medium of exchange accepted by the public**, or a section of the public,
> as payment for goods or services or for the discharge of a debt."
> **Sonucu (verbatim):** "A holder of Token A will only have rights to access and use Company A's
> platform, and the right to use Token A to pay for rental of computing power provided by other
> users. Token A will not provide its holder any other rights or functions attached to it.
> Hence, **Token A will not constitute capital markets products under the SFA.**" ... "Company A's
> offer of Token A will **not be subject to any requirement under the SFA or the FAA**. However,
> Company A must abide by all Singapore laws, including the CDSA, the TSOFA and the UN
> Regulations, in the conduct of its business." ... "Token A will **not be considered a digital
> payment token under the PSB** as it is not or is not intended to be, a medium of exchange
> accepted by the public..."

> **MAS'ın etiket reddi (verbatim, §4.1–4.2):** "The illustrations in the case studies are also
> not exhaustive and **deliberately avoid labelling using terms like 'utility token' or
> 'stablecoin'**." ... "When applying the law to your case, you and your legal advisers should
> **look beyond labels and examine the features and characteristics of each token.**"

**SFA analizi — KÖK v2'ye uygulama (TAMGA):**
- MAS'ın **Case study 1'i KÖK'ün U-katmanıyla neredeyse birebir aynıdır**: kullanıcılar arasında
  **compute gücü paylaşımı/kiralanması** platformu + token yalnızca platforma erişim ve compute
  ödemesi için + başka hak/işlev yok. MAS bu token için **"capital markets product DEĞİL"**
  der → SFA/FAA yükümlülüğü **yok**.
- **KÖK ile Token A arasındaki TEK yapısal fark:** Token A "kamu tarafından bir takas aracı
  olarak kabul edilmemesi" koşuluna bağlıyken, KÖK **ikincil piyasada işlem görecek** ve
  "medium of exchange accepted by the public" olabilir. Bu, KOK'u **DPT tanımına** sokar
  (PSA §2(1)(c)) — **fakat DPT lisansını gerektiren yine *hizmetlerdir* (takas/custody), ihraç
  değil**; yukarıdaki PSA analizi geçerliliğini korur. SFA/FACA açısından ise transfer
  edilebilirlik tek başına "capital markets product" yaratmaz (§2.2 testi haklara bakar).
- **Net sonuç:** Singapur'da saf utility/compute token **ihraç etmek** SFA/FAA/PSA **lisansı
  gerektirmez**; yalnızca KOK'un **takas/custody/transfer hizmetleri** Singapur'da
  sağlanırsa DPT lisansı gerekir.
- **2025–2026 gelişmesi (doğrulanmamış):** Singapur'un PSA'yı yeni **Financial Institutions and
  Services Act (FISA)** ile ikame etme çalıştığı yönündeki bilgi **bu oturumda doğrulanamadı;
  BULUNAMADI olarak işaretlendi**; bir sonraki oturumda MAS üzerinden teyit edilmelidir.

### 4.3 BAE / ADGM (FSRA) — BİRİNCİL Kaynakla ÇÖZÜLDÜ (24 Eylül 2026)

**Kaynak (BİRİNCİL):** ADGM FSRA, "Guidance – Regulation of Virtual Asset Activities in
ADGM" (sürüm **VER07.100625**), 55 sayfalık PDF. Erişim: 24 Eylül 2026, HTTP 200.
https://www.adgm.com/documents/legal-framework/guidance-and-policy/fsra/guidance-virtual-asset-activities-in-adgm-20231218.pdf

> **(a) Utility token = emtia, menkul kıymet DEĞİL (verbatim):** "'Utility Tokens' — **Treated
> as commodities and, therefore, not deemed Specified Investments under FSMR.** (e.g., tokens
> which can be redeemed for access to a specific product or service, typically provided using
> a DLT platform, do not exhibit the features and characteristics of a regulated investment /
> instrument under FSMR)."

> **(b) Spot işlem = düzenli faaliyet DEĞİL (verbatim):** "**Unless such Utility Tokens are
> caught as Accepted Virtual Assets, spot trading and transactions in Utility Tokens do not
> constitute Regulated Activities**, activities envisaged under a Recognition Order (e.g., those
> of a Recognised Investment Exchange or Recognised Clearing House), or activities envisaged
> under MKT."

> **(c) VA Framework İHRAÇLARI kapsamıyor (verbatim, KRİTİK):** "For clarification, **the
> Virtual Asset Framework does not apply to: a) initial token or coin offerings (ICOs),
> (whether Digital Securities or Utility tokens), or other capital formation/ capital raising
> purposes.** For details of FSRA's regulatory treatment of ICOs, Digital Securities and
> utility tokens please refer to the FSRA's ICO Guidance and Digital Securities Guidance;"

> **(d) Beş VA Regulated Activity (verbatim liste) — İHRAÇ YOK:** "Dealing in Investments as
> Principal; Dealing in Investments as Agent; Arranging Deals in Investments; Providing Custody;
> and Operating a Multilateral Trading Facility". **İhraç yalnızca FRT'ler için ayrı bir
> Regulated Activity'dir:** "Issuing a FRT is a distinct Regulated Activity in ADGM." (FRT =
> Fiat Referenced Token = stablecoin; KÖK bunun değildir.)

> **(e) "Virtual Asset" tanımı (verbatim):** "'Virtual Asset' means a digital representation of
> value that can be digitally traded and functions as (1) a medium of exchange; and/or (2) a
> unit of account; and/or (3) a store of value, but does not have legal tender status in any
> jurisdiction. A Virtual Asset is a) neither issued nor guaranteed by any jurisdiction, and
> fulfils the above functions only by agreement within the community of users of the Virtual
> Asset; b) distinguished from Fiat Currency and E-money; and c) not a Specified Investment,
> Fiat-Referenced Token or Spot Commodity."

> **(f) AVA rejimi — lisanslı kişileri bağlar (verbatim):** "COBS Rule 17.2.1 provides that an
> Authorised Person conducting any VA Regulated Activity **shall not conduct such Regulated
> Activity with a Virtual Asset which is not an Accepted Virtual Asset.** An Authorised Person
> is obliged to assess each Virtual Asset it proposes to use against the criteria outlined in
> COBS Rule 17.2.2 ... [and] ... notify the FSRA upon completion of that assessment no later
> than five Business Days prior to using the Virtual Asset."

**ADGM yanıtı (TAMGA analizi):**
- **Saf utility/compute token İHRAÇ ETMEK için FSRA LİSANSI GEREKMEZ.** Üç bağımsız gerekçe
  (hepsi yukarıdaki verbatim pasajlarda): (1) VA Framework "does not apply to ... ICOs ...
  Utility tokens"; (2) utility tokenlar commodity muamelesi görür, Specified Investment
  değildir; (3) "issuing" beş VA Regulated Activity'den hiçbirinde yoktur (yalnızca FRT için
  ayrı bir faaliyettir).
- **KÖK için iki koşullu uyarı:** (i) KOK compute ödemesi olarak kullanıldığı için "medium of
  exchange" fonksiyonunu taşır → "Virtual Asset" tanımına girer. **Bu, ihraççı için değil,
  ADGM'deki lisanslı kişiler içindir:** bir Authorised Person KOK'da dealing/custody/MTF
  yapacaksa **AVA değerlendirmesi** (COBS 17.2.2 kriterleri) + FSRA'ya 5 iş günü önceden
  bildirim zorunluluğu vardır. (ii) Dubai ana karasındaki **VARA** bu FSRA guidance'ı
  kapsamında değildir (ADGM ≠ Dubai); VARA'nın 2025–2026 durumu bu oturumda **BULUNAMADI**.
- **Not:** Bu guidance ADGM'nin **kendi** ICO guidance'ına atıf yapar ("FSRA's ICO Guidance
  and Digital Securities Guidance") — o belgenin tam metni bu oturumda çekilemedi, fakat
  yukarıdaki (a)–(c) pasajlar utility-token ihraçı için **doğrudan** ve **yeterli** bir cevap
  vermektedir.

### 4.4 El Salvador (CNAD) — BİRİNCİL Kaynakla ÇÖZÜLDÜ (24 Eylül 2026)

**Kaynak (BİRİNCİL):** **Ley de Emisión de Activos Digitales**, **Decreto N.° 643** (Asamblea
Legislativa de la República de El Salvador; San Salvador'da **11 Ocak 2023** tarihinde onaylandı),
CNAD'ın resmi kütüphanesinden PDF. Erişim: 24 Eylül 2026, HTTP 200.
https://cnad.gob.sv/wp-content/uploads/2024/08/1.-Ley-de-Emision-de-Activos-Digitales-DL-643.pdf
(*Yasayı doğrulayan ikinci kaynak:* asamblea.gob.sv Decreto N.° 643 PDF'i; bu oturumda bağlantı
vermedi (HTTP 000).)

> **(a) Dijital varlık = menkul kıymet (título valor) DEĞİL (verbatim, Art. 3):** "Un activo
> digital es una representación digital que puede almacenarse y transferirse electrónicamente,
> utilizando un sistema de Tecnología de Registro Distribuida, o tecnología similar o análoga,
> en la cual los registros se encuentran enlazados y cifrados para proteger la seguridad y
> privacidad de las transacciones." ... "**Los activos digitales no se consideran títulos valores
> y por lo tanto no serán aplicables en ningún aspecto las disposiciones referentes a los títulos
> valores**, contenidas en el Código de Comercio, ni tampoco las establecidas en la Ley del
> Mercado de Valores, en la Ley de Títulos Valores Electrónicos, en la Ley de Anotaciones
> Electrónicas de Valores en Cuenta o en la Ley de Inversiones."

> **(b) Utility-token İSTİSNASI (verbatim, Art. 4(c)) — çok DAR:** "Las disposiciones de esta
> Ley no son aplicables a: ... c) **Los activos digitales que únicamente pueden ser intercambiados
> por un bien o servicio que es provisto por el emisor de ese activo digital o por un número
> limitado de proveedores de ese bien o servicio;** d) Activos digitales que no pueden ser
> negociados o intercambiados."
> *(Yani: yalnızca ihraççının (veya sınırlı sayıda sağlayıcının) mal/hizmeti ile değiştirilebilen
> tokenler yasanın kapsamı dışındadır.)*

> **(c) "Token" tanımı (verbatim, Art. 5(z)):** "Token: Es un activo digital que es utilizado
> como unidad de cuenta en una red, basándose en la Tecnología de Registro Distribuido o una
> similar o análoga."

> **(d) PUBLİK TEKLİF İÇİN YETKİLENDİRME ZORUNLU (verbatim, Art. 26 — KRİTİK):** "**Toda oferta
> pública de activos digitales deberá cumplir con la habilitación de la misma**, para lo cual,
> como etapa previa, las entidades certificadoras deberán realizar un análisis integral de los
> requisitos de dicha oferta pública, contemplados en la Ley, reglamentos, instructivos, normas
> técnicas, guías y cualquier normativa emitida por la Comisión Nacional de Activos Digitales.
> Posteriormente, los certificadores deberán emitir un informe que contenga su análisis de la
> viabilidad de la oferta pública propuesta, ya sea favorable o desfavorable, que en todo caso
> presentarán ante la Comisión. **Únicamente los informes favorables se considerarán
> certificados.**"

> **(e) İhraççıların yükümlülükleri (Art. 22):** "Los emisores, incluyendo los que emitan monedas
> estables, podrán realizar las ofertas públicas que esta Ley regula, siempre y cuando cumplan
> con los siguientes requisitos: a) ... descripción general de su negocio ... y domicilio; b)
> Indicar el LRU de su sitio web principal; c) Identificar claramente cuáles son las
> jurisdicciones, países o territorios en donde realizan sus operaciones; ..."

> **(f) CNAD (Art. 6):** "Créase la Comisión Nacional de Activos Digitales ... como una
> institución de derecho público con personalidad jurídica y patrimonio propio, de carácter
> técnico, con autonomía económica, financiera y administrativa ... La Comisión ... se
> relacionará con el Órgano Ejecutivo a través del Ministerio de Economía."

> **(g) Yürürlük (Art. 47):** "El presente Decreto entrará en vigencia **ocho días después de su
> publicación en el Diario Oficial**." (Onay tarihi: San Salvador, 11 Ocak 2023.)

**El Salvador yanıtı (TAMGA analizi) — DİĞER ÜÇ YARGIDAN FARKLI:**
- **Dijital varlıklar menkul kıymet değildir** (Art. 3 açıkça título valor olmadığını belirtir) —
  yani bu bir **menkul kıymet lisansı** rejimi değildir.
- **ANCAK yasa, dijital varlıklar için ÖZEL bir yetkilendirme rejimi yaratmıştır:** her **public
  offer** (oferta pública), CNAD tarafından **habilitación** (yetkilendirme) gerektirir ve bu,
  bir **sertifikatörün olumlu raporuna** bağlıdır (Art. 26). İhraççılar ayrıca Art. 22'deki
  yükümlülükleri (iş tanımı, web sitesi, faaliyet yargıları) sağlamak zorundadır.
- **KÖK v2 için sonuç:** KOK **transfer edilebilir** ve ikincil piyasada işlem göreceği için
  Art. 4(c) istisnasına **girmez** ("únicamente pueden ser intercambiados por un bien o
  servicio" — yalnızca ihraççının mal/hizmetiyle değiştirilebilen tokenler). Dolayısıyla
  KOK'un El Salvador'da bir **oferta pública**'sı CNAD habilitación'ı gerektirir.
- **Fair-launch madencilik açısından (TAMGA çıkarsaması, doğrulanmamış):** Yasanın Art. 4'ünde
  MiCA'daki (Art 4(3)(b)) gibi açık bir **madencilik ödülü istisnası YOKTUR**. Yasa
  "emisores" (ihraççılar) ve "ofertas públicas" (kamusal teklifler) düzenler. Fair-launch
  madencilik ödülünün bir "oferta pública" sayılmayacağı (satış değil, kazanım olduğu için)
  **savunulabilir** — bu, SEC Protocol Mining yorumu ve MiCA Art 4(3)(b) ile **paralel** bir
  argümandır — **fakat bu yoruma dayalıdır ve El Salvador doktrini/uygulamasıyla doğrulanmamıştır.**
- **Net kontrast:** İsviçre / Singapur / ADGM'de saf utility token ihraçı için lisans
  **gerekmezken**, El Salvador'da bir **habilitación rejimi** gerekir. Bu, "en az sorunlu yargı"
  seçiminde belirleyici bir farktır.

### 4.5 Karşılaştırma tablosu (kâr beklentisi OLMAYAN saf utility/compute token İHRAÇ etmek)

| Yargı | Saf utility token menkul kıymet mi? | İhraç için LİSANS gerekir mi? | Birincil dayanak | Güven |
|---|---|---|---|---|
| **ABD (SEC 2026)** | Hayır — "digital commodity"; ama **dağıtım + vaadler** belirleyici | Menkul kıymet lisansı **gerekmez** (Protocol Mining yorumu); kâr vaadiyle satış = investment contract | 33-11412 (17.03.2026); FR teklifi (21.08.2026) | **Yüksek** (birincil) |
| **AB (MiCA)** | "utility token" menkul kıymet değil; crypto-asset olarak MiCA'ya girer | Whitepaper **gerekmez** (Art 4(3)(b) madencilik) — **AMA listelenme niyeti muafiyeti düşürür (Art 4(4))** | Reg (EU) 2023/1114 Art 4 | **Yüksek** (birincil) |
| **İsviçre** | Hayır ("sole purpose ... digital access rights") | **Gerekmez** (menkul kıymet değilse); AML istisnası ancak "non-financial application" ise | FINMA ICO Guidelines (16.02.2018) | **Yüksek** (birincil; 2018 tarihli — güncelleme kontrolü gerek) |
| **Singapur** | DPT tanımına girer (ödeme aracı) ama menkul kıymet değil | **Gerekmez** (ihraç/madencilik lisanslı hizmet değil); takas/custody **ister DPT lisansı** | PSA 2019 s2 + First Schedule Part 3 | **Yüksek** (birincil) |
| **BAE / ADGM** | Hayır — utility token "**Treated as commodities**", Specified Investment değil | **Gerekmez** — "the Virtual Asset Framework does not apply to ... ICOs ... Utility tokens"; "issuing" 5 VA Regulated Activity'de yok | FSRA Guidance VER07.100625 (24.09.2026) | **Yüksek** (birincil) |
| **El Salvador** | "no se consideran títulos valores" (menkul kıymet değil) — **özel yasa rejimi** | **GEREKİR** — "Toda oferta pública ... deberá cumplir con la habilitación" (Art. 26) + sertifika raporu; KOK, Art. 4(c) "únicamente" istisnasına girmez (transfer edilebilir) | Decreto N.° 643 (11.01.2023), CNAD | **Yüksek** (birincil) |

---

## 5. GÖREV 1E — Token Burning: Menkul Kıymet / Vergi Sorunu

### Durum: KISMEN ÇÖZÜLDÜ (24 Eylül 2026) — ikincil hukuk yorumu + birincil çerçeve

**Önemli kaynak-notu:** Token burning üzerine **birincil** bir yasa/mahkeme kaynağı (SEC
kararı, ESMA görüşü, resmi rehber) bu konuda **bulunamadı** — alan henüz doğrudan düzenlenmemiş
görünmektedir. Aşağıda (A) birincil SEC yorumundan **çıkarılan** çerçeve, (B) **ikincil hukuk
yorumu** (hukuk teknoloji blog'ları — güvenilirliği açıkça belirtilmiştir), (C) vergi açısından
**hâlâ BULUNAMADI** kısımları yer alır.

**A. SEC (ABD) açısından — birincil 33-11412'den ÇIKARIM (yorum, hukuk görüşü değil):**
Yorum, menkul kıymet analizini **dağıtım işlemine** (offer/sale) bağlar (§2.4). **Burn'un
kendisi bir "offer and sale" değildir**; bir tokeni yok etme işlemidir. 33-11412'de "burned"
kelimesi yalnızca teknik örneklerde geçer: "When redeemed, the Staking Receipt Tokens are
'burned,' which is a process through which the Staking [Receipt Tokens are destroyed]" (fn 116)
ve Redeemable Wrapped Token örneği (fn 117). **Bu çıkarım TAMGA'ya aittir; resmi bir SEC
görüşü değildir.**

**B. İkincil hukuk yorumu — "burn, security taint'i kaldırmaz, PEKİŞTİRİR" argümanı:**

> **Kaynak 1 (ikincil, hukuk-teknoloji blog'u — orta düşük güvenilirlik):** "Why 'Burn'
> Mechanisms Fail to Remove a Token's Security Taint", ChainScore Labs
> https://chainscorelabs.com/blog/crypto-regulation-global-landscape-and-trends/sec-enforcement-and-securities-law/why-burn-mechanisms-fail-to-remove-a-tokens-security-taint
> (**erişim 24 Eylül 2026; yazar/tarih belirtilmemiş**)
>
> **Core thesis (verbatim):** "**Token burn mechanisms reinforce, rather than eliminate, the
> expectation of profit from a common enterprise, which is the core of the Howey Test.** Burns
> signal artificial scarcity. The protocol actively manages supply to influence price, creating
> a direct link between user participation and token value appreciation. **This is a hallmark of
> an investment contract, not a consumptive good.**"
>
> **★ KRİTİK AYRIM (verbatim) — KÖK'ün U-katmanı doğrudan buraya oturur:** "**Compare to genuine
> utility. A gas token like ETH or MATIC is consumed to execute a transaction; its burn is a
> fee for service. A governance token with a burn is a speculative asset whose mechanics are
> designed to create returns.**"
>
> Diğer argümanları (özet): "Burning is a legal fiction. The SEC's Howey Test examines the
> original investment contract, not the current token supply"; "Post-burn marketing that implies
> future profits can re-trigger the test"; ve çözüm önerisi: "Work Token model with fee capture
> & burn" + test: "Can the network survive and grow if the token price goes to zero?"

**C. KÖK v2'ye uygulama (TAMGA analizi — bu, projenin en önemli yeni içgörülerinden biri):**

Yukarıdaki **"fee for service" vs "supply constriction" ayrımı**, KÖK'ün U-katmanı için
doğrudan bir tasarım kılavuzu verir:

1. **KÖK'ün fee burn'u = "fee for service" kategorisinde tutulmalıdır** (ETH gas burn gibi):
   kullanıcı bir **compute görevi** satın alır, fee'si escrow'a girer, görev yerine gelir ve
   bir kısım **geri alınamaz şekilde** yakılır. Yanan kısım **hizmet bedelinin bir
   bileşenidir**, arz azaltma vaadi değildir. Bu, ChainScore'un "hallmark of an investment
   contract" olarak nitelediği kategorinin **dışında** kalır.
2. ** Yasal risk yüzeyi (kaçınılması gerekenler):** (i) burn mekanizmasının **fiyat artırma**
   amacıyla pazarlanması ("deflationary", "supply shock", "token price will rise") — bu,
   "reasonable expectations of profit" argümanını güçlendirir ve 33-11412 §IV.A'daki
   "representations or promises" analizine girebilir; (ii) burn sonrası "future profits"
   ima eden pazarlama "re-trigger" yapabilir (ChainScore uyarısı); (iii) burn'u bir
   "decentralization" aracı olarak sunma — "theatrical redistribution" olarak görülebilir.
3. **Doğru çerçeve:** burn = **protokol fee politikası** (görev gelirinin bir kısmının
   protokol tarafından tahsis edilemez şekilde yok edilmesi). Hatta ChainScore'un "Work Token
   model with fee capture" önerisi KÖK'ün U-katmanının **adı konmamış tanımıdır.**
4. **Yine de uyarılı:** bu argüman **hiçbir mahkeme veya SEC tarafından test edilmemiştir.**
   ChainScore'un kendisi de "burn = security taint" derken bunu bir **savunma** olarak
   sunmaz; aksine burn'ün **riskli** olduğunu söyler. KÖK, "fee for service" konumlanışını
   whitepaper'da **açıkça ve defalarca** belgelemelidir.

**D. MiCA (AB) açısından (bu oturumda doğrulandı):** MiCA tam metninde burn'a doğrudan hüküm
**bulunamadı** (yalnızca teknik örneklerde "burned/destroyed" geçer). İlgili doğrulanmış kural:
Article 4(3)'ün "offered for free" istisnasının sınırı — "a crypto-asset shall not be considered
to be offered for free where ... the offeror of a crypto-asset receives from prospective holders
of that crypto-asset **any fees, commissions, or monetary or non-monetary benefits in exchange
for that crypto-asset**". KÖK açısından: fee karşılığı compute sağlanıyorsa "free" istisnasına
girilmez; zaten KÖK için geçerli olan 4(3)(b) madencilik ödülü istisnasıdır (§3.3).

**E. Vergi açısından — ikincil yorumla KISMEN belgelendi (kesin görüş hâlâ BULUNAMADI):**

> **★ 2026-09-26 GÜNCELLEME — IRS BİRİNCİL KAYNAĞI BULUNDU ve phantom-income
> argümanını bir "çözülmemiş argüman"dan "yazılı kural" durumuna yükseltti:**
>
> **Kaynak (BİRİNCİL):** IRS, **Rev. Rul. 2023-14**, Internal Revenue Bulletin
> **2023-33**, 14 Ağustos 2023, sayfa 484 (erişim 26 Eylül 2026, **HTTP 200**).
> https://www.irs.gov/irb/2023-33_IRB · PDF: https://www.irs.gov/pub/irs-drop/rr-23-14.pdf
>
> > **Verbatim (IRS'nin kendi kuralı):** *"This revenue ruling provides that if
> > a taxpayer stakes cryptocurrency native to a proof-of-stake blockchain and
> > receives additional units of cryptocurrency as rewards when validation
> > occurs, **the fair market value of the rewards received is included in the
> > taxpayer's gross income in the taxable year in which the taxpayer gains
> > dominion and control over the rewards**."*
>
> **Neden bu KÖK için doğrudan:** KÖK'ün G katmanı PoS DEĞİL, PoW'dur — bu
> görünüşte alakasızdır. **Ama alakalıdır ve alaka şu şekildedir:** kuralın
> operatif kısmı "rewards received ... gross income ... when the taxpayer
> gains dominion and control" ifadesidir. KÖK'ün madencisi bir blok kazandığında
> **block reward'ı dominion'ına alır** — bu, kuralın öngördüğü andır. Ödül
> sonradan **burn component** içeriyorsa (KÖK'ün escrow+burn modeli), madenci
> o andaki **tüm ödülün FMV'sini** gelirine dahil etmiş olabilir; burn'un
> azalttığı kısım sonradan gerçekleşir. **İşte phantom-income burada bir
> argüman olmaktan çıkıp IRS'nin yazılı kuralına dayanır hale geliyor.**
>
> **İkinci birincil kaynak (IRS newsroom, 4 Nisan 2024, son güncelleme
> 25 Ağustos 2026, HTTP 200):**
> https://www.irs.gov/newsroom/report-income-from-transactions-involving-digital-assets-including-cryptocurrency-on-your-tax-return
> > **Verbatim:** *"Any income from transactions involving digital assets must
> > be reported on your federal tax return. Common digital assets include:
> > Convertible virtual currency and cryptocurrency Stablecoins
> > Non-fungible tokens (NFTs) **Rewards income from staking or earn programs**"*
>
> Bu, "rewards income" kategorisini IRS'nin kendi listesinde **resmen adlandırılmış
> bir gelir kategorisi** yapar — KÖK'ün block reward'ı bu kategorinin dışında
> değildir.
>
> **NE HÂLÂ BULUNAMADI (dürüst sınır):** **Burn'a ÖZEL** bir IRS görüşü hâlâ
> yoktur. Rev. Rul. 2023-14 staking reward'ları hakkındadır; aşağıdaki
> phantom-income argümanını **destekler** (dominion anı + FMV dahil etme),
> ama **burn'ün kendisini** ele almaz. Yani: madencinin ödülün TAM FMV'sini
> bildirme yükümlülüğü yazılı bir kuraldır; **burn'ün o yükümlülüğü azaltıp
> azaltmadığı** açıktır ve **hiçbir birincil kaynak bunu doğrudan cevaplamaz.**
> Aşağıdaki ikincil argüman bu boşluğu dolduruyor — ama artık birincil
> kuralın üzerine inşa edilmiş bir argüman olarak, havada asılı bir iddia
> olarak değil.

> **Kaynak 3 (ikincil, hukuk-teknoloji blog'u — orta-düşük güvenilirlik, IRS GÖRÜŞÜ DEĞİLDİR):**
> "Why Token Burning Mechanisms Create Phantom Taxable Income", ChainScore Labs
> https://chainscorelabs.com/blog/legal-tech-smart-contracts-and-the-law/taxation-of-automated-systems/why-token-burning-mechanisms-create-phantom-taxable-income
> (**erişim 24 Eylül 2026; yazar/tarih belirtilmemiş**)

**Bu kaynağın argümanı (verbatim):**
- "Token burning **is a taxable event**. When a protocol ... permanently removes tokens from
  circulation, **it increases the proportional ownership of every remaining holder**. This
  unrealized gain constitutes a **constructive receipt of income** under many tax regimes,
  creating a liability without any cash flow."
- "A protocol's native token is a **liability on its treasury's balance sheet**. When tokens are
  burned, that liability disappears, but the protocol's assets ... remain unchanged. This creates
  an accounting mismatch. ... Under accrual accounting, **destroying a liability without a
  corresponding asset reduction is booked as income.**"
- "Tax authorities like the IRS treat this as a **constructive distribution**, creating taxable
  income without any actual cash flow to the user."

**★ KRİTİK DOĞRULUK NOTU (TAMGA):** Yukarıdaki **bir argümandır, yerleşik vergi kuralı DEĞİLDİR.**
- Kaynağın kendisi bunu "**significant and unresolved conflict with existing tax frameworks**"
  olarak nitelendirir — yani çözülmemiş bir çatışma olarak sunar.
- Dayanak gösterdiği tek gerçek IRS konusu **2019 forks/airdrops guidance**'ıdır (yeni varlık
  ediniminin vergi olayı olduğu); bu **burn hakkında DEĞİLDİR**. Burn'a özel IRS görüşü **bu
  kaynakta yoktur** ve ben de **bulamadım**.
- Kaynaktaki somut sayılar ("4 million ETH burned", "$10M daily", MakerDAO "21% corporate tax")
  **bu dokümanda doğrulanmamıştır** — yalnızca kaynağın kendi iddiaları olarak rapor edilir.

**KÖK v2'ye uygulama (TAMGA analizi):**
- **Fee-for-service burn, "buyback-and-burn"den yapısal olarak farklıdır** (§5.B'deki ayrım):
  KOK yakılan kısım, kullanıcının **compute görevi satın almak için ödediği fee**'nin bir
  bileşenidir — bir tüketim işlemidir, protokolün kasadan token satın alıp yakması değildir.
  "Phantom income" argümanı en güçlü biçimde **buyback-and-burn** için geçerlidir.
- **Yine de sıfır-risk değildir:** her native-token burn'ü toplam arzı azalttığı için kalan
  tutar sahiplerinin oransal sahipliğini teknik olarak artırır; bu yüzden "constructive
  distribution" argümanı teorik olarak KOK için de ileri sürülebilir. Bu, **vergi
  danışmanına/uzman hukuk müşavirine götürülmesi gereken bir konudur**; bu doküman vergi
  tavsiyesi değildir.

> **Kaynak 2 (ikincil, DÜŞÜK güvenilirlik — "AI tarafından yazılmış" uyarısı var):** Pactria,
> "Legal Implications of Token Burn Mechanisms", **17 Ağustos 2024**,
> https://pactria.com/legal-implications-of-token-burn-mechanisms/ — **⚠ Bu kaynağın kendi
> yazar notu: "This content was written by AI. Please use trusted or official sources to
> confirm any facts."** Yalnızca **soru çerçevesi** olarak kullanılmıştır, hukuki sonuç olarak
> değil.
>
> Çerçeve olarak sorması gereken sorular (bu kaynaktan): "Determining whether token burns are
> classified as **transfers, cancellations, or redistributions** under applicable laws";
> "Complying with securities regulations if the tokens involved are deemed investment
> contracts"; "Managing AML and KYC requirements that regulate token transactions and burns";
> "Legal clarity remains limited, with many jurisdictions still developing guidance specific to
> token burn mechanisms."

**Kesin BULUNAMADI:** KÖK'ün **fee-burn mekanizması için Türk vergi hukukunda** (veya ABD/AB'de)
somut bir vergi görüşü/IRS guidance'ı/literatür **bulunamadı**. **Bir sonraki oturumda aranacak
başlıklar:** "token burn tax treatment", "EIP-1559 fee burn tax", "constructive distribution token
burn", "proof-of-burn regulation", "Türkiye'de token yakma vergi".

---

## 6. BULUNAMADI LİSTESİ (kalan 5 madde — bir sonraki oturumda tamamlanacak)

> **24 Eylül 2026 güncellemesi (4. dalga):** **MAS'ın "A Guide to Digital Token Offerings"
> rehberi ÇÖZÜLDÜ** (§4.2 — IOSCO arşivinden 30 Kasım 2018 sürümü, BİRİNCİL; **compute-rental
> case study'si KÖK'ün modeliyle birebir**). **ESMA, ADGM, El Salvador ÇÖZÜLDÜ**; **token
> burning KISMEN ÇÖZÜLDÜ**. Böylece görevlerin **tüm yüksek öncelikli boşlukları kapatıldı**.
> Kalan 5 madde düşük/çok düşük önceliklidir.

| # | Eksik veri | Neden ulaşılamadı | Önerilen sonraki adım |
|---|---|---|---|
| ~~1~~ | ~~**ADGM/FSRA**~~ | **ÇÖZÜLDÜ (24.09.2026)** — §4.3 | — |
| ~~2~~ | ~~**El Salvador**~~ | **ÇÖZÜLDÜ (24.09.2026)** — §4.4 | — |
| ~~3~~ | ~~**ESMA** qualification guidelines~~ | **ÇÖZÜLDÜ (24.09.2026)** — §3.4 | — |
| ~~4~~ | ~~**MAS "A Guide to Digital Token Offerings"**~~ | **ÇÖZÜLDÜ (24.09.2026)** — §4.2 (30.11.2018 sürümü, IOSCO arşivi) | — |
| ~~6~~ | ~~**Token burning** menkul kıymet~~ | **KISMEN ÇÖZÜLDÜ (24.09.2026)** — §5 | — |
| 5 | **Singapur FISA** (PSA'nın ikame edilmesi) 2025–2026 | Arama motorları kapalı | MAS / SSO üzerinden teyit |
| 6 | **Token burning — VERGİ** (ABD IRS / AB / Türkiye'de fee-burn vergi görüşü) | **BİRİNCİL IRS KAYNAĞI BULUNDU (26.09.2026)** — Rev. Rul. 2023-14 (IRB 2023-33) + IRS newsroom 04.04.2024: "rewards income" resmen adlandırılmış gelir kategorisidir ve FMV "dominion and control" anında gelir yazılır. **Burn'a ÖZEL görüş hâlâ YOK** — Rev. Rul. staking hakkındadır, burn'ü ele almaz; phantom-income argümanı artık birincil kural üzerine inşa edilir, havada değil | ~~SSRN/Google Scholar; IRS guidance~~ → **YAPILDI (kısmen)**; kalan: burn'e özel görüş (yok) |
| 7 | ~~**Torres'in 13 Temmuz 2023 kararının asıl metni**~~ | **TAMAMEN ÇÖZÜLDÜ — TAM METİN BİRİNCİL (27.09.2026)** — PDF `curl` ile indirildi (321.952 bayt, iText 7.1.6, SDNY üretimi) ve `pdftotext -layout` ile **1.802 satıra** çıkarıldı: **Document 874, 34 sayfa, 20 Civ. 10832 (AT)**. Üç karar başlığı **verbatim doğrulandı:** (1) *Institutional*: *"having considered the economic reality and totality of circumstances surrounding the Institutional Sales, the Court concludes that Ripple's Institutional Sales of XRP constituted the unregistered offer and sale of investment contracts in violation of Section 5 of the Securities Act"*; (2) *Programmatic* (≈$757.6M): *"the Court concludes that Ripple's Programmatic Sales of XRP did not constitute the offer and sale of investment contracts"* — **üçüncü Howey prong'un kayıtta kurulmadığına** karar verdi, birinci/ikinci prong'a ulaşmadı; (3) *Other Distributions*: *"did not constitute the offer and sale of investment contracts"*. **★ Programmatic-sales bulgusunun teyit edilmesi bu proje için kritikti** — borsa satışlarının menkul kıymet olmadığına dair tek güçlü ABD emsalini artık birincil metinden taşıyor; daha önce ikincil kaynaktı | ~~CourtListener docket 17643223~~ → **TAM METİN BİRİNCİL (mahkemenin kendi sunucusu)** — kalan alt-gap YOK |
| 8 | ~~**Torres'in 26 Haziran 2025 kararının asıl metni**~~ | **TAMAMEN ÇÖZÜLDÜ — TAM METİN BİRİNCİL (27.09.2026)** — **Document 989, 5 sayfa, 20 Civ. 10832 (AT)**, bir hukuk firması barındırma kopyasından (`nutter.com/assets/htmldocuments/SEC v. Ripple Labs 2025.06.26.pdf`, 196.391 bayt, yaratılış tarihi 26.06.2025 15:12) indirilip çıkarıldı. Operatif cümle verbatim: *"the parties' motion for an indicative ruling is DENIED"*; *"if jurisdiction were restored to this Court, the Court would deny the parties' request to vacate the injunction and reduce the Civil Penalty"*. **DOĞRULANAN DETAYLAR (önceki ikincil kayıtta eksik):** talep %60 indirimdi ("cut the Civil Penalty by sixty percent" — $125.035.150'den ~$50M'ye) VE "dissolve" kalıcı injunction; **U.S. Bancorp Mortgage Co. v. Bonner Mall** "exceptional circumstances" standardı uygulandı; **"parties do not have the authority to agree not to be bound by a court's final judgment"**; iki çıkış yolu: temyizi geri çekmek veya temyiz etmek ("primary route"). **★ KÖK için olan kısmı keskinleşti:** mahkeme "taraflar anlaşınca emri kaldırmak" diye bir şey olmadığını söyledi — kalıcı injunction **temyiz geri çekilse veya anlaşma onaylansa bile yürürlükte kalır**; yalnızca "exceptional circumstances" bozabilir ve Torres *"have not come close to doing so here"* dedi | ~~CourtListener / SDNY docket~~ → **TAM METİN BİRİNCİL**; kalan alt-gap YOK (not: mahkemenin kendi sunucusu yerine hukuk firması kopyası — SDNY e-filing doğrudan indirme henüz bulunamadı; belge mahkeme üretimi, başlık/ECF numarası birebir) |
| 9 | ~~**Regulation Crypto Assets teklifine gelen yorumlar / yürürlük takvimi**~~ | **BULUNDU — BİRİNCİL + CANLI (26.09.2026)** — Federal Register: **91 FR 54510–54655 (146 sayfa)**, 21 Ağustos 2026, **Release Nos. 33-11434; 34-106150; File No. S7-2026-27; RIN 3235-AN38**. **★ İKİ MUAFİYET:** (1) **4 yıllık dönemde $5M'a kadar**; (2) **her 12 ayda $75M'a kadar** — ikincisi finansal tablo + sürekli raporlama gerektirir. **★ KOŞULLU GÜVENLİ LİMAN (safe harbor):** koşullar sağlanırsa kripto varlık "investment contract"e tabi DEĞİL sayılır. **Yorumlar 20 Ekim 2026'ya kadar — HÂLÂ AÇIK (24 gün kaldı).** Önemli: hâlâ ÖNERİLEN kural, kesinleşmedi | ~~Federal Register docket S7-2026-27~~ → **YAPILDI; yorumların içeriği henüz yayımlanmadığı için okunamadı (dürüst sınır)** |
| 10 | ~~**AB Komisyonu'nun MiCA uygulama değerlendirme raporu (2025–2026)**~~ | **BULUNDU — CANLI BİRİNCİL KAYNAK (26.09.2026)** — Komisyon'un kendi sayfası: `finance.ec.europa.eu/.../targeted-consultation-review-mica-regulation_en` (HTTP 200). **Değerlendirme henüz rapor DEĞİL, AÇIK BİR İSTİŞARE'dir:** açılış **20 Mayıs 2026**, deadline **30 Eylül 2026'ye UZATILDI** (orijinali 31 Ağustos'tu), DG FISMA yürütüyor. "assess whether MiCA remains fit for purpose in light of the initial implementation and market and policy developments" — **yani değerlendirme SÜRÜYOR, sonuç raporu henüz yok**. EBA'nın resmi yanıtı da teyit edildi (EBA, 20 Mayıs 2026'da yayımlanan istişareye yanıt verdi; PDF ikili alınamadı) | ~~EUR-Lex / Commission sayfaları~~ → **YAPILDI — istişare canlı ve açık; rapor henüz yayımlanMADI (dürüst sınır: tarihi bir rapor değil, devam eden bir süreç)** |
| 11 | **MAS DTO Rehberi'nin Mayıs 2020 sürümü** (§4.2'deki alıntılar 30.11.2018 sürümüne ait) | mas.gov.sg 404; yalnızca 2018 sürümü erişilebildi | mas.gov.sg guidelines arşivi |

---

## 7. KAYNAK LİSTESİ

**Birincil kaynaklar (resmi) — bu oturumda doğrulananlar:**
1. SEC Litigation Release No. **26306** (8 Mayıs 2025) — https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26306
2. SEC Litigation Release No. **26369** (7 Ağustos 2025) — https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26369
3. SEC **Interpretive Release No. 33-11412 / 34-105020** (17 Mart 2026; etkili 23 Mart 2026),
   File No. S7-2026-09 — PDF: https://www.sec.gov/files/rules/interp/2026/33-11412.pdf ;
   özet: https://www.sec.gov/rules-regulations/2026/03/s7-2026-09
4. SEC **Proposed Rule "Regulation Crypto Assets"**, Release Nos. 33-11434; 34-106150,
   File No. S7-2026-27, RIN 3235-AN38, **Federal Register Vol. 91, No. 161, 21 Ağustos 2026,
   s. 54510** — https://www.govinfo.gov/content/pkg/FR-2026-08-21/pdf/2026-17183.pdf
5. Paul S. Atkins, "Regulation Crypto Assets: A Token Safe Harbor", **17 Mart 2026** —
   https://www.sec.gov/newsroom/speeches-statements/atkins-remarks-regulation-crypto-assets-031726
6. Paul S. Atkins, "Regulation Crypto Assets: Fit-for-Purpose Exemptions...", **18 Ağustos
   2026** — https://www.sec.gov/newsroom/speeches-statements/atkins-statement-regulation-crypto-assets-081826
7. **Regulation (EU) 2023/1114 (MiCA)**, OJ L 150, 9 Haziran 2023 —
   https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114
8. **FINMA ICO Guidelines**, **16 Şubat 2018** —
   https://www.finma.ch/en/~/media/finma/dokumente/dokumentencenter/myfinma/1bewilligung/fintech/wegleitung-ico.pdf?la=en
9. **Swiss SIF**, "DLT / blockchain / tokenisation" — https://www.sif.admin.ch/en/dlt-blockchain-en
10. **Payment Services Act 2019 (Singapur)**, konsolide metin — https://sso.agc.gov.sg/Act/PSA2019
11. **ADGM FSRA**, "Guidance – Regulation of Virtual Asset Activities in ADGM"
    (VER07.100625), **erişim 24 Eylül 2026, HTTP 200, 55 sayfa** —
    https://www.adgm.com/documents/legal-framework/guidance-and-policy/fsra/guidance-virtual-asset-activities-in-adgm-20231218.pdf
12. **El Salvador — Ley de Emisión de Activos Digitales, Decreto N.° 643** (Asamblea
    Legislativa, San Salvador, **11 Ocak 2023**), CNAD resmi kütüphanesi PDF, **erişim 24 Eylül
    2026, HTTP 200, 1618 satır** —
    https://cnad.gob.sv/wp-content/uploads/2024/08/1.-Ley-de-Emision-de-Activos-Digitales-DL-643.pdf
    *(Doğrulayıcı ikincil kaynak:* asamblea.gob.sv Decreto N.° 643 PDF'i — bu oturumda bağlantı
    vermedi; vLex ve interbiznet yansıları law metnini doğrular.)*
13. **ESMA**, "Final Report — Guidelines on the conditions and criteria for the qualification of
    crypto-assets as financial instruments", **ESMA75453128700-1323**, **17 Aralık 2024**, 49
    sayfa, **erişim 24 Eylül 2026, HTTP 200** —
    https://www.esma.europa.eu/sites/default/files/2024-12/ESMA75453128700-1323_Final_Report_Guidelines_on_the_conditions_and_criteria_for_the_qualification_of_CAs_as_FIs.pdf

**İkincil hukuk yorumu (token burning için; güvenilirliği §5'te belirtilmiştir):**
14. ChainScore Labs, "Why 'Burn' Mechanisms Fail to Remove a Token's Security Taint" (erişim
    24.09.2026; yazar/tarih belirtilmemiş; orta-düşük güvenilirlik) —
    https://chainscorelabs.com/blog/crypto-regulation-global-landscape-and-trends/sec-enforcement-and-securities-law/why-burn-mechanisms-fail-to-remove-a-tokens-security-taint
14b. ChainScore Labs, "Why Token Burning Mechanisms Create Phantom Taxable Income" (erişim
    25.09.2026; yazar/tarih belirtilmemiş; orta-düşük güvenilirlik; **IRS görüşü DEĞİL**) —
    https://chainscorelabs.com/blog/legal-tech-smart-contracts-and-the-law/taxation-of-automated-systems/why-token-burning-mechanisms-create-phantom-taxable-income
15. Pactria, "Legal Implications of Token Burn Mechanisms", **17 Ağustos 2024** (**⚠ "AI
    tarafından yazılmış" uyarısı; yalnızca soru çerçevesi olarak kullanıldı**) —
    https://pactria.com/legal-implications-of-token-burn-mechanisms/
16. **MAS (Monetary Authority of Singapore)**, "A Guide to Digital Token Offerings", **[Last
    updated on 30 November 2018]**, 23 sayfa, **erişim 24 Eylül 2026, HTTP 200** — IOSCO
    ICO-statements arşivi (resmi mas.gov.sg sürümü 404):
    https://www.iosco.org/library/ico-statements/Singapore%20-%20MAS%20-%20A%20Guide%20to%20Digital%20Token%20Offerings%20-%20updated%20Nov%2030%202018.pdf

**İkincil kaynaklar (kullanıldıkları yerde güvenilirliği belirtilmiştir):**
12. Gordon Law Group, "Partial Ripple Victory: Judge Rules That XRP Is Not a Security" (13
    Temmuz 2023; güncelleme 17 Mart 2026) — https://gordonlaw.com/learn/judge-xrp-not-security/
13. Cryptonews, "Ripple Settlement Denied as Judge Torres Rejects $50M Deal..." (26 Haziran
    2025) — https://cryptonews.com/news/ripple-settlement-denied-as-judge-torres-rejects-50m-deal-xrp-institutional-sales-remain-limited/
14. Lawfold, "Ripple SEC Lawsuit Status 2026" (17 Eylül 2026) —
    https://lawfold.com/ripple-sec-lawsuit-status-2026/ *(düşük güvenilirlik, yalnızca destekleyici)*

**v1'den taşınan ve geçerliliği koruyan bölümler:** MiCA Article 3 numaralandırma düzeltmesi
(utility token = Article 3(9)), MiCA whitepaper beyan yükümlülükleri (Art 13), v1'in Wikipedia
tabanlı Ripple zaman çizelgesi (v2'de yerini birincil SEC kaynaklarına bıraktı).

---

**Belge sürümü:** **v2.6** (25 Eylül 2026, TAMGA) — v2.5'in üzerine **token-burn VERGİ açısı
 ikincil yorumla belgelendi** (§5.E: "phantom taxable income" argümanı + doğruluk notu; kesin
 IRS/AB/TR görüşü hâlâ BULUNAMADI). Bu oturumda kapatılanlar: ADGM, El Salvador, ESMA, MAS DTO
 rehberi + token burning'in menkul-kıymet VE vergi çerçeveleri (ikincil düzeyde). Kalan 5
 BULUNAMADI maddesi §6'da (hepsi düşük öncelikli).
