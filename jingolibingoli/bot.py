import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import config
from database import db
from telegram_client import client_manager
from keyboards import keyboards

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ReporterBot:
    def __init__(self):
        self.bot = None
        self.user_states = {}
        self.handlers = None
        self.monitor = None
        
    async def initialize(self):
        """Initialize the bot"""
        if not config.data.get("bot_token"):
            print("❌ Bot token not set! Please set it first.")
            return False
            
        self.bot = Client(
            "reporter_bot",
            bot_token=config.data["bot_token"],
            api_id=config.data.get("api_id", "23854674"),
            api_hash=config.data.get("api_hash", "c1eb832e3126bacdf74de936f9fe8e75")
        )
        
        # Initialize handlers and monitor
        from bot_handlers import BotHandlers
        from monitor import monitor
        self.handlers = BotHandlers(self)
        self.monitor = monitor
        self.monitor.bot = self
        
        # Register handlers
        self.register_handlers()
        
        # Start monitoring in background
        asyncio.create_task(self.monitor.start_monitoring())
        
        return True
    
    def register_handlers(self):
        """Register all bot handlers"""
        
        @self.bot.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            await self.handle_start(message)
        
        @self.bot.on_callback_query()
        async def callback_handler(client, callback_query: CallbackQuery):
            await self.handle_callback(callback_query)
        
        @self.bot.on_message(filters.text & ~filters.command(["start"]))
        async def text_handler(client, message: Message):
            await self.handle_text_message(message)
    
    async def handle_start(self, message: Message):
        """Handle /start command"""
        user_id = message.from_user.id
        
        # Add user to database
        db.add_user(
            user_id, 
            message.from_user.username, 
            message.from_user.first_name
        )
        
        # Check if user is admin
        if not config.is_admin(user_id):
            await message.reply_text(
                "❌ شما دسترسی به این ربات را ندارید.\n"
                "لطفاً با مدیر سیستم تماس بگیرید.",
                reply_markup=None
            )
            return
        
        # Send welcome message with glass-style design
        welcome_text = f"""
🔮 **سلام {message.from_user.first_name}!**

به ربات ریپورتر خوش آمدید 💎

✨ **امکانات موجود:**
• مدیریت ادمین‌ها و اکانت‌ها
• ریپورت کانال‌ها و پست‌ها
• جوین و ترک خودکار
• ارسال پیام و ریکشن
• نظارت بر وضعیت اکانت‌ها
• بکاپ و بازیابی سشن‌ها

🎯 برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        await message.reply_text(
            welcome_text,
            reply_markup=keyboards.main_menu(),
            
        )
    
    async def handle_callback(self, callback_query: CallbackQuery):
        """Handle callback queries"""
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Check admin access
        if not config.is_admin(user_id):
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
        
        # Update user activity
        db.update_user_activity(user_id)
        
        try:

            if data == "main_menu":
                await self.show_main_menu(callback_query)
            elif data.startswith("get_code_"):
                phone = data.replace("get_code_", "")
                await self.handlers.process_get_phone_code_for_account(callback_query, phone)
            elif data == "admin_menu":
                await self.show_admin_menu(callback_query)
            elif data == "account_menu":
                await self.show_account_menu(callback_query)
            elif data == "set_api_id":
                await self.handlers.set_api_id_prompt(callback_query)
            elif data == "set_api_hash":
                await self.handlers.set_api_hash_prompt(callback_query)
            elif data == "add_admin":
                await self.handlers.add_admin_prompt(callback_query)
            elif data == "remove_admin":
                await self.handlers.remove_admin_prompt(callback_query)
            elif data == "list_admins":
                await self.handlers.list_admins(callback_query)
            elif data == "add_account":
                await self.handlers.add_account_prompt(callback_query)
            elif data == "remove_account":
                await self.handlers.remove_account_prompt(callback_query)
            elif data == "list_accounts":
                await self.list_accounts(callback_query)
            elif data == "report_channel":
                await self.handlers.report_channel_prompt(callback_query)
            elif data == "report_post":
                await self.handlers.report_post_prompt(callback_query)
            elif data == "join_leave_menu":
                await self.show_join_leave_menu(callback_query)
            elif data == "join_chat":
                await self.handlers.join_chat_prompt(callback_query)
            elif data == "leave_chat":
                await self.handlers.leave_chat_prompt(callback_query)
            elif data == "send_message":
                await self.handlers.send_message_prompt(callback_query)
            elif data == "negative_reaction":
                await self.handlers.negative_reaction_prompt(callback_query)
            elif data == "account_status":
                await self.handlers.check_all_accounts_status(callback_query)
            elif data == "settings_menu":
                await self.show_settings_menu(callback_query)
            elif data == "monitor_start":
                await callback_query.edit_message_text(
                    "🟢 مانیتورینگ شروع شد.",
                    reply_markup=keyboards.settings_menu()
                )
                await self.monitor.start_monitoring()
            elif data == "monitor_stop":
                self.monitor.stop_monitoring()
                await callback_query.edit_message_text(
                    "🔴 مانیتورینگ متوقف شد.",
                    reply_markup=keyboards.settings_menu()
                )
            elif data == "monitor_interval":
                self.user_states[user_id] = {"action": "set_monitor_interval"}
                await callback_query.edit_message_text(
                    "⏱️ فاصله زمانی چک را به ثانیه ارسال کنید (حداقل 60):",
                    reply_markup=keyboards.back_keyboard()
                )
            elif data == "backup_menu":
                await self.show_backup_menu(callback_query)
            elif data == "get_phone_code":
                await self.handlers.get_phone_code_prompt(callback_query)
            elif data == "verify_code":
                await self.handlers.verify_code_prompt(callback_query)
            elif data == "view_phones":
                await self.handlers.view_phones(callback_query)
            elif data.startswith("select_account_"):
                phone = data.replace("select_account_", "")
                await self.handle_account_selection(callback_query, phone)
            else:
                # Handle other callbacks through handlers
                await self.handlers.handle_callback(callback_query)
            
            await callback_query.answer()
            
        except Exception as e:
            logging.error(f"Error handling callback {data}: {e}")
            await callback_query.answer("❌ خطا در پردازش درخواست!", show_alert=True)
    
    async def handle_text_message(self, message: Message):
        """Handle text messages based on user state"""
        user_id = message.from_user.id

        if not config.is_admin(user_id):
            return

        state = self.user_states.get(user_id, {})

        if state.get("action") == "add_admin":
            await self.handlers.process_add_admin(message)
        elif state.get("action") == "remove_admin":
            await self.handlers.process_remove_admin(message)
        elif state.get("action") == "add_account":
            await self.handlers.process_add_account(message)
        elif state.get("action") == "report_channel":
            await self.handlers.process_report_channel(message)
        elif state.get("action") == "report_posts":
            await self.handlers.process_report_posts(message)
        elif state.get("action") == "join_chat":
            await self.handlers.process_join_chat(message)
        elif state.get("action") == "leave_chat":
            await self.handlers.process_leave_chat(message)
        elif state.get("action") == "send_message":
            await self.handlers.process_send_message(message)
        elif state.get("action") == "get_phone_code":
            await self.handlers.process_get_phone_code(message)
        elif state.get("action") == "verify_code":
            await self.handlers.process_verify_code(message)
        elif state.get("action") == "set_api_id":
            await self.handlers.process_set_api_id(message)
        elif state.get("action") == "set_api_hash":
            await self.handlers.process_set_api_hash(message)

    # Menu display methods
    async def show_main_menu(self, callback_query: CallbackQuery):
        """Show main menu"""
        text = """
🔮 **پنل مدیریت ربات ریپورتر**

💎 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.main_menu(),
            
        )
    
    async def show_admin_menu(self, callback_query: CallbackQuery):
        """Show admin management menu"""
        text = """
👥 **مدیریت ادمین‌ها**

🔧 در این بخش می‌توانید ادمین‌های ربات را مدیریت کنید:
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.admin_menu(),
            
        )
    
    async def show_account_menu(self, callback_query: CallbackQuery):
        """Show account management menu"""
        accounts_count = len(config.get_accounts())
        text = f"""
📱 **مدیریت اکانت‌ها**

📊 تعداد اکانت‌های فعال: **{accounts_count}**

🔧 در این بخش می‌توانید اکانت‌های تلگرام را مدیریت کنید:
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.account_menu(),
            
        )
    
    async def show_join_leave_menu(self, callback_query: CallbackQuery):
        """Show join/leave menu"""
        text = """
🔗 **جوین و ترک کانال/گروه**

📌 در این بخش می‌توانید اکانت‌ها را به کانال‌ها و گروه‌ها جوین یا از آن‌ها خارج کنید:
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.join_leave_menu(),
            
        )
    
    async def show_settings_menu(self, callback_query: CallbackQuery):
        """Show settings menu"""
        text = """
⚙️ **تنظیمات سیستم**

🔧 در این بخش می‌توانید تنظیمات کلی ربات را مدیریت کنید:
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.settings_menu(),
            
        )
    
    async def show_backup_menu(self, callback_query: CallbackQuery):
        """Show backup menu"""
        text = """
💾 **مدیریت بکاپ**

🔒 در این بخش می‌توانید سشن‌های اکانت‌ها را بکاپ و بازیابی کنید:
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.backup_menu(),
            
        )
    
    # Admin management methods
    async def add_admin_prompt(self, callback_query: CallbackQuery):
        """Prompt to add admin"""
        self.user_states[callback_query.from_user.id] = {"action": "add_admin"}
        text = """
➕ **افزودن ادمین جدید**

📝 لطفاً یوزر آیدی کاربر را ارسال کنید:

💡 **نمونه:** `123456789`

⏰ **اختیاری:** برای تنظیم مدت زمان ادمین بودن، پس از یوزر آیدی، تعداد روز را بنویسید:
**مثال:** `123456789 30` (30 روز)
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard(),
            
        )
    
    async def process_add_admin(self, message: Message):
        """Process add admin request"""
        try:
            parts = message.text.strip().split()
            user_id = int(parts[0])
            duration_days = int(parts[1]) if len(parts) > 1 else None
            
            config.add_admin(user_id, duration_days)
            
            duration_text = f" برای {duration_days} روز" if duration_days else " بدون محدودیت زمانی"
            
            await message.reply_text(
                f"✅ کاربر `{user_id}` با موفقیت به عنوان ادمین اضافه شد{duration_text}",
                reply_markup=keyboards.main_menu(),
                
            )
            
        except (ValueError, IndexError):
            await message.reply_text(
                "❌ فرمت نادرست! لطفاً یوزر آیدی معتبر وارد کنید.",
                reply_markup=keyboards.back_keyboard()
            )
        
        # Clear user state
        self.user_states.pop(message.from_user.id, None)
    
    async def list_accounts(self, callback_query: CallbackQuery):
        """List all accounts"""
        accounts = config.get_accounts()
        
        if not accounts:
            text = "📱 هیچ اکانتی یافت نشد!"
        else:
            text = "📱 **لیست اکانت‌ها:**\n\n"
            for i, (phone, data) in enumerate(accounts.items(), 1):
                status = data.get("status", "unknown")
                status_emoji = "✅" if status == "active" else "❌"
                text += f"{i}. {status_emoji} `{phone}` - {status}\n"
        
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard(),
            
        )
    
    async def view_phones(self, callback_query: CallbackQuery):
        """View all phone numbers as text"""
        accounts = config.get_accounts()
        
        if not accounts:
            text = "📱 هیچ شماره‌ای یافت نشد!"
        else:
            phones = list(accounts.keys())
            text = "📱 **شماره‌های موجود:**\n\n"
            text += "\n".join([f"`{phone}`" for phone in phones])
            text += f"\n\n📊 **تعداد کل:** {len(phones)}"
        
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard(),
            
        )
    
    async def run(self):
        """Run the bot"""
        if await self.initialize():
            print("🚀 Bot initialized successfully!")

            # Start the bot
            await self.bot.start()

            # Keep the bot running until stopped
            await idle()

            # Stop the bot
            await self.bot.stop()
        else:
            print("❌ Failed to initialize bot!")

bot = ReporterBot()

if __name__ == "__main__":
    # Set bot token if not set
    if not config.data.get("bot_token"):
        token = input("Enter your bot token: ")
        config.set_bot_token(token)
    
    # Set API credentials if not set
    if not config.data.get("api_id") or not config.data.get("api_hash"):
        api_id = input("Enter your API ID: ")
        api_hash = input("Enter your API Hash: ")
        config.set_api_credentials(api_id, api_hash)
    
    # Add first admin if no admins exist
    if not config.data.get("admins"):
        admin_id = input("Enter first admin user ID: ")
        config.add_admin({"user_id": int(admin_id)})
        print(f"✅ Added {admin_id} as first admin")
    
    # Run the bot
    
    asyncio.run(bot.run())
