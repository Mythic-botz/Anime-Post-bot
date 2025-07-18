import os
import json
import asyncio
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Bot, Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

# 🌐 Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Example: '@yourchannel'
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))
SCHEDULE_FILE = "anime_schedule.json"

# 📁 Load or create schedule
def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "monday": [], "tuesday": [], "wednesday": [],
                "thursday": [], "friday": [], "saturday": [], "sunday": []
            }, f, indent=2, ensure_ascii=False)
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schedule(data):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 🧠 Format daily post
def format_post():
    schedule = load_schedule()
    now = datetime.now()
    day = now.strftime("%A").lower()
    day_human = now.strftime("%A")
    day_num = now.day
    month = now.strftime("%b")

    anime_list = schedule.get(day, [])
    msg = f"""⟣━━━━━━━━━━━━━━━━━━━⟢
📅 {day_human} • {day_num} {month}
『 Anime Release Guide | Hindi Dub 』
⟣━━━━━━━━━━━━━━━━━━━⟢

"""
    if anime_list:
        for anime in anime_list:
            msg += f"""⫷ {anime['name']} ⫸
┃🕒 Time: {anime['time']}
┃🎬 Episode: {anime['episode']}
┃📺 Platform: {anime['platform']}
┗━━━━━━━━━━━━━━━

"""
    else:
        msg += "🎌 No anime releases scheduled for today\n\n"

    msg += """📌 Daily Hindi Dub Updates Only On:
🔗 t.me/YOUR_CHANNEL

━━━━━━━━━━━━━━━━━━━
#HindiDubbedAnime  #AnimeInHindi
#DrStone #FairyTail #CrunchyrollHindi
━━━━━━━━━━━━━━━━━━━"""
    return msg

# 🚀 Bot command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return await update.message.reply_text("❌ You are not authorized.")
    await update.message.reply_text("🤖 Welcome to Anime Release Bot!")

async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    await update.message.reply_text(format_post())

async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=format_post())
        await update.message.reply_text("✅ Post sent to channel!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    schedule = load_schedule()
    text = "📅 **Current Anime Schedule:**\n\n"
    for day, items in schedule.items():
        text += f"**{day.upper()}**\n"
        if not items:
            text += "• No anime scheduled\n"
        for anime in items:
            text += f"• {anime['name']} at {anime['time']} - {anime['episode']}\n"
        text += "\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def add_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    await update.message.reply_text(
        "📝 Send details like this:\n\n"
        "`Day: friday\n"
        "Name: Fairy Tail\n"
        "Time: 8:30 PM\n"
        "Episode: S03 E01\n"
        "Platform: 🎬 YouTube [Muse India]`",
        parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    msg = update.message.text
    if all(x in msg for x in ["Day:", "Name:", "Time:", "Episode:", "Platform:"]):
        try:
            lines = msg.strip().splitlines()
            anime = {}
            for line in lines:
                key, val = line.split(":", 1)
                anime[key.strip().lower()] = val.strip()
            day = anime.pop("day").lower()
            data = load_schedule()
            if day not in data:
                return await update.message.reply_text("❌ Invalid day.")
            data[day].append(anime)
            save_schedule(data)
            await update.message.reply_text(f"✅ Added '{anime['name']}' to {day.title()}")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to add: {e}")

# 🔁 Daily auto post
async def daily_post(app: Application):
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            try:
                await app.bot.send_message(chat_id=CHANNEL_ID, text=format_post())
                print("✅ Scheduled post sent")
                await asyncio.sleep(60)  # Avoid double-send
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
        await asyncio.sleep(30)

# 🌐 Dummy HTTP server for Render
def run_http_server():
    port = int(os.getenv("PORT", 10000))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write("🤖 Anime Bot is Running (Render Compatible)".encode("utf-8"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🌐 HTTP server started at http://0.0.0.0:{port}")
    server.serve_forever()

# 🧠 Main bot setup
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(CommandHandler("add_anime", add_anime))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # 🔁 Start async post scheduler
    app.job_queue.run_once(lambda _: asyncio.create_task(daily_post(app)), when=1)

    print("🤖 Bot started & polling...")
    await app.run_polling()

# ▶️ Run bot and dummy server together
if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    asyncio.run(main())