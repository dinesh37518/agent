# ================================
# File: trip_planner/communication_service.py
# Requires:
#   - pip install google-generativeai
#   - export GEMINI_API_KEY="your_gemini_key"
# Optional (for real email sending):
#   - Gmail 2FA + App Password
# ================================

from datetime import datetime
import os
import smtplib
import ssl

# Google Gemini (LLM) for improved email content
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# =======================================================
# EMAIL CONFIGURATION: CHANGE THESE TO YOUR REAL DETAILS
# =======================================================
# 1) Set this to True to send real emails via Gmail SMTP.
#    Set to False to only simulate (print + log to file).
USE_REAL_EMAIL = True

# 2) YOUR Gmail address (the account that sends the emails)
FROM_EMAIL = "your_gmail@gmail.com"        # <-- PUT YOUR GMAIL HERE

# 3) YOUR Gmail APP PASSWORD (NOT your normal Gmail password)
#    Turn on 2‑Step Verification in Google, then create an App Password.
FROM_PASSWORD = "your_16_char_app_password"  # <-- PUT APP PASSWORD HERE

# 4) Your own name and your own email (for notifications)
MY_NAME = "Your Name"                        # <-- YOUR NAME
MY_EMAIL = "your_gmail@gmail.com"            # usually same as FROM_EMAIL
# =======================================================

# =======================================================
# GEMINI (Google AI) CONFIG
# =======================================================
# Use Gemini to improve/generate email text if available.
USE_GEMINI = True
GEMINI_MODEL = "gemini-1.5-flash"  # fast and capable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
# =======================================================


class CommunicationService:
    def __init__(self):
        self.my_name = MY_NAME
        self.my_email = MY_EMAIL

        # Init Gemini
        self._ai_enabled = False
        self._gemini_model = None
        if USE_GEMINI and genai is not None and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self._gemini_model = genai.GenerativeModel(GEMINI_MODEL)
                self._ai_enabled = True
            except Exception as e:
                print(f"[Gemini init error] {e}")
        elif USE_GEMINI and genai is None:
            print("[Gemini disabled] Package not installed. Run: pip install google-generativeai")
        elif USE_GEMINI and not GEMINI_API_KEY:
            print("[Gemini disabled] GEMINI_API_KEY not set. Using template fallback.")

    def _fmt_date(self, d):
        return d.strftime("%d-%m-%y")

    def _save_record(self, text):
        try:
            with open("communications.txt", "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass

    def _send_email(self, to_email, subject, message):
        # Log every attempt
        log_text = (
            f"EMAIL_OUT | From: {FROM_EMAIL} | To: {to_email} | "
            f"Subject: {subject} | At: {datetime.now().isoformat(timespec='seconds')} | "
            f"Body: {message.replace(chr(10), ' ')}"
        )
        self._save_record(log_text)

        if not USE_REAL_EMAIL:
            print(f"\n[Email simulated] To: {to_email} | Subject: {subject}\n")
            return False

        email_text = (
            f"From: {FROM_EMAIL}\r\n"
            f"To: {to_email}\r\n"
            f"Subject: {subject}\r\n"
            "\r\n"
            f"{message}"
        )

        # Try STARTTLS on 587 first
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(FROM_EMAIL, FROM_PASSWORD)
                server.sendmail(FROM_EMAIL, [to_email], email_text)
            print(f"\n[Real email sent] To: {to_email} | Subject: {subject} (via 587 STARTTLS)\n")
            return True
        except Exception as e1:
            print(f"[SMTP 587 STARTTLS failed] {e1}")

        # Fallback to SSL on 465
        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=30) as server:
                server.login(FROM_EMAIL, FROM_PASSWORD)
                server.sendmail(FROM_EMAIL, [to_email], email_text)
            print(f"\n[Real email sent] To: {to_email} | Subject: {subject} (via 465 SSL)\n")
            return True
        except Exception as e2:
            print(f"[SMTP 465 SSL failed] {e2}")
            return False

    def _improve_with_ai(self, text, your_name, other_name):
        """
        Try to improve the email text with Gemini.
        If not available, use a friendly template around the text.
        """
        if self._ai_enabled and self._gemini_model is not None:
            try:
                prompt = (
                    "You are an email writing assistant. Rewrite the text to be clear, "
                    "polite, and professional. Keep trip details, dates, and places. "
                    "Friendly tone. Output only the improved email body.\n\n"
                    f"Sender: {your_name}\n"
                    f"Receiver: {other_name}\n\n"
                    f"Original:\n{text}"
                )
                resp = self._gemini_model.generate_content(prompt)
                improved = (getattr(resp, "text", None) or "").strip()
                if improved:
                    return improved
            except Exception as e:
                print(f"[Gemini error] {e}")

        # Fallback: nice template (free, no AI)
        return (
            f"Hi {other_name},\n\n"
            f"{text.strip()}\n\n"
            f"Best regards,\n{your_name}\n"
        )

    def generate_default_email(self, your_name, other_name, subject, plan=None):
        """
        Generate a default email body using Gemini based on the subject and optional trip plan.
        Falls back to a clean template if AI is not available.
        """
        # Build context text for the model or fallback
        if plan:
            trip_category = plan.get("trip_category", "trip")
            context = (
                f"Subject: {subject}\n"
                f"{your_name} is planning a {trip_category} to {plan['destination']} "
                f"from {self._fmt_date(plan['start_date'])} to {self._fmt_date(plan['end_date'])}."
            )
        else:
            context = f"Subject: {subject}\n{your_name} wants to communicate regarding this subject."

        # AI path
        if self._ai_enabled and self._gemini_model is not None:
            try:
                prompt = (
                    "Write a short, friendly, and professional email body (5-7 lines) that references the given subject. "
                    "If trip details are provided, include them naturally. Address the receiver by name and sign off with the sender's name. "
                    "Do not include the subject line itself; produce only the email body text.\n\n"
                    f"Receiver name: {other_name}\n"
                    f"Sender name: {your_name}\n"
                    f"Context:\n{context}\n"
                )
                resp = self._gemini_model.generate_content(prompt)
                body = (getattr(resp, "text", None) or "").strip()
                if body:
                    return body
            except Exception as e:
                print(f"[Gemini default-gen error] {e}")

        # Fallback default body (no AI)
        if plan:
            return (
                f"Hi {other_name},\n\n"
                f"I wanted to reach out regarding \"{subject}\". I'm planning a trip to {plan['destination']} "
                f"from {self._fmt_date(plan['start_date'])} to {self._fmt_date(plan['end_date'])}. "
                f"Please let me know your thoughts or availability.\n\n"
                f"Best regards,\n{your_name}\n"
            )
        else:
            return (
                f"Hi {other_name},\n\n"
                f"I wanted to reach out regarding \"{subject}\". Please let me know your thoughts or availability.\n\n"
                f"Best regards,\n{your_name}\n"
            )

    # ---------------- Notifications (to you) ----------------
    def notify_me(self, subject, message):
        sent = self._send_email(self.my_email, subject, message)

        print("\n[Notification]")
        print(f"  To your email: {self.my_email}")
        print(f"  Subject: {subject}")
        print(f"  Message: {message}")
        print("  Status:", "Real email sent to you." if (sent and USE_REAL_EMAIL) else "Simulated only.")
        print()

        return {
            "type": "SYSTEM_NOTIFY",
            "to_name": self.my_name,
            "to_email": self.my_email,
            "subject": subject,
            "message": message,
            "status": "SENT_REAL" if sent else "SIMULATED",
        }

    # ---------------- Google Meet (mail other + notify you) ----------------
    def book_google_meet(
        self, your_name, other_name, other_email, subject, meeting_datetime
    ):
        code = meeting_datetime.strftime("%d%H%M%S")
        meet_code = f"{code[:3]}-{code[3:7]}-{code[7:].ljust(3, '0')}"
        link = f"https://meet.google.com/{meet_code}"

        record = (
            f"GOOGLE_MEET | Organizer: {your_name} | Participant: {other_name} <{other_email}> | "
            f"Subject: {subject} | DateTime: {meeting_datetime.isoformat()} | Link: {link}"
        )
        self._save_record(record)

        body_for_other = (
            f"{your_name} scheduled a Google Meet with you.\n"
            f"Subject: {subject}\n"
            f"Date & Time: {meeting_datetime.isoformat()}\n"
            f"Meet link: {link}\n\n"
            "This email was sent automatically by the Trip Planner."
        )
        self._send_email(other_email, "Google Meet invitation", body_for_other)

        notify_subject = "Google Meet appointment created"
        notify_message = (
            f"{your_name} booked a Google Meet with {other_name} "
            f"at {meeting_datetime.isoformat()}.\nLink: {link}"
        )
        self.notify_me(notify_subject, notify_message)

        return {
            "type": "GOOGLE_MEET",
            "organizer": {"name": your_name, "email": FROM_EMAIL},
            "participant": {"name": other_name, "email": other_email},
            "subject": subject,
            "datetime": meeting_datetime,
            "link": link,
            "status": "SCHEDULED (simulated)",
        }

    # ---------------- Normal Email (you -> receiver) ----------------
    def send_email(self, your_name, other_name, other_email, subject, message, enhance=True):
        """
        Sends to the receiver (AI‑improved body if enhance=True), then notifies you.
        Also appends: ' - you for the best contents' to the subject.
        If 'message' is already AI‑generated (default), pass enhance=False to avoid double processing.
        """
        full_subject = f"{subject} - you for the best contents"

        timestamp = datetime.now().isoformat(timespec="seconds")
        record = (
            f"EMAIL | From: {your_name} | To: {other_name} <{other_email}> | "
            f"Subject: {full_subject} | SentAt: {timestamp} | Message: {message}"
        )
        self._save_record(record)

        if enhance:
            # Build base body, then improve with AI/template
            base_body = (
                f"This email is from {your_name} via the Trip Planner.\n\n"
                f"{message}\n\n"
                "This email was sent automatically by the Trip Planner."
            )
            body_for_other = self._improve_with_ai(base_body, your_name, other_name)
        else:
            # Use the provided message as-is (assumed already polished)
            body_for_other = message

        self._send_email(other_email, full_subject, body_for_other)

        notify_subject = "Trip email sent"
        notify_message = (
            f"{your_name} sent an email to {other_name} <{other_email}> "
            f"with subject '{full_subject}'."
        )
        self.notify_me(notify_subject, notify_message)

        return {
            "type": "EMAIL",
            "from": your_name,
            "to": other_name,
            "email": other_email,
            "subject": full_subject,
            "message": message,
            "status": "SENT (simulated/real depending on config)",
        }