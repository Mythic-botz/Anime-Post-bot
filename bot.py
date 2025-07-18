import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
from dotenv import load_dotenv

# 🌐 Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456"))

# 📁 Load anime schedule from file
def load_schedule():
    try:
        with open("anime_schedule.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {day: [] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}

# 📝 Format post for the current day
def format_post():
    anime_schedule = load_schedule()
    now = datetime.now()
    day_name = now.strftime("%A").lower()  # e.g., "friday"
    day_display = now.strftime("%A").upper()
    day_number = now.day
    month_name = now.strftime("%b")

    post = f"""⟣━━━━━━━━━━━━━━━━━━━⟢    
📅 {day_display} • {day_number} {month_name}

『 Anime Release Guide | Hindi Dub 』
⟣━━━━━━━━━━━━━━━━━━━⟢

"""

    today_anime = anime_schedule.get(day_name, [])
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

# ✅ /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ You're not authorized to use this bot.")
        return

    await update.message.reply_text("👋 Welcome to the Anime Post Bot!\nUse /preview to test today’s post.")

# 📅 /preview command
async def preview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    message = format_post()
    await update.message.reply_text(message)

# 🚀 Run the bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("preview", preview_command))
    print("✅ Bot started. Use /start or /preview")
    app.run_polling()

if __name__ == "__main__":
    main()
