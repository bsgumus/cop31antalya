#!/usr/bin/env python3
"""COP31 sayacının verisini çeker ve data/ altına yazar.

Yalnız standart kütüphaneyi kullanır. GitHub Actions'ta 15 dakikada bir çalışır;
yerelde `python3 veri/guncelle.py` ile de çalışır.

Kaynaklar:
- TEİAŞ YTBS (https://ytbsbilgi.teias.gov.tr/ytbsbilgi/frm_istatistikler.jsf): sayfa, bugünün
  15 dakikalık üretimini (kaynak bazında, lisanssız dahil) ve yük eğrisini <script> içine gömülü
  getirir. Geçmiş bir gün için tarih alanıyla tek bir form POST'u yeterli; Selenium gerekmez.
- ICE Endex, Dutch TTF Natural Gas Futures: ice.com'daki gecikmeli ön ay fiyatı.
- ECB EUR/USD referans kurları.

Çıktılar:
  data/gun/YYYY-MM-DD.json  günün ham 15 dk verisi (TEİAŞ alan adlarıyla, MW)
  data/fiyat.json           gün gün TTF ön ay fiyatı (€/MWh) ve EUR/USD
  data/ozet.json            sayfanın okuduğu özet: şimdi, bugün, COP dönemi, gün gün, son 24 saat
"""
import http.cookiejar
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import namedtuple
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

URL = "https://ytbsbilgi.teias.gov.tr/ytbsbilgi/frm_istatistikler.jsf"
ICE_SOZLESMELER = "https://www.ice.com/marketdata/api/productguide/charting/contract-data?productId=4331&hubId=7979"
ICE_GECMIS = "https://www.ice.com/marketdata/api/productguide/charting/data/historical?marketId={}&historicalSpan=1"
ECB_KURLAR = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
UA = "Mozilla/5.0 (compatible; cop31antalya-sayac/1.0; +https://cop31antalya.org)"
TSI = timezone(timedelta(hours=3))  # Türkiye Eylül 2016'dan beri sabit UTC+3
KOK = Path(__file__).resolve().parent.parent
GUN_DIZINI = KOK / "data" / "gun"
FIYAT = KOK / "data" / "fiyat.json"
OZET = KOK / "data" / "ozet.json"

COP_BAS = datetime(2026, 11, 9, tzinfo=TSI)
COP_BIT = datetime(2026, 11, 21, tzinfo=TSI)  # 20 Kasım'ın sonu; müzakereler uzarsa ileri al
GERI_DOLDUR = date(2026, 11, 1)  # bu günden itibaren eksik günler çekilir
# TEİAŞ yeni aralığı eksik yayımlayıp sonraki saatte tamamlıyor; düzeltmeler bütün kaynaklara yayılıyor.
# 4 Kasım ölçümü: ilk değer %22-26 düşük, 30 dk sonra ~%7, 45 dk ~%5, 60 dk ~%1,6, 75-120 dk ~%1 düşük;
# 3-4 saatlik aralıklar %0,3'ün altında oynuyor. Bundan yeni aralıklar özete girmez.
KESINLESME = timedelta(minutes=75)

# Kömür katsayıları, Prizdeki Kömür yöntemi (TEİAŞ 2025): yakıt tablosundaki tonaj ÷ Rapor212 üretimi.
# Taş kömürü, ithal kömür ve asfaltit yakıt tablosunda tek kalem; üçü MWh başına aynı miktarı yakıyor sayılır.
LINYIT_T_MWH = 62_470_509.08168 / 38_430_654.092
BIRLESIK_T_MWH = 30_118_611.071 / (76_591_655.496 + 4_091_013.154 + 1_742_454.240)
ITHAL_USD_T = 94  # ithal kömür, 2025 ortalaması

# Doğalgaz: aynı TEİAŞ yakıt tablosundaki gaz tüketimi (1000 m³, kojenerasyon ısısı dahil) ÷ Rapor212 gaz üretimi.
GAZ_M3_MWH = 17_107_093_048.713673 / 79_166_771.183
GAZ_KWH_M3 = 9155 * 4.1868 / 3600  # BOTAŞ'ın üst ısıl değeri (9.155 kcal/Sm³); TTF de üst ısıl değer bazlı

# ETKB, "Türkiye Elektrik Üretimi ve Elektrik Tüketim Noktası Emisyon Faktörleri" (hesaplama dönemi 2023,
# yayım 26.12.2025): yakıta göre elektrik üretim emisyon faktörleri, tCO2/MWh. Hidro, rüzgâr, güneş, jeotermal,
# biyokütle, nükleer ve atık ısı ETKB'deki gibi sıfır. Nafta ve LPG ETKB'de yok (üretimleri sıfıra yakın): motorin.
CO2_T_MWH = {
    "linyit": 1.122, "taskomur": 1.045, "asfaltitkomur": 1.078, "ithalkomur": 0.800,
    "dogalgaz": 0.400, "lng": 0.400, "fueloil": 1.240, "motorin": 0.862, "nafta": 0.862, "lpg": 0.862,
}
KOMUR_ALANLARI = {"linyit", "taskomur", "asfaltitkomur", "ithalkomur"}

# Rüzgâr ve güneş kurulu gücü, ETKB'nin aylık açıklaması (Haziran 2026 sonu). Yenisi çıkınca güncelleyin.
# 2035 hedefi: rüzgâr + güneş 120 GW (ETKB, Ekim 2024).
KAPASITE = {"gunesMw": 27_210, "ruzgarMw": 15_281, "tarih": "2026-06-30", "hedefMw": 120_000, "hedefYil": 2035}

# Sayfadaki gruplar ve karşılık gelen YTBS alanları. Listede olmayan yeni bir alan "diger"e gider.
GRUPLAR = {
    "gunes": ["gunes"],
    "ruzgar": ["ruzgar"],
    "hidro": ["barajli", "akarsu"],
    "jeotermal": ["jeotermal"],
    "biyokutle": ["biyokutle"],
    "nukleer": ["nukleer"],
    "dogalgaz": ["dogalgaz", "lng"],
    "ithalkomur": ["ithalkomur"],
    "linyit": ["linyit"],
    "taskomur": ["taskomur", "asfaltitkomur"],
    "diger": ["fueloil", "motorin", "nafta", "lpg", "atikisi"],
}
BILINEN = {a for alanlar in GRUPLAR.values() for a in alanlar}

# sure: aralığın uzunluğu (saat). YTBS 2024'ten beri 15 dakikalık, öncesinde saatlik veriyor.
Aralik = namedtuple("Aralik", "bitis mw yuk co2 co2_komur gaz_usd_mwh sure")


def bul(desen, metin, varsayilan=None):
    m = re.search(desen, metin, re.S)
    if m:
        return m.group(1)
    if varsayilan is None:
        raise ValueError(f"sayfada bulunamadı: {desen[:50]}")
    return varsayilan


def dizi(html, ad):
    return json.loads(bul(r"var\s+" + ad + r"\s*=\s*(\[.*?\]);", html))


def iso(t):
    return t.isoformat(timespec="minutes")


class Ytbs:
    """Tek oturum. İlk GET hem bugünün verisini hem de form durumunu (ViewState) verir."""

    def __init__(self):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.op.addheaders = [("User-Agent", UA)]
        self.sayfa = self._oku(URL)
        self.action = urllib.parse.urljoin(URL, bul(r'<form id="formdash"[^>]*action="([^"]+)"', self.sayfa))
        tarih = bul(r'id="formdash:bitisTarihi2_input"[^>]*value="([^"]+)"', self.sayfa)
        self.bugun = datetime.strptime(tarih, "%d-%m-%Y").date()
        self._form_durumu(self.sayfa)

    def _form_durumu(self, html):
        self.viewstate = bul(r'name="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', html)
        self.hidden1 = bul(r'name="hidden1" value="([^"]*)"', html, "13")

    def _oku(self, url, veri=None):
        for deneme in range(3):
            try:
                with self.op.open(urllib.request.Request(url, data=veri), timeout=60) as yanit:
                    return yanit.read().decode("utf-8")
            except OSError as e:
                if deneme == 2:
                    raise
                print(f"  yeniden deneniyor ({e})", file=sys.stderr)
                time.sleep(10 * (deneme + 1))

    def gun(self, d):
        if d == self.bugun:
            return ayristir(self.sayfa, d)
        form = {
            "formdash": "formdash",
            "hidden1": self.hidden1,
            "formdash:bitisTarihi2_input": d.strftime("%d-%m-%Y"),
            "formdash:gunlukRapor": "",
            "jakarta.faces.ViewState": self.viewstate,
        }
        html = self._oku(self.action, urllib.parse.urlencode(form).encode())
        self._form_durumu(html)
        return ayristir(html, d)


def ayristir(html, d):
    """Sayfadaki üretim ve yük dizilerini günün kaydına çevirir, yayımlanmamış aralıkları atar."""
    yuk = {r["zaman"]: r.get("deger") or 0 for r in dizi(html, "gunlukYukEgrisiData")}
    satirlar = [r for r in dizi(html, "gunlukUretimEgrisiData") if r.get("toplam")]
    gun_s = d.isoformat()
    if any(not r["zaman"].startswith(gun_s) for r in satirlar):
        raise ValueError(f"{gun_s} istendi, sayfa başka bir gün döndürdü")
    alanlar = sorted({k for r in satirlar for k in r} - {"zaman", "toplam"})
    for a in sorted(set(alanlar) - BILINEN):
        print(f"  UYARI: yeni YTBS alanı '{a}', 'diger' grubuna eklendi", file=sys.stderr)
    return {
        "tarih": gun_s,
        "cekildi": datetime.now(TSI).isoformat(timespec="seconds"),
        "zaman": [r["zaman"][11:] for r in satirlar],  # aralık sonu, "00:15" ... "24:00"
        "kaynak": {a: [round(r.get(a) or 0, 2) for r in satirlar] for a in alanlar},
        "yuk": [round(yuk.get(r["zaman"], 0), 2) for r in satirlar],
    }


def kesin(yol, d):
    """Gün 96 aralıkla tamamsa ve ertesi gün bittikten sonra çekildiyse yeniden çekmeye gerek yok.

    Böylece dün, geç gelen düzeltmeler için bugün boyunca her çalışmada yeniden çekilir.
    """
    try:
        gun = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    esik = datetime(d.year, d.month, d.day, tzinfo=TSI) + timedelta(days=2)
    return len(gun["zaman"]) == 96 and datetime.fromisoformat(gun["cekildi"]) >= esik


def json_al(url):
    istek = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(istek, timeout=30) as yanit:
        return json.load(yanit)


def fiyatlari_guncelle(bugun):
    """Bugünün TTF ön ay fiyatını (ICE Endex) ve ECB EUR/USD kurlarını data/fiyat.json'a ekler.

    ICE ya da ECB'ye ulaşılamazsa eski kayıtlarla devam edilir; o gün en son bilinen fiyat kullanılır.
    """
    try:
        fiyat = json.loads(FIYAT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fiyat = {"ttf": {}, "eurusd": {}}
    try:
        aylik = [s for s in json_al(ICE_SOZLESMELER)
                 if re.fullmatch(r"[A-Z][a-z]{2}\d{2}", s.get("marketStrip", "")) and s.get("lastPrice")]
        on = min(aylik, key=lambda s: s["endDate"])
        fiyat["ttf"][bugun.isoformat()] = on["lastPrice"]
        fiyat["vade"] = on["marketStrip"]
        if not any(g < bugun.isoformat() for g in fiyat["ttf"]):  # ilk çalışma: geçmiş günleri doldur
            for metin, deger in json_al(ICE_GECMIS.format(on["marketId"]))["bars"]:
                g = datetime.strptime(metin, "%a %b %d %H:%M:%S %Y").date()
                if GERI_DOLDUR - timedelta(days=7) <= g < bugun:  # hafta sonları önceki cumaya baksın
                    fiyat["ttf"][g.isoformat()] = deger
    except (OSError, ValueError, KeyError) as e:
        print(f"UYARI: ICE'den TTF alınamadı ({e})", file=sys.stderr)
    try:
        istek = urllib.request.Request(ECB_KURLAR, headers={"User-Agent": UA})
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            kok = ET.parse(yanit).getroot()
        for kup in kok.iter("{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube"):
            gun_s = kup.get("time")
            if gun_s and gun_s >= (GERI_DOLDUR - timedelta(days=7)).isoformat():
                for kur in kup:
                    if kur.get("currency") == "USD":
                        fiyat["eurusd"][gun_s] = float(kur.get("rate"))
    except (OSError, ET.ParseError, ValueError) as e:
        print(f"UYARI: ECB kuru alınamadı ({e})", file=sys.stderr)
    FIYAT.write_text(json.dumps(fiyat, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return fiyat


def gunun(seri, gun):
    """Günün kaydı; yoksa önceki en yakın gününki (hafta sonu, tatil), o da yoksa ilk kayıt."""
    if not seri:
        return None
    onceki = [g for g in seri if g <= gun]
    return seri[max(onceki)] if onceki else seri[min(seri)]


def gaz_usd_mwh(fiyat, gun):
    """Gaz santralinde bir MWh elektrik için yakılan gazın o günün TTF fiyatı ve kuruyla dolar bedeli."""
    ttf, kur = gunun(fiyat["ttf"], gun), gunun(fiyat["eurusd"], gun)
    if ttf is None or kur is None:
        return None
    return GAZ_M3_MWH * GAZ_KWH_M3 / 1000 * ttf * kur


def aralik_suresi(zaman):
    """Aralık uzunluğu (saat), ardışık bitiş zamanlarının en küçük farkından; tek aralık varsa gece yarısından."""
    dk = [60 * int(z[:2]) + int(z[3:]) for z in zaman]
    farklar = [b - a for a, b in zip(dk, dk[1:]) if b > a]
    return (min(farklar) if farklar else dk[0]) / 60


def araliklar(gun, fiyat):
    """Günün aralıkları: bitiş zamanı, {grup: MW}, yük, saatlik CO₂ ve kömürden CO₂ (ton), MWh başına gaz bedeli, süre."""
    d = date.fromisoformat(gun["tarih"])
    gece = datetime(d.year, d.month, d.day, tzinfo=TSI)
    gaz_usd = gaz_usd_mwh(fiyat, gun["tarih"])
    sure = aralik_suresi(gun["zaman"]) if gun["zaman"] else 0.25
    k = gun["kaynak"]
    for i, hhmm in enumerate(gun["zaman"]):
        saat, dakika = map(int, hhmm.split(":"))
        mw = {g: sum(k[a][i] for a in alanlar if a in k) for g, alanlar in GRUPLAR.items()}
        mw["diger"] += sum(k[a][i] for a in k if a not in BILINEN)
        co2 = {a: k[a][i] * f for a, f in CO2_T_MWH.items() if a in k}
        yield Aralik(gece + timedelta(hours=saat, minutes=dakika), mw, gun["yuk"][i],
                     sum(co2.values()), sum(v for a, v in co2.items() if a in KOMUR_ALANLARI), gaz_usd, sure)


def komur(enerji):
    """MWh (ya da saatlik hız için MW) sözlüğünden (yakılan kömür, ithal kömür) tonu."""
    ithal = enerji["ithalkomur"] * BIRLESIK_T_MWH
    return enerji["linyit"] * LINYIT_T_MWH + enerji["taskomur"] * BIRLESIK_T_MWH + ithal, ithal


def toplamla(secili):
    mwh = dict.fromkeys(GRUPLAR, 0.0)
    for a in secili:
        for g, v in a.mw.items():
            mwh[g] += v * a.sure
    komur_t, ithal_t = komur(mwh)
    fiyatsiz = any(a.gaz_usd_mwh is None for a in secili)
    return {
        "bas": iso(secili[0].bitis - timedelta(hours=secili[0].sure)) if secili else None,
        "son": iso(secili[-1].bitis) if secili else None,
        "aralik": len(secili),
        "mwh": {g: round(v, 1) for g, v in mwh.items()},
        "komurTon": round(komur_t),
        "ithalTon": round(ithal_t),
        "ithalUsd": round(ithal_t * ITHAL_USD_T),
        "co2Ton": round(sum(a.co2 * a.sure for a in secili)),
        "co2KomurTon": round(sum(a.co2_komur * a.sure for a in secili)),
        "gazM3": round(mwh["dogalgaz"] * GAZ_M3_MWH),
        "gazUsd": None if fiyatsiz else round(sum(a.mw["dogalgaz"] * a.sure * a.gaz_usd_mwh for a in secili)),
    }


def ozet_yaz(fiyat):
    simdi = datetime.now(TSI)
    gunluk = []
    for p in sorted(GUN_DIZINI.glob("*.json")):
        gun = json.loads(p.read_text(encoding="utf-8"))
        gunluk.append((gun["tarih"], [a for a in araliklar(gun, fiyat) if a.bitis <= simdi - KESINLESME]))
    hepsi = [a for _, secili in gunluk for a in secili]
    if not hepsi:
        raise SystemExit("data/gun altında kesinleşmiş veri yok")
    son = hepsi[-1]
    bugun = simdi.date().isoformat()
    komur_saat, ithal_saat = komur(son.mw)
    son24 = hepsi[-96:]
    son_ttf = max(fiyat["ttf"], default=None)
    son_kur = max(fiyat["eurusd"], default=None)
    gaz_bugun = gaz_usd_mwh(fiyat, bugun)
    ozet = {
        "guncellendi": simdi.isoformat(timespec="seconds"),
        "kaynak": "TEİAŞ YTBS",
        "cop": {"bas": iso(COP_BAS), "bit": iso(COP_BIT)},
        "katsayi": {
            "linyitTonMwh": round(LINYIT_T_MWH, 4),
            "birlesikTonMwh": round(BIRLESIK_T_MWH, 4),
            "ithalUsdTon": ITHAL_USD_T,
            "gazM3Mwh": round(GAZ_M3_MWH, 1),
            "co2TonMwh": CO2_T_MWH,
        },
        "fiyat": {
            "ttf": fiyat["ttf"].get(son_ttf),
            "ttfTarih": son_ttf,
            "vade": fiyat.get("vade"),
            "eurusd": fiyat["eurusd"].get(son_kur),
            "kurTarih": son_kur,
            "gazUsdMwh": None if gaz_bugun is None else round(gaz_bugun, 1),
        },
        "simdi": {
            "zaman": iso(son.bitis),
            "mw": {g: round(v) for g, v in son.mw.items()},
            "yuk": round(son.yuk),
            "co2": round(son.co2, 1),
        },
        # Sayfa sayaçları bir sonraki veriye kadar son aralığın saatlik hızıyla ilerletir.
        "hiz": {
            "mwh": {g: round(v, 1) for g, v in son.mw.items()},
            "komurTon": round(komur_saat, 1),
            "ithalUsd": round(ithal_saat * ITHAL_USD_T),
            "co2Ton": round(son.co2, 1),
            "gazM3": round(son.mw["dogalgaz"] * GAZ_M3_MWH),
            "gazUsd": None if son.gaz_usd_mwh is None else round(son.mw["dogalgaz"] * son.gaz_usd_mwh),
        },
        "bugun": toplamla(next((secili for tarih, secili in gunluk if tarih == bugun), [])),
        "copDonemi": toplamla([a for a in hepsi if COP_BAS < a.bitis <= COP_BIT]),
        "gunler": [{"tarih": tarih, "ttf": gunun(fiyat["ttf"], tarih), **toplamla(secili)}
                   for tarih, secili in gunluk if secili],
        "kapasite": KAPASITE,
        "seri": {
            "zaman": [iso(a.bitis) for a in son24],
            "mw": {g: [round(a.mw[g]) for a in son24] for g in GRUPLAR},
            "yuk": [round(a.yuk) for a in son24],
        },
    }
    OZET.write_text(json.dumps(ozet, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    GUN_DIZINI.mkdir(parents=True, exist_ok=True)
    ytbs = Ytbs()
    gerekli = [ytbs.bugun]
    d = GERI_DOLDUR
    while d < ytbs.bugun:
        if not kesin(GUN_DIZINI / f"{d}.json", d):
            gerekli.append(d)
        d += timedelta(days=1)
    bugun_hatali = False
    for d in sorted(gerekli):
        try:
            gun = ytbs.gun(d)
        except Exception as e:  # bir günün hatası öbür günleri durdurmasın
            print(f"HATA {d}: {e}", file=sys.stderr)
            bugun_hatali = bugun_hatali or d == ytbs.bugun
            continue
        (GUN_DIZINI / f"{d}.json").write_text(json.dumps(gun, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{d}: {len(gun['zaman'])} aralık")
    ozet_yaz(fiyatlari_guncelle(ytbs.bugun))
    return 1 if bugun_hatali else 0


if __name__ == "__main__":
    sys.exit(main())
