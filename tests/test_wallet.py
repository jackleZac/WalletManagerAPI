import unittest
import sys
import datetime
import json
import dotenv
from bson import ObjectId
from datetime import datetime, timedelta

# Add parent directory to Python path
sys.path.append('../')
from app import app
from routes.wallet import connect_to_db, add_wallet, list_wallets, update_wallet, delete_wallet

class TestWallet(unittest.TestCase):
    """Test case for handling wallet"""
    def setUp(self):
        # Create a connection to MongoDB atlas
        self.client, self.db = connect_to_db()
        # Create a connection to collection 'wallet'
        self.collection_wallet = self.db['wallet']
        # Create a connection to collection 'budget'
        self.collection_budget = self.db['budget']
        # Initialize test cleint to simulate requests to Flask App
        self.app = app.test_client()
        # Create a budget for all test wallets
        test_budget = {
            "name": "Budget 1",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "categories": {
                "needs": {"Grocery": 400, "Health & Wellness": 150},
                "wants": {"Entertainment": 100, "Hobbies": 75},
                "bills": {"Housing": 1000, "Utilities": 200}
            }
        }
        # Make a POST request to add the budget
        self.app.post('/budget', json=test_budget, content_type='application/json')
        # Get the budget_id
        budget = self.collection_budget.insert_one(test_budget)
        self.budget_id = budget.inserted_id
        
    def tearDown(self):
        # Clean up collections in the database
        self.collection_wallet.delete_many({})
        self.collection_budget.delete_many({})
        
    def test_add_wallet(self):
        """It should add wallet to database and assert that it exists"""
        test_wallet = {
            "name": "Account 1",
            "balance": 6000.00,
            "budget_id": str(self.budget_id),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        }
        # Make a request to add_wallet function
        response = self.app.post('/wallet', json=test_wallet)
        # Assert that an wallet has been created
        self.assertEqual(response.status_code, 201)
        # Fetch the wallet from MongoDB atlas
        wallet_from_database = self.collection_wallet.find_one({"name": test_wallet["name"]})
        # Assert the wallet is not null
        self.assertIsNotNone(wallet_from_database)
        # Assert that the details are accurate
        self.assertEqual(wallet_from_database["balance"], test_wallet["balance"])
        self.assertAlmostEqual(wallet_from_database["created_at"], test_wallet["created_at"], delta=timedelta(seconds=1))
        self.assertAlmostEqual(wallet_from_database["updated_at"], test_wallet["updated_at"], delta=timedelta(seconds=1))
        self.assertEqual(wallet_from_database["type"], test_wallet["type"])
        self.assertEqual(wallet_from_database["target"], test_wallet["target"])
    
    
    def test_list_wallet(self):
        """It should get a list of all existing wallets"""
        test_wallets = [{
            "wallet_id": str(ObjectId()),
            "name": "Account 1",
            "budget_id": str(self.budget_id),
            "balance": 6000.00,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        },
           {
            "wallet_id": str(ObjectId()),
            "name": "Account 2",
            "budget_id": str(self.budget_id),
            "balance": 5000.00,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        },
           {
            "wallet_id": str(ObjectId()),
            "name": "Account 3",
            "budget_id": str(self.budget_id),
            "balance": 4000.00,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        }]
        # Insert a list of wallets into MongoDB Atlas
        insert_wallet = self.collection_wallet.insert_many(test_wallets)
        self.assertTrue(insert_wallet.acknowledged)
        # Make a GET request to get a list of existing wallets
        response = self.app.get('/wallet')
        # Assert that the wallets have been successfully retrieved
        self.assertEqual(response.status_code, 200)
        # Convert JSON data to Python dict
        response_dict = json.loads(response.data)
        self.assertEqual(len(response_dict["wallets"]), len(test_wallets))
        
    def test_update_wallet(self):
        """It should update wallet and assert that it is accurate"""
        test_wallet = {
            "wallet_id": str(ObjectId()),
            "name": "Account 1",
            "budget_id": str(self.budget_id),
            "balance": 6000.00,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        }
        # Insert a wallet into MongoDB Atlas
        insert_wallet = self.collection_wallet.insert_one(test_wallet)
        self.assertTrue(insert_wallet.acknowledged)
        if (insert_wallet):
            # If succeeds, fetch the wallet from MongoDB Atlas
            inserted_wallet = self.collection_wallet.find_one({"name": test_wallet["name"]})
            # Assert that the wallet exists
            self.assertIsNotNone(inserted_wallet)
            print(inserted_wallet)
            # Get the wallet id
            test_wallet_id = test_wallet["wallet_id"]
            # Create an instance of current datetime
            datetime_current = datetime.now()
            formatted_updated_at = datetime_current.isoformat()
            # Make changes to wallet balance
            update_wallet = {
                "name": "Account 1",
                "budget_id": str(self.budget_id),
                "balance": 1000.00,
                "updated_at": formatted_updated_at,
                "type": "Savings",
                "target": 10000.00 }
            # Make a PUT request to update existing wallet
            response = self.app.put(f'/wallet/{test_wallet_id}', json=update_wallet, content_type='application/json')
            # Assert that an wallet has been successfully updated
            self.assertEqual(response.status_code, 200)
            # Fetch the wallet from MongoDB Atlas
            updated_wallet = self.collection_wallet.find_one({"wallet_id": test_wallet_id})
            self.assertIsNotNone(updated_wallet)
            # Assert that the balance is accurately updated
            self.assertEqual(updated_wallet["balance"], update_wallet["balance"])
            # Assert that the modification date of wallet is updated
            self.assertAlmostEqual(updated_wallet["updated_at"], update_wallet["updated_at"], delta=timedelta(seconds=1))
        else:
            # Raise an error if wallet was not inserted
            self.fail("Failed to insert wallet into database")
            
    def test_delete_wallet(self):
        """It should delete a wallet"""
        test_wallet = {
            "wallet_id": str(ObjectId()),
            "name": "Account 1",
            "budget_id": str(self.budget_id),
            "balance": 1000.00,
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00  } 
        # Insert an wallet into MongoDB 
        insert_wallet = self.collection_wallet.insert_one(test_wallet)
        # Assert that the wallet has been inserted into MongoDB
        self.assertTrue(insert_wallet.acknowledged)
        test_wallet_id = test_wallet["wallet_id"]
        print(test_wallet_id)
        # Make a DELETE request to delete wallet
        response = self.app.delete(f'/wallet/{test_wallet_id}')
        # Assert that the wallet has been successfully deleted
        self.assertEqual(response.status_code, 200)
        # Make an attempt to fetch the wallet again
        deleted_wallet = self.collection_wallet.find_one({"wallet_id": test_wallet_id})
        # Assert that the wallet is not found
        self.assertIsNone(deleted_wallet)