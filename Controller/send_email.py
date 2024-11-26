'''
MIT License

Copyright (c) 2024 Girish G N, Joel Jogy George, Pravallika Vasireddy

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  # Environment variable for sender's email
PASSWORD = os.getenv("EMAIL_PASSWORD")    # Environment variable for sender's password

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_email(subject: str, body: str, receiver_email: str) -> bool:
    if not SENDER_EMAIL or not PASSWORD:
        logging.error("Sender email or password is not set in environment variables.")
        return False

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())
        logging.info(f"Email sent successfully to {receiver_email}.")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False


def s_email(company_name: str, location: str, job_profile: str, salary: str, user: str, 
            password: str, receiver_email: str, sec_question: str, sec_answer: str, 
            notes: str, date_applied: str) -> bool:
    """
    Sends a job application email with details about the applied position.
    """
    subject = "WolfTrack - Job added to List"
    body = (
        f"WOLFTRACK APPLICATION\n\n"
        f"You have applied to {company_name} for the job profile - {job_profile}.\n"
        f"Please find the details below:\n"
        f"Date Applied: {date_applied}\nLocation: {location}\n"
        f"Salary: {salary}\nUsername: {user}\nPassword: {password}\n"
        f"Security Question: {sec_question}\nSecurity Answer: {sec_answer}\n"
        f"Notes: {notes}\n\n"
        "All the best with your application!\nThe WolfTrack Team."
    )
    return send_email(subject, body, receiver_email)

def s_comment_email(receiver_email: str, comments: str) -> bool:
    """
    Sends a comments email with feedback on the user's profile.
    """
    subject = "Resume - Comments"
    body = f"Our admin has reviewed your profile. Please check the comments below:\n{comments}"
    return send_email(subject, body, receiver_email)
