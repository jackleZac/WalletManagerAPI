import unittest
import sys
import datetime
import json
import dotenv
from datetime import datetime
from bson import ObjectId

# Add parent directory to Python path
sys.path.append('../')
from app import app, add_income, get_incomes, update_income, delete_income, connect_to_db;

class TestIncome(unittest.TestCase):
    """Test cases for handling income"""
    def setUp(self):
        # Create a connection to MongoDB Atlas
        self.client, self.db = connect_to_db()
        # Create a connection to collection 'income'
        self.collection_income = self.db['income']
        # Create a connection to collection 'wallet'
        self.collection_wallet = self.db['wallet']
        # Initialize test client to simulate requests to Flask App
        self.app = app.test_client()
        
    def tearDown(self):
        # Clean up resources in database
        self.collection_income.delete_many({})
        self.collection_wallet.delete_many({})
        
    def test_add_income(self):
        """It should add income to database and assert that it exists"""
        # Create and insert a wallet into database
        wallet_id = str(ObjectId())
        test_wallet = {
            "wallet_id": wallet_id,
            "name": "Account 1",
            "balance": 6000.00,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        }
        self.collection_wallet.insert_one(test_wallet)
        # Create an income with the the wallet_id
        test_income = {
            "source": "Salary",
            "amount": 6000,
            "description": "A monthly salary as Data Analyst",
            "date": datetime.now().isoformat(),
            "wallet_id": wallet_id
        }
        # Make a request to add_income function
        response = self.app.post('/income', json=test_income)
        # Assert that an income has been created
        self.assertEqual(response.status_code, 201)
        # Fetch the income from MongoDB atlas
        income_from_database = self.collection_income.find_one({"description": test_income["description"]})
        # Assert the income is not null
        self.assertIsNotNone(income_from_database)
        # Assert that the details are accurate
        self.assertEqual(income_from_database["amount"], test_income["amount"])
        self.assertEqual(income_from_database["source"], test_income["source"])
        self.assertEqual(income_from_database["wallet_id"], test_income["wallet_id"])
        # Fetch the corresponding wallet from database
        wallet_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id})
        # Calculate the expected balance of wallet
        expected_balance = test_wallet["balance"] + test_income["amount"]
        # Assert that the balance of wallet is updated
        self.assertEqual(wallet_from_database["balance"], expected_balance)
    
    def test_list_income(self):
        """It should get a list of all existing incomes"""
        test_incomes = [{
            "source": "Salary",
            "amount": 6000,
            "description": "A monthly salary as Data Analyst",
            "date": datetime.now().isoformat(),
            "wallet_id": "A1"
        },
           {
            "source": "Bonus",
            "amount": 1200,
            "description": "A monthly bonus as a Data Analyts",
            "date": datetime.now().isoformat(),
            "wallet_id": "A1"
        },
           {
            "source": "Second Job",
            "amount": 2000,
            "description": "Part-time Gym Trainer at Eagle GYm, London",
            "date": datetime.now().isoformat(),
            "wallet_id": "A1"
        }]
        # Insert a list of incomes into MongoDB Atlas
        insert_income = self.collection_income.insert_many(test_incomes)
        self.assertTrue(insert_income.acknowledged)
        # Make a GET request to get a list of existing incomes
        response = self.app.get('/income')
        # Assert that the incomes have been successfully retrieved
        self.assertEqual(response.status_code, 200)
        # Convert JSON data to Python dict
        response_dict = json.loads(response.data)
        self.assertEqual(len(response_dict["incomes"]), len(test_incomes))
        
    def test_update_income(self):
        """It should update income and assert that it is accurate"""
        # Create and insert a wallet into database
        wallet_id1 = str(ObjectId())
        wallet_id2 = str(ObjectId())
        test_wallets = [{
            "wallet_id": wallet_id1,
            "name": "Account 1",
            "balance": 6000.00, # Initial amount is set to 6000
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        },
            {
            "wallet_id": wallet_id2,
            "name": "Account 1",
            "balance": 0.00, # Initial amount is set to 0
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        }]
        self.collection_wallet.insert_many(test_wallets)
        # Create an income with the wallet_id
        test_income = {
            "source": "Salary",
            "amount": 6000, # An amount is set to 6000 and is added to wallet1
            "description": "A monthly salary as Data Analyst",
            "date": datetime.now().isoformat(),
            "wallet_id": wallet_id1 # An income is assigned to wallet_id1
        }
        # Insert an income into MongoDB Atlas
        insert_income = self.collection_income.insert_one(test_income)
        self.assertTrue(insert_income.acknowledged)
        if (insert_income):
            # If succeeds, fetch the income from MongoDB Atlas
            inserted_income = self.collection_income.find_one({"description": test_income["description"]})
            # Assert that the income exists
            self.assertIsNotNone(inserted_income)
            print(inserted_income)
            # Get the income id
            test_income_id = inserted_income["_id"]
            print(test_income_id)
            # Make changes to income
            update_income = {
                "source": "Salary",
                "amount": 1000, # An amount is changed from 6000 --> 1000
                "description": "Earn Side Hustle at Fiverr",
                "date": datetime.now().isoformat(),
                "wallet_id": wallet_id2 } # An income is assigned to wallet_id2
            # Make a PUT request to update existing income
            response = self.app.put(f'/income/{test_income_id}', json=update_income, content_type='application/json')
            # Assert that an income has been successfully updated
            self.assertEqual(response.status_code, 200)
            # Fetch the modified income from MongoDB Atlas
            updated_income = self.collection_income.find_one({"_id": test_income_id})
            self.assertIsNotNone(updated_income)
            # Assert the amount has been accurately updated
            self.assertEqual(updated_income["amount"], update_income["amount"])
            self.assertNotEqual(updated_income["amount"], test_income["amount"])
            # Assert that the wallet_id has been accurately updated
            self.assertEqual(updated_income["wallet_id"], update_income["wallet_id"])
            self.assertNotEqual(updated_income["wallet_id"], test_income["wallet_id"])
        else:
            # Raise an error if income was not inserted
            self.fail("Failed to insert income into database")
        # Fetch the corresponding wallet from database
        wallet1_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id1})
        wallet2_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id2})
        # Calculate the expected balance of wallet1
        expected_balance_wallet1 = test_wallets[0]["balance"] - test_income["amount"]
        # Calculate the expected balance of wallet2
        expected_balance_wallet2 = test_wallets[1]["balance"] + update_income["amount"]
        # Assert that the balance of wallet1 subtracted by 6000
        self.assertEqual(wallet1_from_database["balance"], expected_balance_wallet1)
        # Assert that the balance of wallet2 is added by 1000
        self.assertEqual(wallet2_from_database["balance"], expected_balance_wallet2)
            
    def test_delete_income(self):
        """It should delete an income"""
        # Create and insert a wallet into database
        wallet_id = str(ObjectId())
        test_wallet = {
            "wallet_id": wallet_id,
            "name": "Account 1",
            "balance": 6000.00,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "Savings",
            "target": 10000.00
        }
        self.collection_wallet.insert_one(test_wallet)
        # Create an income with the the wallet_id
        test_income = {
            "source": "Salary",
            "amount": 1000,
            "description": "Earn Side Hustle at Fiverr",
            "date": datetime.now().isoformat(),
            "wallet_id": wallet_id } 
        # Insert an income into MongoDB 
        insert_income = self.collection_income.insert_one(test_income)
        self.assertTrue(insert_income.acknowledged)
        # Retrieve income from database
        inserted_income = self.collection_income.find_one({"description": test_income["description"]})
        # Assert that the income exists
        self.assertIsNotNone(inserted_income)
        # Assert that the income ID is not None
        self.assertIsNotNone(inserted_income["_id"])
        test_income_id = inserted_income["_id"]
        print(test_income_id)
        # Make a DELETE request to delete income
        response = self.app.delete(f'/income/{test_income_id}')
        # Assert that the income has been successfully updated
        self.assertEqual(response.status_code, 200)
        # Make an attempt to fetch the income again
        deleted_income = self.collection_income.find_one({"_id": test_income_id})
        # Assert that the income is not found
        self.assertIsNone(deleted_income)
        # Assert that the balance of corresponding wallet is updated
        expected_balance = test_wallet["balance"] - test_income["amount"]
        # Fetch the corresponding wallet from database
        wallet_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id})
        self.assertEqual(wallet_from_database["balance"], expected_balance)