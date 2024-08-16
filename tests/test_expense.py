import unittest
import sys
from datetime import datetime
import json
import dotenv
from bson import ObjectId

# Add parent directory to Python path
sys.path.append('../')
from app import app, add_expense, get_expenses, update_expense, delete_expense, connect_to_db

class TestExpenses(unittest.TestCase):
    """Test cases for handling expenses"""
    def setUp(self):
        # Create a connection to MongoDB Atlas 
        self.client, self.db = connect_to_db()
        # Create a connection to collection 'expense'
        self.collection_expense = self.db['expense']
        # Create a connection to collection 'wallet'
        self.collection_wallet = self.db['wallet']
        # Initialize test client to simulate requests to Flask App
        self.app = app.test_client()
        
    def tearDown(self):
        # Clean up all resources in database
        self.collection_expense.delete_many({})
        self.collection_wallet.delete_many({})
         
    def test_add_expense(self):
        """It should add an expense and assert that it exists"""
        # Create and insert a wallet into database
        wallet_id = str(ObjectId())
        test_wallet = {
            "wallet_id": wallet_id,
            "name": "Account 1",
            "balance": 6000.00,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "Savings",
            "target": 10000.00
        }
        self.collection_wallet.insert_one(test_wallet)
        # Create an income with the the wallet_id
        expense_to_be_added = { 
            "amount": 70.00, 
            "date": datetime.now().isoformat(), 
            "category": "Fitness", 
            "description": "A Monthly Payment for Eagle Gym Membership", 
            "wallet_id": wallet_id 
        }
        # Make a POST request to def add_expense()
        response = self.app.post('/expense', json=expense_to_be_added)
        # Fetch the expense from MongoDB atlas
        expense_from_database = self.collection_expense.find_one({"description": expense_to_be_added["description"]})
        # Assert that an expense has been created
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(expense_from_database)
        # Assert that the details are accurate
        self.assertEqual(expense_from_database["amount"], expense_to_be_added["amount"])
        self.assertEqual(expense_from_database["category"], expense_to_be_added["category"])
        self.assertEqual(expense_from_database["description"], expense_to_be_added["description"])
        self.assertEqual(expense_from_database["wallet_id"], expense_to_be_added["wallet_id"])
        # Fetch the corresponding wallet from database
        wallet_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id})
        # Calculate the expected balance of wallet
        expected_balance = test_wallet["balance"] + expense_to_be_added["amount"]
        # Assert that the balance of wallet is updated
        self.assertEqual(wallet_from_database["balance"], expected_balance)
        
    def test_list_expense(self):
        """It should get all expenses from database"""
        # Create a list of THREE expenses
        expenses_to_be_added = [{
            "amount": 70.00, 
            "date": datetime.now().isoformat(), 
            "category": "Fitness", 
            "description": "A Monthly Payment for Eagle Gym Membership", 
            "wallet_id": "A1" 
        },
        {
            "amount": 50.00, 
            "date": datetime.now().isoformat(), 
            "category": "Meals", 
            "description": "Lunch at McDonald's", 
            "wallet_id": "A1" 
        },
        {
            "amount": 40.00, 
            "date": datetime.now().isoformat(), 
            "category": "Car", 
            "description": "Paid Gas", 
            "wallet_id": "A2" 
        }]
        # Insert the list of expenses into MongoDB 
        self.collection_expense.insert_many(expenses_to_be_added)
        # Make a GET request to def get_expenses()
        response = self.app.get('/expense')
        # Assert that it has been successfully retrieved
        self.assertEqual(response.status_code, 200)
        # Convert JSON data to Python dict
        response_dict = json.loads(response.data)
        # Assert that the number of expenses returned is equal to the number of test expenses
        self.assertEqual(len(response_dict['expenses']), len(expenses_to_be_added))
        # Assert that the expenses returned are similar to the test expenses
        found = False
        for test_expense in expenses_to_be_added:
            for expense in response_dict["expenses"]:
                if expense["description"] == test_expense["description"]:
                    found = True
                    break
            self.assertTrue(found)
            
    def test_update_expense(self):
        """It should update an expense from a database"""
        # Create and insert a wallet into database
        wallet_id1 = str(ObjectId())
        wallet_id2 = str(ObjectId())
        test_wallets = [{
            "wallet_id": wallet_id1,
            "name": "Account 1",
            "balance": 6000.00, # Initial amount is set to 6000
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "Savings",
            "target": 10000.00
        },
            {
            "wallet_id": wallet_id2,
            "name": "Account 1",
            "balance": 1000.00, # Initial amount is set to 1000
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "Savings",
            "target": 10000.00
        }]
        self.collection_wallet.insert_many(test_wallets)
        # Create an income with the wallet_id
        expense_to_be_added = {
            "amount": 70.00, # An amount is set to 6000 and is added to wallet1
            "date": datetime.now(), 
            "category": "Fitness", 
            "description": "A Monthly Payment for Eagle Gym Membership", 
            "wallet_id": wallet_id1 # An expense is assigned to wallet_id1
        } 
        # Insert an expense into MongoDB 
        insert_expense = self.collection_expense.insert_one(expense_to_be_added)
        self.assertTrue(insert_expense.acknowledged)
        # Proceed when expense has been successfully inserted
        if (insert_expense):
            # Retrieve expense from database
            test_expense = self.collection_expense.find_one({"description": expense_to_be_added["description"]})
            # Assert that the expense exists
            self.assertIsNotNone(test_expense)
            print(test_expense)
            # Assert that the expense ID is not None
            self.assertIsNotNone(test_expense["_id"])
            print(test_expense["_id"])
            test_expense_id = test_expense["_id"]
            # Make changes to an expense amount, date and description
            expense_updated = {
                "amount": 241.00, # Update price
                "date": datetime.now().isoformat(), # Update date
                "category": "Fitness", # category remains unchanged
                "description": "A Monthly Payment for BJJ Membership", # Update description
                "wallet_id": wallet_id2} # wallet_id is changed
            # Make a PUT request to def update_expense()
            response = self.app.put(f'/expense/{test_expense_id}', json=expense_updated, content_type='application/json')
            # Assert that the expense has been successfully updated
            self.assertEqual(response.status_code, 200)
            # Fetch the expense from MongoDB atlas
            expense_from_database = self.collection_expense.find_one({"_id": test_expense_id})
            # Assert that an expense exists
            self.assertIsNotNone(expense_from_database)
            # Assert that an expense has been updated
            self.assertEqual(expense_from_database["amount"], expense_updated["amount"])
            self.assertEqual(expense_from_database["description"], expense_updated["description"])
            self.assertEqual(expense_from_database["wallet_id"], expense_updated["wallet_id"])
        else:
            # Raise an error if expense was not inserted
             self.fail("Failed to insert expense into database")
        # Fetch the corresponding wallet from database
        wallet1_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id1})
        wallet2_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id2})
        # Calculate the expected balance of wallet1
        expected_balance_wallet1 = test_wallets[0]["balance"] + expense_to_be_added["amount"]
        # Calculate the expected balance of wallet2
        expected_balance_wallet2 = test_wallets[1]["balance"] - expense_updated["amount"]
        # Print debug information
        print(f"Expected wallet1 balance: {expected_balance_wallet1}")
        print(f"Actual wallet1 balance: {wallet1_from_database['balance']}")
        print(f"Expected wallet2 balance: {expected_balance_wallet2}")
        print(f"Actual wallet2 balance: {wallet2_from_database['balance']}")
        # Assert that the balance of wallet1 added by 70
        self.assertEqual(wallet1_from_database["balance"], expected_balance_wallet1)
        # Assert that the balance of wallet2 is subtracted by 241
        self.assertEqual(wallet2_from_database["balance"], expected_balance_wallet2)
        
    def test_delete_expense(self):
        """It should delete an expense"""
        # Create and insert a wallet into database
        wallet_id = str(ObjectId())
        test_wallet = {
            "wallet_id": wallet_id,
            "name": "Account 1",
            "balance": 6000.00,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "Savings",
            "target": 10000.00
        }
        self.collection_wallet.insert_one(test_wallet)
        # Create an income with the the wallet_id
        expense_to_be_deleted = {
            "amount": 70.00, 
            "date":datetime.now(), 
            "category": "Fitness", 
            "description": "A Monthly Payment for Eagle Gym Membership", 
            "wallet_id": wallet_id} 
        # Insert an expense into MongoDB 
        insert_expense = self.collection_expense.insert_one(expense_to_be_deleted)
        self.assertTrue(insert_expense.acknowledged)
        # Retrieve expense from database
        test_expense = self.collection_expense.find_one({"description": expense_to_be_deleted["description"]})
        # Assert that the expense exists
        self.assertIsNotNone(test_expense)
        # Assert that the expense ID is not None
        self.assertIsNotNone(test_expense["_id"])
        test_expense_id = test_expense["_id"]
        # Make a DELETE request to def delete_expense()
        response = self.app.delete(f'/expense/{test_expense_id}')
        # Assert that the expense has been successfully updated
        self.assertEqual(response.status_code, 200)
        # Make an attempt to fetch the expense again
        deleted_expense = self.collection_expense.find_one({"_id": test_expense_id})
        # Assert that the expense is not found
        self.assertIsNone(deleted_expense)
        # Assert that the balance of corresponding wallet is updated
        expected_balance = test_wallet["balance"] - expense_to_be_deleted["amount"]
        # Fetch the corresponding wallet from database
        wallet_from_database = self.collection_wallet.find_one({"wallet_id": wallet_id})
        self.assertEqual(wallet_from_database["balance"], expected_balance)
