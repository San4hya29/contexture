from tool_registry import TOOLS

def process_query(query):

    query = query.lower()

    if "customer" in query and ("count" in query or "how many" in query):
        return TOOLS["customer_count"]()

    elif "customer" in query:
        return TOOLS["customers"]()

    elif "product" in query:
        return TOOLS["products"]()

    elif "order" in query:
        return TOOLS["orders"]()

    else:
        return {
            "message": "No suitable tool found"
        }