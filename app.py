from flask import Flask, request, jsonify
from dotenv import load_dotenv
from bson import ObjectId
import pymongo
import datetime
import os 
from bson import ObjectId
from flask_cors import CORS
from google.cloud import documentai_v1beta3 as documentai
from google.oauth2 import service_account
import os


app = Flask(__name__)
# Allow cross-origin sharing with React at http://localhost:3000
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

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

@app.route('/expense', methods=['POST'])
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


@app.route('/expense', methods=['GET'])
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

@app.route('/expense/<string:_id>', methods=["PUT"])
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
    app.logger.debug(f"Received ID: {_id}")
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

@app.route('/expense/<string:_id>', methods=["DELETE"])
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


############################################################################################
#####                         ADD INCOME HERE                                         ######
############################################################################################

@app.route('/income', methods=['POST'])
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
    
@app.route('/income', methods=['GET'])
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

@app.route('/income/<string:_id>', methods=['PUT'])
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
    # Log the received ID for debugging
    app.logger.debug(f"Received ID: {_id}")
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

@app.route('/income/<string:_id>', methods=['DELETE'])
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


############################################################################################
#####                         ADD WALLET FUNCTIONS HERE                              #######
############################################################################################

@app.route('/wallet', methods=['POST'])
def add_wallet():
    """It should add a wallet to database"""
    # Receive parsed data sent from the front-end (React)
    wallet = request.json
    # Generate a unique wallet_id
    wallet_id = str(ObjectId())
    wallet["_id"] = wallet_id
    wallet["wallet_id"] = wallet_id
    # Insert an wallet into MongoDB Atlas
    wallet_collection.insert_one(wallet)
    # Return a success message
    return jsonify({"Message": "A wallet has been succesfully added"}), 201

@app.route('/wallet', methods=['GET'])
def get_wallets():
    """It should return a list of all available expenses"""
    # Get a list of wallets from MongoDB
    list_of_wallets = wallet_collection.find({})
    # Convert the ObjectId instances to a JSON serializable format
    wallets = [
        {
         "wallet_id": str(wallet["wallet_id"]), 
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

@app.route('/wallet/<string:wallet_id>', methods=["PUT"])
def update_wallet(wallet_id):
    """It should update a wallet"""
    # Get a content of updated wallet
    updated_wallet = request.json
    # Log the received ID for debugging
    app.logger.debug(f"Received ID: {wallet_id}")
    # Find and update the wallet in MongoDB
    response = wallet_collection.find_one_and_update(
        {"wallet_id": wallet_id},
        {"$set": updated_wallet} )
    if response is None:
        # A wallet with the specified id is not found
        return jsonify({"message": f'Wallet with id: {wallet_id} is not found'}), 404
    else:
        # A wallet is found and updated
        return jsonify({"message": f'Wallet with id: {wallet_id} is updated'}), 200

@app.route('/wallet/<string:wallet_id>', methods=["DELETE"])
def delete_wallet(wallet_id):
    """It should delete a wallet"""
    # Find and delete a wallet from MongoDB
    response = wallet_collection.find_one_and_delete({"wallet_id": wallet_id})
    if response is None:
        # A wallet id is not found hence, is unable to delete
        return jsonify({"message": f'Failed to delete expense with id: {wallet_id}'}), 404
    else:
        # A wallet id is found and deleted
        return jsonify({"message": f'Expense with id: {wallet_id} is deleted'}), 200


############################################################################################
#####                         ADD SCAN RECEIPT FUNCTIONS HERE                         ######
############################################################################################


# Load your Google Cloud service account credentials from the environment variable
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
credentials = service_account.Credentials.from_service_account_file(credentials_path)

# Set Document AI processor details
project_id = 'apt-reality-433311-j4'
location = 'us'
processor_id = 'b348edb6e0374f40'  # This is your processor ID

@app.route('/scan-receipt', methods=['POST'])
def scan_receipt():
    # Check if a file was uploaded
    if 'receipt' not in request.files:
        return jsonify({"error": "No receipt file uploaded"}), 400

    file = request.files['receipt']
    image_content = file.read()

    # Initialize the Document AI client
    client = documentai.DocumentProcessorServiceClient(credentials=credentials)

    # Configure the request to Document AI
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    document = documentai.types.Document(content=image_content, mime_type='image/jpeg')
    doc_request = documentai.types.ProcessRequest(name=name, raw_document=documentai.types.RawDocument(content=image_content, mime_type='image/jpeg'))

    # Process the document
    result = client.process_document(request=doc_request)

    # Extract relevant information from the result
    document = result.document
    amount = None
    description = None
    date = None

    for entity in document.entities:
        if entity.type_ == "total_amount":
            amount = entity.mention_text
        elif entity.type_ == "line_item[description]":
            description = entity.mention_text
        elif entity.type_ == "receipt_date":
            date = entity.mention_text
    print(amount)
    print(description)
    print(date)
    # Return the extracted data as a JSON response
    return jsonify({
        "amount": amount,
        "description": description,
        "date": date,
        "message": "Expense created. Please confirm to add it."
    })

if __name__ == '__main__':   
    app.run(host='0.0.0.0', port=5000)
    


        

