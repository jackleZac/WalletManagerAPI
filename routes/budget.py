from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from bson import ObjectId
import pymongo
from dateutil import parser
import datetime
import os

budget_bp = Blueprint('budget', __name__)

# Load config from .env file
load_dotenv()
MONGODB_URI = os.environ['MONGODB_URI']

def connect_to_db():
    # Set up a connection to MongoDB cluster
    try:
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        if client.server_info():
            print('SUCCESS: MongoDB is connected!')
            # Getting a database
            db = client['myfinance']
            return client, db
        else:
            print('ERROR: MongoDB is not connected!')
    except pymongo.errors.ServerSelectionTimeoutError:
        print('ERROR: MongoDB connection timed out!')
    except Exception as e:
        print('ERROR: An unexpected error occurrred: {e}')
    
client, database_collection = connect_to_db()
expense_collection = database_collection['expense']
income_collection = database_collection['income']
wallet_collection = database_collection['wallet']
budget_collection = database_collection['budget']

############################################################################################
#####                         ADD BUDGET HERE                                         ######
############################################################################################

@budget_bp.route('/budget', methods=['POST'])
def add_budget():
    """It should add a budget to database"""
    # Receive parsed data sent from the front-end (React)
    budget = request.json
    # Insert an budget into MongoDB Atlas
    budget_collection.insert_one(budget)
    # Return a success message
    return jsonify({"Message": "A budget has been succesfully added"}), 201

@budget_bp.route('/budget', methods=['GET'])
def list_budgets():
    """It should return a list of all available expenses"""
    # Get a list of budgets from MongoDB
    list_of_budgets = budget_collection.find({})
    # Convert the ObjectId instances to a JSON serializable format
    budgets = [
        {
         "budget_id": str(budget["_id"]),  
         "created_at": budget["created_at"], 
         "updated_at": budget["updated_at"],
         "wallet_id": budget["wallet_id"],
         "categories": {
                "needs": budget["categories"].get("needs", {}),
                "wants": budget["categories"].get("wants", {}),
                "bills": budget["categories"].get("bills", {})
            }
         } 
        for budget in list_of_budgets
    ]
    # Return a JSON document to the front-end
    return jsonify({'budgets': budgets})

@budget_bp.route('/budget/<budget_id>', methods=['GET'])
def get_budget(budget_id):
    """Retrieve a single budget by its budget_id."""
    # Find the budget in MongoDB by budget_id
    budget = budget_collection.find_one({"budget_id": ObjectId(budget_id)})
    
    if budget:
        # Convert the ObjectId to a JSON serializable format
        budget_data = {
            "budget_id": str(budget["_id"]),
            "created_at": budget["created_at"], 
            "updated_at": budget["updated_at"],
            "wallet_id": budget["wallet_id"],
            "categories": {
                "needs": budget["categories"].get("needs", {}),
                "wants": budget["categories"].get("wants", {}),
                "bills": budget["categories"].get("bills", {})
            }
        }
        # Return the budget details in JSON format
        return jsonify({'budget': budget_data})
    else:
        # Return a 404 error if the budget is not found
        return jsonify({"error": "Budget not found"}), 404

@budget_bp.route('/budget/<string:budget_id>', methods=["PUT"])
def update_budget(budget_id):
    """It should update a budget"""
    # Get a content of updated budget
    updated_budget = request.json
    # Log the received ID for debugging
    budget_bp.logger.debug(f"Received ID: {budget_id}")
    # Find and update the budget in MongoDB
    response = budget_collection.find_one_and_update(
        {"_id": ObjectId(budget_id)},
        {"$set": updated_budget} )
    if response is None:
        # A budget with the specified id is not found
        return jsonify({"message": f'budget with id: {budget_id} is not found'}), 404
    # Find and delete all wallets associated with this budget_id
    wallets = wallet_collection.find({"budget_id": str(budget_id)})
    wallet_ids = [str(wallet["_id"]) for wallet in wallets]  # Collect wallet IDs for deletion of incomes/expenses
    wallet_result = wallet_collection.delete_many({"budget_id": str(budget_id)})
    # Delete incomes and expenses for each deleted wallet
    total_incomes_deleted = 0
    total_expenses_deleted = 0
    for wallet_id in wallet_ids:
        income_result = income_collection.delete_many({"wallet_id": wallet_id})
        expense_result = expense_collection.delete_many({"wallet_id": wallet_id})
        total_incomes_deleted += income_result.deleted_count
        total_expenses_deleted += expense_result.deleted_count
    # Return success message, including number of related documents deleted
    return jsonify({
        "message": f'Budget with id: {budget_id} is deleted',
        "wallets_deleted": wallet_result.deleted_count,
        "incomes_deleted": total_incomes_deleted,
        "expenses_deleted": total_expenses_deleted
    }), 200

@budget_bp.route('/budget/<string:budget_id>', methods=["DELETE"])
def delete_budget(budget_id):
    """It should delete a budget and all associated wallets, incomes, and expenses"""
    # Find and delete the budget from MongoDB
    budget_response = budget_collection.find_one_and_delete({"_id": ObjectId(budget_id)})
    if budget_response is None:
        # Budget id is not found, unable to delete
        return jsonify({"message": f'Failed to delete budget with id: {budget_id}'}), 404
    # Find and delete all wallets associated with this budget_id
    wallets = wallet_collection.find({"budget_id": str(budget_id)})
    wallet_ids = [str(wallet["_id"]) for wallet in wallets]  # Collect wallet IDs for deletion of incomes/expenses
    wallet_result = wallet_collection.delete_many({"budget_id": str(budget_id)})
    # Delete incomes and expenses for each deleted wallet
    total_incomes_deleted = 0
    total_expenses_deleted = 0
    for wallet_id in wallet_ids:
        income_result = income_collection.delete_many({"wallet_id": wallet_id})
        expense_result = expense_collection.delete_many({"wallet_id": wallet_id})
        total_incomes_deleted += income_result.deleted_count
        total_expenses_deleted += expense_result.deleted_count
    # Return success message, including number of related documents deleted
    return jsonify({
        "message": f'Budget with id: {budget_id} is deleted',
        "wallets_deleted": wallet_result.deleted_count,
        "incomes_deleted": total_incomes_deleted,
        "expenses_deleted": total_expenses_deleted
    }), 200
