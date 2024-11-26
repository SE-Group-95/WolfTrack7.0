import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
os.environ["SENDER_EMAIL"] = "mock_sender@example.com"
os.environ["EMAIL_PASSWORD"] = "mock_password"
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'Controller'))
from send_profile import send_email, attach_files, s_profile


class TestEmailWithAttachments(unittest.TestCase):

    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    def test_attach_files_success(self, mock_file, mock_listdir):
        # Mock directory contents
        mock_listdir.return_value = ["resume1.pdf", "resume2.docx"]

        # Create a mock email message
        message = MagicMock()

        # Call function
        attach_files(message, "mock/path")

        # Assertions
        mock_listdir.assert_called_once_with("mock/path")
        mock_file.assert_called()
        self.assertEqual(message.attach.call_count, 2)

    @patch("os.listdir", side_effect=FileNotFoundError("Directory not found"))
    def test_attach_files_directory_not_found(self, mock_listdir):
        # Create a mock email message
        message = MagicMock()

        # Call function
        with self.assertLogs(level="ERROR") as log:
            attach_files(message, "invalid/path")
        self.assertIn("Directory invalid/path not found", log.output[0])

    @patch("os.listdir", side_effect=Exception("Unexpected error"))
    def test_attach_files_unexpected_error(self, mock_listdir):
        # Create a mock email message
        message = MagicMock()

        # Call function
        with self.assertLogs(level="ERROR") as log:
            attach_files(message, "mock/path")
        self.assertIn("Error attaching files", log.output[0])

    @patch("smtplib.SMTP_SSL")
    @patch("send_profile.attach_files")
    def test_send_email_success(self, mock_attach_files, mock_smtp):
        # Mock SMTP server and attachment function
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_attach_files.return_value = None

        # Call function
        result = send_email(
            subject="Test Subject",
            body="Test Body",
            receiver_email="test@example.com",
            path="mock/path"
        )

        # Assertions
        self.assertTrue(result)
        mock_smtp.assert_called_once_with("smtp.gmail.com", 465, context=unittest.mock.ANY)
        mock_attach_files.assert_called_once_with(unittest.mock.ANY, "mock/path")
        mock_server.sendmail.assert_called_once()


    @patch("send_profile.send_email")
    def test_s_profile_success(self, mock_send_email):
        # Mock send_email function
        mock_send_email.return_value = True

        # Call function
        data = {"Skills": ["Python", "SQL"], "Experience": ["Intern", "Engineer"]}
        upcoming_events = ["Hackathon", "Workshop"]
        result = s_profile(data, upcoming_events, "Profile Info", "test@example.com")

        # Assertions
        self.assertTrue(result)
        mock_send_email.assert_called_once_with(
            "WolfTrack - Profile Mailing",
            unittest.mock.ANY,
            "test@example.com",
            "Controller/resume"
        )

    @patch("send_profile.send_email", return_value=False)
    def test_s_profile_failure(self, mock_send_email):
        # Call function
        data = {"Skills": ["Python", "SQL"], "Experience": ["Intern", "Engineer"]}
        upcoming_events = ["Hackathon", "Workshop"]
        result = s_profile(data, upcoming_events, "Profile Info", "test@example.com")

        # Assertions
        self.assertFalse(result)
        mock_send_email.assert_called_once()

if __name__ == "__main__":
    unittest.main()
