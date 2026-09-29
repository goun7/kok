# Modüler Konsensus, Doğrulanabilir Hesaplama ve Veri Bulunabilirliği — 2025–2026 Akademik Durum

**Doğrulama yöntemi.** Bu dosyadaki her kaynak `export.arxiv.org/api/query`
üzerinden **fetch edildi** ve başlık/yazar/özet/tarih/kategori doğrulandı.
Tanımlayıcılar (arXiv no / DOI) o yanıtlardan alındı. Hiçbir kaynak tahmin
edilmedi.

**Tarih.** 29 Eylül 2026 (API sorgu zaman damgası `2026-09-29T08:30Z`).

---

## 0. "Modüler konsensus" için dürüst bir boşluk

KÖK kendini "modüler iki-katmanlı konsensus" olarak tanımlar: G katmanı
lideri seçer, U katmanı faydalı işi taşır ve **sıfır konsensus ağırlığına**
sahiptir. "Modüler" kelimesinin blockchain literatüründeki yaygın anlamı
(consensus / execution / data-availability'in ayrı katmanlar) KÖK'ün
ayrımıyla **aynı şey değildir** — KÖK güvenliği faydadan ayırır, execution'ı
DA'dan değil.

**Bu dosya bu farkı gizlemez.** "Modüler blockchain" / "shared sequencer"
kelime öbekleriyle arXiv'te yapılan aramalar blockchain değil de ML
"shared sequence" çalışmaları getirdi ve doğrulanmış birincil kaynak
vermedi; bu yüzden bu dosyada **"modüler blockchain" literatür özeti bilinçli
olarak boş bırakılır**. KÖK'ün modülerliğinin teorik dayanağı olarak
aşağıdaki [D1] (talep-bağımsız lider seçimi gerekliliği) ve DAG/DA
kaynakları kullanılır.

---

## 1. Güvenlik katmanının teorik dayanağı

### [D1] Demirel — *Proof of Demand Is Not Proof of Work* ★

| Alan | Değer |
|---|---|
| Tanımlayıcı | **ePrint 2026/1492** |
| Yazar | Ömer Demirel |
| Tarih | received 2026-07-21, revised 2026-08-23 |
| URL | https://eprint.iacr.org/2026/1492 |

**Bu dosya için önemi.** Theorem 2: sıfır-talep tasarım normunu karşılayan,
her admissible talep ortamında güvenli ve canlı olan, ve null-talep
projeksiyonu altında kapalı olan her mekanizma, hizmet makbuzlarının
**talep bileşeninden bağımsız bir lider-seçimi yoluna** sahip olmalıdır.
**KÖK'ün iki-katmanlı tasarımı bu gerekliliğin koddaki ifadesidir**:
`kok-u-layer/src/lib.rs::u_task_consensus_weight` her zaman `0` döner, ve
README'nin Layer G tanımı "Leader election is demand-independent by
construction" der.

**Dürüst sınırlar (aynı dosyada):** (a) Theorem 2'nin önşartları vardır ve
KÖK'ün onları sağladığı bir ispat değildir, bir tasarım uyumudur;
(b) Demirel'in kendi ifadesiyle seçim tarafındaki başarısızlık bir **model
tahminidir**, dağıtılmış bir gözlem değildir. Ayrıntılar ve Demirel'in
kısmi sonuçları (Lemma 1, Theorem 1, Corollary 4, "geri alınamaz vergi =
güvenlik kaynağı") için
`docs/arastirma/pouw_ai_madenciligi_2026.md` [S5]'e bakın.

---

## 2. DAG tabanlı konsensus (KÖK'ün G katmanı ordering'i GHOSTDAG kullanır)

### [D2] Keller — *Automated Selfish Mining Analysis for DAG-Based PoW Consensus Protocols*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2501.10888** (v3) |
| Yazar | Patrik Keller |
| Tarih | 2025-01-18 (v3: 2025-06-21) |
| Yayın | ACNS '25 |
| URL | https://arxiv.org/abs/2501.10888 |

**İddia.** Selfish mining, PoW protokollerinde ödülleri ençoklamak için
stratejik kural-çiğnemektir; MDP'ler (Markov Decision Processes) optimal
stratejileri bulmanın tercih aracıdır. DAG tabanlı zincir yapılarında MDP
analizi daha karmaşıktır ve bugüne kadar her protokol için elle özel MDP
yazılmıştır. Bu çalışma Ethereum PoW, **GhostDAG** ve Parallel PoW'u
kapsayan **genel bir saldırı modeli** öneriyor: her protokol kısa bir
program olarak belirtiliyor ve araç selfish-mining MDP'sini otomatik
türetip çözüyor.

**KÖK için önemi.** KÖK'ün `kok-ghostdag` crate'i GHOSTDAG ordering'ini
Kaspa mainnet parametreleriyle (k=18) uygular. Bu makale, GHOSTDAG için
selfish-mine direncinin **artık otomatik analiz edilebilir** olduğunu
gösterir — KÖK'ün henüz koşmadığı bir analiz. README'nin dürüst
limitlerinde GHOSTDAG için "no PoW/validity check, uniform delay model,
k=18 Kaspa BPS=1 template not our own" der; bu makale o sınırın
kapatılabileceği yönün bir kanıttır, kapatıldığına dair bir kanıt değil.

### [D3] Li — *Mazzaroth: A High-Throughput DAG Consensus with State Root*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2506.01960** (v1) |
| Yazar | Haohan Li |
| Tarih | 2025-05-07 |
| URL | https://arxiv.org/abs/2506.01960 |

**İddia.** Tek-zincir blockchain maksimum ağ gecikmesi varsayımıyla blok
üretim hızını sınırlar. blockDAG yapısı throughput'u artırır ama
PG'nin (Phantom) olasılıksal onayı akıllı sözleşme uygulamalarını
kısıtlar. Mazzaroth, lineer bir ordering algoritması ile **state root**
hesaplayarak state finalitesi sağlayan PoW-tabanlı bir blockDAG konsensusu
önerir; ağ ve hashrate dalgalanmalarına göre dinamik zorluk ayarı yapar.

**KÖK için önemi.** DAG + state finalitesi kombinasyonu KÖK'ün
GHOSTDAG portlamasının ötesinde bir hedef; KÖK'ün `kok-ghostdag`'ı
ordering verir ama state finalitesi vermez. Mazzaroth'un dinamik zorluk
ayarı, KÖK'ün `kok-poum/src/retarget.rs`'inin (RT-1..RT-3) yaptığı işin
akademik karşılığıdır.

---

## 3. Veri bulunabilirliği (L1 mezarlama)

### [D4] Feist, Herold, Simkin & Wagner — *Robust Distributed Arrays: Provably Secure Networking for Data Availability Sampling*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2504.13757** (v2) |
| Yazarlar | Dankrad Feist, Gottfried Herold, Mark Simkin, Benedikt Wagner |
| Tarih | 2025-04-18 (v2: 2025-04-22) |
| Kategori | cs.DS, cs.DC |
| URL | https://arxiv.org/abs/2504.13757 |

**İddia.** DAS, Ethereum yol haritasının merkezî bir bileşeni; istemcilerin
bütün veri setini indirmeden veri bulunabilirliğini doğrulamasını sağlar.
Kriptografik ve kodlama yönleri yakın zamanda formal analiz edilmiş olsa da
**peer-to-peer ağ katmanı az incelenmiş**: güvenlik tanımları ve verimli,
ispatlanabilir güvenli constructions eksik. Bu çalışma "robust distributed
arrays" adını verdikleri yeni bir dağıtık veri yapısı sunuyor; açık
permissionless bir ağda bir collection-of-arrays'i taklit eden bir
robustness özelliğini rigoröz tanımlıyor, basit ve verimli bir construction
veriyor ve robustness'ı **ispatlıyor**. Her düğüm yalnızca verinin küçük
bir kısmını saklar; **honest-majority varsayımı yapmazlar** — yalnızca
ağda minimal bir mutlak sayıda dürüst düğümün varlığına güvenirler.

**KÖK için önemi.** KÖK bir L1 olarak veri bulunabilirliğini henüz
uygulamamış olmasına rağmen, bu kaynak **honest-majority olmadan** DA
güvenliğinin kurulabildiğini gösterir — PoW tabanlı bir L1 için önemli bir
yön. KÖK'ün `kok-net` crate'i (P2P transport, block relay, DAG gossip)
üretimde bir DA katmanı değildir; bu dosya DA'nın 2025 sonu teknolojisi
olarak referans alınır.

### [D5] Pigaglio, Ascigil, Król, Rene, Lange, Peeroo, Sadre, Stankovic & Rivière — *PANDAS: Peer-to-peer, Adaptive Networking for Data Availability Sampling within Ethereum Consensus Timebounds*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2507.00824** (v1) |
| Yazarlar | Matthieu Pigaglio, Onur Ascigil, Michał Król, Sergi Rene, Felix Lange, Kaleem Peeroo, Ramin Sadre, Vladimir Stankovic, Etienne Rivière |
| Tarih | 2025-07-01 |
| URL | https://arxiv.org/abs/2507.00824 |

**İddia.** Danksharding, layer-2 verisinin seçici dağıtımını desteklemeyi
amaçlar ve bulunabilirlik rastgele DAS ile doğrulanır. DAS'ı Ethereum
konsensus sürecine entegre etmek zordur çünkü layer-2 veri parçalarının her
konsensus slot'unun başlangıcından itibaren **dört saniye içinde** dağıtılıp
örneklenmesi gerekir; mevcut hiçbir çözüm bu kadar sıkı zaman sınırları
altında dağıtım ve örneklemeyi destekleyemiyor. PANDAS, Ethereum protokollerini
değiştirmeden bu gereksinimler altında DAS'ı entegre etmenin pratik bir
yolunu sunuyor; 1.000-düğümlü bir cluster'da prototype değerlendirmesi ve
20.000 peer'e kadar simülasyonla 4-saniye deadline içinde kaldığını gösterir.

**KÖK için önemi.** DA'nın **zamanlama** yönü — KÖK'ün G-layer'ı saniyeler
içinde blok üretiyorsa, DA örneklemesinin blok üretim hızına yetişmesi
gerekir. PANDAS'ın "4 saniye" ölçütü, KÖK'ün MatMul PoW'ının (milisaniye
olarak ölçülen) yanında çok rahat bir bütçe olduğu anlamına gelir; ama KÖK
DA katmanına sahip olmadığı için bu bir tasarım referansıdır.

### [D6] Grundei, Adat Vasudevan, Konwar & Medard — *From Indexing to Coding: A New Paradigm for Data Availability Sampling*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2509.21586** (v2) |
| Yazarlar | Moritz Grundei, Vipindev Adat Vasudevan, Kishori Konwar, Muriel Medard |
| Tarih | 2025-09-25 (v2: 2026-04-29) |
| URL | https://arxiv.org/abs/2509.21586 |

**İddia.** Mevcut DAS yöntemleri genellikle **sabit-oranlı erasure code'larının
codeword'ları üzerinde kriptografik commitment'lar** oluşturur; bu, hafif
düğümleri önceden belirlenmiş bir coded-symbol setinden örneklemekle
kısıtlar. Bu çalışma, **kodlanmamış veriye commitment yapıp** örneklemeyi
"on-the-fly" kodlama ile yaparak kodlama ve commitment süreçlerini
modülerleştiren yeni bir DAS paradigması sunuyor. Sonuç örnekler çok daha
ifade gücüne sahip; yerleşik Reed-Solomon veya LDPC DAS yöntemlerine göre
**birkaç büyüklük düzeni daha güçlü** veri bulunabilirliği güvenceleri
sağlıyor. Random linear network coding (RLNC) ile somut bir protokol.

**KÖK için önemi.** DA commitment paradigmalarının 2025 sonu hali; sabit-
oranlı RS code'lara olan güvenin (Ethereum/Celestia'nın yaklaşımı)
alternatifleri olduğunu gösterir. KÖK DA'yı henüz tasarlamadığı için bu
yön bir niş meselesidir.

### [D7] Srivastava, Bhattacharjee, Arnold & Pasha — *Polynomial Multiproofs for Scalable Data Availability Sampling in Blockchain Light Clients*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2604.16559** (v1) |
| Yazarlar | Rachit Anand Srivastava, Vikram Bhattacharjee, Will Arnold, Toufeeq Pasha |
| Tarih | 2026-04-17 |
| URL | https://arxiv.org/abs/2604.16559 |

**İddia.** Hafif istemciler tam blokları indirmeden veri bulunabilirliğini
doğruladığı için ölçeklenebilir blockchain sistemlerinde zorunludur. Yaygın
bir deployment pattern'i her örneklenen hücreyi bağımsız bir KZG proof'la
ilişkilendirir; bu da önemli kümülatif bant genişliği, depolama ve
doğrulama overhead'i yaratır. Bu çalışma polynomial multiproof'ları (PMP)
inceyor: birden çok örneklenen hücre değerlendirmesinin **tek bir
toparlanmış kanıtla** doğrulanmasını sağlayan bir tasarım; proof üretimi,
dağıtımı, getirilmesi ve doğrulanmasındaki değişiklikleri tarif ediyor.
**Avail** üzerinde örnek olay olarak değerlendiriyor; proof byte'ları,
doğrulayıcı CPU/bellek kullanımı ve deployment altyapı maliyetlerinde
hücre-başına bazeline göre **%45'e kadar** azalma, ama gruplu getirme
(getirme) trade-off'ları da ortaya çıkıyor.

**KÖK için önemi.** DA doğrulama maliyetinin 2026'daki optimizasyon yönü.
KÖK'ün `kok-ledger` crate'i state/storage sahibidir ama KZG/DA commitment'ları
yoktur; eğer KÖK DA eklemek isterse multiproof yaklaşımı ile karşılaşır.

### [D8] Pham Minh, Vuong Huu & Tran — *Efficient Data Availability Sampling via Coded Distributed Arrays*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2606.16200** (v1) |
| Yazarlar | Dang Pham Minh, Hung Vuong Huu, Duc A. Tran |
| Tarih | 2026-06-15 |
| Yayın | IEEE ICBC 2026 |
| URL | https://arxiv.org/abs/2606.16200 |

**İddia.** Çoğu blockchain sistemi full-replication modeline güvenir; bu
model blok boyutuyla ölçeklenmez. Ethereum DAS'ı benimser. Önceki iş
kriptografik temellere odaklandı; DAS parçalarının discovery ve routing'ini
sağlayan P2P ağ katmanı **az incelenmiş**. CDA, network coding kullanan,
coded distributed arrays tabanlı yeni bir DAS tasarımı sunuyor; Ethereum'ın
en son DAS geliştirmesi olan RDA ile karşılaştırıyor ve **birkaç kat daha
iyi** sonuç bildiriyor.

**KÖK için önemi.** [D4]'ün RDA'sının 2026'daki halefi; DA ağ katmanı
araştırmasının aktif olduğunu gösterir.

---

## 4. MatMul / hesaplama doğrulama

### [D9] Thaler — *Time-Optimal Interactive Proofs for Circuit Evaluation*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 1304.3812** (v4) |
| Yazar | Justin Thaler |
| Tarih | 2013-04-13 (v4: 2017-02-08) |
| URL | https://arxiv.org/abs/1304.3812 |

**İddia.** GKR (Goldwasser–Kalai–Rothblum) etkileşimli kanıt protokolünün
refinement'ı; "regular" kablo desenine sahip circuit'lerde kanıtlayıcının
runtime'ını $O(S)$'ye düşürür (yani kanıt üretmenin maliyeti, kanıtsız
değerlendirmeye göre sadece sabit-katsayı bir şişme). **Yol boyunca, başlı
başına ilgi çeken özel-amaçlı bir matris çarpımı protokolü** tanımlar.

**KÖK için önemi.** MatMul için zaman-optimal etkileşimli kanıtın klasik
sonucu. KÖK'ün G-layer'ı MatMul'ı bir PoW olarak kullanır (kanıt değil);
ama U-layer faydalı işin doğrulanması için bu çizgiyi miras alacak
`kok-fri`'in (toy AIR) teorik atasıdır. **Dürüst not:** tarihi 2013'tür,
2025–2026 çalışması değildir; burada KÖK'ün FRI/AIR prototipinin hangi
teorik çizgide olduğunu belgelemek için listeleniyor, güncel bir gelişme
olduğu için değil.

### [D10] Rahimi, Khalaj & Maddah-Ali — *Range-Arithmetic: Verifiable Deep Learning Inference on an Untrusted Party*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2505.17623** (v2) |
| Tarih | 2025-05-23 (v2: 2026-06-09) |
| URL | https://arxiv.org/abs/2505.17623 |

**İddia.** Merkeziyetsiz ML'de DNN inference'ın dış katılımcılara
outsourcing'ini doğrulama. Sabit-noktalı MatMul'dan sonra yuvarlama ve
ReLU'yu sum-check protokolleri + birleştirilmiş range proof'larla
doğrulanabilir aritmetiğe dönüştürür; Boolean encoding ve büyük lookup
tablolarından kaçınır.

**KÖK için önemi.** U-layer inference doğrulamasının 2026'daki durumu.
Ayrıntılı analiz için `pouw_ai_madenciligi_2026.md` [S12].

---

## 5. Doğrulanamayan / teyit edilemeyen aramalar

- **"modular consensus", "decoupled consensus execution", "shared
  sequencer"** — arXiv'te doğrulanmış 2025–2026 birincil kaynak bulunamadı
  (aramalar ML "shared sequence" eşleşmeleri getirdi). Bu yüzden KÖK'ün
  modülerlik iddiası için bu dosyada **[D1]'in Theorem 2'si dışında bir
  literatür dayanağı listelenmez**. Bu, bilinçli bir boşluk, bir
  unutkanlık değil: "modüler" teriminin KÖK'teki anlamı (güvenlik ↔ fayda
  ayrımı) literatürdeki yaygın anlamından (consensus ↔ execution ↔ DA
  ayrımı) farklıdır ve ikisini aynı listeye koymak yanıltıcı olur.
- **Danksharding'in kendisinin resmi bir akademik özet araması** bu
  sorgularda net bir makale getirmedi; Danksharding'a atıflar yukarıda
  [D5]/[D6] üzerinden, Ethereum'un yol haritası bağlamında yapılır.

---

## 6. Bu araştırmanın KÖK için çıkarımları

1. **KÖK'ün modülerliği literatürdeki "modüler blockchain"ten farklıdır ve
   bu farklılık gizlenmemelidir.** KÖK güvenliği faydadan ayırır (G/U),
   execution'ı DA'dan değil. Dış dünyaya "modüler" denince genelde
   consensus/execution/DA ayrımı anlaşılır — README bu farkı net
   söylemelidir.
2. **GHOSTDAG için selfish-mine analizi artık otomatik yapılabilir**
   ([D2]) — KÖK'ün koşmadığı, ama koşabileceği bir analiz. KÖK'ün
   `kok-ghostdag` sürümü hâlâ "no PoW/validity check" ile sınırlıdır.
3. **DA'da honest-majority varsayımı gerekmiyor** ([D4]) — PoW L1 için
   önemli. KÖK'ün DA'sı yoktur, ama eğer eklenirse bu yönelim çakışmaz.
4. **DA zamanlaması KÖK için şimdilik bir sorun değildir** ([D5]): PANDAS'
   ın 4-saniye bütçesi KÖK'ün milisaniyelik G-layer üretimine göre çok
   geniştir — ama bu, KÖK'ün DA'sı olmadığı için ileriye dönük bir nottur,
   mevcut bir kapasite değildir.
5. **MatMul doğrulamanın tarihi ataları bilinmelidir** ([D9]): KÖK'ün
   `kok-fri` toy AIR'i GKR/Thaler çizgisindedir; üretim ölçeğinde
   Range-Arithmetic ([D10]) gibi yönlere ihtiyaç vardır.
