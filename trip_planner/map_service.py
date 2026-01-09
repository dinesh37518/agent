# =================================
# File: trip_planner/map_service.py
# (Fix: get_live_nav_link(origin, destination) includes explicit origin,
#  so Google Maps shows the starting point correctly. Textual current city is fixed.)
# =================================

import os
import re
from urllib.parse import quote_plus

try:
    from groq import Groq
except Exception:
    Groq = None

DEFAULT_FIXED_CITY = "Karur"
DEFAULT_GROQ_API_KEY = "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"  # prefer env: GROQ_API_KEY


class MapService:
    def __init__(self):
        self.routes = {
            ("chennai", "ooty"): [
                "Start from Chennai.",
                "Take NH32 towards Villupuram.",
                "Continue on NH79 and then NH544 towards Coimbatore.",
                "From Coimbatore, take NH181 via Mettupalayam and Coonoor.",
                "Reach Ooty and check into your hotel.",
            ],
            ("chennai", "kodaikanal"): [
                "Start from Chennai.",
                "Take NH38 towards Trichy.",
                "Continue on NH83 towards Dindigul.",
                "From Dindigul, take the ghat road to Kodaikanal.",
                "Reach Kodaikanal and check into your hotel.",
            ],
            ("chennai", "munnar"): [
                "Start from Chennai.",
                "Take NH32 towards Villupuram.",
                "Continue via Trichy and Madurai towards Theni.",
                "From Theni, take the ghat road towards Munnar.",
                "Reach Munnar and check into your hotel.",
            ],
            ("bangalore", "ooty"): [
                "Start from Bangalore.",
                "Take NICE Road to connect to Mysore Road (NH275).",
                "Drive to Mysore and then towards Gundlupet.",
                "From Gundlupet, take the ghat road via Bandipur and Masinagudi.",
                "Reach Ooty and check into your hotel.",
            ],
            ("bangalore", "coorg"): [
                "Start from Bangalore.",
                "Take NH75 or Mysore Road towards Mandya.",
                "Continue towards Kushalnagar and then Madikeri.",
                "Reach Coorg (Madikeri) and check into your hotel.",
            ],
            ("bangalore", "kodaikanal"): [
                "Start from Bangalore.",
                "Take NH44 towards Salem.",
                "Continue towards Dindigul.",
                "From Dindigul, take the ghat road to Kodaikanal.",
                "Reach Kodaikanal and check into your hotel.",
            ],
            ("hyderabad", "ooty"): [
                "Start from Hyderabad.",
                "Take NH44 towards Kurnool and Anantapur.",
                "Continue towards Bangalore and then Mysore.",
                "From Mysore, proceed via Gundlupet and Bandipur to Ooty.",
                "Reach Ooty and check into your hotel.",
            ],
            ("hyderabad", "munnar"): [
                "Start from Hyderabad.",
                "Take NH44 towards Kurnool and Anantapur.",
                "Continue towards Bangalore and then Salem.",
                "Proceed towards Dindigul, Theni, and then up the ghat road to Munnar.",
                "Reach Munnar and check into your hotel.",
            ],
            ("mumbai", "mahabaleshwar"): [
                "Start from Mumbai.",
                "Take Mumbai–Pune Expressway to Pune.",
                "From Pune, take NH48 towards Satara.",
                "Turn towards Mahabaleshwar at Wai.",
                "Reach Mahabaleshwar and check into your hotel.",
            ],
            ("mumbai", "manali"): [
                "Start from Mumbai.",
                "Travel via Gujarat towards Delhi (NH48).",
                "From Delhi, take NH44 towards Chandigarh.",
                "Continue via Mandi and Kullu to reach Manali.",
                "Reach Manali and check into your hotel.",
            ],
            ("delhi", "manali"): [
                "Start from Delhi.",
                "Take NH44 towards Chandigarh.",
                "Continue towards Bilaspur, Mandi, and Kullu.",
                "Proceed along the Beas river valley to Manali.",
                "Reach Manali and check into your hotel.",
            ],
            ("delhi", "shimla"): [
                "Start from Delhi.",
                "Take NH44 towards Chandigarh.",
                "From Chandigarh, take NH5 via Kalka and Solan.",
                "Drive up the hills to Shimla.",
                "Reach Shimla and check into your hotel.",
            ],
        }

        self.places_info = {
            "chennai": {"name": "Chennai", "description": "A coastal city in Tamil Nadu known for its beaches, temples, and rich culture.", "highlights": ["Marina Beach", "Kapaleeshwarar Temple", "Santhome Church"]},
            "bangalore": {"name": "Bangalore", "description": "Capital of Karnataka, known as the Garden City and IT hub of India.", "highlights": ["Cubbon Park", "Lalbagh Botanical Garden", "Vidhana Soudha"]},
            "mumbai": {"name": "Mumbai", "description": "Financial capital of India, famous for Bollywood and the Gateway of India.", "highlights": ["Marine Drive", "Gateway of India", "Elephanta Caves"]},
            "hyderabad": {"name": "Hyderabad", "description": "Capital of Telangana, known for Charminar and Hyderabadi biryani.", "highlights": ["Charminar", "Golconda Fort", "Hussain Sagar Lake"]},
            "delhi": {"name": "Delhi", "description": "Capital city of India with a mix of historic monuments and modern life.", "highlights": ["Red Fort", "India Gate", "Qutub Minar"]},
            "ooty": {"name": "Ooty", "description": "Ooty is a hill station in Tamil Nadu known for its cool climate and tea gardens.", "highlights": ["Ooty Lake", "Doddabetta Peak", "Nilgiri Mountain Railway"]},
            "kodaikanal": {"name": "Kodaikanal", "description": "Kodaikanal is a scenic hill station in Tamil Nadu.", "highlights": ["Kodaikanal Lake", "Coaker's Walk", "Pine forests"]},
            "munnar": {"name": "Munnar", "description": "Munnar is a hill station in Kerala known for tea plantations and valleys.", "highlights": ["Tea gardens", "Eravikulam National Park", "Mattupetty Dam"]},
            "coorg": {"name": "Coorg", "description": "Coorg is a hill station in Karnataka known for coffee estates and misty hills.", "highlights": ["Coffee plantations", "Abbey Falls", "Raja's Seat"]},
            "manali": {"name": "Manali", "description": "Manali is a hill station in Himachal Pradesh, popular for snow and adventure.", "highlights": ["Solang Valley", "Rohtang Pass", "Hadimba Temple"]},
            "shimla": {"name": "Shimla", "description": "Shimla is the capital of Himachal Pradesh.", "highlights": ["The Ridge", "Mall Road", "Jakhoo Temple"]},
            "mahabaleshwar": {"name": "Mahabaleshwar", "description": "Mahabaleshwar is a hill station in Maharashtra known for viewpoints and strawberries.", "highlights": ["Arthur's Seat", "Venna Lake", "Strawberry farms"]},
        }

        self._fixed_city = self._load_fixed_city() or DEFAULT_FIXED_CITY

        self._ai_client = None
        self._ai_enabled = False
        if Groq is not None:
            api_key = os.environ.get("GROQ_API_KEY", DEFAULT_GROQ_API_KEY).strip()
            if api_key.startswith("gsk_"):
                try:
                    self._ai_client = Groq(api_key=api_key)
                    self._ai_enabled = True
                except Exception as e:
                    print(f"[AI init error] {e}")

    # ---- Fixed city helpers ----
    def _load_fixed_city(self):
        env_city = os.environ.get("MY_HOME_CITY", "").strip()
        if env_city:
            return env_city
        try:
            base = os.path.dirname(__file__)
            path = os.path.join(base, "home_city.txt")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    line = f.readline().strip()
                    if line:
                        return line
        except Exception:
            pass
        return None

    def set_fixed_city(self, city_name):
        city = (city_name or "").strip()
        self._fixed_city = city if city else DEFAULT_FIXED_CITY
        try:
            base = os.path.dirname(__file__)
            path = os.path.join(base, "home_city.txt")
            if city:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(city + "\n")
            else:
                if os.path.exists(path):
                    os.remove(path)
        except Exception:
            pass

    def get_current_city(self, default=None):
        return self._fixed_city or default or DEFAULT_FIXED_CITY

    # ---- AI route generation ----
    def _normalize_steps(self, text):
        lines = [ln.strip() for ln in (text or "").splitlines()]
        out = []
        for ln in lines:
            ln = re.sub(r"^\s*(?:[-–•*]|\d+[\.\)]?)\s*", "", ln)
            if ln:
                out.append(ln)
        return out[:16]

    def _ai_generate_route(self, origin, destination, mode="driving"):
        if not self._ai_enabled or self._ai_client is None:
            return []
        try:
            prompt = (
                "You are a navigation assistant. Provide concise, safe, high-level step-by-step directions.\n"
                f"Origin: {origin}\nDestination: {destination}\nMode: {mode}\n\n"
                "Requirements:\n"
                "- 6 to 12 steps, each one line.\n"
                "- Prefer major highways/arterials; avoid tiny local street names.\n"
                "- No live traffic or exact kilometers.\n"
                "- Output only the steps (no numbering, no intro/outro)."
            )
            resp = self._ai_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=600,
            )
            text = (resp.choices[0].message.content or "").strip()
            return self._normalize_steps(text)
        except Exception as e:
            print(f"[AI route error] {e}")
            return []

    # ---- AI place paragraph ----
    def _ai_place_paragraph(self, place_name):
        if not self._ai_enabled or self._ai_client is None:
            return None
        try:
            prompt = (
                "Write one well-structured paragraph (6–8 sentences) introducing the place below. "
                "Briefly cover: what it is known for, a touch of history, cultural feel (food/festivals), "
                "and 3–4 key highlights. No bullet points, no headings, no markdown; plain text only. "
                "Keep under 900 characters.\n\n"
                f"Place: {place_name}"
            )
            resp = self._ai_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=500,
            )
            paragraph = (resp.choices[0].message.content or "").strip()
            paragraph = re.sub(r"\s+\n", " ", paragraph)
            paragraph = re.sub(r"\n+", " ", paragraph)
            return paragraph if paragraph else None
        except Exception as e:
            print(f"[AI place error] {e}")
            return None

    # ---- Public APIs ----
    def get_route(self, origin, destination, mode="driving"):
        origin_clean = origin.strip()
        dest_clean = destination.strip()

        steps = self._ai_generate_route(origin_clean, dest_clean, mode=mode)
        if steps:
            return steps

        key = (origin_clean.lower(), dest_clean.lower())
        if key in self.routes:
            return self.routes[key]

        return [
            f"Start from {origin_clean}.",
            f"Head towards {dest_clean} using primary highways.",
            "Follow major road signs and your preferred map app as needed.",
            f"Arrive at {dest_clean}.",
        ]

    def get_live_nav_link(self, origin, destination, mode="driving"):
        """
        Live navigation link with explicit origin and destination.
        This fixes the starting point so Google Maps shows the route from origin to destination:
          https://www.google.com/maps/dir/?api=1&origin=<ORIGIN>&destination=<DEST>&travelmode=<MODE>&dir_action=navigate
        """
        o = quote_plus(origin.strip())
        d = quote_plus(destination.strip())
        m = quote_plus((mode or "driving").strip())
        return f"https://www.google.com/maps/dir/?api=1&origin={o}&destination={d}&travelmode={m}&dir_action=navigate"

    def describe_place(self, place_name):
        paragraph = self._ai_place_paragraph(place_name)
        if paragraph:
            return {
                "name": place_name,
                "description": paragraph,
                "history": "",
                "culture": "",
                "highlights": [],
            }

        key = place_name.strip().lower()
        info = self.places_info.get(key)
        if info:
            return {
                "name": info.get("name", place_name),
                "description": info.get("description", f"{place_name} is a notable destination."),
                "history": "",
                "culture": "",
                "highlights": info.get("highlights", []),
            }

        return {
            "name": place_name,
            "description": f"{place_name} is a notable destination with attractions, local cuisine, and culture.",
            "history": "",
            "culture": "",
            "highlights": [],
        }