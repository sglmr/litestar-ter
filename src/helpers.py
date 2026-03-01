import logging
import os
from email.message import EmailMessage
from secrets import choice


async def send_email_async(to_address: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = os.getenv("SMTP_FROM", "noreply@myapp.com")
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    log = logging.getLogger("email")
    log.info(f"Mocking email send to {to_address}: {subject}")
    # In production, configure your SMTP server here


def rand_id(length: int = 40, friendly: bool = True) -> str:
    """Creates a URL-safe ID of random letters.
    friendly=True will return an ID without 0, O, i, l, -, _"""

    alphabet = (
        "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"  # Friendly alphabet
    )
    if not friendly:
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-"

    return "".join(choice(alphabet) for _ in range(length))
