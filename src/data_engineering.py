import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import pytesseract
import pdfplumber
import PyPDF2
from docx import Document
from PIL import Image
import mimetypes

class DataEngineer:
    def __init__(self):
        self.allowed_types = {
            'application/pdf': 'pdf',
            'application/msword': 'docx',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt',
            'application/vnd.ms-excel': 'xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'image/png': 'image',
            'image/jpeg': 'image',
            'image/jpg': 'image'
        }

    def _get_file_type(self, filepath):
        file_type, _ = mimetypes.guess_type(filepath)
        if file_type not in self.allowed_types:
            raise ValueError(f"Unsupported file type: {file_type}")
        return self.allowed_types[file_type]

    def extract_text(self, filepath):
        file_ext = self._get_file_type(filepath)
        text = ""

        if file_ext == 'pdf':
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            # Fallback to PyPDF2 if pdfplumber fails
            if not text.strip():
                with open(filepath, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"

        elif file_ext == 'docx':
            doc = Document(filepath)
            text = '\n'.join([para.text for para in doc.paragraphs])

        elif file_ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

        elif file_ext == 'xlsx':
            df = pd.read_excel(filepath)
            text = df.to_string()

        elif file_ext == 'image':
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)

        return text.strip()

    def structure_data(self, text, filename="document"):
        # We simplify structuring. A more complex layout parsing could be added.
        structured = {
            "metadata": {
                "source": filename,
                "character_count": len(text),
                "word_count": len(text.split())
            },
            "content": text
        }
        return structured

    def to_json(self, structured_data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=4, ensure_ascii=False)
        return output_path

    def to_xml(self, structured_data, output_path):
        root = ET.Element("Document")
        
        meta = ET.SubElement(root, "Metadata")
        for k, v in structured_data["metadata"].items():
            child = ET.SubElement(meta, k.capitalize())
            child.text = str(v)
            
        content = ET.SubElement(root, "Content")
        content.text = structured_data["content"]
        
        xml_str = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="  ")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        return output_path

    def process_file(self, filepath):
        """End-to-end processing: extract, structure, and return dictionary."""
        text = self.extract_text(filepath)
        filename = os.path.basename(filepath)
        structured = self.structure_data(text, filename)
        return structured
