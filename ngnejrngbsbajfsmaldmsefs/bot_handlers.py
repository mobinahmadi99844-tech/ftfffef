import asyncio
import json
import re
from datetime import datetime
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import config
from database import db
from telegram_client import client_manager
from keyboards import keyboards

class BotHandlers:
    def __init__(self, bot_instance):
        self.bot = bot_instance
    
    # Admin management methods
    async def remove_admin_prompt(self, callback_query: CallbackQuery):
        """Prompt to remove admin"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "remove_admin"}
        text = """
➖ **حذف ادمین**

📝 لطفاً یوزر آیدی ادمینی که می‌خواهید حذف کنید را ارسال کنید:

💡 **نمونه:** `123456789`
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_remove_admin(self, message: Message):
        """Process remove admin request"""
        try:
            user_id = int(message.text.strip())
            
            if config.is_admin(user_id):
                config.remove_admin(user_id)
                await message.reply_text(
                    f"✅ ادمین `{user_id}` با موفقیت حذف شد",
                    reply_markup=keyboards.main_menu(),
                    
                )
            else:
                await message.reply_text(
                    f"❌ کاربر `{user_id}` ادمین نیست!",
                    reply_markup=keyboards.back_keyboard(),
                    
                )
                
        except ValueError:
            await message.reply_text(
                "❌ فرمت نادرست! لطفاً یوزر آیدی معتبر وارد کنید.",
                reply_markup=keyboards.back_keyboard()
            )
        
        self.bot.user_states.pop(message.from_user.id, None)
    
    async def add_admin_prompt(self, callback_query: CallbackQuery):
        """Prompt to add admin"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "add_admin"}
        text = """
➕ **افزودن ادمین جدید**

📝 لطفاً یوزر آیدی کاربر را ارسال کنید:

💡 **نمونه:** `123456789`

⏰ **اختیاری:** برای تنظیم مدت زمان ادمین بودن، پس از یوزر آیدی، تعداد روز را بنویسید:
**مثال:** `123456789 30` (30 روز)
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
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
        self.bot.user_states.pop(message.from_user.id, None)
    
    async def list_admins(self, callback_query: CallbackQuery):
        """List all admins"""
        admins = config.data.get("admins", [])
        
        if not admins:
            text = "👥 هیچ ادمینی یافت نشد!"
        else:
            text = "👥 **لیست ادمین‌ها:**\n\n"
            for i, admin in enumerate(admins, 1):
                if isinstance(admin, dict):
                    user_id = admin.get("user_id", "نامشخص")
                    added_date = admin.get("added_date", "-")[:10]
                    expires = admin.get("expires")
                    if expires:
                        expires_date = expires[:10]
                        text += f"{i}. `{user_id}` - تا {expires_date}\n"
                    else:
                        text += f"{i}. `{user_id}` - دائمی\n"
                else:
                    text += f"{i}. `{admin}` - دائمی\n"
        
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard(),
            
        )
    
    # Account management methods
    async def add_account_prompt(self, callback_query: CallbackQuery):
        """Prompt to add account using global API credentials"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "add_account", "step": "phone"}
        text = """
➕ **افزودن اکانت جدید**

📱 لطفاً شماره تلفن را ارسال کنید:

💡 **نمونه:** `+989123456789`

⚠️ ابتدا در تنظیمات، `API ID` و `API Hash` را تنظیم کنید.
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_add_account(self, message: Message):
        """Process add account request"""
        user_id = message.from_user.id
        state = self.bot.user_states.get(user_id, {})
        
        if state.get("step") == "phone":
            phone = message.text.strip()
            if not phone.startswith("+"):
                await message.reply_text(
                    "❌ شماره تلفن باید با + شروع شود!\n💡 مثال: +989123456789",
                    reply_markup=keyboards.back_keyboard()
                )
                return
            
            api_id, api_hash = config.get_api_credentials()
            if not api_id or not api_hash:
                await message.reply_text(
                    "❌ ابتدا `API ID` و `API Hash` را در تنظیمات ثبت کنید.",
                    reply_markup=keyboards.settings_menu(),
                    
                )
                self.bot.user_states.pop(user_id, None)
                return
            
            # Add account using global credentials
            config.add_account(phone, api_id, api_hash)
            await message.reply_text(
                f"✅ اکانت `{phone}` اضافه شد.\n"
                "برای فعال‌سازی، از 'دریافت کد' استفاده کنید.",
                reply_markup=keyboards.main_menu(),
                
            )
            self.bot.user_states.pop(user_id, None)
    
    async def remove_account_prompt(self, callback_query: CallbackQuery):
        """Show account selection for removal"""
        accounts = config.get_accounts()
        
        if not accounts:
            await callback_query.edit_message_text(
                "❌ هیچ اکانتی برای حذف یافت نشد!",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        text = "➖ **حذف اکانت**\n\n📱 اکانت مورد نظر را انتخاب کنید:"
        
        buttons = []
        for phone in accounts.keys():
            buttons.append([InlineKeyboardButton(
                f"🗑️ {phone}", 
                callback_data=f"remove_account_{phone}"
            )])
        
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="account_menu")])
        
        await callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            
        )
    
    # Reporting methods
    async def report_channel_prompt(self, callback_query: CallbackQuery):
        """Prompt for channel reporting"""
        accounts = config.get_accounts()
        
        if not accounts:
            await callback_query.edit_message_text(
                "❌ هیچ اکانتی برای ریپورت یافت نشد!\nابتدا اکانت اضافه کنید.",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        self.bot.user_states[callback_query.from_user.id] = {"action": "report_channel"}
        text = """
📢 **ریپورت کانال/گروه**

🔗 لطفاً لینک یا یوزرنیم کانال/گروه را ارسال کنید:

💡 **نمونه‌ها:**
• `https://t.me/channel_name`
• `@channel_name`
• `channel_name`
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_report_channel(self, message: Message):
        """Process channel report"""
        target = message.text.strip()
        accounts = config.get_accounts()
        
        results = []
        
        for phone in accounts.keys():
            try:
                success, msg = await client_manager.report_channel_or_group(phone, target)
                if success:
                    results.append(f"✅ {phone}: {msg}")
                else:
                    results.append(f"❌ {phone}: {msg}")
            except Exception as e:
                results.append(f"❌ {phone}: خطا - {str(e)}")
        
        result_text = f"📢 **نتیجه ریپورت {target}:**\n\n" + "\n".join(results)
        
        await message.reply_text(
            result_text,
            reply_markup=keyboards.main_menu(),
            
        )
        
        self.bot.user_states.pop(message.from_user.id, None)
    
    async def report_post_prompt(self, callback_query: CallbackQuery):
        """Prompt for post reporting"""
        accounts = config.get_accounts()
        
        if not accounts:
            await callback_query.edit_message_text(
                "❌ هیچ اکانتی برای ریپورت یافت نشد!\nابتدا اکانت اضافه کنید.",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        self.bot.user_states[callback_query.from_user.id] = {"action": "report_posts"}
        text = """
📝 **ریپورت پست‌ها**

🔗 لطفاً لینک‌های پست‌ها را پشت سر هم ارسال کنید:

💡 **نمونه:**
```
https://t.me/VoLtRaYn/5
https://t.me/VoLtRaYn/7
https://t.me/VoLtRaYn/8
```

📌 هر لینک در یک خط جداگانه باشد.
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )

    async def report_post_seq_prompt(self, callback_query: CallbackQuery):
        """Prompt for sequential post reporting"""
        accounts = config.get_accounts()
        if not accounts:
            await callback_query.edit_message_text(
                "❌ هیچ اکانتی برای ریپورت یافت نشد!\nابتدا اکانت اضافه کنید.",
                reply_markup=keyboards.back_keyboard()
            )
            return
        self.bot.user_states[callback_query.from_user.id] = {"action": "report_posts_seq", "step": "links"}
        text = """
⚡ **ریپورت متوالی پست‌ها**

🔗 لینک‌های پست‌ها را هر کدام در یک خط بفرست.
بعد از آن، فاصله زمانی (ثانیه) و تعداد تکرار را می‌پرسیم.

💡 نمونه:
```
https://t.me/VoLtRaYn/5
https://t.me/VoLtRaYn/7
https://t.me/VoLtRaYn/8
```
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_report_posts(self, message: Message):
        """Process post reports"""
        links = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
        accounts = config.get_accounts()
        
        if not links:
            await message.reply_text(
                "❌ هیچ لینکی یافت نشد!",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        results = []
        
        for phone in accounts.keys():
            try:
                success, msg = await client_manager.report_posts(phone, links)
                results.append(f"📱 **{phone}:**\n{msg}\n")
            except Exception as e:
                results.append(f"📱 **{phone}:** ❌ خطا - {str(e)}\n")
        
        result_text = f"📝 **نتیجه ریپورت {len(links)} پست:**\n\n" + "\n".join(results)
        
        await message.reply_text(
            result_text,
            reply_markup=keyboards.main_menu(),
            
        )
        
        self.bot.user_states.pop(message.from_user.id, None)

    async def process_report_posts_seq(self, message: Message):
        """Process sequential post reports with interval and repeats"""
        user_id = message.from_user.id
        state = self.bot.user_states.get(user_id, {})
        step = state.get("step", "links")
        
        if step == "links":
            links = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
            if not links:
                await message.reply_text("❌ هیچ لینکی یافت نشد!", reply_markup=keyboards.back_keyboard())
                return
            self.bot.user_states[user_id] = {"action": "report_posts_seq", "step": "interval", "links": links}
            await message.reply_text("⏱️ فاصله زمانی بین ریپورت‌ها (ثانیه) را بفرست:", reply_markup=keyboards.back_keyboard())
            return
        
        if step == "interval":
            try:
                interval = max(1, int(message.text.strip()))
            except ValueError:
                await message.reply_text("❌ عدد معتبر بفرست!", reply_markup=keyboards.back_keyboard())
                return
            self.bot.user_states[user_id]["interval"] = interval
            self.bot.user_states[user_id]["step"] = "repeats"
            await message.reply_text("🔁 تعداد تکرار برای هر لینک را بفرست (مثلاً 1 یا 2):", reply_markup=keyboards.back_keyboard())
            return
        
        if step == "repeats":
            try:
                repeats = max(1, int(message.text.strip()))
            except ValueError:
                await message.reply_text("❌ عدد معتبر بفرست!", reply_markup=keyboards.back_keyboard())
                return
            links = state["links"]
            interval = state["interval"]
            accounts = config.get_accounts()
            
            await message.reply_text(
                f"🚀 شروع ریپورت متوالی {len(links)} لینک با فاصله {interval}s و تکرار {repeats}.",
                reply_markup=keyboards.main_menu()
            )
            
            async def worker():
                for r in range(repeats):
                    for link in links:
                        results = []
                        for phone in accounts.keys():
                            try:
                                success, msg = await client_manager.report_posts(phone, [link])
                                results.append(f"{phone}: {'OK' if success else 'ERR'}")
                            except Exception as e:
                                results.append(f"{phone}: ERR {e}")
                        try:
                            await self.bot.bot.send_message(
                                user_id,
                                f"📣 نتیجه دور {r+1} لینک {link}:\n" + "\n".join(results)
                            )
                        except Exception:
                            pass
                        await asyncio.sleep(interval)
                try:
                    await self.bot.bot.send_message(user_id, "✅ ریپورت متوالی تمام شد.")
                except Exception:
                    pass
            
            asyncio.create_task(worker())
            self.bot.user_states.pop(user_id, None)
    
    # Join/Leave methods
    async def join_chat_prompt(self, callback_query: CallbackQuery):
        """Prompt for joining chat"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "join_chat"}
        text = """
➕ **جوین کانال/گروه**

🔗 لطفاً لینک یا یوزرنیم کانال/گروه را ارسال کنید:

💡 **نمونه‌ها:**
• `https://t.me/channel_name`
• `@channel_name`
• `channel_name`
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_join_chat(self, message: Message):
        """Process join chat request"""
        target = message.text.strip()
        accounts = config.get_accounts()
        
        results = []
        
        for phone in accounts.keys():
            try:
                success, msg = await client_manager.join_chat(phone, target)
                if success:
                    results.append(f"✅ {phone}: {msg}")
                else:
                    results.append(f"❌ {phone}: {msg}")
            except Exception as e:
                results.append(f"❌ {phone}: خطا - {str(e)}")
        
        result_text = f"➕ **نتیجه جوین {target}:**\n\n" + "\n".join(results)
        
        await message.reply_text(
            result_text,
            reply_markup=keyboards.main_menu(),
            
        )
        
        self.bot.user_states.pop(message.from_user.id, None)
    
    async def leave_chat_prompt(self, callback_query: CallbackQuery):
        """Prompt for leaving chat"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "leave_chat"}
        text = """
➖ **ترک کانال/گروه**

🔗 لطفاً لینک یا یوزرنیم کانال/گروه را ارسال کنید:

💡 **نمونه‌ها:**
• `https://t.me/channel_name`
• `@channel_name`
• `channel_name`
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_leave_chat(self, message: Message):
        """Process leave chat request"""
        target = message.text.strip()
        accounts = config.get_accounts()
        
        results = []
        
        for phone in accounts.keys():
            try:
                success, msg = await client_manager.leave_chat(phone, target)
                if success:
                    results.append(f"✅ {phone}: {msg}")
                else:
                    results.append(f"❌ {phone}: {msg}")
            except Exception as e:
                results.append(f"❌ {phone}: خطا - {str(e)}")
        
        result_text = f"➖ **نتیجه ترک {target}:**\n\n" + "\n".join(results)
        
        await message.reply_text(
            result_text,
            reply_markup=keyboards.main_menu(),
            
        )
        
        self.bot.user_states.pop(message.from_user.id, None)
    
    # Message sending
    async def send_message_prompt(self, callback_query: CallbackQuery):
        """Prompt for sending message"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "send_message", "step": "user_id"}
        text = """
💬 **ارسال پیام**

👤 لطفاً یوزر آیدی مقصد را ارسال کنید:

💡 **نمونه:** `123456789`
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def process_send_message(self, message: Message):
        """Process send message request"""
        user_id = message.from_user.id
        state = self.bot.user_states.get(user_id, {})
        
        if state.get("step") == "user_id":
            try:
                target_user_id = int(message.text.strip())
                self.bot.user_states[user_id] = {
                    "action": "send_message", 
                    "step": "message", 
                    "target_user_id": target_user_id
                }
                
                await message.reply_text(
                    "📝 حالا متن پیام را ارسال کنید:",
                    reply_markup=keyboards.back_keyboard()
                )
                
            except ValueError:
                await message.reply_text(
                    "❌ یوزر آیدی باید عدد باشد!",
                    reply_markup=keyboards.back_keyboard()
                )
                
        elif state.get("step") == "message":
            target_user_id = state["target_user_id"]
            message_text = message.text.strip()
            accounts = config.get_accounts()
            
            results = []
            
            for phone in accounts.keys():
                try:
                    success, msg = await client_manager.send_message(phone, target_user_id, message_text)
                    if success:
                        results.append(f"✅ {phone}: {msg}")
                    else:
                        results.append(f"❌ {phone}: {msg}")
                except Exception as e:
                    results.append(f"❌ {phone}: خطا - {str(e)}")
            
            result_text = f"💬 **نتیجه ارسال پیام به {target_user_id}:**\n\n" + "\n".join(results)
            
            await message.reply_text(
                result_text,
                reply_markup=keyboards.main_menu(),
                
            )
            
            self.bot.user_states.pop(user_id, None)
    
    # Phone code verification
    async def get_phone_code_prompt(self, callback_query: CallbackQuery):
        """Prompt for getting phone code"""
        accounts = config.get_accounts()
        
        if not accounts:
            await callback_query.edit_message_text(
                "❌ هیچ اکانتی یافت نشد!\nابتدا اکانت اضافه کنید.",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        text = "📞 **دریافت کد تایید**\n\n📱 اکانت مورد نظر را انتخاب کنید:"
        
        buttons = []
        for phone in accounts.keys():
            buttons.append([InlineKeyboardButton(
                f"📞 {phone}", 
                callback_data=f"get_code_{phone}"
            )])
        
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="account_menu")])
        
        await callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            
        )

    async def verify_code_prompt(self, callback_query: CallbackQuery):
        """Prompt for verifying phone code"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "verify_code"}
        text = """
✅ **تایید کد**

📱 لطفاً شماره تلفن و کد دریافتی را به صورت زیر ارسال کنید:


```
+989123456789 12345
```
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )

    # Settings: set API ID and API Hash
    async def set_api_id_prompt(self, callback_query: CallbackQuery):
        self.bot.user_states[callback_query.from_user.id] = {"action": "set_api_id"}
        await callback_query.edit_message_text(
            "🔑 API ID را ارسال کنید:",
            reply_markup=keyboards.back_keyboard()
        )

    async def set_api_hash_prompt(self, callback_query: CallbackQuery):
        self.bot.user_states[callback_query.from_user.id] = {"action": "set_api_hash"}
        await callback_query.edit_message_text(
            "🔐 API Hash را ارسال کنید:",
            reply_markup=keyboards.back_keyboard()
        )

    async def process_set_api_id(self, message: Message):
        try:
            api_id = int(message.text.strip())
            config.set_api_credentials(api_id, config.data.get("api_hash", ""))
            await message.reply_text(
                f"✅ API ID تنظیم شد: `{api_id}`",
                reply_markup=keyboards.settings_menu()
            )
        except ValueError:
            await message.reply_text(
                "❌ API ID باید عدد باشد!",
                reply_markup=keyboards.back_keyboard()
            )
        self.bot.user_states.pop(message.from_user.id, None)

    async def process_set_api_hash(self, message: Message):
        api_hash = message.text.strip()
        config.set_api_credentials(config.data.get("api_id", ""), api_hash)
        await message.reply_text(
            f"✅ API Hash تنظیم شد.",
            reply_markup=keyboards.settings_menu()
        )
        self.bot.user_states.pop(message.from_user.id, None)
    
    async def check_all_accounts_status(self, callback_query: CallbackQuery):
        """Check status of all accounts"""
        accounts = config.get_accounts()
        
        if not accounts:
            await callback_query.edit_message_text(
                "❌ هیچ اکانتی یافت نشد!",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        text = "📊 **بررسی وضعیت اکانت‌ها:**\n\n"
        
        for phone in accounts.keys():
            try:
                status, message = await client_manager.check_account_status(phone)
                status_emoji = {
                    "active": "✅",
                    "banned": "🚫",
                    "session_expired": "⏰",
                    "disconnected": "📵",
                    "error": "❌"
                }.get(status, "❓")
                
                text += f"{status_emoji} `{phone}`: {message}\n"
                
            except Exception as e:
                text += f"❌ `{phone}`: خطا - {str(e)}\n"
        
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
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
            reply_markup=keyboards.back_keyboard()
        )
    
    async def negative_reaction_prompt(self, callback_query: CallbackQuery):
        """Prompt for negative reaction"""
        self.bot.user_states[callback_query.from_user.id] = {"action": "negative_reaction", "step": "link"}
        text = """
👎 **ریکشن منفی**

🔗 لطفاً لینک پست را ارسال کنید:

💡 **نمونه:** `https://t.me/channel_name/123`
        """
        await callback_query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard()
        )
    
    async def handle_callback(self, callback_query: CallbackQuery):
        data = callback_query.data
        try:
            if data.startswith("get_code_"):
                phone = data.replace("get_code_", "")
                await self.process_get_phone_code_for_account(callback_query, phone)
            elif data.startswith("remove_account_"):
                phone = data.replace("remove_account_", "")
                accounts = config.get_accounts()
                if phone in accounts:
                    config.remove_account(phone)
                    await callback_query.edit_message_text(
                        f"🗑️ اکانت `{phone}` حذف شد.",
                        reply_markup=keyboards.account_menu()
                    )
                else:
                    await callback_query.edit_message_text(
                        "❌ اکانت یافت نشد!",
                        reply_markup=keyboards.back_keyboard()
                    )
        except Exception as e:
            await callback_query.answer(f"❌ خطا: {str(e)}", show_alert=True)
    
    async def process_get_phone_code_for_account(self, callback_query: CallbackQuery, phone: str):
        """Process getting phone code for specific account"""
        accounts = config.get_accounts()
        if phone not in accounts:
            await callback_query.edit_message_text(
                "❌ اکانت یافت نشد!",
                reply_markup=keyboards.back_keyboard()
            )
            return
        
        # Get global API credentials instead of account-specific ones
        api_id, api_hash = config.get_api_credentials()
        if not api_id or not api_hash:
            await callback_query.edit_message_text(
                "❌ لطفا ابتدا API ID و API Hash را در تنظیمات وارد کنید.",
                reply_markup=keyboards.settings_menu()
            )
            return
            
        try:
            success, msg, phone_code_hash = await client_manager.get_phone_code(
                phone, api_id, api_hash
            )
            if success and phone_code_hash:
                db.store_phone_code_hash(phone, phone_code_hash)
                text = f"✅ **کد ارسال شد**\n\n📱 **شماره:** `{phone}`\n📝 **پیام:** {msg}"
            else:
                text = f"❌ **خطا در ارسال کد**\n\n📱 **شماره:** `{phone}`\n📝 **خطا:** {msg}"
            await callback_query.edit_message_text(
                text,
                reply_markup=keyboards.back_keyboard()
            )
        except Exception as e:
            await callback_query.edit_message_text(
                f"❌ خطا: {str(e)}",
                reply_markup=keyboards.back_keyboard()
            )
    
    async def process_verify_code(self, message: Message):
        """Process code verification"""
        user_id = message.from_user.id
        state = self.bot.user_states.get(user_id, {})
        try:
            parts = message.text.strip().split()
            if len(parts) != 2:
                await message.reply_text(
                    "❌ فرمت نادرست! شماره و کد را به صورت زیر ارسال کنید:\n+989123456789 12345",
                    reply_markup=keyboards.back_keyboard()
                )
                return

            phone, code = parts
            # Get global API credentials
            api_id, api_hash = config.get_api_credentials()
            if not api_id or not api_hash:
                await message.reply_text(
                    "❌ لطفا ابتدا API ID و API Hash را در تنظیمات وارد کنید.",
                    reply_markup=keyboards.settings_menu()
                )
                return

            phone_code_hash = db.get_phone_code_hash(phone)
            if not phone_code_hash:
                await message.reply_text(
                    "❌ ابتدا از بخش 'دریافت کد' کد را دریافت کنید.",
                    reply_markup=keyboards.back_keyboard()
                )
                return

            success, msg = await client_manager.verify_phone_code(
                phone, code, phone_code_hash, api_id, api_hash
            )
            if success:
                await message.reply_text(
                    f"✅ **اکانت با موفقیت ثبت شد!**\n\n"
                    f"📱 **شماره:** `{phone}`\n"
                    f"📝 **وضعیت:** {msg}\n\n"
                    f"🎉 حالا می‌توانید از این اکانت برای ریپورت استفاده کنید.",
                    reply_markup=keyboards.main_menu()
                )
            else:
                await message.reply_text(
                    f"❌ **خطا در تایید کد**\n\n"
                    f"📱 **شماره:** `{phone}`\n"
                    f"📝 **خطا:** {msg}\n\n"
                    f"💡 **راهنمایی:** اگر کد منقضی شده، مجدداً از 'دریافت کد' استفاده کنید.",
                    reply_markup=keyboards.back_keyboard()
                )
        except Exception as e:
            await message.reply_text(
                f"❌ خطا: {str(e)}",
                reply_markup=keyboards.back_keyboard()
            )
        self.bot.user_states.pop(user_id, None)
