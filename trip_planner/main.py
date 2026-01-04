# ===========================
# File: trip_planner/main.py
# (Updated: email content is generated AUTOMATICALLY from one-line subject)
# ===========================

from datetime import date, datetime

from ai_agent import TripPlannerAgent
from map_service import MapService
from weather_service import WeatherService
from calendar_service import CalendarService
from booking_service import BookingService
from communication_service import CommunicationService


def format_date(d):
    """Return date as DD-MM-YY (all 2 characters)."""
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
    home_city = input_non_empty("Enter your home city: ")
    start_date = ask_for_date("Enter the start date for your trip (DD-MM-YY): ")

    user_id = user_name.strip().lower().replace(" ", "_")

    # Calendar check for conflicts
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

    num_days = ask_for_int(
        "How many days do you want your trip to be (1-10)? ", 1, 10
    )

    trip_category = ask_trip_category()

    plan = agent.plan_trip(
        user_name, home_city, start_date, num_days, trip_category
    )

    trip_type_text = {
        "hill": "Hill station",
        "beach": "Beach",
        "spiritual": "Spiritual place",
    }.get(plan.get("trip_category"), "Trip")

    print("\n=== Trip Plan Summary ===")
    print(f"Traveler: {plan['user_name']}")
    print(f"From: {plan['home_city']}")
    print(f"Trip type: {trip_type_text}")
    print(f"Destination: {plan['destination']}")
    if plan.get("distance_km"):
        print(f"Approximate distance: {plan['distance_km']} km")
    if plan.get("avg_summer_temp") is not None:
        print(f"Average temperature there: {plan['avg_summer_temp']}°C")
    print(
        f"Trip dates: {format_date(plan['start_date'])} to {format_date(plan['end_date'])}"
    )
    print(f"Number of days: {plan['num_days']}")

    # Destination info
    info = plan["destination_info"]
    print("\nAbout the destination:")
    print(info["description"])
    if info.get("highlights"):
        print("Highlights:")
        for h in info["highlights"]:
            print(f"  - {h}")

    # Map as trip guider (route)
    print("\nRoute (map trip guide):")
    print(f"Route from {plan['home_city']} to {plan['destination']}:")
    for step in plan["route_steps"]:
        print(f"  - {step}")

    # Weather at destination
    print("\nWeather forecast at destination:")
    for day in plan["weather_forecast"]:
        print(
            f"  - {format_date(day['date'])}: High {day['high']}°C, "
            f"Low {day['low']}°C – {day['description']}"
        )

    # Daily itinerary
    print("\nDaily Itinerary:")
    for day in plan["daily_plan"]:
        d_str = format_date(day["date"])
        print(f"Day {day['day']} ({d_str}): {day['activity']}")
        w = day["weather"]
        print(
            f"    Weather: High {w['high']}°C, Low {w['low']}°C – {w['description']}"
        )

    # Booking travel (flight/train)
    if ask_yes_no("\nDo you want to book tickets for this trip now?"):
        while True:
            mode = input(
                "How do you want to travel? Type 'flight' or 'train': "
            ).strip().lower()
            if mode in ("flight", "train"):
                booking = agent.book_trip(user_name, home_city, plan, mode)
                calendar_service.add_trip(
                    user_id,
                    plan["start_date"],
                    plan["end_date"],
                    f"Trip to {plan['destination']} by {mode}",
                )

                print("\nBooking details:")
                print(f"  Type: {booking['type']}")
                print(f"  Booking ID: {booking['booking_id']}")
                print(
                    f"  Route: {booking['origin']} -> {booking['destination']}"
                )
                print(f"  Travel date: {format_date(booking['date'])}")
                print(f"  Status: {booking['status']}")
                print(f"  Note: {booking['details']}")
                break
            else:
                print("Please enter 'flight' or 'train'.")
    else:
        print("\nTrip plan saved (not booked). You can book later from the main menu.")

    # Optional: inform someone else about this trip
    if ask_yes_no(
        "\nDo you want to inform someone about this trip (Google Meet or email)?"
    ):
        communication_menu(communication_service, user_name, plan)


def communication_menu(communication_service, your_name=None, plan=None):
    """
    Communication menu.
    Email content is AUTOMATICALLY generated from the one-line subject (no manual typing).
    """
    print("\n=== Communication Service ===")
    if your_name is None:
        your_name = input_non_empty("Enter your name: ")

    while True:
        print("\nHow do you want to inform them?")
        print("1. Book a Google Meet appointment")
        print("2. Send an email (auto-generated from subject)")
        print("3. Back to previous menu")
        choice = input("Enter 1, 2, or 3: ").strip()

        if choice == "1":
            other_name = input_non_empty("Enter the other person's name: ")
            other_email = input_non_empty("Enter their email address: ")
            subject = input_non_empty("Enter meeting subject (one line): ")
            meeting_date = ask_for_date("Enter meeting date (DD-MM-YY): ")
            meeting_time = ask_for_time("Enter meeting time (HH:MM, 24-hour): ")
            meeting_datetime = datetime.combine(meeting_date, meeting_time)

            meet = communication_service.book_google_meet(
                your_name,
                other_name,
                other_email,
                subject,
                meeting_datetime,
            )

            print("\nGoogle Meet appointment created (simulated/real):")
            print(f"  Organizer: {meet['organizer']}")
            print(f"  Participant: {other_name} <{other_email}>")
            print(f"  Subject: {meet['subject']}")
            print("  Date & time: " + meeting_datetime.strftime("%d-%m-%y %H:%M"))
            print(f"  Meet link: {meet['link']}")
            print(f"  Status: {meet['status']}")

        elif choice == "2":
            other_name = input_non_empty("Enter the other person's name: ")
            other_email = input_non_empty("Enter their email address: ")
            subject = input_non_empty("Enter email subject (one line): ")

            # AUTO-GENERATE full, meaningful, formatted content from subject (+ plan if available)
            auto_message = communication_service.generate_default_email(
                your_name, other_name, subject, plan
            )

            # Send immediately with the AI-generated message (no extra prompts)
            email = communication_service.send_email(
                your_name,
                other_name,
                other_email,
                subject,
                auto_message,
                enhance=False,  # already generated and formatted
            )

            print("\nEmail sent (simulated/real):")
            print(f"  From: {email['from']['name']} <{email['from']['email']}>")
            print(f"  To: {email['to']['name']} <{email['to']['email']}>")
            print(f"  Subject: {email['subject']}")
            print("  Body preview:")
            print("--------------------------------")
            print(auto_message)
            print("--------------------------------")
            print(f"  Status: {email['status']}")

        elif choice == "3":
            break
        else:
            print("Please enter 1, 2, or 3.")


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
            print(f"\nPlace: {info['name']}")
            print(info["description"])
            if info.get("highlights"):
                print("Highlights:")
                for h in info["highlights"]:
                    print(f"  - {h}")
        elif choice == "2":
            origin = input_non_empty("Enter origin: ")
            destination = input_non_empty("Enter destination: ")
            steps = map_service.get_route(origin, destination)
            print(f"\nRoute from {origin} to {destination}:")
            for step in steps:
                print(f"  - {step}")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")


def check_weather_only(weather_service):
    print("\n=== Weather Service (Standalone) ===")
    place = input_non_empty(
        "Enter city, hill-station, beach, or spiritual place name: "
    )
    start = date.today()
    days = 3
    forecast = weather_service.get_weather_forecast(place, start, days)
    print(f"\nWeather forecast for {place} for the next {days} days:")
    for day in forecast:
        print(
            f"  - {format_date(day['date'])}: High {day['high']}°C, "
            f"Low {day['low']}°C – {day['description']}"
        )


def use_communication_only(communication_service):
    """
    Standalone menu option for communication service,
    without planning a trip first.
    """
    communication_menu(communication_service, your_name=None, plan=None)


def main():
    map_service = MapService()
    weather_service = WeatherService()
    calendar_service = CalendarService()
    booking_service = BookingService()
    communication_service = CommunicationService()
    agent = TripPlannerAgent(
        map_service, weather_service, calendar_service, booking_service
    )

    while True:
        print("\n==============================")
        print("AI Trip Planner")
        print("==============================")
        print("1. Plan a trip")
        print("2. View my calendar")
        print("3. Use map only")
        print("4. Check weather only")
        print("5. Communication service (Meet / Email)")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            run_trip_planner(agent, calendar_service, communication_service)
        elif choice == "2":
            view_calendar(calendar_service)
        elif choice == "3":
            use_map_only(map_service)
        elif choice == "4":
            check_weather_only(weather_service)
        elif choice == "5":
            use_communication_only(communication_service)
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select a number from 1 to 6.")


if __name__ == "__main__":
    main()