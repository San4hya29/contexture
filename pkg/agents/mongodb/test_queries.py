from mongo_connector import *

print("Collections:")
print(get_collections())

print("\nCustomer Count:")
print(count_customers())

print("\nCustomers:")
print(get_all_customers())