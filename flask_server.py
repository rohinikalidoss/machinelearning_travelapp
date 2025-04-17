from flask import Flask, request, jsonify
import torch
import torch.nn as nn
import numpy as np
from pymongo import MongoClient
from travel import TravelRecommender, get_recommendations
import os
from dotenv import load_dotenv
import traceback
import json

app = Flask(__name__)

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection
if MONGO_URI is None:
    raise ValueError("MongoDB URI not found in .env file. Check your .env configuration.")

client = MongoClient(MONGO_URI)
db = client["usertravel"]
collection = db["places"]

# Load place_map and model
model_path = "travel_model.pth"
place_map_path = "place_map.json"

try:
    with open(place_map_path, "r") as f:
        place_map = json.load(f)
    num_classes = len(place_map)
    model = TravelRecommender(num_classes=num_classes)

    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        model.eval()
        print("✅ Model loaded successfully.")
    else:
        print("⚠️ Warning: Model file not found. Please train the model.")
except FileNotFoundError:
    raise FileNotFoundError("❌ place_map.json not found. Please train the model first.")

# Home route
@app.route("/")
def home():
    return jsonify({"message": "Flask Travel Recommendation API is running."})

# Route to get all user data
@app.route("/getUserData", methods=["GET"])
def get_user_data():
    try:
        user_data = list(collection.find({}, {"_id": 0}))
        return jsonify({"data": user_data}), 200
    except Exception as e:
        print("Error in /getUserData:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Route to add user data and get travel recommendation
@app.route("/addUserData", methods=["POST"])
def add_user_data():
    try:
        user_data = request.json
        print("📥 Incoming user data:", user_data)

        # Validate input fields
        required_fields = ["Month", "Season", "Budget", "Activity_Preference", "Group_Size"]
        for field in required_fields:
            if field not in user_data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Get travel prediction
        predictions = get_recommendations(user_data)
        print("Prediction result:", predictions)

        user_data["Suggested_Place"] = predictions["suggested_places"][0]

        # Save to MongoDB
        collection.insert_one(user_data)
        return jsonify({
            "message": "User data added successfully!",
            "prediction": user_data["Suggested_Place"]
        }), 200

    except Exception as e:
        print("Error in /addUserData:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(port=5000, debug=True, use_reloader=False)
