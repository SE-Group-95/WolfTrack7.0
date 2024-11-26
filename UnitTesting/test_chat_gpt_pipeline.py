import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from pathlib import Path
import json
import sys
sys.path.append(str(Path(__file__).parent.parent / 'Controller'))
# sys.path.append(os.path.abspath('../Controller'))
from io import StringIO
from chat_gpt_pipeline import pdf_to_text,chatgpt,extract_top_job_roles


class TestResumeProcessor(unittest.TestCase):

    @patch('chat_gpt_pipeline.PdfFileReader')
    @patch('builtins.open', new_callable=mock_open)
    def test_pdf_to_text(self, mock_open_file, mock_pdf_reader):
        # Mock the PdfFileReader and its pages
        mock_pdf_instance = MagicMock()
        mock_pdf_instance.pages = [MagicMock(), MagicMock()]
        mock_pdf_instance.pages[0].extract_text.return_value = "Sample Page 1 text."
        mock_pdf_instance.pages[1].extract_text.return_value = "Sample Page 2 text."
        mock_pdf_reader.return_value = mock_pdf_instance

        pdf_to_text("dummy.pdf", "output.txt")

        # Verify the output file writing
        mock_open_file.assert_called_with("output.txt", 'w', encoding='utf-8')
        mock_open_file().write.assert_called_once_with("Sample Page 1 text.Sample Page 2 text.")

    @patch('chat_gpt_pipeline.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data="Sample resume content")
    def test_chatgpt(self, mock_open_file, mock_post):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Section 1: Education suggestions\nSection 2: Experience suggestions\nSection 3: Skills suggestions\nSection 4: Projects suggestions'}}]
        }
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict('os.environ', {"OPENAI_API_KEY": "dummy_key"}):
            result = chatgpt("dummy_resume.txt")

        self.assertEqual(result, 'Section 1: Education suggestions\nSection 2: Experience suggestions\nSection 3: Skills suggestions\nSection 4: Projects suggestions')

    @patch('chat_gpt_pipeline.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data="Sample resume content")
    def test_extract_top_job_roles(self, mock_open_file, mock_post):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Software Engineer, Data Scientist, Machine Learning Engineer, DevOps Engineer, Backend Developer'}}]
        }
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict('os.environ', {"OPENAI_API_KEY": "dummy_key"}):
            job_roles = extract_top_job_roles("dummy_resume.txt")

        self.assertEqual(job_roles, ['Software Engineer', 'Data Scientist', 'Machine Learning Engineer', 'DevOps Engineer', 'Backend Developer'])

    @patch('chat_gpt_pipeline.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data="Sample resume content")
    def test_extract_top_job_roles_failure(self, mock_open_file, mock_post):
        # Mock a failed API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error: Bad Request"
        mock_post.return_value = mock_response

        # Mock environment variable
        with patch.dict('os.environ', {"OPENAI_API_KEY": "dummy_key"}):
            job_roles = extract_top_job_roles("dummy_resume.txt")

        self.assertIsNone(job_roles)


# Run the tests
if __name__ == '__main__':
    unittest.main()