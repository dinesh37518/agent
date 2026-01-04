from datetime import timedelta


class TripPlannerAgent:
    def __init__(self, map_service, weather_service, calendar_service, booking_service):
        self.map_service = map_service
        self.weather_service = weather_service
        self.calendar_service = calendar_service
        self.booking_service = booking_service

    def plan_trip(
        self, user_name, home_city, start_date, num_days, trip_category
    ):
        destinations = self.weather_service.get_cool_destinations_near(
            home_city, place_type=trip_category
        )
        if not destinations:
            raise ValueError("No destinations available near this city.")

        chosen = destinations[0]
        destination_name = chosen["name"]

        route_steps = self.map_service.get_route(home_city, destination_name)

        weather_forecast = self.weather_service.get_weather_forecast(
            destination_name, start_date, num_days
        )

        daily_plan = []
        for i in range(num_days):
            day_number = i + 1
            day_forecast = weather_forecast[i]

            if trip_category == "hill":
                if day_number == 1:
                    activity = (
                        f"Travel from {home_city} to {destination_name} and check into your hotel. "
                        f"Evening walk around the hill station and enjoy the cool weather."
                    )
                elif day_number == num_days:
                    activity = (
                        f"Morning sightseeing around {destination_name}, then return journey back to {home_city}."
                    )
                else:
                    activity = (
                        f"Full day sightseeing in and around {destination_name} "
                        f"(viewpoints, tea/coffee estates, parks, and local markets)."
                    )
            elif trip_category == "beach":
                if day_number == 1:
                    activity = (
                        f"Travel from {home_city} to {destination_name} and check into your hotel. "
                        f"Evening at the beach to watch the sunset."
                    )
                elif day_number == num_days:
                    activity = (
                        f"Relax at the beach in the morning, last-minute shopping, "
                        f"and then return journey back to {home_city}."
                    )
                else:
                    activity = (
                        f"Enjoy the beach: swimming (if allowed), water sports (if available), "
                        f"and local seafood around {destination_name}."
                    )
            elif trip_category == "spiritual":
                if day_number == 1:
                    activity = (
                        f"Travel from {home_city} to {destination_name} and check into your accommodation. "
                        f"Evening darshan / visit to the main temple."
                    )
                elif day_number == num_days:
                    activity = (
                        f"Final visit to the temple or ghat in {destination_name}, "
                        f"and then return journey back to {home_city}."
                    )
                else:
                    activity = (
                        f"Visit important temples/ashrams/ghats in and around {destination_name}, "
                        f"attend aarti or meditation programs."
                    )
            else:
                # Fallback generic activities
                if day_number == 1:
                    activity = (
                        f"Travel from {home_city} to {destination_name} and check into your hotel. "
                        f"Evening walk around the town."
                    )
                elif day_number == num_days:
                    activity = (
                        f"Local sightseeing in {destination_name} and return journey back to {home_city}."
                    )
                else:
                    activity = (
                        f"Full day sightseeing in and around {destination_name} "
                        f"(local attractions and markets)."
                    )

            daily_plan.append(
                {
                    "day": day_number,
                    "date": day_forecast["date"],
                    "activity": activity,
                    "weather": day_forecast,
                }
            )

        end_date = start_date + timedelta(days=num_days - 1)

        place_info = self.map_service.describe_place(destination_name)

        plan = {
            "user_name": user_name,
            "home_city": home_city,
            "destination": destination_name,
            "start_date": start_date,
            "end_date": end_date,
            "num_days": num_days,
            "route_steps": route_steps,
            "weather_forecast": weather_forecast,
            "daily_plan": daily_plan,
            "destination_info": place_info,
            "avg_summer_temp": chosen.get("avg_summer_temp"),
            "distance_km": chosen.get("distance_km"),
            "trip_category": trip_category,
        }

        return plan

    def book_trip(self, user_name, home_city, plan, transport_mode):
        mode = transport_mode.strip().lower()
        if mode == "flight":
            booking = self.booking_service.book_flight(
                user_name, home_city, plan["destination"], plan["start_date"]
            )
        elif mode == "train":
            booking = self.booking_service.book_train(
                user_name, home_city, plan["destination"], plan["start_date"]
            )
        else:
            raise ValueError("Unsupported transport mode. Use 'flight' or 'train'.")
        return booking