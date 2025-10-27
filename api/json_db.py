"""
JSON-based database system for Soupie
Replaces SQLAlchemy with simple JSON file storage
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

class JSONDatabase:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.ensure_data_dir()
        self.init_tables()
    
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def init_tables(self):
        """Initialize JSON files for each table"""
        tables = [
            "user_registration.json",
            "question_answer.json", 
            "private_journal.json",
            "open_journal.json",
            "onboarding_records.json"
        ]
        
        for table in tables:
            file_path = os.path.join(self.data_dir, table)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _read_table(self, table_name: str) -> List[Dict]:
        """Read data from a JSON table"""
        file_path = os.path.join(self.data_dir, f"{table_name}.json")
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_table(self, table_name: str, data: List[Dict]):
        """Write data to a JSON table"""
        file_path = os.path.join(self.data_dir, f"{table_name}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def create_user(self, user_data: Dict) -> str:
        """Create a new user"""
        users = self._read_table("user_registration")
        user_id = str(uuid.uuid4())
        user_data.update({
            "id": user_id,
            "created_at": datetime.utcnow().isoformat()
        })
        users.append(user_data)
        self._write_table("user_registration", users)
        return user_id
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        users = self._read_table("user_registration")
        for user in users:
            if user.get("email") == email:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users = self._read_table("user_registration")
        for user in users:
            if user.get("id") == user_id:
                return user
        return None
    
    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user data"""
        users = self._read_table("user_registration")
        for i, user in enumerate(users):
            if user.get("id") == user_id:
                users[i].update(updates)
                self._write_table("user_registration", users)
                return True
        return False
    
    def create_question_answer(self, user_id: str, question: str, answer: str) -> str:
        """Create a question-answer entry"""
        qa_data = self._read_table("question_answer")
        qa_id = str(uuid.uuid4())
        qa_entry = {
            "id": qa_id,
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "created_at": datetime.utcnow().isoformat()
        }
        qa_data.append(qa_entry)
        self._write_table("question_answer", qa_data)
        return qa_id
    
    def get_user_question_answers(self, user_id: str) -> List[Dict]:
        """Get all question-answers for a user"""
        qa_data = self._read_table("question_answer")
        return [qa for qa in qa_data if qa.get("user_id") == user_id]
    
    def create_private_journal(self, user_id: str, content: str, ai_summary: str = None) -> str:
        """Create a private journal entry"""
        journals = self._read_table("private_journal")
        journal_id = str(uuid.uuid4())
        journal_entry = {
            "id": journal_id,
            "user_id": user_id,
            "content": content,
            "ai_summary": ai_summary,
            "created_at": datetime.utcnow().isoformat()
        }
        journals.append(journal_entry)
        self._write_table("private_journal", journals)
        return journal_id
    
    def get_user_private_journals(self, user_id: str) -> List[Dict]:
        """Get all private journals for a user"""
        journals = self._read_table("private_journal")
        return [j for j in journals if j.get("user_id") == user_id]
    
    def get_private_journal_by_id(self, journal_id: str) -> Optional[Dict]:
        """Get a specific private journal entry by ID"""
        journals = self._read_table("private_journal")
        for journal in journals:
            if journal.get("id") == journal_id:
                return journal
        return None
    
    def update_private_journal(self, journal_id: str, updates: Dict) -> bool:
        """Update a private journal entry"""
        journals = self._read_table("private_journal")
        for journal in journals:
            if journal.get("id") == journal_id:
                journal.update(updates)
                self._write_table("private_journal", journals)
                return True
        return False
    
    def create_open_journal(self, user_id: str, content: str, emotion_tag: str = None) -> str:
        """Create an open journal entry"""
        journals = self._read_table("open_journal")
        journal_id = str(uuid.uuid4())
        journal_entry = {
            "id": journal_id,
            "user_id": user_id,
            "content": content,
            "emotion_tag": emotion_tag,
            "created_at": datetime.utcnow().isoformat()
        }
        journals.append(journal_entry)
        self._write_table("open_journal", journals)
        return journal_id
    
    def get_all_open_journals(self) -> List[Dict]:
        """Get all open journal entries"""
        return self._read_table("open_journal")
    
    def get_user_open_journals(self, user_id: str) -> List[Dict]:
        """Get open journals for a specific user"""
        journals = self._read_table("open_journal")
        return [j for j in journals if j.get("user_id") == user_id]
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user and all their data"""
        try:
            # Delete from user_registration
            users = self._read_table("user_registration")
            users = [u for u in users if u.get("id") != user_id]
            self._write_table("user_registration", users)
            
            # Delete from question_answer
            qa_entries = self._read_table("question_answer")
            qa_entries = [qa for qa in qa_entries if qa.get("user_id") != user_id]
            self._write_table("question_answer", qa_entries)
            
            # Delete from private_journal
            private_journals = self._read_table("private_journal")
            private_journals = [pj for pj in private_journals if pj.get("user_id") != user_id]
            self._write_table("private_journal", private_journals)
            
            # Delete from open_journal
            open_journals = self._read_table("open_journal")
            open_journals = [oj for oj in open_journals if oj.get("user_id") != user_id]
            self._write_table("open_journal", open_journals)
            
            return True
        except Exception:
            return False
    
    def create_onboarding_record(self, onboarding_data: Dict) -> str:
        """Create a new onboarding record"""
        try:
            onboarding_data['id'] = str(uuid.uuid4())
            onboarding_data['created_at'] = datetime.now().isoformat()
            
            # Read existing records
            records = self._read_table("onboarding_records")
            records.append(onboarding_data)
            
            # Write back to file
            self._write_table("onboarding_records", records)
            
            return onboarding_data['id']
        except Exception as e:
            print(f"Error creating onboarding record: {e}")
            return None
    
    def get_user_onboarding_record(self, user_id: str) -> Optional[Dict]:
        """Get onboarding record for a specific user"""
        try:
            records = self._read_table("onboarding_records")
            for record in records:
                if record.get("user_id") == user_id:
                    return record
            return None
        except Exception:
            return None

# Global database instance
db = JSONDatabase()

# Database session dependency (compatible with Flask)
def get_db():
    """Database session dependency for Flask compatibility"""
    return db
