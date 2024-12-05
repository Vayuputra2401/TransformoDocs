# Updated extractor.py
import mimetypes
import pandas as pd
import PyPDF2
from docx import Document
import io
import pytesseract
from PIL import Image
import cv2
import numpy as np

def is_scanned_pdf(file):
    """
    Detect if a PDF is likely a scanned document
    """
    try:
        reader = PyPDF2.PdfReader(file)
        first_page = reader.pages[0]
        
        # Check if the page is an image (likely scanned)
        try:
            # Attempt to get page as image
            page_image = first_page.to_image(resolution=200)
            
            # Convert to OpenCV format
            img_array = np.frombuffer(page_image.original_bytes, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            # Basic image analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Count edge pixels as a heuristic for image-like content
            edge_pixel_ratio = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            return edge_pixel_ratio > 0.1
        except Exception:
            return False
    except Exception:
        return False

def preprocess_scanned_image(image):
    """
    Preprocess image for better OCR results
    """
    # Convert to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # Apply deskewing if needed
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def extract_text_from_scanned_pdf(file):
    """
    Extract text from scanned PDF using OCR
    """
    try:
        # Convert PDF to images
        pdf_reader = PyPDF2.PdfReader(file)
        full_text = ""
        
        for page in pdf_reader.pages:
            # Convert page to image
            page_image = page.to_image(resolution=300)
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(page_image.original_bytes))
            
            # Preprocess image
            preprocessed_img = preprocess_scanned_image(img)
            
            # Convert back to PIL Image for Tesseract
            ocr_image = Image.fromarray(preprocessed_img)
            
            # Perform OCR
            page_text = pytesseract.image_to_string(ocr_image)
            full_text += page_text + "\n"
        
        return full_text.strip()
    except Exception as e:
        raise ValueError(f"OCR processing failed: {str(e)}")

def validate_document(file, is_scanned=False):
    """
    Updated validation to support scanned documents
    """
    file_type, _ = mimetypes.guess_type(file.name)
    
    allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'text/plain', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    if file_type not in allowed_types:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # Additional check for scanned PDFs
    if file_type == 'application/pdf' and is_scanned:
        if not is_scanned_pdf(file):
            raise ValueError("The uploaded PDF does not appear to be a scanned document.")
    
    return file_type

def extract_text(file, file_type, is_scanned=False):
    """
    Updated text extraction with OCR support
    """
    if file_type == 'application/pdf':
        if is_scanned:
            return extract_text_from_scanned_pdf(file)
        else:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
    elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        doc = Document(file)
        text = ' '.join([paragraph.text for paragraph in doc.paragraphs])
    elif file_type == 'text/plain':
        text = file.getvalue().decode('utf-8')
    elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        df = pd.read_excel(file)
        text = df.to_json()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return text

def extract_text_with_size(file, file_type, is_scanned=False):
    """
    Updated to support scanned document size extraction
    """
    text = extract_text(file, file_type, is_scanned)
    file_size = file.size
    return text, file_size