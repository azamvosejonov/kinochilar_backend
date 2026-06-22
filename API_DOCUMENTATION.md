# Kinochilar Backend API Documentation

## 🎬 Kinochilar API - To'liq Hujjatlar

Bu hujjatlar Kinochilar backendining barcha API endpointlarini o'z ichiga oladi. FastAPI asosida yaratilgan bo'lib, PostgreSQL va Redis ishlatadi.

**Base URL:** `http://localhost:8085/api/v1`

---

## 🔐 Autentifikatsiya (Auth)

### 1. Ro'yxatdan o'tish (Register)
**POST** `/auth/register`

Yangi foydalanuvchi ro'yxatdan o'tkazadi.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Ism Familiya",
  "is_superuser": false
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Ism Familiya",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 2. Tizimga kirish (Login)
**POST** `/auth/login`

Foydalanuvchi tizimga kiradi va JWT token oladi.

**Request Body (form-data):**
```
username: user@example.com
password: password123
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Usage:** Keyingi so'rovlarda `Authorization: Bearer <token>` headerini ishlating.

---

## 🏠 Discovery (Bosh sahifa)

### 3. Bosh sahifa ma'lumotlari (Home)
**GET** `/discovery/home`

Bosh sahifa uchun barcha kerakli ma'lumotlarni qaytaradi: trending kinolar, top reytingli kinolar, reklamar, janrlar.

**Response (200):**
```json
{
  "trending": [
    {
      "id": 1,
      "title_uz": "Avatar: Suv Yo'li",
      "title_ru": "Аватар: Путь воды",
      "rating": 8.5,
      "views": 1000,
      "poster_path": "https://...",
      "genres": []
    }
  ],
  "top_rated": [...],
  "ads": [],
  "genres": [
    {
      "id": 1,
      "name_uz": "Jangari",
      "name_ru": "Боевик"
    }
  ]
}
```

---

### 4. AI Maslahatchi (AI Chat)
**POST** `/discovery/chat?query=savol`

AI yordamida kino tavsiyalari oladi.

**Parameters:**
- `query`: Savol (masalan: "Yaxshi komediya kinolarini tavsiya bering")

**Response (200):**
```json
{
  "answer": "Sizga quyidagi komediyalarni tavsiya qilaman: ..."
}
```

---

## 🎬 Kinolar (Movies)

### 5. Kinolar ro'yxati (List Movies)
**GET** `/movies/?skip=0&limit=20&genre_id=1&query=test&lang=uz`

Barcha kinolarni ro'yxatini qaytaradi. Filtrlash va qidirish mumkin.

**Parameters:**
- `skip`: Qaysi indexdan boshlash (default: 0)
- `limit`: Nechta kino olish (default: 20)
- `genre_id`: Janr bo'yicha filtrlash
- `query`: Qidiruv so'zi
- `lang`: Til ('uz' yoki 'ru', default: 'uz')

**Response (200):**
```json
[
  {
    "id": 1,
    "code": "avt001",
    "title_uz": "Avatar: Suv Yo'li",
    "title_ru": "Аватар: Путь воды",
    "description_uz": "Jek Salli va Neytiri yangi sarguzashtlarni boshdan kechiradilar.",
    "rating": 8.5,
    "views": 100,
    "poster_path": "https://...",
    "is_premium": 0,
    "is_series": false
  }
]
```

---

### 6. Kino qidirish (Search)
**GET** `/movies/search?query=avatar&lang=uz`

Aqlli qidiruv - xatolarni tuzatadi, fuzzy match ishlatadi.

**Parameters:**
- `query`: Qidiruv so'zi
- `lang`: Til ('uz' yoki 'ru')

**Response (200):**
```json
[
  {
    "id": 1,
    "title_uz": "Avatar: Suv Yo'li",
    "rating": 8.5
  }
]
```

---

### 7. Kino kod bo'yicha (Get by Code)
**GET** `/movies/code/{code}`

Telegram botlar uchun tezkor kino qidirish.

**Parameters:**
- `code`: Kino kodi (masalan: "avt001")

**Response (200):**
```json
{
  "id": 1,
  "code": "avt001",
  "title_uz": "Avatar: Suv Yo'li",
  ...
}
```

---

### 8. Kino ma'lumotlari (Get by ID)
**GET** `/movies/{movie_id}`

Kino haqida batafsil ma'lumot. Ko'rishlar soni avtomatik oshadi.

**Parameters:**
- `movie_id`: Kino ID si

**Response (200):**
```json
{
  "id": 1,
  "title_uz": "Avatar: Suv Yo'li",
  "description_uz": "...",
  "rating": 8.5,
  "views": 101,
  "genres": [],
  "tags": []
}
```

---

### 9. Kino yaratish (Create Movie) - Admin Only
**POST** `/movies/`

Yangi kino qo'shadi (faqat admin uchun).

**Headers:**
- `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "title_uz": "Yangi Kino",
  "title_ru": "Новый фильм",
  "description_uz": "Kino tavsifi",
  "rating": 8.0,
  "genre_ids": [1, 2],
  "tag_ids": [1]
}
```

---

## 🎥 Video Streaming

### 10. Video stream
**GET** `/stream/{movie_id}`

Video faylni stream qiladi. HTTP Range Requests (206 Partial Content) ni qo'llab-quvvatlaydi - foydalanuvchi kinoning istalgan joyiga o'tishi mumkin.

**Parameters:**
- `movie_id`: Kino ID si

**Headers:**
- `Range: bytes=0-1024` (video player tomonidan yuboriladi)

**Response (206):**
```
Content-Range: bytes 0-1024/1048576
Accept-Ranges: bytes
Content-Type: video/mp4
```

---

## ❤️ Foydalanuvchi amallari (Users)

### 11. Sevimlilarga qo'shish (Add to Favorites)
**POST** `/users/favorites/{movie_id}`

Kinoni sevimlilarga qo'shadi.

**Headers:**
- `Authorization: Bearer <token>`

**Response (201):**
```json
{
  "message": "Added to favorites"
}
```

---

### 12. Sevimlilardan o'chirish (Remove from Favorites)
**DELETE** `/users/favorites/{movie_id}`

Kinoni sevimlilardan o'chiradi.

**Headers:**
- `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Removed from favorites"
}
```

---

### 13. Sevimlilar ro'yxati (Get Favorites)
**GET** `/users/favorites`

Foydalanuvchining sevimli kinolari ro'yxati.

**Headers:**
- `Authorization: Bearer <token>`

**Response (200):**
```json
[
  {
    "id": 1,
    "title_uz": "Avatar: Suv Yo'li",
    "rating": 8.5
  }
]
```

---

## 💬 Izohlar (Comments)

### 14. Izohlar ro'yxati (List Comments)
**GET** `/comments/movie/{movie_id}`

Kino uchun barcha izohlarni qaytaradi.

**Parameters:**
- `movie_id`: Kino ID si

**Response (200):**
```json
[
  {
    "id": 1,
    "content": "Bu kino juda ajoyib!",
    "rating": 9.0,
    "user_name": "User Name",
    "movie_id": 1
  }
]
```

---

### 15. Izoh yaratish (Create Comment)
**POST** `/comments/movie/{movie_id}`

Yangi izoh qoldiradi. AI moderatsiyadan o'tadi.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "content": "Bu kino juda ajoyib! Tavsiya qilaman.",
  "rating": 9.0
}
```

**Response (201):**
```json
{
  "id": 1,
  "content": "Bu kino juda ajoyib! Tavsiya qilaman.",
  "rating": 9.0,
  "user_name": "User Name",
  "movie_id": 1
}
```

**AI Moderatsiya:** Spam va noadekvat izohlar avtomatik ravishda rad etiladi.

---

## 📊 Admin (Admin Panel)

### 16. Admin statistikasi (Stats Overview)
**GET** `/admin/stats/overview`

Admin dashboard uchun statistika.

**Headers:**
- `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "users": {
    "total": 100,
    "new_24h": 5
  },
  "ai_performance": {
    "today_acquired": 50,
    "today_descriptions": 10,
    "recent_actions": [
      {
        "action": "user_acquisition",
        "desc": "AI acquired 50 new users",
        "time": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

---

### 17. Foydalanuvchilar ro'yxati (List Users)
**GET** `/admin/users`

Barcha foydalanuvchilar ro'yxati.

**Headers:**
- `Authorization: Bearer <admin_token>`

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "full_name": "User Name",
    "is_active": true,
    "is_superuser": false
  }
]
```

---

### 18. AI avtonom trigger (AI Autonomous)
**POST** `/admin/ai/trigger-autonomous`

AI ni avtonom rejimni ishga tushiradi - kontent yaratish, foydalanuvchilarni jalb qilish.

**Headers:**
- `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
  "status": "AI Master Management cycle completed successfully",
  "actions": ["content_generated", "users_acquired"]
}
```

---

### 19. Reklama yaratish (Create Ad) - Admin Only
**POST** `/admin/ads`

Yangi reklama qo'shadi.

**Headers:**
- `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "title": "Maxsus taklif",
  "description": "50% chegirma",
  "image_url": "https://...",
  "link": "https://...",
  "is_active": true
}
```

---

### 20. Episode yaratish (Create Episode) - Admin Only
**POST** `/admin/episodes`

Serial uchun yangi episode qo'shadi.

**Headers:**
- `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "movie_id": 1,
  "season_number": 1,
  "episode_number": 1,
  "title_uz": "1-qism",
  "video_url": "episode1.mp4"
}
```

---

## 🤖 AI Xususiyatlari

### AI Moderatsiya
Izohlarni avtomatik tekshiradi:
- Spam aniqlash
- Noadekvat kontentni bloklash
- Odob-axloq qoidalariga tekshirish

### AI Auto-Growth
- Avtomatik kontent yaratish
- Foydalanuvchilarni jalb qilish
- Tavsiya tizimini optimallashtirish

### AI Consultant
- Foydalanuvchilarga kino tavsiyalari berish
- Natural language processing
- Personalized tavsiyalar

---

## 📋 Xato kodlari (Error Codes)

- `200` - Muvaffaqiyatli
- `201` - Yaratildi (Created)
- `400` - Xato so'rov (Bad Request)
- `401` - Autentifikatsiya talab qilinadi
- `403` - Ruxsat yo'q (Forbidden)
- `404` - Topilmadi (Not Found)
- `500` - Server xatosi (Internal Server Error)

---

## 🔒 Xavfsizlik

- JWT token based autentifikatsiya
- Bcrypt password hashing
- CORS middleware
- AI content moderation
- Admin role based access control

---

## 🚀 Performance

- Asynchronous FastAPI
- PostgreSQL database
- Redis caching
- HTTP Range Requests for video streaming
- Optimized database queries

---

## 📝 Qo'shimcha ma'lumotlar

- **Swagger UI:** `http://localhost:8085/docs`
- **ReDoc:** `http://localhost:8085/redoc`
- **Database:** PostgreSQL (async)
- **Cache:** Redis
- **Container:** Docker & Docker Compose

---

Yaratuvchi: Antigravity AI  
Versiya: 1.0.0