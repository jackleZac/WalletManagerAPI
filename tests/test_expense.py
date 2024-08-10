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
        self.db = connect_to_db()
        # Initialize test client to simulate requests to Flask App
        self.app = app.test_client()
        
    def tearDown(self):
        # Clean up all resources in database
        self.db.delete_many({})
        
    
    def test_add_expense(self):
        """It should add an expense and assert that it exists"""
        expense_to_be_added = { "amount": 70.00, "date": datetime.datetime.now().isoformat(), "category": "Fitness", "description": "A Monthly Payment for Eagle Gym Membership", "repeatMonthly": True }
        # Make a POST request to def add_expense()
        response = self.app.post('/expense', json=expense_to_be_added)
        # Fetch the expense from MongoDB atlas
        expense_from_database = self.db.find_one({"description": expense_to_be_added["description"]})
        # Assert that an expense has been created
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(expense_from_database)
        # Assert that the details are accurate
        self.assertEqual(expense_from_database["amount"], expense_to_be_added["amount"])
        self.assertEqual(expense_from_database["category"], expense_to_be_added["category"])
        self.assertEqual(expense_from_database["description"], expense_to_be_added["description"])
        self.assertEqual(expense_from_database["repeatMonthly"], expense_to_be_added["repeatMonthly"])
        
    def test_list_expense(self):
        """It should get all expenses from database"""
        # Create a list of THREE expenses
        expenses_to_be_added = [
            {"amount": 70.00, "date": datetime.datetime.now().isoformat(), "category": "Fitness", "description": "A Monthly Payment for Eagle Gym Membership", "repeatMonthly": True },
            {"amount": 50.00, "date": datetime.datetime.now().isoformat(), "category": "Meals", "description": "Lunch at McDonald's", "repeatMonthly": False },
            {"amount": 40.00, "date": datetime.datetime.now().isoformat(), "category": "Car", "description": "Paid Gas", "repeatMonthly": False }, ]
        # Insert the list of expenses into MongoDB 
        self.db.insert_many(expenses_to_be_added)
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
            "repeatMonthly": True} 
        # Insert an expense into MongoDB 
        insert_expense = self.db.insert_one(expense_to_be_added)
        self.assertTrue(insert_expense.acknowledged)
        # Proceed when expense has been successfully inserted
        if (insert_expense):
            # Retrieve expense from database
            test_expense = self.db.find_one({"description": expense_to_be_added["description"]})
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
                "repeatMonthly": True} # repeatMonthly remains unchanged
            # Make a PUT request to def update_expense()
            response = self.app.put(f'/expense/{test_expense_id}', json=expense_updated, content_type='application/json')
            # Assert that the expense has been successfully updated
            self.assertEqual(response.status_code, 200)
            # Fetch the expense from MongoDB atlas
            expense_from_database = self.db.find_one({"_id": test_expense_id})
            # Assert that an expense exists
            self.assertIsNotNone(expense_from_database)
            # Assert that an expense has been updated
            self.assertEqual(expense_from_database["amount"], expense_updated["amount"])
            self.assertEqual(expense_from_database["description"], expense_updated["description"])
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
            "repeatMonthly": True} 
        # Insert an expense into MongoDB 
        insert_expense = self.db.insert_one(expense_to_be_added)
        self.assertTrue(insert_expense.acknowledged)
        # Retrieve expense from database
        test_expense = self.db.find_one({"description": expense_to_be_added["description"]})
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
        deleted_expense = self.db.find_one({"_id": test_expense_id})
        # Assert that the expense is not found
        self.assertIsNone(deleted_expense)


    """Test cases for handling income"""
    def setUp(self):
        # Create a connection to MongoDB Atlas
        self.db = connect_to_db()
        # Initialize test client to simulate requests to Flask App
        self.app = app.test_client()
        
    def tearDown(self):
        # Clean up resources in database
        self.db.delete_many({})
        
    def test_add_income(self):
        """It should add income to database and assert that it exists"""
        test_income = {
            "source": "Salary",
            "amount": 6000,
            "description": "A monthly salary as Data Analyst",
            "date": datetime.datetime.now().isoformat()
        }
        # Make a request to add_income function
        response = self.app.post('/income', json=test_income)
        # Assert that an expense has been created
        self.assertEqual(response.status_code, 201)
        # Fetch the expense from MongoDB atlas
        income_from_database = self.db.find_one({"description": test_income["description"]})
        # Assert the expense is not null
        self.assertIsNotNone(income_from_database)
        # Assert that the details are accurate
        self.assertEqual(income_from_database["amount"], test_income["amount"])
        self.assertEqual(income_from_database["source"], test_income["source"])
    
    def test_list_income(self):
        """It should get a list of all existing incomes"""
        test_incomes = [{
            "source": "Salary",
            "amount": 6000,
            "description": "A monthly salary as Data Analyst",
            "date": datetime.datetime.now().isoformat()
        },
           {
            "source": "Bonus",
            "amount": 1200,
            "description": "A monthly bonus as a Data Analyts",
            "date": datetime.datetime.now().isoformat()
        },
           {
            "source": "Second Job",
            "amount": 2000,
            "description": "Part-time Gym Trainer at Eagle GYm, London",
            "date": datetime.datetime.now().isoformat()
        }]
        # Insert a list of incomes into MongoDB Atlas
        insert_income = self.db.insert_many(test_incomes)
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
        test_income = {
            "source": "Salary",
            "amount": 6000,
            "description": "A monthly salary as Data Analyst",
            "date": datetime.datetime.now().isoformat()
        }
        # Insert an income into MongoDB Atlas
        insert_income = self.db.insert_one(test_income)
        self.assertTrue(insert_income.acknowledged)
        if (insert_income):
            # If succeeds, fetch the income from MongoDB Atlas
            inserted_income = self.db.find_one({"description": test_income["description"]})
            # Assert that the income exists
            self.assertIsNotNone(inserted_income)
            print(inserted_income)
            # Get the income id
            test_income_id = inserted_income["_id"]
            # Make changes to income
            update_income = {
                "source": "Salary",
                "amount": 1000,
                "description": "Earn Side Hustle at Fiverr",
                "date": datetime.datetime.now().isoformat() }
            # Make a PUT request to update existing income
            response = self.app.put(f'/income/{test_income_id}', json=update_income, content_type='application/json')
            # Assert that an income has been successfully updated
            self.assertEqual(response.status_code, 200)
            # Fetch the expense from MongoDB Atlas
            updated_income = self.db.find_one({"_id": test_income_id})
            self.assertIsNotNone(updated_income)
            # Assert the income has been accurately updated
            self.assertEqual(updated_income["source"], update_income["source"])
            self.assertEqual(updated_income["amount"], update_income["amount"])
        else:
            # Raise an error if expense was not inserted
            self.fail("Failed to insert expense into database")
            
    def test_delete_income(self):
        """It should delete an income"""
        test_income = {
            "source": "Salary",
            "amount": 1000,
            "description": "Earn Side Hustle at Fiverr",
            "date": datetime.datetime.now().isoformat() } 
        # Insert an expense into MongoDB 
        insert_income = self.db.insert_one(test_income)
        self.assertTrue(insert_income.acknowledged)
        # Retrieve expense from database
        inserted_income = self.db.find_one({"description": test_income["description"]})
        # Assert that the expense exists
        self.assertIsNotNone(inserted_income)
        # Assert that the expense ID is not None
        self.assertIsNotNone(inserted_income["_id"])
        test_income_id = inserted_income["_id"]
        print(test_income_id)
        # Make a DELETE request to delete income
        response = self.app.delete(f'/income/{test_income_id}')
        # Assert that the expense has been successfully updated
        self.assertEqual(response.status_code, 200)
        # Make an attempt to fetch the expense again
        deleted_income = self.db.find_one({"_id": test_income_id})
        # Assert that the expense is not found
        self.assertIsNone(deleted_income)    

if __name__=='__main__':
    unittest.main()