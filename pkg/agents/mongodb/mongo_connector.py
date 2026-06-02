from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["copilot_db"]


def get_collections():
    return db.list_collection_names()


def count_customers():
    return db.customers.count_documents({})


def get_all_customers():
    customers = list(db.customers.find({}, {"_id": 0}))
    return customers


def get_products():
    products = list(db.products.find({}, {"_id": 0}))
    return products


def get_orders():
    orders = list(db.orders.find({}, {"_id": 0}))
    return orders