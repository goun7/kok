# LEÇVE — Akademik zemin eki (2026-10-07): konsensüs

> **README'ye eklenecek literatür ekidir.** Mevcut `README.md` içeriğine
> **dokunulmamıştır**; bu dosya `docs/` altında YENİ dosya olarak teslim
> edilmiştir (goal: doc bağlarını genişlet).
>
> **FP0:** aşağıdaki her alıntı `web_fetch` ile **HTTP-200 + tam başlık birebir
> eşleşmesi** ile doğrulanmıştır. Uydurma alıntı yoktur. Kanıt:
> [`orkestrasyon/docs/fp0_arxiv_manifest_2026-10-07.json`](../../00_TAMGA-MESH/orkestrasyon/docs/fp0_arxiv_manifest_2026-10-07.json).

---

## Akademik zemin — 2026-09-22..2026-10-07 penceresi (consensus)

KÖK, modüler konsensüs L1 olarak GHOSTDAG-tipi DAG konsensüsü ve faydalı
PoW üzerine kuruludur. Son pencerenin üç makalesi, KÖK'ün DAG-BFT ekseni için
en güncel akademik zemin:

- **Flamingo: On Load Balancing in DAG-based Consensus Protocols**
  ([arXiv:2609.28361](https://arxiv.org/abs/2609.28361), Khor/Gupta/Amiri/Loo,
  cs.DC, 23 Eyl 2026) — DAG-tabanlı konsensüs protokollerinde **yük
  dengelemenin** nasıl yapılması gerektiğini inceler: DAG yapısında düğümler
  arası mesaj yükü dengesiz dağıldığında performans düşer ve bu denge, protokol
  tasarımının birinci-sınıf bir parçası olmalıdır. KÖK'ün DAG katmanı için
  doğrudan ilgili: faydalı-PoW iş yükü düzensiz geldiğinde DAG katmanı bunu
  nasıl emecek? **Fark:** Flamingo genel-dağıtık DAG konsensüsünü ele alır;
  KÖK'ün tezi farklı — DAG katmanına **faydalı iş** (AI-tensor) taşıyarak
  yükün kendisini ekonomik değere dönüştürür. Flamingo'nun yük-denge
  bulguları, KÖK'ün U-katmanının DAG üzerindeki dağılımını tasarlarken
  kullanılması gereken zemin.

- **Adaptive Switching Between Leader-Based and Leaderless BFT Protocols**
  ([arXiv:2609.31388](https://arxiv.org/abs/2609.31388),
  Bhujel/Li/Zhang/Hou/Lou/Xiao, cs.DC, 25 Eyl 2026) — BFT protokollerinde
  **lider-tabanlı ve leadersiz modlar arasında uyarlamalı geçiş** yapmayı
  önerir: ağ koşullarına göre liderli (düşük gecikme) veya leadersiz
  (lider hattı kesintisine dayanıklı) kipe geçilir. KÖK'ün modüler
  konsensüs teziyle birebir aynı eksen — konsensüs, tek bir sabit
  algoritma değil, duruma göre seçilen modlar dizisi. **Fark:** makale
  **klasik BFT** çerçevesinde (token/leader hattı) uyarlamayı ele alır;
  KÖK bunu **faydalı-PoW + DAG** bağlamına taşır: mod seçimi yalnız ağ
  koşuluna değil, U-katmanındaki iş yükünün yoğunluğuna da bağlıdır.

- **Seamless Reconfiguration for DAG-BFT** ([arXiv:2610.00896](https://arxiv.org/abs/2610.00896),
  Hu/Jehl/Franke-Bergmann/Li/Berger, cs.DC, 1 Eki 2026) — DAG-BFT
  protokollerinde **kesintisiz yeniden yapılandırma** (seamless
  reconfiguration) sağlar: ağın üye/katman yapısı değişirken konsensüs
  durmadan güvenli kalır; FLP imkânsızlık sonucu nedeniyle asenkron
  ağlarda bu ancak belirli desenlerle mümkündür. KÖK'ün pre-testnet
  aşaması için kritik zemin: ağ büyüdükçe DAG-BFT katmanını durdurmadan
  yeniden yapılandırmak gerekir. **Fark:** makale üyelik yeniden
  yapılandırmasına odaklanır; KÖK için ek bir boyut daha var —
  **faydalı-PoW doğrulayıcı kümesi**nin değişimi, üyelik değişimiyle
  aynı anda güvenli geçmeli (G-katman güvenliği + U-katman faydası).

---

*Bu ek, `README.md`'nin akademik zemin bölümüne eklenmek üzere hazırlanmıştır.*
