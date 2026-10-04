import os
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings

class SupabaseService:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.client = None

        # Local in-memory caches as fallback & fast retrieval
        self._local_users: Dict[str, Dict[str, Any]] = {}
        self._local_academics: Dict[str, Dict[str, Any]] = {}
        self._local_surveys: List[Dict[str, Any]] = []
        self._local_profiles: Dict[str, Dict[str, Any]] = {}
        self._local_recommendations: List[Dict[str, Any]] = []
        self._local_wishlists: List[Dict[str, Any]] = []
        self._local_conversations: Dict[str, Dict[str, Any]] = {}
        self._local_messages: Dict[str, List[Dict[str, Any]]] = {}

        if self.url and self.key:
            try:
                from supabase import create_client, Client
                self.client: Client = create_client(self.url, self.key)
            except Exception:
                self.client = None

    # 1. USER MANAGEMENT
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(user_data.get("id") or uuid.uuid4())
        user_data["id"] = user_id
        user_data["updated_at"] = datetime.now().isoformat()
        if "created_at" not in user_data:
            user_data["created_at"] = datetime.now().isoformat()

        self._local_users[user_id] = user_data
        email = user_data.get("email")
        if email:
            self._local_users[email] = user_data

        if self.client:
            try:
                res = self.client.table("users").upsert(user_data).execute()
                if res.data:
                    return res.data[0]
            except Exception:
                pass
        return user_data

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if user_id in self._local_users:
            return self._local_users[user_id]
        if self.client:
            try:
                res = self.client.table("users").select("*").eq("id", user_id).single().execute()
                if res.data:
                    self._local_users[user_id] = res.data
                    return res.data
            except Exception:
                pass
        return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if email in self._local_users:
            return self._local_users[email]
        if self.client:
            try:
                res = self.client.table("users").select("*").eq("email", email).single().execute()
                if res.data:
                    self._local_users[email] = res.data
                    return res.data
            except Exception:
                pass
        return None

    # 2. ACADEMIC RECORDS
    async def save_academic_record(self, academic_data: Dict[str, Any]) -> Dict[str, Any]:
        record_id = str(academic_data.get("id") or uuid.uuid4())
        academic_data["id"] = record_id
        user_id = str(academic_data.get("user_id", "default_user"))
        academic_data["updated_at"] = datetime.now().isoformat()

        self._local_academics[user_id] = academic_data

        if self.client:
            try:
                res = self.client.table("academic_records").upsert(academic_data).execute()
                if res.data:
                    return res.data[0]
            except Exception:
                pass
        return academic_data

    async def get_academic_record(self, user_id: str) -> Optional[Dict[str, Any]]:
        if user_id in self._local_academics:
            return self._local_academics[user_id]
        if self.client:
            try:
                res = self.client.table("academic_records").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(1).execute()
                if res.data and len(res.data) > 0:
                    self._local_academics[user_id] = res.data[0]
                    return res.data[0]
            except Exception:
                pass
        return None

    # 3. SURVEY SUBMISSIONS
    async def save_survey_submission(self, survey_data: Dict[str, Any]) -> str:
        sub_id = str(survey_data.get("id") or uuid.uuid4())
        survey_data["id"] = sub_id
        survey_data["created_at"] = datetime.now().isoformat()
        self._local_surveys.append(survey_data)

        if self.client:
            try:
                self.client.table("survey_submissions").insert(survey_data).execute()
            except Exception:
                pass
        return sub_id

    # 4. STUDENT CAREER PROFILES (Career Passport)
    async def save_student_profile(self, profile_data: Dict[str, Any]) -> str:
        profile_id = profile_data.get("id") or f"PRF_{uuid.uuid4().hex[:8].upper()}"
        profile_data["id"] = profile_id
        profile_data["updated_at"] = datetime.now().isoformat()
        self._local_profiles[profile_id] = profile_data

        user_id = profile_data.get("user_id")
        if user_id:
            self._local_profiles[str(user_id)] = profile_data

        if self.client:
            try:
                self.client.table("student_career_profiles").upsert(profile_data).execute()
            except Exception:
                pass
        return profile_id

    async def get_student_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        if profile_id in self._local_profiles:
            return self._local_profiles[profile_id]

        if self.client:
            try:
                res = self.client.table("student_career_profiles").select("*").eq("id", profile_id).single().execute()
                if res.data:
                    self._local_profiles[profile_id] = res.data
                    return res.data
            except Exception:
                pass
        return None

    # 5. RECOMMENDATIONS HISTORY
    async def save_recommendations_history(self, rec_data: Dict[str, Any]) -> str:
        rec_id = str(rec_data.get("id") or uuid.uuid4())
        rec_data["id"] = rec_id
        rec_data["created_at"] = datetime.now().isoformat()
        self._local_recommendations.append(rec_data)

        if self.client:
            try:
                self.client.table("recommendations_history").insert(rec_data).execute()
            except Exception:
                pass
        return rec_id

    # 6. USER WISHLISTS / BOOKMARKS
    async def toggle_bookmark(self, user_id: str, university_code: str, major_code: str, uni_name: str = "", major_name: str = "", cutoff: float = 25.0) -> Dict[str, Any]:
        item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "university_code": university_code,
            "major_code": major_code,
            "university_name": uni_name,
            "major_name": major_name,
            "cutoff_score_2025": cutoff,
            "created_at": datetime.now().isoformat()
        }
        exists = any(b["user_id"] == user_id and b["university_code"] == university_code and b["major_code"] == major_code for b in self._local_wishlists)
        if exists:
            self._local_wishlists = [b for b in self._local_wishlists if not (b["user_id"] == user_id and b["university_code"] == university_code and b["major_code"] == major_code)]
            is_saved = False
        else:
            self._local_wishlists.append(item)
            is_saved = True

        if self.client:
            try:
                if is_saved:
                    self.client.table("user_wishlists").insert(item).execute()
                else:
                    self.client.table("user_wishlists").delete().match({"user_id": user_id, "university_code": university_code, "major_code": major_code}).execute()
            except Exception:
                pass

        return {"success": True, "is_saved": is_saved, "university_code": university_code, "major_code": major_code}

    async def get_user_wishlist(self, user_id: str) -> List[Dict[str, Any]]:
        local_items = [b for b in self._local_wishlists if b.get("user_id") == user_id]
        if self.client:
            try:
                res = self.client.table("user_wishlists").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return local_items

    # 7. CHAT CONVERSATIONS & MESSAGES
    async def create_chat_conversation(self, user_id: str, title: str = "Tư vấn Tuyển sinh 2026") -> str:
        conv_id = str(uuid.uuid4())
        record = {
            "id": conv_id,
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._local_conversations[conv_id] = record
        self._local_messages[conv_id] = []

        if self.client:
            try:
                self.client.table("chat_conversations").insert(record).execute()
            except Exception:
                pass
        return conv_id

    async def save_chat_message(self, conversation_id: str, sender: str, content: str, citations: Optional[List[Dict[str, Any]]] = None, graph_context: Optional[List[Any]] = None) -> str:
        msg_id = str(uuid.uuid4())
        msg = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "sender": sender,
            "content": content,
            "citations": citations or [],
            "graph_context": graph_context or [],
            "created_at": datetime.now().isoformat()
        }
        if conversation_id not in self._local_messages:
            self._local_messages[conversation_id] = []
        self._local_messages[conversation_id].append(msg)

        if self.client:
            try:
                self.client.table("chat_messages").insert(msg).execute()
            except Exception:
                pass
        return msg_id

    async def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        if conversation_id in self._local_messages:
            return self._local_messages[conversation_id]
        if self.client:
            try:
                res = self.client.table("chat_messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
                if res.data:
                    self._local_messages[conversation_id] = res.data
                    return res.data
            except Exception:
                pass
        return []

supabase_service = SupabaseService()
