import os
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import io

from .extractor import validate_document, extract_text_with_size
from .processor import process_document
from .database import save_to_database, get_saved_documents, delete_document

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_routes(app):
    @app.route('/upload', methods=['POST'])
    def upload_document():
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        template = request.form.get('template', None)
        custom_fields = request.form.getlist('custom_fields')

        try:
            # Validate file
            file_type = validate_document(file)
            extracted_text, file_size = extract_text_with_size(file, file_type)

            # Process document
            result = process_document(
                extracted_text, 
                template.lower().replace(" ", "_") if template and template != "Default" else None,
                [field.lower() for field in custom_fields] if custom_fields else None
            )

            return jsonify(result), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/documents', methods=['GET'])
    def list_documents():
        try:
            documents = get_saved_documents()
            return jsonify(documents), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/documents/<document_id>', methods=['DELETE'])
    def remove_document(document_id):
        try:
            delete_document(document_id)
            return jsonify({"message": "Document deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/chat', methods=['POST'])
    def chat_with_document():
        data = request.json
        question = data.get('question', '')
        document_text = data.get('document_text', '')
        
        # Placeholder for LLM integration
        answer = "Sorry, LLM disabled at the moment for prototype."
        return jsonify({"answer": answer}), 200