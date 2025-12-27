import os
import base64
import dotenv
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize the Anthropic client with API key
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def encode_image_to_base64(image_path):
    """Encode the image file as a base64 string."""
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_image

def select_prompt(file_type):
    if file_type == "KTP":
        return (
            "Extract and format details from this Indonesian KTP data in the image or pdf file. "
            "Format it in JSON with fields: NIK, Name, BirthPlace, BirthDate, Gender, BloodType, "
            "Address, RT/RW, Village, District, City, Province, Religion, MaritalStatus, Occupation, Nationality, ValidUntil. "
            "Do not wrap the json codes in JSON markers"
        )
    else:
        return (
            "Extract and format details from this Indonesian NPWP data in the image or pdf file. "
            "Format it in JSON with fields: NPWP15, NPWP16, Name, Issuing Location, Address, RT/RW, Village, District, City, Province, Registration Date. "
            "Do not wrap the json codes in JSON markers"
        )
# image/jpeg = image file
# application/pdf = pdf file
def process_image_with_openai(base64_image, doc_type, file_type):
    print("=== STARTING OCR PROCESSING ===", flush=True)
    prompt = select_prompt(doc_type)
    print(f"Prompt: {prompt[:100]}...", flush=True)

    # Determine media type from file_type
    media_type = "image/jpeg"
    if "png" in file_type.lower():
        media_type = "image/png"
    elif "webp" in file_type.lower():
        media_type = "image/webp"
    elif "gif" in file_type.lower():
        media_type = "image/gif"

    print(f"Media type: {media_type}", flush=True)
    print("Calling Anthropic API...", flush=True)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    print("API call completed!", flush=True)
    print(f"Response: {response}", flush=True)
    details = response.content[0].text
    print(f"Extracted details: {details}", flush=True)

    # Strip markdown code fences if present
    if details.startswith("```"):
        # Remove opening fence (```json or ```)
        details = details.split('\n', 1)[1] if '\n' in details else details[3:]
        # Remove closing fence (```)
        if details.endswith("```"):
            details = details.rsplit('\n```', 1)[0]
        details = details.strip()

    print(f"Cleaned details: {details}", flush=True)
    return details



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    import sys
    sys.stdout.flush()
    print("=== UPLOAD REQUEST RECEIVED ===", flush=True)
    print(str(request), flush=True)
    print(str(request.form), flush=True)
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    doc_type = request.form.get('fileType')
    file_type = file.mimetype
    if doc_type == '':
        return jsonify({'error': 'No file type selected'}), 400

    print("##########File Details############# ")
    print(file)
    print(file_type)
    print("pdf" in file_type)
    print("image/" in file_type)
    print(file_type)
    print("##########File Details############# ")


    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # support only images for now
    if "pdf" in file_type:
        return jsonify({'error': 'PDF file support coming soon!'}), 400
    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Encode the image as base64
    base64_image = encode_image_to_base64(filepath)

    try:
        # Process the image with OpenAI API
        details = process_image_with_openai(base64_image, doc_type, file_type)
        # Return extracted details as JSON
        return jsonify({'details': details})
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Something went wrong: {str(e)}'}), 400
    finally:
        print("Process finished")

    # Process the image with OpenAI API
    # details = process_image_with_openai(base64_image, doc_type, file_type)
    # # Return extracted details as JSON
    # return jsonify({'details': details})

if __name__ == '__main__':
    app.run(debug=True)

