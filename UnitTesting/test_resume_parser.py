import unittest
from unittest.mock import patch, mock_open
from io import BytesIO
import cv2
import os
import sys
from pathlib import Path

import numpy

sys.path.append(str(Path(__file__).parent.parent / 'Controller'))
from ResumeParser import (
    read_image_resume, read_pdf_resume, read_word_resume,
    clean_job_description, get_resume_score
)

class TestResumeAnalysis(unittest.TestCase):

    @patch("cv2.imread")
    @patch("pytesseract.image_to_string")
    def test_read_image_resume(self, mock_image_to_string, mock_imread):
        mock_imread.return_value = "mock_image"
        mock_image_to_string.return_value = "Extracted text from image"
        result = read_image_resume("test_image.jpg")
        self.assertEqual(result, "Extracted text from image")

    @patch("PyPDF2.PdfFileReader")
    def test_read_pdf_resume(self, mock_pdf_reader):
        mock_pdf = mock_pdf_reader.return_value
        mock_pdf.numPages = 1
        mock_pdf.getPage.return_value.extractText.return_value = "Text from PDF"
        with patch("builtins.open", mock_open(read_data="mock_pdf_data")) as mock_file:
            result = read_pdf_resume("test.pdf")
            self.assertEqual(result, "Text from PDF")

    @patch("docx2txt.process")
    def test_read_word_resume(self, mock_docx2txt):
        mock_docx2txt.return_value = "Text from Word file\nwith newlines"
        result = read_word_resume("test.docx")
        self.assertEqual(result, "Text from Word filewith newlines")

    def test_clean_job_description(self):
        job_description = "Software Engineer! @ 123. Apply now!"
        expected_result = ["software", "engineer"]
        with patch("ResumeParser.stopwords.words", return_value={"apply", "now"}):
            result = clean_job_description(job_description)
            self.assertEqual(result, expected_result)

    def test_get_resume_score(self):
        result = get_resume_score(["Resume text", "Job description"])
        self.assertEqual(type(result), numpy.float64)

if __name__ == "__main__":
    unittest.main()
