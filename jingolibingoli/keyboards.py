from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Keyboards:
    @staticmethod
    def main_menu():
        """Main menu keyboard with glass-style emojis"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👥 مدیریت ادمین", callback_data="admin_menu"),
                InlineKeyboardButton("📱 مدیریت اکانت", callback_data="account_menu")
            ],
            [
                InlineKeyboardButton("📢 ریپورت کانال/گروه", callback_data="report_channel"),
                InlineKeyboardButton("📝 ریپورت پست", callback_data="report_post")
            ],
            [
                InlineKeyboardButton("⚡ ریپورت متوالی پست", callback_data="report_post_seq")
            ],
            [
                InlineKeyboardButton("🔗 جوین/ترک", callback_data="join_leave_menu"),
                InlineKeyboardButton("💬 ارسال پیام", callback_data="send_message")
            ],
            [
                InlineKeyboardButton("👎 ریکشن منفی", callback_data="negative_reaction"),
                InlineKeyboardButton("📊 وضعیت اکانت‌ها", callback_data="account_status")
            ],
            [
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings_menu"),
                InlineKeyboardButton("💾 بکاپ سشن", callback_data="backup_menu")
            ]
        ])
    
    @staticmethod
    def admin_menu():
        """Admin management menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ افزودن ادمین", callback_data="add_admin"),
                InlineKeyboardButton("➖ حذف ادمین", callback_data="remove_admin")
            ],
            [
                InlineKeyboardButton("📋 لیست ادمین‌ها", callback_data="list_admins"),
                InlineKeyboardButton("⏰ تنظیم مدت ادمین", callback_data="set_admin_duration")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]
        ])
    
    @staticmethod
    def account_menu():
        """Account management menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"),
                InlineKeyboardButton("➖ حذف اکانت", callback_data="remove_account")
            ],
            [
                InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data="list_accounts"),
                InlineKeyboardButton("🔍 بررسی وضعیت", callback_data="check_accounts")
            ],
            [
                InlineKeyboardButton("📞 دریافت کد", callback_data="get_phone_code"),
                InlineKeyboardButton("✅ تایید کد", callback_data="verify_code")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]
        ])
    
    @staticmethod
    def join_leave_menu():
        """Join/Leave menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ جوین کانال/گروه", callback_data="join_chat"),
                InlineKeyboardButton("➖ ترک کانال/گروه", callback_data="leave_chat")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]
        ])
    
    @staticmethod
    def settings_menu():
        """Settings menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔑 تنظیم API ID", callback_data="set_api_id"),
                InlineKeyboardButton("🔐 تنظیم API Hash", callback_data="set_api_hash")
            ],
            [
                InlineKeyboardButton("🤖 تنظیم Bot Token", callback_data="set_bot_token"),
                InlineKeyboardButton("📱 مشاهده شماره‌ها", callback_data="view_phones")
            ],
            [
                InlineKeyboardButton("🟢 شروع مانیتورینگ", callback_data="monitor_start"),
                InlineKeyboardButton("🔴 توقف مانیتورینگ", callback_data="monitor_stop")
            ],
            [
                InlineKeyboardButton("⏱️ تنظیم فاصله چک", callback_data="monitor_interval")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]
        ])
    
    @staticmethod
    def backup_menu():
        """Backup menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💾 بکاپ همه سشن‌ها", callback_data="backup_all_sessions"),
                InlineKeyboardButton("📥 بازیابی سشن", callback_data="restore_session")
            ],
            [
                InlineKeyboardButton("📤 دانلود بکاپ", callback_data="download_backup"),
                InlineKeyboardButton("📂 آپلود بکاپ", callback_data="upload_backup")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]
        ])
    
    @staticmethod
    def confirmation_keyboard(action_data: str):
        """Confirmation keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{action_data}"),
                InlineKeyboardButton("❌ لغو", callback_data="main_menu")
            ]
        ])
    
    @staticmethod
    def account_selection_keyboard(accounts: dict):
        """Account selection keyboard"""
        buttons = []
        for phone in accounts.keys():
            buttons.append([InlineKeyboardButton(f"📱 {phone}", callback_data=f"select_account_{phone}")])
        
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def back_keyboard():
        """Simple back button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ])

keyboards = Keyboards()
