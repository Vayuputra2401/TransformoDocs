import magic
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from docx import Document
import pandas as pd
import json
import xml.etree.ElementTree as ET

def validate_document(file_path):
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'text/plain', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    if file_type not in allowed_types:
        raise ValueError(f"Unsupported file type: {file_type}")

def extract_text(file_path):
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    
    if file_type == 'application/pdf':
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        doc = Document(file_path)
        return ' '.join([paragraph.text for paragraph in doc.paragraphs])
    elif file_type == 'text/plain':
        with open(file_path, 'r') as file:
            return file.read()
    elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        df = pd.read_excel(file_path)
        return df.to_json()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def process_document(file_path):
    validate_document(file_path)
    return extract_text(file_path)
