from mongo_connector import *

def get_customers_tool():
    return get_all_customers()

def count_customers_tool():
    return {
        "count": count_customers()
    }

def get_products_tool():
    return get_products()

def get_orders_tool():
    return get_orders()