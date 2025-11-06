import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_file="database.json"):
        self.db_file = db_file
        self.load_database()
    
    def load_database(self):
        """Load database from JSON file"""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "users": {},
                "reports": [],
                "sessions": {},
                "verification_codes": {},
                "phone_code_hashes": {},
                "account_status": {}
            }
            self.save_database()
    
    def save_database(self):
        """Save database to JSON file"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user information"""
        self.data["users"][str(user_id)] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "join_date": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        self.save_database()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        return self.data["users"].get(str(user_id))
    
    def update_user_activity(self, user_id: int):
        """Update user's last activity"""
        if str(user_id) in self.data["users"]:
            self.data["users"][str(user_id)]["last_activity"] = datetime.now().isoformat()
            self.save_database()
    
    def add_report(self, user_id: int, report_type: str, target: str, status: str = "pending"):
        """Add new report"""
        report = {
            "id": len(self.data["reports"]) + 1,
            "user_id": user_id,
            "report_type": report_type,
            "target": target,
            "status": status,
            "created_date": datetime.now().isoformat(),
            "completed_date": None
        }
        self.data["reports"].append(report)
        self.save_database()
        return report["id"]
    
    def update_report_status(self, report_id: int, status: str):
        """Update report status"""
        for report in self.data["reports"]:
            if report["id"] == report_id:
                report["status"] = status
                if status == "completed":
                    report["completed_date"] = datetime.now().isoformat()
                break
        self.save_database()
    
    def get_reports(self, user_id: int = None, status: str = None) -> List[Dict]:
        """Get reports with optional filters"""
        reports = self.data["reports"]
        
        if user_id:
            reports = [r for r in reports if r["user_id"] == user_id]
        
        if status:
            reports = [r for r in reports if r["status"] == status]
        
        return reports
    
    def store_session(self, phone: str, session_string: str):
        """Store session string for phone number"""
        self.data["sessions"][phone] = {
            "session_string": session_string,
            "created_date": datetime.now().isoformat()
        }
        self.save_database()
    
    def get_session(self, phone: str) -> Optional[str]:
        """Get session string for phone number"""
        session_data = self.data["sessions"].get(phone)
        return session_data["session_string"] if session_data else None
    
    def store_verification_code(self, phone: str, code: str):
        """Store verification code for phone number"""
        self.data["verification_codes"][phone] = {
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
        self.save_database()
    
    def get_verification_code(self, phone: str) -> Optional[str]:
        """Get verification code for phone number"""
        code_data = self.data["verification_codes"].get(phone)
        if code_data:
            # Remove code after retrieval for security
            del self.data["verification_codes"][phone]
            self.save_database()
            return code_data["code"]
        return None

    def store_phone_code_hash(self, phone: str, phone_code_hash: str):
        """Store phone_code_hash for login verification"""
        self.data["phone_code_hashes"][phone] = {
            "phone_code_hash": phone_code_hash,
            "timestamp": datetime.now().isoformat()
        }
        self.save_database()

    def get_phone_code_hash(self, phone: str) -> Optional[str]:
        """Get phone_code_hash for a phone number without clearing it"""
        hash_data = self.data["phone_code_hashes"].get(phone)
        if hash_data:
            return hash_data["phone_code_hash"]
        return None
    
    def clear_phone_code_hash(self, phone: str):
        """Clear phone_code_hash after successful verification"""
        if phone in self.data["phone_code_hashes"]:
            del self.data["phone_code_hashes"][phone]
            self.save_database()
    
    def update_account_status(self, phone: str, status: str, details: str = None):
        """Update account status (active, banned, frozen, etc.)"""
        self.data["account_status"][phone] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.save_database()
    
    def get_account_status(self, phone: str) -> Optional[Dict]:
        """Get account status"""
        return self.data["account_status"].get(phone)

db = Database()
