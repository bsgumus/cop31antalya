#!/usr/bin/env python3
"""TEİAŞ YTBS'nin 2016'dan bu yana bütün günlerini çekip data/gecmis.json'a gün özeti yazar.

Sayfa bu arşivi şu an kullanmıyor (rekorlar ve geçen yılla karşılaştırma kaldırıldı); 10 yıllık
özet ileride işe yarar diye saklanıyor, canlı iş akışı bu dosyaya dokunmaz. Önce geçen yılın COP
dönemini, sonra en yeni günden geriye bütün günleri çeker; yarıda kesilirse kaldığı yerden devam
eder. TEİAŞ geçmiş bir günü 3-10 sn'de veriyor: baştan doldurmak yarım günü bulur. YTBS 2024
öncesini saatlik, sonrasını 15 dakikalık veriyor (özetteki "dk" alanı).

    python3 veri/gecmis_doldur.py
"""
import json
import sys
import time
from datetime import date, timedelta

import guncelle as g

GECMIS = g.KOK / "data" / "gecmis.json"
GECMIS_BAS = date(2016, 1, 1)  # YTBS'deki en eski gün


def gecmis_oku():
    try:
        return json.loads(GECMIS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gecmis_yaz(gecmis):
    GECMIS.write_text(json.dumps(dict(sorted(gecmis.items())), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def gun_ozeti(aa):
    """Bir günün özeti: grup başına MWh, CO₂ ve günün uç değerleri (en yüksek güneş/rüzgâr ve payları, en düşük yoğunluk)."""
    if not aa:
        return None

    def uc(deger, en=max, basamak=1):
        a = en(aa, key=deger)
        return [round(deger(a), basamak), g.iso(a.bitis)]

    def pay(a, gruplar):
        return 100 * sum(a.mw[k] for k in gruplar) / sum(a.mw.values())

    o = g.toplamla(aa)
    return {
        "aralik": len(aa),
        "dk": round(aa[0].sure * 60),
        "mwh": o["mwh"],
        "co2": o["co2Ton"],
        "gunesMw": uc(lambda a: a.mw["gunes"]),
        "ruzgarMw": uc(lambda a: a.mw["ruzgar"]),
        "gunesPay": uc(lambda a: pay(a, ["gunes"]), basamak=2),
        "rgPay": uc(lambda a: pay(a, ["gunes", "ruzgar"]), basamak=2),
        "yogunluk": uc(lambda a: 1000 * a.co2 / sum(a.mw.values()), en=min, basamak=0),
    }


def sira():
    """Önce geçen yılın aynı dönemi, sonra yeniden eskiye bütün günler."""
    bas = (g.GERI_DOLDUR - timedelta(days=10)).replace(year=g.GERI_DOLDUR.year - 1)
    bit = (g.COP_BIT.date() + timedelta(days=10)).replace(year=g.COP_BIT.year - 1)
    gecen_yil = [bas + timedelta(days=i) for i in range((bit - bas).days + 1)]
    yield from gecen_yil
    d = g.GERI_DOLDUR - timedelta(days=1)
    while d >= GECMIS_BAS:
        if d not in gecen_yil:
            yield d
        d -= timedelta(days=1)


def main():
    gecmis = gecmis_oku()
    ytbs = g.Ytbs()
    yeni = 0
    for d in sira():
        if d.isoformat() in gecmis:
            continue
        for deneme in range(3):
            try:
                gun = ytbs.gun(d)
                break
            except Exception as e:  # oturum düşmüş olabilir: yeni oturumla aynı günü bir daha dene
                print(f"{d}: {e}", file=sys.stderr, flush=True)
                time.sleep(10)
                ytbs = g.Ytbs()
        else:
            continue
        ozet = gun_ozeti(list(g.araliklar(gun, {"ttf": {}, "eurusd": {}})))
        if ozet:
            gecmis[d.isoformat()] = ozet
            yeni += 1
        if yeni and yeni % 10 == 0:
            gecmis_yaz(gecmis)
            print(f"{d} ({len(gecmis)} gün)", flush=True)
        time.sleep(0.3)
    gecmis_yaz(gecmis)
    print(f"bitti: {len(gecmis)} gün, {yeni} yeni", flush=True)


if __name__ == "__main__":
    main()
