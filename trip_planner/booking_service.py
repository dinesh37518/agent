# File: trip_planner/booking_service.py

from datetime import datetime
from communication_service import CommunicationService


class BookingService:
    def __init__(self):
        # Use the same communication service for notifications
        self.comm_service = CommunicationService()

    def _generate_booking_id(self, prefix):
        now = datetime.now()
        return f"{prefix}{now.strftime('%Y%m%d%H%M%S')}"

    def _save_booking(self, booking):
        # Save booking to a simple text file (simulated booking database)
        try:
            with open("bookings.txt", "a", encoding="utf-8") as f:
                line = (
                    f"{booking['type']} | {booking['booking_id']} | "
                    f"{booking['user_name']} | {booking['origin']} -> {booking['destination']} "
                    f"| {booking['date'].isoformat()} | {booking['status']}\n"
                )
                f.write(line)
        except Exception:
            # Ignore file errors; booking is still considered created
            pass

    def book_flight(self, user_name, origin, destination, travel_date):
        booking = {
            "type": "FLIGHT",
            "booking_id": self._generate_booking_id("FL"),
            "user_name": user_name,
            "origin": origin,
            "destination": destination,
            "date": travel_date,
            "status": "CONFIRMED",
            "details": "Flight ticket booked (simulated). Contact airline to choose exact flight.",
        }
        self._save_booking(booking)

        # Notify you about this flight booking
        subject = "Flight booking confirmed"
        message = (
            f"Flight booking {booking['booking_id']} confirmed for {user_name}.\n"
            f"Route: {origin} -> {destination}\n"
            f"Travel date: {booking['date'].isoformat()}\n"
            f"Status: {booking['status']}"
        )
        self.comm_service.notify_me(subject, message)

        return booking

    def book_train(self, user_name, origin, destination, travel_date):
        booking = {
            "type": "TRAIN",
            "booking_id": self._generate_booking_id("TR"),
            "user_name": user_name,
            "origin": origin,
            "destination": destination,
            "date": travel_date,
            "status": "CONFIRMED",
            "details": "Train ticket booked (simulated). Contact railway portal to choose exact train.",
        }
        self._save_booking(booking)

        # Notify you about this train booking
        subject = "Train booking confirmed"
        message = (
            f"Train booking {booking['booking_id']} confirmed for {user_name}.\n"
            f"Route: {origin} -> {destination}\n"
            f"Travel date: {booking['date'].isoformat()}\n"
            f"Status: {booking['status']}"
        )
        self.comm_service.notify_me(subject, message)

        return booking