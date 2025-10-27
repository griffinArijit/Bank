from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pymongo import PyMongo
from models import BankingModel
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/bank_app")
mongo = PyMongo(app)
CORS(app)

# Initialize model
bank_model = BankingModel(mongo.db)

# ---------------------- AUTH DECORATOR ----------------------
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header required"}), 401
        try:
            token = auth_header.split(" ")[1]
            user, status = bank_model.get_user_by_id(token)
            if status != 200:
                return jsonify({"error": "Invalid or expired token"}), 401
            request.current_user = user
        except Exception:
            return jsonify({"error": "Invalid token format"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- BASE ROUTE ----------------------
@app.route("/")
def index():
    return jsonify({
        "message": "Welcome to the Banking API",
        "version": "3.0.0",
        "endpoints": {
            "auth": {
                "register": "POST /api/auth/register",
                "login": "POST /api/auth/login",
                "change_password": "POST /api/auth/change_password"
            },
            "user": {
                "profile": "GET /api/user/profile",
                "balance": "GET /api/user/balance",
                "accounts": {
                    "list": "GET /api/user/accounts",
                    "create": "POST /api/user/accounts"
                }
            },
            "beneficiaries": {
                "add": "POST /api/beneficiaries",
                "list": "GET /api/beneficiaries"
            },
            "transfer": "POST /api/transfer",
            "transactions": "GET /api/transactions"
        }
    })

# ---------------------- AUTH ROUTES ----------------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        required = ["name", "email", "password", "address", "date_of_birth"]
        for field in required:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        user, status = bank_model.create_user(data)
        return jsonify(user), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password required"}), 400
        user, status = bank_model.authenticate_user(data["email"], data["password"])
        if status == 200:
            user["token"] = user["_id"]
        return jsonify(user), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/change_password", methods=["POST"])
@require_auth
def change_password():
    try:
        data = request.get_json()
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        if not old_password or not new_password:
            return jsonify({"error": "Both old_password and new_password required"}), 400
        result, status = bank_model.change_password(
            request.current_user["_id"],
            old_password,
            new_password
        )
        return jsonify(result), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- USER ROUTES ----------------------
@app.route("/api/user/profile", methods=["GET"])
@require_auth
def get_profile():
    return jsonify(request.current_user), 200

@app.route("/api/user/balance", methods=["GET"])
@require_auth
def get_balance():
    result, status = bank_model.get_user_balance(request.current_user["_id"])
    return jsonify(result), status

@app.route("/api/user/accounts", methods=["GET"])
@require_auth
def list_user_accounts():
    result, status = bank_model.get_user_accounts(request.current_user["_id"])
    return jsonify(result), status


@app.route("/api/user/accounts", methods=["POST"])
@require_auth
def create_user_account():
    try:
        data = request.get_json()
        if not data.get("account_type"):
            return jsonify({"error": "account_type is required"}), 400
        result, status = bank_model.create_user_account(
            user_id=request.current_user["_id"],
            account_type=data.get("account_type"),
            initial_deposit=float(data.get("initial_deposit", 0)),
            purpose=data.get("purpose"),
            business_name=data.get("business_name"),
            business_type=data.get("business_type"),
            gst_number=data.get("gst_number"),
            pan_number=data.get("pan_number")
        )
        return jsonify(result), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- BENEFICIARIES ----------------------
from bson import ObjectId

from bson import ObjectId

@app.route("/api/beneficiaries", methods=["POST"])
@require_auth
def add_beneficiary():
    try:
        data = request.get_json()
        required = ["name", "account_number", "ifsc", "email", "bank_name"]
        for field in required:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        user_id = request.current_user["_id"]

        # 1. Check if this beneficiary already exists for the current user
        existing = mongo.db.beneficiaries.find_one({
            "account_number": data["account_number"],
            "user_id": user_id
        })
        if existing:
            return jsonify({"error": "Beneficiary already exists"}), 400

        # 2. Check if the account number exists in accounts collection
        account_doc = mongo.db.accounts.find_one({"account_number": data["account_number"]})

        if account_doc:
            # Account exists, mark verified and link to user
            verified = True
            linked_user_id = account_doc["user_id"]
        else:
            # Account not found, mark pending
            verified = False
            linked_user_id = None

        # 3. Create new beneficiary document
        new_beneficiary = {
            "user_id": user_id,  # the user who adds this beneficiary
            "name": data["name"],
            "account_number": data["account_number"],
            "ifsc": data["ifsc"],
            "email": data["email"],
            "bank_name": data["bank_name"],
            "verified": verified,
            "linked_user_id": linked_user_id
        }

        result = mongo.db.beneficiaries.insert_one(new_beneficiary)
        beneficiary_id = str(result.inserted_id)

        # 4. Link beneficiary to the current user's beneficiaries array
        mongo.db.users.update_one(
            {"_id": user_id},
            {"$addToSet": {"beneficiaries": beneficiary_id}}
        )

        return jsonify({
            "message": "Beneficiary added successfully",
            "beneficiary_id": beneficiary_id,
            "verified": verified
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/beneficiaries", methods=["GET"])
@require_auth
def get_beneficiaries():
    try:
        user_id = request.current_user["_id"]

        # 1. User's own beneficiaries (pending + verified)
        user_beneficiaries = list(mongo.db.beneficiaries.find(
            {"user_id": user_id},
            {"_id": 1, "name": 1, "account_number": 1, "verified": 1, "bank_name": 1}
        ))

        # 2. Other users' verified beneficiaries
        other_verified = list(mongo.db.beneficiaries.find(
            {"user_id": {"$ne": user_id}, "verified": True},
            {"_id": 1, "name": 1, "account_number": 1, "verified": 1, "bank_name": 1}
        ))

        # Merge, avoiding duplicates (by account_number)
        merged = {b["account_number"]: b for b in user_beneficiaries}
        for b in other_verified:
            merged[b["account_number"]] = b

        # Convert _id to string
        response = []
        for b in merged.values():
            response.append({
                "_id": str(b["_id"]),
                "name": b["name"],
                "account_number": b["account_number"],
                "bank_name": b.get("bank_name"),
                "verified": b.get("verified", False)
            })

        return jsonify({"beneficiaries": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------- TRANSFERS ----------------------
@app.route("/api/transfer", methods=["POST"])
@require_auth
def transfer():
    try:
        data = request.get_json()
        required = ["beneficiary_id", "amount", "transfer_mode", "from_acc_number"]
        for field in required:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        user_id = request.current_user["_id"]
        amount = float(data["amount"])
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400

        # Find beneficiary
        beneficiary = mongo.db.beneficiaries.find_one({
            "_id": ObjectId(data["beneficiary_id"]),
            "user_id": user_id
        })
        if not beneficiary:
            return jsonify({"error": "Beneficiary not found"}), 400
        if not beneficiary["verified"]:
            return jsonify({"error": "Cannot transfer to unverified beneficiary"}), 400

        # Find source account
        from_acc = mongo.db.accounts.find_one({
            "user_id": user_id,
            "account_number": data["from_acc_number"]
        })
        if not from_acc:
            return jsonify({"error": "Source account not found"}), 400
        if from_acc["balance"] < amount:
            return jsonify({"error": "Insufficient balance"}), 400

        # Deduct from user's account
        mongo.db.accounts.update_one({"_id": from_acc["_id"]}, {"$inc": {"balance": -amount}})

        # Credit beneficiary if internal account exists
        ben_acc = mongo.db.accounts.find_one({"account_number": beneficiary["account_number"]})
        if ben_acc:
            mongo.db.accounts.update_one({"_id": ben_acc["_id"]}, {"$inc": {"balance": amount}})

        # Log transaction
        mongo.db.transactions.insert_one({
            "user_id": user_id,
            "beneficiary_id": beneficiary["_id"],
            "amount": amount,
            "transfer_mode": data["transfer_mode"]
        })

        return jsonify({"message": "Transfer completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------- TRANSACTIONS ----------------------
@app.route("/api/transactions", methods=["GET"])
@require_auth
def transactions():
    limit = request.args.get("limit", 50, type=int)
    result, status = bank_model.get_transactions(request.current_user["_id"], limit)
    return jsonify(result), status

# ---------------------- START SERVER ----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
