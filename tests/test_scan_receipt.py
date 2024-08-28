import unittest
import io
from flask import Flask
from app import app  # Replace with the actual import of your Flask app

class ScanReceiptTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the test client
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_scan_receipt(self):
        # Create a sample in-memory file to upload
        sample_image = (io.BytesIO(b"fake image data"), 'receipt.jpg')

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

    
