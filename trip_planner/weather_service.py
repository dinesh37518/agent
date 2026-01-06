# ================================
# File: trip_planner/weather_service.py
# (Updated: added get_weather_range to fetch 5 days before and after a date)
# ================================

import os
import requests
from datetime import date, datetime, timedelta


class _WeatherAPIHelper:
    def __init__(self):
        self.owm_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()

    def _fetch_openweather(self, city_name, start_date, days):
        if not self.owm_key:
            return None

        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city_name, "appid": self.owm_key, "units": "metric"}
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code != 200:
                return None
            data = r.json()
            by_date = {}
            for item in data.get("list", []):
                dt_utc = item.get("dt_txt")
                if not dt_utc:
                    ts = item.get("dt")
                    if ts:
                        dt = datetime.utcfromtimestamp(ts)
                    else:
                        continue
                else:
                    dt = datetime.strptime(dt_utc, "%Y-%m-%d %H:%M:%S")
                dkey = dt.date()
                temp = item.get("main", {}).get("temp")
                desc = ""
                wx = item.get("weather") or []
                if wx:
                    desc = wx[0].get("description", "").strip()
                if dkey not in by_date:
                    by_date[dkey] = {"temps": [], "descs": []}
                if temp is not None:
                    by_date[dkey]["temps"].append(float(temp))
                if desc:
                    by_date[dkey]["descs"].append(desc)

            out = []
            for i in range(days):
                day = start_date + timedelta(days=i)
                bucket = by_date.get(day)
                if not bucket:
                    out.append(None)
                    continue
                temps = bucket["temps"]
                descs = bucket["descs"]
                if temps:
                    d_high = int(round(max(temps)))
                    d_low = int(round(min(temps)))
                else:
                    d_high = None
                    d_low = None
                d_desc = descs[0] if descs else "Partly cloudy"
                out.append(
                    {
                        "date": day,
                        "high": d_high if d_high is not None else 26,
                        "low": d_low if d_low is not None else 20,
                        "description": d_desc.capitalize(),
                    }
                )
            return out
        except Exception:
            return None

    @staticmethod
    def _geocode_open_meteo(city_name):
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {"name": city_name, "count": 1}
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                return None
            data = r.json()
            results = data.get("results") or []
            if not results:
                return None
            lat = results[0].get("latitude")
            lon = results[0].get("longitude")
            return (lat, lon) if (lat is not None and lon is not None) else None
        except Exception:
            return None

    @staticmethod
    def _wx_code_to_text(code):
        mapping = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return mapping.get(code, "Pleasant")

    def _fetch_open_meteo(self, city_name, start_date, days):
        latlon = self._geocode_open_meteo(city_name)
        if not latlon:
            return None
        lat, lon = latlon
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = (start_date + timedelta(days=days - 1)).strftime("%Y-%m-%d")

        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone": "auto",
                "start_date": start_str,
                "end_date": end_str,
            }
            r = requests.get(url, params=params, timeout=20)
            if r.status_code != 200:
                return None
            data = r.json()
            daily = data.get("daily") or {}
            dates = daily.get("time") or []
            tmax = daily.get("temperature_2m_max") or []
            tmin = daily.get("temperature_2m_min") or []
            codes = daily.get("weathercode") or []

            out = []
            for i in range(min(days, len(dates))):
                d = datetime.strptime(dates[i], "%Y-%m-%d").date()
                high = int(round(tmax[i])) if i < len(tmax) and tmax[i] is not None else 26
                low = int(round(tmin[i])) if i < len(tmin) and tmin[i] is not None else 20
                desc = self._wx_code_to_text(codes[i]) if i < len(codes) else "Pleasant"
                out.append({"date": d, "high": high, "low": low, "description": desc})
            if len(out) < days:
                while len(out) < days:
                    d = start_date + timedelta(days=len(out))
                    out.append({"date": d, "high": 26, "low": 20, "description": "Pleasant"})
            return out
        except Exception:
            return None

    def get_forecast(self, city_name, start_date, days):
        ow = self._fetch_openweather(city_name, start_date, days)
        if ow:
            return ow
        om = self._fetch_open_meteo(city_name, start_date, days)
        if om:
            return om
        return None


class WeatherService:
    def __init__(self):
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

        self._api = _WeatherAPIHelper()

    def get_cool_destinations_near(self, home_city, max_temp=30, place_type="hill"):
        key = home_city.strip().lower()
        base_list = self.nearby_destinations.get(key)
        if base_list is None:
            base_list = self.nearby_destinations["default"]

        if place_type:
            filtered = [d for d in base_list if d.get("category") == place_type]
            if filtered:
                base_list = filtered
            else:
                default_filtered = [
                    d for d in self.nearby_destinations["default"] if d.get("category") == place_type
                ]
                if default_filtered:
                    base_list = default_filtered

        results = []
        for d in base_list:
            dest_name = d["name"]
            city_key = dest_name.lower()
            city_info = self.city_weather.get(city_key, {})
            temp = city_info.get("avg_summer_temp", 28)
            if place_type == "hill" and temp > max_temp:
                continue
            results.append(
                {"name": dest_name, "distance_km": d.get("distance_km"), "avg_summer_temp": temp}
            )
        if not results:
            for d in base_list:
                dest_name = d["name"]
                city_key = dest_name.lower()
                city_info = self.city_weather.get(city_key, {})
                temp = city_info.get("avg_summer_temp", 30)
                results.append(
                    {"name": dest_name, "distance_km": d.get("distance_km"), "avg_summer_temp": temp}
                )
        results.sort(key=lambda x: x["avg_summer_temp"])
        return results

    def _synthetic_forecast(self, city_name, start_date, days):
        city_key = city_name.strip().lower()
        city_info = self.city_weather.get(city_key, {})
        base_temp = city_info.get("avg_summer_temp", 26)
        place_type = city_info.get("type", "city")

        forecasts = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            high = base_temp + ((i % 3) - 1)
            low = high - 6
            if place_type == "hill":
                description = "Cool and pleasant with clear views."
            elif place_type == "coastal":
                description = "Warm with sea breeze; evenings are pleasant near the water."
            elif base_temp <= 30:
                description = "Warm but comfortable; good for sightseeing."
            else:
                description = "Hot daytime, better to explore in mornings and evenings."
            forecasts.append({"date": d, "high": int(high), "low": int(low), "description": description})
        return forecasts

    def get_weather_forecast(self, city_name, start_date, days):
        real = self._api.get_forecast(city_name, start_date, days)
        if real:
            if len(real) < days:
                pad_needed = days - len(real)
                tail_start = (real[-1]["date"] + timedelta(days=1)) if real else start_date
                for i in range(pad_needed):
                    d = tail_start + timedelta(days=i)
                    real.append({"date": d, "high": 26, "low": 20, "description": "Pleasant"})
            return real[:days]
        return self._synthetic_forecast(city_name, start_date, days)

    # NEW: range around a reference date (e.g., 5 days before and after)
    def get_weather_range(self, city_name, center_date, days_before=5, days_after=5):
        start = center_date - timedelta(days=days_before)
        total = days_before + 1 + days_after
        data = self.get_weather_forecast(city_name, start, total)
        # Ensure sorted by date
        data.sort(key=lambda x: x["date"])
        return data