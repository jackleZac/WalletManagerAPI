from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from bson import ObjectId
import pymongo
from dateutil import parser
import datetime
import os 
from bson import ObjectId
import os

expense_bp = Blueprint('expense', __name__)

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


############################################################################################
#####                         ADD EXPENSE FUNCTIONS HERE                              ######
############################################################################################

@expense_bp.route('/expense', methods=['POST'])
def add_expense():
    """It should add an expense to database"""
    # Receive parsed data sent from the front-end (React)
    expense = request.json
    # Get wallet_id and amount of an income
    wallet_id = expense["wallet_id"]
    amount = expense["amount"]
    # Insert an expense into MongoDB Atlas
    expense_collection.insert_one(expense)
    # Find the corresponding wallet
    wallet = wallet_collection.find_one({"wallet_id": wallet_id})
    # Update a balance of the wallet
    if wallet:
            new_balance = wallet["balance"] - amount
            wallet_collection.update_one(
                {"wallet_id": wallet_id},
                {"$set": {"balance": new_balance, "updated_at": datetime.datetime.now()}}
            )
            return jsonify({"message": "Expense added and wallet balance updated"}), 201
    else:
        return jsonify({"error": "Wallet not found"}), 404


@expense_bp.route('/expense', methods=['GET'])
def get_expenses():
    """It should return a list of all available expenses"""
    # Get a list of expenses from MongoDB
    list_of_expenses = expense_collection.find({})
    # Convert the ObjectId instances to a JSON serializable format
    expenses = [
        {
         "_id": str(expense["_id"]), 
         "amount": expense["amount"], 
         "date": expense["date"], 
         "category": expense["category"],
         "description": expense["description"], 
         "wallet_id": expense["wallet_id"]
         } 
        for expense in list_of_expenses
    ]
    # Return a JSON document to the front-end
    return jsonify({'expenses': expenses})

@expense_bp.route('/expense/<string:_id>', methods=["PUT"])
def update_expense(_id):
    """It should update an expense"""
    # Get a content of updated expense
    updated_expense = request.json
    # Get the previous version of an income (outdated)
    outdated_expense = expense_collection.find_one({"_id": ObjectId(_id)})
    # Check if wallet_id and amount are modified (Skip if None are changed)
    if ((updated_expense["wallet_id"] != outdated_expense["wallet_id"]) or (updated_expense["amount"] != outdated_expense["amount"])):
        if (updated_expense["wallet_id"] != outdated_expense["wallet_id"]):
            # Scenario 1: Changes include wallet_id
            wallet_collection.update_one({"wallet_id": outdated_expense["wallet_id"]},
                {"$inc": {"balance": + outdated_expense["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
            wallet_collection.update_one({"wallet_id": updated_expense["wallet_id"]},
                {"$inc": {"balance": - updated_expense["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
        elif (updated_expense["wallet_id"] == outdated_expense["wallet_id"]) and (updated_expense["amount"] != outdated_expense["amount"]):
            # Scenario 2: Changes NOT include wallet_id
            wallet_collection.update_one({"wallet_id": outdated_expense["wallet_id"]},
            {"$set": {"balance": + outdated_expense["amount"] - updated_expense["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
    # Log the received ID for debugging
    expense_bp.logger.debug(f"Received ID: {_id}")
    # Find and update the expense in MongoDB
    response = expense_collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": updated_expense} )
    if response is None:
        # An expense with the specified id is not found
        return jsonify({"message": f'Expense with id: {_id} is not found'}), 404
    else:
        # An expense is found and updated
        return jsonify({"message": f'Expense with id: {_id} is updated'}), 200

@expense_bp.route('/expense/<string:_id>', methods=["DELETE"])
def delete_expense(_id):
    """It should delete an expense"""
    # Find and delete an expense from MongoDB
    response = expense_collection.find_one_and_delete({"_id": ObjectId(_id)})
    if response is None:
        # An expense is not found hence causing failure to delete
        return jsonify({"message": f'Failed to delete expense with id: {_id}'}), 404
    else:
        # Find and update the balance of corresponding wallet
        wallet_collection.update_one({"wallet_id": response["wallet_id"]},
            {"$inc": {"balance": - response["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
        # An expense is found and deleted
        return jsonify({"message": f'Expense with id: {_id} is deleted'}), 200
