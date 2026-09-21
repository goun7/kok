# KIMLER KULLANACAK? — Gercek Alici Profilleri (web fetch ile dogrulandi, 2026-09-21)

**Yontem:** `mcp__weblocal__web_fetch` ile canli sayfalardan alindi.
**Kural:** dogrulanamayanlar BULUNAMADI. Hicbir musteri profili uydurulmadi.

---

## DOGRULANAN ALICI SEGMENTLERI (web fetch, 2026-09-21)

### 1. Gizlilik-hassas AI isleri — EN SOMUT ALICI (Akash Confidential Compute)

**Kaynak:** `akash.network/blog/confidential-compute-comes-to-akash/` (28 Jul 2026, Greg Osuri, CANLI FETCH)
**Guven: YUKSEK** (resmi urun duyurusu, kod ornegi ile)

Akash'in kendi sozleriyle, hangi islerin "provider reputation"a guvenmedigi yer:

> "what prevents a completely unknown provider from accessing your data when
> you rent their GPU? ... this baseline falls short when protecting
> **sensitive medical records, proprietary algorithmic trading models, or
> core company intellectual property embedded in model weights**."

*** KOK ICIN ANLAMI: *** Akash TEE ile bu sorunu COZUYOR (hardware-enforced).
KOK ise cozumu PROOF ile sunar (TV-38: dogrulayici sertifikayi hesaplamaya baglar).
**AMA DURUST OL:** Akash'in cozumu BUGUN uretimde (TEK SATIR SDL ile: `params.tee: cpu-gpu`).
KOK'ununki F0b'den SONRA var olur. Yani bu segment VAR, gercek, para odemeye hazir —
ama KOK rakibi TEE'nin iki yil onunde.

**Somut alici tipleri (Akash'in kendi listesinden):**
- **Saglik/arastirma**: tibbi kayitlar uzerinde calisan modeller (HIPAA kapsami)
- **Finans**: proprietary algorithmic trading modelleri (IP = model agirlari)
- **Kurumsal**: model agirliklarina gomulu sirket IP'si

### 2. AI inference aliclari — PAZAR GERCEK VE BYUK (AkashML olcumu)

**Kaynak:** `akash.network/blog/akash-network-q1-2026-report/` (1 Apr 2026, CANLI FETCH)
**Guven: YUKSEK** (resmi ceyrek raporu)

- **AkashML: gunde 1.7 MILYAR token** (OpenRouter uzerinden)
- **Akash Q1 2026: $5 milyon ALL-TIME compute spend** (toplam, ceyrek degil)
- **AkashML %70-85 maliyet tasarrufu** iddia ediyor (Llama 3.3-70B, DeepSeek V3, Qwen3-30B)
- **2025 boyunca %60 utilization** (accelerated compute)

*** KOK ICIN ANLAMI: *** Yeterli talep var ve rakip KAZANIYOR. AkashML "managed AI
inference" ile uyumluluk sorununu cozdu; KOK'un U katmani ayni seyi yapmalidir.
**1.7B token/gun = ~$2,000-$5,000/gun gelir** (DeepSeek $1.32/Mtoken ile) —
KOK'un F0 hedefi "1 musteri" olduguna gore, bu pazarin %0.01'i bile F0'yi GECER.

### 3. Jeopolitik dayaniklilik isteyenler (Homenode argumani)

**Kaynak:** ayni Q1 2026 raporu (CANLI FETCH)

> "what happens when a data center gets hit... recent attacks on data centers in
> the Arabian Gulf made that concrete... If a data center in the Middle East takes
> a strike, nodes in Seoul and Frankfurt keep running."

*** KOK ICIN ANLAMI: *** Bu KOK'un GHOSTDAG + 10 BPS hikayesinin gercek bir talep
karsiligidir: **dagitiklik = fiziksel saldiri direnci.** AMA DURUST: Akash bunu
"feature" olarak SATIYOR (Homenode Beta), KOK ise sadece teorik olarak saglar.
KOK'un avantaj iddia edemez; avantaj ancak olculunce (F3b) iddia edilebilir.

### 4. ZK proof aliclari — TALEP GERCEK, REKABET COK SERT

**Kaynak:** `axiom.xyz/` (CANLI FETCH, 2026)
**Guven: YUKSEK** (resmi site)

- **OpenVM 2.1 Preview: Ethereum'u 4 GPU'da GERCEK ZAMANLI kanitliyor** (29 Jul 2026)
- **OpenVM 2.0: 1 GHz proving throughput, 64 GPU** (10 Jul 2026)
- **Ethereum mainnet bloklari < 10 saniyede** kanitlaniyor (EthProofs)
- **100 bit provable post-quantum security**, formally verified (Lean), audited

**Kaynak:** `nil.foundation/` (CANLI FETCH)
- =nil; Ethereum L2, zkSharding, "300+ developers onboarded", MAINNET 2025

*** KOK ICIN KRITIK GERCEK: *** Axiom'in proof altyapisi O ZAMAN HIZLI ki
"proof market" KOK'un cross-subsidy avantajini YOK sayar: 4 GPU ile real-time
proving varken, "madencilikle ayni FLOP'lar" avantaji kalmaz.
**Bu, arastirma subagent'inin "Axiom revenue yayinlamiyor" bulgusunu ONYARGILI
yapmis olabilir: Axiom para kazanmiyor olabilir ama HIZ kazanmis.**
*** SONUC: KOK'un ZK-coprocessing genislemesi zayifliyor — rakip "ucuz" degil
"HIZLI" rekabet ediyor. ***

### 5. AI agent gelistiricileri (Akash'in "agent meta" gozlemi)

**Kaynak:** Akash Q1 2026 raporu (CANLI FETCH): "the agent meta arrived on decentralized compute"
**Guven: ORTA** (govde gozlemi, revenue rakami yok)

*** KOK ICIN ANLAMI: *** Bu, KOK'un "AI agent settlement layer" genişlemesinin
ilk dogrulanmis talep isaretidir — ama henuz PARA degil, "meta".
Paper §11b'de "ERTELENDI - umut uzerine insa edilmez" yazdik; bu veri onu
"IZLEMEYE DEGER" olarak gunceller, ama "YAP" olarak degil.

---

## BULUNAMADI (web fetch ile erisilemeyen)

| Hedef | Sonuc | Neden |
|---|---|---|
| Aethir musteri listesi (aethir.com/customers) | **BULUNAMADI** | 404 — boyle bir sayfa yok |
| Render Network Wikipedia | **BULUNAMADI** | Wikipedia'da boyle sayfa yok |
| Cudos (cudos.org) | **BULUNAMADI** | HTTP 429 rate-limited |
| io.net (io.net) | **BULUNAMADI** | JS-arka sayfa, icerik gelmedi |
| "AI's Infrastructure Problem" makalesi | **BULUNAMADI** | blog listesinde baslik var ama URL 404 |

---

## NET SONUC: KIM KULLANACAK? (dürüst, 3 katmanli)

### Katman A — BUGUN ODEMEYE HAZIR OLANLAR (Akash'in kanitladigi)
**Saglik, finans, kurumsal IP** sahipleri: gizlilik-hassas AI inference istiyorlar.
Akash bunlara TEE satisi YAPIYOR. KOK onlara proof sunabilir — **AMA F0b'den sonra.**
*** Bu, F0b'nin (gercek AIR) neden en yuksek oncelikli teknik is oldugunun PIYASA
KANITIDIR: alici VAR, ihtiyac VAR, para VAR; eksik olan KOK'un urunu. ***

### Katman B — TALEP VAR, REKABET ZOR
AI inference genel pazar: 1.7B token/gun olculuyor. Ama AkashML %70-85 ile kazaniyor,
ve KOK'un cross-subsidy crossover'i ($2.64) ancak token ucuzken calisir.
*** Bu katmanda KOK "biraz daha ucuz" olabilir ama fark buyuk degil —
Akash'in 2 yillik oncu avantaji ve managed urunu var. ***

### Katman C — KOK'UN GERCEK FARKI OLABILIR (ama ispatlanmadi)
**Proof-based provenance**: TEE degil, matematik. TEE'ye guvenmek istemeyenler
icin (donanim ureticisinden bagimsizlik — Intel TDX vs AMD SEV-SNP secimi
Akash'in sozunde "hardware dictates").
*** DURUST SINIR: bu iddia F0b'ye kadar KANITLANAMAZ. Akash'in TEE'si BUGUN calisiyor. ***

---

## STRATEJIK GUNCELLEME (paper §11b'ye islenecek)

1. **F0b'nin onceligi PIYASA ile dogrulandi**: gizlilik-hassas alicilar VAR
   (saglik/finans/IP), Akash onlara TEE satiyor, KOK proof sunabilir.
   Bu, "kim kullanacak" sorusunun ilk GERCEK cevabidir.

2. **ZK-coprocessing genislemesi ZAYIFLIYOR**: Axiom 4 GPU ile real-time Ethereum
   proving yapiyor. KOK'un "ayni FLOP'lar" avantaji hiz karsisinda anlamini yitirir.
   Paper'daki "Secondary" derecesini "WEAK" olarak guncellemeliyim.

3. **Jeopolitik dayaniklilik TALEP olarak dogrulandi** ama Akash bunu SATIYOR
   (Homenode). KOK avantaj iddia edemez — sadece olcebilir (F3b).

4. **Agent meta**: ilk talep isareti; "ERTELENDI" -> "IZLE" olarak guncellenmeli,
   "YAP" degil.

*** EN ONEMELI: "kim kullanacak" sorusunun cevabi ARTIK "saglik/finans/IP
sahipleri, gizlilik-hassas AI inference icin" — cunku bu tek segment hem
VAR (Akash satiyor) hem KOK'un proof yaklasimina ihtiyac duyuyor (TEE'ye
alternatif). F0b bu segmentin kilididir. ***
