import mimetypes
import pandas as pd
import PyPDF2
from docx import Document
import io

def validate_document(file):
    file_type, _ = mimetypes.guess_type(file.filename)
    
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'text/plain', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    if file_type not in allowed_types:
        raise ValueError(f"Unsupported file type: {file_type}")
        
    return file_type

def extract_text(file, file_type):
    # Reset file pointer to beginning
    file.seek(0)
    
    if file_type == 'application/pdf':
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        doc = Document(file)
        text = ' '.join([paragraph.text for paragraph in doc.paragraphs])
    elif file_type == 'text/plain':
        text = file.read().decode('utf-8')
    elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        df = pd.read_excel(file)
        text = df.to_json()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return text

def extract_text_with_size(file, file_type):
    text = extract_text(file, file_type)
    file_size = len(file.read())
    file.seek(0)  # Reset file pointer
    return text, file_size