# Sybil Direnci ve Faydalı İş — 2025–2026 Akademik Durum

**Doğrulama yöntemi.** Bu dosyadaki her kaynak bu oturumda **fetch edilerek** okundu:
arXiv kaynakları `export.arxiv.org/api/query` üzerinden (`id_list` ile birebir sorgu;
başlık, yazar listesi, özet, tarih ve kategori o yanıttan alındı), Demirel
`eprint.iacr.org/2026/1492` üzerinden. Tanımlayıcılar tahmin edilmedi; hiçbir kaynak
"bilinen bir makale" olduğu için listelenmedi.

**Tarih.** arXiv API sorgu zaman damgası: `2026-09-29T09:10Z`. Bu dosya **29 Eylül
2026** itibarıyla yazıldı.

**Bu dosyanın tek iddiası.** KÖK'ün "faydalı iş" seçiminin Sybil direncini
**iyileştirmediğini** söyleyen 2026 kaynakları bulundu ve bu dosya o bulguyu
gizlemek yerine dosyanın merkezine koyar. Faydalı iş, israfı azaltır — bu başka bir
iddiadır ve aşağıda karıştırılmaz.

---

## 0. Sorunun KÖK'teki hali — kodun kendisi söylüyor

KÖK'te Sybil yüzeyi, kaynağını kodun kendi yorumundan alır
(`crates/kok-u-layer/src/assign.rs:22–30`):

> "the miner evaluates the VRF under ITS OWN key, and the assignment probability is
> meant to be weighted by stake or compute. Because the key is per-miner, splitting
> one stake across N registered keys multiplies the number of independent draws by N
> — a single identity gets N tickets instead of one. The VRF cannot fix this: it makes
> each draw verifiable, not the number of draws honest."

Bu, dosyanın geri kalanının neden bu yazıldığını belirler: KÖK'ün Sybil yüzeyi
kaynak tasarımıdır, protokol ince ayarı değildir — ve aşağıdaki [Y1] tam olarak bunu
teorik olarak söyler.

---

## 1. Merkezi sonuç: paralelleştirilebilir kaynaklar Sybil maliyetini amorti eder ★

### [Y1] Maleki, Sainz, Legarda & Santos-Grueiro — *Scarcity Is Not Enough: Structural Limits of Linear Sybil Cost Under Parallelizable Resources*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2605.29651** (v2) |
| Yazarlar | Homayoun Maleki, Nekane Sainz, Jon Legarda, Igor Santos-Grueiro |
| Tarih | 2026-05-28 |
| Kategori | cs.CR |
| URL | https://arxiv.org/abs/2605.29651 |

**İddia (özetten).** İzinsiz (permissionless) sistemler Sybil saldırılarını etkiyi
kıt kaynaklara bağlayarak savuşturur. Ama hesaplama, sermaye ve diğer yeniden
kullanılabilir kaynaklar üzerine kurulu sistemlerde etki yoğunlaşması, protokol
tasarımlarındaki büyük farklılıklara rağmen devam ediyor. Soru şu: yoğunlaşma
başlıca protokol kurallarının sonucu mu, yoksa altta yatan kaynağın **yapısal**
özelliklerinin sonucu mu? Adversarial maliyet fonksiyonu $C(s,T)$ üzerinden — $s$
bağımsız katılımcıyı kontrol etmeye eşdeğer etkiyi $T$ uzunluğundaki bir ufukta
sürdürmenin minimum harcaması — aksiyomatik bir kaynak taksonomisi geliştiriyorlar.

Sonuçlar: **bölünebilirlik (divisibility), etkinin toplanabilirliği (additivity of
influence), zamansal yeniden-kullanılabilirlik (temporal reusability) ve kimlik
aktarılabilirliği (identity transferability)** sağlayan kaynak–mekanizma çiftleri etki
amortismanına izin verir ve $C(s,T) = o(sT)$ verir. Bunun tersine, **verimi sınırlı
(throughput-bounded), aktarılamaz (non-transferable), pencere-yerel (window-local)**
kaynaklar $C(s,T) = \Omega(sT)$'yi zorunlu kılar ve marjinal maliyet $\Delta(s,T) =
\Omega(T)$ zamanla artar. Bu, amortisman kabul eden kaynak sınıfları ile doğrusal
maliyet zorunlu kılanlar arasında **asimptotik bir ayrım** gösterir. Çıkarılan ders
açıkça yazılmış: *"these results shift the focus of decentralization from protocol
design to resource design."* Aynı özellikler, yoğun kontrolin delegasyon, havuzlama
veya **kimlik çoğaltma** (identity replication) yoluyla nominal olarak ayrı birçok
katılımcıya yansıtılmasını sağlar.

**KÖK için önemi — bu dosyanın en dürüst negatif bulgusudur.** KÖK G katmanı etkiyi
**hesaplamaya** bağlar (MatMul PoUW). Hesaplama, [Y1]'in taksonomisinde bölünebilir,
toplanabilir ve zamansal olarak yeniden-kullanılabilen bir kaynaktır — yani amortisman
kabul eden sınıftadır. **Dolayısıyla KÖK, faydalı iş sayesinde PoW'dan daha iyi bir
Sybil direnci iddia edemez.** [Y1]'in analizi, KÖK'ün G katmanının Sybil-maliyet
profilinin Bitcoin'inkini izlediğini öngörür. Bu bir tasarım kusurunun itirafı değil:
faydalı işin satış noktası **israfı azaltmaktır**, Sybil direncini artırmak değildir —
ve bu iki iddia aşağıda kasıtlı olarak ayrı tutulur.

**Dürüst sınırlar.** (a) [Y1] bir özellik sınıflandırması ve asimptotik ayrımdır;
KÖK'ün MatMul kaynağının [Y1]'in aksiyomlarını sağladığı **ispatlanmamıştır**, tasarım
sezgisiyle eşleşir. (b) Makale "yoğunlaşma kalıcıdır" demez — kaynak tasarımının
protokol tasarımından önce geldiğini söyler. (c) KÖK'ün U-ağırlık sıfır kararı
(aşağıda §3) bu makaleden bağımsız gerekçelerle alınmıştır; [Y1] onu haklı çıkarmaz,
sadece Sybil yüzeyinin G katmanında olduğunu teyit eder.

---

## 2. KÖK'ün bilinçle yapmadığı şeyin yayımlanmış örneği: itibar ağırlığı

### [Y2] Stefanović — *Proof of Useful Attestation: A Consensus Primitive for Attestation-Native Chains*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2605.25844** (v1) |
| Yazar | Stefan Stefanović |
| Tarih | 2026-05-25 |
| Kategori | cs.CR |
| URL | https://arxiv.org/abs/2605.25844 |

**İddia (özetten).** Generic PoS zincirlerinde doğrulayıcılar, attestation işini
doğru yapsa da seçici olarak sansürlese de aynı fee'leri kazanır; ana ekonomik
aktivitesi attestation kaydetmek olan zincirler (içerik provenance, **AI-output
attribution**, threshold-imzalı kimlik bilgileri, tedarik zinciri makbuzları) için bu
bir sorundur. **PoUA**, attestation işini konsensus ağırlığının kendisine birinci
sınıf yapar: doğrulayıcı oy ağırlığı = bonded stake × $[r_{min}, r_{max}]$ aralığında
bir itibar skaleri ve bu skaler geçerli attestation işinden birikir. Itibar güncellemesi
additif, fee-ağırlıklı, **aktarılamaz (non-transferable)** ve epoch başına capped.
**Lemma 1 (cost-to-grind floor):** zincir geneli adaptive burn fraksiyonu
$\tau_{burn}$ altında, bir adversary'nin itibarı $\Delta_r$ kadar şişirmek için
ödediği geri-alınamaz maliyet $\tau_{burn} \cdot \Delta_r / (\eta \cdot \alpha_{eff})$
ile alttan sınırlıdır. Önerilen v0 kalibrasyonu ($r_{max}/r_{min} \in [4,10]$) ile
sabit-durumda sermaye adversary'sine karşı maliyet primi, eşdeğer saf-stake PoS'in
**4x–10x** üstündedir. Makale ayrıca altı katmanlı Sybil ve grinding savunması, tüm
katmanlı savunma üzerinden ampirik Monte Carlo strateji-araması ve açık threshold
türetmeleriyle grinding dedektörleri içerir. Kendi ifadesiyle bir mekanizma-tasarımı
önerisidir ve eksiksiz bir kriptografik güvenlik ispatı değildir; bu sürüm Jiangshan
Yu (University of Sydney) ve Marko Vukolić (Bitcoin Scaling Labs) geri bildirimlerini
içerir.

**KÖK için önemi.** PoUA faydalı işi konsensus ağırlığına koyar (itibar × stake). KÖK
ise U katmanına **tam olarak sıfır** ağırlık verir
(`kok-u-layer/src/lib.rs:112` her zaman `0` döner). İkisi de aynı boşluğa farklı
yanıtlardır. İlginç olan [Y1] ile birleşince belirir: PoUA'nın itibarı **aktarılamaz**
ve **epoch başına capped** — yani [Y1]'in taksonomisinde doğrusal maliyet zorunlu
kıldığı sınıfa daha yakın bir kaynaktır. KÖK'ün G katmanı ise hesaplama üzerine olduğu
için [Y1]'in amortisman sınıfındadır. **Dürüst tespit:** KÖK'ün seçimi Sybil maliyetini
iyileştirmez, ama PoUA'nınkine göre bir avantajı vardır — fayda ağırlığı olmadığı için
talep satın alarak güvenlik satın almak mümkün değildir (bkz. §3).

**Dürüst sınırlar.** (a) PoUA bir tekliftir ve kendi itirafıyla eksiksiz bir güvenlik
ispatı değildir; KÖK onu bir benchmark olarak alır, bir standart olarak değil.
(b) KÖK'ün zero-ağırlık seçimi [Y2]'den değil Demirel [Y3] Theorem 2'den gelir.
(c) KÖK'ün U katmanı şu anda **toy ölçekte** (q=97, n=8) ve gerçek bir attestation
piyasası değildir; PoUA'nın hedeflediği "AI-output attribution" ölçeğinde değildir.

---

## 3. KÖK'ün teorik merkezi: serbest pseudonym altında talep kanıtı iş kanıtı değildir

### [Y3] Demirel — *Proof of Demand Is Not Proof of Work: On the Limits of Demand-Weighted Consensus under Free Pseudonyms* ★

| Alan | Değer |
|---|---|
| Tanımlayıcı | **ePrint 2026/1492** |
| Yazar | Ömer Demirel (Snowfall Finance LLC) |
| Tarih | received 2026-07-21, revised 2026-08-23 |
| Kategori | Applications |
| URL | https://eprint.iacr.org/2026/1492 |
| Lisans | CC BY |
| **Bu oturumda doğrulendi** | `https://eprint.iacr.org/2026/1492` fetch edildi (17 253 bayt); başlık ve 2026-07-21 tarihi sayfada teyit edildi |

**İddia.** PoUW hesaplama zorluğunu sertifikalar, **faydayı değil**. Üç özelliği ayırt
eder — iş sağlamlığı W, iş bağlaması B, talep egzogenliği E — ve boşluğu **E**'de
konumlandırır. **Bu dosya için doğrudan ilgili iki sonuç:**

- **(i) Lemma 1:** koalisyon kontrolündeki talepkâr ve worker arasındaki ödemeler
  **geri kazanılabilir transferlerdir** ve **Sybil-dirençli maliyete katkıda
  bulunmazlar**, bu yüzden hiçbir güvenlik alt sınırı nominal değerlerini sayamaz.
  Bu, [Y1]'in "identity replication / amortization" yüzeyinin iktisadi ikizidir:
  serbest pseudonym altında ödemeler etki satın alamaz.
- **(ii) Theorem 2:** sıfır-talep tasarım normunu karşılayan, her admissible talep
  ortamında güvenli ve canlı olan ve null-talep projeksiyonu altında kapalı olan her
  mekanizma, hizmet makbuzlarının **talep bileşeninden bağımsız bir lider-seçimi
  yoluna** sahip olmalıdır. Yapısal olarak: her yerleşmiş ödeme üzerinde **geri
  alınamaz bir vergi** (burn), güvenlik kaynağı yapan şeydir — "bağımsızlık kanıtı"
  değil.

**KÖK için önemi — bu projenin teorik merkezidir.** Theorem 2, KÖK'ün iki-katmanlı
tasarımının **gereklilik yönündeki** argümanıdır: Layer G lideri seçer, Layer U'nun
konsensus ağırlığı tam olarak sıfırdır. Kod ifadesi:
`kok-u-layer/src/lib.rs::u_task_consensus_weight` her zaman `0` döner; ayrılığın üç
katmanlı uygulaması (`kok-consensus/src/lib.rs`): yapısal (GHOSTDAG `Block` tipinin
U proof alanı yok), tipte (imza "bu U proof'unu ağırlıklandır" ifade edemez), ölçülen
(çok high-fee U proof'lu blok ile hiç olmayanın aynı `blue_score` ve `pay_set`'i).

**Dürüst sınırlar.** (a) Theorem 2'nin önşartları vardır ("her admissible talep
ortamında güvenli ve canlı" + "null-talep projeksiyonu altında kapalı"); KÖK'ün
bunları sağladığı bir **ispat** değil, bir tasarım uyumudur. (b) Demirel'in kendi
ifadesiyle seçim tarafındaki başarısızlık bir **model tahminidir**, dağıtılmış bir
gözlem değildir. (c) Burn mekanizması KÖK'te bir **protokol fee politikasıdır**
(`kok-u-layer`: "never a supply-reduction promise"), tedarik azaltma vaadi olarak
konumlandırılmaz.

---

## 4. VRF grinding yüzeyi — atama kodunun adres ettiği sınıf

### [Y4] Zhu, Rethinasamy, Armenakas, Satsangi, Eloul & Shaydulin — *Verifiable Random Sampling*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2607.26734** (v1) |
| Yazarlar | Yeoh Wei Zhu, Soorya Rethinasamy, Anthony Alexiades Armenakas, Yash Satsangi, Shaltiel Eloul, Ruslan Shaydulin |
| Tarih | 2026-07-29 |
| Kategori | cs.CR |
| URL | https://arxiv.org/abs/2607.26734 |

**İddia (özetten).** VRF'ler, belirli bir girdi üzerinde özyinelemeli bir fonksiyonun
herkesçe doğrulanabilir değerlendirmelerini gerektiren uygulamaların temelidir. Ama
public key bir kez yayımlandığında, indüklelenen fonksiyon sabittir ve girdinin
**deterministik** bir fonksiyonudur. Bu determinizm, adversary'lerin elverişli
girdi–çıktı çiftlerini önceden hesaplayıp seçici olarak sömürdüğü **collusion ve
grinding türü saldırıları** mümkün kılar. Çözüm olarak **verifiable random sampling
(VRS)** kavramını tanıtırlar; somut VRS inşası bugünün kuantum cihazlarında
çalıştırılabilen random quantum circuit sampling (RCS) temellidir.

**KÖK için önemi ve KÖK'ün kayıtlı duruşu.** Bu makale KÖK'ün kendi atama kodunda zaten
kayıtlıdır (`crates/kok-u-layer/src/assign.rs:32–46`) ve kod onu **bir benimseme
adayı olarak değil, haritalanmış bir gelecek olarak** kaydeder — iki tehdit modeli
aynı değildir: KÖK'ün yüzeyi bir stake'in bölündüğü **anahtar sayısıdır**,
girdi–çıktı çiftlerinin seçimi değil; bu yüzden bir "freshness" düzeltmesi
kayıt-katmanı bölmesini durdurmaz. Ayrıca makalenin inşası kuantum donanımı varsayar.
Kod şunu söyler: *"It is the citation the paragraph above would move under if a
classical, hardware-free construction with freshness emerges."* Bu dosya o duruşu
değiştirmez.

---

## 5. Sybil tespiti ve ölçümü — KÖK'te henüz olmayan kapasiteler

### [Y5] Bartnicki & Chudziak — *Compression-Based Behavioral Similarity for Open-World Sybil Discovery on Ethereum*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2607.27370** (v1) |
| Yazarlar | Michał Bartnicki, Jarosław A. Chudziak |
| Tarih | 2026-07-29 |
| Kategori | cs.LG |
| URL | https://arxiv.org/abs/2607.27370 |

**İddia (özetten).** Sybil saldırganları, airdrop'ları sömürmek veya yönetimi
etkilemek için normal kullanıcıların özelliklerini benimseyen blockchain aktörleridir.
Mevcut tespit yöntemleri graf inşası içerir (incelenen cüzdanlar arasında token
transferi gerektirir) veya kapalı-küme sınıflandırma problemi olarak ele alır — bu
onları saldırı stratejisindeki veya kaçırtma taktiklerindeki sık değişimlere karşı
savunmasız yapar. Makale, doğrudan finansal bağlantılar **olmadan** sıkıştırma-tabanlı
benzerliğin Sybil botlarını, organik kullanıcıları ve arbitraj bot cüzdanlarını
ayırt edip edemeyeceğini sorar; yüksek-sinyal sözleşmelerin Sybil keşfindeki etkisini
ve behavioral grafların zamansal kayma (temporal drift) ile adversarial pertürbasyon
altındaki sağlamlığını inceler.

**KÖK için önemi.** Bir **ölçüm** geleneğinin 2026'daki halidir ve KÖK'ün henüz
**hiçbir** zincir-üstü Sybil tespiti yoktur. KÖK'ün Sybil yüzeyi kayıt katmanında
olduğu için (§0), bu tarz davranış-tabanlı analiz KÖK'te bir geçiş katmanı analizi
olurdu. **Dürüst sınır:** KÖK'ün U katmanı bir toydur ve bir anahtar setine yayılmış
fiili madenci davranışının zincir-üstü ölçümü, bu dosyanın yapamadığı bir şeydir —
mevcut durumda "ölçülecek zincir" henüz yoktur.

### [Y6] Zhang & Bojja Venkatakrishnan — *Rethinking Collaborative Trust for Verifiably Decentralized Blockchain Systems*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2606.29826** (v1) |
| Yazarlar | Yunqi Zhang, Shaileshh Bojja Venkatakrishnan |
| Tarih | 2026-06-29 |
| Kategori | cs.CR |
| URL | https://arxiv.org/abs/2606.29826 |

**İddia (özetten).** Ölçüm çalışmaları blockchain'lerde belirgin bir merkeziyetsizlik
eksikliği tespit etti; merkezileşme neredeyse tüm katmanlarda, dApp'lerde ve DAO'larda
gözlemlendi ve birçok durumda merkezileşmenin boyutunu kesin olarak belirlemek pratik
olarak imkansız. Makale, doğrulanabilir şekilde merkeziyetsiz blockchain sistemleri
için genel bir çerçeve geliştirir; çekirdek gözlemi **kullanıcılar arasındaki
işbirlikli etkileşimlerin zenginliği ve çeşitliliğinin — kaynak tek biçimliliğinin
değil** — merkeziyetsizliğin temeli olduğudur.

**KÖK için önemi.** [Y1] ile uyumlu ikinci bir "kaynak tasarımı protokol tasarımından
önce gelir" sesi. KÖK'teki karşılığı açıktır: G katmanı bir MatMul kaynağına bağlı
olduğu için [Y1]'in amortisman sınıfındadır ve [Y6]'nın "kaynak tek-biçimliliği"
eleştirisi KÖK için de geçerlidir. **Dürüst sınır:** [Y6] genel bir çerçevedir ve
KÖK'ü değerlendirmez; uyum bir okumadır, bir uygulamadır.

### [Y7] Bara — *Epistemic Sybil Resistance: Multiplying AI Agents Without Multiplying Evidence*

| Alan | Değer |
|---|---|
| Tanımlayıcı | **arXiv 2609.01873** (v1) |
| Yazar | Marc Bara |
| Tarih | 2026-09-01 |
| Kategori | cs.AI |
| URL | https://arxiv.org/abs/2609.01873 |

**İddia (özetten).** Çok-ajanlı AI sistemleri, ajanları çoğaltıp raporları
birleştirerek çıkarımı iyileştirir. "Başka bir ajan başka bir gözlem değildir":
görünüşte bağımsız raporlar aynı kanıttan türemiş olabilir ve gerçekten bağımsız
kanıt neredeyse özdeş raporlar üretebilir. Bu bir **epistemic Sybil problemi** olarak
biçimlendirilir: $Z$ raporu, $R$ raporlarına göre $I(\Theta; Z \mid R) = 0$ olduğunda
epistemic bir Sybil uzantısıdır. Hiçbir sadece-rapor-çeviceleyen (report-only)
agregatör genelde çoğaltmayı bağımsız doğrulamadan ayırt edemez: özdeş raporlar
gözlemlenmemiş soyağacı altında farklı sonsal (posterior) değerler hak edebilir. Bir
Gaussian shared-root modeli, ortak soyağacının tam gereksizlik anlamına gelmediğini
gösterir; tekrarlı çıkarma bir kaynak-seviyesi tavanına doğru bilgi ekler.

**KÖK için önemi.** KÖK'ün U katmanı bir AI görev piyasası olarak tasarlanmıştır; bu
makale, "ajan sayısının kanıt sayısı olmadığını" Sybil terminolojisinde formüle eden
2026 kaynağıdır. Yönü şudur: eğer U katmanı görev çıktılarını ağırlıklı olarak
kullansaydı (ki kullanmaz), AI-ajan Sybil'leri tehdit sınıfı olurdu. **Dürüst sınır:**
[Y7] çıkarım-agregasyon içindir, konsensus değildir; KÖK'ün U katmanı sıfır konsensus
ağırlığına sahip olduğu için bu tehdit modeli KÖK'te **doğrudan geçerli değildir** —
ama bir gün U çıktılarının ağ güvenliğine bağlanmak istenirse, bu makale o
yöndeki uyarıdır.

---

## 6. Doğrulanamayan / teyit edilemeyen aramalar

- **"proof of useful work" + "sybil resistance" birlikte** — arXiv'te 2025–2026'da bu
  iki terimi birlikte ele alan ve PoUW'nin Sybil direncini iyileştirdiğini **söyleyen**
  doğrulanmış bir kaynak bulunamadı. Aranan terimlerle eşleşen çalışmalar ya Sybil
  tespiti ([Y5]) ya da kaynak taksonomisiydi ([Y1]). **Bu boşluk bırakıldı, çünkü
  doldurulacak doğrulanmış kaynak yok** — ve §7'deki ana sonuç tam olarak bu boşluğun
  *yönünden* gelir.
- **KÖK'e özel Sybil ölçümü** — bu projede yapılmış zincir-üstü Sybil ölçümü yoktur ve
  bu dosya bir tane üretmez; §0'daki test çoklayıcıyı ölçer, ağın Sybil direncini değil.
- **Kayıt katmanı (registration-layer) Sybil çözümü** — "bir-bonded-kimlik-bir-anahtar"
  için akademik bir kaynak aranmadı; bu bir protokol bileşeni ihtiyacı olarak
  `crates/kok-u-layer/src/assign.rs`'in kapsamı dışında kaydedilir ve bu dosya onu
  akademik olarak desteklemeye çalışmaz.

---

## 7. Bu araştırmanın KÖK için çıkarımları (sadece yukarıdaki kaynaklardan)

1. **ANA SONUÇ — dürüst ve negatiftir.** KÖK'ün faydalı işi (MatMul), Sybil direncini
   PoW'a göre **iyileştirmez**. [Y1] hesaplamanın bölünebilir/toplanabilir/yeniden
   kullanılabilir olduğunu ve bu sınıfın $C(s,T) = o(sT)$ amortismanına izin verdiğini
   gösterir; KÖK'ün G katmanı bu sınıftadır. **Doğru iddia:** faydalı iş enerji
   israfını azaltmaya yöneliktir; **yanlış iddia:** Sybil direncini artırır. İkisi
   her yerde ayrı tutulmalıdır; README ve kağıt bu ayrıma sadık kalmalıdır.
2. **[Y3] Theorem 2 yine de merkezdir** — ama gereklilik olarak, bir avantaj olarak
   değil. Talep-bağımsız lider seçimi, sıfır-talep normunu karşılayan her güvenli
   mekanizma için bir gerekliliktir; KÖK'ün U-ağırlık = 0 fonksiyonu bunun koddaki
   ifadesidir. Bu, Sybil maliyetini değil, **talep enjeksiyonunun güvenlik satın
   almasını** engeller — farklı bir özellik.
3. **[Y2] KÖK'ün yapmadığının yayımlanmış örneğidir.** Faydalı işi ağırlığa koymak
   (itibar × stake) bir cevap olarak mevcuttur; KÖK kasıtlı olarak bunu yapmaz ve
   nedeni [Y3]'ün Lemma 1'i: serbest pseudonym altında talepkâr–worker ödemeleri geri
   kazanılabilirdir ve Sybil-dirençli maliyete katkıda bulunmaz.
4. **Kayıt katmanı çözülmedi.** KÖK'ün Sybil yüzeyi kodun kendisinde yazılıdır (§0):
   bir stake N anahtara bölününce çekiliş sayısı N ile çarpar. VRF bunu düzeltmez
   ([Y4] grinding sınıfını adlandırır ama KÖK'ün yüzeyi farklıdır). Çözüm
   bir-bonded-kimlik-bir-anahtar'dır ve **bu crate'in kapsamı dışındadır** — KÖK'ün
   açıkta duran en büyük Sybil sorusudur ve bu dosya onu kapatmaz, işaretler.
5. **[Y5], [Y6], [Y7] birer kapasite işaretidir.** Zincir-üstü Sybil tespiti,
   doğrulanabilir-merkeziyetsizlik ölçümü ve AI-ajan Sybil'leri, KÖK'te henüz olmayan
   veya henüz geçerli olmayan şeylerdir; bunlar "yapılacaklar" olarak değil, "canlı bir
   zincir olmadan var olamayacaklar" olarak kaydedilir.
