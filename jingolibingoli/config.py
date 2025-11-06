import json
import os
from datetime import datetime, timedelta

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "bot_token": "",
                "api_id": "",
                "api_hash": "",
                "admins": [],
                "accounts": {},
                "sessions": {},
                "settings": {
                    "auto_join": True,
                    "auto_report": True,
                    "view_reactions": True
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
    
    def add_admin(self, user_id, duration_days=None):
        """Add admin with optional expiration"""
        if isinstance(user_id, int):
            admin_data = {
                "user_id": user_id,
                "added_date": datetime.now().isoformat(),
                "expires": None
            }
        else:
            admin_data = user_id  # Assume it's already a dict
        
        if duration_days:
            expires = datetime.now() + timedelta(days=duration_days)
            admin_data["expires"] = expires.isoformat()
        
        self.data["admins"].append(admin_data)
        self.save_config()
    
    def remove_admin(self, user_id):
        """Remove admin by user ID"""
        self.data["admins"] = [admin for admin in self.data["admins"] 
                              if (isinstance(admin, dict) and admin["user_id"] != user_id) or (isinstance(admin, int) and admin != user_id)]
        self.save_config()
    
    def is_admin(self, user_id):
        """Check if user is admin and not expired"""
        for admin in self.data["admins"]:
            if isinstance(admin, dict):
                if admin["user_id"] == user_id:
                    expires = admin.get("expires")
                    if expires:
                        expires_dt = datetime.fromisoformat(expires)
                        if datetime.now() > expires_dt:
                            self.remove_admin(user_id)
                            return False
                    return True
            elif isinstance(admin, int) and admin == user_id:
                return True
        return False
    
    def add_account(self, phone, api_id, api_hash, session_string=None):
        """Add new account"""
        self.data["accounts"][phone] = {
            "api_id": api_id,
            "api_hash": api_hash,
            "session_string": session_string,
            "status": "active",
            "added_date": datetime.now().isoformat()
        }
        self.save_config()
    
    def remove_account(self, phone):
        """Remove account"""
        if phone in self.data["accounts"]:
            del self.data["accounts"][phone]
            self.save_config()
    
    def get_accounts(self):
        """Get all accounts"""
        return self.data["accounts"]
    
    def update_account_status(self, phone, status):
        """Update account status"""
        if phone in self.data["accounts"]:
            self.data["accounts"][phone]["status"] = status
            self.save_config()
    
    def set_api_credentials(self, api_id, api_hash):
        """Set API credentials"""
        self.data["api_id"] = api_id
        self.data["api_hash"] = api_hash
        self.save_config()

    def get_api_credentials(self):
        """Return global API credentials as tuple (api_id, api_hash)"""
        return self.data.get("api_id"), self.data.get("api_hash")
    
    def set_bot_token(self, token):
        """Set bot token"""
        self.data["bot_token"] = token
        self.save_config()

config = Config()
