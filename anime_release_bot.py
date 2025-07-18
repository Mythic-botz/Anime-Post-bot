#!/usr/bin/env python3
"""
Anime Release Bot for Telegram using Pyrogram
A bot that automatically posts daily anime release schedules to a Telegram channel.
"""

import asyncio
import json
import os
import logging
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Use environment variables for deployment
API_ID = int(os.getenv('API_ID', '0'))  # Get from my.telegram.org
API_HASH = os.getenv('API_HASH', 'your_api_hash_here')  # Get from my.telegram.org
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')  # Get from @BotFather
CHANNEL_ID = os.getenv('CHANNEL_ID', '@your_channel_username')  # Your channel username or chat ID
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))  # Your user ID for admin commands

class AnimeReleaseBot:
    def __init__(self, api_id: int, api_hash: str, bot_token: str, channel_id: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.anime_schedule = {}
        self.adding_anime = False
        self.load_schedule()
        
        # Initialize Pyrogram client
        self.app = Client(
            "anime_bot",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token
        )
        
        # Register handlers
        self.register_handlers()
        
    def load_schedule(self) -> None:
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
            logger.info("Created default anime schedule")

    def save_schedule(self) -> None:
        """Save anime schedule to file"""
        try:
            with open('anime_schedule.json', 'w', encoding='utf-8') as f:
                json.dump(self.anime_schedule, f, indent=2, ensure_ascii=False)
            logger.info("Anime schedule saved successfully")
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")

    def get_day_name(self, date_obj: datetime) -> str:
        """Get formatted day name"""
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        return days[date_obj.weekday()]

    def get_month_name(self, date_obj: datetime) -> str:
        """Get formatted month name"""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return months[date_obj.month - 1]

    def format_post(self, date_obj: Optional[datetime] = None) -> str:
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

    async def send_daily_post(self) -> None:
        """Send daily anime release post"""
        try:
            message = self.format_post()
            await self.app.send_message(chat_id=self.channel_id, text=message)
            logger.info(f"Daily post sent successfully at {datetime.now()}")
        except Exception as e:
            logger.error(f"Error sending daily post: {e}")

    def register_handlers(self) -> None:
        """Register all message handlers"""
        
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            help_text = """🤖 **Anime Release Bot Commands:**

📅 Schedule Management:
/preview - Preview today's post
/post_now - Send post immediately
/schedule - View current schedule
/add_anime - Add new anime (interactive)
/remove_anime - Remove anime from schedule

⚙️ Settings:
/status - Bot status
/test - Test bot functionality

📝 Format for adding anime:
Day: monday/tuesday/wednesday/thursday/friday/saturday/sunday
Name: Anime Name
Time: Release time
Episode: Episode info
Platform: Platform info
"""
            await message.reply(help_text)

        @self.app.on_message(filters.command("preview") & filters.private)
        async def preview_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            post_message = self.format_post()
            await message.reply(f"📋 **Post Preview:**\n\n{post_message}")

        @self.app.on_message(filters.command("post_now") & filters.private)
        async def post_now_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            await self.send_daily_post()
            await message.reply("✅ Post sent successfully!")

        @self.app.on_message(filters.command("schedule") & filters.private)
        async def schedule_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            schedule_text = "📅 **Current Anime Schedule:**\n\n"
            
            for day, anime_list in self.anime_schedule.items():
                schedule_text += f"**{day.upper()}:**\n"
                if anime_list:
                    for i, anime in enumerate(anime_list, 1):
                        schedule_text += f"{i}. {anime['name']} - {anime['time']} - {anime['episode']}\n"
                else:
                    schedule_text += "• No anime scheduled\n"
                schedule_text += "\n"
            
            await message.reply(schedule_text)

        @self.app.on_message(filters.command("add_anime") & filters.private)
        async def add_anime_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            self.adding_anime = True
            await message.reply(
                "📝 **Add New Anime**\n\n"
                "Please send the anime details in this format:\n"
                "```\n"
                "Day: friday\n"
                "Name: Anime Name\n"
                "Time: 8:30 PM\n"
                "Episode: S01 E01\n"
                "Platform: 🎬 YouTube [Channel Name]\n"
                "```\n\n"
                "Send /cancel to cancel adding anime."
            )

        @self.app.on_message(filters.command("remove_anime") & filters.private)
        async def remove_anime_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            await message.reply(
                "🗑️ **Remove Anime**\n\n"
                "Send the anime removal details in this format:\n"
                "```\n"
                "Day: friday\n"
                "Name: Anime Name\n"
                "```"
            )

        @self.app.on_message(filters.command("status") & filters.private)
        async def status_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            status_text = f"""🤖 **Bot Status**

🔄 Status: Running
📅 Today: {datetime.now().strftime('%A, %B %d, %Y')}
🕒 Time: {datetime.now().strftime('%H:%M:%S')}
📺 Channel: {self.channel_id}
🆔 Admin: {ADMIN_USER_ID}

📊 **Schedule Summary:**
"""
            
            total_anime = sum(len(anime_list) for anime_list in self.anime_schedule.values())
            status_text += f"Total anime scheduled: {total_anime}\n"
            
            for day, anime_list in self.anime_schedule.items():
                status_text += f"• {day.capitalize()}: {len(anime_list)} anime\n"

            await message.reply(status_text)

        @self.app.on_message(filters.command("test") & filters.private)
        async def test_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                await message.reply("❌ You're not authorized to use this bot.")
                return

            try:
                # Test channel access
                await self.app.get_chat(self.channel_id)
                await message.reply("✅ Bot is working correctly!\n\n"
                                  "✓ Channel access: OK\n"
                                  "✓ Bot token: Valid\n"
                                  "✓ Admin access: Verified")
            except Exception as e:
                await message.reply(f"❌ Test failed: {str(e)}")

        @self.app.on_message(filters.command("cancel") & filters.private)
        async def cancel_command(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                return

            self.adding_anime = False
            await message.reply("❌ Operation cancelled.")

        @self.app.on_message(filters.text & filters.private & ~filters.command)
        async def handle_text_message(client, message: Message):
            if message.from_user.id != ADMIN_USER_ID:
                return

            text = message.text
            
            # Handle anime removal
            if "Day:" in text and "Name:" in text and "Time:" not in text:
                await self.handle_remove_anime(message, text)
                return
            
            # Handle anime addition
            if "Day:" in text and "Name:" in text and "Time:" in text:
                await self.handle_add_anime(message, text)
                return

    async def handle_add_anime(self, message: Message, text: str) -> None:
        """Handle adding anime to schedule"""
        try:
            lines = text.strip().split('\n')
            anime_data = {}
            day = None
            
            for line in lines:
                line = line.strip()
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
            
            # Validate input
            if day not in self.anime_schedule:
                await message.reply("❌ Invalid day. Use: monday, tuesday, wednesday, thursday, friday, saturday, sunday")
                return
            
            required_fields = ['name', 'time', 'episode', 'platform']
            if not all(field in anime_data for field in required_fields):
                await message.reply("❌ Missing required fields. Please include Name, Time, Episode, and Platform.")
                return
            
            # Add to schedule
            self.anime_schedule[day].append(anime_data)
            self.save_schedule()
            self.adding_anime = False
            await message.reply(f"✅ Added '{anime_data['name']}' to {day.upper()} schedule!")
            
        except Exception as e:
            logger.error(f"Error adding anime: {e}")
            await message.reply(f"❌ Error adding anime: {str(e)}")

    async def handle_remove_anime(self, message: Message, text: str) -> None:
        """Handle removing anime from schedule"""
        try:
            lines = text.strip().split('\n')
            day = None
            anime_name = None
            
            for line in lines:
                line = line.strip()
                if line.startswith("Day:"):
                    day = line.split("Day:")[1].strip().lower()
                elif line.startswith("Name:"):
                    anime_name = line.split("Name:")[1].strip()
            
            if not day or not anime_name:
                await message.reply("❌ Please provide both Day and Name.")
                return
            
            if day not in self.anime_schedule:
                await message.reply("❌ Invalid day.")
                return
            
            # Find and remove anime
            anime_list = self.anime_schedule[day]
            for i, anime in enumerate(anime_list):
                if anime['name'].lower() == anime_name.lower():
                    removed_anime = anime_list.pop(i)
                    self.save_schedule()
                    await message.reply(f"✅ Removed '{removed_anime['name']}' from {day.upper()} schedule!")
                    return
            
            await message.reply(f"❌ Anime '{anime_name}' not found in {day.upper()} schedule.")
            
        except Exception as e:
            logger.error(f"Error removing anime: {e}")
            await message.reply(f"❌ Error removing anime: {str(e)}")

    def setup_scheduler(self) -> None:
        """Setup automatic posting schedule"""
        # Schedule daily post at 9:00 AM
        schedule.every().day.at("09:00").do(self.send_daily_post_sync)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                asyncio.sleep(60)
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Scheduler started - Daily posts at 9:00 AM")

    def send_daily_post_sync(self) -> None:
        """Sync wrapper for daily post (for scheduler)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_daily_post())
            loop.close()
        except Exception as e:
            logger.error(f"Error in scheduled post: {e}")

    async def run(self) -> None:
        """Run the bot"""
        try:
            # Setup scheduler
            self.setup_scheduler()
            
            logger.info("🤖 Anime Release Bot is starting...")
            logger.info("📅 Daily posts scheduled for 9:00 AM")
            
            # Start the bot
            await self.app.start()
            logger.info("✅ Bot started successfully!")
            
            # Keep the bot running
            await asyncio.sleep(float('inf'))
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            await self.app.stop()

def main():
    """Main function"""
    # Validate environment variables
    if API_ID == 0:
        logger.error("❌ Please set API_ID environment variable")
        return
    
    if API_HASH == 'your_api_hash_here':
        logger.error("❌ Please set API_HASH environment variable")
        return
    
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ Please set BOT_TOKEN environment variable")
        return
    
    if CHANNEL_ID == '@your_channel_username':
        logger.error("❌ Please set CHANNEL_ID environment variable")
        return
    
    if ADMIN_USER_ID == 123456789:
        logger.error("❌ Please set ADMIN_USER_ID environment variable")
        return

    # Create and run bot
    try:
        bot = AnimeReleaseBot(API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID)
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
