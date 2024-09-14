from flask import Blueprint, request, jsonify
from dateutil import parser
from google.cloud import documentai_v1beta3 as documentai
from google.oauth2 import service_account
import os

scanner_bp = Blueprint('scanner', __name__)

############################################################################################
#####                         ADD SCAN RECEIPT FUNCTIONS HERE                         ######
############################################################################################

# Load your Google Cloud service account credentials from the environment variable
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
credentials = service_account.Credentials.from_service_account_file(credentials_path)

# Set Document AI processor details
project_id = 'apt-reality-433311-j4'
location = 'us'
processor_id = 'b348edb6e0374f40'  # This is your processor ID

@scanner_bp.route('/scan-receipt', methods=['POST'])
def scan_receipt():
    try:
        # Check if a file was uploaded
        if 'receipt' not in request.files:
            return jsonify({"error": "No receipt file uploaded"}), 400

        file = request.files['receipt']
        image_content = file.read()

        # Initialize the Document AI client
        client = documentai.DocumentProcessorServiceClient(credentials=credentials)

        # Configure the request to Document AI
        name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        document = documentai.types.Document(content=image_content, mime_type='image/jpeg')
        doc_request = documentai.types.ProcessRequest(name=name, raw_document=documentai.types.RawDocument(content=image_content, mime_type='image/jpeg'))

        # Process the document
        result = client.process_document(request=doc_request)

        # Extract relevant information from the result
        document = result.document
        amount = None
        description = None
        date = None
        iso_date = None
        
        for entity in document.entities:
            if entity.type_ == "total_amount":
                amount = entity.mention_text
            if entity.type_ == "supplier_name":
                description = entity.mention_text
            if entity.type_ == "receipt_date":
                date = entity.mention_text
        
        # Convert various date formats to ISO format (yyyy-mm-dd)
        if date:
            try:
                parsed_date = parser.parse(date)
                iso_date = parsed_date.date().isoformat()
            except (ValueError, TypeError) as e:
                print(f"Error parsing date: {e}")
                iso_date = None
       
        if amount:
            try:
                float_amount = float(amount.replace(',', ''))
                int_amount = round(float_amount)
            except (ValueError, TypeError) as e:
                print(f"Error parsing date: {e}")
                iso_date = None
                
        # Print extracted information for debugging
        print("Total Amount:", int_amount)
        print("Description:", description)
        print("Receipt Date:", iso_date)
        # Return the extracted data as a JSON response
        return jsonify({
            "amount": int_amount,
            "description": description,
            "date": iso_date,
            "message": "Expense created. Please confirm to add it."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
