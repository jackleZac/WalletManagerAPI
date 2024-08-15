import unittest
import sys
import datetime
import json
import dotenv

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
        
    
    def test_add_expense(self):
        """It should add an expense and assert that it exists"""
        expense_to_be_added = { "amount": 70.00, "date": datetime.datetime.now().isoformat(), "category": "Fitness", "description": "A Monthly Payment for Eagle Gym Membership", "wallet_id": "A1" }
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
        
    def test_list_expense(self):
        """It should get all expenses from database"""
        # Create a list of THREE expenses
        expenses_to_be_added = [
            {"amount": 70.00, "date": datetime.datetime.now().isoformat(), "category": "Fitness", "description": "A Monthly Payment for Eagle Gym Membership", "wallet_id": "A1" },
            {"amount": 50.00, "date": datetime.datetime.now().isoformat(), "category": "Meals", "description": "Lunch at McDonald's", "wallet_id": "A1" },
            {"amount": 40.00, "date": datetime.datetime.now().isoformat(), "category": "Car", "description": "Paid Gas", "wallet_id": "A2" } ]
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
        expense_to_be_added = {
            "amount": 70.00, 
            "date": datetime.datetime.now().isoformat(), 
            "category": "Fitness", 
            "description": "A Monthly Payment for Eagle Gym Membership", 
            "wallet_id": "A1"} 
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
                "date": datetime.datetime.now().isoformat(), # Update date
                "category": "Fitness", # category remains unchanged
                "description": "A Monthly Payment for BJJ Membership", # Update description
                "wallet_id": "A2"} # wallet_id is changed
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
             
    def test_delete_expense(self):
        """It should delete an expense"""
        expense_to_be_added = {
            "amount": 70.00, 
            "date":datetime.datetime.now().isoformat(), 
            "category": "Fitness", 
            "description": "A Monthly Payment for Eagle Gym Membership", 
            "wallet_id": "A1"} 
        # Insert an expense into MongoDB 
        insert_expense = self.collection_expense.insert_one(expense_to_be_added)
        self.assertTrue(insert_expense.acknowledged)
        # Retrieve expense from database
        test_expense = self.collection_expense.find_one({"description": expense_to_be_added["description"]})
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
  

if __name__=='__main__':
    unittest.main()