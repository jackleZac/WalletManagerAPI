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
from routes.budget import connect_to_db, add_budget, get_budget, list_budgets, update_budget, delete_budget

class TestBudget(unittest.TestCase):
    """Test case for handling budget"""
    def setUp(self):
        # Create a connection to MongoDB atlas
        self.client, self.db = connect_to_db()
        # Create a connection to collection 'budget'
        self.collection = self.db['budget']
        # Initialize test cleint to simulate requests to Flask App
        self.app = app.test_client()
        
    def tearDown(self):
        # Clean up recreated_ats in database
        self.collection.delete_many({})
        
    def test_add_budget(self):
        """It should add a budget to the database and assert that it exists"""
        test_budget = {
            "name": "Budget 1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {"Grocery": 400, "Health & Wellness": 150},
                "wants": {"Entertainment": 100, "Hobbies": 75},
                "bills": {"Housing": 1000, "Utilities": 200}
            }
        }
        # Make a POST request to add the budget
        response = self.app.post('/budget', json=test_budget, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Fetch the budget from MongoDB Atlas
        budget_from_database = self.collection.find_one({"name": test_budget["name"]})
        self.assertIsNotNone(budget_from_database)

        # Validate the details
        self.assertDictEqual(budget_from_database["categories"]["needs"], test_budget["categories"]["needs"])
        self.assertDictEqual(budget_from_database["categories"]["wants"], test_budget["categories"]["wants"])
        self.assertDictEqual(budget_from_database["categories"]["bills"], test_budget["categories"]["bills"])

    
    def test_list_budgets(self):
        """It should get a list of all existing budgets"""
        test_budgets = [{
            "name": "Budget 1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {
                    "Grocery": 400, 
                    "Health & Wellness": 150  
                },
                "wants": {
                    "Entertainment": 100,
                    "Hobbies": 75 
                },
                "bills": {
                    "Housing": 1000, 
                    "Utilities": 200
                }
            }
        },
           {
            "name": "Budget 2",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {
                    "Grocery": 400, 
                    "Health & Wellness": 150  
                },
                "wants": {
                    "Entertainment": 100,
                    "Hobbies": 75 
                },
                "bills": {
                    "Housing": 1000, 
                    "Utilities": 200
                }
            }
        },
           {
            "name": "Budget 3",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {
                    "Grocery": 400, 
                    "Health & Wellness": 150  
                },
                "wants": {
                    "Entertainment": 100,
                    "Hobbies": 75 
                },
                "bills": {
                    "Housing": 1000, 
                    "Utilities": 200
                }
            }
        }]
        # Insert a list of budgets into MongoDB Atlas
        insert_budget = self.collection.insert_many(test_budgets)
        self.assertTrue(insert_budget.acknowledged)
        # Make a GET request to get a list of existing budgets
        response = self.app.get('/budget')
        # Assert that the budgets have been successfully retrieved
        self.assertEqual(response.status_code, 200)
        # Convert JSON data to Python dict
        response_dict = json.loads(response.data)
        self.assertEqual(len(response_dict["budgets"]), len(test_budgets))

    def test_get_budget(self):
        """It should get the correct budget with given id"""
        test_budget = {
            "name": "Budget 1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {
                    "Grocery": 400, 
                    "Health & Wellness": 150  
                },
                "wants": {
                    "Entertainment": 100,
                    "Hobbies": 75 
                },
                "bills": {
                    "Housing": 1000, 
                    "Utilities": 200
                }
            }
        }
        # Insert a budget into MongoDB Atlas
        insert_budget = self.collection.insert_one(test_budget)
        self.assertTrue(insert_budget.acknowledged)
        # Fetch the budget from MongoDB atlas
        budget_from_database = self.collection.find_one({"name": test_budget["name"]})
        # Assert the budget is not null
        self.assertIsNotNone(budget_from_database)
        budget_id = budget_from_database["_id"]
        response = self.app.get(f'budget/{budget_id}')
        # Validate each part of categories in detail
        self.assertDictEqual(response["categories"]["needs"], test_budget["categories"]["needs"])
        self.assertDictEqual(response["categories"]["wants"], test_budget["categories"]["wants"])
        self.assertDictEqual(response["categories"]["bills"], test_budget["categories"]["bills"])
               
    def test_update_budget(self):
        """It should update budget and assert that it is accurate"""
        test_budget = {
            "name": "Budget 1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {
                    "Grocery": 400, 
                    "Health & Wellness": 150  
                },
                "wants": {
                    "Entertainment": 100,
                    "Hobbies": 75 
                },
                "bills": {
                    "Housing": 1000, 
                    "Utilities": 200
                }
            }
        }
        # Insert a budget into MongoDB Atlas
        insert_budget = self.collection.insert_one(test_budget)
        self.assertTrue(insert_budget.acknowledged)
        if (insert_budget):
            # If succeeds, fetch the budget from MongoDB Atlas
            inserted_budget = self.collection.find_one({"name": test_budget["name"]})
            # Assert that the budget exists
            self.assertIsNotNone(inserted_budget)
            print(inserted_budget)
            # Get the budget id
            test_budget_id = inserted_budget["_id"]
            # Make changes to budget balance
            update_budget = {
            "name": "My first budget",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {
                    "Grocery": 200, 
                    "Health & Wellness": 100  
                },
                "wants": {
                    "Entertainment": 50,
                    "Hobbies": 70 
                },
                "bills": {
                    "Housing": 1200, 
                    "Utilities": 400
                }
            }
        }
            # Make a PUT request to update existing budget
            response = self.app.put(f'/budget/{test_budget_id}', json=update_budget, content_type='application/json')
            # Assert that an budget has been successfully updated
            self.assertEqual(response.status_code, 200)
            # Fetch the budget from MongoDB Atlas
            updated_budget = self.collection.find_one({"budget_id": test_budget_id})
            self.assertIsNotNone(updated_budget)
             # Validate each part of categories in detail
            self.assertDictEqual(updated_budget["categories"]["needs"], test_budget["categories"]["needs"])
            self.assertDictEqual(updated_budget["categories"]["wants"], test_budget["categories"]["wants"])
            self.assertDictEqual(updated_budget["categories"]["bills"], test_budget["categories"]["bills"])
        else:
            # Raise an error if budget was not inserted
            self.fail("Failed to insert budget into database")
            
    def test_delete_budget(self):
        """It should delete a budget"""
        test_budget = {
            "name": "Budget 1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "categories": {
                "needs": {"Grocery": 400, "Health & Wellness": 150},
                "wants": {"Entertainment": 100, "Hobbies": 75},
                "bills": {"Housing": 1000, "Utilities": 200}
            }
        }
        # Insert a budget into MongoDB 
        insert_budget = self.collection.insert_one(test_budget)
        self.assertTrue(insert_budget.acknowledged)
        test_budget_id = insert_budget.inserted_id

        # Make a DELETE request to delete the budget
        response = self.app.delete(f'/budget/{test_budget_id}')
        self.assertEqual(response.status_code, 200)

        # Check that the budget no longer exists in the database
        deleted_budget = self.collection.find_one({"_id": test_budget_id})
        self.assertIsNone(deleted_budget)
