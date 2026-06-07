# Kinochilar Backend - Mukammal Kino Sayti API

Bu proekt FastAPI yordamida yaratilgan bo'lib, eng mashhur kino saytlari (Netflix, TMDB, IMDb) ning eng yaxshi xususiyatlarini o'z ichiga oladi.

## Asosiy Xususiyatlar

- **🔐 Mukammal Auth**: OAuth2 Password Flow va JWT tokenlar bilan xavfsiz autentifikatsiya.
- **🎬 Movie Metadata**: Kinolar, janrlar, aktyorlar va reytinglar tizimi (TMDB kabi).
- **🚀 Video Streaming**: HTTP Range Requests (206 Partial Content) ni qo'llab-quvvatlaydigan yuqori samarali stream tizimi. Foydalanuvchilar kinoning xohlagan joyiga o'tkazishi mumkin.
- **📈 User Interactions**: Review-lar, reytinglar, ko'rishlar tarixi (History) va Watchlist.
- **🛠 Admin Dashboard**: Kontentni boshqarish uchun maxsus endpointlar.
- **🐳 Dockerized**: PostgreSQL va Redis bilan birga oson ishga tushirish.

## Texnologiyalar

- **Framework**: FastAPI (Asynchronous)
- **Database**: PostgreSQL (SQLAlchemy Async)
- **Security**: JWT, Bcrypt
- **Caching**: Redis
- **Containerization**: Docker & Docker Compose

## Ishga Tushirish

1. Docker-ni o'rnating.
2. Quyidagi buyruqni bering:
```bash
docker-compose up --build
```
3. API quyidagi manzilda ishlaydi: `http://localhost:8000`
4. Dokumentatsiya (Swagger): `http://localhost:8000/docs`

## Proekt Strukturasi

- `app/api`: API endpointlari (auth, movies, stream).
- `app/core`: Sozlamalar va xavfsizlik (JWT, hashing).
- `app/models`: Ma'lumotlar bazasi modellari.
- `app/schemas`: Pydantic validatsiya modellari.
- `app/db`: Database sessiyalari.

---
Yaratuvchi: Antigravity AI
