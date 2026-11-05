# cop31antalya.org bağlantı önizlemesi (og:image), 1200×630. Karışım çubuğu 3 Kasım 2026'nın gerçek payları.
# Pillow ve macOS'taki Helvetica gerekir; yalnız görseli değiştirmek isterseniz çalıştırın:
#     python3 veri/og_gorsel.py .
import json, sys
from PIL import Image, ImageDraw, ImageFont

kok = sys.argv[1]
W, H, P = 1200, 630, 72
img = Image.new("RGB", (W, H), "#1a1a19")
d = ImageDraw.Draw(img)
HELV = "/System/Library/Fonts/Helvetica.ttc"
kalin = lambda s: ImageFont.truetype(HELV, s, index=1)
ince = lambda s: ImageFont.truetype(HELV, s, index=0)

d.text((P, 84), "COP31 · Antalya · 9–20 Kasım 2026", font=ince(28), fill="#c3c2b7")
d.text((P, 150), "COP31 Elektrik Sayacı", font=kalin(72), fill="#f0efec")
d.text((P, 250), "Türkiye'nin elektriği canlı: rüzgâr ve güneş,", font=ince(36), fill="#f0efec")
d.text((P, 296), "yakılan kömür, CO₂ ve yakıt faturası", font=ince(36), fill="#f0efec")
d.text((P, 356), "Live: Türkiye's electricity during COP31", font=ince(26), fill="#898781")

gun = json.load(open(f"{kok}/data/ozet.json"))["gunler"]
m = next(g for g in gun if g["tarih"] == "2026-11-03")["mwh"]
parca = [("#c98500", m["gunes"]), ("#199e70", m["ruzgar"]), ("#9085e9", m["jeotermal"] + m["biyokutle"]),
         ("#d95926", m["dogalgaz"]), ("#3987e5", m["hidro"]), ("#9c6a21", m["linyit"] + m["ithalkomur"] + m["taskomur"]),
         ("#c3c2b7", m["diger"] + m["nukleer"])]
top, x, cw = sum(v for _, v in parca), P, W - 2 * P - 2 * (len(parca) - 1)
for i, (renk, v) in enumerate(parca):
    w = v / top * cw
    d.rounded_rectangle([x, 440, x + w, 462], radius=11 if i in (0, len(parca) - 1) else 0, fill=renk)
    x += w + 2
d.text((P, 520), "cop31antalya.org", font=kalin(34), fill="#f0efec")
d.text((P, 566), "Bağımsız veri platformu · Kaynak: TEİAŞ YTBS", font=ince(22), fill="#898781")
img.save(f"{kok}/og.png", optimize=True)
print(img.size)
