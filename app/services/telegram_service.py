import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def post_movie_to_telegram(title: str, description: str, poster_url: str, code: str):
    """Sends professional ads to all configured Telegram channels."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHANNELS:
        logger.warning("Telegram configuration missing. Skipping post.")
        return False
    
    channels = settings.TELEGRAM_CHANNELS.split(",")
    
    # Professional message template
    message = f"🎬 *Yangi Kino qo'shildi!* 🎬\n\n"
    message += f"🍿 *Nomi:* {title}\n"
    message += f"📝 *Tavsif:* {description[:200]}...\n\n"
    message += f"🤖 *Bot kodi:* `{code}`\n\n"
    message += f"🔗 *Ko'rish uchun:* [Kinochilar.uz](https://kinochilar.uz/movie/{code})"
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    posted_count = 0
    async with httpx.AsyncClient(timeout=15.0) as client:
        for channel in channels:
            channel = channel.strip()
            payload = {
                "chat_id": channel,
                "photo": poster_url,
                "caption": message,
                "parse_mode": "Markdown"
            }
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Successfully posted to Telegram {channel}: {title}")
                    posted_count += 1
                else:
                    logger.error(f"Telegram API Error for {channel}: {response.text}")
            except Exception as e:
                logger.error(f"Telegram Connection Error for {channel}: {e}")
                
    return posted_count > 0

async def ai_shoutout_to_world(message_text: str):
    """
    Simulates AI advertising 'independently' to other forums/platforms.
    In a production app, this would use webhooks or social media APIs.
    """
    # Placeholder for broader AI-driven marketing (Twitter, Instagram, etc.)
    logger.info(f"AI independent marketing triggered: {message_text[:50]}...")
    return True
