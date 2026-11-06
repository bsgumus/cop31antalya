# cop31antalya.org — Yayına Alma Rehberi

Canlı elektrik sayacı: COP31 boyunca rüzgâr ve güneşten üretim, yakılan kömür, CO₂,
ithal kömür faturası ve gazın TTF fiyatıyla bedeli. Üretim TEİAŞ YTBS'nin 15 dakikalık
verisi (lisanssız dahil); TTF ICE Endex'ten, kur ECB'den, emisyon faktörleri ETKB'den.

Mimari (tamamı ücretsiz, sunucu yok):

```
Bu Mac (Türkiye) ── launchd, 15 dakikada bir ──▶ veri/yayinla.sh
   veri/guncelle.py: TEİAŞ YTBS, ICE Endex (TTF), ECB (EUR/USD)
   → data/gun/*.json + data/fiyat.json + data/ozet.json → git push
        │
        └──▶ GitHub (bsgumus/cop31antalya) ── Actions, her gönderimde ──▶ GitHub Pages ──HTTPS──▶ ziyaretçi
```

**TEİAŞ YTBS yalnız Türkiye'den erişilebiliyor.** 6 Kasım 2026 testi: 40 ülke düğümünden
yalnız İstanbul'dakiler bağlandı; GitHub'ın sunucuları da zaman aşımına uğruyor. Bu yüzden veri
Türkiye'deki bir bilgisayarda çekilir, GitHub yalnız yayınlar. Ziyaretçi kaynaklara hiç
bağlanmaz; herkes aynı statik JSON'u okur.

---

## 1) Depolar (kuruldu)

- `bsgumus/cop31antalya`: site, veri ve yayın iş akışı (`.github/workflows/veri.yml`, her
  gönderimde Pages'e yayınlar). Geçici adres: https://bsgumus.github.io/cop31antalya/
- `bsgumus/cop31antalya-com`: cop31antalya.com'u aynı sayfa ve parametrelerle .org'a yönlendiren
  küçük sayfa (`../cop31antalya-com` klasörü; GitHub Pages, `main` dalı, CNAME dosyası GitHub'ın).
- Bu Mac'te GitHub CLI `~/.local/bin/gh` (bsgumus hesabıyla giriş yapıldı); git gönderimleri
  bunun üzerinden kimlik doğrular.

Sayfada değişiklik yaptıktan sonra yayına göndermek için:

```bash
cd ~/fabledeneme/cop31antalya && git add -A && git commit -m "Sayfa güncellemesi" && git push
```

## 2) Veri güncelleyici (bu Mac)

> **Şu an veriyi telefon gönderiyor** (6 Kasım 10:02'den beri). Mac'teki launchd görevi kaldırıldı;
> gerekirse aşağıdaki kurulum komutuyla geri gelir.

`veri/yayinla.sh` veriyi çekip değişiklik varsa GitHub'a gönderir. launchd her saatin 07, 22,
37 ve 52. dakikasında çalıştırır (`veri/com.cop31antalya.veri.plist`). Kurulum:

```bash
cp ~/fabledeneme/cop31antalya/veri/com.cop31antalya.veri.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cop31antalya.veri.plist
```

- Günlük: `~/Library/Logs/cop31antalya-veri.log`
- Elle bir kez çalıştırmak: `bash ~/fabledeneme/cop31antalya/veri/yayinla.sh`
- Durdurmak:

```bash
launchctl bootout gui/$(id -u)/com.cop31antalya.veri
```

**Mac uyanık ve internete bağlı olmalı.** Uyurken çalışma kaçar, uyanınca bir kez yapılır.
COP boyunca: Sistem Ayarları → Pil → Seçenekler → "Güç adaptörüne bağlıyken ekran kapalıyken
otomatik uyumayı önle" açık, kapak açık ve adaptöre takılı. Veri 3,5 saatten eskiyse sayfa
"Veri gecikmeli" der; sayaçlar en fazla 3 saat ileri gider. Her an açık bir makine için
Türkiye'de küçük bir sunucu ya da evde sürekli açık bir bilgisayar aynı iki dosyayla çalışır.

## 2b) Telefon (Android, Termux): Mac kapalıyken

Aynı iş telefonda `veri/telefon.sh` ile yapılır: her 07, 22, 37 ve 52. dakikada depodaki son hali
alır, veriyi çeker, gönderir. Telefon Türkiye'de ve internette olmalı (günde yaklaşık 50 MB).

1. **Termux'u kurun:** F-Droid'den (https://f-droid.org/packages/com.termux/) ya da
   https://github.com/termux/termux-app/releases adresinden. Play Store sürümü önerilmez.
2. **Termux'u açıp şunu yapıştırın** (paketler, GitHub girişi, depo; birkaç dakika sürer):

```bash
curl -fsSLo kur.sh https://raw.githubusercontent.com/bsgumus/cop31antalya/main/veri/termux_kur.sh && bash kur.sh
```

   GitHub girişinde ekranda bir kod çıkar: https://github.com/login/device adresinde girip onaylayın.
3. **Başlatın** (Termux açık kalsın; bildirimde "1 session" görünür, ekran kapanabilir):

```bash
bash ~/cop31antalya/veri/telefon.sh
```

4. **Android ayarı:** Ayarlar → Uygulamalar → Termux → Pil kullanımı → **Kısıtlamasız**.
   Telefon mümkünse şarjda kalsın. Termux kapatılır ya da telefon yeniden başlarsa 3. adımı
   tekrarlayın.

Telefon çalışırken Mac'teki görevi kapatmak yeterli (ikisi aynı anda gönderirse kaybeden
bir sonraki turu bekler, veri bozulmaz):

```bash
launchctl bootout gui/$(id -u)/com.cop31antalya.veri
```

Mac'e geri dönmek için 2. bölümdeki kurulum komutu yeniden çalıştırılır.

## 3) Alan adları

**Ana adres cop31antalya.org** (6 Kasım'da .com'dan değiştirildi: .org'un sertifikası dakikalar
içinde geldi, .com'unki saatlerce "authorization_pending"de kaldı).

| Alan adı | Kayıt firması / DNS | Ne yapıyor |
|----------|---------------------|------------|
| cop31antalya.org | Porkbun | **Site.** Depo `bsgumus/cop31antalya`, HTTPS zorunlu, sertifika GitHub'ın (Let's Encrypt, kendiliğinden yenilenir) |
| cop31antalya.com | SH Online ("Sadece Hosting") | .org'a yönlenir. Depo `bsgumus/cop31antalya-com` |
| cop31antalya.tr | SH Online | Ertelendi (aşağıda) |

### cop31antalya.org (Porkbun DNS)

| Tip   | Host | Cevap              |
|-------|------|--------------------|
| ALIAS | @    | bsgumus.github.io  |
| CNAME | www  | bsgumus.github.io  |

Dokunmayın: Google doğrulama TXT'si ve iki `_acme-challenge` TXT'si. Porkbun'un eski URL
yönlendirmesi (`*` CNAME → `uixie.porkbun.com` ve URL Forwarding'deki kayıt) yalnız diğer alt
alan adlarını etkiler; istenirse Porkbun panelinden silinebilir (silerken tarayıcı onay sorar).
GitHub tarafı:

```bash
~/.local/bin/gh api -X PUT repos/bsgumus/cop31antalya/pages -f cname=cop31antalya.org
```

### cop31antalya.com (SH DNS)

A @ → 185.199.108.153, .109, .110, .111 ve CNAME www → bsgumus.github.io (MX ve TXT olduğu gibi).
`cop31antalya-com` deposu her yolu `https://cop31antalya.org` + aynı yol ve parametrelere
yönlendirir. HTTP ile çalışıyor; HTTPS sertifikası 6 Kasım gecesi hâlâ bekliyordu. Gelince:

```bash
~/.local/bin/gh api -X PUT repos/bsgumus/cop31antalya-com/pages -F https_enforced=true
```

Durum: `~/.local/bin/gh api repos/bsgumus/cop31antalya-com/pages --jq .https_certificate.state`
(`approved` olunca açılabilir). Uzun süre beklerse alan adını kaldırıp yeniden eklemek
(`-f cname=` boş, sonra yeniden `cop31antalya.com`) isteği baştan başlatır.

### cop31antalya.tr (ertelendi)

SH paneli bu alan adı için DNS yönetimi sunmuyor (yalnız .com'da var). Seçenekler: SH'ye destek
talebi (kayıtları onlar girer ya da DNS yönetimini açarlar) veya isim sunucularını başka bir DNS'e
taşımak. Yapılınca `cop31antalya-com` deposunun kopyası `cop31antalya-tr` adıyla açılıp
`cname=cop31antalya.tr` verilir.

## 4) Kontrol

- `https://cop31antalya.org/`: ana sayfa (Türkçe ya da tarayıcı diline göre İngilizce)
- `https://cop31antalya.org/?lang=en`: İngilizce
- `https://cop31antalya.org/?mod=ekran`: stant ve salon ekranları için tam ekran, koyu
  (`&tema=acik` ile açık tema)
- `https://cop31antalya.org/?mod=widget`: haber sitelerine gömülecek küçük sürüm.
  Gömme kodu sayfanın "Paylaş ve kullan" bölümünde.
- `http://`, `www.` ve `cop31antalya.com/...` aynı sayfaya yönlenir.

---

## Değiştirilebilecek ayarlar

- `veri/guncelle.py`
  - `COP_BAS`, `COP_BIT`: sayacın COP dönemi. Müzakereler 20 Kasım'dan sonraya uzarsa
    `COP_BIT`'i ileri alın.
  - `GERI_DOLDUR`: bu günden bugüne eksik günler çekilir.
  - Kömür katsayıları ve ithal kömür fiyatı (Prizdeki Kömür yöntemi, TEİAŞ 2025).
  - Doğalgaz: `GAZ_M3_MWH` (TEİAŞ 2025 gaz tüketimi ÷ gaz üretimi, ~216 m³/MWh) ve
    `GAZ_KWH_M3` (BOTAŞ üst ısıl değeri). TTF fiyatı ve kur elle girilmez: her çalışmada
    ICE Endex'in Dutch TTF ön ay vadeli fiyatı ile ECB EUR/USD referans kuru
    `data/fiyat.json`'a gün gün eklenir; her gün o günün fiyatıyla değerlenir. Hafta
    sonları ve tatillerde önceki iş gününün değeri kullanılır.
  - `CO2_T_MWH`: ETKB'nin 2023 yakıta göre elektrik üretim emisyon faktörleri
    (tCO₂/MWh). ETKB 2024 faktörlerini yayımlarsa burada değiştirin.
  - `KAPASITE`: rüzgâr ve güneş kurulu gücü (ETKB'nin aylık açıklaması, şu an Haziran 2026 sonu)
    ve 2035 hedefi; "Türkiye'nin 2035 hedefi" kartı bunu kullanır.
- `index.html`
  - `KURUM`: altbilgide "Hazırlayan: ..." satırı. Boşsa görünmez.
  - Gündelik karşılıklar: `KAMYON_TON` (25), `KISI_KWH` (kişi başı yıllık net elektrik,
    TEİAŞ 2022: 3.360 kWh), `KISI_CO2_TON` (kişi başı sera gazı, TÜİK 2024: 6,8 ton).
  - `temalar`: COP31'in gün gün tematik başlıkları (metin sözlüğünde, TR ve EN).
  - `EMISYON`: "Türkiye'nin emisyon hedefleri" grafiğinin verisi, milyon ton CO₂e: TÜİK net
    emisyonu (arazi kullanımı ve ormancılık dahil), 2012 bazlı eski ve 2018 bazlı yeni referans
    senaryo, INDC, birinci NDC ve NDC 3.0 hedefleri. TÜİK yeni yılı yayımlayınca `gercek`
    dizisine ekleyin; manşet ve not kendiliğinden güncellenir.

## İşletme notları

- **Gecikme:** TEİAŞ bir aralığı bittikten 15–30 dakika sonra yayımlıyor, ilk değeri
  eksik verip sonraki saatte tamamlıyor. 4 Kasım ölçümü: ilk değer %22–26 düşük,
  45 dakikada ~%5, 60 dakikada ~%1,6, 75 dakikadan sonra ~%1 düşük; düzeltmeler bütün
  kaynaklara yayılıyor. Bu yüzden `guncelle.py` 75 dakikadan yeni aralıkları özete
  almaz (`KESINLESME`); son veri sayfada genelde 75–95 dakika geriden gelir. Sayaçlar arada son kesin
  15 dakikanın hızıyla ilerler, en fazla 3 saat ileri gider. Saatlerce süren küçük
  düzeltmeler için dünün verisi bugün boyunca her çalışmada yeniden çekilir.
- **TEİAŞ'a ulaşılamazsa:** hata günlüğe yazılır (`~/Library/Logs/cop31antalya-veri.log`).
  Site son veriyle yayında kalır; son veri 3,5 saatten eskiyse sayfada
  "Veri gecikmeli" yazar.
- **ICE ya da ECB'ye ulaşılamazsa:** çalışma düşmez,
  son bilinen fiyat ya da kur kullanılır (uyarı günlüğe yazılır). ICE'nin kullandığımız adresi
  (`marketdata/api/productguide/charting/...`) web sitesinin kendi grafik ucu;
  resmî bir API değil, değişirse gaz bedeli son fiyatla donar.
- **ICE verisi açık lisanslı değil:** ice.com'daki gecikmeli fiyat herkese açık ama
  ICE'nin site kullanım şartlarına tabi. Sitede ham fiyat akışı değil, ondan
  türetilmiş bir tahmin ve kaynak gösteriliyor.
- **Veri geçmişi:** her çalışma `data/` klasörünü depoya kaydeder; commit geçmişi
  aynı zamanda verinin kaydıdır.
- **COP bittikten sonra:** sayaç `COP_BIT` anında durur ve "COP31 boyunca" toplamlarını
  gösterir. Güncelleyiciyi `launchctl bootout gui/$(id -u)/com.cop31antalya.veri` ile
  durdurabilirsiniz; site son haliyle yayında kalır.

## Geçmiş veri arşivi (sitede kullanılmıyor)

`data/gecmis.json`, 1 Ocak 2016 – 31 Ekim 2026 arasındaki 3.957 günün özetini tutar
(~1,8 MB): grup başına MWh, CO₂ ve günün uç değerleri. Sayfadaki "Geçen yıl ve rekorlar"
bölümü kaldırıldığı için site ve iş akışı bu dosyayı kullanmıyor; yüklemeseniz de olur.
İleride rekorlar ya da geçen yılla karşılaştırma geri gelirse diye saklanıyor.

- TEİAŞ YTBS 2016–2023'ü saatlik (`dk: 60`), 2024'ten beri 15 dakikalık (`dk: 15`) veriyor;
  günlük toplamlar aralığın süresiyle hesaplanır.
- Sağlama: yıllık toplamlar 270 TWh (2016) ile 355 TWh (2025) arasında; 2023'ün ortalama
  yoğunluğu 427 g CO₂/kWh, ETKB'nin 2023 ülke ortalaması 430.

Baştan üretmek ya da eksik günleri tamamlamak için (yarım günü bulur, kesilirse kaldığı
yerden devam eder):

```bash
python3 veri/gecmis_doldur.py
```

## Sayfadaki bölümler

- **Manşet cümlesi** ve beş sayaç; her sayaçta gündelik karşılık ve ⓘ açıklaması.
- **Güneş ve rüzgârın günü**: tüketim çizgisi ile rüzgâr ve güneşin karşıladığı kısım.
- **Son veri** ve **son 24 saat** grafiği; **Türkiye'nin emisyon hedefleri** (gerçekleşen net
  emisyon, referans senaryolar, INDC/NDC hedefleri; PNG ve tablo); **Türkiye'nin 2035 hedefi** (120 GW).
- **Gün gün** tablo; her tarih o günün kalıcı bağlantısı (`?gun=2026-11-12`); günlük ve
  15 dakikalık **CSV**, grafiklerin **PNG** indirmesi.
- **COP başladığından bu yana** kutusu (tablonun altında): COP günlerinin kesinleşmiş toplamı.
  9 Kasım'a kadar boş bekler, ilk kesinleşmiş veriyle kendiliğinden dolar; COP bitince
  başlığı "COP31 boyunca" olur.
- **Paylaş ve kullan**: X, Bluesky, LinkedIn, WhatsApp; günün kartı yatay, kare ve dikey;
  gömme kodu (yükseklik 520) ve ekran modu.
- **Sözlük**; **sık sorulan sorular** ve **veri ve yöntem** kapalı açılır bölümler (sayfa içi
  menüdeki SSS bağlantısı bölümü açar).
- Bağlantı önizlemesi `og.png` (1200×630, `veri/og_gorsel.py` ile yeniden üretilir).

## Yerel deneme

```bash
python3 veri/guncelle.py
```
```bash
python3 -m http.server 8925
```
Sonra http://localhost:8925 adresini açın.

## data/ozet.json alanları

| Alan | İçerik |
|------|--------|
| `simdi` | son 15 dk aralığı: kaynak grubu başına MW, yük, saatlik CO₂ (ton) |
| `hiz` | son aralığın saatlik hızı (MWh, ton kömür, ton CO₂, $), sayaçları ilerletmek için |
| `bugun`, `copDonemi` | dönem toplamları (`copDonemi` COP sırasında sayaçların ve "COP başladığından bu yana" kutusunun kaynağı): MWh, yakılan kömür, CO₂ (toplam ve kömürden), ithal kömür tonu ve faturası, yakılan gaz (m³) ve TTF ile bedeli |
| `gunler` | gün gün aynı toplamlar ve o günün TTF fiyatı (`aralik` < 96 ise gün sürüyor) |
| `seri` | son 96 aralık (24 saat), kaynak grubu başına MW |
| `katsayi` | kömür t/MWh katsayıları, ithal kömür $/ton, gaz m³/MWh, yakıta göre tCO₂/MWh |
| `fiyat` | son TTF fiyatı, vadesi ve tarihi, son EUR/USD kuru, bugün MWh başına gaz bedeli |
| `kapasite` | rüzgâr ve güneş kurulu gücü, tarihi ve 2035 hedefi |

`data/fiyat.json` gün gün TTF (€/MWh) ve EUR/USD kayıtlarını tutar; elle düzeltmek
gerekirse buradaki değeri değiştirip iş akışını yeniden çalıştırmak yeter.
