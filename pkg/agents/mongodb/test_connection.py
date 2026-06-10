from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["copilot_db"]

print("Connected Successfully!")

print("\nCollections:")

for collection in db.list_collection_names():
    print("-", collection)