from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from document_processor import process_document
from nlp_processor import process_text
from output_generator import generate_machine_readable_output
from security_measures import token_required

app = Flask(__name__, static_folder='../frontend/build')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ... (previous routes remain the same)

@app.route('/api/document/<filename>', methods=['GET'])
@token_required
def get_document(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        extracted_text = process_document(file_path)
        structured_data = process_text(extracted_text)
        return jsonify({
            'filename': filename,
            'structured_data': structured_data
        }), 200
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/document/<filename>/transform', methods=['GET'])
@token_required
def transform_document(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        extracted_text = process_document(file_path)
        structured_data = process_text(extracted_text)
        output_format = request.args.get('format', 'json')
        transformed_data = generate_machine_readable_output(structured_data, output_format)
        return jsonify({
            'filename': filename,
            'transformed_data': transformed_data
        }