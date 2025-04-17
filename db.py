from pymongo import MongoClient
import pandas as pd

# Correct MongoDB Atlas Connection String
MONGO_URI = "mongodb+srv://gangapalani20:xHa5NvJ8K2UKEFIP@cluster0.j8t3b.mongodb.net/usertravel?retryWrites=true&w=majority"

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # Check connection
    print("Connected to MongoDB Atlas Successfully!")
except Exception as e:
    print(f"MongoDB Atlas Connection Failed: {e}")

# Load CSV Data
df = pd.read_csv("updated_places.csv")
print(f"Loaded 'updated_places.csv' successfully! Total Records: {len(df)}")

#Insert into MongoDB Collection
db = client["usertravel"]   # Make sure this matches your actual database name
collection = db["places"]    # Change this to your correct collection name

data_records = df.to_dict(orient="records")

if data_records:
    result = collection.insert_many(data_records)
    print(f"{len(result.inserted_ids)} records inserted successfully!")
else:
    print("No data found to insert.")
