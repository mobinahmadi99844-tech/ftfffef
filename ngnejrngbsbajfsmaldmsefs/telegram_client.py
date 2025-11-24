import asyncio
import logging
from pyrogram import Client, errors, raw
from pyrogram.types import Message
from typing import Dict, List, Optional
from config import config
from database import db
import re

class TelegramClientManager:
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self.active_sessions = {}
        
    async def create_client(self, phone: str, api_id: int, api_hash: str, session_string: str = None):
        """Create and start a new Telegram client"""
        try:
            if session_string:
                client = Client(
                    name=f"session_{phone}",
                    api_id=int(api_id),
                    api_hash=str(api_hash),
                    session_string=session_string
                )
            else:
                client = Client(
                    name=f"session_{phone}",
                    api_id=int(api_id),
                    api_hash=str(api_hash),
                    phone_number=phone
                )
            
            await client.start()
            self.clients[phone] = client
            
            # Store session string
            session_str = await client.export_session_string()
            db.store_session(phone, session_str)
            
            # Update account status
            db.update_account_status(phone, "active", "Client connected successfully")
            
            return True, "Client created successfully"
            
        except errors.SessionPasswordNeeded:
            return False, "Two-factor authentication required"
        except errors.PhoneCodeInvalid:
            return False, "Invalid phone code"
        except errors.PhoneNumberInvalid:
            return False, "Invalid phone number"
        except errors.FloodWait as e:
            return False, f"Flood wait: {e.value} seconds"
        except Exception as e:
            logging.error(f"Error creating client for {phone}: {e}")
            return False, f"Error: {str(e)}"
    
    async def remove_client(self, phone: str):
        """Remove and stop a client"""
        if phone in self.clients:
            try:
                await self.clients[phone].stop()
                del self.clients[phone]
                return True, "Client removed successfully"
            except Exception as e:
                return False, f"Error removing client: {str(e)}"
        return False, "Client not found"
    
    async def get_client(self, phone: str) -> Optional[Client]:
        """Get client by phone number"""
        return self.clients.get(phone)
    
    async def report_channel_or_group(self, phone: str, target: str, reason: str = "spam"):
        """Report a channel or group using raw API"""
        client = await self.get_client(phone)
        if not client:
            return False, "Client not found"
        
        try:
            # Extract username or ID from target
            if target.startswith("https://t.me/"):
                username = target.split("/")[-1]
            else:
                username = target
            
            # Resolve peer and report via raw API
            peer = await client.resolve_peer(username)
            reason_obj = raw.types.InputReportReasonSpam()
            await client.invoke(
                raw.functions.account.ReportPeer(
                    peer=peer,
                    reason=reason_obj,
                    message="Spam / Abuse"
                )
            )
            
            return True, f"Successfully reported {target}"
            
        except Exception as e:
            logging.error(f"Error reporting {target}: {e}")
            return False, f"Error: {str(e)}"
    
    async def report_posts(self, phone: str, post_links: List[str]):
        """Report multiple posts using raw API"""
        client = await self.get_client(phone)
        if not client:
            return False, "Client not found"
        
        results = []
        
        for link in post_links:
            try:
                # Parse message link
                match = re.match(r'https://t\.me/([^/]+)/(\d+)', link.strip())
                if not match:
                    results.append(f"❌ Invalid link format: {link}")
                    continue
                
                username, message_id = match.groups()
                message_id = int(message_id)
                
                # Resolve peer and report message via raw API
                peer = await client.resolve_peer(username)
                reason_obj = raw.types.InputReportReasonSpam()
                await client.invoke(
                    raw.functions.messages.Report(
                        peer=peer,
                        id=[message_id],
                        reason=reason_obj,
                        message="Spam / Abuse"
                    )
                )
                
                results.append(f"✅ Reported: {link}")
                
            except Exception as e:
                results.append(f"❌ Error reporting {link}: {str(e)}")
        
        return True, "\n".join(results)
    
    async def join_chat(self, phone: str, chat_link: str):
        """Join a chat/channel"""
        client = await self.get_client(phone)
        if not client:
            return False, "Client not found"
        
        try:
            if chat_link.startswith("https://t.me/"):
                username = chat_link.split("/")[-1]
            else:
                username = chat_link
            
            chat = await client.join_chat(username)
            return True, f"Successfully joined {chat.title}"
            
        except Exception as e:
            return False, f"Error joining chat: {str(e)}"
    
    async def leave_chat(self, phone: str, chat_link: str):
        """Leave a chat/channel"""
        client = await self.get_client(phone)
        if not client:
            return False, "Client not found"
        
        try:
            if chat_link.startswith("https://t.me/"):
                username = chat_link.split("/")[-1]
            else:
                username = chat_link
            
            chat = await client.get_chat(username)
            await client.leave_chat(chat.id)
            return True, f"Successfully left {chat.title}"
            
        except Exception as e:
            return False, f"Error leaving chat: {str(e)}"
    
    async def send_message(self, phone: str, user_id: int, message: str):
        """Send message to user ID"""
        client = await self.get_client(phone)
        if not client:
            return False, "Client not found"
        
        try:
            await client.send_message(user_id, message)
            return True, "Message sent successfully"
            
        except Exception as e:
            return False, f"Error sending message: {str(e)}"
    
    async def add_reaction(self, phone: str, chat_id: int, message_id: int, emoji: str = "👎"):
        """Add reaction to message"""
        client = await self.get_client(phone)
        if not client:
            return False, "Client not found"
        
        try:
            await client.send_reaction(chat_id, message_id, emoji)
            return True, f"Added reaction {emoji}"
            
        except Exception as e:
            return False, f"Error adding reaction: {str(e)}"
    
    async def check_account_status(self, phone: str):
        """Check if account is banned/frozen"""
        client = await self.get_client(phone)
        if not client:
            return "disconnected", "Client not connected"
        
        try:
            # Try to get self info
            me = await client.get_me()
            if me:
                db.update_account_status(phone, "active", "Account is working normally")
                return "active", "Account is active"
            
        except errors.UserDeactivated:
            db.update_account_status(phone, "banned", "Account is banned")
            return "banned", "Account is banned"
        except errors.AuthKeyUnregistered:
            db.update_account_status(phone, "session_expired", "Session expired")
            return "session_expired", "Session expired"
        except Exception as e:
            db.update_account_status(phone, "error", str(e))
            return "error", str(e)
    
    async def get_phone_code(self, phone: str, api_id: int, api_hash: str):
        """Request phone verification code and return phone_code_hash"""
        client = None
        is_connected = False
        try:
            # Convert api_id to int explicitly first
            try:
                api_id = int(api_id) if api_id else 0
            except (ValueError, TypeError):
                return False, "API ID باید عدد باشد", None
                
            # Validate API credentials
            if not api_id or not api_hash:
                return False, "API ID یا API Hash تنظیم نشده است", None
            
            # Clean phone number format
            if not phone.startswith('+'):
                phone = '+' + phone.lstrip('+')
            
            # Validate phone number format
            if len(phone) < 10:
                return False, "شماره تلفن کوتاه است", None
            
            # Create client with proper credentials
            client = Client(
                name=f"temp_{phone.replace('+', '')}",
                api_id=api_id,
                api_hash=str(api_hash)
            )
            
            # Connect the client
            await client.connect()
            is_connected = True
            
            try:
                sent_code = await client.send_code(phone)
                phone_code_hash = sent_code.phone_code_hash
                return True, "کد تایید ارسال شد", phone_code_hash
            except errors.ApiIdInvalid:
                return False, "API ID یا API Hash نامعتبر است", None
            except errors.PhoneNumberInvalid:
                return False, "شماره تلفن نامعتبر است", None
            except errors.FloodWait as e:
                return False, f"لطفا {e.value} ثانیه صبر کنید", None
            except Exception as e:
                logging.error(f"Error sending code to {phone}: {e}")
                return False, f"خطا: {str(e)}", None
                    
        except ValueError as e:
            logging.error(f"ValueError in get_phone_code: {e}")
            return False, "API ID باید عدد باشد", None
        except Exception as e:
            logging.error(f"Exception in get_phone_code: {e}")
            return False, f"خطا در ارسال کد: {str(e)}", None
        finally:
            # Only disconnect if client was connected
            if client is not None and is_connected:
                try:
                    await client.disconnect()
                except Exception as e:
                    logging.error(f"Error disconnecting client: {e}")
                    pass
    
    async def verify_phone_code(self, phone: str, code: str, phone_code_hash: str, api_id: int, api_hash: str):
        """Verify phone code and create session"""
        client = None
        is_connected = False
        try:
            # Clean phone number format
            if not phone.startswith('+'):
                phone = '+' + phone.lstrip('+')
                
            client = Client(
                name=f"verify_{phone.replace('+', '')}",
                api_id=int(api_id),
                api_hash=str(api_hash)
            )
            await client.connect()
            is_connected = True
            
            await client.sign_in(phone, code, phone_code_hash)
            session_string = await client.export_session_string()
            
            # Store session
            db.store_session(phone, session_string)
            config.add_account(phone, api_id, api_hash, session_string)
            
            # Clear the phone code hash only after successful verification
            db.clear_phone_code_hash(phone)
            
            # Disconnect temporary client
            try:
                if is_connected:
                    await client.disconnect()
                    is_connected = False
            except Exception as e:
                logging.error(f"Error disconnecting verify client: {e}")
                pass

            # Start a persistent client for this account immediately
            create_success, create_msg = await self.create_client(
                phone,
                api_id,
                api_hash,
                session_string
            )
            if not create_success:
                return True, f"اکانت تایید شد، اما کلاینت شروع نشد: {create_msg}"
            
            return True, "اکانت با موفقیت تایید و اضافه شد"
            
        except errors.PhoneCodeInvalid:
            return False, "کد تایید نامعتبر است"
        except errors.PhoneCodeExpired:
            return False, "کد تایید منقضی شده است. مجدداً درخواست کنید"
        except errors.SessionPasswordNeeded:
            return False, "احراز هویت دو مرحله‌ای فعال است. این قابلیت هنوز پشتیبانی نمی‌شود"
        except Exception as e:
            logging.error(f"Exception in verify_phone_code: {e}")
            return False, f"خطا در تایید کد: {str(e)}"
        finally:
            if client is not None and is_connected:
                try:
                    await client.disconnect()
                except Exception as e:
                    logging.error(f"Error disconnecting client in finally: {e}")
                    pass

client_manager = TelegramClientManager()
