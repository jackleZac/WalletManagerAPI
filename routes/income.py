from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from bson import ObjectId
import pymongo
from dateutil import parser
import datetime
import os

income_bp = Blueprint('income', __name__)

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
#####                         ADD INCOME HERE                                         ######
############################################################################################

@income_bp.route('/income', methods=['POST'])
def add_income():
    # Receive parsed data sent from the front-end (React)
    income = request.json
    # Get wallet_id and amount of an income
    wallet_id = income["wallet_id"]
    amount = income["amount"]
    # Insert income into database
    income_collection.insert_one(income)
    # Find the corresponding wallet
    wallet = wallet_collection.find_one({"wallet_id": wallet_id})
    # Update a balance of the wallet
    if wallet:
            new_balance = wallet["balance"] + amount
            wallet_collection.update_one(
                {"wallet_id": wallet_id},
                {"$set": {"balance": new_balance, "updated_at": datetime.datetime.now()}}
            )
            return jsonify({"message": "Income added and wallet balance updated"}), 201
    else:
        return jsonify({"error": "Wallet not found"}), 404
    
@income_bp.route('/income', methods=['GET'])
def get_incomes():
    """It should return a list of all existing incomes"""
    # Get a list of incomes from MongoDB
    list_of_incomes = income_collection.find({})
    # Convert the ObjectId instances to a JSON serializable format
    incomes = [
            {
                "_id": str(income["_id"]),
                "source": income.get("source", ""),
                "amount": income.get("amount", 0),
                "description": income.get("description", ""),
                "date": income.get("date", ""),
                "wallet_id": income.get("wallet_id", "")
            } 
        for income in list_of_incomes
    ]
    # Return a JSON document to the front-end
    return jsonify({'incomes': incomes}), 200

@income_bp.route('/income/<string:_id>', methods=['PUT'])
def update_income(_id):
    """It should update an income"""
    # Get a content of updated income
    updated_income = request.json
    # Get the previous version of an income (outdated)
    outdated_income = income_collection.find_one({"_id": ObjectId(_id)})
    # Check if wallet_id and amount are modified (Skip if None are changed)
    if ((updated_income["wallet_id"] != outdated_income["wallet_id"]) or (updated_income["amount"] != outdated_income["amount"])):
        if (updated_income["wallet_id"] != outdated_income["wallet_id"]):
            # Scenario 1: Changes include wallet_id
            wallet_collection.update_one({"wallet_id": outdated_income["wallet_id"]},
                {"$inc": {"balance": - outdated_income["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
            wallet_collection.update_one({"wallet_id": updated_income["wallet_id"]},
                {"$inc": {"balance": + updated_income["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
        elif (updated_income["wallet_id"] == outdated_income["wallet_id"]) and (updated_income["amount"] != outdated_income["amount"]):
            # Scenario 2: Changes NOT include wallet_id
            wallet_collection.update_one({"wallet_id": outdated_income["wallet_id"]},
            {"$inc": {"balance": - outdated_income["amount"] + updated_income["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
    # Find and update the income in MongoDB
    response = income_collection.find_one_and_update(
        {"_id": ObjectId(_id)},
        {"$set": updated_income} )
    if response is None:
        # An income with the specified id is not found
        return jsonify({"message": f'income with id: {_id} is not found'}), 404
    else:
        # An income is found and updated
        return jsonify({"message": f'income with id: {_id} is updated'}), 200

@income_bp.route('/income/<string:_id>', methods=['DELETE'])
def delete_income(_id):
    """It should delete an income"""
    # Find and delete an income from MongoDB
    response = income_collection.find_one_and_delete({"_id": ObjectId(_id)})
    if response is None:
        # An income is not found hence is unable to delete
        return jsonify({"message": f'Failed to delete income with id: {_id}'}), 404
    else:
        # Find and update the balance of corresponding wallet
        wallet_collection.update_one({"wallet_id": response["wallet_id"]},
            {"$inc": {"balance": - response["amount"]}, "$set": {"updated_at": datetime.datetime.now()}})
        # An income is deleted and the corresponding wallet has been updated
        return jsonify({"message": f'income with id: {_id} is deleted'}), 200

