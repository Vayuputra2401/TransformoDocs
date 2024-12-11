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
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path


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

def pdf_to_text(pdf_path):
    """
    Extract text from a PDF using PyMuPDF (fitz).
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text from the PDF.
    """
    doc = fitz.open(pdf_path)
    text = ""
    
    # Iterate through each page in the PDF
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # Get page
        text += page.get_text("text")  # Extract text
        
    return text.strip()

def pdf_to_ocr_text(pdf_path):
    """
    Perform OCR on a PDF containing images (using PyMuPDF to extract images and Tesseract).
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text from the PDF.
    """
    extracted_text = ""
    
    try:
        # Open the PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Process each page
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            
            # Extract images from the page (if any)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                image = doc.extract_image(xref)
                img_data = image["image"]
                
                # Convert the image data into a PIL image
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR on the image using Tesseract
                text = pytesseract.image_to_string(pil_image, lang='eng')
                extracted_text += f"\n--- Page {page_num + 1}, Image {img_index + 1} ---\n{text}"
            
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None

    return extracted_text.strip()

def extract_text_from_scanned_pdf(pdf_path):
    # First try extracting text using PyMuPDF (for text-based PDFs)
    print("Extracting text from PDF...")
    text = pdf_to_text(pdf_path)
    
    if text.strip():  # If text extraction works
        print("Text extracted successfully using PyMuPDF.")
        return text
    else:
        # If no text found, fall back to OCR on images
        print("No text found. Falling back to OCR on images.")
        return pdf_to_ocr_text(pdf_path)

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
    # if file_type == 'application/pdf' and is_scanned:
    #     if not is_scanned_pdf(file):
    #         raise ValueError("The uploaded PDF does not appear to be a scanned document.")
    
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