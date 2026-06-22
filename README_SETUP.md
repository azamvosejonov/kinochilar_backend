# Kinochilar - Docker'siz Sozlash

Bu README fayli Kinochilar loyihasini Docker'siz qanday ishga tushirishni ko'rsatadi.

## 📋 Talablar

- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Nginx
- Redis (ixtiyoriy)

## 🚀 Tezkor Sozlash

### 1. Backend Sozlash

```bash
cd /home/azam/Desktop/yaratish/kinochilar

# Backend ishga tushirish
./start_backend.sh
```

Backend `http://localhost:8080` da ishlaydi.
API docs: `http://localhost:8080/docs`

### 2. Frontend Sozlash

```bash
cd /home/azam/Desktop/kinochilar_web

# Frontend ishga tushirish
./start_frontend.sh
```

Frontend `http://localhost:3000` da ishlaydi.

### 3. Nginx Reverse Proxy Sozlash

```bash
cd /home/azam/Desktop/yaratish/kinochilar

# Nginx ishga tushirish
./start_nginx.sh
```

Sayt `http://localhost` da ishlaydi.

## 🗄️ Database Sozlash

PostgreSQL o'rnatish va sozlash:

```bash
# PostgreSQL o'rnatish
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Database yaratish
sudo -u postgres psql
CREATE DATABASE kinochilar;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE kinochilar TO postgres;
\q
```

## 🎬 AI Video Yuklash

AI video yuklash service admin panel orqali boshqariladi:

1. Admin panelga kiring: `http://localhost:8080/docs`
2. Autentifikatsiyadan o'ting
3. Video download endpointlarini ishlating:

### Video Manbalarini Qidirish
```bash
GET /api/v1/admin/video/sources/{movie_id}
```

### Bitta Kino Uchun Video Yuklash
```bash
POST /api/v1/admin/video/download/{movie_id}
```

### Guruhli Video Yuklash
```bash
POST /api/v1/admin/video/batch-download?limit=5
```

## 🌐 Legal Content Yuklash

Legal ochiq content manbalaridan kino yuklash:

### Legal Content Qidirish
```bash
POST /api/v1/admin/legal/search
{
  "query": "action movie"
}
```

### Legal Contentni Databasega Qo'shish
```bash
POST /api/v1/admin/legal/populate
{
  "queries": ["action", "comedy", "drama"],
  "limit": 10
}
```

## 🤖 Content Enrichment

AI orqali kino ma'lumotlarini boyitish:

### Bitta Kinoni Boyitish
```bash
POST /api/v1/admin/enrich/{movie_id}
```

### Guruhli Boyitish
```bash
POST /api/v1/admin/enrich/batch?limit=10
```

Bu endpointlar:
- AI tavsiflar generatsiya qiladi
- TMDB'dan qo'shimcha ma'lumotlar oladi
- Smart taglar yaratadi
- Poster va backdrop rasmlarini yangilaydi

## 📁 Proyekt Tuzilishi

```
kinochilar/
├── app/
│   ├── api/           # API endpointlar
│   ├── core/          # Konfiguratsiya
│   ├── db/            # Database modellari
│   ├── models/        # SQLAlchemy modellari
│   ├── schemas/       # Pydantic schemalari
│   └── services/      # Business logic
│       ├── ai_service.py        # AI kontent yaratish
│       ├── video_service.py     # Video yuklash
│       └── management_ai.py    # AI boshqaruv
├── start_backend.sh   # Backend ishga tushirish
├── start_nginx.sh     # Nginx ishga tushirish
└── .env              # Environment variables

kinochilar_web/
├── app/              # Next.js sahifalar
├── components/       # React komponentlari
├── lib/             # Utility funksiyalar
└── start_frontend.sh # Frontend ishga tushirish
```

## 🔧 Environment Variables

Backend `.env` fayli:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/kinochilar
SECRET_KEY=supersecretkey
AI_API_KEY=your_ai_api_key
TMDB_API_KEY=your_tmdb_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Frontend `.env.local` fayli:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## 🎨 Dizayn Yangiliklari

- **Hero Section**: Ken Burns effekti bilan animatsiyalangan backdrop
- **Movie Cards**: Modern dizayn, rating va view badge'lari
- **Header**: Gradient effektlar, hover animatsiyalari
- **Footer**: To'liq kontakt ma'lumotlari va social media linklari
- **Responsive**: Barcha qurilmalar uchun moslashuvchan dizayn

## 🔍 Monitoring

### Backend status
```bash
curl http://localhost:8080/
```

### Frontend status
```bash
curl http://localhost:3000/
```

### Nginx status
```bash
sudo systemctl status nginx
```

## 🐛 Troubleshooting

### Backend ishlamayapti
- Virtual environment faollashtirilganligini tekshiring
- Dependencies o'rnatilganligini tekshiring
- Database ulanishini tekshiring

### Frontend ishlamayapti
- Node.js o'rnatilganligini tekshiring
- Dependencies o'rnatilganligini tekshiring
- API URL to'g'ri ekanligini tekshiring

### Nginx ishlamayapti
- Nginx o'rnatilganligini tekshiring
- Konfiguratsiya to'g'ri ekanligini tekshiring: `sudo nginx -t`
- Backend va frontend ishlayotganligini tekshiring

## 📞 Yordam

Agar muammolar yuzaga kelsa:
1. Log fayllarini tekshiring
2. Portlar band emasligini tekshiring
3. Firewall sozlamalarini tekshiring

## 🎉 Tayyor!

Endi Kinochilar platformasi to'liq ishlamoqda:
- 🌐 Asosiy sayt: `http://localhost`
- 📚 API docs: `http://localhost:8080/docs`
- 🎬 Video streaming: `http://localhost/stream`