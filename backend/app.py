from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pymongo import PyMongo
from models import User
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure MongoDB
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/bank_app')
mongo = PyMongo(app)

# Enable CORS for all routes
CORS(app)

# Initialize User model
user_model = User(mongo.db)

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header required"}), 401
        
        try:
            # Extract token from "Bearer <token>" format
            token = auth_header.split(' ')[1]
            # For now, we'll use a simple approach - in production, use JWT
            user_id = token  # This should be decoded from JWT token
            user, status = user_model.get_user_by_id(user_id)
            if status != 200:
                return jsonify({"error": "Invalid token"}), 401
            request.current_user = user
        except:
            return jsonify({"error": "Invalid token format"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return jsonify({
        "message": "Bank API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "register": "POST /api/auth/register",
                "login": "POST /api/auth/login"
            },
            "user": {
                "profile": "GET /api/user/profile",
                "update": "PUT /api/user/profile"
            }
        }
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'address', 'date_of_birth']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Validate password strength
        if len(data['password']) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        user, status = user_model.create_user(data)
        return jsonify(user), status
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password are required"}), 400
        
        user, status = user_model.authenticate_user(data['email'], data['password'])
        
        if status == 200:
            # In production, generate JWT token here
            # For now, we'll return user ID as token
            user['token'] = user['_id']
        
        return jsonify(user), status
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    return jsonify(request.current_user), 200

@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Remove sensitive fields that shouldn't be updated
        data.pop('password', None)
        data.pop('account_number', None)
        data.pop('balance', None)
        data.pop('_id', None)
        
        result, status = user_model.update_user(request.current_user['_id'], data)
        return jsonify(result), status
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/balance', methods=['GET'])
@require_auth
def get_balance():
    """Get user account balance"""
    user = request.current_user
    return jsonify({
        "account_number": user['account_number'],
        "balance": user['balance'],
        "account_type": user['account_type']
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
