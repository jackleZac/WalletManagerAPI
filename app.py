from flask import Flask
from flask_cors import CORS
from routes import expense_bp, income_bp, wallet_bp, budget_bp, scanner_bp

app = Flask(__name__)
CORS(app) 

# Register Blueprints
app.register_blueprint(expense_bp)
app.register_blueprint(income_bp)
app.register_blueprint(wallet_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(scanner_bp)


if __name__ == '__main__':   
    app.run(host='0.0.0.0', port=5000)
    


        

