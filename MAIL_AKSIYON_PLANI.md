# MAIL AKSIYON PLANI — cevap gelmezse ne yapacagiz (2026-09-22)

Bu belge, "mailler gelmezse ne yapacagiz" sorusunun cevabidir. Uc hedef var:
**Alon Burg** (Astria, alici kaniti), **Demirel** (G-layer incelemesi = Faz 2
kapisini, iki bagimsiz insan kripto onayi) ve Dikshit. **Hicbirine mail
GONDERILMEZ** — kullanici yasagi. Bu belge yalnizca cevap gelmezse ne yapilacagini
yazar.

## 1. Gercel durum (olculebilir gercekler)

- Davet stratejisi `F3A_INVITATION_STRATEGY.md` L45 der ki: **"So the list is one
  party for now. If Astria does not reply, the list is empty, and that is
  information too."** Yani beklenen tek alici partisi Astria'dir.
- Alon Burg'un **kisisel e-posta adresi bulunamadi** (L153: "not found. LinkedIn
  shows the profile"). Ulasilabilir olan **paylasilmis inbox** versiyonudur (L52).
  Yani "Alon cevap vermedi" ile "inbox'u gormedi" ayni sey DEGILDIR.
- Demirel incelemesi **Faz 2 kapisidir** ve iki bagimsiz insan onayı gerektirir.
- Pearl sessizligi **sifir talep** olarak okunamaz (EPOSTA_SOK.md'un temel
  hatasindan biri buydu: sessizlik = red degildir).

## 2. Kararlar — ne zaman, ne yapacagiz

**Bu kararlar kullaniciya sunulmak uzere yazilir; otomatik uygulanmaz.**

### 2.1 Astria (Alon Burg) — alici kaniti

- **Kural:** sessizligi "ilgilenmiyor" olarak OKUMA. Inbox'a dustugunu bile
  bilmiyoruz olabilir.
- **Aksiyon A (henuz zaman dolmadi):** bekle. Sekizinci oturum boyunca bekledik.
- **Aksiyon B (uygun gorulurse):** `F3A_INVITATION_STRATEGY.md`'in **Version B**
  (paylasilmis inbox versiyonu) kullanilir — Version A kisisel adrese hitap eder
  ve elimizde kisisel adres YOK. Bu ayrim L50-52'de acikca belirtilmistir.
- **Aksiyon C (Astria hic donmezse):** liste bos kalir ve **bu bir olcum
  sonucudur.** "Liste bos" demek F3a testnet'inin gercek bir alici olmadan
  calismasi demektir; bu da phi=0 bos-blok dengelesinin **testin kendisi** olur.
  Bos liste, projenin en rahatsiz edici gercegini (F0 = talep kesfi)
  dogrular, degil gizler. Makale L530 zaten soyluyor: ilk kilometre tasi
  testnet degil, **"A CUSTOMER WITH A JOB"**dur.

### 2.2 Demirel — G-layer incelemesi (Faz 2 kapisı)

- **Kural:** iki bagimsiz insan onayı GEREKLI. Tek bir inceleyici yeterli DEGIL.
- **Aksiyon:** Demirel gelmezse, **ikinci insan** aranir. Bu, protokolun
  gerekliligidir, bir tercih degil.
- **Bu belge "kendimiz yapalim" diyemez:** G-layer guvenligi icin LLM incelemesi
  YERINE GECMEZ (§11.4 — modelin itibari yoktur; yanlis bir beyani zarara
  ugratmaz). LLM incelemesi yalnizca **daha az hatali** olmayi saglar,
  **guvenilir** olmayi degil.

## 3. "Kendimiz baska LLM'lerle denetleme yapamaz miyiz?" — acik cevap

Evet, kismen. Bu oturumda zaten yaptik: **adversarial probe yontemi** bir LLM
denetlemesidir ve **5 gercek bug + 1 geri cekilmis sifir-bilgi iddiasi** buldu.
Makale §11.4 bu ayrimi yazar:

**LLM denetlemesi YAPABILIR:**
- Kodun soyledigi ile makalenin iddia ettigi arasindaki **ucurumu bulmak.**
  (TV-60: esik 0.79 degil break-even; TV-62/63: theta araligi kontrol
  edilmemisti; TV-65: sifir-bilgi yoktu.)
- Bir ozelligin **testi yoksa** onu "desteklenmemis iddia" olarak isaretlemek.
- Sinir durumlarini **olcmek** (TV-59: 572 order girdisi past disinda).

**LLM denetlemesi YAPAMAZ (ve yapamayacagi yer burasi):**
- **Itibar.** Demirel bir konsensus kuralina imza attiginda **adini** ortaya
  koyar; budur ucuncu bir tarafa satilan sey. Modelin ciktisinin boyle bir
  payi yoktur. LLM incelemesi G-layer'i **daha az hatali** yapar, **guvenilir**
  yapmaz.
- **Canli olcum.** Canli guvenlik butcesinin ve **gercek bir alicinin para
  odeyeceginin** kaniti hicbir okuma ile ikame edilemez.
- **F3b/F5/F6'daki gibi formal guvenlik kanitlari** — model uretmez, denetlemez.

**Protokol (§11.4'te yazili):**
1. Her nicel iddiya ya **birinci kaynaktan verbatim** ya da **calisan dosyadan**
   izlenebilir olmali.
2. Problar **dusmanca yazilip saklanmali** (gectigi an regresyon korumasi olur).
3. Kod ile sozcyu celisirse **kod dogrudur, sozcyu duzeltilir** — asla tersi.
4. Desteksiz iddia **yerinde geri cekilir** (tarih + probe ile), silinmez.
5. **Ikinci model kullanilmali, ayni model degil.** Ayni model bir iddianin
   arkasindaki varsayimi zaten kabul etmistir; onu "siradan" bulmaya meyillidir.
   Farkli bir model, paylasilmamis baglami verildiginde o yatirimi tasimaz.

**Bu protokol ilk kez bu oturumda uygulandi:** `subagent` ile **taze baglamli,
paylasilmamis** bir inceleyici baslatildi (d16f2df8). O inceleyicinin bu
belgenin yazarina HIC baglanti yoktur — protokolun 5. maddesinin somut testidir.

**Sonuc:** LLM incelemesi **iddialarin kalitesini** yukseltir, **guveni** degil.
Ikisi arasindaki ayrim, insan-incelemesi satirinin yol haritasinda kritik yolda
kalmasinin nedenidir. Alabilecegimiz ust sinir: her iddianin ya dogrulanmis ya
geri cekilmis oldugu bir makale. Insan incelemesinin ust siniri daha yuksektir,
cunku "adı konmus bir isim, gecmis bir testten daha degerlidir."

## 4. Simdi ne yapacagiz (bu sirada)

1. Taze-baglamli LLM incelemesini **bitir ve bulgulari uygula** (protokol 5).
2. Makaleyi taze dis incelemeye hazirla: her iddia izlenebilir olmali.
3. Problari genislet: yeni modul kalmadi, ama **makaledeki iddialar** hedef olmali.
4. Mailleri **bekle**, gonderme. Gelirse `EPOSTA_SOK.md`'e islenir.

**Hicbir sekilde:** mail gonderme, F3b insa etme, duyurma, finans konusu acma.
