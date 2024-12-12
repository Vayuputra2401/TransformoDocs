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
from transformers import T5Tokenizer, T5ForConditionalGeneration


class LLMDocumentProcessor:
    def __init__(self):
        # Initialize easyocr reader
        self.reader = easyocr.Reader(["en"])

        # Initialize T5 model and tokenizer for structured extraction
        self.t5_tokenizer = T5Tokenizer.from_pretrained("google/t5-base")
        self.t5_model = T5ForConditionalGeneration.from_pretrained("google/t5-base")

        # Comprehensive extraction fields
        self.extraction_fields = [
            "full_name",
            "date_of_birth",
            "gender",
            "email",
            "phone_number",
            "home_address",
            "job_title",
            "company_name",
            "document_type",
            "document_number",
            "issue_date",
            "expiration_date",
        ]

    def convert_pdf_to_images(self, pdf_file):
        try:
            pdf_document = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
            images = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                pixmap = page.get_pixmap(dpi=300)
                image = Image.frombytes(
                    "RGB", [pixmap.width, pixmap.height], pixmap.samples
                )
                images.append(image)
            return images
        except Exception as e:
            st.error(f"PDF conversion error: {e}")
            return []

    def perform_ocr(self, image):
        try:
            result = self.reader.readtext(np.array(image))
            extracted_text = " ".join([text for _, text, _ in result])
            return extracted_text
        except Exception as e:
            st.error(f"OCR processing error: {e}")
            return None

    def extract_with_t5(self, text):
        try:
            prompt = f"Extract the following fields from the text and provide as JSON: {', '.join(self.extraction_fields)}. Text: {text}"

            inputs = self.t5_tokenizer(
                prompt, return_tensors="pt", max_length=512, truncation=True
            )
            outputs = self.t5_model.generate(
                **inputs, max_length=512, num_beams=4, early_stopping=True
            )

            generated_text = self.t5_tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )
            structured_data = json.loads(generated_text)  # Parse into a dictionary

            return structured_data
        except Exception as e:
            st.error(f"T5 extraction error: {e}")
            return {}

    def extract_structured_information(self, image, extracted_text):
        try:
            structured_data = self.extract_with_t5(extracted_text)

            for field in self.extraction_fields:
                if field not in structured_data:
                    structured_data[field] = None

            return structured_data
        except Exception as e:
            st.error(f"Information extraction error: {e}")
            return None


def main():
    st.set_page_config(page_title="Document Information Extractor", layout="wide")

    st.title("\U0001F9E0 Document Information Extraction")

    uploaded_file = st.file_uploader(
        "\U0001F4E4 Upload Document",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload a document image or PDF for advanced information extraction",
    )

    if uploaded_file is not None:
        processor = LLMDocumentProcessor()

        if uploaded_file.type == "application/pdf":
            images = processor.convert_pdf_to_images(uploaded_file)
        else:
            images = [Image.open(uploaded_file)]

        for page_num, image in enumerate(images, 1):
            st.subheader(f"\U0001F4C4 Page {page_num}")

            col1, col2 = st.columns(2)

            with col1:
                st.image(image, caption=f"Page {page_num}", use_column_width=True)

            with col2:
                with st.spinner("\U0001F50D Performing OCR..."):
                    extracted_text = processor.perform_ocr(image)

                if extracted_text:
                    st.subheader("\U0001F4C4 Extracted Text")
                    st.text_area(
                        f"OCR Result - Page {page_num}", extracted_text, height=200
                    )

                with st.spinner("\U0001F9E9 Extracting Structured Information..."):
                    if extracted_text:
                        result = processor.extract_structured_information(
                            image, extracted_text
                        )
                    else:
                        result = None

                if result:
                    st.subheader("\U0001F4CA Extracted Information")
                    st.json(result)

                    json_string = json.dumps(result, indent=4)
                    st.download_button(
                        label="\U0001F4E5 Download Extracted Data",
                        data=json_string,
                        file_name=f"document_extraction_page_{page_num}.json",
                        mime="application/json",
                    )
                else:
                    st.error("\u274C Failed to extract information")


if __name__ == "__main__":
    main()
