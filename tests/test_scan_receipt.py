import unittest
import sys
import io
import os
from flask import Flask

# Add parent directory to Python path
sys.path.append('../')
from app import app, scan_receipt

class ScanReceiptTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the test client
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_scan_receipt(self):
        # Load a real image from disk or a valid image content in bytes
        receipt_path = os.path.join(os.path.dirname(__file__), 'receipt.jpeg')
        with open(receipt_path, 'rb') as image_file:
            image_data = image_file.read()

        sample_image = (io.BytesIO(image_data), 'receipt.jpg')

        # Simulate a POST request to /scan-receipt with a file
        response = self.client.post(
            '/scan-receipt',
            content_type='multipart/form-data',
            data={'receipt': sample_image}
        )

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        data = response.get_json()

        # Optionally, check if the values are correct (depending on the test case)
        self.assertEqual(data['message'], "Expense created. Please confirm to add it.")

    
