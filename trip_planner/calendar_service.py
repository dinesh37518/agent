from datetime import date, timedelta


class CalendarService:
    def __init__(self):
        # Simple in-memory calendar with some demo commitments for 'demo_user'
        today = date.today()
        self.commitments = {
            "demo_user": {
                today + timedelta(days=2): "Office meeting",
                today + timedelta(days=5): "Family function",
            }
        }

    def _ensure_user(self, user_id):
        if user_id not in self.commitments:
            self.commitments[user_id] = {}

    def is_date_available(self, user_id, check_date):
        self._ensure_user(user_id)
        return check_date not in self.commitments[user_id]

    def get_commitment(self, user_id, check_date):
        self._ensure_user(user_id)
        return self.commitments[user_id].get(check_date)

    def add_trip(self, user_id, start_date, end_date, description):
        self._ensure_user(user_id)
        current = start_date
        while current <= end_date:
            self.commitments[user_id][current] = description
            current += timedelta(days=1)

    def suggest_alternative_date(self, user_id, preferred_date, search_days=30):
        self._ensure_user(user_id)
        for i in range(1, search_days + 1):
            candidate = preferred_date + timedelta(days=i)
            if self.is_date_available(user_id, candidate):
                return candidate
        return None

    def get_all_commitments(self, user_id):
        self._ensure_user(user_id)
        # Return a copy to avoid external modification
        return dict(self.commitments[user_id])
