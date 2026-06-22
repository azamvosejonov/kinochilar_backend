#!/bin/bash

# Nginx reverse proxy ishga tushirish scripti

echo "🚀 Nginx Reverse Proxy - Docker'siz ishga tushirish"

# 1. Nginx o'rnatish (agar o'rnatilmagan bo'lsa)
if ! command -v nginx &> /dev/null; then
    echo "📦 Nginx o'rnatilmoqda..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# 2. Nginx konfiguratsiyasini nusxalash
echo "🔧 Nginx konfiguratsiyasi sozlanmoqda..."
sudo cp nginx_simple.conf /etc/nginx/sites-available/kinochilar

# 3. Symbolic link yaratish
sudo ln -sf /etc/nginx/sites-available/kinochilar /etc/nginx/sites-enabled/kinochilar

# 4. Default konfiguratsiyani o'chirish
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Data directory yaratish
echo "📁 Data directory yaratilmoqda..."
sudo mkdir -p /data/movies
sudo chown -R $USER:$USER /data

# 6. Nginx konfiguratsiyasini tekshirish
echo "🔍 Nginx konfiguratsiyasi tekshirilmoqda..."
sudo nginx -t

# 7. Nginxni qayta ishga tushirish
echo "🔄 Nginx qayta ishga tushirilmoqda..."
sudo systemctl restart nginx

# 8. Nginx statusini tekshirish
sudo systemctl status nginx

echo "✅ Nginx reverse proxy ishga tushirildi!"
echo "🌐 Sayt: http://localhost"
echo "📚 Backend API: http://localhost/api"
echo "🎬 Video streaming: http://localhost/stream"