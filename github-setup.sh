#!/bin/bash
# Připojení na GitHub: https://github.com/sharkjd/workia-vendy-bot

cd "$(dirname "$0")"

echo "1. Přidávám remote origin..."
git remote add origin https://github.com/sharkjd/workia-vendy-bot.git 2>/dev/null || git remote set-url origin https://github.com/sharkjd/workia-vendy-bot.git

echo "2. Přejmenovávám větev na main..."
git branch -M main

echo "3. Stahuji obsah z GitHubu (remote má README)..."
git pull origin main --allow-unrelated-histories --no-edit

echo "4. Nahrávám na GitHub..."
git push -u origin main

echo "Hotovo! Repozitář: https://github.com/sharkjd/workia-vendy-bot"
