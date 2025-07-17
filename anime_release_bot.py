import os
import json
import asyncio
import schedule
import time
import threading
from datetime import datetime
from flask import Flask
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from threading import Thread

# === Config ===
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@your_channel_username')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))
PORT = int(os.getenv('PORT', 5000))

# === Flask App ===
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Anime Release Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}, 200

# === Main Bot Class ===
class AnimeReleaseBot:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.bot = Bot(token=token)
        self.telegram_app = Application.builder().token(self.token).build()
        self.anime_schedule = {}
        self.load_schedule()

    def load_schedule(self):
        try:
            with open('anime_schedule.json', 'r', encoding='utf-8') as f:
                self.anime_schedule = json.load(f)
        except FileNotFoundError:
            self.anime_schedule = {
                "monday": [],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": [],
                "sunday": []
            }
            self.save_schedule()

    def save_schedule(self):
        with open('anime_schedule.json', 'w', encoding='utf-8') as f:
            json.dump(self.anime_schedule, f, indent=2, ensure_ascii=False)

    def get_day_name(self, date_obj):
        return ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"][date_obj.weekday()]

    def get_month_name(self, date_obj):
        return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][date_obj.month - 1]

    def format_post(self, date_obj=None):
        if date_obj is None:
            date_obj = datetime.now()
        day_name = self.get_day_name(date_obj)
        day_key = day_name.lower()
        today_anime = self.anime_schedule.get(day_key, [])

        post = f"""⟣━━━━━━━━━━━━━━━━━━━⟢  
      📅 {day_name} • {date_obj.day} {self.get_month_name(date_obj)}  
  『 Anime Release Guide | Hindi Dub 』  
⟣━━━━━━━━━━━━━━━━━━━⟢  

"""
        if today_anime:
            for anime in today_anime:
                post += f"""⫷ {anime['name']} ⫸  
┃🕒 Time: {anime['time']}  
┃🎬 Episode: {anime['episode']}  
┃📺 Platform: {anime['platform']}
┗━━━━━━━━━━━━━━━

"""
        else:
            post += "🎌 No anime releases scheduled for today\n\n"

        post += """📌 Daily Hindi Dub Updates Only On:  
🔗 

━━━━━━━━━━━━━━━━━━━  
#HindiDubbedAnime  #AnimeInHindi  
#DrStone #DanDaDan #FairyTail #MuseIndia #CrunchyrollHindi  

━━━━━━━━━━━━━━━━━━━"""

        return post

    async def send_daily_post(self):
        try:
            message = self.format_post()
            await self.bot.send_message(chat_id=self.channel_id, text=message)
            print(f"✅ Daily post sent at {datetime.now()}")
        except Exception as e:
            print(f"❌ Error sending post: {e}")

    # === Bot Commands ===
    async def start_command(self, update, context):
        if update.effective_user.id != ADMIN_USER_ID:
            return await update.message.reply_text("❌ You're not authorized to use this bot.")
        await update.message.reply_text("🤖 Anime Release Bot is running! Use /preview or /post_now.")

    async def get_chat_id_command(self, update, context):
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        title = update.effective_chat.title or "N/A"
        await update.message.reply_text(
            f"📍 **Chat Info:**\n\n"
            f"**ID:** `{chat_id}`\n**Type:** {chat_type}\n**Title:** {title}",
            parse_mode='Markdown'
        )

    async def preview_command(self, update, context):
        if update.effective_user.id != ADMIN_USER_ID:
            return
        message = self.format_post()
        await update.message.reply_text(f"📋 **Post Preview:**\n\n{message}", parse_mode='Markdown')

    async def post_now_command(self, update, context):
        if update.effective_user.id != ADMIN_USER_ID:
            return
        await self.send_daily_post()
        await update.message.reply_text("✅ Post sent!")

    async def schedule_command(self, update, context):
        if update.effective_user.id != ADMIN_USER_ID:
            return
        msg = "📅 **Schedule:**\n\n"
        for day, animes in self.anime_schedule.items():
            msg += f"**{day.upper()}**\n"
            msg += "\n".join([f"• {a['name']} - {a['time']} - {a['episode']}" for a in animes]) or "• No anime\n"
            msg += "\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def handle_message(self, update, context):
        if update.effective_user.id != ADMIN_USER_ID:
            return
        text = update.message.text
        if "Day:" in text and "Name:" in text:
            try:
                lines = text.strip().split('\n')
                anime = {}
                for line in lines:
                    if line.startswith("Day:"):
                        day = line.split("Day:")[1].strip().lower()
                    elif line.startswith("Name:"):
                        anime['name'] = line.split("Name:")[1].strip()
                    elif line.startswith("Time:"):
                        anime['time'] = line.split("Time:")[1].strip()
                    elif line.startswith("Episode:"):
                        anime['episode'] = line.split("Episode:")[1].strip()
                    elif line.startswith("Platform:"):
                        anime['platform'] = line.split("Platform:")[1].strip()
                if day in self.anime_schedule and all(k in anime for k in ['name', 'time', 'episode', 'platform']):
                    self.anime_schedule[day].append(anime)
                    self.save_schedule()
                    await update.message.reply_text(f"✅ Added '{anime['name']}' to {day.upper()}")
                else:
                    await update.message.reply_text("❌ Invalid format.")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

    def setup_scheduler(self):
        schedule.every().day.at("09:00").do(lambda: asyncio.run(self.send_daily_post()))
        Thread(target=self.run_scheduler_loop, daemon=True).start()

    def run_scheduler_loop(self):
        while True:
            schedule.run_pending()
            time.sleep(60)

    def run(self):
        # Add Telegram handlers
        self.telegram_app.add_handler(CommandHandler("start", self.start_command))
        self.telegram_app.add_handler(CommandHandler("preview", self.preview_command))
        self.telegram_app.add_handler(CommandHandler("post_now", self.post_now_command))
        self.telegram_app.add_handler(CommandHandler("schedule", self.schedule_command))
        self.telegram_app.add_handler(CommandHandler("get_chat_id", self.get_chat_id_command))
        self.telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Start scheduler
        self.setup_scheduler()

        print("🤖 Anime Release Bot is running...")
        print("📅 Daily posts scheduled for 9:00 AM")

        if os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU_APP_NAME'):
            print(f"🌐 Production mode on port {PORT}")
            def run_bot():
                asyncio.run(self.telegram_app.run_polling())
            Thread(target=run_bot, daemon=True).start()
            app.run(host='0.0.0.0', port=PORT)
        else:
            print("🏠 Development mode")
            self.telegram_app.run_polling()

# === Main Entry Point ===
if __name__ == "__main__":
    bot = AnimeReleaseBot(BOT_TOKEN, CHANNEL_ID)
    bot.run()