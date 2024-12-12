import streamlit as st
import easyocr
from PIL import Image
import pdf2image
import numpy as np
import io
import fitz
import base64
import json
import re
from transformers import pipeline


class LLMDocumentProcessor:
    def __init__(self):
        # Initialize easyocr reader
        self.reader = easyocr.Reader(["en"])

        # Initialize NuExtract model for extraction
        self.extraction_pipeline = pipeline(
            "text-generation", model="numind/NuExtract", trust_remote_code=True
        )

        # Comprehensive extraction fields
        self.extraction_fields = [
            # Identification
            "full_name",
            "first_name",
            "last_name",
            "middle_name",
            "date_of_birth",
            "gender",
            "nationality",
            "passport_number",
            "social_security_number",
            # Contact Information
            "email",
            "phone_number",
            "mobile_number",
            "home_address",
            "work_address",
            # Educational Details
            "institution_name",
            "degree",
            "major",
            "graduation_year",
            "gpa",
            "student_id",
            # Professional Details
            "job_title",
            "company_name",
            "department",
            "employee_id",
            "work_email",
            # Financial Information
            "bank_name",
            "account_number",
            "routing_number",
            "credit_card_number",
            "tax_id",
            "annual_income",
            # Document Specifics
            "document_type",
            "document_number",
            "issue_date",
            "expiration_date",
            "issuing_authority",
            # Additional Identifiers
            "registration_number",
            "serial_number",
            # Verification Details
            "signature_present",
            "photo_id_match",
            "document_authenticity",
        ]

    def convert_pdf_to_images(self, pdf_file):
        """
        Convert PDF to images using PyMuPDF

        Args:
            pdf_file (UploadedFile): Uploaded PDF file

        Returns:
            list: List of PIL Images
        """
        try:
            # Open PDF
            pdf_document = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
            images = []

            for page_num in range(len(pdf_document)):
                # Render page to a pixmap with high resolution
                page = pdf_document[page_num]
                pixmap = page.get_pixmap(dpi=300)

                # Convert to PIL Image
                image = Image.frombytes(
                    "RGB", [pixmap.width, pixmap.height], pixmap.samples
                )
                images.append(image)

            return images
        except Exception as e:
            st.error(f"PDF conversion error: {e}")
            return []

    def perform_ocr(self, image):
        """
        Perform OCR using easyocr

        Args:
            image (PIL.Image): Document image

        Returns:
            str: Extracted text
        """
        try:
            # Perform OCR using easyocr
            result = self.reader.readtext(np.array(image))
            extracted_text = " ".join([text for _, text, _ in result])
            return extracted_text
        except Exception as e:
            st.error(f"OCR processing error: {e}")
            return None

    def extract_structured_information(self, image, extracted_text):
        """
        Extract structured information using NuExtract

        Args:
            image (PIL.Image): Document image
            extracted_text (str): OCR extracted text

        Returns:
            dict: Structured document information
        """
        try:
            # Prepare messages for NuExtract
            messages = [
                {
                    "role": "user",
                    "content": f"Extract structured information from the following document text:\n\n{extracted_text}\n\nRequired Fields to Extract:\n{', '.join(self.extraction_fields)}\n\nExtraction Guidelines:\n- Be extremely precise and accurate\n- Use context from both text and image\n- If a field is not found, set to null\n- Provide a confidence score for each extracted field\n- Format output as clean, valid JSON",
                }
            ]

            # Use NuExtract for extraction
            response = self.extraction_pipeline(messages)
            generated_text = response[0]["generated_text"]
            st.write(generated_text)

            # Parse JSON
            try:
                structured_data = json.loads(generated_text)
            except json.JSONDecodeError:
                # Fallback parsing
                structured_data = self._parse_generated_text(generated_text)

            return structured_data

        except Exception as e:
            st.error(f"Information extraction error: {e}")
            return None

    def _parse_generated_text(self, text):
        """
        Fallback parsing for generated text

        Args:
            text (str): Generated text

        Returns:
            dict: Parsed structured data
        """
        parsed_data = {}
        for field in self.extraction_fields:
            # Use regex to extract potential values
            match = re.search(rf"{field}[:\s]*([^\n,]+)", text, re.IGNORECASE)
            parsed_data[field] = match.group(1).strip() if match else None

        return parsed_data


def main():
    st.set_page_config(page_title="Document Information Extractor", layout="wide")

    st.title("🧠 Document Information Extraction")

    # File uploader
    uploaded_file = st.file_uploader(
        "📤 Upload Document",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload a document image or PDF for advanced information extraction",
    )

    if uploaded_file is not None:
        # Process document
        processor = LLMDocumentProcessor()

        # Determine if it's a PDF or image
        if uploaded_file.type == "application/pdf":
            # Convert PDF to images
            images = processor.convert_pdf_to_images(uploaded_file)
        else:
            # If it's an image, convert to list
            images = [Image.open(uploaded_file)]

        # Process each page
        for page_num, image in enumerate(images, 1):
            st.subheader(f"📄 Page {page_num}")

            col1, col2 = st.columns(2)

            with col1:
                # Display image
                st.image(image, caption=f"Page {page_num}", use_column_width=True)

            with col2:
                # Perform OCR
                with st.spinner("🔍 Performing OCR..."):
                    extracted_text = processor.perform_ocr(image)

                if extracted_text:
                    st.subheader("📄 Extracted Text")
                    st.text_area(
                        f"OCR Result - Page {page_num}", extracted_text, height=200
                    )

                # Extract structured information
                with st.spinner("🧩 Extracting Structured Information..."):
                    if extracted_text:
                        result = processor.extract_structured_information(
                            image, extracted_text
                        )
                    else:
                        result = None

                if result:
                    # Display results
                    st.subheader("📊 Extracted Information")
                    st.json(result)

                    # Download option
                    json_string = json.dumps(result, indent=4)
                    st.download_button(
                        label="📥 Download Extracted Data",
                        data=json_string,
                        file_name=f"document_extraction_page_{page_num}.json",
                        mime="application/json",
                    )
                else:
                    st.error("❌ Failed to extract information")


if __name__ == "__main__":
    main()
