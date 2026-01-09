# ===============================
# File: trip_planner/chat_agent.py
# (Chat agent that can reuse the same services created in main.py)
# Run standalone (optional):  python3 trip_planner/chat_agent.py
# ===============================

import re
import sys
import webbrowser
from datetime import datetime, date, timedelta

from ai_agent import TripPlannerAgent
from map_service import MapService
from weather_service import WeatherService
from calendar_service import CalendarService
from booking_service import BookingService
from communication_service import CommunicationService


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
        map_service: MapService | None = None,
        weather_service: WeatherService | None = None,
        calendar_service: CalendarService | None = None,
        booking_service: BookingService | None = None,
        communication_service: CommunicationService | None = None,
        trip_agent: TripPlannerAgent | None = None,
    ):
        # Reuse passed services (from main.py) or create new ones
        self.map = map_service or MapService()
        if hasattr(self.map, "set_fixed_city"):
            # Keep textual current location stable
            self.map.set_fixed_city(self.map.get_current_city("Karur"))

        self.weather = weather_service or WeatherService()
        self.calendar = calendar_service or CalendarService()
        self.booking = booking_service or BookingService()
        self.comm = communication_service or CommunicationService()
        self.tp = trip_agent or TripPlannerAgent(self.map, self.weather, self.calendar, self.booking)

        self.intent_parser = IntentParser()
        self.last_plan = None

    def run(self):
        self._greet()
        while True:
            msg = ask("\nYou: ")
            intent = self.intent_parser.parse(msg)
            if intent == "exit":
                print("Agent: Goodbye! 👋")
                break
            elif intent == "help":
                self._help()
            elif intent == "set_city":
                self._set_city_flow(msg)
            elif intent == "current_city":
                print(f"Agent: Your current city (fixed): {self.map.get_current_city('Karur')}")
            elif intent == "plan_trip":
                self._plan_trip_flow()
            elif intent == "route":
                self._route_flow()
            elif intent == "weather":
                self._weather_flow()
            elif intent == "email":
                self._email_flow()
            elif intent == "meet":
                self._meet_flow()
            elif intent == "calendar":
                self._calendar_flow()
            else:
                print("Agent: I can help you with these:")
                self._help()

    def _greet(self):
        current_city = self.map.get_current_city("Karur")
        print("=======================================")
        print(" AI Trip Planner – Chat Agent")
        print("=======================================")
        print(f"Agent: Hi! I’m your travel assistant. I detect your city as: {current_city}.")
        print("Agent: Tell me what you want to do (e.g., 'plan a trip', 'route to Ooty', 'weather Ooty', 'send email', 'book a meet', 'view calendar').")
        print("Agent: Type 'help' to see options, or 'exit' to quit.")

    def _help(self):
        print("- plan a trip (I’ll ask details and create an itinerary)")
        print("- route (I’ll get directions and a live nav link)")
        print("- weather (I’ll show ±5 days around your date)")
        print("- email (I’ll generate a message from your subject and send it)")
        print("- meet (I’ll create a Google Meet and email the link)")
        print("- calendar (I’ll show your events)")
        print("- setcity Karur (fix your textual current city)")
        print("- exit")

    def _set_city_flow(self, msg: str):
        m = re.match(r"^(?:set\s*city|setcity)\s+(.+)$", msg.strip(), re.I)
        if m:
            city = m.group(1).strip()
        else:
            city = ask("Agent: Enter the city to set as your current location: ").strip()
        if not city:
            print("Agent: City not changed.")
            return
        if hasattr(self.map, "set_fixed_city"):
            self.map.set_fixed_city(city)
        print(f"Agent: Current city set to: {self.map.get_current_city('Karur')}")

    def _plan_trip_flow(self):
        print("Agent: Let’s plan your trip.")
        name = ask("Agent: What’s your name? ")
        if not name:
            print("Agent: I need your name.")
            return

        while True:
            cat = ask("Agent: Trip type (hill / beach / spiritual)? ").strip().lower()
            if cat in ("hill", "beach", "spiritual"):
                break
            print("Agent: Please type one of: hill, beach, spiritual.")

        while True:
            d = ask(f"Agent: Start date (DD-MM-YY) [>= {fmt_date(date.today())}]: ").strip()
            try:
                sd = parse_date(d)
                if sd < date.today():
                    print("Agent: Start date must be today or later.")
                    continue
                break
            except Exception:
                print("Agent: Invalid date. Use DD-MM-YY.")

        while True:
            days_str = ask("Agent: How many days (1-10)? ").strip()
            if days_str.isdigit() and 1 <= int(days_str) <= 10:
                num_days = int(days_str)
                break
            print("Agent: Enter a number 1–10.")

        home_city = self.map.get_current_city("Karur")
        user_id = name.strip().lower().replace(" ", "_")
        start_date = sd

        tries = 0
        while not self.calendar.is_date_available(user_id, start_date) and tries < 30:
            existing = self.calendar.get_commitment(user_id, start_date)
            print(f"Agent: You already have '{existing}' on {fmt_date(start_date)}.")
            alt = self.calendar.suggest_alternative_date(user_id, start_date)
            if alt:
                use_alt = ask_yes_no(f"Agent: Next available is {fmt_date(alt)}. Use this date?")
                if use_alt:
                    start_date = alt
                    break
                else:
                    start_date = start_date + timedelta(days=1)
            tries += 1

        plan = self.tp.plan_trip(name, home_city, start_date, num_days, cat)
        self.last_plan = plan

        print("\n================ Plan Summary ================")
        print(f"Traveler: {plan['user_name']}")
        print(f"From: {plan['home_city']}")
        print(f"Trip type: {plan.get('trip_category', 'Trip')}")
        print(f"Destination: {plan['destination']}")
        if plan.get("distance_km"):
            print(f"Approx distance: {plan['distance_km']} km")
        if plan.get("avg_summer_temp") is not None:
            print(f"Avg temp: {plan['avg_summer_temp']}°C")
        print(f"Dates: {fmt_date(plan['start_date'])} to {fmt_date(plan['end_date'])} ({plan['num_days']} days)")
        print("")
        info = plan["destination_info"]
        if info.get("description"):
            print("About destination:")
            print(info["description"])
            print("")
        if info.get("history"):
            print("History:")
            print(info["history"])
            print("")
        if info.get("culture"):
            print("Culture:")
            print(info["culture"])
            print("")
        highs = info.get("highlights") or []
        if highs:
            print("Highlights:")
            for h in highs:
                print(f"- {h}")
            print("")
        print("Route steps:")
        for s in plan["route_steps"]:
            print(f"- {s}")
        print("")
        print("Weather forecast:")
        for d in plan["weather_forecast"]:
            print(f"- {fmt_date(d['date'])}: High {d['high']}°C, Low {d['low']}°C – {d['description']}")
        print("==============================================")

        if ask_yes_no("Agent: Open live navigation from your city to the destination?"):
            link = self.map.get_live_nav_link(plan["home_city"], plan["destination"])
            print(f"Agent: Live nav link:\n{link}")
            try:
                webbrowser.open(link)
            except Exception:
                pass

        if ask_yes_no("Agent: Do you want to book tickets now?"):
            while True:
                mode = ask("Agent: Type 'flight' or 'train': ").strip().lower()
                if mode in ("flight", "train"):
                    booking = self.tp.book_trip(name, home_city, plan, mode)
                    self.calendar.add_trip(
                        user_id,
                        plan["start_date"],
                        plan["end_date"],
                        f"Trip to {plan['destination']} by {mode}",
                    )
                    print("\nBooking details:")
                    print(f"  Type: {booking['type']}")
                    print(f"  Booking ID: {booking['booking_id']}")
                    print(f"  Route: {booking['origin']} -> {booking['destination']}")
                    print(f"  Travel date: {fmt_date(booking['date'])}")
                    print(f"  Status: {booking['status']}")
                    print(f"  Note: {booking['details']}")
                    break
                print("Agent: Please type 'flight' or 'train'.")

        if ask_yes_no("Agent: Do you want to notify someone (email or Google Meet)?"):
            self._notify_menu(name, plan)

    def _notify_menu(self, your_name, plan):
        while True:
            print("\nAgent: Choose notification method:")
            print("1) Google Meet")
            print("2) Email")
            print("3) Back")
            ch = ask("Select 1/2/3: ")
            if ch == "1":
                self._meet_flow(your_name=your_name)
            elif ch == "2":
                self._email_flow(your_name=your_name, plan=plan)
            elif ch == "3":
                break
            else:
                print("Agent: Please select 1, 2, or 3.")

    def _route_flow(self):
        origin = self.map.get_current_city("Karur")
        dest = ask("Agent: Destination? ").strip()
        if not dest:
            print("Agent: Please provide a destination.")
            return
        steps = self.map.get_route(origin, dest)
        print(f"Agent: Route from {origin} to {dest}:")
        for s in steps:
            print(f"- {s}")
        if ask_yes_no("Agent: Open live navigation with fixed origin?"):
            link = self.map.get_live_nav_link(origin, dest)
            print(f"Agent: {link}")
            try:
                webbrowser.open(link)
            except Exception:
                pass

    def _weather_flow(self):
        current_city = self.map.get_current_city("Karur")
        place = ask(f"Agent: Place (leave empty for current: {current_city}): ").strip() or current_city
        while True:
            d = ask(f"Agent: Reference date (DD-MM-YY) [>= {fmt_date(date.today())}]: ").strip()
            try:
                ref = parse_date(d)
                break
            except Exception:
                print("Agent: Invalid date. Use DD-MM-YY.")
        days_before = 5
        days_after = 5
        try:
            series = self.weather.get_weather_range(place, ref, days_before, days_after)
        except AttributeError:
            start = ref - timedelta(days=days_before)
            total = days_before + 1 + days_after
            series = self.weather.get_weather_forecast(place, start, total)
            series.sort(key=lambda x: x["date"])
        print(f"Agent: Weather around {place} for 5 days before and after {fmt_date(ref)}:")
        print("Previous 5 days:")
        for it in series:
            if it["date"] < ref:
                print(f"- {fmt_date(it['date'])}: High {it['high']}°C, Low {it['low']}°C – {it['description']}")
        print("Selected date:")
        for it in series:
            if it["date"] == ref:
                print(f"= {fmt_date(it['date'])}: High {it['high']}°C, Low {it['low']}°C – {it['description']}")
                break
        print("Next 5 days:")
        for it in series:
            if it["date"] > ref:
                print(f"- {fmt_date(it['date'])}: High {it['high']}°C, Low {it['low']}°C – {it['description']}")

    def _email_flow(self, your_name=None, plan=None):
        if not your_name:
            your_name = ask("Agent: Your name? ").strip()
            if not your_name:
                print("Agent: I need your name.")
                return
        other_name = ask("Agent: Receiver name? ").strip()
        other_email = ask("Agent: Receiver email? ").strip()
        subject = ask("Agent: Email subject (one line)? ").strip()
        if not (other_name and other_email and subject):
            print("Agent: Missing name/email/subject.")
            return

        default_msg = self.comm.generate_default_email(your_name, other_name, subject, plan)
        print("\nAgent: AI-generated message:")
        print("--------------------------------")
        print(default_msg)
        print("--------------------------------")
        use_default = ask_yes_no("Agent: Send this message?")
        final_msg = default_msg if use_default else ask("Agent: Type your custom message (single paragraph): ").strip() or default_msg

        email = self.comm.send_email(your_name, other_name, other_email, subject, final_msg, enhance=False)
        print("Agent: Email sent.")
        print(f"  Subject: {email['subject']}")
        print(f"  Status: {email['status']}")

    def _meet_flow(self, your_name=None):
        if not your_name:
            your_name = ask("Agent: Your name? ").strip()
            if not your_name:
                print("Agent: I need your name.")
                return
        other_name = ask("Agent: Participant name? ").strip()
        other_email = ask("Agent: Participant email? ").strip()
        subj = ask("Agent: Meeting subject? ").strip()
        while True:
            d = ask(f"Agent: Meeting date (DD-MM-YY) [>= {fmt_date(date.today())}]: ").strip()
            try:
                md = parse_date(d)
                if md < date.today():
                    print("Agent: Please choose today or later.")
                    continue
                break
            except Exception:
                print("Agent: Invalid date. Use DD-MM-YY.")
        while True:
            t = ask("Agent: Meeting time (HH:MM 24-hour): ").strip()
            try:
                mt = datetime.strptime(t, "%H:%M").time()
                break
            except Exception:
                print("Agent: Invalid time. Use HH:MM.")
        when = datetime.combine(md, mt)

        meet = self.comm.book_google_meet(your_name, other_name, other_email, subj, when)
        print("\nAgent: Meet created.")
        print(f"  Subject: {meet['subject']}")
        print(f"  Date & time: {when.strftime('%d-%m-%y %H:%M')}")
        print(f"  Link: {meet['link']}")
        print(f"  Status: {meet['status']}")

    def _calendar_flow(self):
        name = ask("Agent: Your name (to view calendar)? ").strip()
        if not name:
            print("Agent: I need your name.")
            return
        user_id = name.strip().lower().replace(" ", "_")
        entries = self.calendar.get_all_commitments(user_id)
        if not entries:
            print("Agent: Your calendar has no entries.")
            return
        print(f"Agent: Upcoming for {name}:")
        for d in sorted(entries.keys()):
            print(f"- {fmt_date(d)}: {entries[d]}")


if __name__ == "__main__":
    try:
        ChatAgent().run()
    except KeyboardInterrupt:
        print("\nAgent: Bye!")
        sys.exit(0)