from datetime import timedelta


class WeatherService:
    def __init__(self):
        # Average summer temperatures and basic type of place
        self.city_weather = {
            "chennai": {"avg_summer_temp": 38, "type": "coastal"},
            "bangalore": {"avg_summer_temp": 30, "type": "city"},
            "hyderabad": {"avg_summer_temp": 36, "type": "city"},
            "mumbai": {"avg_summer_temp": 34, "type": "coastal"},
            "delhi": {"avg_summer_temp": 40, "type": "city"},
            "ooty": {"avg_summer_temp": 22, "type": "hill"},
            "kodaikanal": {"avg_summer_temp": 23, "type": "hill"},
            "munnar": {"avg_summer_temp": 24, "type": "hill"},
            "coorg": {"avg_summer_temp": 25, "type": "hill"},
            "manali": {"avg_summer_temp": 20, "type": "hill"},
            "shimla": {"avg_summer_temp": 21, "type": "hill"},
            "mahabaleshwar": {"avg_summer_temp": 24, "type": "hill"},
            # extra beach/spiritual places
            "pondicherry": {"avg_summer_temp": 32, "type": "coastal"},
            "mahabalipuram": {"avg_summer_temp": 33, "type": "coastal"},
            "rameswaram": {"avg_summer_temp": 34, "type": "coastal"},
            "gokarna": {"avg_summer_temp": 31, "type": "coastal"},
            "goa": {"avg_summer_temp": 32, "type": "coastal"},
            "vizag": {"avg_summer_temp": 32, "type": "coastal"},
            "lonavala": {"avg_summer_temp": 26, "type": "hill"},
            "rishikesh": {"avg_summer_temp": 30, "type": "city"},
            "haridwar": {"avg_summer_temp": 32, "type": "city"},
            "tirupati": {"avg_summer_temp": 34, "type": "city"},
            "shirdi": {"avg_summer_temp": 34, "type": "city"},
            "srisailam": {"avg_summer_temp": 33, "type": "city"},
        }

        # Nearby destinations categorized by type
        self.nearby_destinations = {
            "chennai": [
                {"name": "Ooty", "distance_km": 550, "category": "hill"},
                {"name": "Kodaikanal", "distance_km": 530, "category": "hill"},
                {"name": "Munnar", "distance_km": 580, "category": "hill"},
                {"name": "Pondicherry", "distance_km": 160, "category": "beach"},
                {"name": "Mahabalipuram", "distance_km": 60, "category": "beach"},
                {"name": "Rameswaram", "distance_km": 560, "category": "spiritual"},
            ],
            "bangalore": [
                {"name": "Ooty", "distance_km": 270, "category": "hill"},
                {"name": "Coorg", "distance_km": 260, "category": "hill"},
                {"name": "Kodaikanal", "distance_km": 465, "category": "hill"},
                {"name": "Gokarna", "distance_km": 480, "category": "beach"},
                {"name": "Pondicherry", "distance_km": 320, "category": "beach"},
                {"name": "Tirupati", "distance_km": 250, "category": "spiritual"},
            ],
            "hyderabad": [
                {"name": "Ooty", "distance_km": 850, "category": "hill"},
                {"name": "Munnar", "distance_km": 1000, "category": "hill"},
                {"name": "Vizag", "distance_km": 620, "category": "beach"},
                {"name": "Srisailam", "distance_km": 230, "category": "spiritual"},
            ],
            "mumbai": [
                {"name": "Mahabaleshwar", "distance_km": 260, "category": "hill"},
                {"name": "Lonavala", "distance_km": 85, "category": "hill"},
                {"name": "Goa", "distance_km": 580, "category": "beach"},
                {"name": "Shirdi", "distance_km": 240, "category": "spiritual"},
            ],
            "delhi": [
                {"name": "Manali", "distance_km": 540, "category": "hill"},
                {"name": "Shimla", "distance_km": 345, "category": "hill"},
                {"name": "Rishikesh", "distance_km": 240, "category": "spiritual"},
                {"name": "Haridwar", "distance_km": 220, "category": "spiritual"},
            ],
            "default": [
                {"name": "Ooty", "distance_km": 600, "category": "hill"},
                {"name": "Manali", "distance_km": 800, "category": "hill"},
                {"name": "Munnar", "distance_km": 700, "category": "hill"},
                {"name": "Goa", "distance_km": 900, "category": "beach"},
                {"name": "Rishikesh", "distance_km": 900, "category": "spiritual"},
            ],
        }

    def get_cool_destinations_near(self, home_city, max_temp=30, place_type="hill"):
        key = home_city.strip().lower()
        base_list = self.nearby_destinations.get(key)
        if base_list is None:
            base_list = self.nearby_destinations["default"]

        # Filter by requested category (hill / beach / spiritual)
        if place_type:
            filtered = [d for d in base_list if d.get("category") == place_type]
            if filtered:
                base_list = filtered
            else:
                # fall back to default list for that category
                default_filtered = [
                    d
                    for d in self.nearby_destinations["default"]
                    if d.get("category") == place_type
                ]
                if default_filtered:
                    base_list = default_filtered

        results = []
        for d in base_list:
            dest_name = d["name"]
            city_key = dest_name.lower()
            city_info = self.city_weather.get(city_key, {})
            temp = city_info.get("avg_summer_temp", 28)

            # For hill stations, try to keep temperature under max_temp
            if place_type == "hill" and temp > max_temp:
                continue

            results.append(
                {
                    "name": dest_name,
                    "distance_km": d.get("distance_km"),
                    "avg_summer_temp": temp,
                }
            )

        # If nothing after filter, just return base_list with temps
        if not results:
            for d in base_list:
                dest_name = d["name"]
                city_key = dest_name.lower()
                city_info = self.city_weather.get(city_key, {})
                temp = city_info.get("avg_summer_temp", 30)
                results.append(
                    {
                        "name": dest_name,
                        "distance_km": d.get("distance_km"),
                        "avg_summer_temp": temp,
                    }
                )

        results.sort(key=lambda x: x["avg_summer_temp"])
        return results

    def get_weather_forecast(self, city_name, start_date, days):
        city_key = city_name.strip().lower()
        city_info = self.city_weather.get(city_key, {})
        base_temp = city_info.get("avg_summer_temp", 26)
        place_type = city_info.get("type", "city")

        forecasts = []
        for i in range(days):
            d = start_date + timedelta(days=i)

            # Simple temperature variation pattern
            high = base_temp + ((i % 3) - 1)  # -1, 0, +1 around base
            low = high - 6

            if place_type == "hill":
                description = "Cool and pleasant with clear views."
            elif place_type == "coastal":
                description = "Warm with sea breeze; evenings are pleasant near the water."
            elif base_temp <= 30:
                description = "Warm but comfortable; good for sightseeing."
            else:
                description = (
                    "Hot daytime, better to explore in mornings and evenings."
                )

            forecasts.append(
                {
                    "date": d,
                    "high": int(high),
                    "low": int(low),
                    "description": description,
                }
            )

        return forecasts
    