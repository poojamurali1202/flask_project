from datetime import timedelta

from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token,jwt_required, get_jwt_identity
from bson import ObjectId
import os

app = Flask(__name__)

# Configure MongoDB Atlas
app.config["MONGO_URI"] = "mongodb://localhost:27017/flask"
mongo = PyMongo(app)

# Secret Key for JWT
app.config["JWT_SECRET_KEY"] = "e9b1f85b21c74a9da1c3b25a28e9d07d458eac12268b2c4db86b3c95f328c9f2"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)

@app.route('/')
def home():
    return jsonify({"message": "Flask API is running!"})

# User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if mongo.db.users.find_one({"email": data["email"]}):
        return jsonify({"message": "User already exists"}), 400

    mongo.db.users.insert_one(data)
    user = mongo.db.users.find_one({"email": data["email"]})
    return jsonify({"message": f"User registered successfully{str(user)}"}), 201

# User Login & Token Generation
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = mongo.db.users.find_one({"email": data["email"]})
    if not user or user["password"] != data["password"]:
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=data["email"])
    return jsonify(access_token=access_token), 200

# Insert Template (Protected Route)
@app.route('/template', methods=['POST'])
@jwt_required()
def create_template():
    user_id = get_jwt_identity()
    data = request.json
    template_id = mongo.db.templates.insert_one({**data, "user_id": user_id}).inserted_id
    return jsonify({"message": "Template created", "template_id": str(template_id)}), 201

# Get All Templates for Logged-in User
@app.route('/template', methods=['GET'])
@jwt_required()
def get_templates():
    user_id = get_jwt_identity()
    templates = list(mongo.db.templates.find({"user_id": user_id}))
    return jsonify([{"_id": str(t["_id"]), "template_name": t["template_name"], "subject": t["subject"]} for t in templates]), 200

# Get a Single Template
@app.route('/template/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    user_id = get_jwt_identity()
    template = mongo.db.templates.find_one({"_id": ObjectId(template_id), "user_id": user_id})
    if not template:
        return jsonify({"message": "Template not found"}), 404
    return jsonify({"_id": str(template["_id"]), "template_name": template["template_name"], "subject": template["subject"]}), 200

# Update a Template
@app.route('/template/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    user_id = get_jwt_identity()
    data = request.json
    result = mongo.db.templates.update_one({"_id": ObjectId(template_id), "user_id": user_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"message": "Template not found"}), 404
    return jsonify({"message": "Template updated"}), 200

# Delete a Template
@app.route('/template/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    user_id = get_jwt_identity()
    result = mongo.db.templates.delete_one({"_id": ObjectId(template_id), "user_id": user_id})
    if result.deleted_count == 0:
        return jsonify({"message": "Template not found"}), 404
    return jsonify({"message": "Template deleted"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080,debug=True)
