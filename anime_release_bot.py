import asyncio
import json
import os
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import schedule
import time
import threading

# Configuration - Use environment variables for deployment
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')  # Get from @BotFather
CHANNEL_ID = os.getenv('CHANNEL_ID', '@your_channel_username')  # Your channel username or chat ID
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))  # Your user ID for admin commands

class AnimeReleaseBot:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.bot = Bot(token=token)
        self.anime_schedule = {}
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
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("❌ You're not authorized to use this bot.")
            return
        
        help_text = """🤖 **Anime Release Bot Commands:**

📅 **Schedule Management:**
/preview - Preview today's post
/post_now - Send post immediately
/schedule - View current schedule
/add_anime - Add new anime (interactive)

⚙️ **Settings:**
/set_channel - Set channel ID
/status - Bot status

📝 **Format for adding anime:**
Day: monday/tuesday/wednesday/thursday/friday/saturday/sunday
Name: Anime Name
Time: Release time
Episode: Episode info
Platform: Platform info
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def preview_command(self, update, context):
        """Preview today's post"""
        if update.effective_user.id != ADMIN_USER_ID:
            return
        
        message = self.format_post()
        await update.message.reply_text(f"📋 **Post Preview:**\n\n{message}", parse_mode='Markdown')
    
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
        
        schedule_text = "📅 **Current Anime Schedule:**\n\n"
        
        for day, anime_list in self.anime_schedule.items():
            schedule_text += f"**{day.upper()}:**\n"
            if anime_list:
                for anime in anime_list:
                    schedule_text += f"• {anime['name']} - {anime['time']} - {anime['episode']}\n"
            else:
                schedule_text += "• No anime scheduled\n"
            schedule_text += "\n"
        
        await update.message.reply_text(schedule_text, parse_mode='Markdown')
    
    async def add_anime_command(self, update, context):
        """Add new anime to schedule"""
        if update.effective_user.id != ADMIN_USER_ID:
            return
        
        await update.message.reply_text(
            "📝 **Add New Anime**\n\n"
            "Please send the anime details in this format:\n"
            "```\n"
            "Day: friday\n"
            "Name: Anime Name\n"
            "Time: 8:30 PM\n"
            "Episode: S01 E01\n"
            "Platform: 🎬 YouTube [Channel Name]\n"
            "```",
            parse_mode='Markdown'
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
        app = Application.builder().token(self.token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("preview", self.preview_command))
        app.add_handler(CommandHandler("post_now", self.post_now_command))
        app.add_handler(CommandHandler("schedule", self.schedule_command))
        app.add_handler(CommandHandler("add_anime", self.add_anime_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Setup scheduler
        self.setup_scheduler()
        
        print("🤖 Anime Release Bot is running...")
        print("📅 Daily posts scheduled for 9:00 AM")
        
        # Run the bot
        app.run_polling()

# Main execution
if __name__ == "__main__":
    # Create bot instance
    bot = AnimeReleaseBot(BOT_TOKEN, CHANNEL_ID)
    
    # Run the bot
    bot.run()
