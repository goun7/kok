# Faydalı İş (Proof-of-Useful-Work) ve AI Madenciliği — 2025–2026 Akademik Durum

**Doğrulama yöntemi.** Bu dosyadaki her kaynak, ya `arxiv.org` API'sinden
(`export.arxiv.org/api/query`) ya da `eprint.iacr.org` sayfasından **fetch
edilerek** okundu. ArXiv API'si başlık, yazar listesi, özet, tarih ve
kategori alanlarını doğrudan döndürür; bu dosyadaki tanımlayıcılar (arXiv
no / ePrint no / DOI) o yanıtlardan alındı, tahmin edilmedi. Hiçbir kaynak
sadece "bilinen bir makale" olduğu için listelenmedi.

**Tarih.** ArXiv API'si sorgu zaman damgası: `2026-09-29T08:28Z`. Federal
Register sayfa görüntüleme kaydı aynı günü doğruluyor. Bu dosya
**29 Eylül 2026** itibarıyla yazıldı.

---

## 1. KÖK'ün temelendiği çizgi: MatMul PoUW

### [S1] Komargodski & Weinstein — *Proofs of Useful Work from Arbitrary Matrix Multiplication*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2504.09971** (v4) |
| Yazarlar | Ilan Komargodski, Omri Weinstein |
| Tarih | 2025-04-14 (v4: 2025-11-13) |
| Kategori | cs.CR |
| URL | https://arxiv.org/abs/2504.09971 |

**Makalenin iddiası (özetinden).** Nakamoto PoW'unu gerçek bir hesaplama
görevi $T(x)$ üzerine kurma açık problemine dönüyor. Madencinin **kendisinin
girdiyi seçtiği** (yani izinli-olmayan, permissionless) bir ayarda, PoUW
zorluğu: $T$'nin doğal hesaplamasını, *belirlenmiş zorlukta* (prescribed
hardness) ve en kötü durum karmaşıklığı üzerinde **neglante edilebilir
overhead** ile bir PoW sertifikasına dönüştürmektir. Ana sonuç: keyfi
matrisler için MatMul üzerine, naive MatMul'e göre **1+o(1) çarpan overhead**
ile bir PoUW. Yazarlar, protokollerinin optimal güvenliğe sahip olduğu
konusunda bir **konjektür** ileri sürüyor (düşük-rank rastgele lineer
denklemler topluğuna reduction). MatMul AI compute'un darboğazı olduğu için
bu, Bitcoin madenciliğinin enerji israfını neredeyse ortadan kaldıran bir L1
temel katmanı öneriyor.

**KÖK için önemi.** Bu, KÖK Layer G'nin temelidir (`KOK_V2_PAPER.md` §B).
**Konjektür hâlâ açıktır** — bu projenin miras aldığı en büyük varsayım ve
README'de "Pearl's own Polymath Problem 1" olarak işaret edildiği gibi.
Önemli olan: makale "permissionless" ayarı vurguluyor — madenci girdiyi
seçer. KÖK'ün E-gap bağlaması (TV-77/TV-82) tam da bu noktada çalışır:
madenci kendi seçtiği girdiyle de olsa, bağlam (ctx) ve program-commitment
görevden türetildiği için madencinin "sevdiği" bir matrisi sunması reddedilir.

### [S2] Bar-On, Komargodski & Weinstein — *Proof of Work With External Utilities*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2505.21685** (v1) |
| Yazarlar | Yogev Bar-On, Ilan Komargodski, Omri Weinstein |
| Tarih | 2025-05-27 |
| Kategori | cs.GT |
| URL | https://arxiv.org/abs/2505.21685 |

**İddia.** PoW madencilerinin birim hesaplama başına maliyetlerinin benzer
olduğu varsayımıyla analiz edilir; gerçekte elektrik ve donanım farkları
maliyetleri değiştirir ve PoUW'da bu, madencilerin faydalı iş (AI
training/inference) yaparak **dış ödüller** kazanmasıyla daha da belirgin
hale gelir. Fiat vd.'nin heterojen enerji maliyetli denge modelini dış
 ödülleri de kapsayacak şekilde genişletiyorlar. Bulguları: dış ödüle sahip
madenciler bazı durumlarda faydalı görevleri **tek bir blokta
toplayarak** kârlılığı optimize eder; dış ödüllerin merkezîleşme (Shannon
entropisi ile ölçülen hesaplama-dağılımı) üzerinde etkilerini modelliyorlar.

**KÖK için önemi.** Aynı ekibin MatMul makalesinin iktisat ayağı. "Faydalı
işin tek blokta toplanması" teşviki, KÖK'ün U-layer anti-aggregation fee
cap'ini (C_FEE = 500, `kok-u-layer/src/lib.rs`) haklı çıkaran mekanizmandır:
küçük görevleri paketleyerek fee piyasasını seyreltme teşviki, bu modelde
gerçek bir denge davranışı olarak tanımlanıyor.

---

## 2. 2026'nın en önemli iki sonucu: biri yapıcı, biri yıkıcı

### [S3] Pass — *The Economics of Proof-of-Useful-Work*  ★

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2606.06700** |
| Yazar | Rafael Pass |
| Tarih | 2026-06-04 |
| Kategori | cs.GT, cs.CR, econ.TH |
| DOI | 10.48550/arXiv.2606.06700 |
| URL | https://arxiv.org/abs/2606.06700 |

**İddia.** PoUW'a yönelik yaygın eleştiri: "iş faydalıysa saldırganlar
saldırmak için ödeniyor olabilir." Pass bir **rekabetçi denge modeli**
kuruyor; compute üç şekilde ayrılabilir: saf madencilik, saf faydalı iş
(ML inference olarak), veya ikisini de üreten ama hesaplama overhead'ı olan
"**duplex**" iş. Tam bir **kapalı-form** denge karakterizasyonu veriyor,
tek ekonomik parametre — token-inference oranı — cinsinden. Üç rejim:
**"Bitconia"** (ekonomi klasik PoW'a indirgenir), **"Fortessia"** (duplex
madenciliğin yerini alır, güvenlik artarken faydalı çıktı değişmez),
**"Duplexia"** (token ödülleri inference'u sübvansiye eder, fiyatlar
düşer, inference arzı genişler). **Yaygın saman adam argümanının aksine,
PoUW saldırıları ucuzlatmaz**: denge fiyatları hesaba katıldığında çoğunluk
saldırısının ekonomik maliyeti blok ödülüne bağlı kalır. Duplexia'da blok
ödülleri inference fiyatlarına bir **rebate** gibi davranır.

**KÖK için önemi.** Bu, projedeki `pass_sim_en.py`'in kapalı-form çözücüsünü
yazdığı makaledir (README'de "Closed-form solver for the Pass (2026)
economic model"). KÖK'ün iktisat bölümündeki R_0 / T_half / R_inf
parametreleri ve Fortessia/Duplexia rejim sınıflandırması buradan gelir.
**Dürüst not:** KÖK'ün tasarımı Pass'ın duplex ayarına oturmaz — KÖK
faydalı işi (Layer U) güvenlikten **tamamen ayırır** (sıfır konsensus
ağırlığı), oysa Pass'ın modeli "duplex" işin her ikisini birden ürettiği
ayarlar içindir. KÖK'ün konumu Pass'ı çürütmüyor, onun **bitconia/
fortessia sınırında, E-gap'i exogenous kılan** bir yapısal seçenek
olduğunu söylemek daha doğru. Bu fark makalede analiz edilmemiş bir
köşedir ve dürüstçe "analyzed by the paper's model? No" olarak
işaretlenmelidir.

### [S4] Basu — *The Usefulness Gap in Proof-of-Useful-Work: An Empirical Study of Pearl's cuPOW Protocol* ★

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2606.04819** (v2) |
| Yazar | Abhinaba Basu |
| Tarih | 2026-06-03 (v2: 2026-06-05) |
| Kategori | cs.CR, cs.CY, cs.DC |
| DOI | 10.48550/arXiv.2606.04819 |
| URL | https://arxiv.org/abs/2606.04819 |

**İddia (ölçülen, varsayımsal değil).** Dağıtılmış bir PoUW sisteminin
**ilk sistematik ampirik ölçümü**. Pearl'in 24 EH/s ağının (~320.000
GPU-eşdeğeri, ~112 MW) **sıfır faydalı AI hesaplaması** ürettiğini
buluyor. Madencilik yazılımının halka açıklanmasının ardından bütçe GPU
kiralama fiyatları %38 yükselmiş, kullanım oranı %57'den %94'e fırlamış
(meşru araştırma iş yüklerini displacing). Beş boyutta ölçüm: (1) 8.012
worker'ın tamamı inference-capable donanıma sahip ama dominant madencilik
yazılımında **hiç inference kodu yok**; (2) **doğrulama protokolü
tasarım gereği rastgele matrisleri kabul ediyor** — açık kaynak madenciden
44 havuz-kabul edilen share (NVIDIA, AMD, CPU, Apple Silicon); (3)
istatistiksel dağılış kontrolleri adversarial Gaussian örnekleme ile
kolayca yenilgi; (4) madencilik ekonomisi marjinal (PRL $0.76'da ROI
-1%..+67%); (5) madencilik hesaplaması commodity integer arithmetic —
herhangi bir donanımda çalışıyor, vendor lock-in yok.

**KÖK için önemi — bu dosyanın en önemli kaynağı.** Bu, KÖK'ün kendi
negatif sonuçlarının (TV-72: ölçülen phi=0; TV-82: bağlamanın olmaması)
**harici, bağımsız bir şekilde teyit edildiği** yerdir. Pearl'in hatası
tam olarak [S1]'in permissionless ayarının korunamamasıdır: doğrulayıcı
madencinin matrisini kontrol etmiyordu, bu yüzden "faydalı" iş hiçbir
göreve bağlı değildi. KÖK'ün `egap_cert_en.py` / TV-82 bağlaması
(program_commit'ten tile değerinin yeniden türetilmesi) bu boşluğu
kapatan mekanizmadır. **Dürüst sınırlar:** Basu'nun ölçtüğü sistem
Pearl'dir, KÖK değildir; KÖK'ün bağlamasının Pearl'in hatasını
düzelttiği bir tasarım argümanıdır, ölçülmemiş bir sonuç değil. Ayrıca
Basu'nun (5) bulgusu — işin commodity integer arithmetic olması —
KÖK'ün MatMul seçiminin de aynı "fayda" eleştirisine açık olduğunu
gösterir: MatMul'un kendisi faydalıdır ama **kime göre** olduğu görev
bağlaması olmadan cevapsızdır.

---

## 3. Güvenlik teorisi: talep kanıtı iş kanıtı değildir

### [S5] Demirel — *Proof of Demand Is Not Proof of Work: On the Limits of Demand-Weighted Consensus under Free Pseudonyms* ★

| Alan | Değer |
|---|---|
| Tanımlayıcı | **ePrint 2026/1492** |
| Yazar | Ömer Demirel (Snowfall Finance LLC) |
| Tarih | received 2026-07-21, revised 2026-08-23 |
| Kategori | Applications |
| URL | https://eprint.iacr.org/2026/1492 |
| Lisans | CC BY |

**İddia.** PoUW hesaplama zorluğunu sertifikalar, **faydayı değil**: sertifikalı
bir hesaplama kimsenin talep ettiği iş olmak zorunda değil. Üç özelliği
ayırt eder — iş sağlamlığı W, iş bağlaması (job binding) B, talep
egzogenliği (demand exogeneity) E — ve boşluğu **E**'de konumlandırır.
Denge veya piyasa modeli gerektirmeyen iki sonuç: (i) koalisyon kontrolündeki
talepkâr ve worker arasındaki ödemeler **geri kazanılabilir transferlerdir**
ve Sybil-dirençli maliyete katkıda bulunmaz, bu yüzden hiçbir güvenlik
alt sınırı nominal değerlerini sayamaz (Lemma 1); (ii) belirtilen
gerçekleştirilebilirlik/ayırt-edilemezlik önşartları altında **endojen
makbuzlar E'yi sertifikalayamaz** (Theorem 1). Ayrıca, açık bir
"sıfır-talep" tasarım normu altında, her admissible talep ortamında
güvenli ve canlı olan ve null-talep projeksiyonu altında kapalı olan bir
mekanizma, hizmet makbuzlarının **talep bileşeninden bağımsız bir
lider-seçimi yoluna** sahip olmalıdır (**Theorem 2**). Yapısal olarak: her
yerleşmiş ödeme üzerinde **geri alınamaz bir vergi** (burn), güvenlik
kaynağı yapan şeydir — "bağımsızlık kanıtı" değil. Dağıtılmış kanıt olarak
bir raporlanan denetim (Pearl cuPOW) ve ödül-programı analogları veriyor;
endojen seçim tarafındaki başarısızlık şu an için bir **model
tahminidir**.

**KÖK için önemi — bu projenin teorik merkezidir.** Theorem 2, KÖK'ün
iki-katmanlı tasarımının **gereklilik yönündeki** argümanıdır: Layer G
lideri seçer, Layer U'nun konsensus ağırlığı **tam olarak sıfırdır**
(`kok-u-layer/src/lib.rs::u_task_consensus_weight` her zaman 0 döner).
README'nin "Leader election is demand-independent by construction, which
is what Demirel's Theorem 2 requires" iddiası bu makaleye dayanır ve
**doğrulanmıştır**. **Dürüst sınırlar:** (a) Theorem 2'nin önşartları
vardır — "her admissible talep ortamında güvenli ve canlı" + "null-talep
projeksiyonu altında kapalı"; KÖK'ün bu önşartları sağladığı bir
**ispat** değil, bir tasarım uyumudur. (b) Demirel'in kendi ifadesiyle
seçim tarafındaki başarısızlık bir model tahminidir, dağıtılmış bir
gözlem değildir. (c) Demirel'in "geri alınamaz vergi = güvenlik kaynağı"
sonucu, KÖK'ün burn mekanizmasını destekler, ama KÖK burn'u bir
**protokol fee politikası** olarak konumlandırır (`kok-u-layer`:
"never a supply-reduction promise"), tedarik azaltma vaadi olarak değil.

---

## 4. Diğer 2025–2026 PoUW ve PoL çizgileri

### [S6] Oleksak, Gazdik, Peresini & Homoliak — *SNARKChain: Proof-of-Useful-Work Blockchain Consensus with General-Purpose SNARK Marketplace*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2510.09729** (v2) |
| Tarih | 2025-10-10 (v2: 2026-07-13) |
| URL | https://arxiv.org/abs/2510.09729 |

**İddia.** Mevcut PoUW önerileri genellikle **zincirin bütünlüğünü ve
madencinin kimliğini bulmaca çözümlerine gömeyi** başaramaz; bu da onları
PoW'ın gerekli özelliklerini karşılamayıp savunmasız bırakır. Çözüm:
müşteriye-outsourced SNARK kanıtlarını yan ürün olarak hesaplayan ve
aynı zamanda konsensusu güvenceye alan bir PoUW protokolu; bunun
üzerine, konsensus katmanında çalışan ilk SNARK-outsourcing marketplace.

**KÖK için önemi.** "Zincir bütünlüğü + madenci kimliğinin bulmacaya
gömülmemesi" başarısızlığı, [S4]'ün Pearl ölçümünün teorik ikizidir ve
KÖK'ün kanıt entegrasyonunun (bu oturumda yapılan `kok proof` / did:key
imzalı kanıt) neden bir gereklilik olduğunu bağımsız olarak gösterir:
**kim imzaladı** ve **ne için** kanıtın içinde olmalıdır.

### [S7] Cao, Doger & Ulukus — *SEDULity: A Proof-of-Learning Framework for Distributed and Secure Blockchains with Efficient Useful Work*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2512.13666** (v2) |
| Tarih | 2025-12-15 (v2: 2026-06-10) |
| URL | https://arxiv.org/abs/2512.13666 |

**İddia.** Template block'u eğitim sürecine gömen ve çözmesi zor ama
doğrulaması görece kolay bir "useful function" ile PoW bulmacasının yerine
geçen bir PoL çerçevesi. Teorik olarak rasyonel bir madencinin, iyi
tasarlanmış sistem parametreleriyle **tamamen dürüst** eğitmeye teşvik
edildiğini gösteriyorlar.

**KÖK için önemi.** "Doğrulaması zor olanın kolay doğrulandığı" yapısı
KÖK'ün G-layer'ınkiyle aynıdır; SEDULity'nin incentive-uyumluluk ispatı,
KÖK'ün henüz ispatlamadığı bir özelliktir (KÖK'ün E-gap'i bir bağlama
sorunu olarak ele alır). U-layer için bir referans çizgisi.

### [S8] Orlicki — *PoGO: A Scalable Proof of Useful Work via Quantized Gradient Descent and Merkle Proofs*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2504.07540** (v2) |
| Tarih | 2025-04-10 |
| URL | https://arxiv.org/abs/2504.07540 |

**İddia.** Madenciler büyük-ölçekli ML modelleri eğittiğine dair
doğrulanabilir kanıt üreten PoGO. 4-bit quantized gradients ile depolama
ve hesaplama gereksinimini azaltır; 32-bit model üzerinde Merkle proofs ile
rastgele leaf kontrolleri. GPT-3 (175B) örneği üzerinden ampirik maliyet
analizi. **Uzun blok sürelerinin (potansiyel olarak saatler) gerekliliğini**
tartışıyor.

**KÖK için önemi.** PoL çizgisinin "gerçek ML işi"ne en yakın ölçek
örneği. KÖK'ün U-layer'ı için teyit edici bir tasarım referansı; ama
KÖK'ün G-layer'ı MatMul seçtiği için PoGO'nun saatlerce blok süreleri
KÖK için bağlanmaz (MatMul saniyeler/milisaniyeler ölçeğindedir).

### [S9] Barbaccia, Vhaduri & Dibbo — *Quantum-Resilient Decentralized AI Economies: Proof-of-Useful-Work and Post-Quantum Security*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2606.24942** (v1) |
| Tarih | 2026-06-22 |
| URL | https://arxiv.org/abs/2606.24942 |

**İddia.** Üç-katmanlı (compute / validation / economic coordination) bir
merkeziyetsiz AI ekonomisi; $(\theta_c, \theta_w, W)$ kapalı-döngü token
ekonomisi ve dürüst katılım için yeterli-stake koşulu. Grover hash
bulmacalarına karesel hızlanım verir ama **ML-native lineer cebiri
hızlandırmaz**; Shor imzaları tehdit eder; kafes/tabanlı göçe geçiş imza
katmanını çözer.

**KÖK için önemi.** KÖK'ün `Cargo.toml`'undaki `ml-kem` bağımlılık
bildirimi ("when the chain adds quantum-resistant key agreement it shares
FISP's crate") bu argümanla örtüşür — ama KÖK henüz PQC kullanmıyor ve
dosya bunu açıkça söylüyor. Makalenin "useful work quantum açısından
avantajlı" iddiası KÖK tarafından **sahiplenilmemeli**: KÖK'ün G-layer'ı
MatMul üzerine kuruludur ve makalenin kuantum argümanı ML-native lineer
cebir içindir — MatMul bunun içindedir, ama bu KÖK'ün bir kuantum
güvenlik iddiası yapmak için yeterli bir dayanak değildir.

### [S10] Cao, Ling, Wang, Gao & Ding — *Optimization-based Proof of Useful Work: Framework, Modeling, and Security Analysis*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2405.19027** (v3) |
| Tarih | 2024-05-29 (v3: 2026-08-07) |
| URL | https://arxiv.org/abs/2405.19027 |

**İddia.** Optimizasyon problemleri üzerine genel bir PoUW çerçevesi;
bencillik (selfishness) ve kötülüğe (maliciousness) karşı güvenlik
koşulları, güvenlik overhead'ı için alt sınır, faydalı iş verimi ile PoW
güvencesi arasındaki trade-off. Rasyonel madenci dürüstlüğünü garanti
için ödül fonksiyonu tasarım kılavuzları; long-range saldırılara karşı
gerekli koşul.

**KÖK için önemi.** "Faydalı verim ↔ PoW güvencesi trade-off'u" KÖK'ün
1+o(1) overhead hedefinin (S1) genel çerçevedeki yeri. KÖK bu trade-off'u
MatMul için [S1] üzerinden konumlandırır.

### [S11] Bachman, Chakravorti, Rane & Thyagarajan — *Proof-of-Learning with Incentive Security*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2404.09005** (v8) |
| Tarih | 2023-08-04 (v8: 2026-05-04) |
| URL | https://arxiv.org/abs/2404.09005 |

**İddia.** "Incentive-security" kavramı: rasyonel kanıtlayıcıları kendi
çıkarları için dürüst davranmaya teşvik ederek, Byzantine-güvenli PoL
tasarımının teorik zorluğunu atlatır. İki saldırıya karşı güvenli,
$\Theta(1)$ overhead'ı iyileştirir, kontrol edilebilir zorluk.

**KÖK için önemi.** KÖK'ün "sıfır konsensus ağırlığı" yaklaşımına bir
alternatif paradigma: güvenliği bağlamayla değil, teşviklerle sağlamak.
Her ikisi de [S5]'in E boşluğuna farklı yanıtlardır.

---

## 5. AI işini doğrulama (verifiable ML)

### [S12] Rahimi, Khalaj & Maddah-Ali — *Range-Arithmetic: Verifiable Deep Learning Inference on an Untrusted Party*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2505.17623** (v2) |
| Tarih | 2025-05-23 (v2: 2026-06-09) |
| URL | https://arxiv.org/abs/2505.17623 |

**İddia.** Merkeziyetsiz ML'de DNN inference'ı dış katılımcılara
outsourcing'i doğrulama ihtiyacı. Boolean encoding, yüksek-derece
polinomlar ve büyük lookup tablolarının karmaşıklığından kaçınarak,
sabit-noktalı MatMul'dan sonra yuvarlama ve ReLU gibi aritmetik-olmayan
işlemleri, sum-check protokolleri ve birleştirilmiş range proof'ları ile
doğrulanabilir aritmetik adımlara dönüştürür. Doğrulama maliyetini,
güvenilmeyen tarafın hesaplama çabasını ve iletişim overhead'ını azaltır.

**KÖK için önemi.** KÖK'ün U-layer'ı için doğrudan ilgili: inference
doğrulamanın son teknolojisi. **Dürüst not:** KÖK'ün mevcut `kok-fri`
prototipi bir "STARK-like" izlekli **toy** (q=97) ve gerçek bir AIR
değildir (README dürüst limitlerinde bunu söyler). Range-Arithmetic,
KÖK'ün üretim ölçeğinde alması gereken yönlere bir referanstır, eldeki
bir kapasite değildir.

### [S13] Zhang vd. — *zkVC: Fast Zero-Knowledge Proof for Private and Verifiable Computing*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2504.12217** (v1) |
| Tarih | 2025-04-16 |
| Yayın | DAC 2025 |
| URL | https://arxiv.org/abs/2504.12217 |

**İddia.** MatMul gibi temel işlemlerin bile zkSNARK'larda çok kısıt
gerektirdiği sorununa karşı, Constraint-reduced Polynomial Circuit (CRPC)
ve Prefix-Sum Query (PSQ) ile MatMul için ZKP hesaplamasını optimize eder;
önceki yöntemlere göre kanıt hızında 12 kata kadar artış.

**KÖK için önemi.** MatMul doğrulamanın SNARK maliyetlerinin 2025'in
son teknolojisi — KÖK'ün G-layer'ı MatMul'ı PoW olarak kullandığı için
(bir SNARK değil), zkVC'nin maliyetleri KÖK'ün maliyetleriyle
karşılaştırılabilir bir referans verir.

---

## 6. Doğrulanamayan / teyit edilemeyen aramalar

Aşağıdakiler aranmış ama **doğrulanamamış**, bu yüzden yukarıdaki listeye
alınmadı. Hiçbir kaynak sessizce düşürülmek yerine burada listeleniyor:

- **"Leinweber et al."** — [S4]'ün özetinde "verifiability-usefulness
  tension identified theoretically by Leinweber et al." diye atıf yapılan
  bu çalışma için bağımsız bir arXiv/ePrint kaydı **bulunamadı**. [S4]'ün
  özetinden var olduğu biliniyor ama tanımlayıcısı teyit edilemedi; bu
  yüzden bu dosyada **kaynak olarak listelenmemelidir**, sadece [S4]'ün
  içindeki bir atıf olarak anılmalıdır.
- **"Pearl" / "PRL"** — [S4] ve [S5] Pearl'i referans alır ama Pearl'in
  kendi teknik bir makalesi / resmi bir protokol özellik bu aramalarda
  bulunamadı. Pearl hakkında her şey bu dosyada [S4] üzerinden
  bildirilir, birincil kaynak olmaksızın.
- **"modular consensus" / "shared sequencer" üzerine 2025–2026 akademik
  makaleler** — arXiv'te bu tam kelime öbekleriyle yapılan arama, blockchain
  yerine "shared sequence" (ML) ile eşleşen çalışmaları getirdi; bu
  konuda doğrulanmış birincil kaynaklar bu dosyada **yok**. KÖK'ün
  modüler tasarımının teorik dayanağı olarak [S5] (Theorem 2) kullanılır;
  "modular blockchain" literatür özeti bilinçli olarak **boş bırakılır**
  çünkü doğrulanmadı.

---

## 7. Bu araştırmanın KÖK için çıkarımları (sadece yukarıdaki kaynaklardan)

1. **En büyük açık hâlâ [S1]'in konjektürü.** Komargodski–Weinstein'ın
   random-rotation konjektürü (A.1) açıktır; KÖK'ün güvenliği buna
   dayanır ve dış kriptografik inceleme bu noktaya odaklanmalıdır
   (`KOK_V2_CRYPTO_BRIEF.md` zaten bunu ilk soru yapar).
2. **[S4] KÖK'ün negatif sonuçlarını haricen teyit ediyor.** Pearl'in
   phi=0 sonuçları KÖK'ün TV-72/TV-82'siyle aynı nedenden: **doğrulayıcı
   madencinin girdisini bağlamamış**. KÖK'ün E-gap bağlaması bu boşluğu
   kapatacak şekilde tasarlandı, ama "kapatacak şekilde tasarlandı" ile
   "ölçüldü" aynı şey değildir.
3. **[S5] Theorem 2 KÖK'ün mimarisini zorunlu kılar** — ama önşartlarıyla
   birlikte. Talep-bağımsız lider seçimi bir tercihten ziyade, "sıfır-talep
   normunu karşılayan her güvenli mekanizma" için bir gerekliliktir.
   KÖK'ün U-ağırlığı = 0 fonksiyonu bu gerekliliğin koddaki ifadesidir.
4. **[S3] PoUW saldırıları ucuzlatmaz** — bu, KÖK'ün iktisat bölümünün
   savunduğu şeydir ve Pass'ın modelinde kanıtlanmıştır. Ama [S5] daha
   temkinli: nominal ödeme değerini güvenlik alt sınırında saymamak
   gerektiğini söyler. İki makale çelişmez — Pass duplex işin her ikisini
   de ürettiği ayarı, Demirel serbest pseudonym ayarını inceler.
5. **Kimlik ve bağlamama bulmacanın parçası olmalı** ([S6], [S4]). Bu,
   bu oturumda inşa edilen `kok proof` kanıt entegrasyonunun (did:key
   imzası + program/input commitment'ı + kanıt içi ctx) akademik
   gerekçesidir.
6. **AI işini doğrulamanın kendisi aktif bir araştırma alanıdır** ([S12],
   [S7], [S8], [S13]). KÖK'ün "toy" dürüst limitleri bir kusur değil, bu
   alanın 2026'daki halidir; üretim ölçeğinde doğrulama çözülmemiş bir
   problem olarak kalır.
