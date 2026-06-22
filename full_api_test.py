import httpx
import asyncio
import json

BASE_URL = "http://localhost:8085/api/v1"

async def test_all():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 Kinochilar Backend To'liq Test\n")
        print("=" * 50)

        # 1. Auth - Register
        print("\n📝 1. Ro'yxatdan o'tish (Register)...")
        register_res = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "test123",
                "full_name": "Test User",
                "is_superuser": False
            }
        )
        if register_res.status_code == 200:
            print("✅ Ro'yxatdan o'tish muvaffaqiyatli")
        else:
            print(f"⚠️ Ro'yxatdan o'tish: {register_res.status_code} - {register_res.text}")

        # 2. Auth - Login
        print("\n🔐 2. Tizimga kirish (Login)...")
        login_res = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": "vosejonova@gmail.com", "password": "azam_770"}
        )
        if login_res.status_code != 200:
            print(f"❌ Login xatosi: {login_res.text}")
            return
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login muvaffaqiyatli")

        # 3. Discovery - Home
        print("\n🏠 3. Bosh sahifa (Discovery Home)...")
        home_res = await client.get(f"{BASE_URL}/discovery/home")
        if home_res.status_code == 200:
            data = home_res.json()
            print(f"✅ Trending kinolar: {len(data.get('trending', []))}")
            print(f"✅ Top reytingli kinolar: {len(data.get('top_rated', []))}")
            print(f"✅ Reklamalar: {len(data.get('ads', []))}")
            print(f"✅ Janrlar: {len(data.get('genres', []))}")
        else:
            print(f"❌ Discovery xatosi: {home_res.text}")

        # 4. Movies - List
        print("\n🎬 4. Kinolar ro'yxati (Movies List)...")
        movies_res = await client.get(f"{BASE_URL}/movies/")
        if movies_res.status_code == 200:
            movies = movies_res.json()
            print(f"✅ Jami kinolar: {len(movies)}")
            if movies:
                print(f"   Birinchi kino: {movies[0].get('title_uz', 'N/A')}")
        else:
            print(f"❌ Movies list xatosi: {movies_res.text}")

        # 5. Movies - Search
        print("\n🔍 5. Kino qidirish (Search)...")
        search_res = await client.get(f"{BASE_URL}/movies/search?query=test&lang=uz")
        if search_res.status_code == 200:
            results = search_res.json()
            print(f"✅ Qidiruv natijalari: {len(results)} ta kino")
        else:
            print(f"⚠️ Search xatosi: {search_res.status_code}")

        # 6. Movies - Get by ID
        print("\n📖 6. Kino ma'lumotlari (Get Movie by ID)...")
        # First get a movie ID from the list
        movies_list = await client.get(f"{BASE_URL}/movies/")
        if movies_list.status_code == 200 and movies_list.json():
            movie_id = movies_list.json()[0]['id']
            movie_res = await client.get(f"{BASE_URL}/movies/{movie_id}")
            if movie_res.status_code == 200:
                movie = movie_res.json()
                print(f"✅ Kino topildi: {movie.get('title_uz', 'N/A')}")
                print(f"   Reyting: {movie.get('rating', 0)}")
                print(f"   Ko'rishlar: {movie.get('views', 0)}")
            else:
                print(f"❌ Movie detail xatosi: {movie_res.text}")
        else:
            print("⚠️ Kinolar mavjud emas")

        # 7. Users - Favorites
        print("\n❤️ 7. Sevimlilar (Favorites)...")
        # First try to get a movie ID
        movies_list = await client.get(f"{BASE_URL}/movies/")
        if movies_list.status_code == 200 and movies_list.json():
            movie_id = movies_list.json()[0]['id']
            
            # Add to favorites
            add_fav = await client.post(f"{BASE_URL}/users/favorites/{movie_id}", headers=headers)
            if add_fav.status_code == 201:
                print("✅ Sevimlilarga qo'shildi")
            else:
                print(f"⚠️ Sevimlarga qo'shish: {add_fav.status_code}")
            
            # Get favorites
            get_fav = await client.get(f"{BASE_URL}/users/favorites", headers=headers)
            if get_fav.status_code == 200:
                favs = get_fav.json()
                print(f"✅ Sevimlilar ro'yxati: {len(favs)} ta kino")
            else:
                print(f"❌ Get favorites xatosi: {get_fav.text}")
        else:
            print("⚠️ Kinolar mavjud emas")

        # 8. Comments - List
        print("\n💬 8. Izohlar ro'yxati (Comments List)...")
        movies_list = await client.get(f"{BASE_URL}/movies/")
        if movies_list.status_code == 200 and movies_list.json():
            movie_id = movies_list.json()[0]['id']
            comments_res = await client.get(f"{BASE_URL}/comments/movie/{movie_id}")
            if comments_res.status_code == 200:
                comments = comments_res.json()
                print(f"✅ Izohlar: {len(comments)} ta")
            else:
                print(f"❌ Comments list xatosi: {comments_res.text}")
        else:
            print("⚠️ Kinolar mavjud emas")

        # 9. Comments - Create (with AI moderation)
        print("\n📝 9. Izoh yaratish (Create Comment)...")
        movies_list = await client.get(f"{BASE_URL}/movies/")
        if movies_list.status_code == 200 and movies_list.json():
            movie_id = movies_list.json()[0]['id']
            
            # Good comment
            good_comment = await client.post(
                f"{BASE_URL}/comments/movie/{movie_id}",
                json={"content": "Bu kino juda ajoyib! Tavsiya qilaman.", "rating": 9.0},
                headers=headers
            )
            if good_comment.status_code == 201:
                print("✅ Ijobiy izoh qabul qilindi")
            else:
                print(f"⚠️ Izoh qo'shish: {good_comment.status_code}")

            # Bad comment (spam test)
            bad_comment = await client.post(
                f"{BASE_URL}/comments/movie/{movie_id}",
                json={"content": "REKLAMA! WWW.SPAM.COM TEZ KIRING", "rating": 1.0},
                headers=headers
            )
            if bad_comment.status_code == 400:
                print("✅ AI spamni aniqladi va rad etdi")
            else:
                print(f"⚠️ Spam test: {bad_comment.status_code}")
        else:
            print("⚠️ Kinolar mavjud emas")

        # 10. Admin - Stats
        print("\n📊 10. Admin statistikasi (Admin Stats)...")
        stats_res = await client.get(f"{BASE_URL}/admin/stats/overview", headers=headers)
        if stats_res.status_code == 200:
            stats = stats_res.json()
            print(f"✅ Jami foydalanuvchilar: {stats['users']['total']}")
            print(f"✅ Yangi foydalanuvchilar (24h): {stats['users']['new_24h']}")
            print(f"📈 AI bugun {stats['ai_performance']['today_acquired']} ta foydalanuvchi jalb qildi")
            print(f"🤖 AI tavsiflar yaratdi: {stats['ai_performance']['today_descriptions']}")
        else:
            print(f"❌ Admin stats xatosi: {stats_res.text}")

        # 11. Admin - Users list
        print("\n👥 11. Foydalanuvchilar ro'yxati (Users List)...")
        users_res = await client.get(f"{BASE_URL}/admin/users", headers=headers)
        if users_res.status_code == 200:
            users = users_res.json()
            print(f"✅ Foydalanuvchilar: {len(users)} ta")
            if users:
                print(f"   Birinchi user: {users[0].get('email', 'N/A')}")
        else:
            print(f"❌ Users list xatosi: {users_res.text}")

        # 12. Admin - AI Trigger
        print("\n🤖 12. AI avtonom trigger (AI Autonomous)...")
        ai_res = await client.post(f"{BASE_URL}/admin/ai/trigger-autonomous", headers=headers)
        if ai_res.status_code == 200:
            print(f"✅ AI Master Mode: {ai_res.json().get('status')}")
        else:
            print(f"❌ AI trigger xatosi: {ai_res.text}")

        # 13. AI Chat Consultant
        print("\n💭 13. AI maslahatchi (AI Consultant)...")
        chat_res = await client.post(
            f"{BASE_URL}/discovery/chat",
            params={"query": "Yaxshi komediya kinolarini tavsiya bering"}
        )
        if chat_res.status_code == 200:
            response = chat_res.json()
            print(f"✅ AI javobi: {response.get('answer', 'N/A')[:100]}...")
        else:
            print(f"⚠️ AI chat: {chat_res.status_code}")

        # 14. Stream endpoint test (will fail without video files, but we test the endpoint)
        print("\n🎥 14. Video stream endpoint...")
        movies_list = await client.get(f"{BASE_URL}/movies/")
        if movies_list.status_code == 200 and movies_list.json():
            movie_id = movies_list.json()[0]['id']
            stream_res = await client.get(f"{BASE_URL}/stream/{movie_id}")
            # This will likely fail without actual video files
            if stream_res.status_code == 404:
                print("✅ Stream endpoint ishlayapti (video fayllari mavjud emas)")
            else:
                print(f"⚠️ Stream: {stream_res.status_code}")
        else:
            print("⚠️ Kinolar mavjud emas")

        print("\n" + "=" * 50)
        print("🏁 Test yakunlandi!")
        print("\n📋 API Xulosa:")
        print("🔐 Auth: Register, Login")
        print("🏠 Discovery: Home page, AI chat")
        print("🎬 Movies: List, Search, Get by ID, Get by code")
        print("🎥 Stream: Video streaming with range requests")
        print("❤️ Users: Favorites management")
        print("💬 Comments: Create, List with AI moderation")
        print("📊 Admin: Stats, Users list, AI management")
        print("🤖 AI: Content moderation, Auto-growth, Consultant")

if __name__ == "__main__":
    asyncio.run(test_all())