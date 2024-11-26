import os
os.environ["SENDER_EMAIL"] = "mock_sender@example.com"
os.environ["EMAIL_PASSWORD"] = "mock_password"
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'Controller'))
import unittest
from unittest.mock import patch, MagicMock
from send_email import send_email, s_email, s_comment_email

class TestEmailFunctions(unittest.TestCase):

    @patch("smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp):
        # Setup mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Call function
        result = send_email("Test Subject", "Test Body", "test@example.com")

        # Assertions
        self.assertTrue(result)
        mock_smtp.assert_called_once_with("smtp.gmail.com", 465, context=unittest.mock.ANY)
        mock_server.login.assert_called_once_with(
            unittest.mock.ANY, unittest.mock.ANY
        )
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP_SSL")
    def test_send_email_failure(self, mock_smtp):
        # Mock the SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Raise an exception when sendmail is called
        mock_server.sendmail.side_effect = Exception("SMTP Error")

        # Call the function
        result = send_email("Test Subject", "Test Body", "test@example.com")

        # Assert the function returned False
        self.assertFalse(result)

        # Verify the mocked SMTP methods were called
        mock_smtp.assert_called_once_with("smtp.gmail.com", 465, context=unittest.mock.ANY)


    @patch("send_email.send_email")
    def test_s_email(self, mock_send_email):
        # Setup mock return value
        mock_send_email.return_value = True

        # Call function
        result = s_email(
            company_name="Test Company",
            location="Test Location",
            job_profile="Software Engineer",
            salary="100K",
            user="test_user",
            password="test_password",
            receiver_email="test@example.com",
            sec_question="What is your pet's name?",
            sec_answer="Fluffy",
            notes="Some notes",
            date_applied="2024-11-25"
        )

        # Assertions
        self.assertTrue(result)
        mock_send_email.assert_called_once_with(
            "WolfTrack - Job added to List",
            unittest.mock.ANY,
            "test@example.com"
        )

    @patch("send_email.send_email")
    def test_s_comment_email(self, mock_send_email):
        # Setup mock return value
        mock_send_email.return_value = True

        # Call function
        result = s_comment_email("test@example.com", "Great resume! Please update formatting.")

        # Assertions
        self.assertTrue(result)
        mock_send_email.assert_called_once_with(
            "Resume - Comments",
            "Our admin has reviewed your profile. Please check the comments below:\nGreat resume! Please update formatting.",
            "test@example.com"
        )

if __name__ == "__main__":
    unittest.main()
