import asyncio
import json
import os
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import schedule
import time
import threading
from flask import Flask
from threading import Thread
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Use environment variables for deployment
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@your_channel_username')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))
PORT = int(os.getenv('PORT', 5000))

# Flask app for health check
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Anime Release Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}, 200

class AnimeReleaseBot:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.bot = Bot(token=token)
        self.anime_schedule = {}
        
        # Validate configuration
        if not token or token == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ BOT_TOKEN not configured!")
            raise ValueError("BOT_TOKEN is required")
        
        if not channel_id or channel_id == '@your_channel_username':
            logger.error("❌ CHANNEL_ID not configured!")
            raise ValueError("CHANNEL_ID is required")
        
        logger.info(f"✅ Bot initialized with token: {token[:10]}...")
        logger.info(f"✅ Channel ID: {channel_id}")
        logger.info(f"✅ Admin User ID: {ADMIN_USER_ID}")
        
        self.load_schedule()
        
    def load_schedule(self):
        """Load anime schedule from file"""
        try:
            with open('anime_schedule.json', 'r', encoding='utf-8') as f:
                self.anime_schedule = json.load(f)
        except FileNotFoundError:
            # Default schedule structure
            self.anime_schedule = {
                "monday": [],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [
                    {
                        "name": "Yaiba : Samurai Legend",
                        "time": "~~~",
                        "episode": "S01 E08",
                        "platform": "📱 Amazon prime video [Anime Times]"
                    },
                    {
                        "name": "Fairy Tail",
                        "time": "8:30 PM",
                        "episode": "S03 E01",
                        "platform": "🎬 YouTube [Muse India]"
                    }
                ],
                "saturday": [],
                "sunday": []
            }
            self.save_schedule()
    
    def save_schedule(self):
        """Save anime schedule to file"""
        with open('anime_schedule.json', 'w', encoding='utf-8') as f:
            json.dump(self.anime_schedule, f, indent=2, ensure_ascii=False)
    
    def get_day_name(self, date_obj):
        """Get formatted day name"""
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        return days[date_obj.weekday()]
    
    def get_month_name(self, date_obj):
        """Get formatted month name"""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return months[date_obj.month - 1]
    
    def format_post(self, date_obj=None):
        """Format the anime release post"""
        if date_obj is None:
            date_obj = datetime.now()
        
        day_name = self.get_day_name(date_obj)
        day_num = date_obj.day
        month_name = self.get_month_name(date_obj)
        
        # Get today's anime schedule
        day_key = day_name.lower()
        today_anime = self.anime_schedule.get(day_key, [])
        
        # Header
        post = f"""⟣━━━━━━━━━━━━━━━━━━━⟢  
      📅 {day_name} • {day_num} {month_name}  
  『 Anime Release Guide | Hindi Dub 』  
⟣━━━━━━━━━━━━━━━━━━━⟢  

"""
        
        # Add anime entries
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
        
        # Footer
        post += """📌 Daily Hindi Dub Updates Only On:  
🔗 

━━━━━━━━━━━━━━━━━━━  
#HindiDubbedAnime  #AnimeInHindi  
#DrStone #DanDaDan #FairyTail #MuseIndia #CrunchyrollHindi  

━━━━━━━━━━━━━━━━━━━"""
        
        return post
    
    async def send_daily_post(self):
        """Send daily anime release post"""
        try:
            message = self.format_post()
            await self.bot.send_message(chat_id=self.channel_id, text=message)
            print(f"Daily post sent successfully at {datetime.now()}")
        except Exception as e:
            print(f"Error sending daily post: {e}")
    
    async def start_command(self, update, context):
        """Handle /start command"""
        logger.info(f"Start command received from user: {update.effective_user.id}")
        logger.info(f"Admin User ID: {ADMIN_USER_ID}")
        
        # Remove admin restriction for testing
        # if update.effective_user.id != ADMIN_USER_ID:
        #     await update.message.reply_text("❌ You're not authorized to use this bot.")
        #     return
        
        help_text = """🤖 Anime Release Bot Commands:

📅 Schedule Management:
/preview - Preview today's post
/post_now - Send post immediately
/schedule - View current schedule
/add_anime - Add new anime (interactive)

⚙️ Settings:
/get_chat_id - Get current chat ID
/status - Bot status

📝 Format for adding anime:
Day: friday
Name: Anime Name
Time: 8:30 PM
Episode: S01 E01
Platform: 🎬 YouTube [Channel Name]

💡 For Private Channels:
1. Add bot to your private channel as admin
2. Use /get_chat_id in the channel to get channel ID
3. Use that ID in your configuration

🔧 Your User ID: """ + str(update.effective_user.id) + """
🔧 Bot configured for Admin ID: """ + str(ADMIN_USER_ID)
        
        await update.message.reply_text(help_text)
    
    async def get_chat_id_command(self, update, context):
        """Get current chat ID - useful for private channels"""
        logger.info(f"Get chat ID command received from user: {update.effective_user.id}")
        
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        chat_title = update.effective_chat.title or "N/A"
        
        info_text = f"""📍 Chat Information:
        
Chat ID: {chat_id}
Chat Type: {chat_type}
Chat Title: {chat_title}

💡 Usage:
- For private channels, use this Chat ID in your configuration
- Copy the Chat ID exactly as shown (including the minus sign)
"""
        await update.message.reply_text(info_text)
    
    async def preview_command(self, update, context):
        """Preview today's post"""
        logger.info(f"Preview command received from user: {update.effective_user.id}")
        
        try:
            message = self.format_post()
            await update.message.reply_text(f"📋 Post Preview:\n\n{message}")
        except Exception as e:
            logger.error(f"Error in preview command: {e}")
            await update.message.reply_text(f"❌ Error generating preview: {str(e)}")
    
    async def post_now_command(self, update, context):
        """Send post immediately"""
        if update.effective_user.id != ADMIN_USER_ID:
            return
        
        await self.send_daily_post()
        await update.message.reply_text("✅ Post sent successfully!")
    
    async def schedule_command(self, update, context):
        """View current schedule"""
        if update.effective_user.id != ADMIN_USER_ID:
            return
        
        schedule_text = "📅 Current Anime Schedule:\n\n"
        
        for day, anime_list in self.anime_schedule.items():
            schedule_text += f"{day.upper()}:\n"
            if anime_list:
                for anime in anime_list:
                    schedule_text += f"• {anime['name']} - {anime['time']} - {anime['episode']}\n"
            else:
                schedule_text += "• No anime scheduled\n"
            schedule_text += "\n"
        
        await update.message.reply_text(schedule_text)
    
    async def add_anime_command(self, update, context):
        """Add new anime to schedule"""
        if update.effective_user.id != ADMIN_USER_ID:
            return
        
        await update.message.reply_text(
            "📝 Add New Anime\n\n"
            "Please send the anime details in this format:\n\n"
            "Day: friday\n"
            "Name: Anime Name\n"
            "Time: 8:30 PM\n"
            "Episode: S01 E01\n"
            "Platform: 🎬 YouTube [Channel Name]"
        )
    
    async def handle_message(self, update, context):
        """Handle text messages for adding anime"""
        if update.effective_user.id != ADMIN_USER_ID:
            return
        
        text = update.message.text
        
        # Check if message contains anime data
        if "Day:" in text and "Name:" in text:
            try:
                lines = text.strip().split('\n')
                anime_data = {}
                
                for line in lines:
                    if line.startswith("Day:"):
                        day = line.split("Day:")[1].strip().lower()
                    elif line.startswith("Name:"):
                        anime_data['name'] = line.split("Name:")[1].strip()
                    elif line.startswith("Time:"):
                        anime_data['time'] = line.split("Time:")[1].strip()
                    elif line.startswith("Episode:"):
                        anime_data['episode'] = line.split("Episode:")[1].strip()
                    elif line.startswith("Platform:"):
                        anime_data['platform'] = line.split("Platform:")[1].strip()
                
                # Add to schedule
                if day in self.anime_schedule and all(key in anime_data for key in ['name', 'time', 'episode', 'platform']):
                    self.anime_schedule[day].append(anime_data)
                    self.save_schedule()
                    await update.message.reply_text(f"✅ Added '{anime_data['name']}' to {day.upper()} schedule!")
                else:
                    await update.message.reply_text("❌ Invalid format. Please check your input.")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Error adding anime: {e}")
    
    def setup_scheduler(self):
        """Setup automatic posting schedule"""
        # Schedule daily post at 9:00 AM
        schedule.every().day.at("09:00").do(lambda: asyncio.run(self.send_daily_post()))
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def run(self):
        """Run the bot"""
        try:
            telegram_app = Application.builder().token(self.token).build()
            
            # Add handlers
            telegram_app.add_handler(CommandHandler("start", self.start_command))
            telegram_app.add_handler(CommandHandler("preview", self.preview_command))
            telegram_app.add_handler(CommandHandler("post_now", self.post_now_command))
            telegram_app.add_handler(CommandHandler("schedule", self.schedule_command))
            telegram_app.add_handler(CommandHandler("add_anime", self.add_anime_command))
            telegram_app.add_handler(CommandHandler("get_chat_id", self.get_chat_id_command))
            telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Setup scheduler
            self.setup_scheduler()
            
            logger.info("🤖 Anime Release Bot is running...")
            logger.info("📅 Daily posts scheduled for 9:00 AM")
            logger.info(f"🔧 Bot Token: {self.token[:10]}...")
            logger.info(f"🔧 Channel ID: {self.channel_id}")
            logger.info(f"🔧 Admin User ID: {ADMIN_USER_ID}")
            
            # Test bot connection
            asyncio.run(self.test_bot_connection())
            
            # For Render deployment
            if os.getenv('RENDER'):
                logger.info("🌐 Running on Render - Starting Flask health check server")
                # Run bot in a separate thread
                def run_bot():
                    telegram_app.run_polling(drop_pending_updates=True)
                
                bot_thread = Thread(target=run_bot, daemon=True)
                bot_thread.start()
                
                # Run Flask app for health check
                logger.info(f"🌐 Health check server running on port {PORT}")
                app.run(host='0.0.0.0', port=PORT)
            else:
                # For local development
                logger.info("💻 Running locally")
                telegram_app.run_polling(drop_pending_updates=True)
                
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            raise
    
    async def test_bot_connection(self):
        """Test bot connection"""
        try:
            me = await self.bot.get_me()
            logger.info(f"✅ Bot connected successfully: @{me.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

def run_flask_app():
    """Run Flask app for health check"""
    app.run(host='0.0.0.0', port=PORT)

# Main execution
if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Anime Release Bot...")
        
        # Validate environment variables
        if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ BOT_TOKEN environment variable is not set!")
            logger.error("Please set BOT_TOKEN in your Render environment variables")
            exit(1)
            
        if not CHANNEL_ID or CHANNEL_ID == '@your_channel_username':
            logger.error("❌ CHANNEL_ID environment variable is not set!")
            logger.error("Please set CHANNEL_ID in your Render environment variables")
            exit(1)
        
        # Create bot instance
        bot = AnimeReleaseBot(BOT_TOKEN, CHANNEL_ID)
        
        # Run the bot
        bot.run()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        exit(1)