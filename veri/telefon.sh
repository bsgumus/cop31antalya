#!/data/data/com.termux/files/usr/bin/bash
# Android telefonda (Termux) TEİAŞ verisini her saatin 07, 22, 37 ve 52. dakikasında çekip GitHub'a
# gönderir; GitHub her gönderimde siteyi yayınlar. Mac kapalıyken kullanılır. Telefon Türkiye'de
# olmalı: TEİAŞ yalnız Türkiye'den erişilebiliyor. Kurulum: veri/termux_kur.sh (KURULUM.md).
#
#   bash ~/cop31antalya/veri/telefon.sh            sürekli çalışır (Termux açık kalsın)
#   TEK_SEFER=1 GONDERME=1 bash veri/telefon.sh    bir kez çalışır, göndermez (deneme)
cd "$(dirname "$0")/.." || exit 1
command -v termux-wake-lock >/dev/null && termux-wake-lock   # ekran kapalıyken de çalışsın

tur() {
    # Her tur depodaki son halden başlar: Mac de gönderiyorsa çakışma olmaz, kaybeden bir sonraki turu bekler.
    git fetch -q --depth 1 origin main && git reset -q --hard origin/main || return 1
    python3 veri/guncelle.py   # bugünün verisi alınamasa da fiyat ve özet güncellenmiş olabilir
    git add data
    if git diff --cached --quiet; then echo "değişiklik yok"; return 0; fi
    git commit -q -m "Veri (telefon): $(TZ=Europe/Istanbul date '+%Y-%m-%d %H:%M')"
    [ -n "${GONDERME:-}" ] && { echo "göndermedim (deneme)"; return 0; }
    git push -q origin HEAD:main && echo "gönderildi"
}

bekle() {  # bir sonraki 07, 22, 37 ya da 52. dakikaya kadar saniye
    local m s t
    m=$((10#$(date +%M))); s=$((10#$(date +%S)))
    for t in 7 22 37 52 67; do [ "$t" -gt "$m" ] && break; done
    echo $(( (t - m) * 60 - s ))
}

while true; do
    echo "== $(TZ=Europe/Istanbul date '+%Y-%m-%d %H:%M:%S')"
    tur || echo "bu tur olmadı (bağlantı?), bir sonrakinde yeniden denenecek"
    [ -n "${TEK_SEFER:-}" ] && break
    sleep "$(bekle)"
done
