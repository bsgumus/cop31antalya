#!/data/data/com.termux/files/usr/bin/bash
# Termux'ta (Android) bir kez çalıştırılır: paketler, GitHub girişi, depo. Sonra veri/telefon.sh başlatılır.
#
#   curl -fsSLo kur.sh https://raw.githubusercontent.com/bsgumus/cop31antalya/main/veri/termux_kur.sh && bash kur.sh
#
# (Boru ile "| bash" çalıştırmayın: GitHub girişi klavyeden Enter bekler.)
set -e
pkg update -y
pkg install -y python git gh

# GitHub girişi: ekranda bir kod çıkar; github.com/login/device adresinde girip onaylayın.
gh auth status >/dev/null 2>&1 || gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
git config --global user.name "Bahadır Sercan GÜMÜŞ"
git config --global user.email "70887901+bsgumus@users.noreply.github.com"

[ -d "$HOME/cop31antalya/.git" ] || git clone --depth 1 https://github.com/bsgumus/cop31antalya.git "$HOME/cop31antalya"
echo
echo "Kurulum tamam. Başlatmak için:  bash ~/cop31antalya/veri/telefon.sh"
