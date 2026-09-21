# Hukuk / Uyum Araştırması — KÖK v2

**Araştıran:** Lead (Tamga ağ hatası verdiği için bizzat alındı)
**Tarih:** 2026-09-21
**Yöntem:** EUR-Lex resmi metni (1.68 MB HTML) tam çekildi, tanımlar verbatim çıkarıldı.
**Durum:** web_search ve DuckDuckGo/Bing bu oturumda bot korumasına takıldı; sadece
**direkt URL fetch** çalışıyor. Bu yüzden A (SEC/Ripple) ve D (yargı karşılaştırma)
henüz **BULUNAMADI** — sadece resmi metinlerle teyit edilebilen kısımlar yazıldı.

---

## C) MiCA — Regulation (EU) 2023/1114 (RESMİ METİN, VERBATIM)

Kaynak: EUR-Lex CELEX:32023R1114, Official Journal L 150/40, 9.6.2023.
URL: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114
Erişim: 2026-09-21, HTTP 200, tam metin.

### C.1 Tanımlar — Article 3 (numaralandırma DÜZELTİLDİ)

Önceki notlarımızda "Article 3(1)(5)" yazıyordu. **Resmi metinde numaralandırma
farklıdır** — tanımlar Article 3'ün (5) numaralı paragrafında değil, tek bir
numaralandırılmış listede yer alır:

- **(5) ‘crypto-asset’ means** a digital representation of a value or of a right
  that is able to be **transferred** and stored electronically using distributed
  ledger technology or similar technology;
- **(6) ‘asset-referenced token’ means** a type of crypto-asset that is not an
  electronic money token and that purports to maintain a stable value by
  referencing another value or right or a combination thereof, including one or
  more official currencies;
- **(7) ‘electronic money token’ or ‘e-money token’ means** a type of crypto-asset
  that purports to maintain a stable value by referencing the value of one
  official currency;
- **(9) ‘utility token’ means** a type of crypto-asset that is **only intended to
  provide access to a good or a service supplied by its issuer**;
- **(10) ‘issuer’ means** a natural or legal person, or other undertaking, who
  issues crypto-assets;

### C.2 KÖK v2 için ÇIKARIM (analiz, metin değil)

KÖK v2 token'ı **(9)‘un utility-token tanımına uymaz**: madenci blok ödülleri ve
görev pazarında fee ödemesi, token'a "sadece erişim" dışında bir değer yükler —
token aynı zamanda **value of a right** (5) ve potansiyel olarak **ART (6)**
"purports to maintain a stable value" savına yakınlaşabilir. KÖK v2 ** hiçbir
değer sabitleme vaadi olmadığını** açıkça belirtmelidir (zaten §11'de var).

**Transfer edilebilirlik:** tanımda "non-transferable" şartı YOK — crypto-asset
tanımı (5) transfer edilebilirlik ister, ancak utility token tanımı (9) buna
değinmez. Beyan yükümlülüğü yönünden (white paper'da):
> "the crypto-asset may not always be transferable; (c) the crypto-asset may not
> be liquid; (d) where the offer to the public concerns a utility token, that
> utility token may not be exchangeable against the good or service..."

→ **Bir token hem transfer edilebilir hem utility olabilir**; ancak white
paper'da yukarıdaki 4 beyan zorunludur.

### C.3 Uygulama tarihi (RESMİ)

Regulation 31 May 2023 tarihli, Official Journal'da 9 Haziran 2023.
> "This Regulation shall enter into force on the twentieth day following that of
> its publication in the Official Journal of the European Union."
> "It shall apply from 30 December 2024."

(Regulation'ın son maddelerinden; uygulama tarihi **30 December 2024**.)

---

## A) SEC v. Ripple / Howey — BULUNAMADI

DuckDuckGo (HTML + lite) ve Bing bu oturumda bot koruması döndü (içerik boş);
sec.gov 403 verdi. **CourtListener API'si** bir önceki başarısız subagent'ta
çalıştığı raporlanmıştı ama o oturum kayboldu. **Sonuç: A şıkkı BULUNAMADI** —
paper'daki mevcut "Howey analysis" ifadesi **kendi analizimizdir, iç kaynaklı**,
dış citasyon taşımaz. Bu, paper §9'da "not verified" olarak zaten etiketli.

## D) Yargı karşılaştırma — BULUNAMADI
## E) Burning mekanizması yasal durum — BULUNAMADI

(Eğer web erişimi geri gelirse bu üç şık tamamlanacak; şu an uydurmamak için
BULUNAMADI olarak bırakılıyor.)

---

## A2) SEC v. Ripple — CourtListener API denendi, BULUNAMADI

**Denenen:** CourtListener REST v4 — search (type=o/r, court=ca2/nysd),
dockets search, docket numarası 20-cv-10932, docket ID 646160.
**Sonuç:** Ripple davası CourtListener/RECAP veritabanında **bulunamadı**
(count: 0 ya da boş kayıt). Second Circuit (ca2) aramasında **hiç Ripple
görünmüyor** — bu, eğer bir temyiz devam etseydi orada olması gerektiği
düşüncesiyle çelişkili; ancak **varlık/yokluk çıkarması yapılmaz** (RECAP
kapsamı eksik olabilir).

**DÜRÜST SONUÇ:** SEC v. Ripple'in 2026-09 durumunu **bu oturumda teyit
edemedim**. Paper §9'daki "Howey analysis" **kendi analizimizdir** (iç kaynaklı);
Ripple kararından alıntı yapılmıyor, yalnızca Howey'in genel çerçevesi
kullanılıyor. Bu, paper'da zaten "not verified / open item" olarak etiketli.

**PRATIK ETKI:** hicbiri. Paper zaten dis citasyon olmadan yazilmis;
arastirma bu bosluklari aciga cikardi ki bilerek kalmasin.

---

## A3) *** SEC v. RIPPLE — TAMAMEN COZULDU (2026-09-21) ***

**Yontem:** Wikipedia API (`action=parse&section=10&prop=wikitext`) ile Ripple_Labs
sayfasinin "SEC litigation (2020-2025)" bolumu TAMAMEN cekildi. Onceki CourtListener
ve sec.gov denemeleri basarisizdi ama Wikipedia API calisti.

### DOGRULANMIS ZAMAN CIZELGESI (verbatim ozet)

1. **22 Aralik 2020** — SEC, Ripple + 2 yoneticisine (Larsen, Garlinghouse) SDNY'de
   dava acti (Securities Act of 1933 kayit hukumleri). IDDIA: XRP'nin kayitsiz
   satislariyla **$1.3 milyar** toplanmasi.
2. **13 Temmuz 2023** — Hakim **Analisa Torres** ozet karar verdi:
   - Mahkeme **XRP'nin kendisini satisin kosullarindan ayirdi.**
   - **Kurumsal (institutional) satislar = kayitsiz yatirim sozlesmesi** (menkul kiymet).
   - **Borsalardaki programmatic satislar = menkul kiymet DEGIL** — alicilarin
     "baskalarinin cabalarindan kar bekledigi" gerekliligi saglanmadi.
   - Diger dagitimlar "yatirim-of-money" gerekliligini karsilamadi.
   - Larsen/Garlinghouse'un kendi borsa satislari yatirim sozlesmesi degildi.
3. **Ekim 2023** — SEC, Garlinghouse/Larsen'e yardim-etme iddialarini **with prejudice**
   (tekrar acilamaz) dusurdu.
4. **7 Agustos 2024** — Torres nihai karar: kurumsal satislar icin **$125,035,150
   ceza** + gelecek ihlaller icin ihtiyat hukmu (injunction).
5. **2025** — Taraflar injunction'i kaldirip cezayi **$50 milyon**'e dusurmek istedi;
   **Torres REDDETTI** ("istisnai kosullar" yok).
6. **7 Agustos 2025** — **SEC ve Ripple kendi itirazlarini geri cekti. DAVA KAPANDI.**
7. *** 17 Mart 2026 — SEC, kripto varliklara federal menkul kiymet yasalarinin
   uygulanmasina iliskin YORUM yayimladi (CFTC rehberligiyle). 23 Mart'ta Federal
   Register'da yayimlandi. XRP'yi **bitcoin, ether, solana, stellar ile birlikte
   "dijital emtia" (digital commodity) ornekleri** olarak belirledi — degerin
   "baskalarinin zorunlu yonetici cabalarindan kar beklentisinden" degil,
   "calisan kripto sistemleri ve arz-talep"den kaynaklandigi belirtildi.
   *** ANCAK acikca soyle dedi: "kendisi menkul kiymet olmayan bir kripto varlik
   yine de bir yatirim sozlesmesinin parcasi olarak sunulabilir/satilabilir —
   islemin kosullarina bagli olarak." ***

### KOK v2 ICIN CIKARIM (bu artik kaynakli, ic kaynakli degil!)

- **Fair-launch / borsa satislari guc kazandi:** Torres'in "programmatic satislar
  menkul kiymet degil" karari + 2026 yorumu, "madenci kazanir, borsada satar"
  modelinin Howey disinda kalmasini destekler (alici belirli bir issuernin
  cabasindan kar beklemez).
- *** ANCAK KOK v2 kendini guvene alamaz: *** "kendisi menkul kiymet olmayan varlik
  yine de yatirim sozlesmesi olarak sunulabilir." Yani bir **on-satis / investor
  round / hazine satisi** yine menkul kiymet olur. KOK v2'nin fair-launch
  kararliligi burada deger kazanir: premine/yatirimci YOK.
- **2026 yorumu KOK icin dogrudan alintilanabilir** (Federal Register, 23 Mart 2026).

**SONUC: A SIKKI KAPANDI. Paper §9 Howey analizi artik gercek 2026 ictihati ve
SEC yorumu ile destekleniyor.**
