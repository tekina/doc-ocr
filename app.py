import os
import dotenv
from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic
from dotenv import load_dotenv

# Import new services
from services.config_loader import ConfigLoader
from services.ocr_processor import OCRProcessor
from utils.file_helpers import encode_image_to_base64

load_dotenv()
app = Flask(__name__)

# Initialize the Anthropic client with API key
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# Initialize services
config_loader = ConfigLoader(config_dir='config/document_types')
ocr_processor = OCRProcessor(client, config_loader)


# API Endpoints
@app.route('/api/document-types', methods=['GET'])
def get_document_types():
    """Return all available document types."""
    try:
        doc_types = config_loader.get_all_document_types(enabled_only=True)
        return jsonify({
            'document_types': [dt.to_dict() for dt in doc_types]
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load document types: {str(e)}'}), 500


@app.route('/api/document-types/<doc_type_id>', methods=['GET'])
def get_document_type(doc_type_id):
    """Return specific document type details."""
    try:
        doc_type = config_loader.get_document_type(doc_type_id)
        if not doc_type:
            return jsonify({'error': 'Document type not found'}), 404
        return jsonify(doc_type.to_dict())
    except Exception as e:
        return jsonify({'error': f'Failed to load document type: {str(e)}'}), 500


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process document with OCR (in-memory processing only)."""
    import sys
    sys.stdout.flush()
    print("=== UPLOAD REQUEST RECEIVED ===", flush=True)
    print(str(request), flush=True)
    print(str(request.form), flush=True)

    # Validate file
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    file_type = file.mimetype

    # Get document type ID (support both old 'fileType' and new 'docTypeId' for backward compatibility)
    doc_type_id = request.form.get('docTypeId') or request.form.get('fileType')

    # Map old values to new IDs for backward compatibility
    if doc_type_id == 'KTP':
        doc_type_id = 'id_ktp'
        print("Mapping legacy 'KTP' to 'id_ktp'", flush=True)
    elif doc_type_id == 'NPWP':
        doc_type_id = 'id_npwp'
        print("Mapping legacy 'NPWP' to 'id_npwp'", flush=True)

    if not doc_type_id or doc_type_id == '':
        return jsonify({'error': 'No document type selected'}), 400

    # Validate document type exists
    doc_config = config_loader.get_document_type(doc_type_id)
    if not doc_config:
        return jsonify({'error': f'Invalid document type: {doc_type_id}'}), 400

    print(f"##########File Details############# ", flush=True)
    print(f"File: {file}", flush=True)
    print(f"File type: {file_type}", flush=True)
    print(f"Document type ID: {doc_type_id}", flush=True)
    print(f"##########File Details############# ", flush=True)

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Support only images for now
    if "pdf" in file_type:
        return jsonify({'error': 'PDF file support coming soon!'}), 400

    # Read file directly from memory (never save to disk)
    file_bytes = file.read()

    # Encode the image bytes as base64
    base64_image = encode_image_to_base64(file_bytes)

    try:
        # Process using OCRProcessor service
        details = ocr_processor.process_document(base64_image, doc_type_id, file_type)
        # Return extracted details as JSON
        return jsonify({'details': details})
    except Exception as e:
        print(f"Error occurred: {str(e)}", flush=True)
        print(f"Error type: {type(e).__name__}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Something went wrong: {str(e)}'}), 400
    finally:
        # Clear file bytes from memory
        del file_bytes
        print("Process finished (file processed in memory only)", flush=True)

if __name__ == '__main__':
    app.run(debug=True)

