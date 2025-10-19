from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
import bcrypt
from email_validator import validate_email, EmailNotValidError

class User:
    def __init__(self, db):
        self.db = db
        self.users = db.users
    
    def create_user(self, user_data):
        """Create a new user with hashed password"""
        try:
            # Validate email
            validate_email(user_data['email'])
            
            # Check if user already exists
            if self.users.find_one({"email": user_data['email']}):
                return {"error": "User with this email already exists"}, 400
            
            # Hash password
            password = user_data['password'].encode('utf-8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            
            # Create user document
            user_doc = {
                "name": user_data['name'],
                "email": user_data['email'],
                "password": hashed_password,
                "address": user_data['address'],
                "date_of_birth": user_data['date_of_birth'],
                "phone": user_data.get('phone', ''),
                "account_number": self._generate_account_number(),
                "account_type": user_data.get('account_type', 'savings'),
                "balance": 0.0,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "transactions": []
            }
            
            result = self.users.insert_one(user_doc)
            user_doc['_id'] = str(result.inserted_id)
            del user_doc['password']  # Remove password from response
            
            return user_doc, 201
            
        except EmailNotValidError:
            return {"error": "Invalid email format"}, 400
        except Exception as e:
            return {"error": str(e)}, 500
    
    def authenticate_user(self, email, password):
        """Authenticate user login"""
        try:
            user = self.users.find_one({"email": email})
            if not user:
                return {"error": "Invalid credentials"}, 401
            
            if not user.get('is_active', True):
                return {"error": "Account is deactivated"}, 401
            
            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Update last login
                self.users.update_one(
                    {"_id": user['_id']},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
                
                # Remove password from response
                user['_id'] = str(user['_id'])
                del user['password']
                
                return user, 200
            else:
                return {"error": "Invalid credentials"}, 401
                
        except Exception as e:
            return {"error": str(e)}, 500
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                del user['password']
                return user, 200
            else:
                return {"error": "User not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500
    
    def update_user(self, user_id, update_data):
        """Update user information"""
        try:
            # Remove fields that shouldn't be updated directly
            update_data.pop('password', None)
            update_data.pop('_id', None)
            update_data.pop('account_number', None)
            update_data.pop('balance', None)
            update_data.pop('created_at', None)
            
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count:
                return {"message": "User updated successfully"}, 200
            else:
                return {"error": "User not found or no changes made"}, 404
                
        except Exception as e:
            return {"error": str(e)}, 500
    
    def _generate_account_number(self):
        """Generate unique account number"""
        import random
        while True:
            account_number = f"ACC{random.randint(100000, 999999)}"
            if not self.users.find_one({"account_number": account_number}):
                return account_number
