import asyncio
import logging
from datetime import datetime, timedelta
from config import config
from database import db
from telegram_client import client_manager

class AccountMonitor:
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.monitoring = False
        self.check_interval = 300  # 5 minutes
        self._task = None
        
    async def start_monitoring(self):
        """Start monitoring accounts"""
        if self.monitoring:
            return
        self.monitoring = True
        logging.info("Account monitoring started")
        
        async def _loop():
            while self.monitoring:
                try:
                    await self.check_all_accounts()
                    await asyncio.sleep(self.check_interval)
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        self._task = asyncio.create_task(_loop())
    
    def stop_monitoring(self):
        """Stop monitoring accounts"""
        self.monitoring = False
        logging.info("Account monitoring stopped")
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    def is_running(self) -> bool:
        return self.monitoring

    def set_interval(self, seconds: int):
        self.check_interval = max(60, int(seconds))
    
    async def check_all_accounts(self):
        """Check status of all accounts"""
        accounts = config.get_accounts()
        
        for phone, account_data in accounts.items():
            try:
                await self.check_account(phone, account_data)
            except Exception as e:
                logging.error(f"Error checking account {phone}: {e}")
    
    async def check_account(self, phone: str, account_data: dict):
        """Check individual account status"""
        try:
            # Get current status from database
            current_status = db.get_account_status(phone)
            previous_status = current_status.get("status") if current_status else "unknown"
            
            # Check account status
            new_status, message = await client_manager.check_account_status(phone)
            
            # If status changed, notify admins
            if new_status != previous_status:
                await self.notify_status_change(phone, previous_status, new_status, message)
                
                # Update account status in config
                config.update_account_status(phone, new_status)
            
            # Update database
            db.update_account_status(phone, new_status, message)
            
        except Exception as e:
            logging.error(f"Error checking account {phone}: {e}")
            db.update_account_status(phone, "error", str(e))
    
    async def notify_status_change(self, phone: str, old_status: str, new_status: str, message: str):
        """Notify admins about status change"""
        if not self.bot:
            return
        
        # Get status emojis
        status_emojis = {
            "active": "✅",
            "banned": "🚫",
            "session_expired": "⏰",
            "disconnected": "📵",
            "frozen": "🧊",
            "error": "❌",
            "unknown": "❓"
        }
        
        old_emoji = status_emojis.get(old_status, "❓")
        new_emoji = status_emojis.get(new_status, "❓")
        
        # Create notification message
        notification = f"""
🔔 **تغییر وضعیت اکانت**

📱 **شماره:** `{phone}`
{old_emoji} **وضعیت قبلی:** {old_status}
{new_emoji} **وضعیت جدید:** {new_status}

📝 **جزئیات:** {message}
🕐 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send to all admins (support both int and dict entries)
        admins = config.data.get("admins", [])
        for admin in admins:
            try:
                # admin can be either an int user_id or a dict with "user_id"
                admin_id = admin["user_id"] if isinstance(admin, dict) else admin
                if not isinstance(admin_id, int):
                    # try to coerce strings to int if possible
                    try:
                        admin_id = int(admin_id)
                    except Exception:
                        continue

                if config.is_admin(admin_id):
                    await self.bot.bot.send_message(
                        admin_id,
                        notification,
                        parse_mode="markdown"
                    )
            except Exception as e:
                try:
                    logging.error(f"Error sending notification to admin {admin_id}: {e}")
                except Exception:
                    logging.error(f"Error sending notification to an admin entry: {e}")
    
    async def check_session_validity(self, phone: str):
        """Check if session is still valid"""
        try:
            client = await client_manager.get_client(phone)
            if not client:
                return False, "Client not found"
            
            # Try to get self info
            me = await client.get_me()
            if me:
                return True, "Session is valid"
            else:
                return False, "Cannot get user info"
                
        except Exception as e:
            return False, f"Session error: {str(e)}"
    
    async def auto_reconnect_accounts(self):
        """Try to reconnect disconnected accounts"""
        accounts = config.get_accounts()
        
        for phone, account_data in accounts.items():
            try:
                status = db.get_account_status(phone)
                if status and status.get("status") in ["disconnected", "session_expired"]:
                    await self.try_reconnect_account(phone, account_data)
            except Exception as e:
                logging.error(f"Error auto-reconnecting {phone}: {e}")
    
    async def try_reconnect_account(self, phone: str, account_data: dict):
        """Try to reconnect a specific account"""
        try:
            # Get session string from database
            session_string = db.get_session(phone)
            if not session_string:
                logging.warning(f"No session string found for {phone}")
                return False
            
            # Try to create client with existing session
            success, message = await client_manager.create_client(
                phone,
                account_data["api_id"],
                account_data["api_hash"],
                session_string
            )
            
            if success:
                logging.info(f"Successfully reconnected {phone}")
                await self.notify_status_change(phone, "disconnected", "active", "Auto-reconnected")
                return True
            else:
                logging.warning(f"Failed to reconnect {phone}: {message}")
                return False
                
        except Exception as e:
            logging.error(f"Error reconnecting {phone}: {e}")
            return False

monitor = AccountMonitor()
