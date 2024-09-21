from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from bson import ObjectId
import pymongo
from dateutil import parser
import os

wallet_bp = Blueprint('wallet', __name__)

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
        print(f'ERROR: An unexpected error occurred: {e}')
    
client, database_collection = connect_to_db()
expense_collection = database_collection['expense']
income_collection = database_collection['income']
wallet_collection = database_collection['wallet']
budget_collection = database_collection['budget']

############################################################################################
#####                         ADD WALLET FUNCTIONS HERE                              #######
############################################################################################

@wallet_bp.route('/wallet', methods=['POST'])
def add_wallet():
    """It should add a wallet to database"""
    # Receive parsed data sent from the front-end (React)
    wallet = request.json
    # Verify if the provided budget_id exists in the budget collection
    budget_id = wallet.get("budget_id")
    budget = budget_collection.find_one({"_id": ObjectId(budget_id)})
    if not budget:
        return jsonify({"error": "Invalid budget_id, no matching budget found"}), 404
    # Insert a wallet into MongoDB Atlas
    wallet_collection.insert_one(wallet)
    # Return a success message
    return jsonify({"Message": "A wallet has been succesfully added"}), 201

@wallet_bp.route('/wallet', methods=['GET'])
def get_wallets():
    """It should return a list of all available expenses"""
    # Get a list of wallets from MongoDB
    list_of_wallets = wallet_collection.find({})
    # Convert the ObjectId instances to a JSON serializable format
    wallets = [
        {
         "wallet_id": str(wallet["_id"]), 
         "budget_id": str(wallet["budget_id"]),
         "balance": wallet["balance"], 
         "created_at": wallet["created_at"], 
         "updated_at": wallet["updated_at"],
         "type": wallet["type"], 
         "target": wallet["target"]
         } 
        for wallet in list_of_wallets
    ]
    # Return a JSON document to the front-end
    return jsonify({'wallets': wallets})

@wallet_bp.route('/wallet/<string:wallet_id>', methods=["PUT"])
def update_wallet(wallet_id):
    """It should update a wallet"""
    # Get a content of updated wallet
    updated_wallet = request.json
    # Log the received ID for debugging
    wallet_bp.logger.debug(f"Received ID: {wallet_id}")
    # Find and update the wallet in MongoDB
    response = wallet_collection.find_one_and_update(
        {"_id": ObjectId(wallet_id)},
        {"$set": updated_wallet} )
    if response is None:
        # A wallet with the specified id is not found
        return jsonify({"message": f'Wallet with id: {wallet_id} is not found'}), 404
    else:
        # A wallet is found and updated
        return jsonify({"message": f'Wallet with id: {wallet_id} is updated'}), 200

@wallet_bp.route('/wallet/<string:wallet_id>', methods=["DELETE"])
def delete_wallet(wallet_id):
    """It should delete a wallet"""
    # Find and delete a wallet from MongoDB
    response = wallet_collection.find_one_and_delete({"wallet_id": ObjectId(wallet_id)})
    if response is None:
        # A wallet id is not found, unable to delete
        return jsonify({"message": f'Failed to delete expense with id: {wallet_id}'}), 404
    # Wallet is deleted, now delete associated incomes and expenses
    income_result = income_collection.delete_many({"wallet_id": str(wallet_id)})
    expense_result = expense_collection.delete_many({"wallet_id": str(wallet_id)})
    # Return success message, including number of related documents deleted
    return jsonify({
        "message": f'Wallet with id: {wallet_id} is deleted',
        "incomes_deleted": income_result.deleted_count,
        "expenses_deleted": expense_result.deleted_count
    }), 200

