# ================================
# File: trip_planner/communication_service.py
# Requires:
#   - python3 -m pip install groq
#   - (Option 1 - recommended) export GROQ_API_KEY="gsk_your_key"
#   - (Option 2 - quick demo) put your key into DEFAULT_GROQ_API_KEY below
# Optional (for real email sending):
#   - Gmail 2FA + App Password (set FROM_EMAIL and FROM_PASSWORD)
# ================================

from datetime import datetime
import os
import smtplib
import ssl

# Groq (LLM) import
try:
    from groq import Groq
except Exception as e:
    print(f"[AI import warning] {e}")
    Groq = None

# =======================================================
# EMAIL CONFIGURATION: CHANGE THESE TO YOUR REAL DETAILS
# =======================================================
# Send real emails via Gmail SMTP (True) or simulate (False)
USE_REAL_EMAIL = True

# YOUR Gmail address (the account that sends the emails)
FROM_EMAIL = "d97148012@gmail.com"          # <-- PUT YOUR GMAIL HERE

# YOUR Gmail APP PASSWORD (NOT your normal Gmail password)
# Turn on 2‑Step Verification in Google, then create an App Password.
FROM_PASSWORD = "frzxmdgsmmoewooe"  # <-- PUT APP PASSWORD HERE

# Your own name and your own email (for notifications)
MY_NAME = "Dinesh"                        # <-- YOUR NAME
MY_EMAIL = "d97148012@gmail.com"            # usually same as FROM_EMAIL
# =======================================================

# =======================================================
# GROQ (AI) CONFIG
# =======================================================
# Use Groq LLM to generate/improve email text if available.
USE_GROQ = True
GROQ_MODEL = "llama-3.1-8b-instant"  # fast, good quality

# EXACT PLACE TO PUT YOUR GROQ API KEY (quick demo):
# Replace the placeholder below with your real key (starts with gsk_),
# OR leave it empty and set the env var GROQ_API_KEY in the terminal.
DEFAULT_GROQ_API_KEY = "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"  # "gsk_your_actual_groq_key_here"  # <-- optional demo only
# =======================================================


class CommunicationService:
    def __init__(self):
        self.my_name = MY_NAME
        self.my_email = MY_EMAIL

        self._ai_client = None
        self._ai_enabled = False

        if USE_GROQ and Groq is not None:
            # 1) reads from env var GROQ_API_KEY
            # 2) falls back to DEFAULT_GROQ_API_KEY (demo)
            api_key = os.environ.get("GROQ_API_KEY", DEFAULT_GROQ_API_KEY).strip()

            if api_key and api_key.startswith("gsk_"):
                try:
                    self._ai_client = Groq(api_key=api_key)
                    self._ai_enabled = True
                except Exception as e:
                    print(f"[AI init error] {e}")
            else:
                print("[AI disabled] No valid Groq API key found. "
                      "Set DEFAULT_GROQ_API_KEY or export GROQ_API_KEY.")
        elif USE_GROQ and Groq is None:
            print("[AI disabled] 'groq' package not installed. Run: python3 -m pip install groq")

    def _fmt_date(self, d):
        return d.strftime("%d-%m-%y")

    def _save_record(self, text):
        try:
            with open("communications.txt", "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass

    # =============== FIXED: proper MIME email sending =================
    def _send_email(self, to_email, subject, message):
        # Log every attempt (store only length to avoid huge files)
        log_text = (
            f"EMAIL_OUT | From: {FROM_EMAIL} | To: {to_email} | "
            f"Subject: {subject} | At: {datetime.now().isoformat(timespec='seconds')} | "
            f"BodyLen: {len((message or '').strip())}"
        )
        self._save_record(log_text)

        if not USE_REAL_EMAIL:
            print(f"\n[Email simulated] To: {to_email} | Subject: {subject}\n")
            return False

        # Build a proper MIME email (handles plain text and HTML)
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = FROM_EMAIL

        # Auto-detect HTML vs plain text
        body = message or ""
        is_html = ("</" in body and "<" in body)
        if is_html:
            # Plain fallback + HTML body
            msg.set_content(
                "This message contains HTML. If you see this, your client is showing the plain-text fallback."
            )
            msg.add_alternative(body, subtype="html")
        else:
            # Plain-text body
            msg.set_content(body)

        # Try STARTTLS on 587 first
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(FROM_EMAIL, FROM_PASSWORD)
                server.send_message(msg)
            print(f"\n[Real email sent] To: {to_email} | Subject: {subject} (via 587 STARTTLS)\n")
            return True
        except Exception as e1:
            print(f"[SMTP 587 STARTTLS failed] {e1}")

        # Fallback to SSL on 465
        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=30) as server:
                server.login(FROM_EMAIL, FROM_PASSWORD)
                server.send_message(msg)
            print(f"\n[Real email sent] To: {to_email} | Subject: {subject} (via 465 SSL)\n")
            return True
        except Exception as e2:
            print(f"[SMTP 465 SSL failed] {e2}")
            return False
    # ==================================================================

    def generate_default_email(self, your_name, other_name, subject, plan=None):
        """
        AUTOMATICALLY generate a rich, multi-line email body ONLY from the one-line SUBJECT,
        and optionally include trip details if provided.

        Output format (automatic, meaningful, well-structured):
        - Greeting line (Hi <name>,)
        - 2–3 lines explaining the subject in clear language
        - If a trip plan exists, include destination and dates
        - 3–5 bullet points ('- ') with key details/next steps
        - 1 line inviting questions/confirmation
        - Closing ("Best regards," + sender name)
        """
        # Build context for the model or fallback
        if plan:
            trip_category = plan.get("trip_category", "trip")
            context = (
                f"Subject: {subject}\n"
                f"{your_name} is planning a {trip_category} to {plan['destination']} "
                f"from {self._fmt_date(plan['start_date'])} to {self._fmt_date(plan['end_date'])} "
                f"({plan['num_days']} day(s))."
            )
        else:
            context = f"Subject: {subject}\n{your_name} wants to communicate regarding this subject."

        # AI path: create the full email body automatically
        if self._ai_enabled and self._ai_client is not None:
            try:
                prompt = (
                    "Write a complete email BODY (not the subject) that clearly explains the SUBJECT.\n"
                    "Requirements:\n"
                    "- Start with: Hi {receiver_name}, on its own line.\n"
                    "- In 2–3 lines, explain the purpose in relation to the SUBJECT in plain, friendly language.\n"
                    "- If trip details are provided in the context, include destination and dates naturally.\n"
                    "- Add 3–5 bullet points using '- ' for key details, options, or next steps.\n"
                    "- Add one line inviting questions or confirmation.\n"
                    "- Close with: Best regards, then the sender's name on the next line.\n"
                    "- Return only the email body. Do NOT include the subject line.\n"
                    "- Keep it under 1600 characters, well formatted and meaningful.\n\n"
                    f"Receiver name: {other_name}\n"
                    f"Sender name: {your_name}\n"
                    f"Context:\n{context}\n"
                )
                resp = self._ai_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You write clear, friendly, multi-line emails with bullet points."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.6,
                    max_tokens=600,
                )
                body = (resp.choices[0].message.content or "").strip()
                if body:
                    return body
            except Exception as e:
                print(f"[AI generation error] {e}")

        # Fallback default body (no AI), still multi‑line and explanatory
        if plan:
            return (
                f"Hi {other_name},\n\n"
                f"I’m reaching out regarding \"{subject}\" and wanted to share the key trip details.\n"
                f"The plan is to visit {plan['destination']} from {self._fmt_date(plan['start_date'])} "
                f"to {self._fmt_date(plan['end_date'])} ({plan['num_days']} day(s)).\n\n"
                f"- Purpose: {subject}\n"
                f"- Destination: {plan['destination']}\n"
                f"- Dates: {self._fmt_date(plan['start_date'])} to {self._fmt_date(plan['end_date'])}\n"
                f"- Trip type: {plan.get('trip_category', 'trip')}\n"
                f"- Next steps: confirm availability/preferences and any requirements\n\n"
                f"Please let me know your thoughts or if you need more info.\n\n"
                f"Best regards,\n{your_name}\n"
            )
        else:
            return (
                f"Hi {other_name},\n\n"
                f"I’m writing about \"{subject}\" and wanted to provide a brief explanation and next steps.\n"
                f"Here are a few key points to help us move forward smoothly:\n\n"
                f"- Purpose: clarify the main goal related to \"{subject}\"\n"
                f"- Background: any helpful context supporting decisions\n"
                f"- Options: possible approaches or timelines\n"
                f"- Next steps: what I propose and when\n"
                f"- Support: information or input needed from you\n\n"
                f"Please let me know your thoughts or adjustments you’d prefer.\n\n"
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
    def send_email(self, your_name, other_name, other_email, subject, message, enhance=False):
        """
        Sends to the receiver using the provided multi-line 'message', then notifies you.
        Automatically appends: ' - you for the best contents' to the subject (as requested).
        'enhance' is kept for backward compatibility; default is False because we are now
        auto-generating a polished message via generate_default_email.
        """
        full_subject = f"{subject} - you for the best contents"

        timestamp = datetime.now().isoformat(timespec="seconds")
        record = (
            f"EMAIL | From: {your_name} | To: {other_name} <{other_email}> | "
            f"Subject: {full_subject} | SentAt: {timestamp} | BodyLen: {len((message or '').strip())}"
        )
        self._save_record(record)

        # Use message as-is (already AI-generated and multi-line)
        body_for_other = message or ""

        self._send_email(other_email, full_subject, body_for_other)

        notify_subject = "Trip email sent"
        notify_message = (
            f"{your_name} sent an email to {other_name} <{other_email}> "
            f"with subject '{full_subject}'."
        )
        self.notify_me(notify_subject, notify_message)

        return {
            "type": "EMAIL",
            "from": {"name": your_name, "email": FROM_EMAIL},
            "to": {"name": other_name, "email": other_email},
            "subject": full_subject,
            "message": body_for_other,
            "status": "SENT (simulated/real depending on config)",
        }