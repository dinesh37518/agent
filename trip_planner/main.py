# ===========================
# File: trip_planner/main.py
# (Integrated: adds "0. Chat agent" option that reuses the same services)
# ===========================

from datetime import date, datetime

from ai_agent import TripPlannerAgent
from map_service import MapService
from weather_service import WeatherService
from calendar_service import CalendarService
from booking_service import BookingService
from communication_service import CommunicationService
from chat_agent import ChatAgent  # <-- add this import


def format_date(d):
    return d.strftime("%d-%m-%y")


def input_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def ask_yes_no(prompt):
    while True:
        choice = input(prompt + " (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def ask_for_date(prompt):
    while True:
        text = input(prompt).strip()
        try:
            d = datetime.strptime(text, "%d-%m-%y").date()
            if d < date.today():
                print("Please enter a date that is today or in the future.")
                continue
            return d
        except ValueError:
            print("Invalid date format. Use DD-MM-YY (for example, 15-06-26).")


def ask_for_time(prompt):
    while True:
        text = input(prompt).strip()
        try:
            t = datetime.strptime(text, "%H:%M").time()
            return t
        except ValueError:
            print("Invalid time format. Use HH:MM in 24-hour format (for example, 14:30).")


def ask_for_int(prompt, min_value, max_value):
    while True:
        text = input(prompt).strip()
        if not text.isdigit():
            print("Please enter a number.")
            continue
        value = int(text)
        if value < min_value or value > max_value:
            print(f"Please enter a number between {min_value} and {max_value}.")
            continue
        return value


def ask_trip_category():
    print("\nWhat kind of place do you want to visit?")
    print("1. Hill station (cool mountains)")
    print("2. Beach")
    print("3. Spiritual / pilgrimage place")
    while True:
        choice = input("Enter 1, 2, or 3: ").strip()
        if choice == "1":
            return "hill"
        elif choice == "2":
            return "beach"
        elif choice == "3":
            return "spiritual"
        else:
            print("Please enter 1, 2, or 3.")


def run_trip_planner(agent, calendar_service, communication_service):
    print("\n=== Trip Planner ===")
    user_name = input_non_empty("Enter your name: ")

    home_city = agent.map_service.get_current_city(default="Karur")
    print(f"Using current location: {home_city}")

    start_date = ask_for_date("Enter the start date for your trip (DD-MM-YY): ")

    user_id = user_name.strip().lower().replace(" ", "_")

    while not calendar_service.is_date_available(user_id, start_date):
        existing = calendar_service.get_commitment(user_id, start_date)
        print(f"\nYou already have '{existing}' on {format_date(start_date)}.")
        alt = calendar_service.suggest_alternative_date(user_id, start_date)
        if alt:
            use_alt = ask_yes_no(
                f"Suggested next available date is {format_date(alt)}. Do you want to use this date?"
            )
            if use_alt:
                start_date = alt
                break
        start_date = ask_for_date("Please enter a different start date (DD-MM-YY): ")

    num_days = ask_for_int("How many days do you want your trip to be (1-10)? ", 1, 10)
    trip_category = ask_trip_category()

    plan = agent.plan_trip(user_name, home_city, start_date, num_days, trip_category)

    trip_type_text = {"hill": "Hill station", "beach": "Beach", "spiritual": "Spiritual place"}.get(
        plan.get("trip_category"), "Trip"
    )

    print("\n=== Trip Plan Summary ===")
    print(f"Traveler: {plan['user_name']}")
    print(f"From: {plan['home_city']}")
    print(f"Trip type: {trip_type_text}")
    print(f"Destination: {plan['destination']}")
    if plan.get("distance_km"):
        print(f"Approximate distance: {plan['distance_km']} km")
    if plan.get("avg_summer_temp") is not None:
        print(f"Average temperature there: {plan['avg_summer_temp']}°C")
    print(f"Trip dates: {format_date(plan['start_date'])} to {format_date(plan['end_date'])}")
    print(f"Number of days: {plan['num_days']}")

    info = plan["destination_info"]
    print("\nAbout the destination:")
    if info.get("description"):
        print(info["description"])
    highs = info.get("highlights") or []
    if highs:
        print("\nHighlights:")
        for h in highs:
            print(f"  - {h}")

    print("\nRoute (map trip guide):")
    print(f"Route from {plan['home_city']} to {plan['destination']}:")
    for step in plan["route_steps"]:
        print(f"  - {step}")

    if ask_yes_no("\nOpen live navigation in Google Maps with fixed origin (Karur)?"):
        link = agent.map_service.get_live_nav_link(plan["home_city"], plan["destination"])
        print(f"\nLive navigation link:\n{link}")
        try:
            import webbrowser
            webbrowser.open(link)
        except Exception:
            pass

    print("\nWeather forecast at destination:")
    for day in plan["weather_forecast"]:
        print(f"  - {format_date(day['date'])}: High {day['high']}°C, Low {day['low']}°C – {day['description']}")

    print("\nDaily Itinerary:")
    for day in plan["daily_plan"]:
        d_str = format_date(day["date"])
        print(f"Day {day['day']} ({d_str}): {day['activity']}")

    if ask_yes_no("\nDo you want to book tickets for this trip now?"):
        while True:
            mode = input("How do you want to travel? Type 'flight' or 'train': ").strip().lower()
            if mode in ("flight", "train"):
                booking = agent.book_trip(user_name, home_city, plan, mode)
                calendar_service.add_trip(
                    user_id, plan["start_date"], plan["end_date"], f"Trip to {plan['destination']} by {mode}"
                )
                print("\nBooking details:")
                print(f"  Type: {booking['type']}")
                print(f"  Booking ID: {booking['booking_id']}")
                print(f"  Route: {booking['origin']} -> {booking['destination']}")
                print(f"  Travel date: {format_date(booking['date'])}")
                print(f"  Status: {booking['status']}")
                print(f"  Note: {booking['details']}")
                break
            else:
                print("Please enter 'flight' or 'train'.")
    else:
        print("\nTrip plan saved (not booked). You can book later from the main menu.")

    if ask_yes_no("\nDo you want to inform someone about this trip (Google Meet or email)?"):
        use_communication_only(communication_service)


def view_calendar(calendar_service):
    print("\n=== View My Calendar ===")
    user_name = input_non_empty("Enter your name: ")
    user_id = user_name.strip().lower().replace(" ", "_")
    commitments = calendar_service.get_all_commitments(user_id)
    if not commitments:
        print("No commitments or trips found for you.")
        return
    print(f"\nUpcoming commitments for {user_name}:")
    for d in sorted(commitments.keys()):
        print(f"  - {format_date(d)}: {commitments[d]}")


def use_map_only(map_service):
    while True:
        print("\n=== Map Service (Standalone) ===")
        print("1. Get information about a place")
        print("2. Get a simple route between two places")
        print("3. Back to main menu")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            place = input_non_empty("Enter place name: ")
            info = map_service.describe_place(place)
            print(f"\nPlace: {info.get('name', place)}")
            if info.get("description"):
                print("\nDescription:")
                print(info["description"])
        elif choice == "2":
            origin = map_service.get_current_city(default="Karur")
            destination = input_non_empty("Enter destination: ")
            steps = map_service.get_route(origin, destination)
            print(f"\nRoute from {origin} to {destination}:")
            for step in steps:
                print(f"  - {step}")
            link = map_service.get_live_nav_link(origin, destination)
            print(f"\nLive navigation link:\n{link}")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")


def check_weather_only(weather_service, map_service):
    print("\n=== Weather Service (Standalone) ===")
    current_city = map_service.get_current_city(default="Karur")
    print("Choose location:")
    print("1. Another place")
    print(f"2. Current location ({current_city})")
    while True:
        opt = input("Enter 1 or 2: ").strip()
        if opt in ("1", "2"):
            break
        print("Please enter 1 or 2.")
    if opt == "1":
        place = input_non_empty("Enter city / hill-station / beach / spiritual place name: ")
    else:
        place = current_city
    ref_date = ask_for_date("Enter reference date (DD-MM-YY): ")
    days_before = 5
    days_after = 5
    series = weather_service.get_weather_range(place, ref_date, days_before, days_after)
    print(f"\nWeather around {place} for 5 days before and 5 days after {format_date(ref_date)}:")
    print("\nPrevious 5 days:")
    for item in series:
        if item["date"] < ref_date:
            print(f"  - {format_date(item['date'])}: High {item['high']}°C, Low {item['low']}°C – {item['description']}")
    print("\nSelected date:")
    for item in series:
        if item["date"] == ref_date:
            print(f"  = {format_date(item['date'])}: High {item['high']}°C, Low {item['low']}°C – {item['description']}")
            break
    print("\nNext 5 days:")
    for item in series:
        if item["date"] > ref_date:
            print(f"  - {format_date(item['date'])}: High {item['high']}°C, Low {item['low']}°C – {item['description']}")


def use_communication_only(communication_service):
    print("\n=== Notify Someone ===")
    while True:
        print("1. Google Meet")
        print("2. Email")
        print("3. Back")
        ch = input("Select 1/2/3: ").strip()
        if ch == "1":
            other_name = input_non_empty("Enter the other person's name: ")
            other_email = input_non_empty("Enter their email address: ")
            subject = input_non_empty("Enter meeting subject: ")
            d = ask_for_date("Enter meeting date (DD-MM-YY): ")
            while True:
                t = input("Enter meeting time (HH:MM, 24-hour): ").strip()
                try:
                    mt = datetime.strptime(t, "%H:%M").time()
                    break
                except ValueError:
                    print("Invalid time. Use HH:MM.")
            when = datetime.combine(d, mt)
            # Quick wrapper (you can import comm here, but pass via ChatAgent in chat)
            comm = CommunicationService()
            meet = comm.book_google_meet("You", other_name, other_email, subject, when)
            print("\nGoogle Meet appointment created:")
            print(f"  Subject: {meet['subject']}")
            print(f"  Date & time: {when.strftime('%d-%m-%y %H:%M')}")
            print(f"  Link: {meet['link']}")
            print(f"  Status: {meet['status']}")
        elif ch == "2":
            other_name = input_non_empty("Enter the other person's name: ")
            other_email = input_non_empty("Enter their email address: ")
            subject = input_non_empty("Enter email subject: ")
            comm = CommunicationService()
            default_message = comm.generate_default_email("You", other_name, subject, None)
            print("\nDefault message:")
            print("--------------------------------")
            print(default_message)
            print("--------------------------------")
            if ask_yes_no("Send this message?"):
                message = default_message
            else:
                message = input_non_empty("Type your message: ")
            email = comm.send_email("You", other_name, other_email, subject, message, enhance=False)
            print("\nEmail sent:")
            print(f"  Subject: {email['subject']}")
            print(f"  Status: {email['status']}")
        elif ch == "3":
            break
        else:
            print("Please select 1, 2, or 3.")


def main():
    map_service = MapService()
    if hasattr(map_service, "set_fixed_city"):
        map_service.set_fixed_city("Karur")

    weather_service = WeatherService()
    calendar_service = CalendarService()
    booking_service = BookingService()
    communication_service = CommunicationService()
    agent = TripPlannerAgent(map_service, weather_service, calendar_service, booking_service)

    while True:
        print("\n==============================")
        print("AI Trip Planner")
        print("==============================")
        print("0. Chat agent (conversational mode)")  # <-- integrated chat
        print("1. Plan a trip")
        print("2. View my calendar")
        print("3. Use map only")
        print("4. Check weather only")
        print("5. Communication service (Meet / Email)")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            ChatAgent(
                map_service=map_service,
                weather_service=weather_service,
                calendar_service=calendar_service,
                booking_service=booking_service,
                communication_service=communication_service,
                trip_agent=agent,
            ).run()
        elif choice == "1":
            run_trip_planner(agent, calendar_service, communication_service)
        elif choice == "2":
            view_calendar(calendar_service)
        elif choice == "3":
            use_map_only(map_service)
        elif choice == "4":
            check_weather_only(weather_service, map_service)
        elif choice == "5":
            use_communication_only(communication_service)
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select a number from 0 to 6.")


if __name__ == "__main__":
    main()