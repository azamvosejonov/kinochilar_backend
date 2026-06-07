import httpx
import logging
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)

# User provided Qwen Key
AI_TOKEN = "sk-ws-H.IHDYEX.9Uq5.MEYCIQDIeLEv8Wq5goED9Q6zs46PT4cfyFdYPrsFdI3iGSmzLgIhAMNQeOdLsmQo50GTFDGzQ4lCwaoo0RUtIchE3bNn9E7h"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" # Standard OpenAI-compatible path for Qwen

async def generate_movie_description(title: str, actors: str = "", lang: str = "uz"):
    """Uses Qwen AI to generate a creative movie description."""
    prompt = f"Yaqindagina chiqqan '{title}' kinosi uchun juda qiziqarli va jalb qiluvchi tavsif yozib ber."
    if lang == "ru":
        prompt = f"Напиши очень интересное и захватывающее описание для фильма '{title}'."
    
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "Sen kino sayti uchun professional marketolog va kopirayterisan."},
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {AI_TOKEN}", "Content-Type": "application/json"},
                json=payload
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"AI Error: {response.text}")
                return None
        except Exception as e:
            logger.error(f"AI Connection Error: {e}")
            return None

async def suggest_marketing_strategy():
    """AI suggests how to bring more users today."""
    prompt = "Bugun kino saytimizga ko'proq foydalanuvchi jalb qilish uchun 3 ta kreativ marketing g'oyasini ber. Qisqa va lo'nda bo'lsin."
    
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "Sen growth hacker va marketing bo'yicha mutaxassis san."},
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {AI_TOKEN}", "Content-Type": "application/json"},
                json=payload
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return "Telegram kanallarda ko'proq kinosilkalarni ulashish tavsiya etiladi."
        except:
            return "Marketing xizmati vaqtincha mavjud emas."

async def ai_cinema_assistant(query: str, available_movies: List[dict]):
    """
    Acts as a personal movie consultant.
    Takes user's query and a list of available movies to give a curated suggestion.
    """
    movie_list_str = "\n".join([f"- ID: {m['id']}, Nomi: {m['title']}, Janr: {m['genres']}" for m in available_movies])
    
    prompt = f"""
    Foydalanuvchi so'rovi: "{query}"
    
    Bazadagi mavjud kinolar:
    {movie_list_str}
    
    Sening vazifang:
    1. Foydalanuvchiga juda samimiy va professional javob ber.
    2. Yuqoridagi ro'yxatdan eng mos keladigan 1-3 ta kinoni tavsiya qil.
    3. Agar mos kino bo'lmasa, umumiy tavsiya ber.
    4. Javobingni faqat o'zbek tilida yoz.
    """
    
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "Sen Kinochilar.uz saytining aqlli yordamchisisan."},
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {AI_TOKEN}"},
                json=payload
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return "Hozirda yordam bera olmayman, birozdan keyin urinib ko'ring."
        except:
            return "Bog'lanishda xatolik yuz berdi."

async def moderate_comment(content: str):
    """Checks if a comment is toxic or spam."""
    prompt = f"Ushbu izohni odob-axloq qoidalariga tekshir: '{content}'. Agar u haqoratli, reklama yoki juda yomon bo'lsa faqat 'REJECT' so'zini qaytar, aks holda 'APPROVE' so'zini qaytar."
    
    payload = {
        "model": "qwen-plus",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/chat/completions", headers={"Authorization": f"Bearer {AI_TOKEN}"}, json=payload)
            result = response.json()["choices"][0]["message"]["content"]
            return "APPROVE" in result.upper()
        except:
            return True # Default to approve if AI is down

