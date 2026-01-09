# ===============================
# File: trip_planner/chat_agent.py
# (Human-like conversational agent with empathy, small talk,
#  intent understanding, and gentle guidance. It reuses your
#  existing services and can run standalone or be called from main.py.)
#
# Run:
#   python3 trip_planner/chat_agent.py
#
# Optional (for more human-like tone and rephrasing):
#   python3 -m pip install groq
#   export GROQ_API_KEY="gsk_your_actual_key_here"
# ===============================

import os
import re
import sys
import webbrowser
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict

from ai_agent import TripPlannerAgent
from map_service import MapService
from weather_service import WeatherService
from calendar_service import CalendarService
from booking_service import BookingService
from communication_service import CommunicationService

# Optional Groq for empathetic rewrites
try:
    from groq import Groq
except Exception:
    Groq = None


DATE_FMT = "%d-%m-%y"


def parse_date(s: str) -> date:
    return datetime.strptime(s.strip(), DATE_FMT).date()


def fmt_date(d: date) -> str:
    return d.strftime(DATE_FMT)


def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_yes_no(prompt: str) -> bool:
    while True:
        v = input(prompt + " (y/n): ").strip().lower()
        if v in ("y", "yes"):
            return True
        if v in ("n", "no"):
            return False
        print("Please answer with 'y' or 'n'.")


class EmpathyEngine:
    """
    Makes replies warmer, more human, and emotionally aware.
    Uses Groq LLM if available (GROQ_API_KEY set). Falls back to templates otherwise.
    """

    POSITIVE_WORDS = {"great", "good", "awesome", "nice", "thanks", "thank you", "cool", "love", "yay", "happy"}
    NEGATIVE_WORDS = {"bad", "sad", "angry", "upset", "tired", "stressed", "stress", "hate", "frustrated", "worried", "confused"}
    GREET_WORDS = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}
    BYE_WORDS = {"bye", "goodbye", "see you", "later", "cya"}

    TRAVEL_KEYWORDS = {
        "plan", "trip", "travel", "vacation", "holiday",
        "route", "map", "navigate", "nav", "directions",
        "weather", "forecast", "temperature",
        "email", "mail", "send", "meet", "meeting", "google meet", "calendar", "schedule"
    }

    def __init__(self):
        self.client = None
        self.use_llm = False
        if Groq is not None:
            key = "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"
            if key.startswith("gsk_"):
                try:
                    self.client = Groq(api_key=key)
                    self.use_llm = True
                except Exception:
                    self.use_llm = False

    def analyze_user(self, user_text: str) -> Dict[str, str]:
        t = (user_text or "").lower()
        mood = "neutral"
        if any(w in t for w in self.NEGATIVE_WORDS):
            mood = "negative"
        elif any(w in t for w in self.POSITIVE_WORDS):
            mood = "positive"

        is_greeting = any(w in t for w in self.GREET_WORDS)
        is_farewell = any(w in t for w in self.BYE_WORDS)

        # Off-topic: message has no travel/task keywords and isn't greeting/farewell
        off_topic = (not any(k in t for k in self.TRAVEL_KEYWORDS)) and not is_greeting and not is_farewell

        return {
            "mood": mood,
            "greeting": "yes" if is_greeting else "no",
            "farewell": "yes" if is_farewell else "no",
            "off_topic": "yes" if off_topic else "no",
        }

    def humanize(self, system_reply: str, user_text: str, context_hint: str = "") -> str:
        """
        Rewrite the system reply into a warmer, human-like response.
        Uses LLM if available; otherwise applies simple templates.
        """
        analysis = self.analyze_user(user_text)
        mood = analysis["mood"]
        off_topic = analysis["off_topic"] == "yes"
        greeting = analysis["greeting"] == "yes"
        farewell = analysis["farewell"] == "yes"

        if greeting and not system_reply.strip():
            return "Hey there! How can I help with your trip today? I can plan, map routes, check weather, send emails, or book a Meet."

        if farewell:
            return "Take care! If you need help planning or checking anything for your trip later, I’m here."

        if off_topic:
            # Gently guide back to supported tasks
            guide = (
                "I’m here to help with your travel plans: I can plan a trip, find routes with live navigation, "
                "check weather around a date, send emails, book a Google Meet, or show your calendar."
            )
            if system_reply.strip():
                base = system_reply.strip()
            else:
                base = "Let’s focus on your trip so I can be most helpful."
            # Blend
            sys_text = f"{base}\n\n{guide}\nWhat would you like to do?"
        else:
            sys_text = system_reply.strip()

        if not self.use_llm:
            # Template-based softening
            prefix = ""
            if mood == "negative":
                prefix = "I’m sorry you’re feeling that way. "
            elif mood == "positive":
                prefix = "Awesome! "
            # Keep it crisp and warm
            return (prefix + sys_text).strip()

        # LLM-based rewrite
        try:
            prompt = (
                "You are a warm, concise, emotionally intelligent travel assistant. "
                "Rewrite the assistant message below to sound supportive, natural, and human—like a friendly expert. "
                "Do not invent facts. Keep any links, dates, or commands intact. "
                "If the user seems off-topic, gently guide them toward what you can do: "
                "plan trip, route + live navigation, weather, email, meet, calendar.\n\n"
                f"User message: {user_text}\n"
                f"Context hint: {context_hint}\n"
                f"Assistant message to rewrite:\n{sys_text}\n\n"
                "Output only the improved assistant message in plain text."
            )
            resp = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=400,
            )
            text = (resp.choices[0].message.content or "").strip()
            return text if text else sys_text
        except Exception:
            # Fallback if LLM errors
            return sys_text


class IntentParser:
    def parse(self, text: str) -> str:
        t = (text or "").strip().lower()
        if re.search(r"\b(quit|exit|bye|close)\b", t): return "exit"
        if re.search(r"\b(help|what can you do|menu|options)\b", t): return "help"
        if re.match(r"^(set\s*city|setcity)\b", t): return "set_city"
        if re.search(r"\b(current\s*city|where am i|my location)\b", t): return "current_city"
        if re.search(r"\b(plan|trip|travel|vacation|holiday)\b", t): return "plan_trip"
        if re.search(r"\b(route|directions|navigate|nav|map)\b", t): return "route"
        if re.search(r"\b(weather|forecast|temperature)\b", t): return "weather"
        if re.search(r"\b(email|mail|send mail)\b", t): return "email"
        if re.search(r"\b(meet|meeting|google meet|appointment|call)\b", t): return "meet"
        if re.search(r"\b(calendar|schedule|my events|commitments)\b", t): return "calendar"
        return "unknown"


class ChatAgent:
    def __init__(
        self,
        map_service: Optional[MapService] = None,
        weather_service: Optional[WeatherService] = None,
        calendar_service: Optional[CalendarService] = None,
        booking_service: Optional[BookingService] = None,
        communication_service: Optional[CommunicationService] = None,
        trip_agent: Optional[TripPlannerAgent] = None,
    ):
        # Reuse passed services (from main.py) or create new ones
        self.map = map_service or MapService()
        if hasattr(self.map, "set_fixed_city"):
            self.map.set_fixed_city(self.map.get_current_city("Karur"))

        self.weather = weather_service or WeatherService()
        self.calendar = calendar_service or CalendarService()
        self.booking = booking_service or BookingService()
        self.comm = communication_service or CommunicationService()
        self.tp = trip_agent or TripPlannerAgent(self.map, self.weather, self.calendar, self.booking)

        self.intent_parser = IntentParser()
        self.empathy = EmpathyEngine()

        self.chat_history: List[Tuple[str, str]] = []  # [(user, agent)]
        self.last_plan: Optional[dict] = None
        self.user_name: Optional[str] = None

    # ---------- Humanized output ----------

    def say(self, raw_reply: str, user_text: str = "", context: str = ""):
        final = self.empathy.humanize(raw_reply, user_text, context)
        print(f"Agent: {final}")
        if user_text:
            self.chat_history.append((user_text, final))
        else:
            # system message
            self.chat_history.append(("", final))

    # ---------- Core chat loop ----------

    def run(self):
        self._greet()
        while True:
            msg = ask("\nYou: ")
            intent = self.intent_parser.parse(msg)

            if intent == "exit":
                self.say("Take care! I’m here whenever you need trip help again.", msg)
                break
            elif intent == "help":
                self._help(msg)
            elif intent == "set_city":
                self._set_city_flow(msg)
            elif intent == "current_city":
                self.say(f"Your current city (fixed) is: {self.map.get_current_city('Karur')}", msg)
            elif intent == "plan_trip":
                self._plan_trip_flow(msg)
            elif intent == "route":
                self._route_flow(msg)
            elif intent == "weather":
                self._weather_flow(msg)
            elif intent == "email":
                self._email_flow(msg)
            elif intent == "meet":
                self._meet_flow(msg)
            elif intent == "calendar":
                self._calendar_flow(msg)
            else:
                self._nudge_to_tasks(msg)

    # ---------- Warm greetings & help ----------

    def _greet(self):
        current_city = self.map.get_current_city("Karur")
        self.say(
            f"Hi! I’m your travel buddy. I detect your city as {current_city}. "
            "Tell me what you’d like to do—plan a trip, get directions with a live Google Maps link, "
            "check weather around a date, send an email, book a Google Meet, or view your calendar.",
            ""
        )

    def _help(self, user_msg: str):
        self.say(
            "- Plan a trip (I’ll ask for dates, days, and type)\n"
            "- Route (I’ll get steps and a live Google Maps link)\n"
            "- Weather (I’ll show ±5 days around a date)\n"
            "- Email (I’ll craft a message from your subject and send it)\n"
            "- Meet (I’ll create a Google Meet and email the link)\n"
            "- Calendar (I’ll show your events)\n"
            "- setcity Karur (fix your textual current city)\n"
            "- exit",
            user_msg
        )

    def _nudge_to_tasks(self, user_msg: str):
        self.say(
            "I might have misunderstood. I can help plan trips, find routes (with live nav), "
            "check weather, send emails, schedule Google Meets, or show your calendar. "
            "What would you like to do?",
            user_msg
        )

    # ---------- Flows (humanized) ----------

    def _set_city_flow(self, msg: str):
        m = re.match(r"^(?:set\s*city|setcity)\s+(.+)$", msg.strip(), re.I)
        if m:
            city = m.group(1).strip()
        else:
            city = ask("Agent: Which city should I set as your current location? ").strip()
        if not city:
            self.say("No problem—your current city stays the same.", msg)
            return
        if hasattr(self.map, "set_fixed_city"):
            self.map.set_fixed_city(city)
        self.say(f"Got it. I’ll treat your current city as {self.map.get_current_city('Karur')}.", msg)

    def _ask_name_once(self, user_msg: str):
        if self.user_name:
            return
        nm = ask("Agent: What’s your name? ").strip()
        if nm:
            self.user_name = nm
            self.say(f"Nice to meet you, {self.user_name}! Let’s get this sorted.", user_msg)
        else:
            self.user_name = "You"
            self.say("No worries, I’ll just call you ‘You’ for now. 😊", user_msg)

    def _plan_trip_flow(self, user_msg: str):
        self._ask_name_once(user_msg)

        # Trip type
        while True:
            cat = ask("Agent: Which vibe are you going for (hill / beach / spiritual)? ").strip().lower()
            if cat in ("hill", "beach", "spiritual"):
                break
            self.say("Please type one of: hill, beach, spiritual.", user_msg)

        # Start date
        while True:
            d = ask(f"Agent: Start date (DD-MM-YY) [>= {fmt_date(date.today())}]: ").strip()
            try:
                sd = parse_date(d)
                if sd < date.today():
                    self.say("Let’s pick a start date that’s today or later.", user_msg)
                    continue
                break
            except Exception:
                self.say("Hmm, that date format didn’t parse. Try DD-MM-YY (like 20-07-26).", user_msg)

        # Days
        while True:
            days_str = ask("Agent: How many days do you have in mind (1–10)? ").strip()
            if days_str.isdigit() and 1 <= int(days_str) <= 10:
                num_days = int(days_str)
                break
            self.say("Please enter a number from 1 to 10 so I can plan realistically.", user_msg)

        home_city = self.map.get_current_city("Karur")
        user_id = (self.user_name or "You").strip().lower().replace(" ", "_")
        start_date = sd

        tries = 0
        while not self.calendar.is_date_available(user_id, start_date) and tries < 30:
            existing = self.calendar.get_commitment(user_id, start_date)
            self.say(f"You already have '{existing}' on {fmt_date(start_date)}.", user_msg)
            alt = self.calendar.suggest_alternative_date(user_id, start_date)
            if alt:
                use_alt = ask_yes_no(f"Would you like to shift to {fmt_date(alt)}?")
                if use_alt:
                    start_date = alt
                    break
                else:
                    start_date = start_date + timedelta(days=1)
            tries += 1

        plan = self.tp.plan_trip(self.user_name or "You", home_city, start_date, num_days, cat)
        self.last_plan = plan

        # Build summary
        lines = []
        lines.append(f"Here’s your plan to {plan['destination']} ({plan.get('trip_category', 'Trip')}):")
        lines.append(f"- From: {plan['home_city']}")
        lines.append(f"- Dates: {fmt_date(plan['start_date'])} → {fmt_date(plan['end_date'])} ({plan['num_days']} days)")
        if plan.get("distance_km"):
            lines.append(f"- Distance (approx): {plan['distance_km']} km")
        if plan.get("avg_summer_temp") is not None:
            lines.append(f"- Avg temp: {plan['avg_summer_temp']}°C")
        lines.append("")
        info = plan["destination_info"]
        if info.get("description"):
            lines.append("Quick intro:")
            lines.append(info["description"])
            lines.append("")
        lines.append("Route steps:")
        for s in plan["route_steps"]:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("Weather highlights:")
        for d in plan["weather_forecast"]:
            lines.append(f"- {fmt_date(d['date'])}: High {d['high']}°C, Low {d['low']}°C – {d['description']}")

        self.say("\n".join(lines), user_msg)

        if ask_yes_no("Agent: Want me to open a live Google Maps route from your city to the destination?"):
            link = self.map.get_live_nav_link(plan["home_city"], plan["destination"])
            self.say(f"Here you go:\n{link}", user_msg)
            try:
                webbrowser.open(link)
            except Exception:
                pass

        if ask_yes_no("Agent: Would you like me to book tickets now?"):
            while True:
                mode = ask("Agent: Type 'flight' or 'train': ").strip().lower()
                if mode in ("flight", "train"):
                    booking = self.tp.book_trip(self.user_name or "You", home_city, plan, mode)
                    self.calendar.add_trip(
                        user_id,
                        plan["start_date"],
                        plan["end_date"],
                        f"Trip to {plan['destination']} by {mode}",
                    )
                    self.say(
                        f"All set! Booking {booking['booking_id']} confirmed. "
                        f"{booking['origin']} → {booking['destination']} on {fmt_date(booking['date'])}.",
                        user_msg
                    )
                    break
                self.say("Please type either 'flight' or 'train'.", user_msg)

        if ask_yes_no("Agent: Do you want me to notify someone (email or Google Meet)?"):
            self._notify_menu(self.user_name or "You", plan, user_msg)

    def _notify_menu(self, your_name: str, plan: dict, user_msg: str):
        while True:
            self.say("How should I notify them? 1) Meet  2) Email  3) Back", user_msg)
            ch = ask("Select 1/2/3: ").strip()
            if ch == "1":
                self._meet_flow(user_msg, your_name=your_name)
            elif ch == "2":
                self._email_flow(user_msg, your_name=your_name, plan=plan)
            elif ch == "3":
                break
            else:
                self.say("Please pick 1, 2, or 3.", user_msg)

    def _route_flow(self, user_msg: str):
        origin = self.map.get_current_city("Karur")
        dest = ask("Agent: Where do you want to go? ").strip()
        if not dest:
            self.say("No worries—tell me a destination when you’re ready.", user_msg)
            return
        steps = self.map.get_route(origin, dest)
        lines = [f"Directions from {origin} to {dest}:"]
        lines += [f"- {s}" for s in steps]
        self.say("\n".join(lines), user_msg)
        if ask_yes_no("Agent: Open a live Google Maps route with this origin and destination?"):
            link = self.map.get_live_nav_link(origin, dest)
            self.say(f"Here’s the live link:\n{link}", user_msg)
            try:
                webbrowser.open(link)
            except Exception:
                pass

    def _weather_flow(self, user_msg: str):
        current_city = self.map.get_current_city("Karur")
        place = ask(f"Agent: Which place? (Enter to use current: {current_city}) ").strip() or current_city
        while True:
            d = ask(f"Agent: Reference date (DD-MM-YY) [>= {fmt_date(date.today())}]: ").strip()
            try:
                ref = parse_date(d)
                break
            except Exception:
                self.say("That didn’t parse—Use DD-MM-YY like 20-07-26.", user_msg)

        days_before = 5
        days_after = 5
        try:
            series = self.weather.get_weather_range(place, ref, days_before, days_after)
        except AttributeError:
            start = ref - timedelta(days=days_before)
            total = days_before + 1 + days_after
            series = self.weather.get_weather_forecast(place, start, total)
            series.sort(key=lambda x: x["date"])

        lines = [f"Weather around {place} for 5 days before and after {fmt_date(ref)}:"]
        lines.append("\nPrevious 5 days:")
        for it in series:
            if it["date"] < ref:
                lines.append(f"- {fmt_date(it['date'])}: High {it['high']}°C, Low {it['low']}°C – {it['description']}")
        lines.append("\nSelected date:")
        for it in series:
            if it["date"] == ref:
                lines.append(f"= {fmt_date(it['date'])}: High {it['high']}°C, Low {it['low']}°C – {it['description']}")
                break
        lines.append("\nNext 5 days:")
        for it in series:
            if it["date"] > ref:
                lines.append(f"- {fmt_date(it['date'])}: High {it['high']}°C, Low {it['low']}°C – {it['description']}")
        self.say("\n".join(lines), user_msg)

    def _email_flow(self, user_msg: str, your_name: Optional[str] = None, plan: Optional[dict] = None):
        if not your_name:
            self._ask_name_once(user_msg)
            your_name = self.user_name or "You"
        other_name = ask("Agent: Receiver name? ").strip()
        other_email = ask("Agent: Receiver email? ").strip()
        subject = ask("Agent: Email subject (one line)? ").strip()
        if not (other_name and other_email and subject):
            self.say("I need a name, email, and subject to send it properly.", user_msg)
            return

        default_msg = self.comm.generate_default_email(your_name, other_name, subject, plan)
        self.say(
            "Here’s a draft I wrote—tell me if you’d like to tweak anything:\n\n"
            + default_msg,
            user_msg
        )
        if ask_yes_no("Agent: Send this now?"):
            final_msg = default_msg
        else:
            final_msg = ask("Agent: Type your final message (single paragraph): ").strip() or default_msg

        email = self.comm.send_email(your_name, other_name, other_email, subject, final_msg, enhance=False)
        self.say(f"Sent! Subject: {email['subject']}", user_msg)

    def _meet_flow(self, user_msg: str, your_name: Optional[str] = None):
        if not your_name:
            self._ask_name_once(user_msg)
            your_name = self.user_name or "You"
        other_name = ask("Agent: Participant name? ").strip()
        other_email = ask("Agent: Participant email? ").strip()
        subj = ask("Agent: Meeting subject? ").strip()
        while True:
            d = ask(f"Agent: Meeting date (DD-MM-YY) [>= {fmt_date(date.today())}]: ").strip()
            try:
                md = parse_date(d)
                if md < date.today():
                    self.say("Let’s pick today or later so it’s valid.", user_msg)
                    continue
                break
            except Exception:
                self.say("Use DD-MM-YY (e.g., 20-07-26).", user_msg)
        while True:
            t = ask("Agent: Meeting time (HH:MM 24-hour): ").strip()
            try:
                mt = datetime.strptime(t, "%H:%M").time()
                break
            except Exception:
                self.say("Use HH:MM (e.g., 14:30).", user_msg)
        when = datetime.combine(md, mt)

        meet = self.comm.book_google_meet(your_name, other_name, other_email, subj, when)
        self.say(
            f"Done! Meet on {when.strftime('%d-%m-%y %H:%M')}.\nLink: {meet['link']}",
            user_msg
        )

    def _calendar_flow(self, user_msg: str):
        nm = ask("Agent: Your name (to read your calendar)? ").strip()
        if not nm:
            self.say("No problem—try again when you’re ready.", user_msg)
            return
        user_id = nm.strip().lower().replace(" ", "_")
        entries = self.calendar.get_all_commitments(user_id)
        if not entries:
            self.say("Your calendar looks clear for now.", user_msg)
            return
        lines = [f"Upcoming for {nm}:"]
        for d in sorted(entries.keys()):
            lines.append(f"- {fmt_date(d)}: {entries[d]}")
        self.say("\n".join(lines), user_msg)


if __name__ == "__main__":
    try:
        ChatAgent().run()
    except KeyboardInterrupt:
        print("\nAgent: Bye!")
        sys.exit(0)