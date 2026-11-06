#!/bin/bash
# TEİAŞ YTBS yalnız Türkiye'den erişilebildiği için veri bu bilgisayarda çekilir ve GitHub'a
# gönderilir; GitHub her gönderimde siteyi yayınlar (.github/workflows/veri.yml).
# macOS'ta launchd 15 dakikada bir çalıştırır: veri/com.cop31antalya.veri.plist (KURULUM.md).
set -u
cd "$(dirname "$0")/.." || exit 1
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"
echo "== $(date '+%Y-%m-%d %H:%M:%S')"
/usr/bin/python3 veri/guncelle.py   # bugünün verisi alınamasa da fiyat ve özet güncellenmiş olabilir
git add data
if git diff --cached --quiet; then echo "değişiklik yok"; exit 0; fi
git commit -q -m "Veri: $(TZ=Europe/Istanbul date '+%Y-%m-%d %H:%M')"
if ! git pull -q --rebase --autostash origin main; then
    # Telefon da gönderiyorsa veri dosyaları çakışabilir: yerel veri kaydı bırakılır, depodaki daha
    # yeni veri alınır, bir sonraki turda yeniden üretilir. Kaydedilmemiş yerel düzenlemeler korunur.
    git rebase --abort 2>/dev/null
    git reset -q --keep origin/main && echo "çakışma: depodaki veri alındı"
    exit 0
fi
git push -q origin main && echo "gönderildi"
