import httpx
import asyncio
import json

BASE_URL = "http://localhost:8085/api/v1"

async def test_all():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 Kompleks test boshlandi...\n")

        # 1. Login
        print("1. Autentifikatsiya tekshirilmoqda...")
        login_res = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": "vosejonova@gmail.com", "password": "azam_770"}
        )
        if login_res.status_code != 200:
            print(f"❌ Login xatosi: {login_res.text}")
            return
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login muvaffaqiyatli.\n")

        # 2. Discovery Home
        print("2. Discovery (Asosiy sahifa) tekshirilmoqda...")
        home_res = await client.get(f"{BASE_URL}/discovery/home")
        if home_res.status_code == 200:
            data = home_res.json()
            print(f"✅ Discovery ishlayapti. Kinolar: {len(data.get('trending', []))}, Reklamalar: {len(data.get('ads', []))}")
        else:
            print(f"❌ Discovery xatosi: {home_res.text}")
        print()

        # 3. AI Moderation & Comments
        print("3. AI Moderatsiya va Izohlar tekshirilmoqda...")
        # Good comment
        good_comment = await client.post(
            f"{BASE_URL}/comments/movie/1",
            json={"content": "Bu kino juda ajoyib ekan, hamma ko'rsin!", "rating": 9.5},
            headers=headers
        )
        if good_comment.status_code == 201:
            print("✅ Ijobiy izoh qabul qilindi.")
        else:
            print(f"⚠️ Ijobiy izohda xatolik (Kino ID=1 bo'lmasligi mumkin): {good_comment.status_code}")

        # Bad comment (Spam)
        bad_comment = await client.post(
            f"{BASE_URL}/comments/movie/1",
            json={"content": "REKLAMA! TEZ KIRING WWW.SPAM.COM", "rating": 1.0},
            headers=headers
        )
        if bad_comment.status_code == 400:
            print("✅ AI Spamni aniqladi va rad etdi.")
        else:
            print(f"⚠️ Spam moderatsiyadan o'tib ketdi yoki boshqa xato: {bad_comment.status_code}")
        print()

        # 4. AI Autonomous Trigger
        print("4. AI Avtonom menejmenti trigger qilinmoqda...")
        ai_res = await client.post(f"{BASE_URL}/admin/ai/trigger-autonomous", headers=headers)
        if ai_res.status_code == 200:
            print(f"✅ AI Master Mode muvaffaqiyatli bajarildi: {ai_res.json().get('status')}")
        else:
            print(f"❌ AI Trigger xatosi: {ai_res.text}")
        print()

        # 5. Admin Stats
        print("5. Admin statistikasi tekshirilmoqda...")
        stats_res = await client.get(f"{BASE_URL}/admin/stats/overview", headers=headers)
        if stats_res.status_code == 200:
            stats = stats_res.json()
            print(f"✅ Statistika: Jami foydalanuvchilar: {stats['users']['total']}")
            print(f"📈 AI bugun jami {stats['ai_performance']['today_acquired']} ta foydalanuvchi jalb qildi.")
        else:
            print(f"❌ Statistika xatosi: {stats_res.text}")
        print()

        print("🏁 Test yakunlandi.")

if __name__ == "__main__":
    asyncio.run(test_all())
