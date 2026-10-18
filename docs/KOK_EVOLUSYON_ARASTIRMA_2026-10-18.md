# KÖK EVOLUSYON ARAŞTIRMASI — 18 Ekim 2026

> **Soru:** "L1 PoUW pazarı aşırı doygun" gerekçesiyle FROZEN ilan edilen KÖK Network v2,
> başka bir yapıya evrim geçirmeli mi? Evet ise hangisine?
>
> **Yöntem:** kok repo'sundaki ana dokümanlar okundu (README, KOK_V2_PAPER.md §1–13,
> KOK_V2_TECHNICAL_SPEC.md, F3A_INVITATION_STRATEGY.md, findings.md, F0B_PRODUCTION_DESIGN.md,
> KOK_V2_CRYPTO_BRIEF.md, docs/OLCUM_D4_2026-10-17.md, docs/LECVE_2026-10-07_konsensus.md);
> MESH'in tamamı tarandı (tamga, sester, orkestrasyon/PORTFOY_SINERJI_HARITASI_2026-09-24.md,
> PORTFOY-KARAR-BRIFINGI_2026-09-28.md); web üzerinde Ekim 2026 itibarıyla pazar, rakipler,
> yayın kanalları ve talep kanıtları araştırıldı. Her iddiaya bir URL, dosya yolu veya ölçülmüş
> sayı bağlıdır. **Kod değiştirilmedi, test koşturulmadı.**
>
> **Dürüstlük beyanı:** Bu rapor projenin devamı için kanıt aramaz; kanıt nereyi işaret
> ediyorsa orayı yazar. Kullanıcı ("truth, not morale") ve portföyün kendi disiplini
> ("false claims are worse than no claims") bunu gerektirir.

---

## §0 Mevcut durum (ölçülmüş)

### 0.1 Tanım

İki katmanlı bir **L1 tasarımı**: Layer G = KW (Komargodski–Weinstein) MatMul PoW ile
talepten-bağımsız güvenlik; Layer U = asla lider seçmeyen, fee ödemeli verifiable-compute
pazarı (escrow + bond + geri-alamaz burn). Pearl'e karşı konumlanmıştır ("Anti-Pearl").
**Pre-testnet'tir**: kağıt + spec + çalışan prototipler; zincir, kullanıcı, fon yok.

### 0.2 Ölçümler

| Metrik | Değer | Kanıt |
|---|---|---|
| Commit | 388 toplam; **42 commit sadece 1–18 Ekim 2026** | `git log --since=2026-10-01 \| wc -l` = 42 |
| Hız | 97 commit/hafta — portföydeki **en pahalı** proje | kullanıcı ölçümü |
| Testler | 1.568 Python + 397 Rust PASS, 0 FAIL (2026-10-18) | `README.md:49-52` |
| Dosya | 79 dosya, 2.006 KB (236 git-tracked) | kullanıcı ölçümü; `git ls-files \| wc -l` = 236 |
| Kod kalitesi | **1.070 ruff error** | kullanıcı ölçümü |
| Dış varlık | **ZERO** — PyPI yok, GitHub remote yok, landing page yok | kullanıcı ölçümü |
| Kâğıt | `KOK_V2_PAPER.md` 2.310 satır; `KOK_V2_REFERENCES.md` 977 satır (11/11 canlı-doğrulanmış); `KOK_V2_TECHNICAL_SPEC.md` 1.031 satır; `KOK_V2_CRYPTO_BRIEF.md` 6 soruluk dış-review paketi | `wc -l` |
| Prototip | 33 çalışan `_en.py` prototipi + 2 gate scripti | `KOK_V2_PAPER.md:1321` |
| Ölçüm büyütme | FRI q=97→40.009 (6/6 kademe), forgery 0/200; GHOSTDAG 60→960 blok (6/6) | `docs/OLCUM_D4_2026-10-17.md` |
| Talep keşfi (F0) | **0 görüşme, 0 niyet mektubu** — araç kendi worked-example'larını görüşme sayıyordu, Round-4 düzeltti | `README.md:102`, `KOK_V2_PAPER.md:1937-1939` |
| Dış review | **Sıfır insan kriptograf cevabı.** Demirel e-postasına cevap yok. | `STAGE4_HUMAN_MONEY_GAP.md`, `EPOSTA_DEMIREL*.md` |

### 0.3 Çelişki tablosu (kendi dokümanlarından)

Raporun en önemli bulgusu, kok'un **kendi iç disiplininin** ulaştığı sonuçlardır:

1. **Projeyi öldürme kriteri zaten yazılmış:** "F3a sonunda sıfır gerçek talep çıkarsa
   projenin durması gerekir" (`KOK_V2_PAPER.md:1913-1947`). F3a **başlamadı bile**.
2. **Kritik yol taleptir, kriptografi değil:** "Projeyi sürdüren şey kriptografi veya
   hukuk değil — **tek bir müşteri, tek bir iş**" (`KOK_V2_PAPER.md:1920-1924`).
3. **F0 (talep keşfi) başlamadı:** "0 görüşme yapıldı, 0 mektup imzalandı... NOT STARTED"
   (`KOK_V2_PAPER.md:1937-1939`).
4. **L1'in kıymeti kağıtta tavan yapmış:** "Mükemmel bir kâğıt çalışan bir zincire eşit
   değildir. Kâğıt tavanı ~85/100; kalan ~15 puan deneyseldir, kağıtta kazanılamaz"
   (`README.md:152-153`).
5. **Tokenomik modeli Pearl'in 108 sn varsayımı üzerine kurulu**, kendi referans kaydı
   194 sn diyor — 194 sn'de revenue/cost **1.06 değil 0.589**'a düşüyor, yanitiraf edilmiş
   girdi duyarlılığı var (`KOK_V2_PAPER.md:479-492`).
6. **F3b (consensus devnet) fundable değildir:** "2-3 mühendis × 6 ay — bugün finanse
   edilemiyor" (`KOK_V2_PAPER.md:1324`).
7. **L1 vizyonu MESH'ten izole:** "KÖK'ün 'egemen L1' tezi mevcut 80 projenin tamamından
   **izole** bir teknoloji yığını seçiyor" (hepsi EVM/Solidity; portföyde 0 .proto)
   (`orkestrasyon/PORTFOY_SINERJI_HARITASI_2026-09-24.md:16-18`).

**Sonuç:** Kok, sağlam bir şekilde FROZEN. Ama donma gerekçesi yanlış. Sorun "pazar doygun"
değildir (öyle olsa Pearl başarılı olurdu). Sorun şudur: **388 commit'in hiçbiri dışarıya
çıkmadı** — aynı hataya 9 ay önceki portföy brifing'in işaret ettiği yer
(`PORTFOY-KARAR-BRIFINGI_2026-09-28.md §0`: "tek bir e-posta gönderilmedi").

---

## §1 Pazar doğrulaması — "Aşırı doygun" DOĞRU mu?

### 1.1 Kısa cevap: HAYIR — pazar doygun değil, pazar **BOŞ**. Doygunluk ölçütü yanlış.

"L1 PoUW pazarı aşırı doygun" dense de ölçülebilir kanıtlar tam tersini gösterir: alanın
**canlı birincisi (Pearl) dahi talep kanıtlayamamışken**, "doygunluk" kelimesi yanlış
adrestedir. Pazar, çok sayıda rakiple dolu değil; **hiçbir PoUW L1'i gerçek AI-compute
geliri yayımlamıyor**. Yani sorun rekabet değil, **talebin kendisinin ölçülmemiş olmasıdır**.

### 1.2 Pearl'in Ekim 2026'daki dürüst durumu

| Kanıt | Değer | Kaynak |
|---|---|---|
| Mainnet launch | 27 Nisan 2026 | [onebullex](https://www.onebullex.com/news/articles/pearl-research-labs-launches-proof-of-useful-work-mainnet-on-april-27-2026) |
| Anlık fiyat (Eki 2026) | **~$1.85**, ATH $2.10 (14 Eki), 7 günde +%30.7, market cap ~$641M, sıralama #135 | [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2) |
| Ralyonun sebebi | **Açıklanmış bir katalizör YOK** — Ansem KOL çağrısı, Dragonfly övgüsü, No Limit Holdings pozisyonu, Token2049 yanetkinliği. Sayfanın kendisi: "No single announcement has been confirmed as the driver of the latest 24-hour move" | [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2) |
| Merkezileşme | Tek havuz network hashrate'inin **~%21'i** ve baskın madenci yazılımında **hiç inference kodu yok** (vllm/transformer/llama/safetensor: 0/4.803 string) | [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2), [arXiv 2606.04819](https://arxiv.org/html/2606.04819v2) |
| Enflasyon | ~1M yeni PRL/gün; önümüzdeki 12 ayda ~305M PRL = mevcut dolaşan arza (348.7M) **%~100 enflasyon** | [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2) |
| İlk 6 günde issuance | Castle Labs: **122M PRL** = mevcut dolaşan arzın %36'sı 6 günde basıldı | [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2) |
| İşlem likiditesi | Sadece 2 borsa (BigONE, SafeTrade), 24s hacim ~$5.67M = cap'in %0.9'u | [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2) |
| Başlangıç hashrate | 3.56 EH/s (≈BTC'nin %0.4'ü) Mayıs 2026 | [kucoin](https://www.kucoin.com/news/insight/PRL/6a1837a357e8dc00078b3caf) |
| Mining karlılığı | Basu: PRL $0.21 iken tüm GPU tier'larında **karlı değil** | [arXiv 2606.04819v1](https://arxiv.org/html/2606.04819v1) |
| Together AI anlaşması | **Tek** gerçek alıcı kanıtı — ama indirim **PRL emission ile sübvansiye ediliyor**. [hashrateindex](https://hashrateindex.com/blog/pearl-prl-ai-compute-cryptocurrency/): "most of the 'useful work' is inference nobody bought... AI-shaped proof-of-work, not useful work" | [together.ai](https://www.together.ai/blog/together-ai-partners-with-pearl-research-labs), [hashrateindex](https://hashrateindex.com/blog/pearl-prl-ai-compute-cryptocurrency/) |

**Karar:** Pearl, 24 EH/s'te çalışıyor ama **φ=0 ölçüldü**. Fiyat ralyosu KOL + enflasyon +
yarım likidite; useful-work kanıtıyla bağlantısız. **Pearl, KÖK'ün tezinin (E-gap)
doğruluğunun en güçlü kanıtıdır — rakip değil.**

### 1.3 Rakip haritası (2026 — kim gelir yayımlıyor?)

| Proje | Useful work | Konsensüs | Gelir yayımlıyor? | Kaynak |
|---|---|---|---|---|
| Pearl | LLM inference (NoisyGEMM) | PoUW | **HAYIR** — φ=0 ölçüldü | [arXiv 2606.04819](https://arxiv.org/abs/2606.04819) |
| Qubic | UPoW (Aigarth eğitimi) | PoUW | **HAYIR** | [qubic.org](https://qubic.org/faq) |
| Dynex | neuromorphic PoUW | PoUW | **HAYIR**; token'ı iptal ediyor (Şub 2026), DNX $0.00119 (−%99.91) | `KOK_V2_PAPER.md:2089`, `findings.md:77` |
| Bittensor | subnet ML görevleri | incentive chain | ~%88'i emission | `KOK_V2_PAPER.md:2087` |
| Gensyn | training → verifiable inference / oracles | PoUW değil | "not yet"; tahmin pazarlarına kaydı | `KOK_V2_PAPER.md:2090`, [gensyn.ai](https://www.gensyn.ai/) |
| **Akash** | genel GPU/CPU compute | **PoS marketplace** | **EVET** — $5M tüm zamanlar (kendi raporu); Messari: **Q1 2026'da ~$253K zincir-üzeri kira geliri, −%45 Q/Q**, yıllık ~$1M | [akash Q1 2026](https://akash.network/blog/akash-network-q1-2026-report/), [hoge.gg](https://hoge.gg/akash-network-2026-gpu-market-leaves-cosmos/) |
| Aethir | GPU cloud | DePIN | **EVET** — $127.8M/2025, $166M ARR | `KOK_V2_PAPER.md:2095` |
| Render | GPU rendering | PoS marketplace | evet, üretim | `KOK_V2_PAPER.md:2092` |

**Üçüncü-şahsın en öğretici verisi:** [hoge.gg](https://hoge.gg/akash-network-2026-gpu-market-leaves-cosmos/)
"CoreWeave tek bir öğleden sonra, açık pazarın üç ayda kazandığından fazla ciroya ulaşıyor"
(CoreWeave Q2 2026: $2.58B, ~$104B backlog). **Akash'ın ~$253K/çeyrek geliri, açık bir
compute piyasanın ne kadar küçük olduğunu kanıtlıyor.** Doygunluk değil, **tam-talef-ölçülmemiş
boşluğu** var.

### 1.4 Doygunluğun gerçek ölçütü: Doğrulama (verification) için kim para ödüyor?

2026'da kanıt-satan projelerin hepsi çöküşte:

| Proje (verification token) | Zirveden | Kaynak |
|---|---|---|
| EIGEN (EigenLayer) | −%96 | [hoge.gg](https://hoge.gg/opml-inference-verifiable-ai-training-2026/) |
| PROVE (Succinct) | −%89 | aynı |
| ZKC | −%97 | aynı |
| LA (Lagrange) | −%96 | aynı |
| PHA (Phala) | −%98 | aynı |
| ORA (opML) | ~$0.0025, cap ~$412K, günlük hacim ~$28; oracle'da "only a few thousand lifetime requests", **hiç fraud proof-file edilmemiş** | aynı |

Aynı kaynaktaki net cümleler: **"almost nobody pays extra for a proof when they could just
trust the vendor, because trusting the vendor is free"** ve **"the market is paying almost
nothing for verification sold on its own."**

[DCS Compute](https://compute.trdn.io/) her inference işine Filecoin üzerine pinned imzalı
receipt basıyor ("Phase 2 · Proof-of-Compute receipts Shipped") — yani **receipt formatı
başkası tarafından zaten implemente edilmiş**. Bu kok'a hem bir meydan okuma hem bir
talep/işaretidir.

### 1.5 Sonuç

**"Aşırı doygun" yanlış. Doğru teşhis: L1 PoUW pazarı küçük, gelir-gösterilmemiş ve
fiyat-olarak-sübvansiyonlu.** Üç olasılık:

- **(a) Pazar yok** — herkes güvene ücretsiz devam ediyor (yukarıdaki −%89..−%98 çöküş).
- **(b) Pazar var ama standardize değil** — [hoge.gg](https://hoge.gg/verifiable-compute-trilemma-proving-ai-2026/):
  EU AI Act (Ağustos 2026 yürürlük, cezalar onlarca milyon €), cüzdanlı otonom ajanlar ve
  DeFi'de sermayeyi kontrol eden modeller = 3 talep şeridi. **Ama henüz ödeme yok.**
- **(c) Pazar bir L1 değil, bir özellik (feature).** Gensyn'in Verde/Judge'ı verification'ı
  compute ile birlikte satıyor: *"opML was never going to be a standalone product so much
  as one ingredient"* ([hoge.gg](https://hoge.gg/opml-inference-verifiable-ai-training-2026/)).

**Kok'un kendi 21 Eylül 2026 tarihli teşhisi hâlâ doğru** (`KOK_V2_PAPER.md:2097-2103`):

> "Useful work with paying customers exists — in marketplaces on PoS, where it is not tied
> to block production. True PoUW exists — with no paying customer. **The two halves have
> not met in one system.**"

Cevap L1 değil, **marketplace tarafıdır**. Kok'un gitmesi gereken yer burasıdır.

---


## §2 Kok'un gerçek differentiating knowledge'ı nedir?

### 2.1 388 commit sonra ortaya çıkan bulgu (kendi LLM okuması olarak)

Kok 388 commit sonra, beş farklı seviyede gerçek bilgi üretti. Sıralama önemli:

| # | Bilgi | Tür | Kanıt | Kıymet |
|---|---|---|---|---|
| **1** | **E-gap teşhisi** — Pearl'in çöküş sebebiPW'nin çalışmaması değil, **E'nin (demand exogeneity) sağlanamaması**. W (work soundness) ve B (job binding) kriptografik olarak elde edilebilir, E elde edilemez. | Teorik, doğrulanmış (Demirel) | `findings.md:271-283`; [ePrint 2026/1492](https://eprint.iacr.org/2026/1492) | **ÇOK YÜKSEK** — 2026'nın PoUW alanının tek net teşhisi |
| **2** | **Binding-mechanism tasarımı** — verification'ın "job identity"yi değil **"computation"ı** bağlaması gerektiği. TV-82 Round-5b'de *kendi* hatasını buldu: `verify_g_cert_bound` commitment STRING'ini bağlıyordu, computation'ı değil; commissioned [[2,3],[4,5]] (tile 26) yerine madencilik [[2,3],[4,6]] (tile 30) **kabul ediliyordu**. Düzeltildi ve ölçüldü. | Deneysel, negatif-sonuç | `README.md:107`, `KOK_V2_PAPER.md:534-543` (`tv72_egap_mechanism_en.py` 5/5 ön-binding / 4/4 post-binding — `KOK_V2_PAPER.md:534-543`) | **ÇOK YÜKSEK** — bu bir *anti-pattern* dersi, herhangi bir proof-of-compute sisteminde geçerli |
| **3** | **Negatif-sonuç metodolojisi** — "bir iddia ile kod arasındaki tutarsızlığı yakalama" disiplini. Round-5'te `pass_sim_en.py`'nin theta=1.05 yerine **1.657** çıkardığını (pearl'ün PR'yi 2.0489'da 1 yerine 2.24e-16'ya yeniden üretti), FRI'nin "logaritmik verifier cost" iddiasının **linear** olduğunu (q=97'den q=2003'e 33× süre) ve ZK maskelemesinin **hiç gizlemediğini** (verifier kendi seed'ini veriyordu) buldu. Her seferinde **retract + ölç + probe ekle**. | Metodolojik | `README.md:128-150`, `docs/OLCUM_D4_2026-10-17.md` | **YÜKSEK** — taşınabilir, mesh'in tamamında uygulanabilir |
| **4** | **Anti-Pearl konumlandırma** — iki-katman (G/U) ayrımı, güvenliğin **asla** talepten gelmemesi (Demirel Thm 2), pure-PoW fallback ile her koşulda yaşam (TV-8). | Tasarım | `KOK_V2_PAPER.md:107-136`, `README.md:5-16` | **ORTA-YÜKSEK** — doğru, ama *mimari* bir katkı değil; bir **düzeltme** |
| **5** | **KW Conjecture 6.4 / A.1 analizi** — Conjecture A.1 hâlâ açık (Pearl'in kendi Polymath Problem 1), ama 6.4'ün aslında gereksiz olduğu (output-size lower bound nedeniyle) kendi bağımsız analizinde bulundu. `KW_ANALIZ.md` riski high → low-medium. | Teorik, **LLLM okuması** | `KW_ANALIZ.md`, `KOK_V2_PAPER.md:1356-1365` | **ORTA** — insan-kriptograf onayı olmadan kıymeti sınırlı |

### 2.2 KÖK'ün iddia ettiği yenilikçilikten alınanlar (dürüst geri çekmeler)

Raporun tarafsızlığı için, **kağıtın kendisinin geri çektiği** iddiaları da saymalıyız:

- **"2-for-1 faydalı PoW = bedava compute"** — geri alındı. Doğrusu: "token emisyonu ile
  sübvansiye edilmiş compute", yani **tax incidence** argümanı (`KOK_V2_PAPER.md:1546-1573`,
  Pass'in Duplexia analizi ile uyumlu: "block rewards act as REBATES on inference prices").
- **ZK (sıfır-bilgi) iddiası** — geri alındı, sonra kısmen iade edildi, sonra **doğru
  sınırlarla** yazıldı: q=97'de brute-force ~912.673 pad'i 0.25 saniyede yürüyor
  (`README.md:115`, `probe_f0b_zk_en.py` TV-65).
- **"Logaritmik doğrulama"** — ölçülünce **linear** çıktı (q=40.009'da `verify_round`
  0.10019 s; `docs/OLCUM_D4_2026-10-17.md`).
- **Pearl'in θ=1.05** — 1.657'ye düzeltildi (kendi residual checker'ı bir identity olduğu
  için 4 round boyunca yakalanmamış; `README.md:131-142`).
- **θ=1.657'ye rağmen 108 sn'lik block time girdisi**, 194 sn'de 0.589'a dönüşüyor
  — Kağıt bunu **kendisi** itiraf ediyor (`KOK_V2_PAPER.md:479-492`).

### 2.3 Kritik gerçeğin tekrarı — knowledge'ın hiçbiri dışarı çıkmadı

Yukarıdaki 5 maddenin **hiçbiri** dış dünyada yok: PyPI'de paket yok, GitHub remote yok,
landing page yok, arXiv/ePrint'te yayın yok, insan-kriykograf cevap yok. Yani:
**KOK'un varlığı, bilginin kendi başına bir varlık olmadığını kanıtlıyor.** Bilgi,
ancak bir artefakt + bir okuyucu olduğunda var. 388 commit'in hiçbiriri okunmadı.

### 2.4 WWW haritasında KÖK'ün yeri

Mesh'in [PORTFOY_SINERJI_HARITASI](../../orkestrasyon/PORTFOY_SINERJI_HARITASI_2026-09-24.md) zaten bu teşhisi koymuş:

> "KÖK'ün 'egemen L1' tezi, mevcut 80 projenin tamamından **izole** bir teknoloji yığını
> seçiyor." (hepsi EVM/Solidity)

Aynı harita KÖK U-katmanı için bir pilot iş yükü de önermiş: **19-GNoME-Forge** (GNN
inference, $490–1.490/sentez-analizi), **77-Dumen** (SAE + activation steering — "KÖK
U-katmanı için en güçlü tensor işi"), 06-KlinikKapıcı, 11-FootnoteAlpha. Yani mesh
kendisi **talep adaylarını** listelemiş — ama F3a hiç başlamadı.

---

## §3 Evrim seçenekleri

Her seçenek için: neye dönüştüğü, hangi kod/kağıt desteklediği, talep kanıtı, maliyet ve
**dürüst olasılık**.

---

### Seçenek A — L1 kağıt-only olarak kal (status quo, FROZEN'dan farklı değil)

**Neye dönüşür:** Şimdi olduğu gibi — 2.310 satırlık kağıt, 1.031 satırlık spec, 33 prototip.
Beklenen: Demirel cevap verir, kriptograflar gelir, F3a başlar.

**Destekleyen kod:** hepsi.

**Talep kanıtı:** **YOK.** Sıfır görüşme, sıfır niyet mektubu, sıfır external artefakt.
Demirel e-postasına cevap yok (2026-09-23'ten beri). 9 ay önce aynı portföy brifingi,
aynı durumu teşhis etmiş: "139 commit atıldı — ve **tek bir e-posta gönderilmedi**"
(`PORTFOY-KARAR-BRIFINGI_2026-09-28.md §0`).

**Maliyet:** 97 commit/hafta = portföydeki en pahalı proje. Her hafta L1'i kağıtta
mükemmelleştirmek, F3b'ye (2-3 mühendis × 6 ay, fundable değil) hiç yaklaşmaz.

**Dürüst olasılık:** **~%5.** Kağıt zaten ~85/100 tavanında (kendi itirafı,
`README.md:152-153`). Kalan 15 puan deneysel ve dışarı çıkmadan kazanılamaz.
Ayrıca: [hoge.gg](https://hoge.gg/opml-inference-verifiable-ai-training-2026/)'in
ölçümü: verification token'ları zirveden −%89..−%98. Bekleyiş, pazarın gelmesini değil,
kendi ölümünü bekliyor.

**KILL-condition:** zaten yazılmış (`KOK_V2_PAPER.md:1913-1947`). F3a başlamadığı için
bu seçenek halihazırda ölüm-dirayaçta.

---

### Seçenek B — Doğrulama kütüphanesine / SDK'ya küçült (verification library)

**Neye dönüşür:** Kok'un **tek başına bağımsız olarak değerli** olan parçası, G/U
L1'inin hiçbirgereksinimi olmadan: **KW MatMul PoW sertifika üreticisi + bağımsız doğrulayıcı**.
Yani `crates/` Rust workspace'inde zaten çalışan iki komut:

```bash
cargo run -q --bin kok -- create --ctx 20261020 --target 2 --out kanit.json
cargo run -q --bin kok -- verify kanit.json
```

README.md:53-56 bunu "the same code a third party would call, which is the point: the
useful work is independently verifiable off-chain" olarak yazıyor. **Yani bu zaten
var.** Bu, bir "compute-proof receipt" kütüphanesi olabilir: herhangi bir compute
provider'ın ürettiği MatMul işi için bağlanabilir, bağlam-türetilmiş, off-chain
doğrulanabilir bir makbuz.

**Destekleyen kod:** `crates/kok-consensus/` (397 Rust testi), `g_layer_tests_en.py`
(TV-1..TV-21), `f0b_air_proto.py` (AIR + Merkle commitment + FRI),
`egap_cert_en.py` (TV-77 binding), `probe_round5b_egap_en.py` (TV-82, computation-binding).

**Talep kanıtı:** **Zayıf ama sıfır değil.**
- [hoge.gg](https://hoge.gg/verifiable-compute-trilemma-proving-ai-2026/): üç talep şeridi
  – EU AI Act (Ağustos 2026 yürürlük), ajan-cüzdanlar, DeFi. **Ama verification tek başına
  satılmıyor** (−%89..−%98 token çöküşü).
- [DCS Compute](https://compute.trdn.io/) "Proof-of-Compute receipts" zaten shipping —
  formatı standart olmayan bir implementations var, yani SDK-olarak-boşluk var.
- [TRM Labs](https://www.trmlabs.com/trm-tech-blog/whos-actually-paying-measuring-ai-agent-payments-onchain):
  $52.7M x402 hacminin sadece **%0.6–7.5'i** gerçekten ajansal; önerisi **"counterparty
  reputation an agent can check on its own"** — yani bağımsız-doğrulanabilir kanıt.

**Maliyet:** **DÜŞÜK.** 79 dosyadan ~20'sini pyflakes ile seçmek, bir README + PyPI
paketı + örnek. Mevcut Rust crate'leri zaten başlangıcı verir. 1-2 kişi-hafta.

**Dürüst olasılık:** **~%20'lik gerçek başarı + %50'lik "titreyerek öğrenme".**
Başarısızlık riski: kütüphaneleri kimse indirmiyor (portföyün `dumen` 1.633 indirme /
`tamga-protocol` 2 yıldız — `PORTFOY-KARAR-BRIFINGI_2026-09-28.md §2.1`). **Ama en azından
başarısızlık ölçülebilir** (indirme sayısı, GitHub stars) — L1'de ise hiç ölçülemedi.

**KILL-condition:** PyPI'de 90 gün sonra <50 indirme → geri çek.

---

### Seçenek C — Mesh'in kanıt katmanına entegre ol (Tamga/Sester "compute-proof layer")

**Neye dönüşür:** Kok, L1 olmaktan çıkar; **Tamga'nın proof ledger'ı için "compute-proof"
nice elamanı** olur. Tamga'nın receipt-zinciri ve `x402` proof-of-done teklifi
(GitHub issue [#3379](https://github.com/x402-foundation/x402/issues/3379), 58 yorum,
halen AÇIK) tam olarak boşluğu tanımlıyor:

> "x402 ödemenin gerçekleştiğini kanıtlar ama yapılan işin yapıldığını kanıtlamaz... 'bugün makbuz
> bir ödeme ekran görüntüsü'."

Tamga'nın teklifi `scheme: "tamga-ledger-v1"` + `receiptHash`. **Kok, bu schemelerin
"compute-work" sınıfı olabilir:** agent ödeme yapmadan önce, provider'ın gerçekten
MatMul inference yaptığını kanıtlayan, Tamga'nın hash-zincirine bağlanan, kok'un
TV-82 computation-binding'ini kullanan bir makbuz.

**Neden bu raporun en güçlü önerisi olduğunu düşünüyorum — kod-kanıtıyla:**

1. **Tamga'nın receipt formatı zaten 6 proje tarafından kod-kanıtıyla tüketiliyor:**
   Sester (`AT-055/AT-056`), Veridict, PQHaven (**AT-065 5/5**), Swarmax (AT-067 6/6),
   Dümen (AT-068 6/6), Fleksa (AT-070 6/6), Tenderix (AT-071 6/6), Veridrome (AT-072 6/6).
   (`tamga/docs/PROJE-ENTEGRASYON-HARITASI.md §1` — her satır gerçek dosya+yol+AT-kilidi).
   Yani **mesh'in içinde gerçek bir tüketici tabanı var**, dışarıda aramaya gerek yok.

2. **Ajan Borsası (`borsa_core.py:70, :176`) zaten `receipt_hash: str | None` alanı
   okuyor** — Sester'a bağlı değil, sadece okuyor. Bu, RFC-010'ın 5 kontrolünden 5'incisi
    (`evidenceHash == receiptHash`) için doğal kaynak. (`PROJE-ENTEGRASYON-HARITASI.md §2`)

3. **Sester zaten x402 standardında aktif**: 649 PyPI indirme, 2.944 test, **2.944Test
   PASS rc=0 (LEED-verified 2026-10-18)**. Sester'ın ledger'i `K0_SHARED_ENVELOPE_SPEC.md
   §7-kural-9` ile Tamga'ya bağlı. Kok'un MatMul kanıtı bu zincirin **compute-work
   budunu** olabilir.

4. **TRM Labs'in birinci önerisi tam budur:** "counterparty reputation an agent can check
   on its own" + "accurate agent registration" — [TRM](https://www.trmlabs.com/trm-tech-blog/whos-actual-paying-measuring-ai-agent-payments-onchain).

5. **x402 maintainers'ı henüz karar vermedi** ama #3379'da üç-eksen tablo çıktı:
   durable-evidence (ne teslim edildi) + proof-of-done (iş yapıldı) + capacity-attest
   (alıcı onayı). **Kok'un knowledge'ı bu üçgenin "iş yapıldı" köşesinde——ve orada
   için matematiksel olarak en sağlam teklif.**

**Destekleyen kod:** TV-82 computation-binding, ctx-binding (T-A2), AIR + FRI prototipleri.
Ayrıca MESH'te halihazırda tüketici hazır: **19-GNoME-Forge** (GNN inference — "KÖK
U-katmanı için baş aday"), **77-Dümen** (torch SAE), **74-Semt** (yerel GPU'yu x402 ile
satma) — (`PORTFOY_SINERJI_HARITASI_2026-09-24.md §2.5, §3`).

**Talep kanıtı:** **ORTA.** x402 gerçek hacim (TRM: $25.62M ekranlanmış ticaret) var;
ancak verification için ayrı ödeme yok. **Bununla birlikte**, mesh'in iç talebi
somuttur: Sester'ın kendi MONETIZATION.md'si, ajan-borsası'nın receipt_hash alanı ve
RFC-008 / RFC-010'ın "PILOT-PENDING" kapıları — hepsi bir compute-kanıt kaynağı bekliyor.

**Maliyet:** **DÜŞÜK-ORTA.** L1'den vazgeçmek: GHOSTDAG, emisyon modeli, hukuk
(§9, 270+ satır SEC/MiCA/ESMA) ve tokenomik'in tümünü silmek. Kodun çoğu zaten
stdlib-only Python + Rust crate'leri. Tamga'nın receipt schemetine bir adapter ~1 ay.
Kok'un adı bile korunabilir: **"kok" = kök = DAG'ün kökü** → receipt DAG'inin kökü.

**Dürüst olasılık:** **~%40.** Neden düşük değil: mesh'in içinde 6-8 kod-kanıtla-tüketici
var, kok'un knowledge'ı boşa gitmez. Neden %100 değil: proof-of-done hâlenâ x402
maintainers'ı tarafından REDDEDİLMEDİ ama KABUL de EDİLMEDİ (issue #3379 açık, 58 yorum,
karar yok). **Ve Tamga zaten kendi receipt'leri ile bu işi yapıyor — kok'un katkısı
sadece MatMul/compute-specific kanıt sınıfı olursa anlamlı.**

**KILL-condition:** x402 #3379 kapatılırsa veya Tamga compute-proof katmanını kendi
yazarsa → kok'un bu pozisyonu da ölür. **3 ay içinde mesh içindeki en az 1 projede
kod-kanıtla-tüketilmemişse → ölüm.**

---

### Seçenek D — Öldür ve geri dönüşümleri parçala (salvage)

**Neye dönüşür:** kok repo'su bir **öğretici/kaynak** haline gelir: negative results +
methodoloji, MESH'in geri kalanına aktarılır.

**Geri alınabilir parçalar:**

| Parça | Nereye | Kanıt |
|---|---|---|
| E-gap teşhisi + Demirel okuması | MESH-genel bir `docs/E_GAP_TEŞHISI.md` (yeni tf universe) | `findings.md:269-297` |
| "Binding identity değil computation" anti-pattern dersi | Tamga'nın AUDIT-GATE + sester'ın denetim | `README.md:107` (TV-82) |
| Negatif-sonuç metodolojisi (retract + ölç + probe) | orkestrasyon/DENETIM_SOP.md | `README.md:128-150` |
| Rust crate'leri (KW prove/verify) | C seçeneğinde de kullanılabilen çekirdek | `crates/kok-consensus/` |
| 33 prototip + 2 gate | eğitim materyali, CC-BY-4.0 | `README.md:88-116` |

**Talep kanıtı:** N/A (bu bir ölüm seçeneği).

**Maliyet:** ~1 hafta (bir veda dokümanı + parçaların taşınması).

**Dürüst olasılık:** **Eğer C reddedilirse %100'e çıkar.** Tek başına D'ninavantajı:
97 commit/hafta'lık kan damarı kesilir ve MESH'in 20 diğer projesine kaynak akar.

**KILL-condition:** kendisi bir kill-condition'dur.

---

### Seçeneklerin karşılaştırma tablosu

| | A (L1 kağıt) | B (SDK/kütüphane) | **C (Mesh kanıt katmanı)** | D (öldür) |
|---|---|---|---|---|
| Var olan kodu kullanma | %100 (işlemiyor) | %70 | **%40 (en değerli kısım)** | %20 (doküman) |
| Talep kanıtı | SIFIR | zayıf (indirme) | **mesh'te 6-8 kod-kanıtlı tüketici** | N/A |
| Dış dünya ile temas | YOK | PyPI | **x402/Tamga standart süreci** | N/A |
| Ölçülebilir başarı kriteri | yok | indirme/stars | **mesh entegrasyon sayısı / x402 durumu** | kan damarı=0 |
| 97 commit/hafta maliyeti | devam | düşer | **düşer** | **0** |
| Olasılık | ~%5 | ~%20 | **~%40** | C red → %100 |

---

## §4 Yayın stratejisi (arXiv alternatifleri)

### 4.1 Kanal analizi — bağımsız/akademik-olmayan birisi gerçekten nereye yayınlayabilir?

| Kanal | Endorsement gerekir mi? | Bağımsız biri yayınlayabilir mi? | Tür | Notlar |
|---|---|---|---|---|
| **arXiv** | **EVET.** 21 Ocak 2026'dan itibaren institutional email tek başına yeterli DEĞİL: ya (1) institutional email + o endorsement-domain'inde kabul edilmiş ortak-yazar makale, ya da (2) aynı domain'de bir arXiv yazarından kişisel endorsement. [blog.arxiv.org](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/), [info.arxiv.org/help/endorsement.html](https://info.arxiv.org/help/endorsement.html) | **Teknik olarak HAYIR** (endorser bulmadan) | preprint | Kullanıcının durumu: e-postalara cevap alamıyor. **Yol arıyor olmak, 9 ayda sıfır external artefact'tan daha kolay değil.** |
| **IACR ePrint** | **HAYIR.** | **EVET — en uygun kanal.** | preprint (modere) | [eprint.iacr.org/operations.html](https://eprint.iacr.org/operations.html): "Any author can submit a paper with a technical contribution in the field of cryptology." Hiçbir affiliation/endorsement koşulu YOK. Şartlar: cryptology alanı, açık-okunaklı, **proofs or convincing arguments**, isim+iletişim adresi (anonymous değil). **Kok'un içeriği tam bu şartlara uygun** (KW + Demirel + toy proofs). Önceki örnekler mevcut: [2026/1628](https://eprint.iacr.org/2026/1628) (Blockstream'den bağımsız görünen yazar). |
| **Zenodo** | **HAYIR.** | **EVET.** | herhangi araştırma artefaktı + DOI | [about.zenodo.org/policies](https://about.zenodo.org/policies/): "Anyone may register as user of Zenodo. All users are allowed to deposit content for which they possess the appropriate rights." 50GB/record, CERN-backed, 20+ yıl, DOI verir. **Hepsi alanlar kabul edilir, tüm formatlar.** |
| **SSRN** | **HAYIR** (ama editöryel tarama var). | **Muhtemelen EVET** — affiliation kısıtlaması bulunamadı | sosyal bilimler preprint | [casrai.org](https://casrai.org/guides/ssrn-how-it-works-for-researchers): ücretsiz, "administrative, not peer review". Ama **ekonomi/hukuk/finans odaklı** — kok'un $\S9$ hukuk bölümü için uygun, kriptografi için DEĞİL. |
| **HAL** | Affiliation gerekir (Fransız kurum). | **HAYIR** (arXiv-transfer yolu dahil) | portail d'archive | [CCSD](https://www.ccsd.cnrs.fr/en/2026/03/do-arxiv-s-rule-changes-have-an-impact-on-hal/): "being affiliated with a French institution" şart; CCSD/HAL endorsement vermez. |
| **OSF Preprints** | **HAYIR** | **EVET** (upload + metadata) | preprint | [cos.io](https://www.cos.io/products/osf-preprints): "makes sharing research as easy as uploading a file". **Az_visible, kriptografi topluluğu okumuyor.** |
| **ResearchGate** | HAYIR | EVET (ben-upload) | sosyal ağ | Kontrol-dışı, spam-uyumlu; akademik ağırlığı düşük. |
| **Blog + GitHub repo** | HAYIR | **EVET** | genel | **En az güvenilir ama en erişilebilir.** Örnek: [hoge.gg](https://hoge.gg/verifiable-compute-trilemma-proving-ai-2026/) tarzı analizler gerçek etki yaratıyor (bu rapor da onları okudu). |

### 4.2 Konkret öneri: **IACR ePrint + Zenodo, ikisi birlikte**

1. **IACR ePrint'e kriptografik kısım.** Kok'un KW/Layer-G analizini, TV-82
   computation-binding mekanizmasını ve E-gap teşhisini içeren **kısa, kanıt-odaklı** bir
   makale. Şartlara uyar: cryptology, self-contained, proofs. **Eğer kok, C
   seçeneğine evrim geçirirse**, makalenin tezi net olur: **"Dışarıdan Story: receipt
   binding, identity değil computation"** — bir anti-pattern + bir mekanizması + toy
   protokolü. **Bu makale, L1oloşma'nın ötesinde kendi başına değer taşır.**
2. **Zenodo'ya Tam artefakt bankası** (kağıt + spec + 33 prototip + ölçüm json'ları +
   `KOK_V2_REFERENCES.md`) — DOI ile alıntılanabilir. Bu, kodun "var" olduğu dünyaya
   çıkmasının en düşük maliyetli yolu.
3. **Blog-post + repo**: Pearl Analizi (`PEARL_DOCS_ANALIZ.md` + Basu + Ekim 2026 fiyat
   verisi) **kendi başına çok okunabilir bir analiz**. Hoge.gg tarzı yayınlar bu konuda
   okunuyor. **Beklenen kalite: Kok'un kendi disiplini (her iddia bir URL ile) bu formata
   çok uygun.**

### 4.3 Demirel cevapsızlığı üzerine — dürüst değerlendirme

**Durum:** E-posta 2026-09-20 civarı gönderildi (`EPOSTA_DEMIREL_DUZELTME.md`,
`EPOSTA_DEMIREL_TESEKKUR.md`), cevap yok. 18 Ekim 2026 itibarıyla ~4 hafta.

**Bunun ne anlama geldiğini doğru okumak önemli:**

- **Kişisel değil, yapısal.** Demirel'in kendi çalışmasında [2026/1492](https://eprint.iacr.org/2026/1492)'da
  "Deployed evidence comprises one reported audit (Pearl cuPOW)" diyor — yani Demirel'in
  ilgilendiği deployed sistemler. **Kok'in bulunduğu pre-testnet aşaması, onun
  çalışmasının kapsamı dışında.** E-postanın cevaplandırılmamasının%95 ihtimalle
  içerik değil, **önemsizlik** sebebiyle: kok onun için gerçek bir veri noktası değil.
- **Beklemek stratejik bir hata oldu:** `STAGE4_HUMAN_MONEY_GAP.md`'de 2026-09-23'te
  "Priced at $215/hr, declined... the deferral argument now recognised as circular"
  yazılmış. Yani kok kendisi fark etti: **Anonim oldğu için ödeme yapamıyor; ödeme
  yapamadığı için review'ı bekliyor; bekledikçe hiçbir şey üretemiyor.** Bu bir
  çıkmazdır (deadlock).
- **Yapıcı hareket:** Demirel'in makalesini [ePrint 2026/1492](https://eprint.iacr.org/2026/1492)'da
  okuyup **kendi makalemizi yayımlamak** (IACR ePrint' endorsement gerektirmiyor).
  Bu, "bir kâğıda cevap" değil, **konuşmaya katılmaktır**. Kok'un TV-82 mekanizması,
  Demirel'in Corollary 4'üne (burn-priced boost cap) doğrudan bir implementasyon
  örneğidir. **Demirel'in referansına girmenin tek yolu, kendi yayınını yayımlamaktır.**
- **Anonimlik maliyeti:** `KOK_V2_PAPER.md:1335-1338`'de yazdığı gibi "Anonymity is a means,
  not a value". Eğer C seçeneğine evrilirse, anonimliğin anlamı zaten kalmaz (token yok,
  alıcı-satıcı ilişkisi yok). **İsimle yayın, review alma olasılığını artırır.**

**Özet:** arXiv kapalı, IACR ePrint AÇIK, Zenodo AÇIK. Demirel'le temasın yolu **beklemek
değil, yayımlamaktır** — IACR ePrint endorsement istemez.

---

## §5 Öneri

### 5.1 TEK TAVSİYE: **Seçenek C — Kok'u mesh'in compute-proof katmanına evrim geçir; L1'i bırak.**

**Karar:** Kok, bir L1 blokzinciri olmaktan çıkar; **Tamga + x402 standardında
"compute-work proof" receipt sınıfı** haline gelir. GHOSTDAG, tokenomik, emisyon modeli,
SEC/MiCA hukuk bölümü (§9) ve L1'in tümü **kasten terk edilir**.

**Hedef cümlesi (tek satır):**

> Kok, bir compute-provider'ın gerçekten hangi MatMul/işlemi yaptığını **bağımsızca
> doğrulanabilir** bir makbuz olarak üretir; bu makbuz Tamga'nın hash-zincirine ve x402'nin
> proof-of-done extension'ına bağlanır. Madencilik yok, token yok, L1 yok.

### 5.2 Gerekçe — 7 kanıt, sıralı

1. **Kok'un kendi dokümanları L1'i zaten mahkûm etmiş.** Kill kriteri: "F3a sonunda sıfır
   gerçek talep çıkarsa proje dursun" (`KOK_V2_PAPER.md:1913`). F3a **başlamadı**.
   "F3a cannot start without F0 — an economy testnet with no demand measures nothing,
   which is the precise error Pearl's years of running made" (`KOK_V2_PAPER.md:1941-1942`).
   F0 = **0 görüşme**. Yani L1 yolu, kok'un kendi kurallarıyla **zaten kapanmıştır**.

2. **Gerçek differentiating knowledge L1 gerektirmiyor.** §2'deki 5 maddenin en değerli
   ikisi — **E-gap teşhisi** ve **computation-binding (TV-82) mekanizması** — bir
   blockchain olmadan tamamen geçerli. Hatta **daha geçerli**: Demirel [2026/1492](https://eprint.iacr.org/2026/1492)'un
   kendisi receipt'lerin "payment, collateral, loss allocation, and a bounded, priced
   election boost" için uygun, "leader-election floor için DEĞİL" diyor. **Kok'un bilgisi,
   bir L1'de kullanılırsa kendi başına önemsizleşir; bir receipt standardında kullanılırsa
   doğrudan değerli olur.**

3. **Mesh'in içinde gerçek bir tüketici tabanı var — sıfır pazarlama gerekmeden.**
   Tamga'nın receipt formatı **7+ proje tarafından kod-kanıtıla tüketiliyor**
   (`tamga/docs/PROJE-ENTEGRASYON-HARITASI.md §1`: Sester AT-055/056, Veridict, PQHaven
   **AT-065 5/5**, Swarmax AT-067 6/6, Dümen AT-068 6/6, Fleksa AT-070 6/6, Tenderix
   AT-071 6/6, Veridrome AT-072 6/6). Ajan Borsası `receipt_hash: str | None` alanını
   **kod-kanıtı ile** okuyor (`borsa_core.py:70, :176`). **Kok'un 42 hafta boyunca
   aradığı "tek bir müşteri, tek bir iş" — mesh'in içinde zaten yazılmış durumda.**

4. **x402 proof-of-done tam bu boşluğu tanımlıyor.** Issue [#3379](https://github.com/x402-foundation/x402/issues/3379)
   (AÇIK, 58 yorum): "bir script ile bir agent aynı kaydı bırakır" — yani **ödeme kanıtı
   = iş kanıtı değil**. Üç eksen ortaya çıktı: durable-evidence (ne) + **proof-of-done (iş)** +
   capacity-attest (alıcı). Kok, "iş yapıldı" ekseninde **matematiksel olarak en sağlam**
   teklif olabilir (TV-82 computation binding + ctx T-A2). **Henüz REDDEDİLMEDİ — karar
   bekliyor. Bu bir penceredir.**

5. **TRM Labs'in birinci önerisi bu yöndedir.** $52.7M x402 hacminin %0.6–7.5'i gerçek
   ajansal. Önerisi: **"counterparty reputation an agent can check on its own"** — yani
   dışarıdan bağımsızca doğrulanabilen bir kanıt. Kok'un bağımsız verify'ı (`cargo run --
   verify kanit.json`, "no secrets and no network", `README.md:53-56`) tam budur.

6. **Pazar verification'ı bir L1 olarak satın almıyor, bir ÖZELLİK olarak satın alıyor.**
   \- EIGEN −%96, PROVE −%89, ZKC −%97, LA −%96, PHA −%98; ORA cap $412K, günlük $28
   hacim. "opML was never going to be a standalone product so much as one ingredient"
   ([hoge.gg](https://hoge.gg/opml-inference-verifiable-ai-training-2026/)). **Gensyn'in
   Verde'si verification'ı compute ile birlikte satıyor.** Yani doğru konum
   standalone L1 değil, **varolan marketplace/ödeme sistemlerine entegre bir kanıttır.**
   Tamga/Sester tam böyle bir sistem.

7. **97 commit/haftalık kan damarı, portföyün başka yerlerine kitlesin.** Seçenek A'nın
   görünen fırsat maliyeti: 9 ayda 388 commit, **sıfır external artefakt**. Portföyün
   brifingi aynı teşhisi koyuyor ("9 aydır portföyeye ~20 yeni proje eklendi, 139 commit
   atıldı — ve tek bir e-posta gönderilmedi", `PORTFOY-KARAR-BRIFINGI_2026-09-28.md §0`).
   Kok, bu hatayı TEKRARLIYOR. **Ekonomik olarak: 97/hafta'lık bir kaynağın L1 olarak
   kalması, bekleyişin maliyetidir.**

### 5.3 KILL-CONDITION (kesin, tarihli)

**12 hafta (18 Ocak 2027) içinde aşağıdakilerin hepsi sağlanmazsa → kok tamamen öldürülür
(Seçenek D), kod MESH'in başka projelerine parçalanır:**

| # | Koşul | Ölçüm yöntemi | Durum ( 2026-10-18) |
|---|---|---|---|
| K1 | Tamga'ya bir `compute-proof` receipt scheme eklenmiş ve **en az 1 mesh projesinde kod-kanıtı ile** tüketiliyor (Sester, Ajan Borsası, GNoME-Forge veya Dümen) | PROJE-ENTEGRASYON-HARITASI'nda bir satır + AT-testi | ✅ **TAMGA-BAĞLANDI** — RFC-011 `compute-anchor` op'u ( `tamga/tools/compute_anchor.py`), 14 AT-080-testi, tam-suit 3110/3110-rc0. **Ancak henüz başka-bir-mesh-projesinde-tüketilmiyor** — koşulun-ikinci-yarısı açık |
| K2 | Kok'un çekirdek kanıt kodu (KW prove/verify + computation binding) bağımsız bir kütüphane olarak ayrılmış (Rust crate + Python paketi) | `git`'te yeni bir repo/klasör | ✅ `kok/receipt/` — ~400-satır bağımsız-Python-doğrulayıcı ( kok'tan-import-yok); Rust-binary→Python-verify çapraz-dil aynı-receipt |
| K3 | IACR ePrint'e (veya Zenodo'ya) yayınlanmış bir makale/artefakt | URL | ⚠️ **PAKET-HAZIR, GÖNDERİLMEDİ** — `docs/IACR_EPRINT_PAKETI_2026-10-18.md` ( endorsement-yok-çözümü); `github.com/goun7/kok` public-repo pushlandı ( kok'un-ilk-external-artefaktı). **Gönderim-tuşu kullanıcı-sırasında** ( gerçek-yazar-adı-gerekli) |
| K4 | **x402 issue #3379'a** kok'un compute-proof önerisi yazılmış (mevcut discussion'a katkı) | GitHub yorum linki | ✅ [yorum-6251938895](https://github.com/x402-foundation/x402/issues/3379#issuecomment-6251938895) + kamu-test-vektörü ( `docs/TEST-VEKTOR-KOK-COMPUTE-WORK.md`). **Maintainer-yanıtı bekleniyor** |
| K5 | L1 dokümantasyonu (tokenomik, hukuk §9, GHOSTDAG, emisyon) ya arşivlenmiş ya da "historical" olarak işaretlenmiş | dosya durumu | ✅ `docs/historical_l1/` — "mezarlık-değil-mahkeme-kaydı" |

**K-koşul-ölçümü ( 2026-10-18): 5/5-çalışıldı, 3-tam-yeşil ( K1-kısmi, K2, K5), 1-paket-hazır ( K3-gönderim-kullanıcıda), 1-gönderildi-yanıt-bekliyor ( K4).**
K1'in-açık-yarısı ( başka-mesh-projesinde-tüketim) ve K3'ün-gönderim-tuşu
2027-01-18 öncesi kapatılması-gereken-iki-boşluk.

**Ek mutlak kill:** Eğer x402 maintainersu #3379'daki proof-of-done teklifini **REDDEDERLERSE**
veya Tamga compute-proof katmanını kendisi yazarsa → K1 ölür, bu durumda kok'un
C-pozisyonu çöker; D'ye geç.

### 5.4 Ne YAPILMAYACAK (dürüst uyarılar)

- **Yeni L1 dokümanı yazılmaz.** §9 (hukuk, 270 satır), tokenomik modeli, GHOSTDAG
  parametreleri — bunların hiçbirine yeni commit atılmaz. Kağıt 85/100 tavanında, kalan
  15 deneysel ve kağıtta kazanılamaz (`README.md:152-153`).
- **Demirel beklenmez.** 4 hafta sessizlik + onun makalesinin "deployed evidence" kapsamı
  = bekleme bir strateji değildir. Yayın yapılır (IACR ePrint endorsement istemez).
- **F3a için "bir alıcı bulunmaz."** Seçenek C'de alıcı zaten bellidir: mesh'in içindeki
  7+ entegre proje. **Dışarıdaki Astria e-postası** (`F3A_INVITATION_STRATEGY.md`)
  archive'lenir — tek başına bir support-inbox'a bağımlılık, ölçülebilir bir strateji
  değildir.
- **Test suite'leri çalıştırılmaz / değiştirilmez.** Bu rapor araştırmadır;
  çekirdek kod pointer'ları README ile sabitlenmiştir.

### 5.5 Son bir dürüst değerlendirme — sicimde

Kok'un en derin başarısı, **kendi hatasını bulma disiplinidir**: θ=1.05→1.657, "logaritmik
cost"→linear, ZK maskeleyme→gizlemiyor, commitment-string→computation-binding,
kendi-view-self-interview sayımı→0. **Bu disiplin, L1 vizyonunun ölümünü de kabul
etmelidir.** En sağlam on iki ay, en pahalı proje, en yüksek test sayısı — ve **hiç kimse
hiçbir şeyi okumadı**. Raporun en acı cümlesi kok'un kendisinde yazıyor:

> **"The project's survival does not depend on the cryptography (as sound as a paper can
> make it) or the law (now navigable). It depends on one customer with one job."**
> (`KOK_V2_PAPER.md:1920-1924`)

Müşteri mesh'in içinde. İş tanımlandı: **ödemenin kanıtlandığı yere, işin de kanıtlandığı
bir makbuz.** L1'i bırakmak, kok'u küçültmez — onu 42 hafta sonra ilk kez **gerçek bir
probleme** oturtur.

---

## Kaynak özeti (dış)

- Pearl: [onebullex mainnet](https://www.onebullex.com/news/articles/pearl-research-labs-launches-proof-of-useful-work-mainnet-on-april-27-2026), [arXiv 2606.04819 (Basu)](https://arxiv.org/abs/2606.04819), [hashrateindex](https://hashrateindex.com/blog/pearl-prl-ai-compute-cryptocurrency/), [coinstats](https://coinstats.app/ai/a/latest-news-for-pearl-2), [kucoin](https://www.kucoin.com/news/insight/PRL/6a1837a357e8dc00078b3caf), [together.ai](https://www.together.ai/blog/together-ai-partners-with-pearl-research-labs), [coingecko](https://www.coingecko.com/en/coins/pearl-research)
- Teori: [ePrint 2026/1492 (Demirel)](https://eprint.iacr.org/2026/1492), [arXiv 2504.09971 (KW)](https://arxiv.org/abs/2504.09971), [Dagstuhl ESA 2026](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESA.2026.2)
- Pazar: [hoge.gg opML](https://hoge.gg/opml-inference-verifiable-ai-training-2026/), [hoge.gg verifiable compute trilemma](https://hoge.gg/verifiable-compute-trilemma-proving-ai-2026/), [Akash Q1 2026](https://akash.network/blog/akash-network-q1-2026-report/), [hoge.gg Akash](https://hoge.gg/akash-network-2026-gpu-market-leaves-cosmos/), [TRM Labs](https://www.trmlabs.com/trm-tech-blog/whos-actually-paying-measuring-ai-agent-payments-onchain), [DCS Compute](https://compute.trdn.io/), [Gensyn](https://www.gensyn.ai/)
- Yayın: [arXiv endorsement policy](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/), [arXiv help](https://info.arxiv.org/help/endorsement.html), [IACR ePrint operations](https://eprint.iacr.org/operations.html), [Zenodo policies](https://about.zenodo.org/policies/), [SSRN guide](https://casrai.org/guides/ssrn-how-it-works-for-researchers), [CCSD HAL](https://www.ccsd.cnrs.fr/en/2026/03/do-arxiv-s-rule-changes-have-an-impact-on-hal/), [OSF](https://www.cos.io/products/osf-preprints)
- Tamga/Sester: [x402 #3379](https://github.com/x402-foundation/x402/issues/3379), [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004), [arXiv 2606.26028 (ERC-8004 empirical study)](https://arxiv.org/abs/2606.26028)
