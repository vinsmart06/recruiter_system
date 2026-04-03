import pdfplumber
import docx
import requests
from bs4 import BeautifulSoup
import re

def parse_resume_file(file_path):
    if not isinstance(file_path, str):
        raise ValueError("Expected file path string")
    if file_path.endswith(".pdf"):
        return parse_pdf(file_path)

    elif file_path.endswith(".docx"):
        return parse_docx(file_path)

    else:
        raise ValueError("Unsupported file type")


def parse_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    return text


def parse_docx(path):

    doc = docx.Document(path)

    text = "\n".join([p.text for p in doc.paragraphs])

    return text


def parse_linkedin_profile(url):

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text()

    return text

def extract_email(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text):
    pattern = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_name(text):
    """
    Robust name extraction using multiple heuristics
    """

    lines = text.split("\n")

    # Step 1: Look in first 10 lines
    for line in lines[:10]:
        line = line.strip()

        if not line:
            continue

        if "@" in line or any(char.isdigit() for char in line):
            continue

        if 2 <= len(line.split()) <= 4:
            if re.match(r"^[A-Z][a-z]+(\s[A-Z][a-z]+)+$", line):
                return line

    # Step 2: Look anywhere in resume
    name_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
    matches = re.findall(name_pattern, text)

    if matches:
        return matches[0]

    return None

def parse_resume(text):

    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)

    return {
        "name": name,
        "email": email,
        "phone": phone
    }