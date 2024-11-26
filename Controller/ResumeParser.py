'''
MIT License

Copyright (c) 2024 Girish G N, Joel Jogy George, Pravallika Vasireddy

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
import re
import io
import cv2
import nltk
import numpy as np
import PyPDF2
import docx2txt
import pytesseract
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Download required NLTK data files if not already present
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

def read_image_resume(file: str) -> str:
    """Extract text from an image resume using Tesseract OCR."""
    image = cv2.imread(file)
    text = pytesseract.image_to_string(image)
    return text if text else ''

def read_pdf_resume(file: str) -> str:
    """Extract text from the first page of a PDF resume."""
    with open(file, 'rb') as pdfFileObj:
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        if pdfReader.numPages > 0:
            pageObj = pdfReader.getPage(0)
            return pageObj.extractText() or ''
    return ''

def read_word_resume(word_doc: str) -> str:
    """Extract text from a Word document resume."""
    resume = docx2txt.process(word_doc)
    return resume.replace("\n", "") if resume else ''

def clean_job_description(jd: str) -> list:
    """Clean the job description for text processing."""
    clean_jd = re.sub(r'[^\w\s]', '', jd.lower()).strip()
    clean_jd = re.sub('[0-9]+', '', clean_jd)
    tokens = word_tokenize(clean_jd)
    stop_words = set(stopwords.words('english'))
    return [word for word in tokens if word not in stop_words]

def create_word_cloud(corpus: list):
    """Generate and display a word cloud from the given text corpus."""
    frequency_distribution = FreqDist(corpus)
    word_cloud = WordCloud(width=800, height=800, background_color='white', max_words=500)
    word_cloud.generate_from_frequencies(frequency_distribution)
    plt.figure(figsize=(10, 10))
    plt.imshow(word_cloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()

def get_resume_score(text: list) -> str:
    """Calculate similarity score between resume and job description."""
    cv = CountVectorizer(stop_words='english')
    count_matrix = cv.fit_transform(text)
    match_percentage = cosine_similarity(count_matrix.toarray())[0][1] * 100
    # return f"Your resume matches about {round(match_percentage + 50, 2)}% of the job description."
    return round(match_percentage + 50, 2)

def resume_analyzer(jobtext: str, file: str) -> str:
    """Analyze a resume against a job description and generate insights."""
    if file.endswith(".pdf"):
        resume = read_pdf_resume(file)
    elif file.lower().endswith((".jpeg", ".jpg", ".png")):
        resume = read_image_resume(file)
    else:
        resume = read_word_resume(file)

    clean_jd = clean_job_description(jobtext)
    create_word_cloud(clean_jd)
    return f"Your resume matches about {get_resume_score([resume, jobtext])}% of the job description."